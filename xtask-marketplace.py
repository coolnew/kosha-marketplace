#!/usr/bin/env python3
# SPDX-License-Identifier: MIT OR Apache-2.0
# SPDX-FileCopyrightText: 2026 Neeraj Sharma <neerajsharma.9@outlook.com> and The kosha contributors

"""Generate a deterministic marketplace catalog/indexes from package manifests.

Edit packages/**/manifest.json and package artifacts. --check never writes.
No network requests, Git operations, publication, or version changes occur.
"""

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
MAX_ROOT = 256 * 1024
MAX_SHARD = 2 * 1024 * 1024
MAX_TOTAL = 16 * 1024 * 1024
MAX_ENTRIES = 16384
MAX_ARTIFACT = 1024 * 1024
KINDS = {"recipe-pack": "recipes", "plugin": "plugins"}


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def token(value):
    return isinstance(value, str) and re.fullmatch(r"[a-z0-9][a-z0-9-]{0,79}", value) is not None


def safe(root, name):
    if not isinstance(name, str):
        raise ValueError("Expected a relative artifact path")
    path = PurePosixPath(name)
    if not name or path.is_absolute() or path.as_posix() != name or any(part in {".", ".."} for part in path.parts) or any(char in name for char in "\\:%?#"):
        raise ValueError(f"Unsafe marketplace path: {name}")
    target = root / name
    for parent in (target, *target.parents):
        if parent.is_symlink() or getattr(parent, "is_junction", lambda: False)():
            raise ValueError("Marketplace paths must not traverse links")
    if not target.resolve().is_relative_to(root.resolve()):
        raise ValueError("Marketplace artifact escapes its root")
    return target


def metadata(value):
    fields = {"id", "publisher", "title", "description", "version", "tags"}
    if not isinstance(value, dict) or set(value) - fields or not {"id", "title", "description", "version"} <= value.keys():
        raise ValueError("Invalid package metadata fields")
    if not token(value["id"]) or not token(value.get("publisher")):
        raise ValueError("Package ID and publisher must be lowercase identifiers")
    for name, limit in [("title", 120), ("description", 1024), ("version", 64)]:
        text = value[name]
        if not isinstance(text, str) or not text.strip() or len(text.encode()) > limit or any(ord(c) < 32 or ord(c) == 127 for c in text):
            raise ValueError(f"Invalid package {name}")
    version = value["version"]
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.+-]{0,63}", version):
        raise ValueError("Version must be a safe directory component")
    tags = value.get("tags", [])
    if not isinstance(tags, list) or len(tags) > 32 or any(not isinstance(t, str) or not t.strip() or len(t.encode()) > 64 or any(ord(c) < 32 or ord(c) == 127 for c in t) for t in tags):
        raise ValueError("Invalid package tags")


def generated(root, cli=None):
    root = root.resolve()
    manifests = sorted((root / "packages").rglob("manifest.json"))
    if not manifests or len(manifests) > MAX_ENTRIES:
        raise ValueError("Expected 1..16384 package manifests")
    groups = {}
    seen = set()
    for file in manifests:
        file = safe(root, file.relative_to(root).as_posix())
        if file.stat().st_size > MAX_ROOT:
            raise ValueError("Package manifest is too large")
        entry = json.loads(file.read_text(encoding="utf-8"))
        required = {"schema", "kind", "publisher", "metadata", "platforms", "requires", "path"}
        if not isinstance(entry, dict) or set(entry) - {"listed", "cases"} != required or entry["schema"] != 1 or not isinstance(entry.get("listed", True), bool):
            raise ValueError(f"Invalid schema/fields in {file}")
        kind = entry["kind"]
        if not token(kind):
            raise ValueError("Package kind must be a lowercase identifier")
        meta = entry["metadata"]
        metadata(meta)
        if entry["publisher"] != meta["publisher"]:
            raise ValueError("Manifest and metadata publishers disagree")
        key = (meta["publisher"], meta["id"])
        if key in seen and entry.get("listed", True):
            raise ValueError(f"Duplicate package identity: {key}")
        if entry.get("listed", True):
            seen.add(key)
        group = KINDS.get(kind, kind)
        prefix = f"packages/{group}/{meta['publisher']}/{meta['id']}/{meta['version']}/"
        if file.relative_to(root).as_posix() != prefix + "manifest.json" or not entry["path"].startswith(prefix):
            raise ValueError("Package directory does not match its kind, publisher, ID and version")
        platforms = entry["platforms"]
        requires = entry["requires"]
        if not isinstance(platforms, list) or len(platforms) > 3 or len(set(platforms)) != len(platforms) or any(p not in {"windows", "linux", "macos"} for p in platforms):
            raise ValueError("Invalid package platforms")
        if not isinstance(requires, list) or len(requires) > 32 or len(set(requires)) != len(requires) or any(not isinstance(r, str) or not re.fullmatch(r"[a-z0-9][a-z0-9.-]{0,79}", r) for r in requires):
            raise ValueError("Invalid package capabilities")
        artifact = safe(root, entry["path"])
        limit = MAX_ARTIFACT if kind == "recipe-pack" else 1024 * 1024 * 1024
        if not artifact.is_file() or artifact.stat().st_size > limit:
            raise ValueError("Package artifact is missing or exceeds its kind's size limit")
        size = artifact.stat().st_size
        with artifact.open('rb') as source:
            digest = hashlib.file_digest(source, 'sha256').hexdigest()
        if kind == "recipe-pack":
            data = artifact.read_bytes()
            document = json.loads(data)
            if document.get("schema") != 1 or document.get("kind") != kind or document.get("metadata") != meta or document.get("requires", []) != requires or not isinstance(document.get("recipes"), list):
                raise ValueError("Recipe artifact metadata/capabilities disagree with its manifest")
            if cli:
                subprocess.run([str(cli), "search", "--describe", "--recipes", str(artifact), "files"], check=True, capture_output=True)
        if "cases" in entry:
            cases_path = safe(root, entry["cases"])
            if not entry["cases"].startswith(prefix) or cases_path.stat().st_size > MAX_ROOT or kind != "recipe-pack":
                raise ValueError("Recipe cases must be a bounded JSONL file inside their package directory")
            cases = cases_path.read_text(encoding='utf-8').splitlines()
            if len(cases) > 1024:
                raise ValueError("Use at most 1024 recipe corpus examples per package")
            for number, line in enumerate(cases, 1):
                case = json.loads(line)
                if not isinstance(case, dict) or set(case) - {"input", "dsl", "error", "os"} or not isinstance(case.get("input"), str) or not case['input'] or len(case['input'].encode()) > 16384 or ("dsl" in case) == (case.get("error") is True):
                    raise ValueError(f"Invalid recipe corpus case {number}")
                if 'os' in case and case['os'] not in {'linux', 'windows', 'macos'}:
                    raise ValueError("Invalid recipe corpus OS")
                if 'dsl' in case and not isinstance(case['dsl'], str):
                    raise ValueError("Corpus DSL must be a string")
                host = 'windows' if sys.platform == 'win32' else 'macos' if sys.platform == 'darwin' else 'linux'
                if cli and case.get('os', host) == host:
                    check = subprocess.run([str(cli), 'search', '--describe', '--json', '--recipes', str(artifact), case['input']], capture_output=True, text=True, encoding='utf-8')
                    if (case.get('error') is True and check.returncode != 1) or ('dsl' in case and (check.returncode != 0 or json.loads(check.stdout)['dsl'] != case['dsl'])):
                        raise ValueError(f"Recipe corpus case {number} failed: {case['input']}")
        if not entry.get("listed", True):
            continue
        record = {key: value for key, value in entry.items() if key not in {"schema", "listed", "cases"}}
        record.update(bytes=size, sha256=digest)
        groups.setdefault(group, []).append(record)
    outputs = {}
    indexes = []
    total = 0
    for group, entries in sorted(groups.items()):
        entries.sort(key=lambda e: (e["publisher"], e["metadata"]["id"]))
        chunks = [[]]
        size = 0
        for entry in entries:
            line = (json.dumps(entry, ensure_ascii=False, separators=(",", ":")) + "\n").encode()
            if len(line) > min(MAX_ROOT, MAX_SHARD):
                raise ValueError("Index entry is too large")
            if size + len(line) > MAX_SHARD:
                chunks.append([])
                size = 0
            chunks[-1].append(line)
            size += len(line)
        for index, lines in enumerate(chunks):
            name = f"indexes/{group}" + (f"-{index + 1:03}" if len(chunks) > 1 else "") + ".jsonl"
            data = b"".join(lines)
            total += len(data)
            outputs[name] = data
            indexes.append({"kind": entries[0]["kind"], "path": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(), "entries": len(lines)})
    if len(indexes) > 64 or total > MAX_TOTAL:
        raise ValueError("Catalog indexes exceed total size/count bounds")
    outputs["catalog.json"] = encode({"schema": 1, "indexes": indexes})
    if len(outputs["catalog.json"]) > MAX_ROOT:
        raise ValueError("Root catalog is too large")
    if total + len(outputs["catalog.json"]) > MAX_TOTAL:
        raise ValueError("Root and indexes exceed total byte budget")
    return outputs


def compatibility(root, destination):
    """Keep the application's old Git example paths usable; not a remote layout."""
    packages = []
    copies = {}
    for platform in ("linux", "windows"):
        name = f"packages/recipes/coolnew/{platform}-essentials/1.0.0/pack.json"
        data = safe(root, name).read_bytes()
        meta = json.loads(data)["metadata"]
        target = f"recipes/{platform}.json"
        copies[safe(ROOT, target)] = data
        packages.append({"kind": "recipe-pack", "publisher": "coolnew", "metadata": meta,
                         "platforms": [platform], "requires": ["recipe.exact"], "path": target,
                         "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    copies[safe(ROOT, "recipes/catalog.json")] = encode({"schema": 1, "packages": packages})
    return copies


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT / "marketplace" if (ROOT / "marketplace").exists() else ROOT)
    parser.add_argument("--check", action="store_true", help="Refuse stale/missing generated indexes without writing")
    parser.add_argument("--cli", type=Path, help="Also validate recipe artifacts with this built kosha executable")
    parser.add_argument("--compat-recipes", type=Path, help="Refresh this application's generated legacy Git examples")
    args = parser.parse_args()
    try:
        outputs = generated(args.root, args.cli.resolve() if args.cli else None)
        current = {p.relative_to(args.root).as_posix() for p in (args.root / "indexes").glob("*.jsonl")}
        retired = current - outputs.keys()
        if retired:
            raise ValueError(f"Retired indexes need manual review/removal; nothing deleted: {sorted(retired)}")
        writes = {safe(args.root, name): data for name, data in outputs.items()}
        if args.compat_recipes:
            destination = args.compat_recipes.resolve()
            if destination != ROOT / "recipes":
                raise ValueError("Compatibility output must be this script checkout's recipes directory")
            writes.update(compatibility(args.root, destination))
        stale = [str(path) for path, data in writes.items() if not path.exists() or path.read_bytes() != data]
        if args.check and stale:
            raise ValueError(f"Stale generated marketplace files: {stale}")
        if not args.check:
            for path, data in writes.items():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
        print(f"Marketplace {'checked' if args.check else 'generated'}: {len(outputs) - 1} indexes; versions unchanged")
        return 0
    except (OSError, ValueError, TypeError, subprocess.CalledProcessError) as error:
        print(f"Marketplace generation refused: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
