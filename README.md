![Code Cannon](.github/assets/readme-header.png)

# Code Cannon

Write your team's AI agent workflow once — start, submit-for-review, review, deploy — and sync it to Claude Code, Cursor, Gemini, and Codex across all your projects.

## The problem

AI coding agents are powerful, but every project reinvents the same workflows: how to create issues, open PRs, run reviews, deploy releases. These instructions live in scattered prompt files, maintained per-project, per-agent, with no consistency and no reuse.

## The solution

Code Cannon is a shared skill library that lives as a git submodule. Skills are written once as portable markdown. A sync script reads your project config and generates agent-specific command files:

```
skills/*.md  →  sync.sh + .codecannon.yaml  →  .claude/commands/*.md
                                              →  .cursor/rules/*.mdc
```

One source of truth for every project and every agent.

## What you get

A complete development workflow in five commands:

```
/start  →  [code + test]  →  /submit-for-review  →  [QA]  →  /deploy
```

| Command | What it does |
|---|---|
| `/start` | Create a GitHub issue, feature branch, and write code |
| `/submit-for-review` | Check, commit, open PR, run AI review, merge |
| `/review` | Standalone code review on any PR |
| `/deploy` | Bump version, create a GitHub Release, promote to production |
| `/status` | Standup-ready snapshot of PRs, issues, and progress |

Plus `/qa` for structured QA workflows and `/setup` for guided onboarding.

![Code Cannon Agents Working With Humans](.github/assets/readme-inline-agents-working-with-humans.png)

## Philosophy

**Humans stay in the loop.** The agent proposes; you approve. `/start` waits for your sign-off before creating anything. `/deploy` requires explicit confirmation.

**Every change has a ticket.** There is no path for code without an issue. The issue is the unit of work — branch, PR, and release all link back to it.

**Configure, don't fork.** Skills use `{{PLACEHOLDER}}` tokens. Your `.codecannon.yaml` fills them in. When upstream improves, pull the submodule and re-sync.

## Quick start

```bash
git submodule add https://github.com/LightbridgeLab/CodeCannon.git CodeCannon
cp CodeCannon/templates/codecannon.yaml .codecannon.yaml
CodeCannon/sync.sh
```

Then optionally run `/setup` for a guided walkthrough.

To update to the latest version:

```bash
CodeCannon/sync.sh --update
```

## Documentation

- **[Getting started](docs/index.md)** — full quickstart, migration guide, and workflow details
- **[Branching models](docs/branching.md)** — trunk, two-branch, and three-branch workflows
- **[Customization](docs/customization.md)** — tailoring skills, sync.sh reference
- **[Config reference](docs/config-reference.md)** — every `.codecannon.yaml` setting documented
- **[Adapters](docs/adapters.md)** — supported agents and how to add new ones
- **Skill reference:** [/start](docs/skills/start.md) · [/submit-for-review](docs/skills/submit-for-review.md) · [/review](docs/skills/review.md) · [/deploy](docs/skills/deploy.md) · [/qa](docs/skills/qa.md) · [/status](docs/skills/status.md) · [/setup](docs/skills/setup.md)

## License

MIT
