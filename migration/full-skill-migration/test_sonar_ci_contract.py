#!/usr/bin/env python3
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUTO_PROPERTIES = ROOT / ".sonarcloud.properties"
CI_PROPERTIES = ROOT / "sonar-project.properties"
SONAR_WORKFLOW = ROOT / ".github/workflows/factory-sonar-ci.yml"

CHECKOUT_SHA = "11d5960a326750d5838078e36cf38b85af677262"
SONAR_SCAN_SHA = "22918119ff8e1ca75a623e15c8296b6ea4fbe28f"


def parse_properties(path: Path) -> dict[str, str]:
    properties: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        properties[key.strip()] = value.strip()
    return properties


class SonarCiContractTest(unittest.TestCase):
    def test_ci_analysis_is_pinned_fail_closed_and_scope_equivalent(self) -> None:
        self.assertTrue(CI_PROPERTIES.is_file(), "CI-based Sonar requires sonar-project.properties")
        self.assertTrue(SONAR_WORKFLOW.is_file(), "CI-based Sonar requires a dedicated GitHub Actions workflow")
        self.assertTrue(AUTO_PROPERTIES.is_file(), ".sonarcloud.properties remains the exact-scope compatibility manifest")

        ci = parse_properties(CI_PROPERTIES)
        automatic = parse_properties(AUTO_PROPERTIES)
        self.assertEqual(ci.get("sonar.projectKey"), "Gustavaopere_minecraft-mod-factory")
        self.assertEqual(ci.get("sonar.organization"), "gustavaopere")
        self.assertEqual(ci.get("sonar.sources"), ".")
        self.assertEqual(ci.get("sonar.qualitygate.wait"), "true")
        self.assertEqual(ci.get("sonar.qualitygate.timeout"), "600")
        self.assertEqual(ci.get("sonar.exclusions"), automatic.get("sonar.exclusions"))

        workflow = SONAR_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("push:", workflow)
        self.assertIn("pull_request:", workflow)
        self.assertNotIn("pull_request_target:", workflow)
        self.assertIn("permissions:\n  contents: read\n", workflow)
        self.assertIn(f"uses: actions/checkout@{CHECKOUT_SHA}", workflow)
        self.assertIn("fetch-depth: 0", workflow)
        self.assertIn("submodules: false", workflow)
        self.assertIn(f"uses: SonarSource/sonarqube-scan-action@{SONAR_SCAN_SHA}", workflow)
        self.assertNotIn("SonarSource/sonarqube-scan-action@v", workflow)
        self.assertIn("SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}", workflow)
        self.assertIn("github.event.pull_request.head.repo.full_name == github.repository", workflow)


if __name__ == "__main__":
    unittest.main()
