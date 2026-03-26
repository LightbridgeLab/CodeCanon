# Adapters

Adapters translate Code Cannon's generic skill format into agent-specific file formats. Each adapter defines an output directory, file extension, and invocation header.

## Supported adapters

| Adapter | Output | Notes |
|---|---|---|
| `claude` | `.claude/commands/*.md` | Full feature support including sub-agent spawning |
| `cursor` | `.cursor/rules/*.mdc` | Agent-requested rules; sub-agent spawning not supported |
| `codex` | `.agents/skills/*/SKILL.md` | Codex CLI skills; sub-agent spawning not supported |
| `gemini` | `.gemini/skills/*/SKILL.md` | Gemini CLI skills; sub-agent spawning not supported |

### Claude Code

The Claude adapter generates slash commands in `.claude/commands/`. Users invoke skills with `/skill-name` in Claude Code. The `/ship` skill can spawn a review sub-agent natively.

### Cursor

The Cursor adapter generates agent-requested rules in `.cursor/rules/`. Users trigger rules via `@rulename` in Agent mode, or the agent requests them by description.

**Limitation:** Cursor does not support sub-agent spawning. The review step in `/ship` (which spawns a separate review agent) must be performed manually by pasting the review-agent prompt into a new chat.

### Codex CLI

The Codex adapter generates agent skills in `.agents/skills/`. Each skill gets its own directory with a `SKILL.md` file containing YAML frontmatter (`name` and `description`). Skills are triggered by description matching during conversation or via the `$skill-creator` built-in.

**Limitation:** Codex CLI does not support sub-agent spawning. The review step in `/ship` must be performed manually by pasting the review-agent prompt into a new session.

### Gemini CLI

The Gemini adapter generates agent skills in `.gemini/skills/`. Each skill gets its own directory with a `SKILL.md` file containing YAML frontmatter (`name` and `description`). Skills are triggered by description matching during conversation.

**Limitation:** Gemini CLI does not support sub-agent spawning. The review step in `/ship` must be performed manually by pasting the review-agent prompt into a new session.

## Enabling adapters

List the adapters you want in `.codecannon.yaml`:

```yaml
adapters:
  - claude
  - cursor
  - codex
  - gemini
```

Run `sync.sh` to generate files for all listed adapters. You can enable both simultaneously — they write to different directories and don't conflict.

## How adapters work

Each adapter lives in `adapters/<name>/` and contains:

- **`config.yaml`** — defines `output_directory` and `output_extension`
- **`header.md`** — the invocation header template prepended to each generated skill file

The header template uses `{skill}` and `{description}` as placeholders (distinct from the `{{CONFIG}}` placeholders used in skill bodies).

## Adding a new adapter

To support a new AI coding agent:

1. Create `adapters/<name>/config.yaml`:
   ```yaml
   agent: <name>
   description: <one-line description>
   output_directory: <where generated files go>
   output_extension: <file extension>
   ```

2. Create `adapters/<name>/header.md` — the invocation header that tells the agent how to interpret the skill. Use `{skill}` and `{description}` as placeholders for the skill name and description.

3. Test with `sync.sh --skill start` against a test project.

4. Document any adapter limitations in `config.yaml` under `notes`.

5. Add the adapter name to `adapters:` in `.codecannon.yaml` for any project that should use it.
