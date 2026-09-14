#!/usr/bin/env python3
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SONAR_WORKFLOW = ROOT / ".github/workflows/factory-sonar-ci.yml"
SONAR_SCAN_SHA = "22918119ff8e1ca75a623e15c8296b6ea4fbe28f"


class SonarCampaignTargetCoverageContractTest(unittest.TestCase):
    def test_campaign_target_migration_surfaces_are_covered_before_scan(self) -> None:
        workflow = SONAR_WORKFLOW.read_text(encoding="utf-8")
        scanner = f"uses: SonarSource/sonarqube-scan-action@{SONAR_SCAN_SHA}"
        required = (
            "engineering/tooling/resolve-neoforge-campaign-target.py",
            "engineering/tests/test_neoforge_campaign_target.py",
            "--include=engineering/tooling/resolve-neoforge-campaign-target.py",
            "engineering/tooling/scaffolder/scaffold_mod.py",
            "engineering/tests/test_i3_mod_scaffolder.py",
            "engineering/tests/test_i3_security_review.py",
            "--source=engineering/tooling/scaffolder",
            "engineering/tooling/test-harness/run_test_harness.py",
            "engineering/tests/test_i5_test_harness.py",
            "--source=engineering/tooling/test-harness",
            "engineering/tooling/validate-e1-s1-governance.py",
            "engineering/tests/test_e1_s1_governance.py",
            "--include=engineering/tooling/validate-e1-s1-governance.py",
        )
        self.assertIn(scanner, workflow)
        for token in required:
            with self.subTest(token=token):
                self.assertIn(token, workflow)
                self.assertLess(workflow.index(token), workflow.index(scanner))


if __name__ == "__main__":
    unittest.main()
