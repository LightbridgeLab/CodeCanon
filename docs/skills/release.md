# /release

Create a GitHub Release and promote to production.

**Source prompt:** [`../../skills/release.md`](../../skills/release.md)

## What it does

`/release` is the final step in the workflow. Its behavior varies by branching model:

- **Trunk mode:** Creates a GitHub Release from `BRANCH_PROD` using the latest version tag. No promotion PR needed since features already merged to `BRANCH_PROD`.
- **Two-branch mode:** Opens a promotion PR from `BRANCH_DEV` to `BRANCH_PROD`, merges it (which auto-closes linked issues), and creates a GitHub Release.
- **Three-branch mode:** Same as two-branch but promotes from `BRANCH_TEST` to `BRANCH_PROD`.

## Usage

```
/release
```

No arguments. Run after `/version` has tagged the release.

## Step-by-step (trunk mode)

1. **Verify state** — switches to `BRANCH_PROD` if needed, verifies a version tag exists on HEAD.
2. **Compute release contents** — finds merge commits since the previous tag, extracts linked PRs and issues.
3. **Human gate** — shows a release summary and waits for you to type "release".
4. **Create GitHub Release** — creates a release with a changelog listing all included PRs and issues.

## Step-by-step (two-branch and three-branch mode)

1. **Verify state** — switches to the pre-production branch, verifies a version tag exists on HEAD.
2. **Compute what's being promoted** — finds merge commits in the pre-production branch not yet in `BRANCH_PROD`, extracts linked PRs and issues.
3. **Human gate** — shows a release summary with all included PRs and issues that will close. Waits for you to type "release".
4. **Create promotion PR** — opens a PR from the pre-production branch to `BRANCH_PROD` with `Closes #N` references so issues auto-close on merge.
5. **Merge** — merges the promotion PR directly (does not use `MERGE_CMD`, which may refuse `BRANCH_PROD` targets).
6. **Create GitHub Release** — creates a release with a changelog and full comparison link.

## Why it's built this way

**Human gate is mandatory.** The "type release to confirm" gate exists because promoting to production is irreversible in practice. The summary gives you one last chance to verify that the right changes are going out.

**Issues close on release, not on feature merge.** In multi-branch modes, feature PRs use `Issue #N` instead of `Closes #N`. Issues only auto-close when the promotion PR merges to `BRANCH_PROD`. This means issues stay open through the QA/staging phase, giving you visibility into what's deployed where.

**Promotion PR bypasses MERGE_CMD.** `MERGE_CMD` typically includes safeguards that prevent direct merges to `BRANCH_PROD`. `/release` uses `gh pr merge` directly because this is the one intentional case where merging to production is correct.

**Changelog is computed from git history.** The release notes are built from merge commits and their linked PRs/issues, not from manual input. This ensures the changelog matches what actually shipped.

## Config keys used

- `BRANCH_PROD`, `BRANCH_DEV`, `BRANCH_TEST` — determine mode and promotion path
- `MERGE_CMD` — NOT used for promotion merges (uses `gh pr merge` directly)
- `DEPLOY_PROD_CMD` — suggested after release for deploying to production
