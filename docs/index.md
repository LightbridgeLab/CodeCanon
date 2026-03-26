# Code Cannon Documentation

Code Cannon is a portable agent workflow skill library. Write your team's development workflow once — start, ship, review, version, release — and sync it to Claude Code, Cursor, and other AI coding agents across all your projects.

## How it works

1. **Skills** live in `skills/` as plain markdown with `{{PLACEHOLDER}}` tokens for project-specific values.
2. **`sync.sh`** reads your project config (`.codecannon.yaml`), substitutes values, wraps each skill in an agent-specific invocation header, and writes the generated files to the right place (`.claude/commands/`, `.cursor/rules/`, etc.).
3. **Generated files** carry a hash so sync.sh can detect manual edits and warn before overwriting.

## The workflow

The intended sequence for a complete change:

```
/start  →  [code + local test]  →  /ship  →  [QA on preview]  →  /version  →  /release
```

- [`/start`](skills/start.md) — reads code, proposes an approach, **waits for human approval**, then creates the issue, branch, and writes code
- [`/ship`](skills/ship.md) — runs checks, commits everything, pushes, opens the PR, spawns an agent review, merges if approved
- [`/review`](skills/review.md) — standalone review on any PR; also called internally by `/ship`
- [`/version`](skills/version.md) — bumps semver, tags, pushes
- [`/release`](skills/release.md) — promotes to production, creates a GitHub Release, closes issues
- [`/status`](skills/status.md) — read-only snapshot of open PRs, merged work, and open issues
- [`/qa`](skills/qa.md) — view the QA queue or record findings on a specific issue
- [`/setup`](skills/setup.md) — first-run onboarding: check config, labels, and milestone setup

## Human gates

Code Cannon is opinionated about where humans stay in the loop:

- `/start` pauses before creating the issue to confirm the implementation approach.
- `/release` requires an explicit "release" confirmation before promoting to production.
- `/qa` shows the review comment and waits for approval before posting.
- Everything else runs unattended.

The agent commits; you test. `/start` writes code but does not commit — it hands off to you with "run your dev command and test locally." Committing happens in `/ship`. The human approval loop before shipping is where you catch things the agent missed.

## Quickstart

### 1. Add Code Cannon as a submodule

```bash
git submodule add https://github.com/LightbridgeLab/CodeCannon.git CodeCannon
git submodule update --init
```

### 2. Create your project config

```bash
cp CodeCannon/templates/codecannon.yaml .codecannon.yaml
```

Edit `.codecannon.yaml` — set your branch names, check command, deploy commands, and which adapters to generate. See the [config reference](config-reference.md) for all available settings.

### 3. Run sync

```bash
CodeCannon/sync.sh
```

This generates skill files for each adapter listed in your config. For Claude Code, that's `.claude/commands/*.md`. For Cursor, `.cursor/rules/*.mdc`.

### 4. Copy AGENTS.md template (optional)

```bash
cp CodeCannon/templates/AGENTS.md.template AGENTS.md
```

Edit the project-specific section at the bottom.

### 5. Add Makefile targets (optional)

```makefile
# In your Makefile
include CodeCannon/Makefile.agents.mk
```

Or copy the targets from `Makefile.agents.mk` directly.

### 6. Commit and share

Commit `.codecannon.yaml`, `AGENTS.md`, and the generated `.claude/` directory. Every teammate gets a working installation on `git clone` + `git submodule update --init` — no further setup needed.

`.codecannon.yaml` is a team contract, not personal config. Changes to it should be reviewed like any other config change.

Or skip all of this and run `/setup` for a guided walkthrough.

## Keeping skills up to date

```bash
git submodule update --remote CodeCannon   # pull latest skills
CodeCannon/sync.sh                         # regenerate skill files
```

If any generated files have been manually customized, sync.sh will warn and skip them. Use `--force` to overwrite.

## Migrating from the old `agentgate` submodule

If your project still uses the previous repo URL or folder name:

1. Point `.gitmodules` at `https://github.com/LightbridgeLab/CodeCannon.git` and use submodule path `CodeCannon/` (or rename your existing checkout to match).
2. Rename `.agentgate.yaml` to `.codecannon.yaml`.
3. Run `CodeCannon/sync.sh --force` once if needed so generated file headers match the new provenance marker.

## Further reading

- [Branching models](branching.md) — trunk, two-branch, and three-branch workflows explained
- [Customization guide](customization.md) — how to tailor skills to your project
- [Config reference](config-reference.md) — every `.codecannon.yaml` placeholder documented
- [Adapters](adapters.md) — supported agents and how to add new ones
- Individual skill documentation — see links in the workflow section above
