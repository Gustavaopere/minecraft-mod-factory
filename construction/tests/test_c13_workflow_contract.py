from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/factory-construction-c13-skill-router.yml"
BLOCKER = "SUPER_HYPER_URGENT_FINAL_CONSTRUCTION_PHYSICAL_ACCEPTANCE"
CAPTURE_STATE = "construction/fixtures/complex-modded-golden/capture-state.json"
C12_FINAL_REPORT = "construction/fixtures/complex-modded-golden/c12-runtime-acceptance-report.json"


class C13WorkflowContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = WORKFLOW.read_text(encoding="utf-8")

    def final_job(self) -> str:
        marker = "  c13-final-acceptance:"
        self.assertIn(marker, self.text)
        return self.text[self.text.index(marker):]

    def test_workflow_splits_preflight_from_final_acceptance(self) -> None:
        self.assertIn("  c13-router-preflight:", self.text)
        self.assertIn("  c13-final-acceptance:", self.text)
        self.assertIn("needs: c13-router-preflight", self.text)

    def test_preflight_runs_required_cross_boundary_regressions(self) -> None:
        required = (
            "construction/tests/test_c13_skill_router_integration.py",
            "construction/tests/test_c13_workflow_contract.py",
            "skills/scripts/validate_skill_repository.py",
            "construction/tests/test_c9_agent_mcp.py",
            "construction/tests/test_c9_mcp_stdio.py",
            "construction/tests/test_c10_provider_profiles.py",
            "construction/tests/test_c10_handoff_request.py",
            "construction/tests/test_c10_handoff_receipt.py",
            "construction/tests/test_c10_security.py",
            "construction/tests/test_c10_workflow_contract.py",
            "construction/tests/test_c12_runtime_acceptance.py",
            "construction/tests/test_c12_runtime_acceptance_security.py",
            "construction/tests/test_c12_workflow_contract.py",
            "construction/tests/test_construction_final_physical_acceptance_gate.py",
            "migration/full-skill-migration/test_sonar_ci_contract.py",
            "git diff --check",
        )
        for token in required:
            with self.subTest(token=token):
                self.assertIn(token, self.text)

    def test_final_acceptance_checks_exact_blocker_before_c12_report(self) -> None:
        final_job = self.final_job()
        guard = (
            'if state.get("status") == blocker and '
            'state.get("blocks_c13_final_acceptance") is True:'
        )
        self.assertIn(f'blocker = "{BLOCKER}"', final_job)
        self.assertIn(CAPTURE_STATE, final_job)
        self.assertIn(guard, final_job)
        self.assertIn(f'C13_FINAL_ACCEPTANCE_BLOCKED: {BLOCKER}', final_job)
        self.assertIn(C12_FINAL_REPORT, final_job)
        self.assertLess(final_job.index(guard), final_job.index(C12_FINAL_REPORT))

    def test_final_acceptance_requires_physical_c12_pass(self) -> None:
        final_job = self.final_job()
        self.assertIn("validate_runtime_acceptance_report", final_job)
        self.assertIn('report.get("mode") != "PHYSICAL_ACCEPTANCE"', final_job)
        self.assertIn('report.get("overall_acceptance") != "PASS"', final_job)

    def test_final_acceptance_requires_accepted_c11_c12_c13_routes(self) -> None:
        final_job = self.final_job()
        self.assertIn("load_capability_index", final_job)
        self.assertIn("validate_capability_index", final_job)
        for intent in (
            "construction.complex_modded_golden",
            "construction.runtime_acceptance",
            "construction.skill_router_integration",
        ):
            with self.subTest(intent=intent):
                self.assertIn(intent, final_job)
        self.assertIn('route.get("readiness") != "AVAILABLE"', final_job)
        self.assertIn('route.get("acceptance") != "ACCEPTED"', final_job)


if __name__ == "__main__":
    unittest.main()
