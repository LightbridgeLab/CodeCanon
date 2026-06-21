---
skill: deploy
type: skill
description: "Code Cannon: Bump the project version, create a GitHub Release, and promote to production — handles both versioning and releasing in one step"
args: none
---

## What `/deploy` does

`/deploy` is the final step in the workflow. It combines version bumping and release creation into a single command: check state, optionally bump the version, then create a GitHub Release (and in multi-branch mode, promote to production).

---

## Step 1 — Verify branch

Run:
```bash
git branch --show-current
```

{{#if BRANCH_TEST}}
Required branch: `{{BRANCH_TEST}}` (three-branch mode).
{{/if}}
{{#if !BRANCH_TEST}}
{{#if BRANCH_DEV}}
Required branch: `{{BRANCH_DEV}}` (two-branch mode).
{{/if}}
{{#if !BRANCH_DEV}}
Required branch: `{{BRANCH_PROD}}` (trunk mode).
{{/if}}
{{/if}}

If not on the required branch, abort and say: "Switch to `<required-branch>` before running `/deploy`."

Sync to the remote before proceeding. The script below guards against uncommitted local changes, then runs `git checkout`, `git fetch`, and `git reset --hard origin/<base>` as one atomic operation. The deploy branch is never edited locally under the CodeCannon workflow (only fast-forwarded from CodeCannon's own merges), so the hard reset is the correct sync; the dirty-tree guard catches accidental local edits before they get silently discarded.

{{#if BRANCH_TEST}}
```bash
python3 CodeCannon/skills/github-agile/scripts/sync-base-branch.py {{BRANCH_TEST}}
```
{{/if}}
{{#if !BRANCH_TEST}}
{{#if BRANCH_DEV}}
```bash
python3 CodeCannon/skills/github-agile/scripts/sync-base-branch.py {{BRANCH_DEV}}
```
{{/if}}
{{#if !BRANCH_DEV}}
```bash
python3 CodeCannon/skills/github-agile/scripts/sync-base-branch.py {{BRANCH_PROD}}
```
{{/if}}
{{/if}}

If the script exits non-zero, stop and resolve the issue it reports before continuing.

---

## Step 2 — Check current state

### Find the latest version tag

```bash
git describe --tags --abbrev=0 2>/dev/null
```

If no tag exists, note this is the first release.

### Read current version

```bash
{{VERSION_READ_CMD}}
```

### Show commits since last tag

If a previous tag exists, show what's on the branch since that tag:

{{#if !BRANCH_DEV}}
```bash
git log <latest-tag>..HEAD --merges --pretty=format:"%s"
```

Parse PR numbers from merge commit subjects (format: `Merge pull request #N from branch/name`).
{{/if}}
{{#if BRANCH_DEV}}
{{#if !BRANCH_TEST}}
```bash
git log {{BRANCH_PROD}}..{{BRANCH_DEV}} --merges --pretty=format:"%s"
```

Parse PR numbers from merge commit subjects (format: `Merge pull request #N from branch/name`).
{{/if}}
{{#if BRANCH_TEST}}
```bash
git log {{BRANCH_PROD}}..{{BRANCH_TEST}} --merges --pretty=format:"%s"
```

Parse PR numbers from merge commit subjects. Note: some merge commits here may be promotion merges from `{{BRANCH_DEV}}` — these are identifiable by subjects matching "Merge ... from `{{BRANCH_DEV}}`". Include them in the list but note they are promotion merges; extract the original feature PRs from their PR bodies when possible.
{{/if}}
{{/if}}

For each PR number found, retrieve the PR body:
```bash
gh pr view <N> --json number,title,body
```

{{#if !BRANCH_DEV}}
Extract `Closes #N` references from PR bodies. Compile:
- List of PRs included (number + title)
- List of issues linked to those PRs
{{/if}}
{{#if BRANCH_DEV}}
Extract closing keywords **separately** from context references — do **not** merge them into a single set:

- **Close set** — the union of every `Closes #N` line across all constituent PR bodies. These issues will auto-close when the release PR merges into `{{BRANCH_PROD}}`. Record, per constituent PR, the exact `Closes #N` lines it contained so they can be reproduced verbatim in the release PR body.
- **Reference set** — issues mentioned only via `Related to #N`, or via the legacy `Issue #N` form. These are context links and will **not** close. Legacy `Issue #N` carries no recoverable close-intent, so it stays in the reference set rather than being guessed into the close set; the HUMAN GATE surfaces it so you can manually close any straggler that should have been a `Closes`.

Compile:
- List of PRs included (number + title)
- Close set and reference set, kept distinct
{{/if}}

### Check for open unmerged PRs

```bash
gh pr list --state open --json number,title,headRefName --jq '.[] | "#\(.number) \(.title) (\(.headRefName))"'
```

### Present the summary

Tell the user:

```
Current version: X.Y.Z
Latest tag: vX.Y.Z

Commits/PRs since last tag:
  #17 — Add /docs directory
  #18 — Fix checkout runtime error

Open PRs not yet merged:
  #19 — Add dark mode (feature/dark-mode)

Would you like to bump the version before deploying?
  - **patch** → X.Y.C
  - **minor** → X.B.0
  - **major** → A.0.0
  - **specific** → enter a version number
  - **skip** → proceed to release with the latest existing tag
```

Wait for their response.

---

## Step 3 — Version bump (if requested)

If the user chose to skip, find the latest version tag in the branch history:
```bash
git describe --tags --abbrev=0 2>/dev/null
```

If no tag is found at all (first release), warn: "No version tag found. You must bump the version before deploying." Return to the version bump prompt. Otherwise, use the tag found as the release version.

If the user chose a bump level, map their response to a bump command and run `bump-and-tag.py`, which performs the bump, verifies the resulting tag (creating an annotated fallback if `tag.forceSignAnnotated` silently rejected a lightweight tag), and pushes both the commit and the tag. The resolved version is printed on stdout — capture it for the release step.

| User says | `--bump-cmd` |
|---|---|
| "patch" / anything mentioning patch | `{{BUMP_PATCH_CMD}}` |
| "minor" | `{{BUMP_MINOR_CMD}}` |
| "major" | `{{BUMP_MAJOR_CMD}}` |
| A specific version e.g. "2.4.5" | `{{SET_VERSION_CMD}}2.4.5` |

```bash
python3 CodeCannon/skills/github-agile/scripts/bump-and-tag.py \
  --bump-cmd "<bump-command-from-table>" \
  --version-read-cmd "{{VERSION_READ_CMD}}"
```

If the script exits non-zero, stop and resolve the issue it reports before continuing. On success, the version printed on stdout is the new version — use it as `<new-version>` in subsequent steps.

---

## Step 4 — Compute release contents

Determine the version tag (either from the bump just performed, or from the existing HEAD tag if the user skipped bumping).

Find the previous tag to determine the range:
```bash
git describe --abbrev=0 <version-tag>^ 2>/dev/null
```

{{#if !BRANCH_DEV}}
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
{{/if}}
{{#if BRANCH_DEV}}
{{#if !BRANCH_TEST}}
Use the PR list, close set, and reference set already computed in Step 2. If the version bump added new commits, re-fetch if needed.
{{/if}}
{{#if BRANCH_TEST}}
Use the PR list, close set, and reference set already computed in Step 2. If the version bump added new commits, re-fetch if needed.
{{/if}}
{{/if}}

---

## Step 5 — HUMAN GATE

Show the user the release summary. Example format:

```
Ready to release vX.Y.Z to production.

PRs included:
  #17 — Add /docs directory
  #18 — Fix checkout runtime error

{{#if !BRANCH_DEV}}
Issues that will be referenced:
  #14 — Add /docs directory
  #15 — Fix checkout runtime error
{{/if}}
{{#if BRANCH_DEV}}
Issues that will close on merge (Closes #N, reproduced verbatim from constituent PRs):
  #14 — Add /docs directory
  #15 — Fix checkout runtime error

Issues referenced but NOT closing (Related to #N / legacy Issue #N — confirm none of these should actually close):
  #20 — Tighten error copy on the upload form
{{/if}}

{{#if !BRANCH_DEV}}
Have you confirmed everything above is ready for production? Type 'release' to confirm.
{{/if}}
{{#if BRANCH_DEV}}
{{#if !BRANCH_TEST}}
Have you tested all of the above on preview? Type 'release' to confirm.
{{/if}}
{{#if BRANCH_TEST}}
Have you tested all of the above on the {{BRANCH_TEST}} environment? Type 'release' to confirm.
{{/if}}
{{/if}}
```

Wait for the user to type "release" or an explicit confirmation. Any other response → stop and ask what they'd like to change.

---

{{#if !BRANCH_DEV}}
## Step 6 — Create GitHub Release

The version tag and PR/issue list are already known. If no previous tag exists, omit the "Full changelog" line.

First, create a temp directory for this invocation:

```bash
mkdir -p /tmp/CodeCannon && mktemp -d /tmp/CodeCannon/XXXXXX
```

Note the returned path (e.g. `/tmp/CodeCannon/a8f3b2`). Use this path for all temp files in this invocation.

Then use your file-writing tool (not Bash) to create `<tmpdir>/release_notes.md`:

```markdown
## Changes

- #<issue> — <PR title> (PR #<pr-number>)
[... one line per PR included in this release ...]

**Full changelog:** https://github.com/<owner>/<repo>/compare/<previous-tag>...<version-tag>
```

Then create the release (do NOT use `--notes`, `--notes-file -`, or heredocs):

```bash
gh release create <version-tag> \
  --title "<version-tag>" \
  --notes-file <tmpdir>/release_notes.md
```

Format each PR line as `- #<linked-issue> — <PR title> (PR #<N>)`. If a PR had no linked issue, use just the PR title.

After the command runs, note the release URL from the output.

---

## Step 7 — Report

Tell the user:

> "Released vX.Y.Z. Issues closed on merge. GitHub Release vX.Y.Z created at `<url>`. Run `{{DEPLOY_PROD_CMD}}` to ship to production."
{{/if}}
{{#if BRANCH_DEV}}
{{#if !BRANCH_TEST}}
## Step 6 — Create PR: `{{BRANCH_DEV}}` → `{{BRANCH_PROD}}`

First, create a temp directory for this invocation:

```bash
mkdir -p /tmp/CodeCannon && mktemp -d /tmp/CodeCannon/XXXXXX
```

Note the returned path (e.g. `/tmp/CodeCannon/a8f3b2`). Use this path for all temp files in this invocation.

Then use your file-writing tool (not Bash) to create `<tmpdir>/release_pr_body.md`:

```markdown
Release vX.Y.Z

PRs included:
- #17 — Add /docs directory
- #18 — Fix checkout runtime error

Closes #14
Closes #15

Related to #20
```

Reproduce **every** `Closes #N` line from the close set computed in Step 2 — verbatim, one per line, omitting none. Add a `Related to #N` line for each issue in the reference set so the links appear on the release PR without triggering an auto-close. If the reference set is empty, omit the `Related to` lines entirely.

Then create the PR (do NOT use `--body`, `--body-file -`, or heredocs):

```bash
gh pr create --base {{BRANCH_PROD}} --head {{BRANCH_DEV}} \
  --title "Release vX.Y.Z" \
  --body-file <tmpdir>/release_pr_body.md
```

Note the PR number from the output.

The `Closes #N` lines will auto-close the linked issues because this PR merges into `{{BRANCH_PROD}}` (the default branch).

> **Critical:** Use the unqualified `#N` form only. Never write `Closes owner/repo#N`, even for same-repo refs — GitHub's closing-keyword parser only populates `closingIssuesReferences` for the unqualified form, and the qualified form silently breaks auto-close.

---

## Step 7 — Merge

Do NOT use `{{MERGE_CMD}}` — it refuses PRs targeting `{{BRANCH_PROD}}`. Use `gh pr merge` directly:

```bash
gh pr merge <pr-number> --merge
```

---

## Step 8 — Create GitHub Release

The version tag (from Step 3) and the PR/issue list (from Step 4) are already known. Find the previous tag to build the changelog link:

```bash
git describe --abbrev=0 <version-tag>^ 2>/dev/null
```

If no previous tag exists, omit the "Full changelog" line.

Use your file-writing tool (not Bash) to create `<tmpdir>/release_notes.md` (same temp directory from Step 6):

```markdown
## Changes

- #<issue> — <PR title> (PR #<pr-number>)
[... one line per PR included in this release ...]

**Full changelog:** https://github.com/<owner>/<repo>/compare/<previous-tag>...<version-tag>
```

Then create the release (do NOT use `--notes`, `--notes-file -`, or heredocs):

```bash
gh release create <version-tag> \
  --title "<version-tag>" \
  --notes-file <tmpdir>/release_notes.md
```

Format each PR line as `- #<linked-issue> — <PR title> (PR #<N>)`. If a PR had no linked issue, omit the `#<issue>` prefix and use just the PR title.

After the command runs, note the release URL from the output.

---

## Step 9 — Report

Tell the user:

> "Released vX.Y.Z. Issues #N, #M closed automatically. GitHub Release vX.Y.Z created at `<url>`. Run `{{DEPLOY_PROD_CMD}}` to ship to production."
{{/if}}
{{#if BRANCH_TEST}}
## Step 6 — Create PR: `{{BRANCH_TEST}}` → `{{BRANCH_PROD}}`

First, create a temp directory for this invocation:

```bash
mkdir -p /tmp/CodeCannon && mktemp -d /tmp/CodeCannon/XXXXXX
```

Note the returned path (e.g. `/tmp/CodeCannon/a8f3b2`). Use this path for all temp files in this invocation.

Then use your file-writing tool (not Bash) to create `<tmpdir>/release_pr_body.md`:

```markdown
Release vX.Y.Z

PRs included:
- #17 — Add /docs directory
- #18 — Fix checkout runtime error

Closes #14
Closes #15

Related to #20
```

Reproduce **every** `Closes #N` line from the close set computed in Step 2 — verbatim, one per line, omitting none. Add a `Related to #N` line for each issue in the reference set so the links appear on the release PR without triggering an auto-close. If the reference set is empty, omit the `Related to` lines entirely.

Then create the PR (do NOT use `--body`, `--body-file -`, or heredocs):

```bash
gh pr create --base {{BRANCH_PROD}} --head {{BRANCH_TEST}} \
  --title "Release vX.Y.Z" \
  --body-file <tmpdir>/release_pr_body.md
```

Note the PR number from the output.

The `Closes #N` lines will auto-close the linked issues because this PR merges into `{{BRANCH_PROD}}` (the default branch).

> **Critical:** Use the unqualified `#N` form only. Never write `Closes owner/repo#N`, even for same-repo refs — GitHub's closing-keyword parser only populates `closingIssuesReferences` for the unqualified form, and the qualified form silently breaks auto-close.

---

## Step 7 — Merge

Do NOT use `{{MERGE_CMD}}` — it refuses PRs targeting `{{BRANCH_PROD}}`. Use `gh pr merge` directly:

```bash
gh pr merge <pr-number> --merge
```

---

## Step 8 — Create GitHub Release

The version tag (from Step 3) and the PR/issue list (from Step 4) are already known. Find the previous tag to build the changelog link:

```bash
git describe --abbrev=0 <version-tag>^ 2>/dev/null
```

If no previous tag exists, omit the "Full changelog" line.

Use your file-writing tool (not Bash) to create `<tmpdir>/release_notes.md` (same temp directory from Step 6):

```markdown
## Changes

- #<issue> — <PR title> (PR #<pr-number>)
[... one line per PR included in this release ...]

**Full changelog:** https://github.com/<owner>/<repo>/compare/<previous-tag>...<version-tag>
```

Then create the release (do NOT use `--notes`, `--notes-file -`, or heredocs):

```bash
gh release create <version-tag> \
  --title "<version-tag>" \
  --notes-file <tmpdir>/release_notes.md
```

Format each PR line as `- #<linked-issue> — <PR title> (PR #<N>)`. If a PR had no linked issue, omit the `#<issue>` prefix and use just the PR title.

After the command runs, note the release URL from the output.

---

## Step 9 — Report

Tell the user:

> "Released vX.Y.Z. Issues #N, #M closed automatically. GitHub Release vX.Y.Z created at `<url>`. Run `{{DEPLOY_PROD_CMD}}` to ship to production."
{{/if}}
{{/if}}
