from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONSTRUCTION = ROOT / "construction"
MODULE_PATH = CONSTRUCTION / "core" / "modded_palette.py"
C4_MODULE_PATH = CONSTRUCTION / "core" / "modpack_registry.py"
REQUEST_SCHEMA_PATH = CONSTRUCTION / "schemas" / "palette-request.schema.json"
RESOLUTION_SCHEMA_PATH = CONSTRUCTION / "schemas" / "palette-resolution.schema.json"
I2_IMPORTER = ROOT / "engineering" / "tooling" / "import-physical-modlist.py"
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "factory-construction-c5-modded-palette.yml"
IMPLEMENTATION_READY = all(
    path.is_file()
    for path in (MODULE_PATH, REQUEST_SCHEMA_PATH, RESOLUTION_SCHEMA_PATH)
)

PHYSICAL_SAMPLE = """Mods count: 4

jar name | notes | mod id | mod name | mod version | mixin configs | modrinth hash | curseforge hash
---------+-------+--------+----------+-------------+---------------+---------------+----------------
neoforge-21.1.248 (modloader) | | neoforge | neoforge | neoforge-21.1.248 | | |
alpha-1.0.0.jar | | alpha | Alpha | 1.0.0 | alpha.mixins.json | aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa | 111
    /META-INF/jarjar/metadata-only.jar | | | | | | |
opaque-top-level.jar | | | | | | |
beta-1.1.0.jar | | beta | Beta | 1.1.0 | | bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb | 222
"""


def load_path(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_module():
    return load_path(MODULE_PATH, "construction_c5_modded_palette")


def c4_registry_module():
    return load_path(C4_MODULE_PATH, "construction_c4_registry_for_c5")


def build_spec(*, allow_modded: bool = True) -> dict[str, object]:
    return {
        "schema_version": 1,
        "identity": {"name": "c5-test", "seed": 5005},
        "target": {
            "minecraft_version": "1.21.1",
            "loader": "neoforge",
            "modpack_snapshot": "physical-modlist-test",
        },
        "geometry": {
            "max_size": {"x": 9, "y": 9, "z": 9},
            "terrain_policy": "flat",
            "architectural_brief": "C5 contract fixture",
            "required_spaces": [],
        },
        "palette": {
            "allow_modded": allow_modded,
            "allowed_namespaces": ["minecraft", "alpha"],
            "forbidden_blocks": ["alpha:brass_casing"],
        },
        "qa": {"require_determinism": True},
        "outputs": {"formats": ["sponge_v3"]},
    }


def registry() -> dict[str, object]:
    c4 = c4_registry_module()
    i2 = load_path(I2_IMPORTER, "engineering_i2_modlist_for_c5")
    physical = i2.parse_modlist_text(PHYSICAL_SAMPLE, captured_at="2026-09-11")
    runtime = {
        "schema_version": 1,
        "captured_at": "2026-09-11T00:00:00Z",
        "physical_snapshot_sha256": physical["source_sha256"],
        "target": {
            "minecraft": "1.21.1",
            "loader": "neoforge",
            "loader_version": "21.1.248",
        },
        "blocks": [
            {
                "id": "alpha:brass_casing",
                "states": [{}],
                "safety": "ordinary",
            },
            {
                "id": "alpha:cut_granite_bricks",
                "states": [{}],
                "safety": "ordinary",
            },
            {
                "id": "alpha:future_machine",
                "states": [{}],
                "safety": "functional_machine",
            },
            {
                "id": "alpha:test_block_entity",
                "states": [{"facing": "north"}, {"facing": "south"}],
                "safety": "block_entity",
            },
            {
                "id": "minecraft:oak_log",
                "states": [{"axis": "x"}, {"axis": "y"}, {"axis": "z"}],
                "safety": "ordinary",
            },
            {
                "id": "minecraft:stone_bricks",
                "states": [{}],
                "safety": "ordinary",
            },
        ],
    }
    static_indexes = [
        {
            "jar": "alpha-1.0.0.jar",
            "sha256": "0" * 64,
            "mod_ids": ["alpha"],
            "blockstates": [
                "alpha:cut_granite_bricks",
                "alpha:static_only_bricks",
            ],
            "block_models": [],
            "block_textures": [],
            "nested_jars": [],
        }
    ]
    return c4.build_modpack_registry(physical, static_indexes, runtime)


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
        self.assertEqual(
            role["properties"]["allowed_safety"]["items"]["enum"],
            ["ordinary", "block_entity"],
        )
        self.assertIn("required_state_properties", role["properties"])
        self.assertTrue(role["additionalProperties"] is False)
        self.assertEqual(resolution_schema["properties"]["schema_version"]["const"], 1)
        self.assertRegex(resolution_schema["properties"]["registry_fingerprint"]["pattern"], r"64")
        selected = resolution_schema["properties"]["roles"]["items"]["properties"]["selected"]
        self.assertIn("state_candidates", selected["properties"])
        self.assertIn("selected_state", selected["properties"])
        self.assertIn("authority", selected["properties"])
        self.assertNotIn("source_mod", selected["properties"])

    @unittest.skipUnless(IMPLEMENTATION_READY, "C5 implementation not present yet")
    def test_fixture_is_produced_by_canonical_c4_registry_contract(self) -> None:
        reg = registry()
        blocks = {block["id"]: block for block in reg["blocks"]}
        self.assertEqual("runtime_confirmed", blocks["alpha:cut_granite_bricks"]["authority"])
        self.assertEqual([{}], blocks["alpha:cut_granite_bricks"]["states"])
        self.assertEqual(
            "static_only_unconfirmed",
            blocks["alpha:static_only_bricks"]["authority"],
        )
        self.assertNotIn("namespace", blocks["alpha:cut_granite_bricks"])
        self.assertNotIn("source_mod", blocks["alpha:cut_granite_bricks"])

    @unittest.skipUnless(IMPLEMENTATION_READY, "C5 implementation not present yet")
    def test_resolution_is_deterministic_and_bound_to_registry_fingerprint(self) -> None:
        module = load_module()
        spec = build_spec()
        reg = registry()
        req = request(required_terms=["brick"], preferred_namespaces=["alpha", "minecraft"])
        first = module.resolve_palette(spec, reg, req)
        second = module.resolve_palette(spec, reg, req)
        self.assertEqual(first, second)
        self.assertEqual(first["registry_fingerprint"], reg["content_sha256"])
        selected = first["roles"][0]["selected"]
        self.assertEqual(selected["block"], "alpha:cut_granite_bricks")
        self.assertEqual(selected["namespace"], "alpha")
        self.assertEqual(selected["authority"], "runtime_confirmed")

    @unittest.skipUnless(IMPLEMENTATION_READY, "C5 implementation not present yet")
    def test_registry_fingerprint_is_verified_not_merely_copied(self) -> None:
        module = load_module()
        reg = registry()
        reg["blocks"][0]["id"] = "alpha:tampered_block"
        with self.assertRaises(module.PaletteResolutionError):
            module.resolve_palette(
                build_spec(),
                reg,
                request(required_terms=["brick"]),
            )

    @unittest.skipUnless(IMPLEMENTATION_READY, "C5 implementation not present yet")
    def test_build_spec_target_must_match_c4_runtime_target(self) -> None:
        module = load_module()
        spec = build_spec()
        spec["target"]["minecraft_version"] = "1.20.1"
        with self.assertRaises(module.PaletteResolutionError):
            module.resolve_palette(spec, registry(), request(required_terms=["brick"]))

    @unittest.skipUnless(IMPLEMENTATION_READY, "C5 implementation not present yet")
    def test_allow_modded_false_effectively_restricts_selection_to_minecraft(self) -> None:
        module = load_module()
        spec = build_spec(allow_modded=False)
        req = request(required_terms=["brick"], preferred_namespaces=["alpha", "minecraft"])
        result = module.resolve_palette(spec, registry(), req)
        self.assertEqual(result["roles"][0]["selected"]["block"], "minecraft:stone_bricks")

    @unittest.skipUnless(IMPLEMENTATION_READY, "C5 implementation not present yet")
    def test_namespaces_forbidden_blocks_and_c4_authority_are_enforced(self) -> None:
        module = load_module()
        spec = build_spec()
        spec["palette"]["allowed_namespaces"] = ["alpha"]
        req = request(
            required_terms=["bricks"],
            preferred_block_ids=["alpha:static_only_bricks", "alpha:brass_casing"],
        )
        result = module.resolve_palette(spec, registry(), req)
        self.assertEqual(result["roles"][0]["selected"]["block"], "alpha:cut_granite_bricks")
        alternatives = [candidate["block"] for candidate in result["roles"][0]["alternatives"]]
        self.assertNotIn("alpha:static_only_bricks", alternatives)
        self.assertNotIn("alpha:brass_casing", alternatives)

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
    def test_reserved_c4_safety_classes_cannot_be_opted_in_by_c5(self) -> None:
        module = load_module()
        with self.assertRaises(module.PaletteResolutionError):
            module.resolve_palette(
                build_spec(),
                registry(),
                request(required_terms=["future_machine"], allowed_safety=["functional_machine"]),
            )

    @unittest.skipUnless(IMPLEMENTATION_READY, "C5 implementation not present yet")
    def test_required_terms_and_explicit_preferences_have_stable_precedence(self) -> None:
        module = load_module()
        req = request(
            required_terms=["brick"],
            preferred_block_ids=["minecraft:stone_bricks"],
            preferred_namespaces=["alpha"],
        )
        result = module.resolve_palette(build_spec(), registry(), req)
        self.assertEqual(result["roles"][0]["selected"]["block"], "minecraft:stone_bricks")

    @unittest.skipUnless(IMPLEMENTATION_READY, "C5 implementation not present yet")
    def test_required_state_properties_normalize_c4_states_to_c2_blockstates(self) -> None:
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
        expected = {"name": "minecraft:oak_log", "properties": {"axis": "y"}}
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
        self.assertEqual(
            [candidate["properties"]["axis"] for candidate in selected["state_candidates"]],
            ["x", "y", "z"],
        )

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
