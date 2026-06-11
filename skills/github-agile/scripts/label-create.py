#!/usr/bin/env python3
"""label-create — create GitHub labels with sensible defaults.

Wraps `gh label create` so call-sites don't have to improvise colors and
descriptions. A baked-in table covers the names skills commonly reference
(bug, enhancement, documentation, chore, ready-for-qa, qa-passed,
qa-failed). For any other name — including operator-renamed QA labels
(e.g. QA_PASSED_LABEL: "tested") — falls back to neutral gray with no
description; the operator can refine later in the GitHub UI.

Used by /setup Phase 4 in two places: the greenfield baseline create when
the repo has zero labels, and the configured-label audit when one or more
labels referenced by .codecannon.yaml don't yet exist in the repo.

Per the warn-and-continue posture established in #182, a single label
that fails to create (typically because it already exists) prints a
one-line warning and the script moves on to the next name. Exit is 0 as
long as the loop completed; only argument errors abort.

Usage:
    python3 CodeCannon/skills/github-agile/scripts/label-create.py <name>...

Exit codes:
    0  loop completed (individual labels may have warned to stderr)
    3  no label names provided
"""

import subprocess
import sys

# Default color and description for well-known label names. Colors are the
# GitHub defaults where they exist (bug, enhancement, documentation) and
# conventional traffic-light choices for the QA labels.
DEFAULTS = {
    'bug':           ('d73a4a', "Something isn't working"),
    'enhancement':   ('a2eeef', 'New feature or request'),
    'documentation': ('0075ca', 'Improvements or additions to documentation'),
    'chore':         ('cccccc', 'Routine maintenance'),
    'ready-for-qa':  ('fbca04', 'Ready for QA review'),
    'qa-passed':     ('0e8a16', 'Passed QA review'),
    'qa-failed':     ('e11d21', 'Failed QA review'),
}

FALLBACK_COLOR = 'cccccc'


def main(argv):
    if len(argv) < 2:
        print(f"Usage: {argv[0]} <name>...", file=sys.stderr)
        return 3

    for name in argv[1:]:
        color, description = DEFAULTS.get(name, (FALLBACK_COLOR, ''))
        cmd = ['gh', 'label', 'create', name, '--color', color]
        if description:
            cmd += ['--description', description]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            stderr = result.stderr.strip() or '(no stderr)'
            print(f"Warning: failed to create label '{name}': {stderr}", file=sys.stderr)
            continue
        print(f"Created label: {name}")

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
