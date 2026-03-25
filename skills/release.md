---
skill: release
type: skill
description: "Create a GitHub Release; in two-branch and three-branch mode, also promotes the pre-production branch to `{{BRANCH_PROD}}`"
args: none
---

## What `/release` does

Creates a GitHub Release and, in two-branch and three-branch mode, promotes the pre-production branch to `{{BRANCH_PROD}}`. Run this after preview/staging testing is confirmed.

---

## Step 1 — Verify state and determine mode

Check the current branch:
```bash
git branch --show-current
```

**Determine mode:**
- If `{{BRANCH_DEV}}` is empty → **Trunk Mode**. Follow the Trunk Mode section below.
- If `{{BRANCH_DEV}}` is set but `{{BRANCH_TEST}}` is empty → **Two-Branch Mode**. Follow the Two-Branch Mode section below.
- If both `{{BRANCH_DEV}}` and `{{BRANCH_TEST}}` are set → **Three-Branch Mode**. Follow the Three-Branch Mode section below.

---

## Trunk Mode

### Step 1T — Verify on `{{BRANCH_PROD}}` with tag

If not on `{{BRANCH_PROD}}`, switch to it:
```bash
git checkout {{BRANCH_PROD}} && git pull
```

Verify a version tag exists on HEAD (i.e., `/version` was run before this):
```bash
git describe --exact-match --tags HEAD 2>/dev/null
```

If no tag is found, warn: "No version tag found on HEAD. Run `/version` first to tag this release before running `/release`." Stop unless the user explicitly says to proceed anyway.

### Step 2T — Compute release contents

Find the previous tag to determine the range:
```bash
git describe --abbrev=0 <version-tag>^ 2>/dev/null
```

Find all merge commits since the previous tag:
```bash
git log <prev-tag>..HEAD --merges --pretty=format:"%s"
```

Parse PR numbers from merge commit subjects (format: `Merge pull request #N from branch/name`).

For each PR number found, retrieve the PR body:
```bash
gh pr view <N> --json number,title,body
```

Extract `Closes #N` references from PR bodies (trunk PRs use `Closes #N`). Compile:
- List of PRs included (number + title)
- List of issues linked via `Closes #N`

### Step 3T — HUMAN GATE

Show the user the release summary. Example format:

```
Ready to release vX.Y.Z to production.

PRs included:
  #17 — Add /docs directory
  #18 — Fix checkout runtime error

Issues that will be referenced:
  #14 — Add /docs directory
  #15 — Fix checkout runtime error

Have you confirmed everything above is ready for production? Type 'release' to confirm.
```

Wait for the user to type "release" or an explicit confirmation. Any other response → stop and ask what they'd like to change.

### Step 4T — Create GitHub Release

The version tag and PR/issue list are already known. If no previous tag exists, omit the "Full changelog" line.

```bash
gh release create <version-tag> \
  --title "<version-tag>" \
  --notes "$(cat <<'EOF'
## Changes

- #<issue> — <PR title> (PR #<pr-number>)
[... one line per PR included in this release ...]

**Full changelog:** https://github.com/<owner>/<repo>/compare/<previous-tag>...<version-tag>
EOF
)"
```

Format each PR line as `- #<linked-issue> — <PR title> (PR #<N>)`. If a PR had no linked issue, use just the PR title.

After the command runs, note the release URL from the output.

### Step 5T — Report

Tell the user:

> "Released vX.Y.Z. Issues closed on merge. GitHub Release vX.Y.Z created at `<url>`. Run `{{DEPLOY_PROD_CMD}}` to ship to production."

---

## Two-Branch Mode

### Step 1 — Verify state

If not on `{{BRANCH_DEV}}`, switch to it:
```bash
git checkout {{BRANCH_DEV}} && git pull
```

Verify a version tag exists on HEAD:
```bash
git describe --exact-match --tags HEAD 2>/dev/null
```

If no tag is found, warn: "No version tag found on HEAD. Run `/version` first to tag this release before promoting it." Stop unless the user explicitly says to proceed anyway.

### Step 2 — Compute what's being promoted

Find all merge commits in `{{BRANCH_DEV}}` not yet in `{{BRANCH_PROD}}`:
```bash
git log {{BRANCH_PROD}}..{{BRANCH_DEV}} --merges --pretty=format:"%s"
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

### Step 3 — HUMAN GATE

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

### Step 4 — Create PR: `{{BRANCH_DEV}}` → `{{BRANCH_PROD}}`

```bash
gh pr create --base {{BRANCH_PROD}} --head {{BRANCH_DEV}} \
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

The `Closes #N` lines will auto-close the linked issues because this PR merges into `{{BRANCH_PROD}}` (the default branch).

### Step 5 — Merge

Do NOT use `{{MERGE_CMD}}` — it refuses PRs targeting `{{BRANCH_PROD}}`. Use `gh pr merge` directly:

```bash
gh pr merge <pr-number> --merge
```

### Step 6 — Create GitHub Release

The version tag (from Step 1) and the PR/issue list (from Step 2) are already known. Find the previous tag to build the changelog link:

```bash
git describe --abbrev=0 <version-tag>^ 2>/dev/null
```

If no previous tag exists, omit the "Full changelog" line.

Create the release:

```bash
gh release create <version-tag> \
  --title "<version-tag>" \
  --notes "$(cat <<'EOF'
## Changes

- #<issue> — <PR title> (PR #<pr-number>)
[... one line per PR included in this release ...]

**Full changelog:** https://github.com/<owner>/<repo>/compare/<previous-tag>...<version-tag>
EOF
)"
```

Format each PR line as `- #<linked-issue> — <PR title> (PR #<N>)`. If a PR had no linked issue, omit the `#<issue>` prefix and use just the PR title.

After the command runs, note the release URL from the output.

### Step 7 — Report

Tell the user:

> "Released vX.Y.Z. Issues #N, #M closed automatically. GitHub Release vX.Y.Z created at `<url>`. Run `{{DEPLOY_PROD_CMD}}` to ship to production."

---

## Three-Branch Mode

### Step 1 — Verify state

If not on `{{BRANCH_TEST}}`, switch to it:
```bash
git checkout {{BRANCH_TEST}} && git pull
```

Verify a version tag exists on HEAD:
```bash
git describe --exact-match --tags HEAD 2>/dev/null
```

If no tag is found, warn: "No version tag found on HEAD. Run `/version` first to tag this release before promoting it." Stop unless the user explicitly says to proceed anyway.

### Step 2 — Compute what's being promoted

Find all merge commits in `{{BRANCH_TEST}}` not yet in `{{BRANCH_PROD}}`:
```bash
git log {{BRANCH_PROD}}..{{BRANCH_TEST}} --merges --pretty=format:"%s"
```

Parse PR numbers from the merge commit subjects. Note: some merge commits here may be promotion merges from `{{BRANCH_DEV}}` — these are identifiable by subjects matching "Merge ... from `{{BRANCH_DEV}}`". Include them in the list but note they are promotion merges; extract the original feature PRs from their PR bodies when possible.

For each PR number found, retrieve the PR body:
```bash
gh pr view <N> --json number,title,body
```

Extract `Issue #N` and `Closes #N` references from PR bodies.

Compile (best-effort):
- List of PRs being promoted (number + title)
- List of open issues linked to those PRs

### Step 3 — HUMAN GATE

Show the user the release summary. Example format:

```
Ready to release vX.Y.Z to production.

PRs included:
  #17 — Add /docs directory
  #18 — Fix checkout runtime error

Issues that will close:
  #14 — Add /docs directory
  #15 — Fix checkout runtime error

Have you tested all of the above on the {{BRANCH_TEST}} environment? Type 'release' to confirm.
```

Wait for the user to type "release" or an explicit confirmation. Any other response → stop and ask what they'd like to change.

### Step 4 — Create PR: `{{BRANCH_TEST}}` → `{{BRANCH_PROD}}`

```bash
gh pr create --base {{BRANCH_PROD}} --head {{BRANCH_TEST}} \
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

The `Closes #N` lines will auto-close the linked issues because this PR merges into `{{BRANCH_PROD}}` (the default branch).

### Step 5 — Merge

Do NOT use `{{MERGE_CMD}}` — it refuses PRs targeting `{{BRANCH_PROD}}`. Use `gh pr merge` directly:

```bash
gh pr merge <pr-number> --merge
```

### Step 6 — Create GitHub Release

The version tag (from Step 1) and the PR/issue list (from Step 2) are already known. Find the previous tag to build the changelog link:

```bash
git describe --abbrev=0 <version-tag>^ 2>/dev/null
```

If no previous tag exists, omit the "Full changelog" line.

Create the release:

```bash
gh release create <version-tag> \
  --title "<version-tag>" \
  --notes "$(cat <<'EOF'
## Changes

- #<issue> — <PR title> (PR #<pr-number>)
[... one line per PR included in this release ...]

**Full changelog:** https://github.com/<owner>/<repo>/compare/<previous-tag>...<version-tag>
EOF
)"
```

Format each PR line as `- #<linked-issue> — <PR title> (PR #<N>)`. If a PR had no linked issue, omit the `#<issue>` prefix and use just the PR title.

After the command runs, note the release URL from the output.

### Step 7 — Report

Tell the user:

> "Released vX.Y.Z. Issues #N, #M closed automatically. GitHub Release vX.Y.Z created at `<url>`. Run `{{DEPLOY_PROD_CMD}}` to ship to production."
