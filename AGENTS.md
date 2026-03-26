# AGENTS.md — Code Cannon

Instructions for AI coding agents working on the Code Cannon project itself.

Code Cannon is a skill distribution system. It stores generic agent workflow skills in `skills/`, adapter configs in `adapters/`, and a `sync.sh` script that generates agent-specific skill files for downstream projects.

## Branch Strategy

```
feature/* → development → main
```

- `main` — published releases. Never push directly.
- `development` — integration. Never push directly.
- `feature/*` — short-lived. Branch from `development`, PR back.

## Working on Code Cannon

### Editing skills

Skills live in `skills/*.md`. Each file has YAML frontmatter followed by the skill body. Placeholder tokens use `{{UPPERCASE_NAME}}` syntax and are documented in `config.schema.yaml`.

When editing a skill:
1. Edit the `.md` file in `skills/`.
2. Test locally by running sync against the APrimeforYou project (a known consumer): `cd ../APrimeforYou && CodeCannon/sync.sh --dry-run`
3. Verify generated output looks correct before committing.

### Adding a new adapter

1. Create `adapters/{name}/config.yaml` — set `output_directory` and `output_extension`.
2. Create `adapters/{name}/header.md` — the invocation header template. Use `{skill}` and `{description}` as placeholders.
3. Test with `sync.sh --skill start` against a test project.
4. Document any adapter limitations in `config.yaml` under `notes`.

### Adding a new placeholder

1. Add it to `config.schema.yaml` with description, default, and `used_in` list.
2. Add it with its default value to `templates/codecannon.yaml`.
3. Use `{{PLACEHOLDER_NAME}}` in the relevant skill files.

### Testing sync.sh

```bash
cd /path/to/a/consumer/project
../CodeCannon/sync.sh --dry-run       # verify output paths and content
../CodeCannon/sync.sh                 # generate for real
```

## Self-hosting: using Code Cannon to develop Code Cannon

- **Sync path exception**: agents working on this repo run `./sync.sh`, not `CodeCannon/sync.sh`. Every consumer project uses `CodeCannon/sync.sh` via the submodule path — this repo is the only exception.
- **Edit-test loop**: edit a skill in `skills/` → `make check` to validate placeholders → `make dev` to preview generated output → commit and `/submit-for-review`.
- **Re-run sync after skill edits**: after changing any file in `skills/`, run `./sync.sh` to regenerate `.claude/commands/`. Commit the updated generated files in the same PR as the skill source change.
- **Never edit `.claude/commands/` directly** — those files are generated. Edit the source skill in `skills/` and re-run sync.

## What Agents Must Never Do

- Push directly to `main` or `development`
- Edit generated files in consumer projects — edit the source skill instead
- Add project-specific content to `skills/` — skills must remain generic (use placeholders)

## Project Layout

```
skills/           source skill files (edit here)
adapters/         per-agent adapter configs and header templates
templates/        files for downstream projects to copy
config.schema.yaml  placeholder documentation
sync.sh           the installer / generator
Makefile.agents.mk  generic git workflow Makefile targets
AGENTS.md         this file
README.md         human-facing docs
.agents/          legacy workflow files (still functional for template-repo usage)
```
