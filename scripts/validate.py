#!/usr/bin/env python3
# SPDX-License-Identifier: MIT OR Apache-2.0
# SPDX-FileCopyrightText: 2026 Neeraj Sharma <neerajsharma.9@outlook.com> and The kosha contributors
"""Check generated catalog/indexes and LF; optionally run Kosha rule/corpus checks."""

import argparse
import importlib.util
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("marketplace_build", ROOT / "xtask-marketplace.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate(root=ROOT, kosha=None):
    root = root.resolve()
    outputs = builder.generated(root, Path(kosha).resolve() if kosha else None)
    current = {p.relative_to(root).as_posix() for p in (root / "indexes").glob("*.jsonl")}
    require(not current - outputs.keys(), "retired indexes must be removed explicitly")
    for name, data in outputs.items():
        path = builder.safe(root, name)
        require(not path.is_symlink(), f"generated file must not be a symlink: {name}")
        require(path.is_file() and path.read_bytes() == data, f"stale generated file: {name}")
    print("Catalog/index integrity passed." + (" Kosha rule and corpus checks passed." if kosha
                                              else " Rule semantics and corpus expectations require --kosha."))


def check_text_files(root=ROOT):
    # Include newly added, unignored files so the same check works before staging.
    result = subprocess.run(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                            cwd=root, check=True, capture_output=True)
    for name in set(result.stdout.decode("utf-8").split("\0")) - {""}:
        path = root / name
        require(not path.is_symlink(), f"tracked symlink is not allowed: {name}")
        if not path.exists():
            continue  # Tracked files deliberately deleted in the current change.
        data = path.read_bytes()
        if b"\0" in data:
            continue
        data.decode("utf-8")
        require(b"\r" not in data, f"CR line ending: {name}")
        require(not data or data.endswith(b"\n"), f"missing final newline: {name}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kosha", help="compatible Kosha executable for rule and corpus validation")
    args = parser.parse_args()
    try:
        check_text_files()
        validate(kosha=args.kosha)
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f"Validation failed: {error}", file=sys.stderr)
        return 1
    print("LF checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
