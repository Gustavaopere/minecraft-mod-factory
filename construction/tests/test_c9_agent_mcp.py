from __future__ import annotations

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


if __name__ == "__main__":
    unittest.main()
