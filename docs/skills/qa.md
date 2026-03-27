# /qa

View the QA queue or record findings on a specific issue.

**Source prompt:** [`../../skills/qa.md`](../../skills/qa.md)

## What it does

`/qa` provides a structured QA workflow for teams using two-branch development. It has two modes:

- **No argument** — lists all issues with the `QA_READY_LABEL`, showing the current QA queue.
- **Issue number** — walks through a QA review for a specific issue: prompts for testing findings, posts a structured comment, and applies a verdict label.

## Usage

```
/qa          # show all issues awaiting QA
/qa 42       # review issue #42
```

## Pre-flight

`/qa` requires `QA_READY_LABEL` to be set in `.codecannon.yaml`. Without it, the skill can't identify which issues are waiting for QA. If unset, it explains how to enable the label workflow.

The QA label workflow is primarily used in two-branch mode, where `/submit-for-review` automatically applies `QA_READY_LABEL` after merging a feature to `BRANCH_DEV`. In trunk or three-branch mode, the label must be applied manually.

## Queue view (no argument)

Queries GitHub for all open issues with the `QA_READY_LABEL` and displays them as a numbered list with issue number, title, milestone, and URL. Takes no other action.

## Issue review (numeric argument)

1. **Load context** — reads the issue body and comments. Warns if the issue doesn't have the `QA_READY_LABEL` (it may not be deployed yet).

2. **Review prompt** — asks you to test the feature on the preview environment and report your findings and verdict (pass or fail).

3. **Post findings** — builds a structured QA review comment with verdict, what was tested, findings, and screenshots. Shows the comment and asks for confirmation before posting to GitHub.

4. **Apply verdict label** — on pass, adds `QA_PASSED_LABEL` and removes `QA_READY_LABEL`. On fail, adds `QA_FAILED_LABEL`, removes `QA_READY_LABEL`, and CCs the issue's assignees in the comment.

## Why it's built this way

**Structured QA comments.** QA findings are posted as structured comments with a consistent format. This makes it easy to scan an issue's history and find the QA verdict, what was tested, and what was found.

**Label-driven workflow.** Using labels to track QA state means the queue is visible in GitHub's issue list without any external tools. `/qa` (no argument) simply queries for issues with the ready label.

**Human gate on posting.** The comment is shown to the QA person before posting. This prevents accidental verdicts and gives a chance to edit findings.

**Never closes issues.** `/qa` records the verdict but never closes the issue. Closure happens when `/deploy` promotes to production and the `Closes #N` reference triggers GitHub's auto-close. QA verdict and issue closure are separate concerns.

## Config keys used

- `QA_READY_LABEL` — label that identifies issues waiting for QA (required)
- `QA_PASSED_LABEL` — label applied on pass verdict
- `QA_FAILED_LABEL` — label applied on fail verdict
- `BRANCH_DEV` — relevant because QA labels are primarily used in two-branch mode
