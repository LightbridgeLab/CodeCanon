---
skill: submit-for-review
type: skill
description: Type-check, commit, open PR, review, and merge to the integration branch
args: none
---

## What `/submit-for-review` does

`/submit-for-review` is Phase 3 of the workflow: type-check, commit, open PR, spawn review agent, act on verdict.

---

## Step 1 — Verify branch

Check current branch:
```
git branch --show-current
```

Protected branches (not a feature branch):
- `{{BRANCH_PROD}}`
{{#if BRANCH_DEV}}
- `{{BRANCH_DEV}}`
{{/if}}
{{#if BRANCH_TEST}}
- `{{BRANCH_TEST}}`
{{/if}}

If the current branch matches any of the above, **abort immediately** and say:

> "You are on `<branch>`. `/submit-for-review` must be run from a feature branch. Switch to your feature branch first."

---

## Step 2 — Type-check gate

Run:
```
{{CHECK_CMD}}
```

If errors are reported, **stop**. Report the errors to the user and say:

> "Check failed. Fix the errors above before shipping."

Do not proceed until `{{CHECK_CMD}}` passes cleanly.

---

## Step 3 — Identify linked issue

Check for a linked issue by inspecting the branch name (should follow `feature/<name>` linked via `gh issue develop`) or by running:
```
gh pr view --json number,body 2>/dev/null
```

If a linked issue number is identifiable, note it for the PR body. If not identifiable, proceed without it but mention this to the user.

---

## Step 4 — Sync with base branch

Bring the feature branch up to date before committing:

{{#if BRANCH_DEV}}
```
git fetch origin {{BRANCH_DEV}} && git merge origin/{{BRANCH_DEV}}
```
{{/if}}
{{#if !BRANCH_DEV}}
```
git fetch origin {{BRANCH_PROD}} && git merge origin/{{BRANCH_PROD}}
```
{{/if}}

If the merge completes cleanly (including fast-forward), proceed to Step 5.

If there are merge conflicts, **stop** and say:

> "Merge conflicts with `<base branch>`. Resolve them before shipping."

List the conflicting files. Help the user resolve them if asked, then continue.

---

## Step 5 — Commit

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

## Step 6 — Push and open PR

First, push the branch:
```
git push -u origin HEAD
```

Next, check for a CODEOWNERS file:
```
git ls-files CODEOWNERS .github/CODEOWNERS docs/CODEOWNERS 2>/dev/null
```

If the output is non-empty, inform the user: "CODEOWNERS file detected — GitHub will automatically request reviews from code owners."

{{#if BRANCH_DEV}}
PR target branch: `{{BRANCH_DEV}}`

Use `Issue #<number>` as the issue reference — the issue stays open until `/release` promotes to `{{BRANCH_PROD}}`.
{{/if}}
{{#if !BRANCH_DEV}}
PR target branch: `{{BRANCH_PROD}}` (trunk mode)

Use `Closes #<number>` as the issue reference — merging to the default branch will auto-close the issue.
{{/if}}

Then create the PR with explicit title and body (never use an interactive editor):
```
gh pr create --base <target-branch> --title "<title>" --body "$(cat <<'EOF'
<description of what changed and why>

<Closes #N  OR  Issue #N, based on target above>
EOF
)"
```

{{#if DEFAULT_REVIEWERS}}
Add `--reviewer` to the `gh pr create` command above using the handles from `{{DEFAULT_REVIEWERS}}`. Before passing them, strip any leading `@` from each comma-separated handle (e.g. `@alice,@org/team` becomes `alice,org/team`) — the `gh` CLI requires bare usernames.

If a CODEOWNERS file exists, both apply: CODEOWNERS triggers automatic review requests from GitHub; the `--reviewer` flag adds the explicitly configured handles on top.
{{/if}}

**Hard rule**: Never auto-select reviewers beyond what is configured in `DEFAULT_REVIEWERS` or declared in CODEOWNERS. Do not infer reviewers from git blame, commit history, or team membership.

Omit the issue line entirely if no linked issue was identified in Step 3.

---

## Step 7 — Review (conditional)

If `{{REVIEW_GATE}}` is `"off"`, skip directly to Step 8 (merge without review).

Otherwise, load `{{REVIEW_AGENT_PROMPT}}` and perform the review for this PR.

**If sub-agent spawning is supported** (e.g. Claude Code): invoke a dedicated review agent with the prompt and PR number.

**If sub-agent spawning is not supported** (e.g. Codex, Cursor, Gemini): perform the review yourself inline — follow the instructions in the review-agent prompt directly.

The review must:
1. Read the PR diff
2. Read relevant files for context
3. Post findings as a PR comment via `gh pr comment <number>`

Wait for the review to complete and report its verdict.

---

## Step 8 — Act on verdict

{{#if BRANCH_DEV}}
Merge command (used by all paths below): `{{MERGE_CMD}}`
{{/if}}
{{#if !BRANCH_DEV}}
Merge command (used by all paths below): `gh pr merge <number> --merge` (trunk mode — `{{MERGE_CMD}}` may refuse merges targeting `{{BRANCH_PROD}}`).
{{/if}}

---

**If `{{REVIEW_GATE}}` is `"off"` (review skipped):**

Run the merge command. Apply QA label and report success (see below).

---

**If `{{REVIEW_GATE}}` is `"advisory"`:**

Report the review findings to the user. Then merge regardless — treat as APPROVE.

If the review contained CRITICAL findings, note:

> "Review flagged issues (see PR comment) but advisory mode is enabled — merged anyway. Review the findings when convenient."

Apply QA label and report success (see below).

---

**If `{{REVIEW_GATE}}` is `"ai"` (default):**

**If APPROVE (no CRITICAL findings):** Run the merge command. Apply QA label and report success (see below).

**If REQUEST CHANGES (at least one CRITICAL finding):** Report the findings to the user. Do NOT merge. Say:

> "The review found blocking issues (see above). Fix them and run `/submit-for-review` again."

Return to the coding loop. When fixed, run `/submit-for-review` again from Step 1.

---

### After merge — QA label and success report

{{#if QA_READY_LABEL}}
{{#if BRANCH_DEV}}
{{#if !BRANCH_TEST}}
If a linked issue number was identified in Step 3, apply the QA label:
```
gh issue edit <number> --add-label "{{QA_READY_LABEL}}"
```
If no linked issue was found, skip silently.
{{/if}}
{{/if}}
{{/if}}

Report success based on mode:
{{#if !BRANCH_DEV}}
"PR merged. Issue #N closed automatically. Run `{{DEPLOY_PROD_CMD}}` when ready to deploy to production."
{{/if}}
{{#if BRANCH_DEV}}
{{#if !BRANCH_TEST}}
"PR merged. Issues stay open until testing confirms the fix. Run `{{DEPLOY_PREVIEW_CMD}}` when ready to deploy to preview."
{{/if}}
{{#if BRANCH_TEST}}
"PR merged to `{{BRANCH_DEV}}`. Promote to `{{BRANCH_TEST}}` when ready for staging."
{{/if}}
{{/if}}

---

## Important constraints

- Never skip `{{CHECK_CMD}}`. A failed check is a hard stop.
- When `{{REVIEW_GATE}}` is `"ai"`, never merge if the review verdict is REQUEST CHANGES.
- When `{{REVIEW_GATE}}` is `"advisory"`, always merge after review completes, regardless of verdict.
- When `{{REVIEW_GATE}}` is `"off"`, skip the review agent entirely — merge immediately after checks pass.
{{#if BRANCH_DEV}}
- `/submit-for-review` merges only to `{{BRANCH_DEV}}` — never directly to `{{BRANCH_PROD}}`.
{{/if}}
{{#if !BRANCH_DEV}}
- Merges target `{{BRANCH_PROD}}` (trunk mode).
{{/if}}
- If `{{MERGE_CMD}}` fails for any reason, report it and stop — do not attempt workarounds.
