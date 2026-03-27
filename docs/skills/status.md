# /status

Read-only snapshot of open PRs, recently merged work, and open issues.

**Source prompt:** [`../../skills/status.md`](../../skills/status.md)

## What it does

`/status` generates a standup-style summary from GitHub data. It classifies work into three buckets — in progress, done, and up next — by cross-referencing open PRs, merged PRs, and open issues.

It also supports a milestone mode for sprint-level views.

## Usage

```
/status              # your work, last 7 days
/status 14           # your work, last 14 days
/status @alice       # alice's work, last 7 days
/status @alice 14    # alice's work, last 14 days
/status --milestone "Sprint 4"   # all issues in Sprint 4
/status --sprint "Sprint 4"      # same (alias)
```

## Personal mode (default)

Fetches three things in parallel:

- **Open PRs** authored by the subject
- **Recently merged PRs** within the lookback window
- **Open issues** assigned to the subject

Then classifies items:

- **In progress** — open PRs, with linked issues identified from PR bodies
- **Done** — merged PRs within the lookback window
- **Up next** — open issues with no associated open PR

Open issues that are linked from an open PR appear under "In progress", not "Up next".

## Milestone mode

When `--milestone` or `--sprint` is passed, `/status` fetches all issues in that milestone and classifies them by cross-referencing with open PRs:

- **Done** — closed issues
- **In progress** — open issues referenced in an open PR body
- **Not started** — open issues with no associated open PR

Shows a progress summary: "X of Y issues closed, Z in progress, W not started."

## What's next (personal mode only)

After the status summary, `/status` appends a single actionable suggestion based on local git state and the GitHub data already fetched. It evaluates conditions in priority order and shows the first match:

- **Feature branch with uncommitted changes** → "Run `/submit-for-review`"
- **Feature branch with approved PR and passing checks** → "Run `/deploy`"
- **Feature branch with open PR** → "Awaiting review"
- **Feature branch with no PR** → "Run `/submit-for-review` to open one"
- **Integration branch with unreleased commits since last tag** → "Run `/deploy`"
- **Nothing in progress** → "Run `/start`"
- **Open issues in backlog** → "Run `/start N` to pick one up"

This section is omitted in milestone mode and when no condition matches.

## Why it's built this way

**Read-only, always.** `/status` never writes to GitHub — no comments, labels, or issue updates. It's safe to run at any time without side effects.

**Cross-referenced classification.** Rather than relying on labels or project board columns, `/status` infers work state from the relationship between PRs and issues. An open issue with a linked open PR is "in progress" — no manual status tracking needed.

**Useful outside development.** `/status` generates standup summaries from GitHub data. It's valuable for project managers, team leads, or anyone who wants to see what's happening without reading code.

## Config keys used

None. `/status` uses only `gh` CLI commands and git log. It works with any Code Cannon configuration.
