# /start

Start a new feature or resume an existing issue.

**Source prompt:** [`../../skills/start.md`](../../skills/start.md)

## What it does

`/start` is the entry point for all work in Code Cannon. It has two modes:

- **New work** (text description) — reads the codebase, proposes an implementation approach, waits for human approval, creates a GitHub issue and linked feature branch, then writes the code.
- **Resume** (issue number) — loads an existing issue's context and comments, summarizes what was done and what remains, then picks up where work left off.

There is no path for committing code without an issue. The issue is the unit of work — the branch, PR, and commit history all link back to it.

## Usage

```
/start Add dark mode toggle to settings page
/start Fix the 404 on the Contact Us footer link
/start 42
```

### Inline flags

You can append flags after the description to override label and milestone selection:

```
/start Add dark mode --label enhancement
/start Add dark mode --label enhancement,ux --milestone "Sprint 4"
/start Fix login bug --milestone sprint-4
```

- `--label <value>` / `-l <value>` — use these labels verbatim instead of auto-selecting from the configured pool
- `--milestone <value>` / `-m <value>` — use this milestone instead of the configured default or auto-detection

Flags replace auto-selection entirely; they do not append.

## Step-by-step: new work

1. **Investigate** — the agent reads relevant code and proposes a concrete implementation approach, specifying which files change and how.

2. **Human gate** — the agent asks: *"Does this approach sound right? I'll create a GitHub issue and branch before writing any code."* Nothing happens until you confirm.

3. **Create GitHub issue** — runs `gh issue create` with a descriptive title, human-readable body, and resolved labels/milestone. Posts a technical implementation plan as an issue comment.

4. **Create feature branch** — runs `gh issue develop` to create a `feature/*` branch linked to the issue in GitHub. Verifies the branch before proceeding.

5. **Write the code** — implements the approach. Does NOT commit. Hands off to you: *"The code is ready for review. Please run your dev command and test locally."*

## Step-by-step: resume existing issue

1. **Load context** — reads the issue body, all comments, and any prior agent implementation notes.

2. **Summarize and gate** — tells you what the issue is about, what was done, and what remains. Asks if this matches your understanding.

3. **Check out branch** — finds or creates the linked feature branch.

4. **Write the code** — continues from where work left off. Does NOT commit.

## Label resolution

Labels are resolved in a three-tier order:

1. **Per-invocation flag** — `--label` value used verbatim
2. **Pool selection** — agent picks 1-3 fitting labels from `TICKET_LABELS` config
3. **No label** — if the pool is empty or nothing fits, the label is omitted (or a new one is created if `TICKET_LABEL_CREATION_ALLOWED` is `true`)

## Milestone resolution

Milestones are resolved in a three-tier order:

1. **Per-invocation flag** — `--milestone` value used verbatim
2. **Config default** — `DEFAULT_MILESTONE` from `.codecannon.yaml`
3. **Auto-detect** — queries GitHub for open milestones: uses a single milestone silently, prompts when multiple exist, omits when none exist

## Why it's built this way

**Issue-first workflow.** Every piece of work starts with an issue. This creates traceability from idea through branch, PR, and release. It also means `/start` can be used to create well-formed tickets without writing any code — useful for non-developers or planning sessions.

**Human gate before creation.** The agent proposes an approach and waits. This prevents wasted work on the wrong approach and gives you a chance to redirect before any GitHub artifacts are created.

**No commits during /start.** Code is written but not committed. This is intentional — the human testing loop between `/start` and `/ship` is where you catch things the agent missed. Committing happens in `/ship` after you've verified the code locally.

**Branch linking via `gh issue develop`.** Instead of `git checkout -b`, Code Cannon uses `gh issue develop` so the branch is linked to the issue in GitHub's UI. This makes it easy to find the branch from the issue and vice versa.

## Config keys used

- `DEV_CMD` — suggested to the user for local testing after code is written
- `ABANDON_CMD` — suggested if the user wants to scrap the work
- `TICKET_LABELS` — label pool for auto-selection
- `TICKET_LABEL_CREATION_ALLOWED` — whether new labels can be created on the fly
- `DEFAULT_MILESTONE` — default milestone for new issues
