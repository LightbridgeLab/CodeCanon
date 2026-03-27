# /review

Run a standalone code review on a pull request.

**Source prompt:** [`../../skills/review.md`](../../skills/review.md)

## What it does

`/review` runs a code review on any PR using the project's review agent prompt. It reads the PR diff, examines files for context, and posts structured findings as a PR comment.

This is the same review that `/submit-for-review` runs automatically — `/review` just lets you trigger it independently at any time.

## Usage

```
/review          # review the current branch's open PR
/review 42       # review PR #42
```

## Step-by-step

1. **Pre-flight** — if `REVIEW_GATE` is `off`, the skill aborts with a message explaining how to enable reviews.

2. **Identify the PR** — uses the argument as a PR number, or detects the current branch's open PR if no argument is given.

3. **Spawn review agent** — loads `REVIEW_AGENT_PROMPT` and invokes the review agent. The agent reads the diff, reads files for context, and posts findings as a PR comment.

4. **Report verdict** — relays the review agent's verdict:
   - **APPROVE** — no critical findings
   - **REQUEST CHANGES** — at least one critical finding; suggests fixing and re-running

## What the review agent checks

In priority order:

1. **Correctness** — logic errors, edge cases, regressions
2. **Security** — SQL injection, XSS, secrets in code, unsafe redirects
3. **Platform compliance** — project-specific rules from `PLATFORM_COMPLIANCE_NOTES`
4. **Conventions** — project-specific rules from `CONVENTIONS_NOTES`, plus commit message format
5. **Code quality** (light touch) — obvious duplication, misleading names, dead code

The review agent does NOT flag style preferences, documentation completeness, or future improvement suggestions.

## Why it's built this way

**Standalone and composable.** `/review` exists separately from `/submit-for-review` so you can review any PR at any time — not just as part of the shipping pipeline. It's useful for reviewing PRs from other contributors or re-reviewing after changes.

**Same prompt, same standards.** Both `/submit-for-review` and `/review` use the same `REVIEW_AGENT_PROMPT`, so reviews are consistent regardless of how they're triggered.

**Read-only.** `/review` never commits, pushes, or merges. It only reads and comments. This makes it safe to run at any point in the workflow.

**Customizable via config.** The review agent's knowledge of your project comes from `PLATFORM_COMPLIANCE_NOTES` and `CONVENTIONS_NOTES` in `.codecannon.yaml`. Without these, it runs generic checks. With them, it catches project-specific issues.

## Config keys used

- `REVIEW_GATE` — must not be `off` for `/review` to run
- `REVIEW_AGENT_PROMPT` — path to the review agent system prompt
- `PLATFORM_COMPLIANCE_NOTES` — platform-specific rules (via review-agent prompt)
- `CONVENTIONS_NOTES` — project conventions (via review-agent prompt)
