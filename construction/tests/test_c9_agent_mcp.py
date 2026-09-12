from __future__ import annotations

import importlib.metadata
import importlib.util
import unittest
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
        spec = importlib.util.spec_from_file_location("construction_c4_for_c9_contract", path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
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


if __name__ == "__main__":
    unittest.main()
