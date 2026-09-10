from __future__ import annotations

import configparser
import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SUBMODULE_PATH = "construction/upstream/snapshots/schematica"
SUBMODULE_SECTION = f'submodule "{SUBMODULE_PATH}"'
UPSTREAM_URL = "https://github.com/tester2024/schematica.git"
PINNED_COMMIT = "0c88770005e7bbd7246997c81e810ba935c8e4cf"


def git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )


class ConstructionC1SchematicaPreservationTest(unittest.TestCase):
    def test_gitmodules_declares_exact_schematica_source(self) -> None:
        path = ROOT / ".gitmodules"
        self.assertTrue(path.is_file(), ".gitmodules is required for C1")
        parser = configparser.ConfigParser()
        parser.read(path, encoding="utf-8")
        self.assertIn(SUBMODULE_SECTION, parser)
        section = parser[SUBMODULE_SECTION]
        self.assertEqual(section.get("path"), SUBMODULE_PATH)
        self.assertEqual(section.get("url"), UPSTREAM_URL)

    def test_schematica_is_gitlink_pinned_to_audited_commit(self) -> None:
        result = git("ls-files", "--stage", "--", SUBMODULE_PATH)
        self.assertEqual(result.returncode, 0, result.stderr)
        rows = [line for line in result.stdout.splitlines() if line.strip()]
        self.assertEqual(len(rows), 1, f"expected exactly one gitlink row, got: {rows}")
        metadata, tracked_path = rows[0].split("\t", 1)
        mode, sha, stage = metadata.split()
        self.assertEqual(tracked_path, SUBMODULE_PATH)
        self.assertEqual(mode, "160000", "Schematica must be an immutable gitlink, not copied editable files")
        self.assertEqual(stage, "0")
        self.assertEqual(sha, PINNED_COMMIT)

    def test_registry_pin_matches_gitlink_contract(self) -> None:
        registry = json.loads((ROOT / "construction/upstream/registry.json").read_text(encoding="utf-8"))
        schematica = next(source for source in registry["sources"] if source["id"] == "schematica")
        self.assertEqual(schematica["repository"], "tester2024/schematica")
        self.assertEqual(schematica["pinned_commit"], PINNED_COMMIT)
        self.assertEqual(schematica["integration_policy"], "IMMUTABLE_SNAPSHOT")

    def test_superproject_tracks_no_editable_schematica_payload(self) -> None:
        result = git("ls-files", "--stage", "--", f"{SUBMODULE_PATH}/")
        self.assertEqual(result.returncode, 0, result.stderr)
        ordinary = []
        for row in result.stdout.splitlines():
            if not row.strip():
                continue
            metadata, tracked_path = row.split("\t", 1)
            mode = metadata.split()[0]
            if tracked_path != SUBMODULE_PATH or mode != "160000":
                ordinary.append(row)
        self.assertEqual(ordinary, [], "Schematica payload must remain owned by the pinned upstream repository")


if __name__ == "__main__":
    unittest.main()
