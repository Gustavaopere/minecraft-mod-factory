from __future__ import annotations

import copy
import hashlib
import importlib
import importlib.metadata
import importlib.util
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MCP_DIR = ROOT / "construction" / "mcp"
SERVER_PATH = MCP_DIR / "server.py"
FACADE_PATH = MCP_DIR / "facade.py"
ARTIFACTS_PATH = MCP_DIR / "artifacts.py"
ERRORS_PATH = MCP_DIR / "errors.py"
LOCK_PATH = ROOT / "construction" / "upstream" / "harness" / "c9-mcp-lock.txt"
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "factory-construction-c9-agent-mcp.yml"
SPEC_PATH = ROOT / "docs" / "superpowers" / "specs" / "2026-09-11-construction-c9-agent-mcp-design.md"
PLAN_PATH = ROOT / "docs" / "superpowers" / "plans" / "2026-09-11-construction-c9-agent-mcp.md"

REQUIRED_ACCEPTANCE_TEST_NAMES = (
    "test_mcp_dependency_is_exact_2_2_0",
    "test_exact_nine_tool_catalog",
    "test_no_forbidden_tool_surface",
    "test_tool_schemas_are_closed",
    "test_c4_public_validator_parity",
    "test_registry_search_filters_and_order",
    "test_palette_resolve_matches_c5",
    "test_build_canonicalize_matches_c2",
    "test_build_validate_mirrors_c2_errors",
    "test_build_edit_add_replace_remove",
    "test_build_edit_rejects_duplicate_touch_absent_remove_and_bounds",
    "test_build_edit_requires_matching_build_spec_fingerprint",
    "test_qa_structural_matches_c7",
    "test_preview_render_matches_c8_and_is_deterministic",
    "test_preview_bundle_manifest_is_canonical_and_bound",
    "test_qa_visual_matches_c8",
    "test_qa_visual_rejects_forged_stale_or_wrong_ir_bundle",
    "test_export_sponge_v3_matches_c6_and_revalidates",
    "test_artifact_store_deduplicates_and_is_immutable",
    "test_artifact_store_enforces_all_limits",
    "test_errors_are_stable_and_sanitized",
    "test_real_stdio_discovery_and_tool_call",
    "test_real_stdio_resource_read",
    "test_real_stdio_golden_flow",
    "test_stdio_server_terminates_cleanly",
)


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot load module spec for {path.relative_to(ROOT)}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class C9RedContractTests(unittest.TestCase):
    def test_mcp_dependency_is_exact_2_2_0(self) -> None:
        self.assertTrue(LOCK_PATH.is_file())
        self.assertEqual(importlib.metadata.version("mcp"), "2.2.0")
        lock = LOCK_PATH.read_text(encoding="utf-8")
        self.assertIn("mcp==2.2.0 --hash=sha256:", lock)
        self.assertNotIn("mcp>=", lock)
        self.assertNotIn("mcp~=", lock)

    def test_c9_design_and_plan_are_frozen(self) -> None:
        self.assertTrue(SPEC_PATH.is_file())
        self.assertTrue(PLAN_PATH.is_file())
        self.assertEqual(len(REQUIRED_ACCEPTANCE_TEST_NAMES), 25)
        self.assertEqual(len(REQUIRED_ACCEPTANCE_TEST_NAMES), len(set(REQUIRED_ACCEPTANCE_TEST_NAMES)))

    def test_c4_public_validator_parity(self) -> None:
        path = ROOT / "construction" / "core" / "modpack_registry.py"
        module = _load_module(path, "construction_c4_for_c9_contract")
        self.assertTrue(callable(getattr(module, "validate_modpack_registry", None)))

    def test_c9_modules_exist(self) -> None:
        missing = [
            str(path.relative_to(ROOT))
            for path in (SERVER_PATH, FACADE_PATH, ARTIFACTS_PATH, ERRORS_PATH)
            if not path.is_file()
        ]
        self.assertEqual(missing, [], "C9 production modules are not implemented: " + ", ".join(missing))

    def test_c9_workflow_exists(self) -> None:
        self.assertTrue(WORKFLOW_PATH.is_file(), "C9 workflow is not implemented")


class C9ArtifactStoreContractTests(unittest.TestCase):
    def _modules(self):
        self.assertTrue(ARTIFACTS_PATH.is_file(), "C9 ArtifactStore is not implemented")
        self.assertTrue(ERRORS_PATH.is_file(), "C9 error boundary is not implemented")
        errors = importlib.import_module("construction.mcp.errors")
        artifacts = importlib.import_module("construction.mcp.artifacts")
        return artifacts, errors

    def test_artifact_store_deduplicates_and_is_immutable(self) -> None:
        artifacts, errors = self._modules()
        store = artifacts.ArtifactStore()
        data = b"abc"
        sha256 = hashlib.sha256(data).hexdigest()
        expected = {
            "uri": f"construction://artifact/sha256/{sha256}",
            "media_type": "application/octet-stream",
            "sha256": sha256,
            "byte_length": 3,
            "kind": "sponge_v3",
        }

        descriptor = store.put(data, media_type="application/octet-stream", kind="sponge_v3")
        self.assertEqual(descriptor, expected)
        self.assertEqual(store.put(data, media_type="application/octet-stream", kind="sponge_v3"), expected)
        self.assertEqual(store.list_descriptors(), [expected])

        record = store.get(expected["uri"])
        self.assertEqual(record.uri, expected["uri"])
        self.assertEqual(record.data, data)
        self.assertEqual(record.media_type, "application/octet-stream")
        self.assertEqual(record.sha256, sha256)
        self.assertEqual(record.byte_length, 3)
        self.assertEqual(record.kind, "sponge_v3")
        with self.assertRaises(FrozenInstanceError):
            record.media_type = "text/plain"

        second = store.put(b"def", media_type="application/json", kind="preview_bundle")
        self.assertEqual(
            store.list_descriptors(),
            sorted([expected, second], key=lambda item: item["uri"]),
        )

        with self.assertRaises(errors.C9Error) as invalid_uri:
            store.get("file:///tmp/not-an-artifact")
        self.assertEqual(invalid_uri.exception.code, "INVALID_INPUT")

        unknown_uri = "construction://artifact/sha256/" + ("0" * 64)
        with self.assertRaises(errors.C9Error) as missing:
            store.get(unknown_uri)
        self.assertEqual(missing.exception.code, "ARTIFACT_NOT_FOUND")

        collision_store = artifacts.ArtifactStore(_digest_fn=lambda _data: "a" * 64)
        collision_store.put(b"left", media_type="application/octet-stream", kind="sponge_v3")
        with self.assertRaises(errors.C9Error) as collision:
            collision_store.put(b"right", media_type="application/octet-stream", kind="sponge_v3")
        self.assertEqual(collision.exception.code, "INTERNAL_ERROR")

    def test_artifact_store_enforces_all_limits(self) -> None:
        artifacts, errors = self._modules()
        mib = 1024 * 1024

        single = artifacts.ArtifactStore()
        at_single_limit = b"x" * (64 * mib)
        descriptor = single.put(
            at_single_limit,
            media_type="application/octet-stream",
            kind="sponge_v3",
        )
        self.assertEqual(descriptor["byte_length"], 64 * mib)
        before = single.list_descriptors()
        with self.assertRaises(errors.C9Error) as too_large:
            single.put(
                b"y" * ((64 * mib) + 1),
                media_type="application/octet-stream",
                kind="sponge_v3",
            )
        self.assertEqual(too_large.exception.code, "ARTIFACT_LIMIT")
        self.assertEqual(single.list_descriptors(), before)

        aggregate = artifacts.ArtifactStore()
        for value in range(4):
            aggregate.put(
                bytes([value]) * (64 * mib),
                media_type="application/octet-stream",
                kind="sponge_v3",
            )
        self.assertEqual(sum(item["byte_length"] for item in aggregate.list_descriptors()), 256 * mib)
        before = aggregate.list_descriptors()
        with self.assertRaises(errors.C9Error) as aggregate_limit:
            aggregate.put(b"overflow", media_type="application/octet-stream", kind="sponge_v3")
        self.assertEqual(aggregate_limit.exception.code, "ARTIFACT_LIMIT")
        self.assertEqual(aggregate.list_descriptors(), before)

        records = artifacts.ArtifactStore()
        for value in range(512):
            records.put(
                value.to_bytes(2, "big"),
                media_type="application/octet-stream",
                kind="sponge_v3",
            )
        self.assertEqual(len(records.list_descriptors()), 512)
        before = records.list_descriptors()
        with self.assertRaises(errors.C9Error) as record_limit:
            records.put(b"record-513", media_type="application/octet-stream", kind="sponge_v3")
        self.assertEqual(record_limit.exception.code, "ARTIFACT_LIMIT")
        self.assertEqual(records.list_descriptors(), before)

        invalid = artifacts.ArtifactStore()
        for media_type, kind in (
            ("text/plain", "sponge_v3"),
            ("application/octet-stream", "unknown"),
        ):
            with self.subTest(media_type=media_type, kind=kind):
                with self.assertRaises(errors.C9Error) as rejected:
                    invalid.put(b"x", media_type=media_type, kind=kind)
                self.assertEqual(rejected.exception.code, "INVALID_INPUT")
                self.assertEqual(invalid.list_descriptors(), [])

    def test_errors_are_stable_and_sanitized(self) -> None:
        _artifacts, errors = self._modules()
        error = errors.C9Error(
            "AUTHORITY_REJECTED",
            "C4 rejected supplied registry",
            authority="C4",
            details=["registry.blocks[0].authority is invalid"],
        )
        self.assertEqual(str(error), "C4 rejected supplied registry")
        self.assertEqual(
            error.payload(),
            {
                "code": "AUTHORITY_REJECTED",
                "message": "C4 rejected supplied registry",
                "authority": "C4",
                "details": ["registry.blocks[0].authority is invalid"],
            },
        )
        self.assertEqual(
            errors.C9Error("INVALID_INPUT", "request is invalid").payload(),
            {"code": "INVALID_INPUT", "message": "request is invalid"},
        )

        for code in ("INVALID_INPUT", "AUTHORITY_REJECTED", "ARTIFACT_NOT_FOUND", "ARTIFACT_LIMIT", "INTERNAL_ERROR"):
            with self.subTest(code=code):
                authority = "C2" if code == "AUTHORITY_REJECTED" else None
                self.assertEqual(errors.C9Error(code, "stable", authority=authority).code, code)

        with self.assertRaises(ValueError):
            errors.C9Error("UNKNOWN", "must reject unstable codes")
        with self.assertRaises(ValueError):
            errors.C9Error("AUTHORITY_REJECTED", "bad authority", authority="C9")
        with self.assertRaises(ValueError):
            errors.C9Error("INVALID_INPUT", "authority is not valid here", authority="C2")

        payload = error.payload()
        serialized = repr(payload).lower()
        self.assertNotIn("traceback", serialized)
        self.assertNotIn(str(ROOT).lower(), serialized)
        self.assertNotIn("environment", serialized)


class C9FacadeParityContractTests(unittest.TestCase):
    def _modules(self):
        self.assertTrue(FACADE_PATH.is_file(), "C9 facade is not implemented")
        facade_module = importlib.import_module("construction.mcp.facade")
        artifacts = importlib.import_module("construction.mcp.artifacts")
        errors = importlib.import_module("construction.mcp.errors")
        c2 = _load_module(ROOT / "construction" / "core" / "build_ir.py", "construction_c2_for_c9_facade")
        c4 = _load_module(ROOT / "construction" / "core" / "modpack_registry.py", "construction_c4_for_c9_facade")
        c5 = _load_module(ROOT / "construction" / "core" / "modded_palette.py", "construction_c5_for_c9_facade")
        fixtures = _load_module(
            ROOT / "construction" / "tests" / "test_c5_modded_palette.py",
            "construction_c5_fixtures_for_c9_facade",
        )
        facade = facade_module.ConstructionFacade(artifacts.ArtifactStore())
        return facade, errors, c2, c4, c5, fixtures

    def test_registry_search_filters_and_order(self) -> None:
        facade, errors, _c2, _c4, _c5, fixtures = self._modules()
        registry = fixtures.registry()
        expected = [
            {
                "id": block["id"],
                "namespace": block["id"].split(":", 1)[0],
                "available": block["available"],
                "authority": block["authority"],
                "safety": block["safety"],
                "state_count": len(block["states"]),
            }
            for block in sorted(registry["blocks"], key=lambda item: item["id"])
        ]
        self.assertEqual(
            facade.registry_search(
                registry,
                query=None,
                namespace=None,
                authority=None,
                safety=None,
                limit=25,
            ),
            expected,
        )
        self.assertEqual(
            facade.registry_search(
                registry,
                query="brick",
                namespace="alpha",
                authority="runtime_confirmed",
                safety=["ordinary"],
                limit=25,
            ),
            [item for item in expected if item["id"] == "alpha:cut_granite_bricks"],
        )
        self.assertEqual(
            facade.registry_search(
                registry,
                query=None,
                namespace=None,
                authority=None,
                safety=None,
                limit=2,
            ),
            expected[:2],
        )

        tampered = copy.deepcopy(registry)
        tampered["blocks"][0]["authority"] = "invented"
        with self.assertRaises(errors.C9Error) as rejected_registry:
            facade.registry_search(
                tampered,
                query=None,
                namespace=None,
                authority=None,
                safety=None,
                limit=25,
            )
        self.assertEqual(rejected_registry.exception.code, "AUTHORITY_REJECTED")
        self.assertEqual(rejected_registry.exception.authority, "C4")

        invalid_filters = (
            {"query": "Brick"},
            {"namespace": "Alpha"},
            {"authority": "invented"},
            {"safety": []},
            {"safety": ["invented"]},
            {"limit": 0},
            {"limit": 101},
            {"limit": True},
        )
        for override in invalid_filters:
            kwargs = {
                "query": None,
                "namespace": None,
                "authority": None,
                "safety": None,
                "limit": 25,
            }
            kwargs.update(override)
            with self.subTest(override=override):
                with self.assertRaises(errors.C9Error) as rejected_filter:
                    facade.registry_search(registry, **kwargs)
                self.assertEqual(rejected_filter.exception.code, "INVALID_INPUT")

    def test_palette_resolve_matches_c5(self) -> None:
        facade, errors, _c2, _c4, c5, fixtures = self._modules()
        build_spec = fixtures.build_spec()
        registry = fixtures.registry()
        request = fixtures.request(
            required_terms=["brick"],
            preferred_namespaces=["alpha", "minecraft"],
        )
        expected = c5.resolve_palette(build_spec, registry, request)
        self.assertEqual(facade.palette_resolve(build_spec, registry, request), expected)

        impossible = fixtures.request(required_terms=["definitely_missing_block"])
        with self.assertRaises(c5.PaletteResolutionError) as direct:
            c5.resolve_palette(build_spec, registry, impossible)
        with self.assertRaises(errors.C9Error) as wrapped:
            facade.palette_resolve(build_spec, registry, impossible)
        self.assertEqual(wrapped.exception.code, "AUTHORITY_REJECTED")
        self.assertEqual(wrapped.exception.authority, "C5")
        self.assertEqual(wrapped.exception.details, [str(direct.exception)])

    def test_build_canonicalize_matches_c2(self) -> None:
        facade, errors, c2, _c4, _c5, fixtures = self._modules()
        build_spec = fixtures.build_spec()
        placements = [
            {
                "x": 2,
                "y": 0,
                "z": 0,
                "block_state": {"name": "minecraft:oak_log", "properties": {"axis": "y"}},
            },
            {
                "x": 0,
                "y": 0,
                "z": 0,
                "block_state": {"name": "minecraft:stone_bricks", "properties": {}},
            },
        ]
        expected = c2.canonicalize_build_ir(
            build_spec,
            placements,
            producer="construction-c9-mcp",
            producer_version="c9-mcp-v1",
        )
        self.assertEqual(facade.build_canonicalize(build_spec, placements), expected)

        invalid = copy.deepcopy(placements)
        invalid[0]["x"] = 99
        with self.assertRaises(c2.BuildIRError) as direct:
            c2.canonicalize_build_ir(
                build_spec,
                invalid,
                producer="construction-c9-mcp",
                producer_version="c9-mcp-v1",
            )
        with self.assertRaises(errors.C9Error) as wrapped:
            facade.build_canonicalize(build_spec, invalid)
        self.assertEqual(wrapped.exception.code, "AUTHORITY_REJECTED")
        self.assertEqual(wrapped.exception.authority, "C2")
        self.assertEqual(wrapped.exception.details, [str(direct.exception)])

    def test_build_validate_mirrors_c2_errors(self) -> None:
        facade, _errors, c2, _c4, _c5, fixtures = self._modules()
        build_spec = fixtures.build_spec()
        build_ir = c2.canonicalize_build_ir(
            build_spec,
            [
                {
                    "x": 0,
                    "y": 0,
                    "z": 0,
                    "block_state": {"name": "minecraft:stone_bricks", "properties": {}},
                }
            ],
            producer="construction-c9-mcp",
            producer_version="c9-mcp-v1",
        )
        self.assertEqual(facade.build_validate(build_ir), {"valid": True, "errors": []})

        invalid = copy.deepcopy(build_ir)
        invalid["target"]["minecraft_version"] = "1.20.1"
        expected_errors = c2.validate_build_ir(invalid)
        self.assertTrue(expected_errors)
        self.assertEqual(
            facade.build_validate(invalid),
            {"valid": False, "errors": expected_errors},
        )


class C9BuildEditContractTests(unittest.TestCase):
    def _fixture(self):
        facade_module = importlib.import_module("construction.mcp.facade")
        artifacts = importlib.import_module("construction.mcp.artifacts")
        errors = importlib.import_module("construction.mcp.errors")
        c2 = _load_module(ROOT / "construction" / "core" / "build_ir.py", "construction_c2_for_c9_edit")
        fixtures = _load_module(
            ROOT / "construction" / "tests" / "test_c5_modded_palette.py",
            "construction_c5_fixtures_for_c9_edit",
        )
        facade = facade_module.ConstructionFacade(artifacts.ArtifactStore())
        build_spec = fixtures.build_spec()
        placements = [
            {
                "x": 0,
                "y": 0,
                "z": 0,
                "block_state": {"name": "minecraft:stone_bricks", "properties": {}},
            },
            {
                "x": 1,
                "y": 0,
                "z": 0,
                "block_state": {"name": "minecraft:oak_log", "properties": {"axis": "y"}},
            },
        ]
        build_ir = c2.canonicalize_build_ir(
            build_spec,
            placements,
            producer="construction-c9-mcp",
            producer_version="c9-mcp-v1",
        )
        return facade, errors, c2, build_spec, build_ir

    def test_build_edit_add_replace_remove(self) -> None:
        facade, _errors, c2, build_spec, build_ir = self._fixture()
        original_spec = copy.deepcopy(build_spec)
        original_ir = copy.deepcopy(build_ir)
        operations = [
            {
                "op": "set_block",
                "x": 0,
                "y": 0,
                "z": 0,
                "block_state": {"name": "minecraft:oak_log", "properties": {"axis": "x"}},
            },
            {
                "op": "set_block",
                "x": 2,
                "y": 0,
                "z": 0,
                "block_state": {"name": "minecraft:stone", "properties": {}},
            },
            {"op": "remove_block", "x": 1, "y": 0, "z": 0},
        ]

        edited = facade.build_edit(build_spec, build_ir, operations)
        expected = c2.canonicalize_build_ir(
            build_spec,
            [
                {
                    "x": 0,
                    "y": 0,
                    "z": 0,
                    "block_state": {"name": "minecraft:oak_log", "properties": {"axis": "x"}},
                },
                {
                    "x": 2,
                    "y": 0,
                    "z": 0,
                    "block_state": {"name": "minecraft:stone", "properties": {}},
                },
            ],
            producer="construction-c9-edit",
            producer_version="c9-mcp-v1",
        )
        self.assertEqual(edited, expected)
        self.assertEqual(c2.validate_build_ir(edited), [])
        self.assertEqual(edited["metadata"]["producer"], "construction-c9-edit")
        self.assertEqual(edited["metadata"]["producer_version"], "c9-mcp-v1")
        self.assertEqual(edited["metadata"]["build_spec_sha256"], c2.build_spec_fingerprint(build_spec))
        self.assertEqual(build_spec, original_spec)
        self.assertEqual(build_ir, original_ir)

    def test_build_edit_rejects_duplicate_touch_absent_remove_and_bounds(self) -> None:
        facade, errors, _c2, build_spec, build_ir = self._fixture()
        cases = {
            "duplicate_touch": [
                {
                    "op": "set_block",
                    "x": 0,
                    "y": 0,
                    "z": 0,
                    "block_state": {"name": "minecraft:stone", "properties": {}},
                },
                {"op": "remove_block", "x": 0, "y": 0, "z": 0},
            ],
            "absent_remove": [{"op": "remove_block", "x": 8, "y": 8, "z": 8}],
            "out_of_bounds": [
                {
                    "op": "set_block",
                    "x": 9,
                    "y": 0,
                    "z": 0,
                    "block_state": {"name": "minecraft:stone", "properties": {}},
                }
            ],
            "empty_operations": [],
            "malformed_operation": [{"op": "remove_block", "x": 0, "y": 0, "z": 0, "extra": True}],
            "explicit_air": [
                {
                    "op": "set_block",
                    "x": 2,
                    "y": 0,
                    "z": 0,
                    "block_state": {"name": "minecraft:air", "properties": {}},
                }
            ],
            "block_entity_payload": [
                {
                    "op": "set_block",
                    "x": 2,
                    "y": 0,
                    "z": 0,
                    "block_state": {"name": "minecraft:stone", "properties": {}},
                    "block_entity": {},
                }
            ],
        }
        for label, operations in cases.items():
            with self.subTest(label=label):
                before = copy.deepcopy(build_ir)
                with self.assertRaises(errors.C9Error) as rejected:
                    facade.build_edit(build_spec, build_ir, operations)
                self.assertEqual(rejected.exception.code, "INVALID_INPUT")
                self.assertIsNone(rejected.exception.authority)
                self.assertEqual(build_ir, before)

    def test_build_edit_requires_matching_build_spec_fingerprint(self) -> None:
        facade, errors, c2, build_spec, build_ir = self._fixture()
        mismatched_spec = copy.deepcopy(build_spec)
        mismatched_spec["identity"]["name"] = "different-build"
        self.assertNotEqual(
            c2.build_spec_fingerprint(mismatched_spec),
            build_ir["metadata"]["build_spec_sha256"],
        )
        with self.assertRaises(errors.C9Error) as mismatch:
            facade.build_edit(
                mismatched_spec,
                build_ir,
                [{"op": "remove_block", "x": 1, "y": 0, "z": 0}],
            )
        self.assertEqual(mismatch.exception.code, "AUTHORITY_REJECTED")
        self.assertEqual(mismatch.exception.authority, "C2")

        invalid_ir = copy.deepcopy(build_ir)
        invalid_ir["target"]["minecraft_version"] = "1.20.1"
        direct_errors = c2.validate_build_ir(invalid_ir)
        self.assertTrue(direct_errors)
        with self.assertRaises(errors.C9Error) as invalid:
            facade.build_edit(
                build_spec,
                invalid_ir,
                [{"op": "remove_block", "x": 1, "y": 0, "z": 0}],
            )
        self.assertEqual(invalid.exception.code, "AUTHORITY_REJECTED")
        self.assertEqual(invalid.exception.authority, "C2")
        self.assertEqual(invalid.exception.details, direct_errors)


class C9QaPreviewContractTests(unittest.TestCase):
    def _fixture(self):
        facade_module = importlib.import_module("construction.mcp.facade")
        artifacts = importlib.import_module("construction.mcp.artifacts")
        errors = importlib.import_module("construction.mcp.errors")
        c2 = _load_module(
            ROOT / "construction" / "core" / "build_ir.py",
            "construction_c2_for_c9_task6",
        )
        c7 = _load_module(
            ROOT / "construction" / "core" / "structural_qa.py",
            "construction_c7_for_c9_task6",
        )
        renderer = _load_module(
            ROOT / "construction" / "qa" / "preview_renderer.py",
            "construction_c8_renderer_for_c9_task6",
        )
        fixtures = _load_module(
            ROOT / "construction" / "tests" / "test_c8_visual_qa.py",
            "construction_c8_fixtures_for_c9_task6",
        )
        store = artifacts.ArtifactStore()
        facade = facade_module.ConstructionFacade(store)
        build_spec = fixtures.make_build_spec(
            size=(3, 3, 3),
            loader="none",
            allow_modded=False,
            require_determinism=True,
            seed=906,
        )
        placements = [
            fixtures.placement(0, 0, 0, "minecraft:stone_bricks"),
            fixtures.placement(1, 0, 0, "minecraft:oak_log", {"axis": "y"}),
            fixtures.placement(1, 1, 0, "minecraft:oak_log", {"axis": "y"}),
            fixtures.placement(2, 0, 1, "minecraft:stone"),
        ]
        build_ir = c2.canonicalize_build_ir(
            build_spec,
            placements,
            producer="construction-c9-task6-test",
            producer_version="1",
        )
        return facade_module, facade, store, errors, c2, c7, renderer, build_spec, build_ir

    def test_qa_structural_matches_c7(self) -> None:
        _facade_module, facade, _store, errors, _c2, c7, _renderer, build_spec, build_ir = self._fixture()
        expected = c7.run_structural_qa(build_spec, build_ir, None)
        self.assertEqual(facade.qa_structural(build_spec, build_ir, None), expected)

        invalid_ir = copy.deepcopy(build_ir)
        invalid_ir["target"]["minecraft_version"] = "1.20.1"
        with self.assertRaises(c7.StructuralQAError) as direct:
            c7.run_structural_qa(build_spec, invalid_ir, None)
        with self.assertRaises(errors.C9Error) as wrapped:
            facade.qa_structural(build_spec, invalid_ir, None)
        self.assertEqual(wrapped.exception.code, "AUTHORITY_REJECTED")
        self.assertEqual(wrapped.exception.authority, "C7")
        self.assertEqual(wrapped.exception.details, [str(direct.exception)])

    def test_preview_render_matches_c8_and_is_deterministic(self) -> None:
        _facade_module, facade, store, errors, c2, _c7, renderer, _build_spec, build_ir = self._fixture()
        direct = renderer.render_canonical_views(build_ir)
        self.assertEqual(tuple(direct), tuple(renderer.VIEW_IDS))

        first = facade.preview_render(build_ir)
        second = facade.preview_render(build_ir)
        self.assertEqual(first, second)
        self.assertEqual(
            set(first),
            {"renderer_version", "build_ir_sha256", "bundle_uri", "views"},
        )
        self.assertEqual(first["renderer_version"], renderer.RENDERER_VERSION)
        self.assertEqual(first["build_ir_sha256"], c2.fingerprint_build_ir(build_ir))
        self.assertEqual(
            [item["id"] for item in first["views"]],
            list(renderer.VIEW_IDS),
        )

        for descriptor in first["views"]:
            self.assertEqual(
                set(descriptor),
                {"id", "uri", "media_type", "sha256", "byte_length"},
            )
            view_id = descriptor["id"]
            record = store.get(descriptor["uri"])
            self.assertEqual(record.kind, "preview_svg")
            self.assertEqual(record.media_type, "image/svg+xml")
            self.assertEqual(record.data, direct[view_id])
            self.assertEqual(record.sha256, hashlib.sha256(direct[view_id]).hexdigest())
            self.assertEqual(record.byte_length, len(direct[view_id]))
            self.assertEqual(descriptor["media_type"], record.media_type)
            self.assertEqual(descriptor["sha256"], record.sha256)
            self.assertEqual(descriptor["byte_length"], record.byte_length)

        invalid_ir = copy.deepcopy(build_ir)
        invalid_ir["target"]["minecraft_version"] = "1.20.1"
        with self.assertRaises(renderer.PreviewRenderError) as direct_error:
            renderer.render_canonical_views(invalid_ir)
        with self.assertRaises(errors.C9Error) as wrapped:
            facade.preview_render(invalid_ir)
        self.assertEqual(wrapped.exception.code, "AUTHORITY_REJECTED")
        self.assertEqual(wrapped.exception.authority, "C8")
        self.assertEqual(wrapped.exception.details, [str(direct_error.exception)])

    def test_preview_bundle_manifest_is_canonical_and_bound(self) -> None:
        import json

        _facade_module, facade, store, _errors, c2, _c7, renderer, _build_spec, build_ir = self._fixture()
        result = facade.preview_render(build_ir)
        build_ir_sha256 = c2.fingerprint_build_ir(build_ir)
        expected_views = [
            {
                "id": item["id"],
                "uri": item["uri"],
                "media_type": item["media_type"],
                "sha256": item["sha256"],
                "byte_length": item["byte_length"],
            }
            for item in result["views"]
        ]
        expected_manifest = {
            "schema_version": 1,
            "renderer_version": renderer.RENDERER_VERSION,
            "build_ir_sha256": build_ir_sha256,
            "views": expected_views,
        }
        expected_bytes = (
            json.dumps(
                expected_manifest,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            )
            + "\n"
         ).encode("utf-8")

        bundle = store.get(result["bundle_uri"])
        self.assertEqual(bundle.kind, "preview_bundle")
        self.assertEqual(bundle.media_type, "application/json")
        self.assertEqual(bundle.data, expected_bytes)
        self.assertTrue(bundle.data.endswith(b"\n"))
        self.assertFalse(bundle.data.endswith(b"\n\n"))
        self.assertEqual(json.loads(bundle.data), expected_manifest)
        self.assertEqual(result["renderer_version"], expected_manifest["renderer_version"])
        self.assertEqual(result["build_ir_sha256"], expected_manifest["build_ir_sha256"])

        repeated = facade.preview_render(build_ir)
        self.assertEqual(repeated["bundle_uri"], result["bundle_uri"])
        self.assertEqual(store.get(repeated["bundle_uri"]).data, expected_bytes)


if __name__ == "__main__":
    unittest.main()
