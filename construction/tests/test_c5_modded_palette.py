from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONSTRUCTION = ROOT / "construction"
MODULE_PATH = CONSTRUCTION / "core" / "modded_palette.py"
REQUEST_SCHEMA_PATH = CONSTRUCTION / "schemas" / "palette-request.schema.json"
RESOLUTION_SCHEMA_PATH = CONSTRUCTION / "schemas" / "palette-resolution.schema.json"
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "factory-construction-c5-modded-palette.yml"
IMPLEMENTATION_READY = all(
    path.is_file()
    for path in (MODULE_PATH, REQUEST_SCHEMA_PATH, RESOLUTION_SCHEMA_PATH)
)


def load_module():
    spec = importlib.util.spec_from_file_location("construction_c5_modded_palette", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise AssertionError("unable to load C5 modded palette module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_spec(*, allow_modded: bool = True) -> dict[str, object]:
    return {
        "schema_version": 1,
        "identity": {"name": "c5-test", "seed": 5005},
        "target": {
            "minecraft_version": "1.21.1",
            "loader": "neoforge",
            "modpack_snapshot": "physical-modlist-595",
        },
        "geometry": {
            "max_size": {"x": 9, "y": 9, "z": 9},
            "terrain_policy": "flat",
            "architectural_brief": "C5 contract fixture",
            "required_spaces": [],
        },
        "palette": {
            "allow_modded": allow_modded,
            "allowed_namespaces": ["minecraft", "create"],
            "forbidden_blocks": ["create:brass_casing"],
        },
        "qa": {"require_determinism": True},
        "outputs": {"formats": ["sponge_v3"]},
    }


def registry() -> dict[str, object]:
    def state(block: str, **properties: str) -> dict[str, object]:
        return {"block": block, "properties": properties}

    return {
        "schema_version": 1,
        "physical": {
            "captured_at": "2026-09-11T00:00:00Z",
            "source_name": "modlist.txt",
            "source_sha256": "1" * 64,
            "loader_version": "21.1.248",
            "top_level_mods": 595,
            "nested_mods": 0,
            "total_entries": 595,
            "provider_count": 595,
            "unidentified_entries": 0,
        },
        "runtime": {
            "authority": "neoforge_runtime_registry",
            "minecraft_version": "1.21.1",
            "loader": "neoforge",
            "loader_version": "21.1.248",
        },
        "static_index": {"authority": "jar_static_discovery"},
        "blocks": [
            {
                "id": "minecraft:oak_log",
                "namespace": "minecraft",
                "source_mod": "minecraft",
                "available": True,
                "authority": "runtime_registry",
                "safety": "ordinary",
                "states": [
                    state("minecraft:oak_log", axis="x"),
                    state("minecraft:oak_log", axis="y"),
                    state("minecraft:oak_log", axis="z"),
                ],
            },
            {
                "id": "minecraft:stone_bricks",
                "namespace": "minecraft",
                "source_mod": "minecraft",
                "available": True,
                "authority": "runtime_registry",
                "safety": "ordinary",
                "states": [state("minecraft:stone_bricks")],
            },
            {
                "id": "create:cut_granite_bricks",
                "namespace": "create",
                "source_mod": "create",
                "available": True,
                "authority": "runtime_registry",
                "safety": "ordinary",
                "states": [state("create:cut_granite_bricks")],
            },
            {
                "id": "create:brass_casing",
                "namespace": "create",
                "source_mod": "create",
                "available": True,
                "authority": "runtime_registry",
                "safety": "ordinary",
                "states": [state("create:brass_casing")],
            },
            {
                "id": "create:test_block_entity",
                "namespace": "create",
                "source_mod": "create",
                "available": True,
                "authority": "runtime_registry",
                "safety": "block_entity",
                "states": [
                    state("create:test_block_entity", facing="north"),
                    state("create:test_block_entity", facing="south"),
                ],
            },
            {
                "id": "create:test_controller",
                "namespace": "create",
                "source_mod": "create",
                "available": True,
                "authority": "runtime_registry",
                "safety": "multiblock_or_controller",
                "states": [state("create:test_controller")],
            },
            {
                "id": "create:unknown_machine",
                "namespace": "create",
                "source_mod": "create",
                "available": True,
                "authority": "runtime_registry",
                "safety": "unsafe_or_unknown",
                "states": [state("create:unknown_machine")],
            },
            {
                "id": "create:static_only_bricks",
                "namespace": "create",
                "source_mod": "create",
                "available": False,
                "authority": "static_only_unconfirmed",
                "safety": "ordinary",
                "states": [],
            },
        ],
        "content_sha256": "a" * 64,
    }


def request(
    *,
    role: str = "primary_wall",
    required_terms: list[str] | None = None,
    excluded_terms: list[str] | None = None,
    preferred_block_ids: list[str] | None = None,
    preferred_namespaces: list[str] | None = None,
    allowed_safety: list[str] | None = None,
    required_state_properties: dict[str, str] | None = None,
) -> dict[str, object]:
    role_request: dict[str, object] = {
        "role": role,
        "required_terms": required_terms or [],
        "excluded_terms": excluded_terms or [],
        "preferred_block_ids": preferred_block_ids or [],
        "preferred_namespaces": preferred_namespaces or [],
        "required_state_properties": required_state_properties or {},
    }
    if allowed_safety is not None:
        role_request["allowed_safety"] = allowed_safety
    return {"schema_version": 1, "roles": [role_request]}


class ConstructionC5ModdedPaletteTest(unittest.TestCase):
    def test_required_c5_files_exist(self) -> None:
        required = [
            "construction/core/modded_palette.py",
            "construction/schemas/palette-request.schema.json",
            "construction/schemas/palette-resolution.schema.json",
        ]
        missing = [path for path in required if not (ROOT / path).is_file()]
        self.assertEqual(missing, [])

    def test_c5_workflow_is_pinned_read_only_and_runs_regressions(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertIn("actions/checkout@11d5960a326750d5838078e36cf38b85af677262", workflow)
        self.assertIn("actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065", workflow)
        self.assertIn("construction/tests/test_c5_modded_palette.py", workflow)
        self.assertIn("construction/tests/test_c4_modpack_registry.py", workflow)
        self.assertIn("construction/tests/test_c3_vanilla_golden.py", workflow)
        self.assertIn("construction/tests/test_c2_build_ir.py", workflow)
        self.assertIn("construction/tests/test_c0_foundation.py", workflow)
        self.assertIn("construction/scripts/validate_c0.py", workflow)

    @unittest.skipUnless(IMPLEMENTATION_READY, "C5 implementation not present yet")
    def test_request_and_resolution_schemas_define_fail_closed_contract(self) -> None:
        request_schema = json.loads(REQUEST_SCHEMA_PATH.read_text(encoding="utf-8"))
        resolution_schema = json.loads(RESOLUTION_SCHEMA_PATH.read_text(encoding="utf-8"))
        self.assertEqual(request_schema["properties"]["schema_version"]["const"], 1)
        role = request_schema["properties"]["roles"]["items"]
        self.assertEqual(role["properties"]["allowed_safety"]["items"]["enum"], ["ordinary", "block_entity"])
        self.assertIn("required_state_properties", role["properties"])
        self.assertTrue(role["additionalProperties"] is False)
        self.assertEqual(resolution_schema["properties"]["schema_version"]["const"], 1)
        self.assertRegex(resolution_schema["properties"]["registry_fingerprint"]["pattern"], r"64")
        selected = resolution_schema["properties"]["roles"]["items"]["properties"]["selected"]
        self.assertIn("state_candidates", selected["properties"])
        self.assertIn("selected_state", selected["properties"])

    @unittest.skipUnless(IMPLEMENTATION_READY, "C5 implementation not present yet")
    def test_resolution_is_deterministic_and_bound_to_registry_fingerprint(self) -> None:
        module = load_module()
        spec = build_spec()
        reg = registry()
        req = request(required_terms=["brick"], preferred_namespaces=["create", "minecraft"])
        first = module.resolve_palette(spec, reg, req)
        second = module.resolve_palette(spec, reg, req)
        self.assertEqual(first, second)
        self.assertEqual(first["registry_fingerprint"], reg["content_sha256"])
        self.assertEqual(first["roles"][0]["selected"]["block"], "create:cut_granite_bricks")

    @unittest.skipUnless(IMPLEMENTATION_READY, "C5 implementation not present yet")
    def test_allow_modded_false_effectively_restricts_selection_to_minecraft(self) -> None:
        module = load_module()
        spec = build_spec(allow_modded=False)
        req = request(required_terms=["brick"], preferred_namespaces=["create", "minecraft"])
        result = module.resolve_palette(spec, registry(), req)
        self.assertEqual(result["roles"][0]["selected"]["block"], "minecraft:stone_bricks")

    @unittest.skipUnless(IMPLEMENTATION_READY, "C5 implementation not present yet")
    def test_namespaces_forbidden_blocks_and_runtime_authority_are_enforced(self) -> None:
        module = load_module()
        spec = build_spec()
        spec["palette"]["allowed_namespaces"] = ["create"]
        req = request(required_terms=["bricks"], preferred_block_ids=["create:static_only_bricks", "create:brass_casing"])
        result = module.resolve_palette(spec, registry(), req)
        self.assertEqual(result["roles"][0]["selected"]["block"], "create:cut_granite_bricks")
        alternatives = [candidate["block"] for candidate in result["roles"][0]["alternatives"]]
        self.assertNotIn("create:static_only_bricks", alternatives)
        self.assertNotIn("create:brass_casing", alternatives)

    @unittest.skipUnless(IMPLEMENTATION_READY, "C5 implementation not present yet")
    def test_safety_defaults_to_ordinary_and_block_entity_requires_explicit_opt_in(self) -> None:
        module = load_module()
        spec = build_spec()
        with self.assertRaises(module.PaletteResolutionError):
            module.resolve_palette(spec, registry(), request(required_terms=["test_block_entity"]))
        result = module.resolve_palette(
            spec,
            registry(),
            request(required_terms=["test_block_entity"], allowed_safety=["block_entity"]),
        )
        self.assertEqual(result["roles"][0]["selected"]["safety"], "block_entity")

    @unittest.skipUnless(IMPLEMENTATION_READY, "C5 implementation not present yet")
    def test_unsafe_and_multiblock_safety_classes_cannot_be_opted_in(self) -> None:
        module = load_module()
        for block_term, safety in (
            ("test_controller", "multiblock_or_controller"),
            ("unknown_machine", "unsafe_or_unknown"),
        ):
            with self.subTest(safety=safety):
                with self.assertRaises(module.PaletteResolutionError):
                    module.resolve_palette(
                        build_spec(),
                        registry(),
                        request(required_terms=[block_term], allowed_safety=[safety]),
                    )

    @unittest.skipUnless(IMPLEMENTATION_READY, "C5 implementation not present yet")
    def test_required_terms_and_explicit_preferences_have_stable_precedence(self) -> None:
        module = load_module()
        req = request(
            required_terms=["brick"],
            preferred_block_ids=["minecraft:stone_bricks"],
            preferred_namespaces=["create"],
        )
        result = module.resolve_palette(build_spec(), registry(), req)
        self.assertEqual(result["roles"][0]["selected"]["block"], "minecraft:stone_bricks")

    @unittest.skipUnless(IMPLEMENTATION_READY, "C5 implementation not present yet")
    def test_required_state_properties_only_filter_runtime_reported_states(self) -> None:
        module = load_module()
        result = module.resolve_palette(
            build_spec(),
            registry(),
            request(
                role="vertical_frame",
                required_terms=["oak_log"],
                required_state_properties={"axis": "y"},
            ),
        )
        selected = result["roles"][0]["selected"]
        expected = {"block": "minecraft:oak_log", "properties": {"axis": "y"}}
        self.assertEqual(selected["state_candidates"], [expected])
        self.assertEqual(selected["selected_state"], expected)

    @unittest.skipUnless(IMPLEMENTATION_READY, "C5 implementation not present yet")
    def test_multiple_runtime_states_are_preserved_without_arbitrary_selection(self) -> None:
        module = load_module()
        result = module.resolve_palette(
            build_spec(),
            registry(),
            request(role="frame", required_terms=["oak_log"]),
        )
        selected = result["roles"][0]["selected"]
        self.assertEqual(len(selected["state_candidates"]), 3)
        self.assertIsNone(selected["selected_state"])

    @unittest.skipUnless(IMPLEMENTATION_READY, "C5 implementation not present yet")
    def test_zero_candidate_fails_closed(self) -> None:
        module = load_module()
        with self.assertRaises(module.PaletteResolutionError):
            module.resolve_palette(
                build_spec(),
                registry(),
                request(required_terms=["definitely_absent_material"]),
            )

    @unittest.skipUnless(IMPLEMENTATION_READY, "C5 implementation not present yet")
    def test_inputs_are_not_mutated_and_later_phase_export_is_absent(self) -> None:
        module = load_module()
        spec = build_spec()
        reg = registry()
        req = request(required_terms=["brick"])
        snapshots = (copy.deepcopy(spec), copy.deepcopy(reg), copy.deepcopy(req))
        module.resolve_palette(spec, reg, req)
        self.assertEqual((spec, reg, req), snapshots)
        source = MODULE_PATH.read_text(encoding="utf-8").lower()
        self.assertNotIn(".schem", source)
        self.assertNotIn("sponge", source)
        self.assertNotIn("structure_nbt", source)
        self.assertNotIn("litematic", source)


if __name__ == "__main__":
    unittest.main()
