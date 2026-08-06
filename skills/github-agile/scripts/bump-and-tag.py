#!/usr/bin/env python3
"""bump-and-tag — run a version bump, verify the tag, and push commit + tag.

Wraps the bump-verify-push sequence used by /deploy Step 3 so the agent
doesn't narrate it step-by-step. The project-specific bump and version-read
commands are passed in as opaque shell strings (the same template variables
the skill already uses: {{BUMP_PATCH_CMD}}, {{VERSION_READ_CMD}}, etc.), so
this script is agnostic to whether the project uses Make, npm, uv, or a
custom script.

Defensive behaviour:
1. Run the bump command. Bail on non-zero exit.
2. Re-read the version via the version-read command.
3. Check `git tag -l "v<version>"`. If missing (e.g. tag.forceSignAnnotated
   silently rejected a lightweight tag), create an annotated tag as a
   fallback.
4. Push the commit and the tag. Both must succeed.

The resolved version is printed to stdout on success so the calling skill
can capture it for the release step. All diagnostics go to stderr.

Usage:
    python3 .../bump-and-tag.py --bump-cmd <shell> --version-read-cmd <shell>

Exit codes:
    0  success (version printed to stdout)
    1  bump command failed
    2  version-read command failed or produced no output
    3  tag creation or push failed

Bad arguments (missing/invalid --bump-cmd or --version-read-cmd) are handled
by argparse, which prints a usage message and exits 2.
"""

import argparse
import subprocess
import sys


def run_shell(cmd, *, capture=False):
    """Run a shell command string. Returns CompletedProcess."""
    return subprocess.run(cmd, shell=True, text=True, capture_output=capture)


def main(argv):
    parser = argparse.ArgumentParser(
        prog=argv[0],
        description="Run a version bump, verify the resulting tag, and push.",
    )
    parser.add_argument(
        '--bump-cmd',
        required=True,
        help="Shell command that bumps the version, commits, and tags "
             "(e.g. 'make bump-patch', 'npm version patch').",
    )
    parser.add_argument(
        '--version-read-cmd',
        required=True,
        help="Shell command that prints the current version to stdout "
             "(e.g. 'node -p \"require(\\'./package.json\\').version\"').",
    )
    args = parser.parse_args(argv[1:])

    # 1. Run the bump.
    bump = run_shell(args.bump_cmd)
    if bump.returncode != 0:
        print(f"Error: bump command failed: {args.bump_cmd}", file=sys.stderr)
        return 1

    # 2. Re-read the version.
    read = run_shell(args.version_read_cmd, capture=True)
    if read.returncode != 0:
        print(
            f"Error: version-read command failed: {args.version_read_cmd}\n"
            f"  stderr: {read.stderr.strip()}",
            file=sys.stderr,
        )
        return 2
    version = read.stdout.strip()
    if not version:
        print(
            f"Error: version-read command produced no output: {args.version_read_cmd}",
            file=sys.stderr,
        )
        return 2

    tag = f"v{version}"

    # 3. Verify the tag exists; fall back to an annotated tag if not.
    check = subprocess.run(
        ['git', 'tag', '-l', tag],
        capture_output=True,
        text=True,
    )
    if check.returncode != 0:
        print("Error: 'git tag -l' failed.", file=sys.stderr)
        return 3
    if not check.stdout.strip():
        print(
            f"Tag {tag} not found after bump — creating annotated tag "
            "(bump command likely produced a lightweight tag that was "
            "rejected by tag.forceSignAnnotated).",
            file=sys.stderr,
        )
        fallback = subprocess.run(['git', 'tag', '-a', tag, '-m', tag])
        if fallback.returncode != 0:
            print(f"Error: failed to create annotated tag {tag}.", file=sys.stderr)
            return 3

    # 4. Push commit and tag.
    for cmd in (['git', 'push'], ['git', 'push', '--tags']):
        result = subprocess.run(cmd)
        if result.returncode != 0:
            print(f"Error: command failed: {' '.join(cmd)}", file=sys.stderr)
            return 3

    # Emit the resolved version so the caller can capture it.
    print(version)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
