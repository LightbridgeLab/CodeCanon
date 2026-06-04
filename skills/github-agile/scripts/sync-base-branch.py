#!/usr/bin/env python3
"""sync-base-branch — make a local branch a perfect mirror of its origin counterpart.

Performs the dirty-tree-guard + checkout + fetch + hard-reset sequence used by
/start (before branching off the base) and /deploy (before tagging). Replaces
the equivalent inlined shell so skill call-sites collapse to a single command.

Usage:
    python3 CodeCannon/skills/github-agile/scripts/sync-base-branch.py <branch>

Exit codes:
    0  success
    1  working tree has uncommitted changes
    2  a git subcommand failed
    3  bad arguments
"""

import subprocess
import sys


def run(cmd):
    """Run a git command, streaming output. Returns the CompletedProcess."""
    return subprocess.run(cmd, check=False)


def main(argv):
    if len(argv) != 2:
        print(f"Usage: {argv[0]} <branch>", file=sys.stderr)
        return 3

    branch = argv[1]
    if not branch:
        print("Error: branch name is empty.", file=sys.stderr)
        return 3

    # Dirty-tree guard. Both unstaged and staged changes must be absent.
    unstaged = subprocess.run(['git', 'diff', '--quiet']).returncode
    staged = subprocess.run(['git', 'diff', '--cached', '--quiet']).returncode
    if unstaged != 0 or staged != 0:
        print(
            f"Uncommitted changes detected — resolve before syncing '{branch}'.\n"
            "  Commit, stash, or discard the changes, then re-run.",
            file=sys.stderr,
        )
        return 1

    # Checkout, fetch, hard-reset.
    for cmd in (
        ['git', 'checkout', branch],
        ['git', 'fetch', 'origin', branch],
        ['git', 'reset', '--hard', f'origin/{branch}'],
    ):
        result = run(cmd)
        if result.returncode != 0:
            print(f"Error: command failed: {' '.join(cmd)}", file=sys.stderr)
            return 2

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
