# SPDX-License-Identifier: MIT OR Apache-2.0
# SPDX-FileCopyrightText: 2026 Neeraj Sharma <neerajsharma.9@outlook.com> and The kosha contributors
"""Keep sign-off enforcement consistent for ordinary and merge commits."""

from contextlib import redirect_stdout
import importlib.util
import io
from pathlib import Path
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location("dco", Path(__file__).resolve().parents[1] / "xtask-dco.py")
dco = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dco)


class DcoTests(unittest.TestCase):
    def check_commit(self, body, parents=1):
        record = ("a" * 40, "Example change", parents, body)
        with patch.object(dco, "commits", return_value=[record]), patch("sys.argv", ["xtask-dco.py"]):
            with redirect_stdout(io.StringIO()):
                return dco.main()

    def test_signed_commit_passes(self):
        self.assertEqual(self.check_commit("Example\n\nSigned-off-by: Contributor <dev@example.com>\n"), 0)

    def test_unsigned_commit_fails(self):
        self.assertEqual(self.check_commit("Example\n"), 1)

    def test_unsigned_merge_fails(self):
        self.assertEqual(self.check_commit("Merge branch\n", parents=2), 1)

    def test_coauthor_trailer_fails_even_with_signoff(self):
        body = "Example\n\nSigned-off-by: Contributor <dev@example.com>\nCo-authored-by: Another <a@example.com>\n"
        self.assertEqual(self.check_commit(body), 1)


if __name__ == "__main__":
    unittest.main()
