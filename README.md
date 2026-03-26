![Code Cannon](.github/assets/readme-header.png)

# Code Cannon

A portable agent workflow skill library. Write your team's development workflow once — start, ship, review, deploy — and sync it to Claude Code, Cursor, and other AI coding agents across all your projects.

Repository: [github.com/LightbridgeLab/CodeCannon](https://github.com/LightbridgeLab/CodeCannon)

## The problem

AI coding agents are powerful, but every project reinvents the same workflows: how to create issues, open PRs, run reviews, bump versions, deploy releases. These instructions live in scattered prompt files, maintained per-project, per-agent, with no consistency and no reuse.

## The solution

Code Cannon is a shared skill library that lives as a git submodule. Skills are written once as portable markdown with placeholder tokens. A sync script reads your project config, substitutes values, and generates agent-specific command files for each AI tool your team uses.

```
skills/*.md  →  sync.sh + .codecannon.yaml  →  .claude/commands/*.md
                                              →  .cursor/rules/*.mdc
```

One source of truth. Every project. Every agent.

## What you get

**A complete development workflow in five commands:**

```
/start  →  [code + test]  →  /ship  →  [QA]  →  /deploy
```

- `/start` — creates a GitHub issue, feature branch, and writes code (with human approval before any work begins)
- `/ship` — checks, commits, opens PR, runs AI review, merges
- `/review` — standalone code review on any PR
- `/deploy` — bumps version, creates a GitHub Release, promotes to production
- `/status` — standup-ready snapshot of PRs, issues, and progress

Plus `/qa` for structured QA workflows and `/setup` for guided onboarding.

## Philosophy

**Humans stay in the loop.** The agent proposes; you approve. `/start` waits for your sign-off before creating anything. `/deploy` requires explicit confirmation. The agent commits; you test.

**Every change has a ticket.** There is no path for code without an issue. The issue is the unit of work — branch, PR, and release all link back to it.

## GitHub baseline for PM/BA setup

If your repo is new and you want predictable behavior from `/start` and `/qa`, configure a minimal GitHub baseline before day-to-day usage:

- **Starter labels for issue intake:** `bug`, `enhancement`, `chore`, `documentation`
- **QA lifecycle labels:** `ready-for-qa`, `qa-passed`, `qa-failed`
- **Optional planning labels:** a single priority scheme (for example `priority:high`, `priority:medium`, `priority:low`)

How this maps to Code Cannon behavior:

- `/start` uses `TICKET_LABELS` as its allowed label pool when creating issues.
- `/qa` depends on `QA_READY_LABEL` to build the QA queue and applies `QA_PASSED_LABEL` or `QA_FAILED_LABEL` as verdicts.
- Milestones can stay dynamic (auto-detected from GitHub open milestones) or be pinned using `DEFAULT_MILESTONE` when your team runs fixed iterations (for example `Sprint 12` or `Release 2026.04`).

For first-time setup, run `/setup`; it can populate labels and walk through these options interactively.

**Reviewer selection is never automatic.** `/ship` adds reviewers only from two sources: a detected `CODEOWNERS` file (checked in `CODEOWNERS`, `.github/CODEOWNERS`, and `docs/CODEOWNERS`) and the `DEFAULT_REVIEWERS` config key. The agent never infers reviewers from git history, blame, or team membership.

**Configure, don't fork.** Skills use `{{PLACEHOLDER}}` tokens for project-specific values. Your `.codecannon.yaml` fills them in. When upstream skills improve, pull the submodule and re-sync.

**Agent-agnostic.** Skills are written once. Adapters handle the translation to Claude Code, Cursor, or any future agent.

![Code Cannon Agents Working With Humans](.github/assets/readme-inline-agents-working-with-humans.png)

## Quick start

```bash
# Add Code Cannon to your project
git submodule add https://github.com/LightbridgeLab/CodeCannon.git CodeCannon
git submodule update --init

# Create and edit your config
cp CodeCannon/templates/codecannon.yaml .codecannon.yaml

# Generate skill files
CodeCannon/sync.sh
```

Or run `/setup` for a guided walkthrough that detects your project state and configures everything interactively.

## Documentation

- **[Getting started](docs/index.md)** — detailed overview, full quickstart, migration guide
- **[Branching models](docs/branching.md)** — trunk, two-branch, and three-branch workflows
- **[Customization](docs/customization.md)** — tailoring skills to your project, sync.sh reference
- **[Config reference](docs/config-reference.md)** — every `.codecannon.yaml` setting documented
- **[Adapters](docs/adapters.md)** — supported agents and how to add new ones

### Skill reference

| Skill | Docs | Description |
|---|---|---|
| `/start` | [docs](docs/skills/start.md) | Create a GitHub issue, branch, and write code |
| `/ship` | [docs](docs/skills/ship.md) | Check, commit, open PR, review, merge |
| `/review` | [docs](docs/skills/review.md) | Standalone code review on a PR |
| `/deploy` | [docs](docs/skills/deploy.md) | Bump version, create GitHub Release, promote to production |
| `/qa` | [docs](docs/skills/qa.md) | QA queue and structured review workflow |
| `/status` | [docs](docs/skills/status.md) | Snapshot of PRs, issues, and progress |
| `/setup` | [docs](docs/skills/setup.md) | Guided onboarding and configuration |

## License

MIT
