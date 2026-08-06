"""Exit-code contract tests for the extracted github-agile scripts.

Each script under skills/github-agile/scripts/ wraps a permission-sensitive
gh/git sequence. These tests pin the documented exit codes — one success path
plus one case per documented non-zero exit — so a change to argument handling,
exit codes, or the guarded shell sequence can't drift unnoticed.

No network and no live gh/git: subprocess.run is mocked in-process (via a
patched module attribute) or the script runs in a temp directory. The scripts
have hyphenated filenames, so they are loaded by path rather than imported.
"""

import contextlib
import importlib.util
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "skills" / "github-agile" / "scripts"


def load_script(filename):
    """Load a hyphenated script file as a module object."""
    modname = "ccscript_" + filename.replace("-", "_").removesuffix(".py")
    spec = importlib.util.spec_from_file_location(modname, SCRIPTS_DIR / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# Load each script once.
make_workdir = load_script("make-workdir.py")
post_issue_comment = load_script("post-issue-comment.py")
sync_base_branch = load_script("sync-base-branch.py")
list_open_milestones = load_script("list-open-milestones.py")
list_sub_issues = load_script("list-sub-issues.py")
label_create = load_script("label-create.py")
label_audit = load_script("label-audit.py")
bump_and_tag = load_script("bump-and-tag.py")


class FakeProc:
    """Stand-in for subprocess.CompletedProcess."""

    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def call(mod, argv, run_results=None):
    """Run mod.main(argv) with stdout/stderr captured.

    If run_results is given, mod.subprocess.run is patched to return those
    FakeProcs in call order. Returns (exit_code, stdout, stderr, run_mock).
    """
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        if run_results is None:
            code = mod.main(argv)
            run_mock = None
        else:
            with patch.object(mod.subprocess, "run") as run_mock:
                run_mock.side_effect = run_results
                code = mod.main(argv)
    return code, out.getvalue(), err.getvalue(), run_mock


@contextlib.contextmanager
def chdir(path):
    old = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old)


class TestMakeWorkdir(unittest.TestCase):

    def test_success_prints_existing_path(self):
        code, out, _, _ = call(make_workdir, ["make-workdir.py"])
        self.assertEqual(code, 0)
        path = Path(out.strip())
        try:
            self.assertTrue(path.is_dir())
        finally:
            if path.is_dir():
                path.rmdir()

    def test_mkdtemp_failure_exits_2(self):
        with patch.object(make_workdir.tempfile, "mkdtemp", side_effect=OSError("boom")):
            code, _, err, _ = call(make_workdir, ["make-workdir.py"])
        self.assertEqual(code, 2)
        self.assertIn("could not create", err)


class TestPostIssueComment(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(lambda: __import__("shutil").rmtree(self.tmp, ignore_errors=True))
        self.body = Path(self.tmp) / "body.md"
        self.body.write_text("hello")

    def test_wrong_argc_exits_3(self):
        code, _, _, _ = call(post_issue_comment, ["p", "5"])
        self.assertEqual(code, 3)

    def test_non_digit_issue_exits_3(self):
        code, _, _, _ = call(post_issue_comment, ["p", "abc", str(self.body)])
        self.assertEqual(code, 3)

    def test_missing_body_file_exits_1(self):
        code, _, _, _ = call(post_issue_comment, ["p", "5", str(Path(self.tmp) / "nope.md")])
        self.assertEqual(code, 1)

    def test_empty_body_file_exits_1(self):
        empty = Path(self.tmp) / "empty.md"
        empty.write_text("")
        code, _, _, _ = call(post_issue_comment, ["p", "5", str(empty)])
        self.assertEqual(code, 1)

    def test_gh_failure_exits_2(self):
        code, _, _, _ = call(post_issue_comment, ["p", "5", str(self.body)], [FakeProc(1)])
        self.assertEqual(code, 2)

    def test_success_exits_0_and_builds_command(self):
        code, _, _, run_mock = call(
            post_issue_comment, ["p", "5", str(self.body)], [FakeProc(0)]
        )
        self.assertEqual(code, 0)
        cmd = run_mock.call_args.args[0]
        self.assertEqual(cmd, ["gh", "issue", "comment", "5", "--body-file", str(self.body)])


class TestSyncBaseBranch(unittest.TestCase):

    def test_wrong_argc_exits_3(self):
        code, _, _, _ = call(sync_base_branch, ["p"])
        self.assertEqual(code, 3)

    def test_empty_branch_exits_3(self):
        code, _, _, _ = call(sync_base_branch, ["p", ""])
        self.assertEqual(code, 3)

    def test_dirty_tree_exits_1(self):
        code, _, err, _ = call(sync_base_branch, ["p", "dev"], [FakeProc(0, stdout=" M foo\n")])
        self.assertEqual(code, 1)
        self.assertIn("not clean", err)

    def test_status_failure_exits_2(self):
        code, _, _, _ = call(sync_base_branch, ["p", "dev"], [FakeProc(1)])
        self.assertEqual(code, 2)

    def test_checkout_failure_exits_2(self):
        # status clean, then checkout fails.
        code, _, _, _ = call(
            sync_base_branch, ["p", "dev"], [FakeProc(0, stdout=""), FakeProc(1)]
        )
        self.assertEqual(code, 2)

    def test_success_exits_0(self):
        # status clean, then checkout, fetch, reset all succeed.
        code, _, _, _ = call(
            sync_base_branch,
            ["p", "dev"],
            [FakeProc(0, stdout=""), FakeProc(0), FakeProc(0), FakeProc(0)],
        )
        self.assertEqual(code, 0)


class TestListOpenMilestones(unittest.TestCase):

    def test_success_filters_open_only(self):
        payload = json.dumps([
            {"number": 1, "title": "Backlog", "state": "open"},
            {"number": 2, "title": "Done", "state": "closed"},
        ])
        code, out, _, _ = call(list_open_milestones, ["p"], [FakeProc(0, stdout=payload)])
        self.assertEqual(code, 0)
        parsed = json.loads(out)
        self.assertEqual(parsed["count"], 1)
        self.assertEqual(parsed["milestones"], [{"number": 1, "title": "Backlog"}])

    def test_gh_failure_exits_2(self):
        code, _, _, _ = call(list_open_milestones, ["p"], [FakeProc(1, stderr="boom")])
        self.assertEqual(code, 2)

    def test_unparseable_output_exits_2(self):
        code, _, _, _ = call(list_open_milestones, ["p"], [FakeProc(0, stdout="not json")])
        self.assertEqual(code, 2)


class TestListSubIssues(unittest.TestCase):

    def test_wrong_argc_exits_3(self):
        code, _, _, _ = call(list_sub_issues, ["p"])
        self.assertEqual(code, 3)

    def test_non_digit_parent_exits_3(self):
        code, _, _, _ = call(list_sub_issues, ["p", "abc"])
        self.assertEqual(code, 3)

    def test_success_exits_0(self):
        payload = json.dumps([{"number": 7, "title": "Sub", "state": "open"}])
        code, out, _, _ = call(list_sub_issues, ["p", "42"], [FakeProc(0, stdout=payload)])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out), [{"number": 7, "title": "Sub", "state": "open"}])

    def test_gh_failure_exits_2(self):
        code, _, _, _ = call(list_sub_issues, ["p", "42"], [FakeProc(1, stderr="boom")])
        self.assertEqual(code, 2)

    def test_unparseable_output_exits_2(self):
        code, _, _, _ = call(list_sub_issues, ["p", "42"], [FakeProc(0, stdout="{bad")])
        self.assertEqual(code, 2)


class TestLabelCreate(unittest.TestCase):

    def test_no_names_exits_3(self):
        code, _, _, _ = call(label_create, ["p"])
        self.assertEqual(code, 3)

    def test_success_exits_0(self):
        code, out, _, _ = call(label_create, ["p", "bug"], [FakeProc(0)])
        self.assertEqual(code, 0)
        self.assertIn("Created label: bug", out)

    def test_failed_label_warns_but_exits_0(self):
        # A single label that fails to create warns and the loop continues.
        code, _, err, _ = call(
            label_create, ["p", "bug", "chore"], [FakeProc(1, stderr="already exists"), FakeProc(0)]
        )
        self.assertEqual(code, 0)
        self.assertIn("Warning: failed to create label 'bug'", err)


class TestLabelAudit(unittest.TestCase):

    def _write_config(self, dirpath, config_body):
        (Path(dirpath) / ".codecannon.yaml").write_text(config_body)

    def test_missing_config_exits_1(self):
        with tempfile.TemporaryDirectory() as d, chdir(d):
            code, _, err, _ = call(label_audit, ["p"])
        self.assertEqual(code, 1)
        self.assertIn("not found", err)

    def test_no_configured_labels_exits_0(self):
        with tempfile.TemporaryDirectory() as d:
            self._write_config(d, "config:\n  BRANCH_PROD: main\n")
            with chdir(d):
                code, _, err, _ = call(label_audit, ["p"])
        self.assertEqual(code, 0)
        self.assertIn("audited 0 configured labels", err)

    def test_missing_labels_listed_exits_0(self):
        with tempfile.TemporaryDirectory() as d:
            self._write_config(d, 'config:\n  TICKET_LABELS: "bug, chore"\n')
            existing = json.dumps([{"name": "bug"}])
            with chdir(d):
                code, out, _, _ = call(label_audit, ["p"], [FakeProc(0, stdout=existing)])
        self.assertEqual(code, 0)
        self.assertEqual(out.strip(), "chore")

    def test_gh_failure_exits_2(self):
        with tempfile.TemporaryDirectory() as d:
            self._write_config(d, 'config:\n  TICKET_LABELS: "bug"\n')
            with chdir(d):
                code, _, _, _ = call(label_audit, ["p"], [FakeProc(1, stderr="boom")])
        self.assertEqual(code, 2)


class TestBumpAndTag(unittest.TestCase):

    ARGS = ["p", "--bump-cmd", "true", "--version-read-cmd", "true"]

    def test_bad_arguments_exit_2_via_argparse(self):
        # argparse intercepts missing required args and exits 2 (not the old
        # phantom exit 4). See the docstring correction in bump-and-tag.py.
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as ctx:
                bump_and_tag.main(["p"])
        self.assertEqual(ctx.exception.code, 2)

    def test_bump_failure_exits_1(self):
        code, _, _, _ = call(bump_and_tag, self.ARGS, [FakeProc(1)])
        self.assertEqual(code, 1)

    def test_version_read_failure_exits_2(self):
        code, _, _, _ = call(bump_and_tag, self.ARGS, [FakeProc(0), FakeProc(1, stderr="x")])
        self.assertEqual(code, 2)

    def test_empty_version_exits_2(self):
        code, _, _, _ = call(bump_and_tag, self.ARGS, [FakeProc(0), FakeProc(0, stdout="  ")])
        self.assertEqual(code, 2)

    def test_push_failure_exits_3(self):
        results = [
            FakeProc(0),                       # bump
            FakeProc(0, stdout="1.2.3"),       # version-read
            FakeProc(0, stdout="v1.2.3"),      # git tag -l (tag present)
            FakeProc(1),                       # git push fails
        ]
        code, _, _, _ = call(bump_and_tag, self.ARGS, results)
        self.assertEqual(code, 3)

    def test_success_exits_0_and_prints_version(self):
        results = [
            FakeProc(0),                       # bump
            FakeProc(0, stdout="1.2.3\n"),     # version-read
            FakeProc(0, stdout="v1.2.3"),      # git tag -l (tag present)
            FakeProc(0),                       # git push
            FakeProc(0),                       # git push --tags
        ]
        code, out, _, _ = call(bump_and_tag, self.ARGS, results)
        self.assertEqual(code, 0)
        self.assertEqual(out.strip(), "1.2.3")


if __name__ == "__main__":
    unittest.main()
