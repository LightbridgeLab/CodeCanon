![Code Cannon](.github/assets/readme-header.png)

# Code Cannon

A portable agent workflow skill library. Write your team's development workflow once — start, ship, review, version, release — and sync it to Claude Code, Cursor, and other AI coding agents across all your projects.

Repository: [github.com/LightbridgeLab/CodeCanon](https://github.com/LightbridgeLab/CodeCanon)

## How it works

1. Skills live in `skills/` as plain markdown with `{{PLACEHOLDER}}` tokens for project-specific values.
2. `sync.sh` reads your project config, substitutes values, wraps each skill in an agent-specific invocation header, and writes the generated files to the right place (`.claude/commands/`, `.cursor/rules/`, etc.).
3. Generated files carry a hash so sync.sh can detect manual edits and warn before overwriting.

## Workflow model

Before configuring anything, understand the assumptions these skills encode.

**GitHub only.** Every skill uses the `gh` CLI. GitLab, Gitea, and Bitbucket are not supported (yet).

**Every session has a ticket.** `/start` either creates a new GitHub issue or resumes an existing one by number. There is no path for committing code without an issue. The issue is the unit of work — the branch, PR, and commit history all link back to it.

**Branching model.** Three models are supported — set `BRANCH_DEV` and `BRANCH_TEST` in `.codecannon.yaml` to match your workflow:

```
# Trunk-based (BRANCH_DEV and BRANCH_TEST empty):
feature/<name>  →  BRANCH_PROD (default: main)
    /start           /ship merges here; /version and /release run here

# Two-branch (BRANCH_DEV set):
feature/<name>  →  BRANCH_DEV  →  BRANCH_PROD
    /start           /ship           /release

# Three-branch (BRANCH_DEV and BRANCH_TEST set):
feature/<name>  →  BRANCH_DEV  →  BRANCH_TEST  →  BRANCH_PROD
    /start           /ship        manual/future       /release
                                   /promote
```

**All three models are supported.** Set `BRANCH_DEV` and `BRANCH_TEST` in `.codecannon.yaml` to match your workflow. Leave both empty for trunk-based development. Trunk mode is the default when no dev branch is configured.

In two-branch mode, feature PRs target `BRANCH_DEV`. Issues deliberately stay open through this merge — `Closes #N` is not used on feature PRs because they don't land in the default branch. Issues only auto-close when `/release` promotes to `BRANCH_PROD`. This supports a QA gate between merging code and shipping to production.

In trunk mode, feature PRs target `BRANCH_PROD` directly and use `Closes #N` — issues auto-close on merge.

## Choose your workflow

Code Cannon adapts to your process, not your team size. Run `/setup` for a guided walkthrough, or configure `.codecannon.yaml` manually. Common profiles:

| Profile | Branch model | AI review | QA flow | Reviewers | Good for |
|---|---|---|---|---|---|
| **Lightweight** | Trunk | Advisory (posts but doesn't block) | Off | None | Fast iteration, low ceremony |
| **Standard** | Two-branch | Blocks merge | Optional | Optional | Review-gated development |
| **Governed** | Two or three-branch | Blocks merge | On | Assigned | Full traceability and QA handoff |

These aren't rigid modes — they're starting points. Every setting is independently configurable.

**The intended sequence for a complete change:**

```
/start  →  [code + local test]  →  /ship  →  [QA on preview]  →  /version  →  /release
```

- `/start` — reads code, proposes an approach, **waits for human approval**, then creates the issue, branch, and writes code
- `/ship` — runs `CHECK_CMD`, commits everything, pushes, opens the PR, spawns an agent review, merges if approved; runs from a feature branch
- `/version` — bumps semver, tags, pushes; runs from the pre-production branch (determined by mode) after features are merged
- `/release` — in two/three-branch mode, opens a promotion PR to `BRANCH_PROD`, **waits for human to type "release"**, merges, creates a GitHub Release, closes issues; in trunk mode, creates the GitHub Release directly from `BRANCH_PROD`
- `/review` — standalone review on any PR; also called internally by `/ship`
- `/status` — read-only snapshot: open PRs, recently merged PRs, and open issues for a user (defaults to `@me`, scoped to the current repo)

**Human gates.** `/start` pauses before creating the issue to confirm the implementation approach. `/release` requires an explicit "release" confirmation. Everything else runs unattended.

**Branch discipline is enforced.** `/ship` aborts if run from any protected branch (`BRANCH_PROD`, `BRANCH_DEV`, or `BRANCH_TEST` when set). `/version` aborts if not on the required pre-production branch (determined by mode). The agent will not proceed past these checks.

**Milestone assignment is automatic.** When `/start` creates an issue it resolves the active milestone in order: per-invocation `--milestone` flag → `DEFAULT_MILESTONE` config → open milestones queried from GitHub. If one open milestone exists it's used silently; if multiple exist you're prompted once; if none exist the issue is created without one. Set `DEFAULT_MILESTONE` only if you want to pin a value and skip detection.

**Reviewer selection is never automatic.** `/ship` adds reviewers only from two sources: a detected `CODEOWNERS` file (checked in `CODEOWNERS`, `.github/CODEOWNERS`, and `docs/CODEOWNERS`) and the `DEFAULT_REVIEWERS` config key. The agent never infers reviewers from git history, blame, or team membership.

**The agent commits; you test.** `/start` writes code but does not commit — it hands off to you with "run `DEV_CMD` and test locally." Committing happens in `/ship`. This is intentional: the human approval loop before shipping is where you catch things the agent missed.

## Quickstart

### 1. Add Code Cannon as a submodule

```bash
git submodule add https://github.com/LightbridgeLab/CodeCanon.git CodeCanon
git submodule update --init
```

### 2. Create your project config

```bash
cp CodeCanon/templates/codecannon.yaml .codecannon.yaml
```

Edit `.codecannon.yaml` — set your branch names, check command, deploy commands, and which adapters to generate.

### 3. Run sync

```bash
CodeCanon/sync.sh
```

This generates skill files for each adapter listed in your config. For Claude Code, that's `.claude/commands/*.md`. For Cursor, `.cursor/rules/*.mdc`.

### 4. Copy AGENTS.md template (optional)

```bash
cp CodeCanon/templates/AGENTS.md.template AGENTS.md
```

Edit the project-specific section at the bottom.

### 5. Add Makefile targets (optional)

```makefile
# In your Makefile
include CodeCanon/Makefile.agents.mk
```

Or copy the targets from `Makefile.agents.mk` directly.

### 6. Commit and share

Commit `.codecannon.yaml`, `AGENTS.md`, and the generated `.claude/` directory. Every teammate gets a working installation on `git clone` + `git submodule update --init` — no further setup needed.

`.codecannon.yaml` is a team contract, not personal config. Changes to it should be reviewed like any other config change.

## Keeping skills up to date

```bash
git submodule update --remote CodeCanon   # pull latest skills
CodeCanon/sync.sh                         # regenerate skill files
```

If any generated files have been manually customized, sync.sh will warn and skip them. Use `--force` to overwrite.

## Migrating from the old `agentgate` submodule

If your project still uses the previous repo URL or folder name:

1. Point `.gitmodules` at `https://github.com/LightbridgeLab/CodeCanon.git` and use submodule path `CodeCanon/` (or rename your existing checkout to match).
2. Rename `.agentgate.yaml` → `.codecannon.yaml`.
3. Run `CodeCanon/sync.sh --force` once if needed so generated file headers match the new provenance marker.

## Customizing the review agent

The review agent prompt is generated to the path in `REVIEW_AGENT_PROMPT`. Two config keys make it project-aware — set them in `.codecannon.yaml` and re-run sync:

`**PLATFORM_COMPLIANCE_NOTES**` — infrastructure and framework rules that are easy to get wrong and hard to catch in tests. Examples:

- `Postgres: use parameterized queries via the ORM; never raw string interpolation`
- `Redis: TTLs required on all keys written in request handlers`
- `Next.js: server components must not import client-only modules`

`**CONVENTIONS_NOTES**` — non-obvious team rules that differ from common defaults. Examples:

- `API logic in services/, UI in app/ — no business logic in components`
- `Use the design system tokens — no hardcoded hex values`
- `Feature flags via the flags/ module only; no ad-hoc env var checks`

These are the primary way Code Cannon becomes project-aware rather than a generic tool. Until set, both sections default to an HTML comment (invisible to agents, visible to you as a nudge). Use YAML block scalars for multi-line content:

```yaml
CONVENTIONS_NOTES: |
  - Rule one
  - Rule two
```

## sync.sh reference

```
./CodeCanon/sync.sh [options]

Options:
  --config path     Project config file (default: .codecannon.yaml)
  --force           Overwrite customized files without prompting
  --dry-run         Preview what would be written, no changes made
  --skill name,...  Sync only specific skill(s), comma-separated
```

## Included skills


| Skill          | Description                                                                                                          |
| -------------- | -------------------------------------------------------------------------------------------------------------------- |
| `start`        | Start a new feature: create a GitHub issue, branch, and write code                                                   |
| `ship`         | Type-check, commit, open PR, spawn review agent, merge                                                               |
| `review`       | Standalone code review on a PR                                                                                       |
| `version`      | Bump version, tag, push — run before deploying to preview environment                                                |
| `release`      | Create GitHub Release; in two-branch and three-branch mode, also promotes the pre-production branch to `BRANCH_PROD` |
| `status`       | Snapshot of open PRs, recently merged work, and open issues                                                          |
| `qa`           | View the QA queue or record findings and apply a verdict label to a specific issue                                   |
| `setup`        | First-run onboarding: check config, labels, and milestone setup                                                      |
| `review-agent` | Code review agent system prompt (used by `ship` and `review`)                                                        |


## Supported adapters


| Adapter  | Output                  | Notes                                                   |
| -------- | ----------------------- | ------------------------------------------------------- |
| `claude` | `.claude/commands/*.md` | Full feature support including sub-agent spawning       |
| `cursor` | `.cursor/rules/*.mdc`   | Agent-requested rules; sub-agent spawning not supported |


## Config reference

See `config.schema.yaml` for all available `{{PLACEHOLDERS}}` with descriptions and defaults.

## Adding your project's conventions

After running sync, add project-specific sections to `AGENTS.md` (below the separator line) — architecture notes, coding conventions, platform gotchas. These are not managed by Code Cannon sync and won't be overwritten.

## Legacy: template-repo usage

The original copy-based workflow (AGENTS.md + `.agents/config.yaml` + `Makefile.agents.mk`) still works for projects that prefer to copy files rather than use a submodule. See `.agents/` for those files.

## License

MIT
