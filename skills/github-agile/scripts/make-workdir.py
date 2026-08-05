#!/usr/bin/env python3
"""make-workdir — create a fresh temp working directory and print its path.

Replaces the `mkdir -p /tmp/CodeCannon && mktemp -d /tmp/CodeCannon/XXXXXX`
pattern at skill call-sites. That compound form (two commands joined with
`&&`) cannot be statically analyzed by the harness permission system, so it
prompts on every run and can never be "always allowed". A single
`python3 .../make-workdir.py` invocation is a clean, allow-listable command.

The directory is created under /tmp/CodeCannon so it shares the temp-file
conventions used across the skills. The absolute path — and nothing else — is
printed to stdout, so a skill can capture it directly.

Usage:
    python3 CodeCannon/skills/github-agile/scripts/make-workdir.py

Exit codes:
    0  success (path printed to stdout)
    2  could not create the directory
"""

import sys
import tempfile
from pathlib import Path


def main(argv):
    base = Path('/tmp/CodeCannon')
    try:
        base.mkdir(parents=True, exist_ok=True)
        workdir = tempfile.mkdtemp(dir=str(base))
    except OSError as e:
        print(f"Error: could not create work directory: {e}", file=sys.stderr)
        return 2
    print(workdir)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
