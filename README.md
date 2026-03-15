# Agent Workflow Template

A portable, agent-agnostic workflow for AI-assisted development with human oversight. Drop-in `AGENTS.md`, config, review prompt, and Makefile targets that work with Claude Code, GitHub Copilot, Cursor, Windsurf, or any AI coding agent. Defines a three-phase workflow (Discovery → Implementation → Publish) with human gates, automated PR review via a spawned review agent, and safe branch management. Just copy the files into your project and customize.

## What's Included

| File | Purpose |
|---|---|
| `AGENTS.md` | The universal workflow spec — phases, human gates, branch strategy |
| `.agents/config.yaml` | Project-specific settings — branch names, commands, review options |
| `.agents/review-prompt.md` | Review agent prompt — spawned automatically to review PRs before merge |
| `Makefile.agents.mk` | Git workflow targets (`branch`, `pr`, `merge`, `abandon`) — includable in any Makefile |

## Usage

This is a GitHub template repository. Click **"Use this template"** on GitHub to create a new project with these files, then customize freely.

### Pulling upstream improvements

If improvements are made to the template after you've created your project, you can selectively pull them in:

```bash
# Add the template as a remote (one-time)
git remote add agentgate https://github.com/LightbridgeLab/agentgate.git

# Fetch and cherry-pick specific improvements
git fetch agentgate
git cherry-pick <commit-hash>
```

### Contributing improvements back

If you improve the workflow in your project and want to share it back, commit the change directly to your agentgate fork or open a PR against the original template.

## Setup

After creating your project from the template:

### 1. Copy files into place

The template files are ready to use at the root. If you're adding to an existing project instead, copy them in:

```bash
cp AGENTS.md /path/to/your/project/
cp -r .agents /path/to/your/project/
```

### 2. Add Makefile targets

Either include the provided Makefile fragment:

```makefile
# In your project's Makefile
include Makefile.agents.mk
```

Or copy the targets from `Makefile.agents.mk` directly into your existing Makefile.

### 3. Edit `.agents/config.yaml`

Customize for your project:

- **Branch names** — Change `integration` if you use `staging`, `dev`, etc.
- **Commands** — Point to your actual build/test/lint commands.
- **Phases** — Disable `discovery` for speed, `human_gates` for autonomy, `review_agent` to skip automated review.
- **Review categories** — Add or remove categories (e.g. `platform_compliance` for Cloudflare/AWS/etc. projects).

### 4. Point your agent config

Add a line to your agent's config file (e.g. `.claude/CLAUDE.md`, `.cursorrules`, etc.):

```
Follow the workflow in AGENTS.md. Commands are in .agents/config.yaml.
```

### 5. Add project-specific conventions

Add your project's coding conventions, architecture notes, etc. to the bottom of `AGENTS.md` (below the `---` separator), or keep them in your agent-specific config files.

## The Workflow

```
Phase 1: Discovery          Phase 2: Implementation       Phase 3: Publish
─────────────────           ───────────────────────       ────────────────
Read code                   Create feature branch         Create PR
Propose approach            Write code                    Review agent checks
  ↓ HUMAN GATE               ↓ HUMAN GATE                Merge (or fix + re-review)
"Sound right?"              "Test it, looks good?"        Done
```

Each phase has a human gate. The user can redirect, iterate, or abandon at any gate.

## Configuration Reference

### `.agents/config.yaml`

```yaml
workflow:
  branches:
    production: main           # Never commit directly
    integration: development   # PRs target this branch
    feature_prefix: "feature/" # Prefix for feature branches

  commands:
    create_branch: "make branch name={name}"
    dev_server: "make dev"
    build: "make build"
    test: "make test"
    lint: "make lint"
    create_pr: "make pr"
    merge_pr: "make merge"
    abandon: "make abandon"

  phases:
    discovery: true      # Propose before coding
    human_gates: true    # Wait for human confirmation
    review_agent: true   # Auto-review PRs before merge

  review:
    prompt: ".agents/review-prompt.md"
    categories:
      - correctness
      - security
      - conventions
      - code_quality
```

## Prerequisites

- `git`
- `gh` (GitHub CLI) — install with `brew install gh` and authenticate with `gh auth login`

## License

MIT
