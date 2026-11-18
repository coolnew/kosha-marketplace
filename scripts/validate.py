#!/usr/bin/env python3
# SPDX-License-Identifier: MIT OR Apache-2.0
# SPDX-FileCopyrightText: 2026 Neeraj Sharma <neerajsharma.9@outlook.com> and The kosha contributors
"""Check catalog integrity; optionally validate DSL with a compatible Kosha CLI."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
PLATFORMS = {"linux", "windows", "macos"}
ID = r"[a-z0-9-]{1,80}"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def fields(value, required, optional=()):
    require(isinstance(value, dict), "expected an object")
    require(set(required) <= value.keys() <= set(required) | set(optional),
            f"unexpected or missing fields: {list(value)}")


def text(value, limit):
    return (isinstance(value, str) and bool(value.strip())
            and len(value.encode("utf-8")) <= limit
            and not any(unicodedata.category(c) == "Cc" for c in value))


def metadata(value):
    fields(value, ("id", "title", "description", "version"), ("tags",))
    require(text(value["id"], 80) and re.fullmatch(ID, value["id"]), "invalid pack ID")
    for name, limit in (("title", 120), ("description", 1024), ("version", 64)):
        require(text(value[name], limit), f"invalid metadata {name}")
    tags = value.get("tags", [])
    require(isinstance(tags, list) and len(tags) <= 32
            and all(text(tag, 64) for tag in tags), "invalid metadata tags")


def unique_object(pairs):
    value = {}
    for key, item in pairs:
        require(key not in value, f"duplicate JSON field: {key}")
        value[key] = item
    return value


def load(path, limit):
    require(not path.is_symlink(), f"symlink is not allowed: {path}")
    data = path.read_bytes()
    require(len(data) <= limit, f"file too large: {path}")
    require(b"\r" not in data and data.endswith(b"\n"), f"expected LF and final newline: {path}")
    return data, json.loads(data.decode("utf-8"), object_pairs_hook=unique_object)


def validate(root=ROOT, kosha=None):
    _, catalog = load(root / "catalog.json", 256 * 1024)
    fields(catalog, ("schema", "packages"))
    require(type(catalog["schema"]) is int and catalog["schema"] == 1, "unsupported catalog schema")
    entries = catalog["packages"]
    require(isinstance(entries, list) and 0 < len(entries) <= 256, "invalid package count")
    ids, paths = set(), set()
    for entry in entries:
        fields(entry, ("kind", "metadata", "platforms", "path", "sha256"))
        require(entry["kind"] == "recipe-pack", "unsupported package kind")
        metadata(entry["metadata"])
        pack_id = entry["metadata"]["id"]
        require(pack_id not in ids, f"duplicate pack ID: {pack_id}")
        ids.add(pack_id)
        path = entry["path"]
        require(isinstance(path, str) and re.fullmatch(r"recipes/" + ID + r"\.json", path),
                f"unsafe pack path: {path}")
        require(path not in paths, f"duplicate pack path: {path}")
        paths.add(path)
        require(not (root / "recipes").is_symlink(), "recipes directory must not be a symlink")
        platforms = entry["platforms"]
        require(isinstance(platforms, list) and len(platforms) <= 3
                and all(isinstance(p, str) and p in PLATFORMS for p in platforms), "invalid platforms")
        require(len(set(platforms)) == len(platforms), "duplicate platform")
        digest = entry["sha256"]
        require(isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest), "invalid SHA-256")
        data, pack = load(root / path, 1024 * 1024)
        require(hashlib.sha256(data).hexdigest() == digest, f"SHA-256 mismatch: {path}")
        fields(pack, ("schema", "kind", "metadata", "recipes"))
        require(type(pack["schema"]) is int and pack["schema"] == 1
                and pack["kind"] == "recipe-pack", f"unsupported pack format: {path}")
        metadata(pack["metadata"])
        require(pack["metadata"] == entry["metadata"], f"metadata mismatch: {path}")
        recipes = pack["recipes"]
        require(isinstance(recipes, list) and 0 < len(recipes) <= 256, f"invalid recipe count: {path}")
        seen, active = [], set()
        for recipe in recipes:
            fields(recipe, ("phrase", "dsl"), ("os",))
            require(text(recipe["phrase"], 256), "invalid recipe phrase")
            dsl = recipe["dsl"]
            require(isinstance(dsl, str) and dsl.strip()
                    and len(dsl.encode("utf-8")) <= 16384, "invalid recipe DSL")
            os_name = recipe.get("os")
            require(os_name is None or isinstance(os_name, str) and os_name in PLATFORMS, "invalid recipe OS")
            phrase = " ".join(recipe["phrase"].split()).lower()
            require(not any(phrase == old and (os_name is None or os_old is None or os_name == os_old)
                            for old, os_old in seen), f"duplicate recipe phrase: {phrase}")
            seen.append((phrase, os_name))
            active.update(PLATFORMS if os_name is None else {os_name})
        require(active == (set(platforms) if platforms else PLATFORMS),
                f"catalog platforms differ from recipe coverage: {path}")
        if kosha:
            subprocess.run([kosha, "search", "--describe", "--recipes", str(root / path), "files"], check=True)
        print(f"OK {pack_id} {entry['metadata']['version']}: {len(recipes)} recipes")
    actual = {p.relative_to(root).as_posix() for p in (root / "recipes").rglob("*.json")}
    require(actual == paths, "catalog must list every recipe pack exactly once")


def check_text_files(root=ROOT):
    # Include newly added, unignored files so the same check works before staging.
    result = subprocess.run(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                            cwd=root, check=True, capture_output=True)
    for name in set(result.stdout.decode("utf-8").split("\0")) - {""}:
        path = root / name
        require(not path.is_symlink(), f"tracked symlink is not allowed: {name}")
        data = path.read_bytes()
        if b"\0" in data:
            continue
        data.decode("utf-8")
        require(b"\r" not in data, f"CR line ending: {name}")
        require(not data or data.endswith(b"\n"), f"missing final newline: {name}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kosha", help="path to a compatible Kosha executable; also validate all DSL")
    args = parser.parse_args()
    try:
        check_text_files()
        validate(kosha=args.kosha)
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f"Validation failed: {error}", file=sys.stderr)
        return 1
    print("Catalog and LF checks passed." + (" DSL checked by Kosha." if args.kosha else " DSL requires Kosha validation."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
