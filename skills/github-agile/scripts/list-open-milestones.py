#!/usr/bin/env python3
"""list-open-milestones — print open milestones for the current repo as JSON.

Replaces the inline `gh api repos/{owner}/{repo}/milestones --jq '...'`
pipeline at the /start call-site. The `--jq` filter (quoting + pipe) cannot be
statically analyzed by the harness permission system, so it prompts every
time. A single `python3 .../list-open-milestones.py` is a clean,
allow-listable command.

Output (stdout) is a JSON object:
    {"count": <n>, "milestones": [{"number": <n>, "title": "<t>"}, ...]}

Usage:
    python3 CodeCannon/skills/github-agile/scripts/list-open-milestones.py

Exit codes:
    0  success (JSON printed to stdout)
    2  gh subcommand failed or returned unparseable output
"""

import json
import subprocess
import sys


def main(argv):
    # gh resolves the {owner}/{repo} placeholders against the current repo.
    cmd = ['gh', 'api', 'repos/{owner}/{repo}/milestones', '--paginate']
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: command failed: {' '.join(cmd)}\n{result.stderr}", file=sys.stderr)
        return 2
    try:
        milestones = json.loads(result.stdout or '[]')
    except json.JSONDecodeError as e:
        print(f"Error: could not parse gh output: {e}", file=sys.stderr)
        return 2

    open_ms = [m for m in milestones if m.get('state') == 'open']
    out = {
        'count': len(open_ms),
        'milestones': [{'number': m['number'], 'title': m['title']} for m in open_ms],
    }
    print(json.dumps(out))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
