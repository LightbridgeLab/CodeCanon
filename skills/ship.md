---
skill: ship
description: Type-check, commit, open PR, review, and merge to the integration branch
args: none
---

## What `/ship` does

`/ship` is Phase 3 of the workflow: type-check, commit, open PR, spawn review agent, act on verdict.

---

## Step 1 — Verify branch

Check current branch:
```
git branch --show-current
```

If the current branch is `{{INTEGRATION_BRANCH}}` or `main`, **abort immediately** and say:

> "You are on `<branch>`. `/ship` must be run from a feature branch. Switch to your feature branch first."

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

If a linked issue number is identifiable, note it for the PR body (`Issue #N`). If not identifiable, proceed without it but mention this to the user.

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

Then create the PR with explicit title and body (never use an interactive editor):
```
gh pr create --base {{INTEGRATION_BRANCH}} --title "<title>" --body "$(cat <<'EOF'
<description of what changed and why>

Issue #<number>
EOF
)"
```

Include a reference to the issue (`Issue #<number>`) in the PR body if one was identified in Step 3. Do NOT use `Closes #N` here: merges go to `{{INTEGRATION_BRANCH}}` (not the default branch), so the keyword will never auto-close the issue.

---

## Step 6 — Spawn review agent

Load `{{REVIEW_AGENT_PROMPT}}` and invoke a review agent, passing the PR number. The review agent will:
1. Read the PR diff
2. Read relevant files for context
3. Post findings as a PR comment via `gh pr comment <number>`

Wait for the review agent to complete and report its verdict.

---

## Step 7 — Act on verdict

**If APPROVE (no CRITICAL findings):**
```
{{MERGE_CMD}}
```

Tell the user: **"PR merged. Issues stay open until testing confirms the fix — close them then, or when promoting to production. Run `{{DEPLOY_PREVIEW_CMD}}` when ready to deploy."**

**If REQUEST CHANGES (at least one CRITICAL finding):**
Report the findings to the user. Do NOT merge. Say:

> "The review found blocking issues (see above). Fix them and run `/ship` again."

Return to the coding loop. When fixed, run `/ship` again from Step 1.

---

## Important constraints

- Never skip `{{CHECK_CMD}}`. A failed check is a hard stop.
- Never merge if the review verdict is REQUEST CHANGES.
- Never merge to `main`. Merges are always to `{{INTEGRATION_BRANCH}}`.
- If `{{MERGE_CMD}}` fails for any reason, report it and stop — do not attempt workarounds.
