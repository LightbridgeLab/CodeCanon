#!/usr/bin/env python3
"""sync-base-branch — make a local branch a perfect mirror of its origin counterpart.

Performs the dirty-tree-guard + checkout + fetch + hard-reset sequence used by
/start (before branching off the base) and /deploy (before tagging). Replaces
the equivalent inlined shell so skill call-sites collapse to a single command.

Must be invoked from a working directory inside the target git repo (no `-C`
flag is passed to git). Skill call-sites already run from the project root, so
this is fine for the current use case.

Usage:
    python3 CodeCannon/skills/github-agile/scripts/sync-base-branch.py <branch>

Exit codes:
    0  success
    1  working tree has uncommitted or untracked changes
    2  a git subcommand failed
    3  bad arguments
"""

import subprocess
import sys


def main(argv):
    if len(argv) != 2:
        print(f"Usage: {argv[0]} <branch>", file=sys.stderr)
        return 3

    branch = argv[1]
    if not branch:
        print("Error: branch name is empty.", file=sys.stderr)
        return 3

    # Dirty-tree guard. `git status --porcelain` prints one line per staged,
    # unstaged, or untracked change — empty output means the tree is clean.
    status = subprocess.run(
        ['git', 'status', '--porcelain'],
        capture_output=True,
        text=True,
    )
    if status.returncode != 0:
        print("Error: 'git status' failed (is this a git repository?).", file=sys.stderr)
        return 2
    if status.stdout.strip():
        print(
            f"Working tree is not clean — resolve before syncing '{branch}'.\n"
            "  Commit, stash, or remove any uncommitted/untracked changes, then re-run.\n"
            "  Current status:",
            file=sys.stderr,
        )
        # Re-emit `git status --porcelain` output so the user sees exactly what's flagged.
        for line in status.stdout.splitlines():
            print(f"    {line}", file=sys.stderr)
        return 1

    # Checkout, fetch, hard-reset.
    for cmd in (
        ['git', 'checkout', branch],
        ['git', 'fetch', 'origin', branch],
        ['git', 'reset', '--hard', f'origin/{branch}'],
    ):
        result = subprocess.run(cmd)
        if result.returncode != 0:
            print(f"Error: command failed: {' '.join(cmd)}", file=sys.stderr)
            return 2

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
