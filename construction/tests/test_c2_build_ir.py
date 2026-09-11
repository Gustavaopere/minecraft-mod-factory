from __future__ import annotations

import importlib.util
import json
import unittest
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONSTRUCTION = ROOT / "construction"
SCHEMA = CONSTRUCTION / "schemas" / "build-ir.schema.json"
MODULE = CONSTRUCTION / "core" / "build_ir.py"
WORKFLOW = ROOT / ".github" / "workflows" / "factory-construction-c2-build-ir.yml"
IMPLEMENTED = SCHEMA.is_file() and MODULE.is_file()


def load_build_ir_module():
    if not MODULE.is_file():
        raise AssertionError(f"C2 module is required at {MODULE.relative_to(ROOT)}")
    spec = importlib.util.spec_from_file_location("construction_c2_build_ir", MODULE)
    if spec is None or spec.loader is None:
        raise AssertionError("unable to load C2 build IR module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_spec() -> dict[str, object]:
    return {
        "schema_version": 1,
        "identity": {
            "name": "c2-contract-fixture",
            "seed": 424242,
            "description": "deterministic C2 fixture",
        },
        "target": {
            "minecraft_version": "1.21.1",
            "loader": "neoforge",
            "modpack_snapshot": "sha256:7c0a23d6013101383d196526e4b6ba6940fb54a0fed10eaed5956ab015cfcc00",
        },
        "geometry": {
            "max_size": {"x": 8, "y": 6, "z": 10},
            "terrain_policy": "flat",
            "architectural_brief": "small deterministic validation fixture",
            "required_spaces": ["entry", "core"],
        },
        "palette": {
            "allow_modded": True,
            "allowed_namespaces": ["minecraft", "examplemod"],
            "forbidden_blocks": ["minecraft:bedrock"],
        },
        "qa": {
            "require_walkability": True,
            "require_complete_interior": False,
            "require_determinism": True,
        },
        "outputs": {"formats": ["sponge_v3"]},
    }


def placements() -> list[dict[str, object]]:
    return [
        {
            "x": 2,
            "y": 1,
            "z": 3,
            "block_state": {
                "name": "examplemod:machine_casing",
                "properties": {"axis": "y", "active": "false"},
            },
        },
        {
            "x": 0,
            "y": 0,
            "z": 0,
            "block_state": {"name": "minecraft:stone", "properties": {}},
        },
        {
            "x": 1,
            "y": 1,
            "z": 3,
            "block_state": {
                "name": "minecraft:oak_stairs",
                "properties": {"waterlogged": "false", "facing": "north", "half": "bottom", "shape": "straight"},
            },
        },
    ]


class ConstructionC2BuildIRTest(unittest.TestCase):
    def test_required_c2_files_exist(self) -> None:
        required = [SCHEMA, MODULE, WORKFLOW]
        missing = [path.relative_to(ROOT).as_posix() for path in required if not path.is_file()]
        self.assertEqual(missing, [])

    def test_workflow_is_read_only_and_revalidates_on_main(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("- main", workflow)
        self.assertIn("feat/construction-c2-canonical-build-ir", workflow)
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertIn("actions/checkout@11d5960a326750d5838078e36cf38b85af677262", workflow)
        self.assertIn("actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065", workflow)
        self.assertIn("python3 -m unittest construction/tests/test_c2_build_ir.py -v", workflow)
        self.assertIn("python3 -m unittest construction/tests/test_c0_foundation.py -v", workflow)
        self.assertIn("python3 construction/scripts/validate_c0.py", workflow)

    @unittest.skipUnless(IMPLEMENTED, "C2 implementation not present yet")
    def test_schema_is_provider_neutral_sparse_palette_ir(self) -> None:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(schema["properties"]["schema_version"]["const"], 1)
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(
            schema["required"],
            ["schema_version", "identity", "target", "bounds", "coordinate_system", "palette", "blocks", "metadata"],
        )
        target = schema["properties"]["target"]["properties"]
        self.assertEqual(target["minecraft_version"]["const"], "1.21.1")
        self.assertIn("neoforge", target["loader"]["enum"])
        self.assertIn("none", target["loader"]["enum"])
        serialized = json.dumps(schema, sort_keys=True)
        for forbidden in ("sponge", "litematic", "block_entity", "entities", "worldgen", "geckolib", "blockbench"):
            self.assertNotIn(forbidden, serialized.lower())

    @unittest.skipUnless(IMPLEMENTED, "C2 implementation not present yet")
    def test_schema_excludes_explicit_air_states(self) -> None:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        name_schema = schema["$defs"]["block_state"]["properties"]["name"]
        self.assertEqual(
            name_schema["not"]["enum"],
            ["minecraft:air", "minecraft:cave_air", "minecraft:void_air"],
        )

    @unittest.skipUnless(IMPLEMENTED, "C2 implementation not present yet")
    def test_canonicalization_is_deterministic_and_does_not_mutate_inputs(self) -> None:
        module = load_build_ir_module()
        spec_a = build_spec()
        spec_b = deepcopy(spec_a)
        blocks_a = placements()
        blocks_b = list(reversed(deepcopy(blocks_a)))
        props = blocks_b[0]["block_state"]["properties"]
        blocks_b[0]["block_state"]["properties"] = dict(reversed(list(props.items())))
        original_spec = deepcopy(spec_a)
        original_blocks = deepcopy(blocks_a)

        ir_a = module.canonicalize_build_ir(spec_a, blocks_a, producer="contract", producer_version="1")
        ir_b = module.canonicalize_build_ir(spec_b, blocks_b, producer="contract", producer_version="1")

        self.assertEqual(ir_a, ir_b)
        self.assertEqual(spec_a, original_spec)
        self.assertEqual(blocks_a, original_blocks)
        self.assertEqual(ir_a["coordinate_system"], {"axes": ["x", "y", "z"], "up": "y", "origin": "min_corner", "unit": "block"})
        self.assertEqual(ir_a["bounds"]["size"], {"x": 8, "y": 6, "z": 10})
        self.assertEqual([block["x"] for block in ir_a["blocks"]], [0, 1, 2])
        self.assertEqual(module.validate_build_ir(ir_a), [])

    @unittest.skipUnless(IMPLEMENTED, "C2 implementation not present yet")
    def test_palette_is_canonical_and_supports_namespaced_modded_states(self) -> None:
        module = load_build_ir_module()
        ir = module.canonicalize_build_ir(build_spec(), placements(), producer="contract", producer_version="1")
        states = ir["palette"]
        self.assertEqual(states, sorted(states, key=module.canonical_block_state_string))
        modded = next(state for state in states if state["name"] == "examplemod:machine_casing")
        self.assertEqual(modded["properties"], {"active": "false", "axis": "y"})
        self.assertRegex(ir["metadata"]["build_spec_sha256"], r"^[0-9a-f]{64}$")
        self.assertRegex(ir["metadata"]["content_sha256"], r"^[0-9a-f]{64}$")

    @unittest.skipUnless(IMPLEMENTED, "C2 implementation not present yet")
    def test_duplicate_coordinates_fail_closed(self) -> None:
        module = load_build_ir_module()
        duplicate = placements() + [deepcopy(placements()[0])]
        with self.assertRaisesRegex(module.BuildIRError, "duplicate coordinate"):
            module.canonicalize_build_ir(build_spec(), duplicate, producer="contract", producer_version="1")

    @unittest.skipUnless(IMPLEMENTED, "C2 implementation not present yet")
    def test_out_of_bounds_and_explicit_air_fail_closed(self) -> None:
        module = load_build_ir_module()
        outside = placements()
        outside[0] = deepcopy(outside[0])
        outside[0]["x"] = 8
        with self.assertRaisesRegex(module.BuildIRError, "out of bounds"):
            module.canonicalize_build_ir(build_spec(), outside, producer="contract", producer_version="1")

        explicit_air = placements()
        explicit_air[0] = deepcopy(explicit_air[0])
        explicit_air[0]["block_state"] = {"name": "minecraft:air", "properties": {}}
        with self.assertRaisesRegex(module.BuildIRError, "explicit air"):
            module.canonicalize_build_ir(build_spec(), explicit_air, producer="contract", producer_version="1")

    @unittest.skipUnless(IMPLEMENTED, "C2 implementation not present yet")
    def test_validator_rejects_schema_invalid_identity_fields(self) -> None:
        module = load_build_ir_module()

        extra_field = module.canonicalize_build_ir(build_spec(), placements(), producer="contract", producer_version="1")
        extra_field["identity"]["unexpected"] = "value"
        extra_field["metadata"]["content_sha256"] = module.fingerprint_build_ir(extra_field)
        extra_errors = module.validate_build_ir(extra_field)
        self.assertTrue(any("identity fields" in error for error in extra_errors), extra_errors)

        invalid_description = module.canonicalize_build_ir(build_spec(), placements(), producer="contract", producer_version="1")
        invalid_description["identity"]["description"] = 42
        invalid_description["metadata"]["content_sha256"] = module.fingerprint_build_ir(invalid_description)
        description_errors = module.validate_build_ir(invalid_description)
        self.assertTrue(any("identity.description" in error for error in description_errors), description_errors)

    @unittest.skipUnless(IMPLEMENTED, "C2 implementation not present yet")
    def test_invalid_state_and_hash_tampering_are_rejected(self) -> None:
        module = load_build_ir_module()
        invalid = placements()
        invalid[0] = deepcopy(invalid[0])
        invalid[0]["block_state"] = {"name": "Machine Casing", "properties": {}}
        with self.assertRaisesRegex(module.BuildIRError, "block state name"):
            module.canonicalize_build_ir(build_spec(), invalid, producer="contract", producer_version="1")

        ir = module.canonicalize_build_ir(build_spec(), placements(), producer="contract", producer_version="1")
        ir["blocks"][0]["x"] = 7
        errors = module.validate_build_ir(ir)
        self.assertTrue(any("content_sha256" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
