# /deploy

Bump the project version, create a GitHub Release, and promote to production.

**Source prompt:** [`../../skills/deploy.md`](../../skills/deploy.md)

## What it does

`/deploy` is the final step in the workflow. It combines version bumping and release creation into a single command. Its behavior varies by branching model:

- **Trunk mode:** Optionally bumps the version, then creates a GitHub Release from `BRANCH_PROD` using the version tag.
- **Two-branch mode:** Optionally bumps the version, opens a promotion PR from `BRANCH_DEV` to `BRANCH_PROD`, merges it (which auto-closes linked issues), and creates a GitHub Release.
- **Three-branch mode:** Same as two-branch but promotes from `BRANCH_TEST` to `BRANCH_PROD`.

## Usage

```
/deploy
```

No arguments. Must be run from the correct branch (determined by your branching model).

## Step-by-step

1. **Verify branch** — checks that you're on the required pre-production branch:
   - **Trunk mode:** `BRANCH_PROD`
   - **Two-branch mode:** `BRANCH_DEV`
   - **Three-branch mode:** `BRANCH_TEST`

   Aborts if on the wrong branch.

2. **Check current state** — finds the latest version tag, reads the current version, shows commits/PRs since the last tag, and lists any open unmerged PRs.

3. **Ask about version bump** — presents bump options with computed values:
   - **major** (e.g. 1.2.3 -> 2.0.0)
   - **minor** (e.g. 1.2.3 -> 1.3.0)
   - **patch** (e.g. 1.2.3 -> 1.2.4)
   - set a specific version
   - or skip (proceed with existing tag)

4. **Version bump** (if requested) — runs the appropriate bump command (`BUMP_PATCH_CMD`, `BUMP_MINOR_CMD`, `BUMP_MAJOR_CMD`, or `SET_VERSION_CMD`), then pushes the commit and tag.

5. **Compute release contents** — finds merge commits since the previous tag, extracts linked PRs and issues.

6. **Human gate** — shows a release summary and waits for you to type "release".

7. **Create GitHub Release** (trunk mode) or **Create promotion PR, merge, then create GitHub Release** (multi-branch modes).

## Why it's built this way

**Version bump and release in one flow.** Previously these were separate `/version` and `/release` commands. Combining them reduces the workflow from six commands to five and eliminates the possibility of bumping a version but forgetting to release, or vice versa. The version bump step is optional — if you've already tagged, you can skip straight to release.

**Human gate is mandatory.** The "type release to confirm" gate exists because promoting to production is irreversible in practice. The summary gives you one last chance to verify that the right changes are going out.

**Issues close on release, not on feature merge.** In multi-branch modes, feature PRs use `Issue #N` instead of `Closes #N`. Issues only auto-close when the promotion PR merges to `BRANCH_PROD`. This means issues stay open through the QA/staging phase, giving you visibility into what's deployed where.

**State check surfaces surprises early.** Showing open unmerged PRs at the start prevents accidental releases that miss in-flight work.

**Bump commands are external.** Code Cannon doesn't implement version bumping itself — it delegates to your project's Makefile or scripts. This keeps the skill generic across different version file formats (package.json, VERSION file, setup.py, etc.).

## Config keys used

- `VERSION_READ_CMD` — prints the current version
- `BUMP_PATCH_CMD`, `BUMP_MINOR_CMD`, `BUMP_MAJOR_CMD` — semver bump commands
- `SET_VERSION_CMD` — set an arbitrary version
- `DEPLOY_PREVIEW_CMD` — suggested for deploying to preview after version bump
- `DEPLOY_PROD_CMD` — suggested after release for deploying to production
- `BRANCH_PROD`, `BRANCH_DEV`, `BRANCH_TEST` — determine mode and promotion path
- `MERGE_CMD` — NOT used for promotion merges (uses `gh pr merge` directly)
