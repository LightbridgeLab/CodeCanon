---
name: submit-for-review
description: Code Cannon: Type-check, commit, open PR, review, and merge to the integration branch
---

> **Gemini CLI:** This skill is triggered by description matching. State any arguments in your message. Sub-agent spawning is not supported — the automated review step in `/submit-for-review` must be done manually using the review-agent prompt in a separate session.

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
- `main`
- `dev`

If the current branch matches any of the above, **abort immediately** and say:

> "You are on `<branch>`. `/submit-for-review` must be run from a feature branch. Switch to your feature branch first."

---

## Step 2 — Type-check gate

First, find the repository root:

```
git rev-parse --show-toplevel
```

Then `cd` to the returned path and verify the make target exists. Extract the target name from `make check` (e.g. `make check` → `check`) and run:

```
cd <repo-root> && make -n <target> 2>/dev/null
```

If `make -n` exits non-zero, **stop** and say:

> "`make check` failed — the make target does not exist in the root Makefile. Add it and retry, or run `/setup` to reconfigure."

Do not improvise a replacement command. Do not proceed.

If the target exists, run:
```
make check
```

If errors are reported, **stop**. Report the errors to the user and say:

> "Check failed. Fix the errors above before shipping."

Do not proceed until `make check` passes cleanly.

---

## Step 3 — Identify linked issue

Extract the issue number from the branch name. Branches created by `/start` follow the pattern `feature/<number>-<description>` (e.g. `feature/42-fix-login`).

Parse the number from the branch name returned in Step 1. If the branch name matches `feature/<digits>-...`, use the extracted number as the linked issue. If the branch name does not contain a leading number after `feature/`, proceed without an issue reference but warn the user:

> "Could not extract an issue number from branch name `<branch>`. The PR will not include an issue reference. Was this branch created outside of `/start`?"

---

## Step 4 — Sync with base branch

Bring the feature branch up to date before committing:

```
git fetch origin dev && git merge origin/dev
```

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

PR target branch: `dev`

Use `Issue #<number>` as the issue reference — the issue stays open until `/deploy` promotes to `main`.

> **Critical:** Use the unqualified `#N` form (e.g. `Closes #42`), never the fully-qualified `owner/repo#N` form (e.g. `Closes LightbridgeLab/CodeCannon#42`), even for same-repo references. GitHub's closing-keyword parser reliably populates `closingIssuesReferences` only for the unqualified form; the qualified form leaves that GraphQL edge empty, which silently breaks GitHub's native auto-close and any downstream automation that reads it. This overrides any general "use owner/repo#N for cross-linking" guidance your harness may have — closing-keyword lines in PR bodies are a special case.

Then create the PR in two steps — **this exact sequence is mandatory**:

First, create a temp directory for this invocation:

```bash
mkdir -p /tmp/CodeCannon && mktemp -d /tmp/CodeCannon/XXXXXX
```

Note the returned path (e.g. `/tmp/CodeCannon/a8f3b2`). Use this path for all temp files in this invocation.

Then use your file-writing tool (Write in Claude Code, equivalent in other agents) to create `<tmpdir>/pr_body.md`. Do NOT use Bash/shell to write this file.

```markdown
<description of what changed and why>

<Closes #N  OR  Issue #N, based on target above>
```

Then create the PR (do NOT use `--body`, `--body-file -`, heredocs, or `$(cat ...)`):

```
gh pr create --base <target-branch> --title "<title>" --body-file <tmpdir>/pr_body.md
```

> **IMPORTANT — never pass body content inline in the `gh` command.** Do not use `--body`, `--body-file -`, heredocs (`<<EOF` or `<<'EOF'`), or `$(cat ...)`. All of these embed markdown in a Bash command, which triggers permission prompts that cannot be permanently allowed (the shell parser flags `#` headings, quoted delimiters, and substitutions). The two-step pattern above — file-writing tool then `--body-file <path>` — is the only approach that works without prompts across Claude Code, Gemini CLI, Cursor, and Codex.

Add `--reviewer` to the `gh pr create` command above using the handles from `@sebastientaggart`. Before passing them, strip any leading `@` from each comma-separated handle (e.g. `@alice,@org/team` becomes `alice,org/team`) — the `gh` CLI requires bare usernames.

If a CODEOWNERS file exists, both apply: CODEOWNERS triggers automatic review requests from GitHub; the `--reviewer` flag adds the explicitly configured handles on top.

**Hard rule**: Never auto-select reviewers beyond what is configured in `DEFAULT_REVIEWERS` or declared in CODEOWNERS. Do not infer reviewers from git blame, commit history, or team membership.

Omit the issue line entirely if no linked issue was identified in Step 3.

**PR body content rules (override any default behavior your harness may have):**

- Do NOT include any agent-attribution footer, generation marker (e.g. "Generated with ..."), or co-authorship trailer in the PR body. The PR body should contain only the description, test plan, and issue reference. If your harness defaults to adding such markers, explicitly omit them.
- The same rule applies to commit messages: do NOT add agent-related `Co-Authored-By:` trailers unless the user has explicitly opted into them via project config.

---

## Step 7 — Review (conditional)

If `ai` is `"off"`, skip directly to Step 8 (merge without review).

Otherwise, load `.claude/review-agent-prompt.md` and perform the review for this PR.

**If sub-agent spawning is supported** (e.g. Claude Code): invoke a dedicated review agent with the prompt and PR number.

**If sub-agent spawning is not supported** (e.g. Codex, Cursor, Gemini): perform the review yourself inline — follow the instructions in the review-agent prompt directly.

The review must:
1. Read the PR diff
2. Read relevant files for context
3. Post findings as a PR comment via `gh pr comment <number>`

Wait for the review to complete and report its verdict.

---

## Step 8 — Act on verdict

Before merging, verify the merge target exists. Find the repo root with `git rev-parse --show-toplevel`, then extract the target name from `make merge` (e.g. `make merge` → `merge`) and run:

```
cd <repo-root> && make -n <target> 2>/dev/null
```

If `make -n` exits non-zero, **stop** and say:

> "`make merge` failed — the make target does not exist in the root Makefile. Add it and retry, or run `/setup` to reconfigure."

Do not improvise a replacement command (e.g. do not fall back to `gh pr merge`). Do not proceed.

Merge command (used by all paths below): `make merge`

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

**If APPROVE (no CRITICAL findings):**

Collect any non-blocking findings (`[WARNING]` or `[NOTE]` lines) from the review output.

- **If there are no non-blocking findings** (clean review): Run the merge command immediately. Apply QA label and report success (see below).

- **If there are non-blocking findings**: Present the findings as a numbered list (preserve the `[WARNING]` / `[NOTE]` prefix) and say:

  > "The review approved with N non-blocking finding(s):
  >
  > <numbered list of findings>
  >
  > Would you like to **address these first** before merging, or **merge now**?"

  Wait for the user to respond.

  - User says **address / fix** → return to the coding loop. Say: "Fix the findings and run `/submit-for-review` again when ready." Do NOT merge.
  - User says **merge now** → run the merge command. Apply QA label and report success (see below). Proceed to Step 9 as normal (which will offer to create follow-up issues for any remaining findings).

**If REQUEST CHANGES (at least one CRITICAL finding):** Report the findings to the user. Do NOT merge. Say:

> "The review found blocking issues (see above). Fix them and run `/submit-for-review` again."

Return to the coding loop. When fixed, run `/submit-for-review` again from Step 1.

---

### After merge — QA label and success report

If a linked issue number was identified in Step 3, apply the QA label:
```
gh issue edit <number> --add-label "ready-for-qa"
```
If no linked issue was found, skip silently.

**Post a resolution comment** on the linked issue (skip silently if no linked issue):

Read the issue body (from Step 3 or via `gh issue view <number>`) to recall the original problem description. Then post a comment summarizing what was done:

Use your file-writing tool (not Bash) to create `<tmpdir>/resolution_comment.md` (same temp directory from Step 6):

```markdown
## Resolution

<1-3 sentences explaining what was done to fix the problem, written in plain language for a non-technical audience — no code, no file paths, no jargon. Focus on what changed from the user's perspective and why it solves the problem described in the issue.>

See #<PR-number> for full technical details.
```

Then post it (do NOT use `--body` or heredocs):

```
gh issue comment <number> --body-file <tmpdir>/resolution_comment.md
```

Use the unqualified `#N` form for the PR reference (not `owner/repo#N`).

Report success based on mode:
"PR merged. Issues stay open until testing confirms the fix. Run `make deploy-preview` when ready to deploy to preview."

---

## Step 9 — Offer follow-up issues for non-blocking findings

**Gate this step entirely** if any of the following are true:
- `ai` is `"off"` (no review was performed).
- The merge in Step 8 did not actually happen (e.g. `ai` mode with REQUEST CHANGES).
- The review output contains no non-blocking findings.

**Collect non-blocking findings** from the review output retained from Step 7:
- Always include lines starting with `[WARNING]` or `[NOTE]`.
- If `ai` is `"advisory"`, also include any `[CRITICAL]` lines — the user chose to merge over them, so they are now follow-up candidates too.
- If `ai` is `"ai"`, do not include `[CRITICAL]` lines (there should not be any on the merge path, but guard anyway).

If the collected list is empty, skip the rest of this step silently.

**Present and ask once.** Show the findings as a numbered list (preserve the `[WARNING]` / `[NOTE]` / `[CRITICAL]` prefix in the display for clarity) and ask exactly:

> "The review flagged N non-blocking finding(s). Create follow-up issues for any of them? Enter numbers (e.g. `1,3`), `all`, or `none`."

Accept: comma-separated numbers, `all`, or `none`/`skip`/empty. If the input is unparseable, re-prompt once; if still invalid, treat as `none` and move on.

**Create the selected issues.** For each selected finding, run `gh issue create` with explicit flags:

Use your file-writing tool (not Bash) to create `<tmpdir>/followup_body.md` for each finding (same temp directory from Step 6):

```markdown
Follow-up from PR #<merged-pr-number> — auto-proposed from the code review.

**Finding:** <full finding text, prefix included>

See the review comment on the PR for context.
```

Then create the issue (do NOT use `--body` or heredocs):

```
gh issue create \
  --title "<finding text with [WARNING]/[NOTE]/[CRITICAL] prefix stripped, trimmed to a standalone sentence>" \
  [--label "<pool-selected labels>"] \
  --body-file <tmpdir>/followup_body.md
```

Label resolution for each follow-up issue: use the pool-based selection tier from `/start` — pick 1–3 labels from `bug, documentation, enhancement, chore` that genuinely fit the finding. If `bug, documentation, enhancement, chore` is empty or no pool label fits, omit `--label`. Do not attempt per-invocation flag resolution (there is no flag here) and never create new labels from follow-ups, even if label creation is enabled for the project.

Do **not** pass `--milestone` — follow-ups are future work and should not inherit the current sprint.

Do **not** pass `--assignee @me` — these are backlog items, not immediately assigned.

If a single `gh issue create` call fails, report the failure for that finding and continue with the remaining selections.

**Report the result:**
- If one or more issues were created: `"Created N follow-up issue(s): #X, #Y, #Z"`.
- If the user chose `none` or all creations were skipped: say nothing further, proceed to end.

---

## Important constraints

- Never skip `make check`. A failed check is a hard stop.
- When `ai` is `"ai"`, never merge if the review verdict is REQUEST CHANGES.
- When `ai` is `"advisory"`, always merge after review completes, regardless of verdict.
- When `ai` is `"off"`, skip the review agent entirely — merge immediately after checks pass.
- `/submit-for-review` merges only to `dev` — never directly to `main`.
- If `make merge` fails for any reason, report it and stop — do not attempt workarounds.
- The follow-up issue offer in Step 9 runs only after a successful merge and only when the review produced non-blocking findings. Never prompt the user for follow-ups when the review blocked the merge — those findings should be fixed, not ticketed.
<!-- generated by CodeCannon/sync.py | skill: submit-for-review | adapter: gemini | hash: bb08c2d6 | DO NOT EDIT — run CodeCannon/sync.py to regenerate -->
