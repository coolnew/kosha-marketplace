# SPDX-License-Identifier: MIT OR Apache-2.0
# SPDX-FileCopyrightText: 2026 Neeraj Sharma <neerajsharma.9@outlook.com> and The kosha contributors
"""Check the complete replacement seed and its generated integrity chain."""

import json
from pathlib import Path
import shutil
import tempfile
import unittest

from scripts.validate import ROOT, validate


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        for name in ("packages", "indexes"):
            shutil.copytree(ROOT / name, self.root / name)
        shutil.copyfile(ROOT / "catalog.json", self.root / "catalog.json")
        self.folder = self.root / "packages/recipes/coolnew/search-power-tools/1.0.0"

    def test_seed_is_valid(self):
        validate(self.root)

    def test_changed_artifact_invalidates_generated_index(self):
        path = self.folder / "pack.json"
        path.write_bytes(path.read_bytes() + b"\n")
        with self.assertRaisesRegex(ValueError, "stale generated file"):
            validate(self.root)

    def test_modified_index_is_rejected(self):
        (self.root / "indexes/recipes.jsonl").write_bytes(b"{}\n")
        with self.assertRaisesRegex(ValueError, "stale generated file"):
            validate(self.root)

    def test_modified_root_is_rejected(self):
        (self.root / "catalog.json").write_bytes(b"{}\n")
        with self.assertRaisesRegex(ValueError, "stale generated file"):
            validate(self.root)

    def test_retired_index_requires_explicit_removal(self):
        (self.root / "indexes/retired.jsonl").write_bytes(b"{}\n")
        with self.assertRaisesRegex(ValueError, "retired indexes"):
            validate(self.root)

    def test_publisher_and_version_remain_unchanged(self):
        entries = [json.loads(line) for line in (self.root / "indexes/recipes.jsonl").read_bytes().splitlines()]
        self.assertEqual({e["metadata"]["id"] for e in entries},
                         {"linux-essentials", "windows-essentials", "search-power-tools", "developer-tools", "content-creator-tools"})
        for entry in entries:
            self.assertEqual(entry["publisher"], "coolnew")
            self.assertEqual(entry["metadata"]["publisher"], "coolnew")
            self.assertEqual(entry["metadata"]["version"], "1.0.0")

    def test_all_seed_artifacts_are_listed(self):
        catalog = json.loads((self.root / "catalog.json").read_bytes())
        entries = [json.loads(line) for index in catalog["indexes"]
                   for line in (self.root / index["path"]).read_bytes().splitlines()]
        actual = {p.relative_to(self.root).as_posix() for p in (self.root / "packages").rglob("pack.json")}
        self.assertEqual({entry["path"] for entry in entries}, actual)


if __name__ == "__main__":
    unittest.main()
