# /status

Read-only snapshot of open PRs, recently merged work, and open issues — with health indicators, stale detection, and team-wide views.

**Source prompt:** [`../../skills/github-agile/status.md`](../../skills/github-agile/status.md)

## What it does

`/status` generates a standup-style summary from GitHub data. It classifies work into buckets — in progress, done, up next, and needs your review — by cross-referencing open PRs, merged PRs, and open issues. Each open PR shows health badges for CI checks, review decision, draft status, and merge conflicts.

It supports three modes: personal (default), milestone, and team.

## Usage

```
/status              # your work, last 7 days
/status 14           # your work, last 14 days
/status @alice       # alice's work, last 7 days
/status @alice 14    # alice's work, last 14 days
/status --milestone "Sprint 4"   # all issues in Sprint 4
/status --sprint "Sprint 4"      # same (alias)
/status --team                   # all open work across the team
```

## Personal mode (default)

Fetches four things in parallel:

- **Open PRs** authored by the subject (with health fields: checks, review decision, mergeable, draft status)
- **Recently merged PRs** within the lookback window
- **Open issues** assigned to the subject
- **PRs requesting your review** (only when subject is `@me`)

Then classifies items:

- **In progress** — open PRs, with linked issues identified from PR bodies. Each shows health badges.
- **Done** — merged PRs within the lookback window
- **Needs your review** — PRs where your review has been requested (only for `@me`)
- **Up next** — open issues with no associated open PR

Open issues that are linked from an open PR appear under "In progress", not "Up next".

A summary counts line appears at the top: `3 in progress · 2 done · 4 up next · 1 need your review`

### Health badges

Each open PR in "In progress" shows:

- **Draft**: `[draft]` if the PR is a draft
- **CI checks**: `✅ checks passing`, `❌ checks failing`, or `⏳ checks pending`
- **Review decision**: `✅ approved`, `🔄 changes requested`, or `⏳ awaiting review`
- **Merge conflicts**: `⚠️ conflicts` if the PR cannot be cleanly merged

### Stale detection

Items not updated within the configured threshold (`STALE_DAYS`, default 14) get a `⚠️ stale (<N>d)` badge and appear in a consolidated "Stale" section at the bottom.

## Milestone mode

When `--milestone` or `--sprint` is passed, `/status` fetches all issues in that milestone and classifies them by cross-referencing with open PRs:

- **Done** — closed issues
- **In progress** — open issues referenced in an open PR body (with health badges from the linked PR)
- **Not started** — open issues with no associated open PR

Shows a progress summary: "X of Y issues closed, Z in progress, W not started."

## Team mode

When `--team` is passed, `/status` fetches all open PRs and issues across the entire repo (no author/assignee filter) and groups them by person. Each person's section shows their in-progress items (with health badges) and up-next items. Unassigned issues appear in their own group. Stale items are consolidated at the bottom.

Team mode is designed for standups and team leads who need the full picture in one command.

## What's next (personal mode only)

After the status summary, `/status` appends a single actionable suggestion based on local git state and the GitHub data already fetched. It evaluates conditions in priority order and shows the first match:

- **Feature branch with uncommitted changes** → "Run `/submit-for-review`"
- **Feature branch with approved PR and passing checks** → "Run `/deploy`"
- **Feature branch with open PR** → "Awaiting review"
- **PRs requesting your review** → "You also have N PR(s) awaiting your review" (appended to above)
- **Feature branch with no PR** → "Run `/submit-for-review` to open one"
- **Integration branch with unreleased commits since last tag** → "Run `/deploy`"
- **Nothing in progress** → "Run `/start`"
- **Open issues in backlog** → "Run `/start N` to pick one up"

This section is omitted in milestone mode, team mode, and when no condition matches.

## Why it's built this way

**Read-only, always.** `/status` never writes to GitHub — no comments, labels, or issue updates. It's safe to run at any time without side effects.

**Cross-referenced classification.** Rather than relying on labels or project board columns, `/status` infers work state from the relationship between PRs and issues. An open issue with a linked open PR is "in progress" — no manual status tracking needed.

**Health at a glance.** A PR with failing checks or requested changes needs immediate attention but without badges looks identical to one awaiting first review. Health indicators surface this without clicking through GitHub.

**Useful outside development.** `/status` generates standup summaries from GitHub data. It's valuable for project managers, team leads, or anyone who wants to see what's happening without reading code. Team mode extends this to the whole repo.

## Config keys used

| Key | Default | Description |
|-----|---------|-------------|
| `STALE_DAYS` | `14` | Days after which open PRs/issues are flagged as stale. Set to `0` to disable. |
