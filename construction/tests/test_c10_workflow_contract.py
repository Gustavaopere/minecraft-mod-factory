from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "factory-construction-c10-external-providers.yml"

CHECKOUT_PIN = "actions/checkout@11d5960a326750d5838078e36cf38b85af677262"
SETUP_PYTHON_PIN = "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065"
SETUP_JAVA_PIN = "actions/setup-java@cf277c60eb25467037889841efdb72551f06f6c3"


class ConstructionC10WorkflowContractTest(unittest.TestCase):
    def workflow_text(self) -> str:
        if not WORKFLOW.is_file():
            self.skipTest("C10 workflow does not exist yet")
        return WORKFLOW.read_text(encoding="utf-8")

    def test_required_workflow_exists(self):
        self.assertTrue(
            WORKFLOW.is_file(),
            ".github/workflows/factory-construction-c10-external-providers.yml is required",
        )

    def test_workflow_has_fail_closed_offline_boundary(self):
        text = self.workflow_text()
        self.assertIn("name: Factory Construction C10 External Providers", text)
        self.assertIn("permissions:\n  contents: read", text)
        self.assertIn("runs-on: ubuntu-24.04", text)
        self.assertIn("python-version: '3.11'", text)
        self.assertIn("java-version: '21'", text)
        self.assertNotIn("curl ", text)
        self.assertNotIn("wget ", text)
        self.assertNotIn("secrets.", text)

    def test_workflow_uses_repository_pinned_actions(self):
        text = self.workflow_text()
        self.assertIn(CHECKOUT_PIN, text)
        self.assertIn(SETUP_PYTHON_PIN, text)
        self.assertIn(SETUP_JAVA_PIN, text)
        self.assertNotIn("actions/checkout@v", text)
        self.assertNotIn("actions/setup-python@v", text)
        self.assertNotIn("actions/setup-java@v", text)

    def test_workflow_runs_c10_and_inherited_authority_regressions(self):
        text = self.workflow_text()
        required_fragments = [
            "engineering/tests/test_i2_modlist_catalog.py",
            "engineering/tests/test_i2_security_review.py",
            "construction/tests/test_c10_*.py",
            "construction/scripts/validate_c10.py",
            "construction/tests/test_c9_agent_mcp.py",
            "construction/tests/test_c9_mcp_stdio.py",
            "construction/tests/test_c8_visual_qa.py",
            "construction/tests/test_c8_palette_resolution_contract.py",
            "construction/tests/test_c7_architecture_qa.py",
            "construction/tests/test_c7_registry_authority.py",
            "construction/tests/test_c6_sponge_v3.py",
            "construction/tests/test_c5_modded_palette.py",
            "construction/tests/test_c4_modpack_registry.py",
            "construction/tests/test_c4_runtime_registry_probe.py",
            "construction/scripts/prepare_neoforge_registry_probe.py",
            "./gradlew test build --no-daemon",
            "construction/tests/test_c3_vanilla_golden.py",
            "construction/tests/test_c2_build_ir.py",
            "construction/tests/test_c0_foundation.py",
            "construction/scripts/validate_c0.py",
            "git diff --check",
        ]
        for fragment in required_fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, text)

        positions = [text.index(fragment) for fragment in required_fragments]
        self.assertEqual(sorted(positions), positions)

    def test_pull_request_paths_cover_c10_and_consumed_authorities(self):
        text = self.workflow_text()
        required_paths = [
            ".github/workflows/factory-construction-c10-external-providers.yml",
            "engineering/tooling/import-physical-modlist.py",
            "engineering/tests/test_i2_modlist_catalog.py",
            "engineering/tests/test_i2_security_review.py",
            "construction/providers/**",
            "construction/schemas/**",
            "construction/tests/test_c10_*.py",
            "construction/fixtures/c10/**",
            "construction/upstream/registry.json",
            "construction/upstream/harness/c9-mcp-lock.txt",
            "construction/core/build_ir.py",
            "construction/core/modpack_registry.py",
            "construction/core/modded_palette.py",
            "construction/core/sponge_v3.py",
            "construction/core/structural_qa.py",
            "construction/core/visual_qa.py",
            "construction/qa/**",
            "construction/mcp/**",
            "construction/runtime/neoforge-registry-probe/**",
            "construction/scripts/prepare_neoforge_registry_probe.py",
            "construction/scripts/validate_c0.py",
            "construction/scripts/validate_c10.py",
            "construction/tests/test_c9_agent_mcp.py",
            "construction/tests/test_c9_mcp_stdio.py",
            "construction/tests/test_c8_visual_qa.py",
            "construction/tests/test_c8_palette_resolution_contract.py",
            "construction/tests/test_c7_architecture_qa.py",
            "construction/tests/test_c7_registry_authority.py",
            "construction/tests/test_c6_sponge_v3.py",
            "construction/tests/test_c5_modded_palette.py",
            "construction/tests/test_c4_modpack_registry.py",
            "construction/tests/test_c4_runtime_registry_probe.py",
            "construction/tests/test_c3_vanilla_golden.py",
            "construction/tests/test_c2_build_ir.py",
            "construction/tests/test_c0_foundation.py",
            "docs/superpowers/specs/2026-09-12-construction-c10-external-providers-design.md",
            "docs/superpowers/plans/2026-09-12-construction-c10-external-providers.md",
            "construction/README.md",
            "construction/docs/ARCHITECTURE.md",
            "construction/STATUS.md",
        ]
        for path in required_paths:
            with self.subTest(path=path):
                self.assertIn(f"- '{path}'", text)

    def test_checkout_preserves_recursive_submodules_and_hashed_locks(self):
        text = self.workflow_text()
        self.assertIn("submodules: recursive", text)
        self.assertIn("--require-hashes --no-deps -r construction/upstream/harness/schematica-test-lock.txt", text)
        self.assertIn("--require-hashes --no-deps -r construction/upstream/harness/c9-mcp-lock.txt", text)
        self.assertIn('assert version("mcp") == "2.2.0"', text)


if __name__ == "__main__":
    unittest.main()
