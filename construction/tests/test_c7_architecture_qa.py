from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONSTRUCTION = ROOT / "construction"
MODULE_PATH = CONSTRUCTION / "core" / "structural_qa.py"
C2_MODULE_PATH = CONSTRUCTION / "core" / "build_ir.py"
SCHEMA_PATH = CONSTRUCTION / "schemas" / "structural-qa-report.schema.json"
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "factory-construction-c7-architecture-qa.yml"
VANILLA_SPEC_PATH = CONSTRUCTION / "fixtures" / "vanilla-golden" / "build-spec.json"
VANILLA_IR_PATH = CONSTRUCTION / "fixtures" / "vanilla-golden" / "expected-build-ir.json"
IMPLEMENTATION_READY = MODULE_PATH.is_file()

CHECK_ORDER = [
    "bounds",
    "runtime_state_validity",
    "head_clearance",
    "walkable_surface_graph",
    "circulation_components",
    "vertical_step_connectivity",
    "enclosure",
    "floor_continuity_semantic",
    "unsupported_placement",
]


def load_path(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_module():
    return load_path(MODULE_PATH, "construction_c7_structural_qa")


def c2_module():
    return load_path(C2_MODULE_PATH, "construction_c2_for_c7")


def canonical_json_bytes(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def make_build_spec(
    *,
    size: tuple[int, int, int] = (3, 3, 3),
    loader: str = "none",
    allow_modded: bool = False,
    require_walkability: bool = False,
    require_complete_interior: bool = False,
    require_determinism: bool = True,
    seed: int = 7007,
) -> dict[str, object]:
    namespaces = ["minecraft", "test"] if allow_modded else ["minecraft"]
    return {
        "schema_version": 1,
        "identity": {
            "name": "c7-architecture-qa-test",
            "seed": seed,
            "description": "Deterministic C7 Architecture QA fixture",
        },
        "target": {
            "minecraft_version": "1.21.1",
            "loader": loader,
            **({"modpack_snapshot": "c7-test-snapshot"} if loader == "neoforge" else {}),
        },
        "geometry": {
            "max_size": {"x": size[0], "y": size[1], "z": size[2]},
            "terrain_policy": "flat",
            "architectural_brief": "C7 conservative structural QA fixture",
            "required_spaces": ["test_space"],
        },
        "palette": {
            "allow_modded": allow_modded,
            "allowed_namespaces": namespaces,
            "forbidden_blocks": [],
        },
        "qa": {
            "require_walkability": require_walkability,
            "require_complete_interior": require_complete_interior,
            "require_determinism": require_determinism,
        },
        "outputs": {"formats": ["sponge_v3"]},
    }


def placement(x: int, y: int, z: int, name: str = "minecraft:stone_bricks", properties=None):
    return {
        "x": x,
        "y": y,
        "z": z,
        "block_state": {
            "name": name,
            "properties": dict(properties or {}),
        },
    }


def make_ir(build_spec: dict[str, object], placements: list[dict[str, object]]):
    return c2_module().canonicalize_build_ir(
        build_spec,
        placements,
        producer="construction-c7-test",
        producer_version="1",
    )


def registry_with_blocks(blocks: list[dict[str, object]]) -> dict[str, object]:
    document: dict[str, object] = {
        "schema_version": 1,
        "physical": {
            "captured_at": "2026-09-11T00:00:00Z",
            "source_name": "c7-test-modlist.txt",
            "source_sha256": "1" * 64,
            "loader_version": "21.1.248",
            "top_level_mods": 1,
            "nested_mods": 0,
            "total_entries": 1,
            "provider_count": 1,
            "unidentified_entries": 0,
        },
        "runtime": {
            "captured_at": "2026-09-11T00:00:00Z",
            "physical_snapshot_sha256": "1" * 64,
            "target": {
                "minecraft": "1.21.1",
                "loader": "neoforge",
                "loader_version": "21.1.248",
            },
        },
        "static_index": {
            "jar_count": 0,
            "nested_jar_count": 0,
            "discovered_block_count": 0,
        },
        "blocks": blocks,
    }
    document["content_sha256"] = hashlib.sha256(canonical_json_bytes(document)).hexdigest()
    return document


def matching_registry(build_ir: dict[str, object]) -> dict[str, object]:
    blocks = []
    for state in build_ir["palette"]:
        blocks.append(
            {
                "id": state["name"],
                "available": True,
                "authority": "runtime_confirmed",
                "static_discovered": False,
                "states": [copy.deepcopy(state["properties"])],
                "safety": "ordinary",
            }
        )
    return registry_with_blocks(blocks)


def check(report: dict[str, object], check_id: str) -> dict[str, object]:
    for item in report["checks"]:
        if item["id"] == check_id:
            return item
    raise AssertionError(f"missing check: {check_id}")


class ConstructionC7ArchitectureQATest(unittest.TestCase):
    def test_required_c7_production_file_exists(self) -> None:
        self.assertTrue(
            MODULE_PATH.is_file(),
            "C7 production module is required at construction/core/structural_qa.py",
        )

    def test_report_schema_declares_closed_c7_contract(self) -> None:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(schema["properties"]["schema_version"]["const"], 1)
        self.assertEqual(
            schema["properties"]["overall_status"]["enum"],
            ["PASS", "FAIL", "DEFERRED"],
        )
        self.assertEqual(schema["properties"]["checks"]["minItems"], len(CHECK_ORDER))
        self.assertEqual(schema["properties"]["checks"]["maxItems"], len(CHECK_ORDER))
        self.assertEqual(
            schema["$defs"]["check"]["properties"]["id"]["enum"],
            CHECK_ORDER,
        )
        self.assertIn("required", schema["$defs"]["check"]["required"])
        self.assertFalse(schema["$defs"]["check"]["additionalProperties"])
        self.assertFalse(schema["properties"]["metrics"]["additionalProperties"])

    def test_c7_workflow_is_pinned_read_only_and_runs_full_regressions(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertIn(
            "actions/checkout@11d5960a326750d5838078e36cf38b85af677262",
            workflow,
        )
        self.assertIn(
            "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065",
            workflow,
        )
        self.assertIn(
            "actions/setup-java@cf277c60eb25467037889841efdb72551f06f6c3",
            workflow,
        )
        self.assertIn("python-version: '3.11'", workflow)
        self.assertIn("java-version: '21'", workflow)
        self.assertIn("--require-hashes --no-deps", workflow)
        self.assertIn("engineering/tests/test_i2_modlist_catalog.py", workflow)
        self.assertIn("engineering/tests/test_i2_security_review.py", workflow)
        for test_path in (
            "construction/tests/test_c7_architecture_qa.py",
            "construction/tests/test_c6_sponge_v3.py",
            "construction/tests/test_c5_modded_palette.py",
            "construction/tests/test_c4_modpack_registry.py",
            "construction/tests/test_c4_runtime_registry_probe.py",
            "construction/tests/test_c3_vanilla_golden.py",
            "construction/tests/test_c2_build_ir.py",
            "construction/tests/test_c0_foundation.py",
        ):
            self.assertIn(test_path, workflow)
        self.assertIn("construction/scripts/prepare_neoforge_registry_probe.py", workflow)
        self.assertIn("./gradlew test build --no-daemon", workflow)
        self.assertIn("construction/scripts/validate_c0.py", workflow)
        self.assertIn("git diff --check HEAD^ --", workflow)

    @unittest.skipUnless(IMPLEMENTATION_READY, "C7 implementation not present yet")
    def test_single_floor_walkability_and_single_component_pass(self) -> None:
        module = load_module()
        spec = make_build_spec(size=(2, 3, 1), require_walkability=True)
        ir = make_ir(spec, [placement(0, 0, 0), placement(1, 0, 0)])
        report = module.run_structural_qa(spec, ir)

        self.assertEqual(report["overall_status"], "PASS")
        self.assertEqual(check(report, "head_clearance")["status"], "PASS")
        self.assertEqual(check(report, "walkable_surface_graph")["status"], "PASS")
        self.assertEqual(check(report, "circulation_components")["status"], "PASS")
        self.assertEqual(check(report, "vertical_step_connectivity")["status"], "NOT_APPLICABLE")
        self.assertEqual(report["metrics"]["clear_foot_cell_count"], 2)
        self.assertEqual(report["metrics"]["walkable_component_count"], 1)
        self.assertEqual(report["metrics"]["component_sizes"], [2])

    @unittest.skipUnless(IMPLEMENTATION_READY, "C7 implementation not present yet")
    def test_zero_clear_cell_fails_when_walkability_is_required(self) -> None:
        module = load_module()
        spec = make_build_spec(size=(1, 2, 1), require_walkability=True)
        ir = make_ir(spec, [placement(0, 0, 0)])
        report = module.run_structural_qa(spec, ir)

        self.assertEqual(report["overall_status"], "FAIL")
        self.assertEqual(check(report, "head_clearance")["status"], "FAIL")
        self.assertEqual(check(report, "walkable_surface_graph")["status"], "FAIL")
        self.assertEqual(check(report, "circulation_components")["status"], "FAIL")
        self.assertEqual(report["metrics"]["clear_foot_cell_count"], 0)

    @unittest.skipUnless(IMPLEMENTATION_READY, "C7 implementation not present yet")
    def test_blocked_supported_cells_are_informational_when_clear_space_exists(self) -> None:
        module = load_module()
        spec = make_build_spec(size=(2, 3, 1), require_walkability=True)
        ir = make_ir(
            spec,
            [
                placement(0, 0, 0),
                placement(1, 0, 0),
                placement(1, 2, 0, "minecraft:oak_planks"),
            ],
        )
        report = module.run_structural_qa(spec, ir)

        self.assertEqual(check(report, "head_clearance")["status"], "PASS")
        self.assertEqual(report["metrics"]["supported_foot_cell_count"], 2)
        self.assertEqual(report["metrics"]["clear_foot_cell_count"], 1)
        self.assertEqual(report["metrics"]["blocked_supported_cell_count"], 1)
        self.assertTrue(
            any(finding["code"] == "blocked_supported_cell" for finding in check(report, "head_clearance")["findings"])
        )

    @unittest.skipUnless(IMPLEMENTATION_READY, "C7 implementation not present yet")
    def test_disconnected_walkable_components_are_deferred_not_fabricated_fail(self) -> None:
        module = load_module()
        spec = make_build_spec(size=(3, 3, 1), require_walkability=True)
        ir = make_ir(spec, [placement(0, 0, 0), placement(2, 0, 0)])
        report = module.run_structural_qa(spec, ir)

        self.assertEqual(report["metrics"]["walkable_component_count"], 2)
        self.assertEqual(check(report, "circulation_components")["status"], "DEFERRED")
        self.assertTrue(check(report, "circulation_components")["required"])
        self.assertEqual(report["overall_status"], "DEFERRED")

    @unittest.skipUnless(IMPLEMENTATION_READY, "C7 implementation not present yet")
    def test_one_block_vertical_step_is_detected(self) -> None:
        module = load_module()
        spec = make_build_spec(size=(2, 4, 1), require_walkability=True)
        ir = make_ir(spec, [placement(0, 0, 0), placement(1, 1, 0)])
        report = module.run_structural_qa(spec, ir)

        self.assertEqual(report["metrics"]["walkable_y_levels"], [1, 2])
        self.assertEqual(report["metrics"]["vertical_step_edge_count"], 1)
        self.assertEqual(check(report, "vertical_step_connectivity")["status"], "PASS")
        self.assertEqual(report["metrics"]["walkable_component_count"], 1)

    @unittest.skipUnless(IMPLEMENTATION_READY, "C7 implementation not present yet")
    def test_multilevel_without_step_is_deferred(self) -> None:
        module = load_module()
        spec = make_build_spec(size=(3, 4, 1), require_walkability=True)
        ir = make_ir(spec, [placement(0, 0, 0), placement(2, 1, 0)])
        report = module.run_structural_qa(spec, ir)

        self.assertEqual(report["metrics"]["walkable_y_levels"], [1, 2])
        self.assertEqual(report["metrics"]["vertical_step_edge_count"], 0)
        self.assertEqual(check(report, "vertical_step_connectivity")["status"], "DEFERRED")
        self.assertTrue(check(report, "vertical_step_connectivity")["required"])
        self.assertEqual(report["overall_status"], "DEFERRED")

    @unittest.skipUnless(IMPLEMENTATION_READY, "C7 implementation not present yet")
    def test_runtime_confirmed_state_is_accepted(self) -> None:
        module = load_module()
        spec = make_build_spec(loader="neoforge", allow_modded=True)
        ir = make_ir(spec, [placement(0, 0, 0, "test:bricks", {"facing": "north"})])
        registry = matching_registry(ir)
        report = module.run_structural_qa(spec, ir, registry)

        self.assertEqual(check(report, "runtime_state_validity")["status"], "PASS")
        self.assertTrue(check(report, "runtime_state_validity")["required"])
        self.assertEqual(report["registry_fingerprint"], registry["content_sha256"])
        self.assertEqual(report["overall_status"], "PASS")

    @unittest.skipUnless(IMPLEMENTATION_READY, "C7 implementation not present yet")
    def test_runtime_state_missing_static_only_and_property_mismatch_fail(self) -> None:
        module = load_module()
        spec = make_build_spec(loader="neoforge", allow_modded=True)
        ir = make_ir(spec, [placement(0, 0, 0, "test:bricks", {"facing": "north"})])
        base_block = matching_registry(ir)["blocks"][0]

        variants = []
        variants.append(registry_with_blocks([]))


        static_only = copy.deepcopy(base_block)
        static_only["available"] = False
        static_only["authority"] = "static_only_unconfirmed"
        static_only["static_discovered"] = True
        static_only["states"] = []
        static_only["safety"] = "unknown"
        variants.append(registry_with_blocks([static_only]))

        mismatch = copy.deepcopy(base_block)
        mismatch["states"] = [{"facing": "south"}]
        variants.append(registry_with_blocks([mismatch]))

        for registry in variants:
            with self.subTest(registry=registry["blocks"]):
                report = module.run_structural_qa(spec, ir, registry)
                self.assertEqual(check(report, "runtime_state_validity")["status"], "FAIL")
                self.assertEqual(report["overall_status"], "FAIL")

    @unittest.skipUnless(IMPLEMENTATION_READY, "C7 implementation not present yet")
    def test_modded_neoforge_without_registry_is_required_deferred(self) -> None:
        module = load_module()
        spec = make_build_spec(loader="neoforge", allow_modded=True)
        ir = make_ir(spec, [placement(0, 0, 0, "test:bricks")])
        report = module.run_structural_qa(spec, ir)

        state_check = check(report, "runtime_state_validity")
        self.assertTrue(state_check["required"])
        self.assertEqual(state_check["status"], "DEFERRED")
        self.assertEqual(report["overall_status"], "DEFERRED")

    @unittest.skipUnless(IMPLEMENTATION_READY, "C7 implementation not present yet")
    def test_vanilla_no_loader_without_registry_is_not_applicable(self) -> None:
        module = load_module()
        spec = make_build_spec(loader="none", allow_modded=False)
        ir = make_ir(spec, [placement(0, 0, 0)])
        report = module.run_structural_qa(spec, ir)

        state_check = check(report, "runtime_state_validity")
        self.assertFalse(state_check["required"])
        self.assertEqual(state_check["status"], "NOT_APPLICABLE")
        self.assertEqual(report["overall_status"], "PASS")

    @unittest.skipUnless(IMPLEMENTATION_READY, "C7 implementation not present yet")
    def test_complete_interior_requires_deferred_enclosure_and_prevents_pass(self) -> None:
        module = load_module()
        spec = make_build_spec(require_complete_interior=True)
        ir = make_ir(spec, [placement(0, 0, 0)])
        report = module.run_structural_qa(spec, ir)

        enclosure = check(report, "enclosure")
        self.assertTrue(enclosure["required"])
        self.assertEqual(enclosure["status"], "DEFERRED")
        self.assertEqual(report["overall_status"], "DEFERRED")

    @unittest.skipUnless(IMPLEMENTATION_READY, "C7 implementation not present yet")
    def test_semantic_floor_and_provider_support_remain_explicit_deferred(self) -> None:
        module = load_module()
        spec = make_build_spec()
        ir = make_ir(spec, [placement(0, 0, 0)])
        report = module.run_structural_qa(spec, ir)

        for check_id in ("floor_continuity_semantic", "unsupported_placement"):
            item = check(report, check_id)
            self.assertFalse(item["required"])
            self.assertEqual(item["status"], "DEFERRED")

    @unittest.skipUnless(IMPLEMENTATION_READY, "C7 implementation not present yet")
    def test_report_is_deterministic_across_repeated_executions(self) -> None:
        module = load_module()
        spec = make_build_spec(loader="neoforge", allow_modded=True, require_walkability=True)
        ir = make_ir(spec, [placement(0, 0, 0, "test:bricks"), placement(1, 0, 0)])
        registry = matching_registry(ir)

        first = module.run_structural_qa(spec, ir, registry)
        second = module.run_structural_qa(copy.deepcopy(spec), copy.deepcopy(ir), copy.deepcopy(registry))
        self.assertEqual(first, second)
        self.assertEqual(canonical_json_bytes(first), canonical_json_bytes(second))

    @unittest.skipUnless(IMPLEMENTATION_READY, "C7 implementation not present yet")
    def test_report_validator_accepts_canonical_report_and_rejects_mutations(self) -> None:
        module = load_module()
        spec = make_build_spec()
        ir = make_ir(spec, [placement(0, 0, 0)])
        report = module.run_structural_qa(spec, ir)

        self.assertIsNone(module.validate_structural_qa_report(report))

        wrong_order = copy.deepcopy(report)
        wrong_order["checks"][0], wrong_order["checks"][1] = wrong_order["checks"][1], wrong_order["checks"][0]
        with self.assertRaises(module.StructuralQAError):
            module.validate_structural_qa_report(wrong_order)

        invalid_status = copy.deepcopy(report)
        invalid_status["checks"][0]["status"] = "UNKNOWN"
        with self.assertRaises(module.StructuralQAError):
            module.validate_structural_qa_report(invalid_status)

        invalid_sha = copy.deepcopy(report)
        invalid_sha["build_ir_sha256"] = "bad"
        with self.assertRaises(module.StructuralQAError):
            module.validate_structural_qa_report(invalid_sha)

        inconsistent = copy.deepcopy(report)
        inconsistent["overall_status"] = "FAIL" if report["overall_status"] != "FAIL" else "PASS"
        with self.assertRaises(module.StructuralQAError):
            module.validate_structural_qa_report(inconsistent)

    @unittest.skipUnless(IMPLEMENTATION_READY, "C7 implementation not present yet")
    def test_invalid_authoritative_inputs_fail_closed(self) -> None:
        module = load_module()
        spec = make_build_spec()
        ir = make_ir(spec, [placement(0, 0, 0)])

        invalid_spec = copy.deepcopy(spec)
        invalid_spec["qa"]["require_walkability"] = "yes"
        with self.assertRaises(module.StructuralQAError):
            module.run_structural_qa(invalid_spec, ir)

        tampered_ir = copy.deepcopy(ir)
        tampered_ir["target"]["minecraft_version"] = "1.20.1"
        with self.assertRaises(module.StructuralQAError):
            module.run_structural_qa(spec, tampered_ir)

        mismatched_spec = copy.deepcopy(spec)
        mismatched_spec["identity"]["seed"] = 999
        with self.assertRaises(module.StructuralQAError):
            module.run_structural_qa(mismatched_spec, ir)

        registry = matching_registry(ir)
        registry["content_sha256"] = "0" * 64
        with self.assertRaises(module.StructuralQAError):
            module.run_structural_qa(spec, ir, registry)

    @unittest.skipUnless(IMPLEMENTATION_READY, "C7 implementation not present yet")
    def test_build_spec_flags_change_gating_without_changing_geometry_metrics(self) -> None:
        module = load_module()
        off_spec = make_build_spec(size=(3, 3, 1), require_walkability=False)
        on_spec = make_build_spec(size=(3, 3, 1), require_walkability=True)
        placements = [placement(0, 0, 0), placement(2, 0, 0)]
        off_report = module.run_structural_qa(off_spec, make_ir(off_spec, placements))
        on_report = module.run_structural_qa(on_spec, make_ir(on_spec, placements))

        self.assertEqual(off_report["metrics"], on_report["metrics"])
        self.assertEqual(check(off_report, "circulation_components")["status"], "NOT_APPLICABLE")
        self.assertEqual(check(on_report, "circulation_components")["status"], "DEFERRED")
        self.assertEqual(off_report["overall_status"], "PASS")
        self.assertEqual(on_report["overall_status"], "DEFERRED")

    @unittest.skipUnless(IMPLEMENTATION_READY, "C7 implementation not present yet")
    def test_existing_vanilla_golden_is_analyzable_without_visual_claims(self) -> None:
        module = load_module()
        spec = json.loads(VANILLA_SPEC_PATH.read_text(encoding="utf-8"))
        ir = json.loads(VANILLA_IR_PATH.read_text(encoding="utf-8"))
        report = module.run_structural_qa(spec, ir)

        self.assertEqual(report["build_spec_sha256"], ir["metadata"]["build_spec_sha256"])
        self.assertEqual(report["build_ir_sha256"], c2_module().fingerprint_build_ir(ir))
        self.assertEqual([item["id"] for item in report["checks"]], CHECK_ORDER)
        self.assertFalse(any("visual" in item["id"] for item in report["checks"]))
        self.assertEqual(check(report, "enclosure")["status"], "DEFERRED")
        self.assertEqual(check(report, "unsupported_placement")["status"], "DEFERRED")
        self.assertEqual(report["overall_status"], "PASS")


if __name__ == "__main__":
    unittest.main()
