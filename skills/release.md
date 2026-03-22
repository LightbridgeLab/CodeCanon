---
skill: release
description: Promote the integration branch to main, close linked issues, prep for production deploy
args: none
---

## What `/release` does

Promotes `{{INTEGRATION_BRANCH}}` to `main`, closes linked issues, and prepares for production deployment. Run this after preview testing is confirmed.

---

## Step 1 — Verify state

Check the current branch:
```bash
git branch --show-current
```

If not on `{{INTEGRATION_BRANCH}}`, switch to it:
```bash
git checkout {{INTEGRATION_BRANCH}} && git pull
```

Verify a version tag exists on HEAD (i.e., `/version` was run before this):
```bash
git describe --exact-match --tags HEAD 2>/dev/null
```

If no tag is found, warn the user: "No version tag found on HEAD. Run `/version` first to tag this release before promoting it." Stop unless the user explicitly says to proceed anyway.

---

## Step 2 — Compute what's being promoted

Find all merge commits in `{{INTEGRATION_BRANCH}}` not yet in `main`:
```bash
git log main..{{INTEGRATION_BRANCH}} --merges --pretty=format:"%s"
```

Parse PR numbers from the merge commit subjects. GitHub's format is:
`Merge pull request #N from branch/name`

For each PR number found, retrieve the PR body:
```bash
gh pr view <N> --json number,title,body
```

Extract `Issue #N` references from PR bodies (look for the pattern `Issue #\d+`).

Compile:
- List of PRs being promoted (number + title)
- List of open issues linked to those PRs

---

## Step 3 — HUMAN GATE

Show the user the release summary. Example format:

```
Ready to release vX.Y.Z to production.

PRs included:
  #17 — Add /docs directory
  #18 — Fix checkout runtime error

Issues that will close:
  #14 — Add /docs directory
  #15 — Fix checkout runtime error

Have you tested all of the above on preview? Type 'release' to confirm.
```

Wait for the user to type "release" or an explicit confirmation. Any other response → stop and ask what they'd like to change.

---

## Step 4 — Create PR: {{INTEGRATION_BRANCH}} → main

```bash
gh pr create --base main --head {{INTEGRATION_BRANCH}} \
  --title "Release vX.Y.Z" \
  --body "$(cat <<'EOF'
Release vX.Y.Z

PRs included:
- #17 — Add /docs directory
- #18 — Fix checkout runtime error

Closes #14
Closes #15
EOF
)"
```

Note the PR number from the output.

The `Closes #N` lines will auto-close the linked issues because this PR merges into `main` (the default branch).

---

## Step 5 — Merge

Do NOT use `{{MERGE_CMD}}` — it refuses PRs targeting `main`. Use `gh pr merge` directly:

```bash
gh pr merge <pr-number> --merge
```

---

## Step 6 — Report

Tell the user:

> "Released vX.Y.Z. Issues #N, #M closed automatically. Run `{{DEPLOY_PROD_CMD}}` to ship to production."
