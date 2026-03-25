# /version

Bump the project version, tag, and push.

**Source prompt:** [`../../skills/version.md`](../../skills/version.md)

## What it does

`/version` reads the current version, asks what kind of bump you want, runs the appropriate bump command, and pushes both the commit and the tag. Run it after features are merged and before deploying.

## Usage

```
/version
```

No arguments. Must be run from the correct branch (determined by your branching model).

## Step-by-step

1. **Verify branch** — checks that you're on the required pre-production branch:
   - **Trunk mode:** `BRANCH_PROD`
   - **Two-branch mode:** `BRANCH_DEV`
   - **Three-branch mode:** `BRANCH_TEST`

   Aborts if on the wrong branch.

2. **Read current version** — runs `VERSION_READ_CMD` to display the current version.

3. **Ask the user** — presents bump options with computed values:
   - **major** (e.g. 1.2.3 -> 2.0.0)
   - **minor** (e.g. 1.2.3 -> 1.3.0)
   - **patch** (e.g. 1.2.3 -> 1.2.4)
   - or set a specific version

4. **Run bump command** — maps your choice to the appropriate command (`BUMP_PATCH_CMD`, `BUMP_MINOR_CMD`, `BUMP_MAJOR_CMD`, or `SET_VERSION_CMD`). These commands are expected to update the version file, create a commit, and create a tag.

5. **Push** — pushes the commit and the tag to the remote.

6. **Report** — tells you the new version and next steps based on your branching model.

## Why it's built this way

**Separate from /release.** Version bumping and release promotion are distinct steps. You might bump the version and deploy to a preview environment for testing before deciding to promote to production. Keeping them separate supports this QA workflow.

**Branch enforcement.** `/version` runs from the pre-production branch, not from a feature branch. This ensures the version bump happens after features are merged and the integration branch is stable.

**Bump commands are external.** Code Cannon doesn't implement version bumping itself — it delegates to your project's Makefile or scripts. This keeps the skill generic across different version file formats (package.json, VERSION file, setup.py, etc.).

## Config keys used

- `VERSION_READ_CMD` — prints the current version
- `BUMP_PATCH_CMD`, `BUMP_MINOR_CMD`, `BUMP_MAJOR_CMD` — semver bump commands
- `SET_VERSION_CMD` — set an arbitrary version
- `DEPLOY_PREVIEW_CMD` — suggested for deploying to preview after version bump
- `BRANCH_PROD`, `BRANCH_DEV`, `BRANCH_TEST` — determine which branch `/version` must run from
