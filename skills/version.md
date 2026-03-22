---
skill: version
description: Bump the project version, tag, and push — run before deploying to preview
args: none
---

## Step 1 — Verify branch

Run:
```bash
git branch --show-current
```

If not on `{{INTEGRATION_BRANCH}}`, abort and say: "Switch to `{{INTEGRATION_BRANCH}}` before running `/version`."

---

## Step 2 — Read current version

```bash
{{VERSION_READ_CMD}}
```

---

## Step 3 — Ask the user

Tell the user (filling in the actual computed values):

> "You are on version X.Y.Z. Do you want to bump:
> - **major** → A.0.0
> - **minor** → X.B.0
> - **patch** → X.Y.C
> - or set a specific version?"

Wait for their response.

---

## Step 4 — Interpret and run

Map the user's natural language response to a command:

| User says | Run |
|---|---|
| "patch" / anything mentioning patch | `{{BUMP_PATCH_CMD}}` |
| "minor" | `{{BUMP_MINOR_CMD}}` |
| "major" | `{{BUMP_MAJOR_CMD}}` |
| A specific version e.g. "2.4.5" | `{{SET_VERSION_CMD}} 2.4.5` |

These targets update the version manifest, create a git commit, and create a git tag. Do not create commits or tags manually.

---

## Step 5 — Push

```bash
git push
git push --tags
```

Both the version bump commit and the tag must be pushed.

---

## Step 6 — Report

Tell the user the new version and tag:

> "Tagged as vX.Y.Z. Run `{{DEPLOY_PREVIEW_CMD}}` to deploy to preview for testing. When testing is complete, run `/release`."
