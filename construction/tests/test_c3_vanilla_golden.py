from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONSTRUCTION = ROOT / "construction"
FIXTURE = CONSTRUCTION / "fixtures" / "vanilla-golden"
BUILD_SPEC = FIXTURE / "build-spec.json"
GENERATOR = FIXTURE / "generate.py"
EXPECTED_IR = FIXTURE / "expected-build-ir.json"
BUILD_IR_MODULE = CONSTRUCTION / "core" / "build_ir.py"
WORKFLOW = ROOT / ".github" / "workflows" / "factory-construction-c3-vanilla-golden.yml"
SCHEMATICA_PIN = "0c88770005e7bbd7246997c81e810ba935c8e4cf"
IMPLEMENTED = BUILD_SPEC.is_file() and GENERATOR.is_file() and EXPECTED_IR.is_file()


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"unable to load {path.relative_to(ROOT)}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ConstructionC3VanillaGoldenTest(unittest.TestCase):
    def test_required_c3_files_exist(self) -> None:
        required = [BUILD_SPEC, GENERATOR, EXPECTED_IR, WORKFLOW]
        missing = [path.relative_to(ROOT).as_posix() for path in required if not path.is_file()]
        self.assertEqual(missing, [])

    def test_workflow_is_read_only_pinned_and_revalidates_on_main(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("- main", workflow)
        self.assertIn("feat/construction-c3-vanilla-golden", workflow)
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertIn("actions/checkout@11d5960a326750d5838078e36cf38b85af677262", workflow)
        self.assertIn("actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065", workflow)
        self.assertIn("pip install --require-hashes --no-deps", workflow)
        self.assertIn("python3 -m unittest construction/tests/test_c3_vanilla_golden.py -v", workflow)
        self.assertIn("python3 -m unittest construction/tests/test_c2_build_ir.py -v", workflow)
        self.assertIn("python3 -m unittest construction/tests/test_c0_foundation.py -v", workflow)
        self.assertIn("python3 construction/scripts/validate_c0.py", workflow)

    @unittest.skipUnless(IMPLEMENTED, "C3 vanilla golden fixture not present yet")
    def test_build_spec_is_vanilla_only_and_deterministic(self) -> None:
        spec = json.loads(BUILD_SPEC.read_text(encoding="utf-8"))
        self.assertEqual(spec["schema_version"], 1)
        self.assertEqual(spec["target"], {"minecraft_version": "1.21.1", "loader": "none"})
        self.assertEqual(spec["geometry"]["max_size"], {"x": 7, "y": 5, "z": 7})
        self.assertEqual(spec["palette"]["allow_modded"], False)
        self.assertEqual(spec["palette"]["allowed_namespaces"], ["minecraft"])
        self.assertTrue(spec["qa"]["require_determinism"])
        self.assertEqual(spec["outputs"]["formats"], ["sponge_v3"])

    @unittest.skipUnless(IMPLEMENTED, "C3 vanilla golden fixture not present yet")
    def test_generator_is_pinned_to_preserved_schematica(self) -> None:
        generator = load_module(GENERATOR, "construction_c3_vanilla_golden")
        self.assertEqual(generator.SCHEMATICA_PIN, SCHEMATICA_PIN)
        self.assertEqual(generator.PRODUCER, "schematica")
        self.assertEqual(generator.PRODUCER_VERSION, SCHEMATICA_PIN)

    @unittest.skipUnless(IMPLEMENTED, "C3 vanilla golden fixture not present yet")
    def test_generated_ir_matches_checked_in_golden_exactly(self) -> None:
        generator = load_module(GENERATOR, "construction_c3_vanilla_golden_generate")
        expected = json.loads(EXPECTED_IR.read_text(encoding="utf-8"))
        generated_a = generator.generate_golden()
        generated_b = generator.generate_golden()
        self.assertEqual(generated_a, generated_b)
        self.assertEqual(generated_a, expected)

    @unittest.skipUnless(IMPLEMENTED, "C3 vanilla golden fixture not present yet")
    def test_golden_ir_is_valid_vanilla_only_and_has_known_cardinality(self) -> None:
        build_ir = load_module(BUILD_IR_MODULE, "construction_c2_build_ir_for_c3")
        expected = json.loads(EXPECTED_IR.read_text(encoding="utf-8"))
        self.assertEqual(build_ir.validate_build_ir(expected), [])
        self.assertEqual(expected["bounds"]["size"], {"x": 7, "y": 5, "z": 7})
        self.assertEqual(len(expected["blocks"]), 110)
        self.assertEqual(
            [build_ir.canonical_block_state_string(state) for state in expected["palette"]],
            [
                "minecraft:oak_log[axis=y]",
                "minecraft:oak_planks",
                "minecraft:stone_bricks",
            ],
        )
        self.assertTrue(all(state["name"].startswith("minecraft:") for state in expected["palette"]))
        self.assertEqual(expected["metadata"]["producer"], "schematica")
        self.assertEqual(expected["metadata"]["producer_version"], SCHEMATICA_PIN)

    @unittest.skipUnless(IMPLEMENTED, "C3 vanilla golden fixture not present yet")
    def test_c3_does_not_smuggle_later_phase_artifacts(self) -> None:
        forbidden_suffixes = {".schem", ".litematic", ".nbt"}
        leaked = [path.relative_to(ROOT).as_posix() for path in FIXTURE.rglob("*") if path.suffix in forbidden_suffixes]
        self.assertEqual(leaked, [])
        generator_text = GENERATOR.read_text(encoding="utf-8").lower()
        for forbidden in ("blockentity", "block_entity", "runtime registry", "modded palette"):
            self.assertNotIn(forbidden, generator_text)


if __name__ == "__main__":
    unittest.main()
