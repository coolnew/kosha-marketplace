# SPDX-License-Identifier: MIT OR Apache-2.0
# SPDX-FileCopyrightText: 2026 Neeraj Sharma <neerajsharma.9@outlook.com> and The kosha contributors
"""Exercise integrity failures that would break commit-pinned installation."""

import hashlib
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
        self.root = Path(self.temp.name)
        shutil.copytree(ROOT / "recipes", self.root / "recipes")
        shutil.copyfile(ROOT / "catalog.json", self.root / "catalog.json")
        self.catalog = json.loads((self.root / "catalog.json").read_text())

    def save_catalog(self):
        (self.root / "catalog.json").write_bytes((json.dumps(self.catalog) + "\n").encode())

    def change_pack(self, change):
        entry = self.catalog["packages"][0]
        path = self.root / entry["path"]
        pack = json.loads(path.read_text())
        change(pack)
        path.write_bytes((json.dumps(pack) + "\n").encode())
        entry["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        self.save_catalog()

    def test_seed_is_valid(self):
        validate(self.root)

    def test_modified_bytes_fail_hash(self):
        path = self.root / self.catalog["packages"][0]["path"]
        path.write_bytes(path.read_bytes() + b"\n")
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            validate(self.root)

    def test_metadata_tag_order_matters(self):
        self.change_pack(lambda p: p["metadata"]["tags"].reverse())
        with self.assertRaisesRegex(ValueError, "metadata mismatch"):
            validate(self.root)

    def test_path_traversal_is_rejected(self):
        self.catalog["packages"][0]["path"] = "recipes/../linux.json"
        self.save_catalog()
        with self.assertRaisesRegex(ValueError, "unsafe pack path"):
            validate(self.root)

    def test_duplicate_id_is_rejected(self):
        self.catalog["packages"].append(self.catalog["packages"][0])
        self.save_catalog()
        with self.assertRaisesRegex(ValueError, "duplicate pack ID"):
            validate(self.root)

    def test_wrong_platform_is_rejected(self):
        self.catalog["packages"][0]["platforms"] = ["macos"]
        self.save_catalog()
        with self.assertRaisesRegex(ValueError, "platforms differ"):
            validate(self.root)

    def test_overlapping_phrase_is_rejected(self):
        def duplicate(pack):
            pack["recipes"].append(dict(pack["recipes"][0], os=None))
        self.change_pack(duplicate)
        with self.assertRaisesRegex(ValueError, "duplicate recipe phrase"):
            validate(self.root)

    def test_unknown_field_is_rejected(self):
        self.change_pack(lambda p: p.update(executable="no"))
        with self.assertRaisesRegex(ValueError, "unexpected or missing fields"):
            validate(self.root)

    def test_crlf_is_rejected(self):
        path = self.root / "catalog.json"
        path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
        with self.assertRaisesRegex(ValueError, "expected LF"):
            validate(self.root)


if __name__ == "__main__":
    unittest.main()
