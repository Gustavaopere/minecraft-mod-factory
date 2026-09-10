from __future__ import annotations

import configparser
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SUBMODULE_PATH = "construction/upstream/snapshots/schematica"
SUBMODULE_SECTION = f'submodule "{SUBMODULE_PATH}"'
UPSTREAM_URL = "https://github.com/tester2024/schematica.git"
PINNED_COMMIT = "0c88770005e7bbd7246997c81e810ba935c8e4cf"
WORKFLOW = ROOT / ".github/workflows/factory-construction-c1-schematica-upstream.yml"
LOCK = ROOT / "construction/upstream/harness/schematica-test-lock.txt"
SONAR_PROPERTIES = ROOT / ".sonarcloud.properties"
LOCK_LINE_RE = re.compile(
    r"^(?P<name>[A-Za-z0-9_.-]+)==[^\s]+ --hash=sha256:[0-9a-f]{64}$"
)
REQUIRED_UPSTREAM_TEST_PACKAGES = {
    "numpy",
    "nbtlib",
    "shapely",
    "trimesh",
    "matplotlib",
    "prompt-toolkit",
    "noise",
    "pillow",
    "pytest",
    "pytest-cov",
    "hypothesis",
    "ruff",
    "mypy",
    "scipy",
}


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

    def test_sonar_excludes_immutable_schematica_snapshot(self) -> None:
        self.assertTrue(SONAR_PROPERTIES.is_file(), ".sonarcloud.properties must define Factory analysis scope")
        exclusions: set[str] = set()
        for raw in SONAR_PROPERTIES.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line.startswith("sonar.exclusions="):
                continue
            exclusions.update(item.strip() for item in line.split("=", 1)[1].split(",") if item.strip())

        self.assertIn(
            SUBMODULE_PATH,
            exclusions,
            "the immutable third-party Schematica gitlink must not be analyzed as Factory-authored source",
        )
        self.assertTrue(all("*" not in item for item in exclusions), "automatic-analysis exclusions must remain exact paths")

    def test_workflow_has_fixed_gitlink_integrity_gate(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("Verify Schematica gitlink mode and pin", workflow)
        self.assertIn(
            "git ls-files --stage -- construction/upstream/snapshots/schematica",
            workflow,
        )
        self.assertIn(f"160000 {PINNED_COMMIT} 0", workflow)

    def test_test_environment_is_fully_pinned_and_hashed(self) -> None:
        self.assertTrue(LOCK.is_file(), "C1 requires a Factory-owned hashed dependency lock")
        package_names: set[str] = set()
        for line_number, raw_line in enumerate(LOCK.read_text(encoding="utf-8").splitlines(), start=1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            match = LOCK_LINE_RE.fullmatch(line)
            self.assertIsNotNone(match, f"unlocked or unhashed requirement at line {line_number}: {line}")
            assert match is not None
            normalized_name = match.group("name").lower().replace("_", "-")
            self.assertNotIn(normalized_name, package_names, f"duplicate locked package: {normalized_name}")
            package_names.add(normalized_name)

        self.assertTrue(
            REQUIRED_UPSTREAM_TEST_PACKAGES.issubset(package_names),
            f"lock missing required upstream/test packages: {sorted(REQUIRED_UPSTREAM_TEST_PACKAGES - package_names)}",
        )

    def test_workflow_uses_lock_without_editable_dependency_resolution(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn(
            "python3 -m pip install --require-hashes --no-deps -r construction/upstream/harness/schematica-test-lock.txt",
            workflow,
        )
        self.assertIn("PYTHONPATH: construction/upstream/snapshots/schematica/scripts", workflow)
        self.assertNotIn("pip install -e", workflow)
        self.assertNotIn("schematica-test-requirements.txt", workflow)


if __name__ == "__main__":
    unittest.main()
