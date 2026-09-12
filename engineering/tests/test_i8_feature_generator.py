import copy
import hashlib
import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GENERATOR = ROOT / "engineering/tooling/feature-generator/generate_feature.py"
GOLDEN = ROOT / "engineering/tests/golden/i3-golden-mod"
REQUEST_FIXTURE = ROOT / "engineering/tests/fixtures/i8-feature-set.json"
CORE_FEATURE_KINDS = (
    "block",
    "item",
    "block_entity",
    "menu",
    "network_payload",
    "recipe",
)
MAIN_RELATIVE = Path("src/main/java/dev/example/i3golden/I3GoldenMod.java")


def load_generator():
    spec = importlib.util.spec_from_file_location("i8_generate_feature", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_request():
    return json.loads(REQUEST_FIXTURE.read_text(encoding="utf-8"))


def copy_golden(target: Path) -> Path:
    shutil.copytree(GOLDEN, target)
    return target


def tree_snapshot(root: Path) -> dict[str, bytes]:
    return {
        str(path.relative_to(root)).replace("\\", "/"): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class I8FeatureGeneratorCoreContractTest(unittest.TestCase):
    def require_generator(self):
        if not GENERATOR.is_file():
            self.skipTest("production I8 feature generator is intentionally absent during RED")
        return load_generator()

    def test_feature_generator_production_entrypoint_exists(self):
        self.assertTrue(
            GENERATOR.is_file(),
            "I8 RED: production generator engineering/tooling/feature-generator/generate_feature.py is missing",
        )

    def test_core_feature_kinds_cover_canonical_i8_scope(self):
        module = self.require_generator()
        self.assertEqual(CORE_FEATURE_KINDS, tuple(module.CORE_FEATURE_KINDS))

    def test_planning_is_deterministic_and_has_no_filesystem_side_effects(self):
        module = self.require_generator()
        request = load_request()
        with tempfile.TemporaryDirectory() as tmp:
            project = copy_golden(Path(tmp) / "project")
            before = tree_snapshot(project)
            first = module.plan_feature_set(project, copy.deepcopy(request))
            second = module.plan_feature_set(project, copy.deepcopy(request))
            after = tree_snapshot(project)

        self.assertEqual(first, second)
        self.assertEqual(before, after)
        self.assertEqual(1, first["schema_version"])
        self.assertEqual(list(CORE_FEATURE_KINDS), first["feature_kinds"])
        self.assertEqual([], first["conflicts"])
        self.assertTrue(first["operations"])
        paths = [operation["path"] for operation in first["operations"]]
        self.assertEqual(len(paths), len(set(paths)), "each planned path must be unique")

    def test_planning_rejects_unsupported_target_and_unsafe_identifiers(self):
        module = self.require_generator()
        request = load_request()
        with tempfile.TemporaryDirectory() as tmp:
            project = copy_golden(Path(tmp) / "project")

            wrong_target = copy.deepcopy(request)
            wrong_target["target"]["neoforge"] = "21.1.999"
            with self.assertRaises(ValueError):
                module.plan_feature_set(project, wrong_target)

            unsafe_id = copy.deepcopy(request)
            unsafe_id["features"][0]["id"] = "../escape"
            with self.assertRaises(ValueError):
                module.plan_feature_set(project, unsafe_id)

    def test_plan_contains_generated_tests_registry_and_datagen_operations(self):
        module = self.require_generator()
        with tempfile.TemporaryDirectory() as tmp:
            project = copy_golden(Path(tmp) / "project")
            plan = module.plan_feature_set(project, load_request())

        roles = {operation["role"] for operation in plan["operations"]}
        self.assertIn("feature_source", roles)
        self.assertIn("generated_test", roles)
        self.assertIn("registry", roles)
        self.assertIn("datagen", roles)

    def test_modified_existing_file_requires_explicit_confirmation_and_diff(self):
        module = self.require_generator()
        with tempfile.TemporaryDirectory() as tmp:
            project = copy_golden(Path(tmp) / "project")
            target = project / MAIN_RELATIVE
            original = target.read_text(encoding="utf-8")
            planned = original.replace("    }\n}", "        // I8 planned edit\n    }\n}")
            plan = {
                "schema_version": 1,
                "feature_kinds": [],
                "conflicts": [],
                "operations": [
                    {
                        "action": "modify",
                        "role": "registry",
                        "path": MAIN_RELATIVE.as_posix(),
                        "before_sha256": sha256_text(original),
                        "content": planned,
                        "diff": "--- before\n+++ after\n+// I8 planned edit\n",
                        "requires_confirmation": True,
                    }
                ],
            }

            with self.assertRaises(module.ConfirmationRequiredError) as ctx:
                module.apply_plan(project, plan, confirm_modified=False)
            self.assertIn("diff", str(ctx.exception).lower())
            self.assertEqual(original, target.read_text(encoding="utf-8"))

            module.apply_plan(project, plan, confirm_modified=True)
            self.assertEqual(planned, target.read_text(encoding="utf-8"))

    def test_apply_rejects_stale_plan_even_when_confirmation_is_requested(self):
        module = self.require_generator()
        with tempfile.TemporaryDirectory() as tmp:
            project = copy_golden(Path(tmp) / "project")
            target = project / MAIN_RELATIVE
            original = target.read_text(encoding="utf-8")
            planned = original + "\n// planned\n"
            plan = {
                "schema_version": 1,
                "feature_kinds": [],
                "conflicts": [],
                "operations": [
                    {
                        "action": "modify",
                        "role": "registry",
                        "path": MAIN_RELATIVE.as_posix(),
                        "before_sha256": sha256_text(original),
                        "content": planned,
                        "diff": "--- before\n+++ after\n+// planned\n",
                        "requires_confirmation": True,
                    }
                ],
            }
            concurrent = original + "\n// user edit after planning\n"
            target.write_text(concurrent, encoding="utf-8", newline="\n")

            with self.assertRaises(module.StalePlanError):
                module.apply_plan(project, plan, confirm_modified=True)
            self.assertEqual(concurrent, target.read_text(encoding="utf-8"))

    def test_apply_rejects_paths_outside_project_root(self):
        module = self.require_generator()
        with tempfile.TemporaryDirectory() as tmp:
            project = copy_golden(Path(tmp) / "project")
            plan = {
                "schema_version": 1,
                "feature_kinds": [],
                "conflicts": [],
                "operations": [
                    {
                        "action": "create",
                        "role": "feature_source",
                        "path": "../escape.txt",
                        "content": "escape\n",
                        "requires_confirmation": False,
                    }
                ],
            }
            with self.assertRaises(ValueError):
                module.apply_plan(project, plan, confirm_modified=False)
            self.assertFalse((Path(tmp) / "escape.txt").exists())


if __name__ == "__main__":
    unittest.main()
