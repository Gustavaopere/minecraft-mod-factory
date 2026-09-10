import contextlib
import importlib.util
import json
import re
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCAFFOLDER = ROOT / "engineering" / "tooling" / "scaffolder" / "scaffold_mod.py"
MOD_SPEC = ROOT / "engineering" / "tests" / "fixtures" / "i3-golden-mod-spec.json"
SCAFFOLD_CONFIG = ROOT / "engineering" / "tests" / "fixtures" / "i3-golden-scaffold-config.json"
BUILD_TEMPLATE = ROOT / "engineering" / "templates" / "neoforge-mod" / "build.gradle.tmpl"
CI_TEMPLATE = ROOT / "engineering" / "templates" / "neoforge-mod" / "ci.yml.tmpl"
GOLDEN = ROOT / "engineering" / "tests" / "golden" / "i3-golden-mod"


def load_scaffolder():
    spec = importlib.util.spec_from_file_location("i3_security_review", SCAFFOLDER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class I3SecurityAndReviewContractTest(unittest.TestCase):
    def setUp(self):
        self.module = load_scaffolder()
        self.mod_spec = json.loads(MOD_SPEC.read_text(encoding="utf-8"))

    def test_output_outside_working_directory_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workspace = root / "workspace"
            workspace.mkdir()
            outside = root / "outside-project"
            with contextlib.chdir(workspace):
                with self.assertRaises(ValueError):
                    self.module.generate_project(MOD_SPEC, SCAFFOLD_CONFIG, outside)
            self.assertFalse(outside.exists())

    def test_user_supplied_mod_spec_outside_working_directory_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workspace = root / "workspace"
            workspace.mkdir()
            outside_spec = root / "outside-spec.json"
            outside_spec.write_text(MOD_SPEC.read_text(encoding="utf-8"), encoding="utf-8")
            with contextlib.chdir(workspace):
                with self.assertRaises(ValueError):
                    self.module.generate_project(outside_spec, SCAFFOLD_CONFIG, Path("generated"))

    def test_scaffolder_validates_complete_mod_spec_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            incomplete = {
                "schema_version": self.mod_spec["schema_version"],
                "identity": self.mod_spec["identity"],
                "release": self.mod_spec["release"],
            }
            with contextlib.chdir(workspace):
                bad_spec = Path("incomplete.json")
                bad_spec.write_text(json.dumps(incomplete), encoding="utf-8")
                with self.assertRaises(ValueError):
                    self.module.generate_project(bad_spec, SCAFFOLD_CONFIG, Path("generated"))

    def test_main_resources_include_official_datagen_output(self):
        template = BUILD_TEMPLATE.read_text(encoding="utf-8")
        self.assertIn(
            "srcDir 'src/generated/resources'",
            template,
            "I3 RED: generated datagen resources must be packaged in sourceSets.main.resources",
        )

    def test_generated_ci_pins_every_remote_action_to_full_commit_sha(self):
        template = CI_TEMPLATE.read_text(encoding="utf-8")
        uses = [line.strip().split("uses:", 1)[1].strip() for line in template.splitlines() if "uses:" in line]
        self.assertGreater(len(uses), 0)
        for action in uses:
            self.assertRegex(
                action,
                r"^[^@\s]+@[0-9a-f]{40}(?:\s+#.*)?$",
                f"I3 RED: remote action must use immutable 40-hex SHA: {action}",
            )

    def test_generated_project_enables_dependency_locking_and_carries_lock_state(self):
        template = BUILD_TEMPLATE.read_text(encoding="utf-8")
        self.assertIn(
            "dependencyLocking",
            template,
            "I3 RED: canonical build must enable Gradle dependency locking",
        )
        self.assertIn(
            "lockAllConfigurations()",
            template,
            "I3 RED: canonical build must lock every resolvable project configuration",
        )
        golden_lock = GOLDEN / "gradle.lockfile"
        self.assertTrue(golden_lock.is_file(), "I3 RED: checked-in Golden gradle.lockfile is missing")
        self.assertGreater(golden_lock.stat().st_size, 0, "I3 RED: Golden gradle.lockfile must not be empty")
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            with contextlib.chdir(workspace):
                generated = self.module.generate_project(MOD_SPEC, SCAFFOLD_CONFIG, Path("generated"))
            generated_lock = generated / "gradle.lockfile"
            self.assertTrue(generated_lock.is_file(), "I3 RED: generated project must carry canonical gradle.lockfile")
            self.assertEqual(golden_lock.read_bytes(), generated_lock.read_bytes())


if __name__ == "__main__":
    unittest.main()
