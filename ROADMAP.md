# Roadmap

Ideas and future work. Not prioritized — just captured so they don't get lost.

## Swarm mode / multi-agent workflows

The current skill set (start/submit-for-review/review/version/release) assumes **deep mode**: one issue, one branch, one coherent PR. This works well for disciplined, sequential work.

In practice, developers often run multiple agents simultaneously on unrelated tasks — "swarm mode." This resists the ticket-per-change structure because the agents share a working directory and branch. Worktrees could isolate agents, but only Claude Code supports them natively; Cursor, Codex, and Gemini don't.

Possible additions:

- **`/checkpoint` skill** — commit and push WIP without the full ship ceremony. Gives save points during swarm mode without pretending each save is a reviewable unit.
- **Worktree launcher** — a `make agent name=<task>` target that creates a worktree, launches an agent with `/start`, and registers cleanup after `/submit-for-review`. Orchestration layer outside the skills themselves.
- **Conflict detection** — warn when multiple agents are modifying overlapping files on the same branch.

Decision for now: better discipline (one agent per issue, sequential) is the right path. Revisit when the pain of sequential work outweighs the cost of coordination tooling.

## Three-branch Makefile targets

GitHub issue #6. `Makefile.agents.mk` lacks `STAGING_BRANCH` support — no `promote` target, no staging guard rails. The skills handle three-branch mode but the Makefile doesn't.
