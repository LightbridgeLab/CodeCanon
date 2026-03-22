# agentgate

A portable agent workflow skill library. Write your team's development workflow once — start, ship, review, version, release — and sync it to Claude Code, Cursor, and other AI coding agents across all your projects.

## How it works

1. Skills live in `skills/` as plain markdown with `{{PLACEHOLDER}}` tokens for project-specific values.
2. `sync.sh` reads your project config, substitutes values, wraps each skill in an agent-specific invocation header, and writes the generated files to the right place (`.claude/commands/`, `.cursor/rules/`, etc.).
3. Generated files carry a hash so sync.sh can detect manual edits and warn before overwriting.

## Quickstart

### 1. Add agentgate as a submodule

```bash
git submodule add https://github.com/LightbridgeLab/agentgate.git agentgate
git submodule update --init
```

### 2. Create your project config

```bash
cp agentgate/templates/agentgate.yaml .agentgate.yaml
```

Edit `.agentgate.yaml` — set your branch names, check command, deploy commands, and which adapters to generate.

### 3. Run sync

```bash
agentgate/sync.sh
```

This generates skill files for each adapter listed in your config. For Claude Code, that's `.claude/commands/*.md`. For Cursor, `.cursor/rules/*.mdc`.

### 4. Copy AGENTS.md template (optional)

```bash
cp agentgate/templates/AGENTS.md.template AGENTS.md
```

Edit the project-specific section at the bottom.

### 5. Add Makefile targets (optional)

```makefile
# In your Makefile
include agentgate/Makefile.agents.mk
```

Or copy the targets from `Makefile.agents.mk` directly.

## Keeping skills up to date

```bash
git submodule update --remote agentgate   # pull latest skills from agentgate
agentgate/sync.sh                         # regenerate skill files
```

If any generated files have been manually customized, sync.sh will warn and skip them. Use `--force` to overwrite.

## Customizing the review agent prompt

The review agent prompt (`skills/review-agent.md`) is generated to the path set in `REVIEW_AGENT_PROMPT` in your config. After first sync, open that file and fill in the **Platform Compliance** and **Conventions** sections for your stack — these are the only parts that should be project-specific.

The file's hash comment will change after your edits, so future syncs will warn before overwriting it (by design).

## sync.sh reference

```
./agentgate/sync.sh [options]

Options:
  --config path     Project config file (default: .agentgate.yaml)
  --force           Overwrite customized files without prompting
  --dry-run         Preview what would be written, no changes made
  --skill name,...  Sync only specific skill(s), comma-separated
```

## Included skills

| Skill | Description |
|---|---|
| `start` | Start a new feature: create a GitHub issue, branch, and write code |
| `ship` | Type-check, commit, open PR, spawn review agent, merge |
| `review` | Standalone code review on a PR |
| `version` | Bump version, tag, push — run before deploying to preview |
| `release` | Promote integration branch to main, close issues, prep for prod deploy |
| `review-agent` | Code review agent system prompt (used by `ship` and `review`) |

## Supported adapters

| Adapter | Output | Notes |
|---|---|---|
| `claude` | `.claude/commands/*.md` | Full feature support including sub-agent spawning |
| `cursor` | `.cursor/rules/*.mdc` | Agent-requested rules; sub-agent spawning not supported |

## Config reference

See `config.schema.yaml` for all available `{{PLACEHOLDERS}}` with descriptions and defaults.

## Adding your project's conventions

After running sync, add project-specific sections to `AGENTS.md` (below the separator line) — architecture notes, coding conventions, platform gotchas. These are not managed by agentgate and won't be overwritten.

## Legacy: template-repo usage

The original agentgate workflow (AGENTS.md + `.agents/config.yaml` + `Makefile.agents.mk`) still works for projects that prefer to copy files rather than use a submodule. See `.agents/` for those files.

## License

MIT
