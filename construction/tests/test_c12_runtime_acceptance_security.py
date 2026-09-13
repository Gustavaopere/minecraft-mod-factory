from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from construction.runtime.c12_evidence import C12EvidenceError, package_evidence


class C12RuntimeAcceptanceSecurityTest(unittest.TestCase):
    def test_parent_escape_is_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            workspace = root / "workspace"
            workspace.mkdir()
            outside = root / "outside.log"
            outside.write_text("outside", encoding="utf-8")
            with self.assertRaises(C12EvidenceError):
                package_evidence(workspace, [outside])

    def test_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            workspace = Path(raw)
            real = workspace / "real.log"
            real.write_text("payload", encoding="utf-8")
            link = workspace / "link.log"
            link.symlink_to(real)
            with self.assertRaises(C12EvidenceError):
                package_evidence(workspace, [link])

    def test_missing_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            workspace = Path(raw)
            with self.assertRaises(C12EvidenceError):
                package_evidence(workspace, [workspace / "missing.log"])

    def test_directory_is_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            workspace = Path(raw)
            directory = workspace / "evidence-dir"
            directory.mkdir()
            with self.assertRaises(C12EvidenceError):
                package_evidence(workspace, [directory])

    def test_duplicate_paths_are_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            workspace = Path(raw)
            evidence = workspace / "evidence.log"
            evidence.write_text("payload", encoding="utf-8")
            with self.assertRaises(C12EvidenceError):
                package_evidence(workspace, [evidence, evidence])

    def test_output_is_sorted_and_hashed(self):
        with tempfile.TemporaryDirectory() as raw:
            workspace = Path(raw)
            a = workspace / "a.log"
            b = workspace / "b.log"
            a.write_text("a", encoding="utf-8")
            b.write_text("b", encoding="utf-8")
            packaged = package_evidence(workspace, [b, a])
            self.assertEqual([item["path"] for item in packaged], ["a.log", "b.log"])
            self.assertTrue(all(len(item["sha256"]) == 64 for item in packaged))


if __name__ == "__main__":
    unittest.main()
