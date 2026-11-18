#!/usr/bin/env python3
# SPDX-License-Identifier: MIT OR Apache-2.0
# SPDX-FileCopyrightText: 2026 Neeraj Sharma <neerajsharma.9@outlook.com> and The kosha contributors
"""Verify Developer Certificate of Origin sign-off on a range of commits.

    python xtask-dco.py [<range>]

With no argument, checks every commit reachable from HEAD. In CI, pass the
pull request's range, e.g. `origin/main..HEAD`.

Written in Python rather than as a shell loop for the same reason as the other
checks: one `git log` invocation instead of three per commit, which is the
difference between instant and a minute on a large history. It also puts the
rule in one place that a contributor can run locally and read.
"""
import re
import subprocess
import sys

SIGNOFF = re.compile(r"^Signed-off-by:\s*.+\s<[^>]+@[^>]+>\s*$", re.MULTILINE)
CO_AUTHOR = re.compile(r"^Co-authored-by:", re.MULTILINE | re.IGNORECASE)

# Record separator. Git expands `%x00` itself; a literal NUL byte in the
# argument vector is rejected by the OS, so it has to stay an escape until git
# sees it.
RECORD_END = "%x00%x00%x00"
SEP = "\x00\x00\x00"


def commits(rev_range):
    """Yield (sha, subject, parent_count, body) for each commit in the range."""
    out = subprocess.run(
        ["git", "log", "--format=%H%x00%s%x00%p%x00%B" + RECORD_END, rev_range],
        capture_output=True,
        check=True,
    ).stdout.decode("utf-8", "replace")

    for record in out.split(SEP):
        record = record.strip("\n")
        if not record:
            continue
        sha, subject, parents, body = record.split("\x00", 3)
        yield sha, subject, len(parents.split()), body


def main() -> int:
    rev_range = sys.argv[1] if len(sys.argv) > 1 else "HEAD"
    problems = []
    checked = 0

    try:
        found = list(commits(rev_range))
    except subprocess.CalledProcessError as e:
        print(f"could not read commits in `{rev_range}`: {e}")
        return 1

    for sha, subject, _parent_count, body in found:
        checked += 1
        label = f"{sha[:8]} {subject}"

        signoffs = len(SIGNOFF.findall(body))
        if signoffs == 0:
            problems.append((label, "missing a Signed-off-by line"))
        elif signoffs > 1 and len(set(SIGNOFF.findall(body))) > 1:
            # Several distinct sign-offs are legitimate on a co-developed
            # commit; several copies of the same one is a rebase accident.
            pass
        if CO_AUTHOR.search(body):
            problems.append(
                (label, "has a Co-authored-by trailer; authorship is recorded by sign-off")
            )

    for label, why in problems:
        print(f"{label}\n    {why}")

    if problems:
        print()
        print("Fix the most recent commit with:  git commit --amend -s --no-edit")
        print("Fix a whole branch with:          git rebase --signoff <base>")
        print("See CONTRIBUTING.md and DCO.")
        return 1

    print(f"All {checked} commits in `{rev_range}` are signed off.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
