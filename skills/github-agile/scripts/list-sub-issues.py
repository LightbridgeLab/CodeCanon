#!/usr/bin/env python3
"""list-sub-issues — print the sub-issues of a parent issue as JSON.

Replaces the inline `gh api .../sub_issues --jq '.[] | {number,title,state}'`
pipeline at the /story call-site. The `--jq` filter (quoting + pipe) cannot be
statically analyzed by the harness permission system, so it prompts every
time. A single `python3 .../list-sub-issues.py <parent>` is a clean,
allow-listable command.

Output (stdout) is a JSON array, in the order GitHub returns them:
    [{"number": <n>, "title": "<t>", "state": "<s>"}, ...]

Usage:
    python3 CodeCannon/skills/github-agile/scripts/list-sub-issues.py <parent-issue-number>

Exit codes:
    0  success (JSON printed to stdout)
    2  gh subcommand failed or returned unparseable output
    3  bad arguments
"""

import json
import subprocess
import sys


def main(argv):
    if len(argv) != 2:
        print(f"Usage: {argv[0]} <parent-issue-number>", file=sys.stderr)
        return 3
    parent = argv[1]
    if not parent.isdigit():
        print(f"Error: parent issue number must be digits, got '{parent}'.", file=sys.stderr)
        return 3

    # gh resolves the {owner}/{repo} placeholders against the current repo.
    cmd = ['gh', 'api', f'repos/{{owner}}/{{repo}}/issues/{parent}/sub_issues', '--paginate']
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: command failed: {' '.join(cmd)}\n{result.stderr}", file=sys.stderr)
        return 2
    try:
        subs = json.loads(result.stdout or '[]')
    except json.JSONDecodeError as e:
        print(f"Error: could not parse gh output: {e}", file=sys.stderr)
        return 2

    out = [{'number': s['number'], 'title': s['title'], 'state': s['state']} for s in subs]
    print(json.dumps(out))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
