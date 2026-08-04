#!/usr/bin/env python3
"""label-audit — list configured labels that don't exist in the GitHub repo.

Reads `.codecannon.yaml` from the current working directory, collects the
labels that skills will try to apply at runtime (TICKET_LABELS pool plus the
three QA labels), then queries `gh label list` and emits the missing names —
one per line — on stdout. Used by /setup Phase 4 to catch the failure mode
where a configured label doesn't exist in the repo and a downstream skill
(/submit-for-review, /qa, /start) only finds out at the worst moment.

Stdout is intentionally minimal so the calling skill can do `if stdout is
non-empty: prompt the operator`. A one-line diagnostic goes to stderr for
transparency.

Usage:
    python3 CodeCannon/skills/github-agile/scripts/label-audit.py

Exit codes:
    0  audit completed (stdout may be empty or list missing labels)
    1  could not read .codecannon.yaml
    2  gh subcommand failed
"""

import json
import subprocess
import sys
from pathlib import Path


def _dequote(value):
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
        return value[1:-1]
    return value


def read_config_values(config_path):
    """Return the {key: value} pairs nested under the top-level `config:` key.

    Minimal flat-YAML reader — only covers what /setup writes: a `config:`
    block of `KEY: value` lines, indent 2, optional quotes. Block scalars
    (`|`) and other keys are ignored — the audit only needs string values.
    """
    text = config_path.read_text()
    values = {}
    in_config = False
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        indent = len(line) - len(line.lstrip())
        stripped = line.strip()
        if indent == 0:
            in_config = stripped == 'config:'
            continue
        if not in_config or indent != 2 or ':' not in stripped:
            continue
        key, _, value = stripped.partition(':')
        value = value.strip()
        if value == '|' or not value:
            continue
        values[key.strip()] = _dequote(value)
    return values


def collect_configured_labels(values):
    """Return the unique set of label names referenced by configured skills."""
    labels = set()
    pool = values.get('TICKET_LABELS', '')
    for name in pool.split(','):
        name = name.strip()
        if name:
            labels.add(name)
    for key in ('QA_READY_LABEL', 'QA_PASSED_LABEL', 'QA_FAILED_LABEL'):
        name = values.get(key, '').strip()
        if name:
            labels.add(name)
    return labels


def fetch_existing_labels():
    """Return the set of label names that exist in the current GitHub repo."""
    result = subprocess.run(
        ['gh', 'label', 'list', '--limit', '100', '--json', 'name'],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"Error: gh label list failed: {result.stderr.strip()}", file=sys.stderr)
        return None
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        print(f"Error: could not parse gh label list output: {exc}", file=sys.stderr)
        return None
    return {entry['name'] for entry in data}


def main(argv):
    config_path = Path('.codecannon.yaml')
    if not config_path.is_file():
        print(f"Error: {config_path} not found in current directory.", file=sys.stderr)
        return 1

    try:
        values = read_config_values(config_path)
    except OSError as exc:
        print(f"Error: could not read {config_path}: {exc}", file=sys.stderr)
        return 1

    configured = collect_configured_labels(values)
    if not configured:
        print("audited 0 configured labels (none set in .codecannon.yaml)", file=sys.stderr)
        return 0

    existing = fetch_existing_labels()
    if existing is None:
        return 2

    missing = sorted(configured - existing)
    print(
        f"audited {len(configured)} configured label(s); {len(missing)} missing",
        file=sys.stderr,
    )
    for name in missing:
        print(name)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
