# AGENTS.md — agentgate

Instructions for AI coding agents working on the agentgate project itself.

agentgate is a skill distribution system. It stores generic agent workflow skills in `skills/`, adapter configs in `adapters/`, and a `sync.sh` script that generates agent-specific skill files for downstream projects.

## Branch Strategy

```
feature/* → development → main
```

- `main` — published releases. Never push directly.
- `development` — integration. Never push directly.
- `feature/*` — short-lived. Branch from `development`, PR back.

## Working on agentgate

### Editing skills

Skills live in `skills/*.md`. Each file has YAML frontmatter followed by the skill body. Placeholder tokens use `{{UPPERCASE_NAME}}` syntax and are documented in `config.schema.yaml`.

When editing a skill:
1. Edit the `.md` file in `skills/`.
2. Test locally by running sync against the APrimeforYou project (a known consumer): `cd ../APrimeforYou && agentgate/sync.sh --dry-run`
3. Verify generated output looks correct before committing.

### Adding a new adapter

1. Create `adapters/{name}/config.yaml` — set `output_directory` and `output_extension`.
2. Create `adapters/{name}/header.md` — the invocation header template. Use `{skill}` and `{description}` as placeholders.
3. Test with `sync.sh --skill start` against a test project.
4. Document any adapter limitations in `config.yaml` under `notes`.

### Adding a new placeholder

1. Add it to `config.schema.yaml` with description, default, and `used_in` list.
2. Add it with its default value to `templates/agentgate.yaml`.
3. Use `{{PLACEHOLDER_NAME}}` in the relevant skill files.

### Testing sync.sh

```bash
cd /path/to/a/consumer/project
../agentgate/sync.sh --dry-run       # verify output paths and content
../agentgate/sync.sh                 # generate for real
```

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
