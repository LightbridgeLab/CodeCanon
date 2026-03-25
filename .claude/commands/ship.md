You are executing the `/ship` skill. Your argument is: $ARGUMENTS

---

<!-- Mode reference (derived from config at runtime):
     Trunk mode:       BRANCH_DEV empty, BRANCH_TEST empty  → PR targets BRANCH_PROD
     Two-branch mode:  BRANCH_DEV set,   BRANCH_TEST empty  → PR targets BRANCH_DEV
     Three-branch mode: BRANCH_DEV set,  BRANCH_TEST set    → PR targets BRANCH_DEV
-->

## What `/ship` does

`/ship` is Phase 3 of the workflow: type-check, commit, open PR, spawn review agent, act on verdict.

---

## Step 1 — Verify branch

Check current branch:
```
git branch --show-current
```

Determine which branches are protected (i.e., not a feature branch):
- Always: `main`
- If `dev` is non-empty: also `dev`
- If `` is non-empty: also ``

If the current branch matches any of the above, **abort immediately** and say:

> "You are on `<branch>`. `/ship` must be run from a feature branch. Switch to your feature branch first."

---

## Step 2 — Type-check gate

Run:
```
make check
```

If errors are reported, **stop**. Report the errors to the user and say:

> "Check failed. Fix the errors above before shipping."

Do not proceed until `make check` passes cleanly.

---

## Step 3 — Identify linked issue

Check for a linked issue by inspecting the branch name (should follow `feature/<name>` linked via `gh issue develop`) or by running:
```
gh pr view --json number,body 2>/dev/null
```

If a linked issue number is identifiable, note it for the PR body. If not identifiable, proceed without it but mention this to the user.

---

## Step 4 — Commit

Stage all changes and commit:
```
git add -A
git commit -m "<imperative-mood message>"
```

Commit message rules:
- Imperative mood ("Add X", "Fix Y", "Remove Z")
- Concise but meaningful — describes what changed and why in one line
- No `.env` files, build artifacts, `node_modules`, or secrets

---

## Step 5 — Push and open PR

First, push the branch:
```
git push -u origin HEAD
```

Next, check for a CODEOWNERS file:
```
git ls-files CODEOWNERS .github/CODEOWNERS docs/CODEOWNERS 2>/dev/null
```

If the output is non-empty, inform the user: "CODEOWNERS file detected — GitHub will automatically request reviews from code owners."

Determine the PR target branch:
- If `dev` is non-empty, target `dev` (two-branch or three-branch mode).
- Otherwise, target `main` (trunk mode).

Determine the issue reference format:
- If the PR targets `main` (trunk mode), use `Closes #<number>` — merging to the default branch will auto-close the issue.
- Otherwise, use `Issue #<number>` — the issue stays open until `/release` promotes to `main`.

Then create the PR with explicit title and body (never use an interactive editor):
```
gh pr create --base <target-branch> --title "<title>" --body "$(cat <<'EOF'
<description of what changed and why>

<Closes #N  OR  Issue #N, based on target above>
EOF
)"
```

If `` is non-empty, add `--reviewer ` to the `gh pr create` command above. If `` is empty, omit the `--reviewer` flag entirely — do not pass `--reviewer ""`.

If a CODEOWNERS file exists and `` is also set, both apply: CODEOWNERS triggers automatic review requests from GitHub; the `--reviewer` flag adds the explicitly configured handles on top.

**Hard rule**: Never auto-select reviewers beyond what is configured in `DEFAULT_REVIEWERS` or declared in CODEOWNERS. Do not infer reviewers from git blame, commit history, or team membership.

Omit the issue line entirely if no linked issue was identified in Step 3.

---

## Step 6 — Review (conditional)

If `ai` is `"off"`, skip directly to Step 7 (merge without review).

Otherwise, load `.claude/review-agent-prompt.md` and invoke a review agent, passing the PR number. The review agent will:
1. Read the PR diff
2. Read relevant files for context
3. Post findings as a PR comment via `gh pr comment <number>`

Wait for the review agent to complete and report its verdict.

---

## Step 7 — Act on verdict

Determine merge command (used by all paths below):
- If in **trunk mode** (`dev` is empty): use `gh pr merge <number> --merge` directly — `make merge` may refuse merges targeting `main`.
- Otherwise: use `make merge`.

---

**If `ai` is `"off"` (review skipped):**

Run the merge command. Apply QA label and report success (see below).

---

**If `ai` is `"advisory"`:**

Report the review findings to the user. Then merge regardless — treat as APPROVE.

If the review contained CRITICAL findings, note:

> "Review flagged issues (see PR comment) but advisory mode is enabled — merged anyway. Review the findings when convenient."

Apply QA label and report success (see below).

---

**If `ai` is `"ai"` (default):**

**If APPROVE (no CRITICAL findings):** Run the merge command. Apply QA label and report success (see below).

**If REQUEST CHANGES (at least one CRITICAL finding):** Report the findings to the user. Do NOT merge. Say:

> "The review found blocking issues (see above). Fix them and run `/ship` again."

Return to the coding loop. When fixed, run `/ship` again from Step 1.

---

### After merge — QA label and success report

Apply the QA label only in **two-branch mode** (`dev` is set AND `` is empty):
- If `` is non-empty AND a linked issue number was identified in Step 3:
  ```
  gh issue edit <number> --add-label ""
  ```
- In trunk mode or three-branch mode: skip the QA label entirely.
- If `` is empty or no linked issue was found: skip silently.

Report success based on mode:
- **Trunk mode**: "PR merged. Issue #N closed automatically. Run `make deploy-prod` when ready to deploy to production."
- **Two-branch mode**: "PR merged. Issues stay open until testing confirms the fix. Run `make deploy-preview` when ready to deploy to preview."
- **Three-branch mode**: "PR merged to `dev`. Promote to `` when ready for staging."

---

## Important constraints

- Never skip `make check`. A failed check is a hard stop.
- When `ai` is `"ai"`, never merge if the review verdict is REQUEST CHANGES.
- When `ai` is `"advisory"`, always merge after review completes, regardless of verdict.
- When `ai` is `"off"`, skip the review agent entirely — merge immediately after checks pass.
- In trunk mode, merges target `main`. Otherwise, `/ship` merges only to `dev` — never directly to `` or `main`.
- If `make merge` fails for any reason, report it and stop — do not attempt workarounds.
<!-- generated by CodeCanon/sync.sh | skill: ship | adapter: claude | hash: d98aef47 | DO NOT EDIT — run CodeCanon/sync.sh to regenerate -->
