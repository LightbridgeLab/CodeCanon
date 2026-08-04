#!/usr/bin/env python3
"""post-issue-comment — post a GitHub issue comment from a body file.

Wraps `gh issue comment <number> --body-file <path>` so skill call-sites can
collapse the mkdir/mktemp + gh invocation pattern into a single command. Used
by /start (agent implementation notes, investigation findings) and
/submit-for-review (resolution comment).

The agent writes the comment body to a file using its native file-writing
tool (markdown content must never be embedded in a shell command — the shell
parser flags `#` headings, quoted delimiters, and substitutions), then
invokes this script with the issue number and the file path.

Usage:
    python3 CodeCannon/skills/github-agile/scripts/post-issue-comment.py \\
        <issue-number> <body-file>

Exit codes:
    0  success
    1  body file is missing or empty
    2  gh subcommand failed
    3  bad arguments
"""

import subprocess
import sys
from pathlib import Path


def main(argv):
    if len(argv) != 3:
        print(f"Usage: {argv[0]} <issue-number> <body-file>", file=sys.stderr)
        return 3

    issue_number = argv[1]
    if not issue_number.isdigit():
        print(f"Error: issue number must be digits, got '{issue_number}'.", file=sys.stderr)
        return 3

    body_path = Path(argv[2])
    if not body_path.is_file():
        print(f"Error: body file not found: {body_path}", file=sys.stderr)
        return 1
    if body_path.stat().st_size == 0:
        print(f"Error: body file is empty: {body_path}", file=sys.stderr)
        return 1

    cmd = ['gh', 'issue', 'comment', issue_number, '--body-file', str(body_path)]
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"Error: command failed: {' '.join(cmd)}", file=sys.stderr)
        return 2

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
