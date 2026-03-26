---
name: status
description: Summarize in-progress and recently completed work from GitHub and git
---

> **Gemini CLI:** This skill is triggered by description matching. State any arguments in your message. Sub-agent spawning is not supported — the automated review step in `/ship` must be done manually using the review-agent prompt in a separate session.

---

## Step 1 — Parse arguments

First, check whether `$ARGUMENTS` contains `--milestone` or `--sprint` (they are identical aliases).

**Milestone mode:** If either flag is present, extract everything after `--milestone` or `--sprint` as the milestone name (trim leading/trailing whitespace; preserve internal spaces). Ignore any other arguments. Enter milestone mode (Steps M1–M3 below) and skip Steps 2–5.

Examples:
- `--milestone Sprint 4` → milestone name = `Sprint 4`
- `--sprint Sprint 4` → milestone name = `Sprint 4`
- `--milestone Q2 Release` → milestone name = `Q2 Release`
- `--milestone 12` → milestone name = `12`

**Personal mode** (no `--milestone` / `--sprint` flag): determine:

- **subject**: default `@me`. If the argument starts with `@` or is a plain word that is not a number, treat it as a GitHub username. Strip the leading `@` for `gh` commands that do not accept it (e.g. `gh pr list --author alice`); keep it for display.
- **lookback**: default `7`. If the argument is a number (digits only), use it as the lookback window in days.

No argument → subject = `@me`, lookback = `7`.

---

## Step 2 — Fetch GitHub data (run all three in parallel)

Run these commands concurrently:

**Open PRs authored by subject:**
```bash
gh pr list --author <subject> --state open \
  --json number,title,url,labels,milestone,baseRefName,body
```

**Recently merged PRs (last `<lookback>` days):**
```bash
gh pr list --author <subject> --state merged --limit 20 \
  --json number,title,url,mergedAt,labels,baseRefName
```
Filter the results to keep only entries where `mergedAt` is within the last `<lookback>` days.

**Open issues assigned to subject:**
```bash
gh issue list --assignee <subject> --state open \
  --json number,title,url,labels,milestone
```

If any `gh` command exits with a non-zero status (including auth errors), report the error message and stop. Do not retry.

---

## Step 3 — Fetch local git context

Check if the current directory is inside a git repository:
```bash
git rev-parse --is-inside-work-tree 2>/dev/null
```

If yes, run:
```bash
git log --oneline --since="<lookback> days ago"
```

If not inside a git repo, skip this step and note it was skipped in the output.

---

## Step 4 — Classify items

Using the data from Steps 2 and 3, classify each item:

- **In progress** — open PRs. For each, attempt to identify a linked issue number from the PR body (look for `#N`, `closes #N`, `fixes #N`, `issue #N`). If found, cross-reference with open issues.
- **Done** — merged PRs within the lookback window.
- **Up next** — open issues that are NOT associated with any open PR (i.e. no open PR body references their issue number).

An open issue that IS linked from an open PR body appears under "In progress" alongside that PR, not under "Up next".

---

## Step 5 — Output the summary

Print a formatted summary. Use this structure:

```
## Status for <subject> — last <lookback> days

### In progress
- #<number> <title> [<labels>] [<milestone>]
  PR: <url>
  Linked issue: #<number> (if found)

### Done
- #<number> <title> [<labels>] — merged <date>
  PR: <url>

### Up next
- #<number> <title> [<labels>] [<milestone>]
  Issue: <url>

---
Local commits (current branch):
<git log output, or "skipped — not in a git repo">
```

Rules:
- Omit any section that has no items — do not show an empty heading.
- Show labels only if present; show milestone only if present.
- Dates use `YYYY-MM-DD` format.
- If all three GitHub sections are empty, print: `Nothing found for <subject> in the last <lookback> days.`

Do not post, comment, write files, or take any action. Output only.

---

## Milestone mode (Steps M1–M3)

Only entered when `--milestone` or `--sprint` is detected in Step 1.

### Step M1 — Fetch milestone issues

```bash
gh issue list --milestone "<name>" --state all --limit 200 \
  --json number,title,state,labels,assignees,url
```

If this command fails for any reason (milestone not found, auth error, etc.), report the error and stop.

### Step M2 — Classify issues

Fetch all open PRs to detect which issues are in progress:

```bash
gh pr list --state open --json number,title,body,baseRefName
```

Group issues into three buckets:

- **Done** — `state: closed`
- **In progress** — `state: open` AND the issue number appears in any open PR body (look for `#<number>`, `closes #<number>`, `fixes #<number>`, `issue #<number>`)
- **Not started** — `state: open` AND no open PR body references the issue number

### Step M3 — Output the summary

```
## Sprint: <name>

<Y> of <total> issues closed · <Z> in progress · <W> not started

### In progress (<Z>)
- #<number> <title> [@<assignee>] [<milestone>]
  <url>

### Not started (<W>)
- #<number> <title> [@<assignee>]

### Done (<Y>)
- #<number> <title>
```

Rules:
- Show "In progress" first, then "Not started", then "Done"
- Show assignee only if present; omit if unassigned
- Show URLs only for in-progress items; omit URLs for closed issues
- If a section has no items, omit it entirely

Do not post, comment, write files, or take any action. Output only.

---

## Hard rules

- Never write to GitHub (no comments, labels, issue updates, or PR changes).
- Never suggest what the developer should work on next.
- If `gh` is unauthenticated or any fetch fails, report the error and stop immediately.
- Do not retry failed commands.
- Strip the leading `@` from the subject when passing to `gh` flags that do not accept it.
<!-- generated by CodeCanon/sync.sh | skill: status | adapter: gemini | hash: 74df8b14 | DO NOT EDIT — run CodeCanon/sync.sh to regenerate -->
