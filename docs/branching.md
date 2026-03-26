# Branching Models

Code Cannon supports three branching models. Set `BRANCH_DEV` and `BRANCH_TEST` in `.codecannon.yaml` to match your workflow.

## Trunk-based development

**Config:** Leave `BRANCH_DEV` and `BRANCH_TEST` empty (or unset).

```
feature/<name>  →  main
    /start           /ship merges here
                     /deploy runs here
```

The simplest model. Feature branches are created from and merged directly into `BRANCH_PROD` (default: `main`). `/ship` opens a PR targeting `main` with `Closes #N` — issues auto-close on merge.

**When to use:** Solo developers, small teams, projects where every merge is production-ready. Fast iteration with low ceremony.

**Skill behavior in trunk mode:**
- `/ship` targets `BRANCH_PROD` directly
- `/deploy` runs from `BRANCH_PROD` — bumps version and creates a GitHub Release (no promotion PR needed)
- QA labels are not applied automatically

## Two-branch development

**Config:** Set `BRANCH_DEV` to your integration branch (e.g. `dev`, `development`, `staging`).

```
feature/<name>  →  BRANCH_DEV  →  BRANCH_PROD
    /start           /ship           /deploy
```

Feature PRs target `BRANCH_DEV`. Issues deliberately stay open through the feature merge — `Closes #N` is not used on feature PRs because they don't land in the default branch. Issues only auto-close when `/deploy` promotes `BRANCH_DEV` to `BRANCH_PROD`.

This supports a QA gate between merging code and shipping to production. After `/ship` merges a feature, you deploy the integration branch to a preview environment, test it, then run `/deploy` when satisfied.

**When to use:** Teams that want a review/QA gate before production. The most common model for teams with a staging or preview environment.

**Skill behavior in two-branch mode:**
- `/ship` targets `BRANCH_DEV` and uses `Issue #N` (not `Closes`)
- `/ship` applies `QA_READY_LABEL` to the linked issue (if configured)
- `/deploy` runs from `BRANCH_DEV` — bumps version, opens a promotion PR from `BRANCH_DEV` to `BRANCH_PROD` with `Closes #N` to auto-close issues

## Three-branch development

**Config:** Set both `BRANCH_DEV` and `BRANCH_TEST`.

```
feature/<name>  →  BRANCH_DEV  →  BRANCH_TEST  →  BRANCH_PROD
    /start           /ship        manual/future       /deploy
                                   /promote
```

Adds a dedicated test/staging branch between integration and production. Feature PRs still target `BRANCH_DEV`. The promotion from `BRANCH_DEV` to `BRANCH_TEST` is a manual PR or a future `/promote` skill.

**When to use:** Teams with a formal QA or staging environment that is separate from the integration environment. Common in regulated industries or teams with dedicated QA staff.

**Skill behavior in three-branch mode:**
- `/ship` targets `BRANCH_DEV` (same as two-branch)
- `/deploy` runs from `BRANCH_TEST` — bumps version and promotes `BRANCH_TEST` to `BRANCH_PROD`
- The `BRANCH_DEV` to `BRANCH_TEST` step is outside Code Cannon's current scope

## Choosing your model

| Profile | Branch model | AI review | QA flow | Good for |
|---|---|---|---|---|
| **Lightweight** | Trunk | Advisory (posts but doesn't block) | Off | Fast iteration, low ceremony |
| **Standard** | Two-branch | Blocks merge | Optional | Review-gated development |
| **Governed** | Two or three-branch | Blocks merge | On | Full traceability and QA handoff |

These aren't rigid modes — they're starting points. Every setting is independently configurable. Run `/setup` for a guided walkthrough that helps you pick the right profile and configure it.

## Branch discipline

Code Cannon enforces branch rules at the skill level:

- `/ship` aborts if run from any protected branch (`BRANCH_PROD`, `BRANCH_DEV`, or `BRANCH_TEST` when set). It must be run from a `feature/*` branch.
- `/deploy` aborts if not on the required pre-production branch (determined by mode).
- `/start` always creates `feature/*` branches via `gh issue develop`, ensuring every branch is linked to an issue.

The agent will not proceed past these checks. There is no override flag — if you're on the wrong branch, switch first.
