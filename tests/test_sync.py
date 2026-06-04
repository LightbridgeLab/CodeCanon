"""Tests for CodeCannon sync.py — the sync engine."""

import hashlib
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest.mock import patch

# Add the repo root to the path so we can import sync as a module.
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import sync


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_skill(tmpdir, name, frontmatter, body):
    """Write a skill markdown file into tmpdir/skills/<name>.md."""
    skills_dir = Path(tmpdir) / "skills"
    skills_dir.mkdir(exist_ok=True)
    path = skills_dir / f"{name}.md"
    content = f"---\n{frontmatter}\n---\n\n{body}"
    path.write_text(content)
    return path


def _make_adapter(tmpdir, name, config_yaml, header_md=""):
    """Write an adapter directory into tmpdir/adapters/<name>/."""
    adapter_dir = Path(tmpdir) / "adapters" / name
    adapter_dir.mkdir(parents=True, exist_ok=True)
    (adapter_dir / "config.yaml").write_text(config_yaml)
    if header_md:
        (adapter_dir / "header.md").write_text(header_md)
    return adapter_dir


def _make_args(**overrides):
    """Return a minimal argparse-like namespace for sync_skill."""
    defaults = {"force": False, "dry_run": False}
    defaults.update(overrides)
    return type("Args", (), defaults)()


# ═══════════════════════════════════════════════════════════════════════════════
# YAML PARSING
# ═══════════════════════════════════════════════════════════════════════════════


class TestDequote(unittest.TestCase):

    def test_double_quoted(self):
        self.assertEqual(sync._dequote('"hello world"'), "hello world")

    def test_single_quoted(self):
        self.assertEqual(sync._dequote("'hello world'"), "hello world")

    def test_unquoted(self):
        self.assertEqual(sync._dequote("hello"), "hello")

    def test_double_quoted_escape_quote(self):
        self.assertEqual(sync._dequote(r'"say \"hi\""'), 'say "hi"')

    def test_double_quoted_escape_backslash(self):
        self.assertEqual(sync._dequote(r'"back\\slash"'), "back\\slash")

    def test_single_quoted_no_escapes(self):
        self.assertEqual(sync._dequote(r"'no \" escapes'"), r'no \" escapes')

    def test_empty_double_quotes(self):
        self.assertEqual(sync._dequote('""'), "")

    def test_empty_single_quotes(self):
        self.assertEqual(sync._dequote("''"), "")

    def test_single_char(self):
        self.assertEqual(sync._dequote("x"), "x")

    def test_empty_string(self):
        self.assertEqual(sync._dequote(""), "")


class TestParseYamlSimple(unittest.TestCase):

    def test_flat_key_value(self):
        text = "name: Alice\nage: 30"
        result = sync.parse_yaml_simple(text)
        self.assertEqual(result, {"name": "Alice", "age": "30"})

    def test_nested_dict(self):
        text = "config:\n  FOO: bar\n  BAZ: qux"
        result = sync.parse_yaml_simple(text)
        self.assertEqual(result, {"config": {"FOO": "bar", "BAZ": "qux"}})

    def test_list(self):
        text = "adapters:\n  - claude\n  - cursor"
        result = sync.parse_yaml_simple(text)
        self.assertEqual(result, {"adapters": ["claude", "cursor"]})

    def test_comments_and_blanks_ignored(self):
        text = "# comment\n\nkey: value\n  # nested comment"
        result = sync.parse_yaml_simple(text)
        self.assertEqual(result, {"key": "value"})

    def test_quoted_values(self):
        text = 'config:\n  MSG: "hello world"\n  OTHER: \'single\''
        result = sync.parse_yaml_simple(text)
        self.assertEqual(result["config"]["MSG"], "hello world")
        self.assertEqual(result["config"]["OTHER"], "single")

    def test_empty_value_creates_dict(self):
        text = "config:"
        result = sync.parse_yaml_simple(text)
        self.assertEqual(result, {"config": {}})

    def test_mixed_list_after_dict_key(self):
        """If a key starts as a dict, then encounters a list item, it converts."""
        text = "items:\n  - alpha\n  - beta"
        result = sync.parse_yaml_simple(text)
        self.assertEqual(result["items"], ["alpha", "beta"])


class TestParseFrontmatter(unittest.TestCase):

    def test_basic_frontmatter(self):
        text = "---\nskill: deploy\ntype: skill\n---\n\nBody content here."
        fm, body = sync.parse_frontmatter(text)
        self.assertEqual(fm["skill"], "deploy")
        self.assertEqual(fm["type"], "skill")
        self.assertEqual(body, "Body content here.")

    def test_no_frontmatter(self):
        text = "Just a body with no frontmatter."
        fm, body = sync.parse_frontmatter(text)
        self.assertEqual(fm, {})
        self.assertEqual(body, "Just a body with no frontmatter.")

    def test_quoted_description(self):
        text = '---\ndescription: "My cool skill"\n---\n\nBody.'
        fm, body = sync.parse_frontmatter(text)
        self.assertEqual(fm["description"], "My cool skill")

    def test_inline_list_in_frontmatter(self):
        text = "---\ntags: [foo, bar, baz]\n---\n\nBody."
        fm, body = sync.parse_frontmatter(text)
        self.assertEqual(fm["tags"], ["foo", "bar", "baz"])

    def test_body_stripped(self):
        text = "---\nk: v\n---\n\n  Body with leading space.  \n\nTrailing."
        fm, body = sync.parse_frontmatter(text)
        self.assertIn("Body with leading space.", body)


# ═══════════════════════════════════════════════════════════════════════════════
# CONDITIONAL BLOCKS
# ═══════════════════════════════════════════════════════════════════════════════


class TestApplyConditionals(unittest.TestCase):

    def test_truthy_keeps_block(self):
        text = "before\n{{#if FOO}}\nkept\n{{/if}}\nafter"
        result = sync.apply_conditionals(text, {"FOO": "yes"})
        self.assertIn("kept", result)
        self.assertIn("before", result)
        self.assertIn("after", result)
        self.assertNotIn("{{#if", result)
        self.assertNotIn("{{/if}}", result)

    def test_falsy_removes_block(self):
        text = "before\n{{#if FOO}}\nremoved\n{{/if}}\nafter"
        result = sync.apply_conditionals(text, {"FOO": ""})
        self.assertNotIn("removed", result)
        self.assertIn("before", result)
        self.assertIn("after", result)

    def test_missing_key_is_falsy(self):
        text = "{{#if MISSING}}\nhidden\n{{/if}}\nvisible"
        result = sync.apply_conditionals(text, {})
        self.assertNotIn("hidden", result)
        self.assertIn("visible", result)

    def test_negated_truthy_removes_block(self):
        text = "{{#if !FOO}}\nhidden\n{{/if}}\nvisible"
        result = sync.apply_conditionals(text, {"FOO": "yes"})
        self.assertNotIn("hidden", result)
        self.assertIn("visible", result)

    def test_negated_falsy_keeps_block(self):
        text = "{{#if !FOO}}\nkept\n{{/if}}\nvisible"
        result = sync.apply_conditionals(text, {"FOO": ""})
        self.assertIn("kept", result)

    def test_boolean_false_string_is_falsy(self):
        for val in ("false", "False", "FALSE", "no", "No", "0"):
            text = "{{#if FLAG}}\nshown\n{{/if}}"
            result = sync.apply_conditionals(text, {"FLAG": val})
            self.assertNotIn("shown", result, f"Expected '{val}' to be falsy")

    def test_nested_conditionals(self):
        text = textwrap.dedent("""\
            {{#if OUTER}}
            outer-start
            {{#if INNER}}
            inner-content
            {{/if}}
            outer-end
            {{/if}}""")
        result = sync.apply_conditionals(text, {"OUTER": "yes", "INNER": "yes"})
        self.assertIn("outer-start", result)
        self.assertIn("inner-content", result)
        self.assertIn("outer-end", result)

    def test_nested_outer_false_removes_all(self):
        text = textwrap.dedent("""\
            {{#if OUTER}}
            outer-start
            {{#if INNER}}
            inner-content
            {{/if}}
            outer-end
            {{/if}}""")
        result = sync.apply_conditionals(text, {"OUTER": "", "INNER": "yes"})
        self.assertNotIn("outer-start", result)
        self.assertNotIn("inner-content", result)

    def test_multiple_independent_blocks(self):
        text = "{{#if A}}\nalpha\n{{/if}}\n{{#if B}}\nbeta\n{{/if}}"
        result = sync.apply_conditionals(text, {"A": "yes", "B": ""})
        self.assertIn("alpha", result)
        self.assertNotIn("beta", result)

    def test_malformed_no_open_tag(self):
        """A lone {{/if}} should not crash — processing just stops."""
        text = "content\n{{/if}}\nmore"
        result = sync.apply_conditionals(text, {})
        # The malformed block stops processing; the text is returned as-is
        self.assertIn("content", result)


# ═══════════════════════════════════════════════════════════════════════════════
# PLACEHOLDER SUBSTITUTION
# ═══════════════════════════════════════════════════════════════════════════════


class TestApplyPlaceholders(unittest.TestCase):

    def test_basic_substitution(self):
        text = "Branch: {{BRANCH_PROD}}"
        result = sync.apply_placeholders(text, {"BRANCH_PROD": "main"})
        self.assertEqual(result, "Branch: main")

    def test_multiple_placeholders(self):
        text = "{{A}} and {{B}}"
        result = sync.apply_placeholders(text, {"A": "alpha", "B": "beta"})
        self.assertEqual(result, "alpha and beta")

    def test_repeated_placeholder(self):
        text = "{{X}} then {{X}}"
        result = sync.apply_placeholders(text, {"X": "val"})
        self.assertEqual(result, "val then val")

    def test_unresolved_left_alone(self):
        text = "{{KNOWN}} and {{UNKNOWN}}"
        result = sync.apply_placeholders(text, {"KNOWN": "ok"})
        self.assertEqual(result, "ok and {{UNKNOWN}}")

    def test_empty_values_dict(self):
        text = "nothing {{HERE}}"
        result = sync.apply_placeholders(text, {})
        self.assertEqual(result, "nothing {{HERE}}")


class TestFindUnresolved(unittest.TestCase):

    def test_finds_unresolved(self):
        text = "{{RESOLVED}} and {{MISSING}}"
        result = sync.find_unresolved(text)
        self.assertEqual(result, ["RESOLVED", "MISSING"])

    def test_no_unresolved(self):
        text = "plain text"
        result = sync.find_unresolved(text)
        self.assertEqual(result, [])

    def test_ignores_lowercase(self):
        text = "{{lowercase}}"
        result = sync.find_unresolved(text)
        self.assertEqual(result, [])

    def test_multiple_same(self):
        text = "{{A}} and {{A}}"
        result = sync.find_unresolved(text)
        self.assertEqual(result, ["A", "A"])


# ═══════════════════════════════════════════════════════════════════════════════
# HASH AND CHANGE DETECTION
# ═══════════════════════════════════════════════════════════════════════════════


class TestContentHash(unittest.TestCase):

    def test_deterministic(self):
        self.assertEqual(sync.content_hash("hello"), sync.content_hash("hello"))

    def test_different_inputs(self):
        self.assertNotEqual(sync.content_hash("a"), sync.content_hash("b"))

    def test_length(self):
        h = sync.content_hash("test")
        self.assertEqual(len(h), 8)

    def test_matches_md5(self):
        expected = hashlib.md5("test".encode()).hexdigest()[:8]
        self.assertEqual(sync.content_hash("test"), expected)


class TestFirstLineHasSyncMarker(unittest.TestCase):

    def test_current_marker(self):
        line = f"<!-- {sync.MARKER} | skill: foo | adapter: bar | hash: abcd1234 | DO NOT EDIT -->"
        self.assertTrue(sync.first_line_has_sync_marker(line))

    def test_legacy_marker(self):
        line = "<!-- generated by CodeCannon/sync.sh | skill: foo | hash: 1234 -->"
        self.assertTrue(sync.first_line_has_sync_marker(line))

    def test_no_marker(self):
        self.assertFalse(sync.first_line_has_sync_marker("just a normal line"))

    def test_empty_line(self):
        self.assertFalse(sync.first_line_has_sync_marker(""))


class TestReadFileInfo(unittest.TestCase):

    def test_nonexistent_file(self):
        stored, body_h, is_gen, migrate = sync.read_file_info("/nonexistent/path")
        self.assertIsNone(stored)
        self.assertFalse(is_gen)

    def test_file_with_current_marker_at_end(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            body = "some content\n"
            h = sync.content_hash(body)
            marker = f"<!-- {sync.MARKER} | skill: test | adapter: claude | hash: {h} | DO NOT EDIT -->"
            f.write(body + marker + "\n")
            f.flush()
            stored, body_h, is_gen, migrate = sync.read_file_info(f.name)
        os.unlink(f.name)
        self.assertEqual(stored, h)
        self.assertEqual(body_h, h)
        self.assertTrue(is_gen)
        self.assertFalse(migrate)

    def test_file_with_legacy_marker_at_start(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            h = "abcd1234"
            marker = f"<!-- {sync.MARKER} | skill: test | adapter: claude | hash: {h} -->"
            body_lines = "body content\n"
            # Legacy: marker at first line
            f.write(marker + "\n" + body_lines)
            f.flush()
            stored, body_h, is_gen, migrate = sync.read_file_info(f.name)
        os.unlink(f.name)
        self.assertEqual(stored, h)
        self.assertTrue(is_gen)
        self.assertTrue(migrate)  # marker at start → needs migration

    def test_file_without_marker(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("plain file\nno marker\n")
            f.flush()
            stored, body_h, is_gen, migrate = sync.read_file_info(f.name)
        os.unlink(f.name)
        self.assertIsNone(stored)
        self.assertFalse(is_gen)
        self.assertFalse(migrate)

    def test_customized_file_detected(self):
        """If the body was edited after sync, body_hash != stored_hash."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            original_body = "original content\n"
            original_hash = sync.content_hash(original_body)
            marker = f"<!-- {sync.MARKER} | skill: test | adapter: claude | hash: {original_hash} | DO NOT EDIT -->"
            # Write with a modified body but the old hash in the marker
            f.write("modified content\n" + marker + "\n")
            f.flush()
            stored, body_h, is_gen, migrate = sync.read_file_info(f.name)
        os.unlink(f.name)
        self.assertEqual(stored, original_hash)
        self.assertNotEqual(body_h, stored)
        self.assertTrue(is_gen)

    def test_legacy_marker_text_detected(self):
        """Files with old marker text (sync.sh) need migration."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            body = "content\n"
            marker = "<!-- generated by CodeCannon/sync.sh | skill: test | hash: abcd1234 -->"
            f.write(body + marker + "\n")
            f.flush()
            stored, body_h, is_gen, migrate = sync.read_file_info(f.name)
        os.unlink(f.name)
        self.assertTrue(is_gen)
        self.assertTrue(migrate)  # legacy marker text


# ═══════════════════════════════════════════════════════════════════════════════
# ADAPTER LOADING
# ═══════════════════════════════════════════════════════════════════════════════


class TestLoadAdapter(unittest.TestCase):

    def test_load_claude_adapter(self):
        adapter = sync.load_adapter("claude")
        self.assertIsNotNone(adapter)
        self.assertEqual(adapter["name"], "claude")
        self.assertEqual(adapter["output_directory"], ".claude/commands")
        self.assertEqual(adapter["output_extension"], ".md")
        self.assertIn("{description}", adapter["header_template"])

    def test_load_cursor_adapter(self):
        adapter = sync.load_adapter("cursor")
        self.assertIsNotNone(adapter)
        self.assertEqual(adapter["name"], "cursor")
        self.assertEqual(adapter["output_extension"], ".mdc")

    def test_nonexistent_adapter(self):
        adapter = sync.load_adapter("nonexistent_adapter_xyz")
        self.assertIsNone(adapter)


class TestBuildHeader(unittest.TestCase):

    def test_substitutes_skill_and_description(self):
        adapter = {
            "header_template": "Skill: {skill}\nDesc: {description}\n",
        }
        fm = {"description": "My description"}
        header = sync.build_header(adapter, "deploy", fm)
        self.assertIn("Skill: deploy", header)
        self.assertIn("Desc: My description", header)

    def test_defaults_description_to_skill_name(self):
        adapter = {"header_template": "{description}"}
        fm = {}  # no description
        header = sync.build_header(adapter, "test-skill", fm)
        self.assertEqual(header, "test-skill")

    def test_empty_header_template(self):
        adapter = {"header_template": ""}
        fm = {"description": "Something"}
        header = sync.build_header(adapter, "s", fm)
        self.assertEqual(header, "")


# ═══════════════════════════════════════════════════════════════════════════════
# SYNC SKILL (integration-level)
# ═══════════════════════════════════════════════════════════════════════════════


class TestSyncSkill(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.project_root = Path(self.tmpdir) / "project"
        self.project_root.mkdir()
        self.adapter = {
            "name": "test",
            "output_directory": ".test/commands",
            "output_extension": ".md",
            "header_template": "{description}\n\n---\n\n",
        }
        self.config = {"BRANCH_PROD": "main", "BRANCH_DEV": "dev"}

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _write_skill(self, name, body, **fm_extra):
        fm_lines = [f'skill: {name}', 'type: skill', f'description: "Test skill: {name}"']
        for k, v in fm_extra.items():
            fm_lines.append(f'{k}: "{v}"')
        skill_dir = Path(self.tmpdir) / "skills"
        skill_dir.mkdir(exist_ok=True)
        path = skill_dir / f"{name}.md"
        path.write_text(f"---\n" + "\n".join(fm_lines) + "\n---\n\n" + body)
        return path

    def test_writes_file_on_first_sync(self):
        skill_path = self._write_skill("demo", "Hello {{BRANCH_PROD}}")
        args = _make_args()
        result = sync.sync_skill(skill_path, self.adapter, self.config, self.project_root, args)
        self.assertFalse(result)  # not dry-run, so returns False
        out = self.project_root / ".test" / "commands" / "demo.md"
        self.assertTrue(out.exists())
        content = out.read_text()
        self.assertIn("Hello main", content)
        self.assertIn(sync.MARKER, content)

    def test_dry_run_does_not_write(self):
        skill_path = self._write_skill("demo", "content")
        args = _make_args(dry_run=True)
        result = sync.sync_skill(skill_path, self.adapter, self.config, self.project_root, args)
        self.assertTrue(result)  # would write
        out = self.project_root / ".test" / "commands" / "demo.md"
        self.assertFalse(out.exists())

    def test_idempotent_second_sync(self):
        skill_path = self._write_skill("demo", "stable content")
        args = _make_args()
        sync.sync_skill(skill_path, self.adapter, self.config, self.project_root, args)
        # Second sync should detect up-to-date
        result = sync.sync_skill(skill_path, self.adapter, self.config, self.project_root, args)
        self.assertFalse(result)

    def test_skips_customized_file_without_force(self):
        skill_path = self._write_skill("demo", "original")
        args = _make_args()
        sync.sync_skill(skill_path, self.adapter, self.config, self.project_root, args)

        # Tamper with the output file body (but keep the marker)
        out = self.project_root / ".test" / "commands" / "demo.md"
        content = out.read_text()
        out.write_text(content.replace("original", "CUSTOMIZED"))

        # Update the source skill to trigger a regeneration attempt
        skill_path.write_text(skill_path.read_text().replace("original", "new-source"))

        result = sync.sync_skill(skill_path, self.adapter, self.config, self.project_root, args)
        self.assertFalse(result)
        # File should still contain the customization
        self.assertIn("CUSTOMIZED", out.read_text())

    def test_force_overwrites_customized_file(self):
        skill_path = self._write_skill("demo", "original")
        args = _make_args()
        sync.sync_skill(skill_path, self.adapter, self.config, self.project_root, args)

        out = self.project_root / ".test" / "commands" / "demo.md"
        content = out.read_text()
        out.write_text(content.replace("original", "CUSTOMIZED"))

        skill_path.write_text(skill_path.read_text().replace("original", "new-source"))

        args_force = _make_args(force=True)
        sync.sync_skill(skill_path, self.adapter, self.config, self.project_root, args_force)
        self.assertIn("new-source", out.read_text())
        self.assertNotIn("CUSTOMIZED", out.read_text())

    def test_conditional_blocks_in_sync(self):
        body = textwrap.dedent("""\
            {{#if BRANCH_DEV}}
            Dev: {{BRANCH_DEV}}
            {{/if}}
            {{#if BRANCH_TEST}}
            Test: {{BRANCH_TEST}}
            {{/if}}
            Prod: {{BRANCH_PROD}}""")
        skill_path = self._write_skill("cond", body)
        args = _make_args()
        sync.sync_skill(skill_path, self.adapter, self.config, self.project_root, args)
        out = self.project_root / ".test" / "commands" / "cond.md"
        content = out.read_text()
        self.assertIn("Dev: dev", content)
        self.assertNotIn("Test:", content)  # BRANCH_TEST not in config
        self.assertIn("Prod: main", content)

    def test_no_invocation_header(self):
        skill_path = self._write_skill("bare", "bare body", no_invocation_header="true")
        args = _make_args()
        sync.sync_skill(skill_path, self.adapter, self.config, self.project_root, args)
        out = self.project_root / ".test" / "commands" / "bare.md"
        content = out.read_text()
        # Should NOT have the header (description + ---)
        self.assertTrue(content.startswith("bare body"))

    def test_output_path_override(self):
        skill_path = self._write_skill(
            "custom", "custom body",
            output_path_override=".custom/output.md"
        )
        args = _make_args()
        sync.sync_skill(skill_path, self.adapter, self.config, self.project_root, args)
        out = self.project_root / ".custom" / "output.md"
        self.assertTrue(out.exists())
        # Default path should NOT exist
        default_out = self.project_root / ".test" / "commands" / "custom.md"
        self.assertFalse(default_out.exists())

    def test_skips_non_generated_existing_file(self):
        """If a file exists but has no sync marker, skip without --force."""
        out_dir = self.project_root / ".test" / "commands"
        out_dir.mkdir(parents=True)
        out = out_dir / "demo.md"
        out.write_text("User-created file, no marker.\n")

        skill_path = self._write_skill("demo", "new content")
        args = _make_args()
        result = sync.sync_skill(skill_path, self.adapter, self.config, self.project_root, args)
        self.assertFalse(result)
        self.assertIn("User-created file", out.read_text())

    def test_regenerates_when_source_changes(self):
        """If source skill changes but output wasn't customized, regenerate."""
        skill_path = self._write_skill("demo", "version-1")
        args = _make_args()
        sync.sync_skill(skill_path, self.adapter, self.config, self.project_root, args)

        # Update source (rewrite the skill file)
        skill_path.write_text(skill_path.read_text().replace("version-1", "version-2"))

        sync.sync_skill(skill_path, self.adapter, self.config, self.project_root, args)
        out = self.project_root / ".test" / "commands" / "demo.md"
        self.assertIn("version-2", out.read_text())


# ═══════════════════════════════════════════════════════════════════════════════
# VALIDATION
# ═══════════════════════════════════════════════════════════════════════════════


class TestValidatePlaceholders(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_no_errors_when_all_defined(self):
        path = _make_skill(self.tmpdir, "ok", 'skill: ok\ndescription: "test"', "Use {{FOO}}")
        errors = sync.validate_placeholders([path], {"FOO": "bar"})
        self.assertEqual(errors, [])

    def test_reports_undefined_placeholder(self):
        path = _make_skill(self.tmpdir, "bad", 'skill: bad\ndescription: "test"', "Use {{MISSING}}")
        errors = sync.validate_placeholders([path], {})
        self.assertEqual(len(errors), 1)
        self.assertIn("MISSING", errors[0])

    def test_placeholder_in_stripped_conditional_not_reported(self):
        body = "{{#if ACTIVE}}\n{{OPTIONAL}}\n{{/if}}\nPlain text."
        path = _make_skill(self.tmpdir, "cond", 'skill: cond\ndescription: "test"', body)
        # ACTIVE is falsy → the block is stripped → OPTIONAL should not be reported
        errors = sync.validate_placeholders([path], {"ACTIVE": ""})
        self.assertEqual(errors, [])

    def test_placeholder_in_kept_conditional_reported(self):
        body = "{{#if ACTIVE}}\n{{OPTIONAL}}\n{{/if}}"
        path = _make_skill(self.tmpdir, "cond", 'skill: cond\ndescription: "test"', body)
        # ACTIVE is truthy → OPTIONAL is in final output → should be reported
        errors = sync.validate_placeholders([path], {"ACTIVE": "yes"})
        self.assertEqual(len(errors), 1)
        self.assertIn("OPTIONAL", errors[0])

    def test_description_placeholders_checked(self):
        path = _make_skill(
            self.tmpdir, "desc",
            'skill: desc\ndescription: "Uses {{UNDEFINED}}"',
            "Body is fine."
        )
        errors = sync.validate_placeholders([path], {})
        self.assertEqual(len(errors), 1)
        self.assertIn("UNDEFINED", errors[0])


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN / CLI INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════════


class TestMainCLI(unittest.TestCase):
    """Test main() behavior via subprocess or sys.exit interception."""

    def setUp(self):
        self._original_cwd = os.getcwd()

    def tearDown(self):
        os.chdir(self._original_cwd)

    def _chdir_to_project(self):
        """Change to the project root if .codecannon.yaml exists, else skip."""
        if not (REPO_ROOT / ".codecannon.yaml").exists():
            self.skipTest(".codecannon.yaml not found in repo root")
        os.chdir(REPO_ROOT)

    def test_missing_config_exits_1(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("sys.argv", ["sync.py", "--config", os.path.join(tmpdir, "nope.yaml")]):
                with self.assertRaises(SystemExit) as ctx:
                    sync.main()
                self.assertEqual(ctx.exception.code, 1)

    def test_validate_with_real_config(self):
        """Running --validate against the real project config should pass."""
        self._chdir_to_project()
        with patch("sys.argv", ["sync.py", "--validate"]):
            sync.main()

    def test_dry_run_with_real_config(self):
        """Running --dry-run against the real project should exit 0 (no drift) or 1 (drift)."""
        self._chdir_to_project()
        with patch("sys.argv", ["sync.py", "--dry-run"]):
            try:
                sync.main()
            except SystemExit as e:
                self.assertIn(e.code, (None, 0, 1))

    def test_no_adapters_exits_1(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = Path(tmpdir) / "empty.yaml"
            cfg.write_text("config:\n  FOO: bar\n")
            os.chdir(tmpdir)
            with patch("sys.argv", ["sync.py", "--config", str(cfg)]):
                with self.assertRaises(SystemExit) as ctx:
                    sync.main()
                self.assertEqual(ctx.exception.code, 1)

    def test_skill_filter(self):
        """--skill flag should restrict which skills are synced."""
        self._chdir_to_project()
        with patch("sys.argv", ["sync.py", "--dry-run", "--skill", "checkpoint"]):
            try:
                sync.main()
            except SystemExit:
                pass  # acceptable

    def test_nonexistent_skill_filter_exits_1(self):
        self._chdir_to_project()
        with patch("sys.argv", ["sync.py", "--dry-run", "--skill", "nonexistent_skill_xyz"]):
            with self.assertRaises(SystemExit) as ctx:
                sync.main()
            self.assertEqual(ctx.exception.code, 1)

    def test_missing_skill_group_exits_1(self):
        """Config without a skill_group entry should fail loudly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = Path(tmpdir) / "nogroup.yaml"
            cfg.write_text("adapters:\n  - claude\nconfig:\n  FOO: bar\n")
            os.chdir(tmpdir)
            with patch("sys.argv", ["sync.py", "--config", str(cfg)]):
                with self.assertRaises(SystemExit) as ctx:
                    sync.main()
                self.assertEqual(ctx.exception.code, 1)

    def test_nonexistent_skill_group_exits_1(self):
        """skill_group naming a directory that doesn't exist should fail loudly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = Path(tmpdir) / "badgroup.yaml"
            cfg.write_text("skill_group: does-not-exist\nadapters:\n  - claude\nconfig:\n  FOO: bar\n")
            os.chdir(tmpdir)
            with patch("sys.argv", ["sync.py", "--config", str(cfg)]):
                with self.assertRaises(SystemExit) as ctx:
                    sync.main()
                self.assertEqual(ctx.exception.code, 1)


# ═══════════════════════════════════════════════════════════════════════════════
# GOLDEN-FILE SNAPSHOT TESTS
# ═══════════════════════════════════════════════════════════════════════════════


class TestGoldenFileSnapshots(unittest.TestCase):
    """Verify that sync output for each adapter matches what's already on disk.

    This is a regression test: if a skill template or the sync engine changes,
    the on-disk output should also be updated (via ./sync.py). If it drifts,
    these tests catch it — same as the CI dry-run check, but at unittest level.

    Uses sync_skill to render into a temp directory, then compares against
    the on-disk files. This avoids duplicating the rendering pipeline.
    """

    def test_all_generated_files_are_current(self):
        """Every generated file on disk should match what sync would produce today."""
        import shutil

        project_root = REPO_ROOT
        config_path = project_root / ".codecannon.yaml"
        if not config_path.exists():
            self.skipTest(".codecannon.yaml not found")

        raw_config = sync.parse_yaml_simple(config_path.read_text())
        adapters_list = raw_config.get("adapters", [])
        project_config = raw_config.get("config", {})
        project_config.setdefault("TICKET_LABEL_CREATION_ALLOWED", "false")
        skill_group = raw_config.get("skill_group", "")
        if not skill_group:
            self.skipTest("skill_group not set in .codecannon.yaml")

        skills_dir = REPO_ROOT / "skills" / skill_group
        skill_files = sorted(skills_dir.glob("*.md"))
        args = _make_args()

        tmpdir = Path(tempfile.mkdtemp())
        try:
            stale = []
            for adapter_name in adapters_list:
                adapter = sync.load_adapter(adapter_name)
                if not adapter:
                    continue
                for skill_path in skill_files:
                    # Render via sync_skill into the temp directory
                    sync.sync_skill(skill_path, adapter, project_config, tmpdir, args)

                    # Determine the output path (mirrors sync_skill logic)
                    raw = skill_path.read_text()
                    fm, _ = sync.parse_frontmatter(raw)
                    skill_name = fm.get("skill", skill_path.stem)
                    output_path_override = fm.get("output_path_override", "")
                    if output_path_override:
                        output_path_override = sync.apply_placeholders(output_path_override, project_config)
                        fresh_path = tmpdir / output_path_override
                        disk_path = project_root / output_path_override
                    else:
                        ext = adapter["output_extension"]
                        fresh_path = tmpdir / adapter["output_directory"] / f"{skill_name}{ext}"
                        disk_path = project_root / adapter["output_directory"] / f"{skill_name}{ext}"

                    if not disk_path.exists():
                        stale.append(f"{adapter_name}/{skill_name}: file missing at {disk_path}")
                        continue

                    if not fresh_path.exists():
                        continue  # sync_skill decided not to write (shouldn't happen on fresh dir)

                    if fresh_path.read_text() != disk_path.read_text():
                        stale.append(f"{adapter_name}/{skill_name}: content differs from freshly rendered output")
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

        if stale:
            self.fail(
                "Generated files are out of date. Run ./sync.py to regenerate.\n"
                + "\n".join(f"  - {s}" for s in stale)
            )


# ═══════════════════════════════════════════════════════════════════════════════
# SYNC-BASE-BRANCH SCRIPT
# ═══════════════════════════════════════════════════════════════════════════════


class TestSyncBaseBranchScript(unittest.TestCase):
    """Exit-code behavior of skills/github-agile/scripts/sync-base-branch.py.

    The script is mechanical — these tests cover the user-visible contract
    (exit codes, dirty-tree guard) without exercising real network operations.
    """

    SCRIPT = REPO_ROOT / "skills" / "github-agile" / "scripts" / "sync-base-branch.py"

    def _git(self, repo, *args):
        subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)

    def _init_repo(self, repo):
        """Initialize a tiny git repo with one committed file on branch 'main'."""
        self._git(repo, "init", "-q", "-b", "main")
        self._git(repo, "config", "user.email", "test@example.com")
        self._git(repo, "config", "user.name", "Test")
        (repo / "README").write_text("hello\n")
        self._git(repo, "add", "README")
        self._git(repo, "commit", "-q", "-m", "init")

    def _run(self, repo, *args):
        return subprocess.run(
            [sys.executable, str(self.SCRIPT), *args],
            cwd=str(repo),
            capture_output=True,
            text=True,
        )

    def test_missing_argument_exits_3(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self._run(Path(tmp))
        self.assertEqual(result.returncode, 3)
        self.assertIn("Usage", result.stderr)

    def test_empty_argument_exits_3(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self._run(Path(tmp), "")
        self.assertEqual(result.returncode, 3)

    def test_dirty_unstaged_tree_exits_1(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            (repo / "README").write_text("dirty\n")  # unstaged change
            result = self._run(repo, "main")
        self.assertEqual(result.returncode, 1)
        self.assertIn("Uncommitted changes", result.stderr)

    def test_dirty_staged_tree_exits_1(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            (repo / "new").write_text("staged\n")
            self._git(repo, "add", "new")  # staged but not committed
            result = self._run(repo, "main")
        self.assertEqual(result.returncode, 1)

    def test_clean_tree_no_remote_exits_2(self):
        """With a clean tree but no `origin` remote, git fetch fails — exit 2."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            result = self._run(repo, "main")
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
