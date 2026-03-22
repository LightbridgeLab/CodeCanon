---
skill: start
description: Start a new feature or bugfix
args: "feature description or issue number"
---

## CRITICAL: Order of operations

**You must complete Steps 1–4 before writing any code.**
Do not open any source file with intent to edit until `git branch --show-current` shows a `feature/*` branch.

---

## Determine case

If `$ARGUMENTS` is a number (digits only) → go to **Case B: Resume existing issue**.
Otherwise → go to **Case A: New work**.

---

## Case A: New work (text description)

### Step 1 — Investigate

Read the relevant code. Propose a concrete implementation approach. Be specific about which files change and how.

### Step 2 — HUMAN GATE

Say exactly: **"Does this approach sound right? I'll create a GitHub issue and branch before writing any code."**

Stop. Wait for the user to confirm.

- User says yes → continue to Step 3.
- User redirects → revise approach, ask again.
- User abandons → stop. Nothing to clean up.

### Step 3 — Create GitHub Issue

Run `gh issue create` with explicit flags (do NOT open an interactive editor):

```bash
gh issue create \
  --title "<standalone full sentence — must make sense with no context>" \
  --body "<human-readable explanation: what the problem is, why it matters, general approach — written for a non-developer, no code or file paths>"
```

**Title rules:**
- ✅ `Fix 'Contact Us' footer link pointing to 404 instead of /contact-us`
- ❌ `Fix broken link`

After the command runs, note the issue number from the output URL (e.g. `https://github.com/.../issues/42` → issue `42`).

Show the user: `Created issue #<number>: <title>`

Then immediately post agent implementation notes as a comment:

```bash
gh issue comment <number> --body "## Agent Implementation Notes

<full technical plan: exact files to change, approach, key decisions, edge cases>"
```

### Step 4 — Create feature branch

```bash
gh issue develop <number> --name feature/<short-descriptive-name> --checkout
```

Verify the branch was created:

```bash
git branch --show-current
```

Show the user: `On branch feature/<name>`

**Do not proceed to Step 5 until this shows a `feature/*` branch.**

### Step 5 — Write the code

Now write the code. Do NOT commit anything.

When done, say: **"The code is ready for review. Please run `{{DEV_CMD}}` and test locally. Let me know if it looks good, needs changes, or should be scrapped."**

- User says looks good → run `/ship`
- User requests changes → iterate, repeat this message
- User says scrap it → run `{{ABANDON_CMD}}`

---

## Case B: Resume existing issue (numeric argument)

### Step 1 — Load context

```bash
gh issue view <number> --comments
```

Read the full body and all comments. Note: what was done, what remains, branch status.

### Step 2 — Summarize and gate

Tell the user:
- What the issue is about
- What was previously done (from agent notes if present)
- What appears to remain

Ask: **"Does this match your understanding? Continue this ticket, or open a fresh one?"**

- Continue → Step 3.
- New ticket → restart as Case A with a new description.

### Step 3 — Check out branch

Find and check out the existing branch, or create a new one linked to the issue:

```bash
gh issue develop <number> --name feature/<short-name> --checkout
```

Verify:

```bash
git branch --show-current
```

Post a resumption comment:

```bash
gh issue comment <number> --body "Resuming work. <brief note on what's being continued.>"
```

### Step 4 — Write the code

Continue from where work left off. Do NOT commit.

When done, say: **"The code is ready for review. Please run `{{DEV_CMD}}` and test locally."**

---

## Hard rules

- Do not write or edit any source file before `git branch --show-current` shows `feature/*`.
- Do not use `make branch` — always use `gh issue develop` so the branch is linked to the issue in GitHub.
- Do not commit during `/start` — commits happen in `/ship`.
- If already on a feature branch when `/start` is invoked, warn the user before creating another branch.
- `gh issue create` must use `--title` and `--body` flags. Never open an interactive editor.
