# /ship

Type-check, commit, open PR, spawn review agent, and merge.

**Source prompt:** [`../../skills/ship.md`](../../skills/ship.md)

## What it does

`/ship` is Phase 3 of the workflow — it takes code that has been written and tested locally, and moves it through the full shipping pipeline: check, commit, push, PR, review, merge.

It must be run from a `feature/*` branch. Running it from any protected branch (`BRANCH_PROD`, `BRANCH_DEV`, `BRANCH_TEST`) causes an immediate abort.

## Usage

```
/ship
```

No arguments. `/ship` operates on the current branch.

## Step-by-step

1. **Verify branch** — confirms you're on a `feature/*` branch, not a protected branch.

2. **Type-check gate** — runs `CHECK_CMD`. If it fails, `/ship` stops and reports the errors. This is a hard gate — no bypass.

3. **Identify linked issue** — looks for the issue number linked to this branch (from `gh issue develop` or the PR body).

4. **Commit** — stages all changes and creates a single commit with an imperative-mood message. Excludes `.env` files, build artifacts, and secrets.

5. **Push and open PR** — pushes the branch and creates a PR targeting the correct branch based on your branching model:
   - **Trunk mode:** targets `BRANCH_PROD`, uses `Closes #N`
   - **Two/three-branch mode:** targets `BRANCH_DEV`, uses `Issue #N` (issue stays open until `/deploy`)

6. **Review** (conditional) — behavior depends on `REVIEW_GATE`:
   - `ai` (default): spawns a review agent, waits for verdict
   - `advisory`: spawns a review agent, posts findings, merges regardless
   - `off`: skips review entirely

7. **Act on verdict** — if `REVIEW_GATE` is `ai` and the review finds CRITICAL issues, `/ship` stops and asks you to fix them. Otherwise, it merges the PR.

8. **Post-merge** — in two-branch mode, applies `QA_READY_LABEL` to the linked issue if configured. Reports next steps based on your branching model.

## Reviewer selection

`/ship` adds reviewers from exactly two sources:

- **CODEOWNERS file** — checked in `CODEOWNERS`, `.github/CODEOWNERS`, and `docs/CODEOWNERS`. GitHub automatically requests reviews from code owners.
- **`DEFAULT_REVIEWERS` config** — comma-separated handles or team slugs added to the PR.

The agent never infers reviewers from git history, blame, or team membership.

## Review gate modes

| Mode | Review happens? | Blocks merge? | Use case |
|---|---|---|---|
| `ai` | Yes | Yes, on CRITICAL findings | Default. Full review-gated development. |
| `advisory` | Yes | No | Review posts findings but merges anyway. Good for fast iteration with visibility. |
| `off` | No | N/A | No review. Merges immediately after checks pass. |

## Why it's built this way

**Single command for the full pipeline.** The check-commit-push-PR-review-merge sequence is mechanical and error-prone when done manually. `/ship` automates the entire chain while keeping a human gate (the review) in the middle.

**Mandatory check gate.** `CHECK_CMD` must pass before anything is committed or pushed. This prevents known-broken code from ever reaching a PR.

**Issue linking varies by mode.** In trunk mode, `Closes #N` auto-closes issues on merge because the PR targets the default branch. In multi-branch mode, `Issue #N` keeps issues open until `/deploy` promotes to production — this supports QA workflows where you want to track issues through the staging environment.

**QA label automation.** In two-branch mode, `/ship` applies `QA_READY_LABEL` to signal that a feature is ready for testing on the preview environment. This feeds into the `/qa` skill's queue view.

## Config keys used

- `CHECK_CMD` — lint/type-check gate
- `MERGE_CMD` — merge command for feature PRs
- `REVIEW_GATE` — controls review behavior (`ai`, `advisory`, `off`)
- `REVIEW_AGENT_PROMPT` — path to the review agent system prompt
- `DEFAULT_REVIEWERS` — auto-assigned PR reviewers
- `QA_READY_LABEL` — label applied in two-branch mode after merge
- `BRANCH_PROD`, `BRANCH_DEV`, `BRANCH_TEST` — determine PR target and issue reference format
