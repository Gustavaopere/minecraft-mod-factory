from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/factory-construction-c12-runtime-acceptance.yml"
BLOCKER = "SUPER_HYPER_URGENT_FINAL_CONSTRUCTION_PHYSICAL_ACCEPTANCE"
FINAL_REPORT = "construction/fixtures/complex-modded-golden/c12-runtime-acceptance-report.json"


class C12WorkflowContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = WORKFLOW.read_text(encoding="utf-8")

    def test_workflow_has_split_preflight_and_acceptance_jobs(self):
        self.assertIn("  c12-preflight:", self.text)
        self.assertIn("  c12-acceptance:", self.text)
        self.assertIn("needs: c12-preflight", self.text)

    def test_preflight_runs_c12_i5_final_gate_sonar_and_whitespace_regressions(self):
        required = (
            "construction/tests/test_c12_runtime_acceptance.py",
            "construction/tests/test_c12_runtime_acceptance_security.py",
            "construction/tests/test_c12_workflow_contract.py",
            "engineering/tests/test_i5_test_harness.py",
            "construction/tests/test_construction_final_physical_acceptance_gate.py",
            "migration/full-skill-migration/test_sonar_ci_contract.py",
            "git diff --check",
        )
        for token in required:
            with self.subTest(token=token):
                self.assertIn(token, self.text)

    def test_acceptance_checks_exact_blocker_before_final_report(self):
        blocker_guard = (
            'if state.get("status") == blocker and '
            'state.get("blocks_c12_acceptance") is True:'
        )
        self.assertIn(f'blocker = "{BLOCKER}"', self.text)
        self.assertIn(blocker_guard, self.text)
        self.assertIn(f'C12_ACCEPTANCE_BLOCKED: {BLOCKER}', self.text)
        self.assertIn(FINAL_REPORT, self.text)
        self.assertLess(self.text.index(blocker_guard), self.text.index(FINAL_REPORT))

    def test_acceptance_does_not_treat_preflight_as_final_acceptance(self):
        self.assertIn('report.get("mode") != "PHYSICAL_ACCEPTANCE"', self.text)
        self.assertIn('report.get("overall_acceptance") != "PASS"', self.text)


if __name__ == "__main__":
    unittest.main()
