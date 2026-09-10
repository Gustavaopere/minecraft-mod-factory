from __future__ import annotations

import configparser
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SUBMODULE_PATH = "construction/upstream/snapshots/schematica"
SUBMODULE_SECTION = f'submodule "{SUBMODULE_PATH}"'
UPSTREAM_URL = "https://github.com/tester2024/schematica.git"
PINNED_COMMIT = "0c88770005e7bbd7246997c81e810ba935c8e4cf"
WORKFLOW = ROOT / ".github/workflows/factory-construction-c1-schematica-upstream.yml"


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

    def test_registry_pin_matches_gitlink_contract(self) -> None:
        registry = json.loads((ROOT / "construction/upstream/registry.json").read_text(encoding="utf-8"))
        schematica = next(source for source in registry["sources"] if source["id"] == "schematica")
        self.assertEqual(schematica["repository"], "tester2024/schematica")
        self.assertEqual(schematica["pinned_commit"], PINNED_COMMIT)
        self.assertEqual(schematica["integration_policy"], "IMMUTABLE_SNAPSHOT")

    def test_workflow_has_fixed_gitlink_integrity_gate(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("Verify Schematica gitlink mode and pin", workflow)
        self.assertIn(
            "git ls-files --stage -- construction/upstream/snapshots/schematica",
            workflow,
        )
        self.assertIn(f"160000 {PINNED_COMMIT} 0", workflow)


if __name__ == "__main__":
    unittest.main()
