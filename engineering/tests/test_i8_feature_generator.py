import copy
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


class I8FeatureGeneratorCoreContractTest(unittest.TestCase):
    def require_generator(self):
        if not GENERATOR.is_file():
            self.skipTest("production I8 feature generator is intentionally absent during RED")
        return load_generator()

    def test_feature_generator_production_entrypoint_exists(self):
        self.assertTrue(GENERATOR.is_file())

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
        paths = [operation["path"] for operation in first["operations"]]
        self.assertTrue(paths)
        self.assertEqual(len(paths), len(set(paths)))

    def test_planning_rejects_unsupported_target_and_invalid_identifiers(self):
        module = self.require_generator()
        request = load_request()
        with tempfile.TemporaryDirectory() as tmp:
            project = copy_golden(Path(tmp) / "project")

            wrong_target = copy.deepcopy(request)
            wrong_target["target"]["neoforge"] = "21.1.999"
            with self.assertRaises(ValueError):
                module.plan_feature_set(project, wrong_target)

            invalid_id = copy.deepcopy(request)
            invalid_id["features"][0]["id"] = "Invalid-ID"
            with self.assertRaises(ValueError):
                module.plan_feature_set(project, invalid_id)

    def test_block_entity_reference_must_target_requested_block(self):
        module = self.require_generator()
        request = load_request()
        request["features"][2]["block_id"] = "missing_block"
        with tempfile.TemporaryDirectory() as tmp:
            project = copy_golden(Path(tmp) / "project")
            with self.assertRaises(ValueError):
                module.plan_feature_set(project, request)

    def test_plan_contains_generated_tests_registry_datagen_and_bootstrap(self):
        module = self.require_generator()
        with tempfile.TemporaryDirectory() as tmp:
            project = copy_golden(Path(tmp) / "project")
            plan = module.plan_feature_set(project, load_request())

        roles = {operation["role"] for operation in plan["operations"]}
        self.assertIn("feature_source", roles)
        self.assertIn("generated_test", roles)
        self.assertIn("registry", roles)
        self.assertIn("datagen", roles)
        self.assertIn("bootstrap", roles)

    def test_request_authoritative_apply_requires_confirmation_then_is_idempotent(self):
        module = self.require_generator()
        request = load_request()
        with tempfile.TemporaryDirectory() as tmp:
            project = copy_golden(Path(tmp) / "project")
            before = tree_snapshot(project)

            with self.assertRaises(module.ConfirmationRequiredError):
                module.apply_feature_set(project, request, confirm_modified=False)
            self.assertEqual(before, tree_snapshot(project))

            written = module.apply_feature_set(project, request, confirm_modified=True)
            self.assertTrue(written)
            main = project / MAIN_RELATIVE
            source = main.read_text(encoding="utf-8")
            self.assertIn("FactoryGeneratedRegistries.register(modBus);", source)
            self.assertIn("modBus.addListener(FactoryGeneratedData::gatherData);", source)

            self.assertEqual([], module.apply_feature_set(project, request, confirm_modified=True))

    def test_partial_bootstrap_wiring_is_rejected(self):
        module = self.require_generator()
        with tempfile.TemporaryDirectory() as tmp:
            project = copy_golden(Path(tmp) / "project")
            main = project / MAIN_RELATIVE
            original = main.read_text(encoding="utf-8")
            partial = original.replace(
                "package dev.example.i3golden;\n\n",
                "package dev.example.i3golden;\n\nimport dev.example.i3golden.registry.FactoryGeneratedRegistries;\n",
                1,
            )
            main.write_text(partial, encoding="utf-8", newline="\n")
            with self.assertRaises(ValueError):
                module.plan_feature_set(project, load_request())

    def test_workspace_loader_and_safe_relative_path_accept_canonical_inputs(self):
        module = self.require_generator()
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp).resolve()
            request_path = workspace / "request.json"
            shutil.copyfile(REQUEST_FIXTURE, request_path)
            project = copy_golden(workspace / "project")

            loaded = module.load_request(workspace, "request.json")
            self.assertEqual(load_request(), loaded)
            self.assertEqual(project.resolve(), module._workspace_input(workspace, "project", directory=True))
            self.assertEqual(
                Path("src/main/java/dev/example/Test.java"),
                module._safe_relative_path("src/main/java/dev/example/Test.java"),
            )

    def test_fully_wired_bootstrap_is_a_noop(self):
        module = self.require_generator()
        request = load_request()
        with tempfile.TemporaryDirectory() as tmp:
            project = copy_golden(Path(tmp) / "project")
            module.apply_feature_set(project, request, confirm_modified=True)
            plan = module.plan_feature_set(project, request)
            bootstrap = next(operation for operation in plan["operations"] if operation["role"] == "bootstrap")
            self.assertEqual("noop", bootstrap["action"])
            self.assertFalse(bootstrap["requires_confirmation"])


if __name__ == "__main__":
    unittest.main()
