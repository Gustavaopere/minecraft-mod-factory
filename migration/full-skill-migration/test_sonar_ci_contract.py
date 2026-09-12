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
SONAR_PROJECT_VERSION = "ci-baseline-v1"
TEST_PATTERNS = {
    "**/tests/**/*",
    "**/test_*.py",
    "**/*_test.py",
    "**/src/test/**/*",
    "**/*.test.js",
    "**/*.test.mjs",
    "**/*.test.cjs",
    "**/*.test.ts",
    "**/*.spec.js",
    "**/*.spec.mjs",
    "**/*.spec.cjs",
    "**/*.spec.ts",
}


def parse_properties(path: Path) -> dict[str, str]:
    properties: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        properties[key.strip()] = value.strip()
    return properties


def parse_csv(value: str | None) -> set[str]:
    return {item.strip() for item in (value or "").split(",") if item.strip()}


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
        self.assertEqual(
            parse_csv(ci.get("sonar.exclusions")) - TEST_PATTERNS,
            parse_csv(automatic.get("sonar.exclusions")),
            "CI migration must preserve every canonical non-test source exclusion",
        )

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

    def test_ci_analysis_classifies_test_code_outside_main_coverage(self) -> None:
        ci = parse_properties(CI_PROPERTIES)
        automatic = parse_properties(AUTO_PROPERTIES)

        self.assertEqual(ci.get("sonar.tests"), ".", "mixed-root Factory analysis must explicitly define the test root")
        self.assertEqual(
            parse_csv(ci.get("sonar.test.inclusions")),
            TEST_PATTERNS,
            "only canonical test naming/layout patterns may enter Sonar test scope",
        )
        self.assertEqual(
            parse_csv(ci.get("sonar.exclusions")),
            parse_csv(automatic.get("sonar.exclusions")) | TEST_PATTERNS,
            "test files must leave source scope while canonical non-test exclusions remain unchanged",
        )
        self.assertNotIn(
            "sonar.coverage.exclusions",
            ci,
            "test code must be classified as tests instead of hiding source files from coverage",
        )

    def test_previous_version_new_code_uses_stable_ci_baseline_version(self) -> None:
        ci = parse_properties(CI_PROPERTIES)
        self.assertEqual(
            ci.get("sonar.projectVersion"),
            SONAR_PROJECT_VERSION,
            "Previous version new-code mode requires an explicit stable project version after the CI migration baseline",
        )
        self.assertNotIn("${", ci["sonar.projectVersion"])
        self.assertNotIn("github", ci["sonar.projectVersion"].lower())


if __name__ == "__main__":
    unittest.main()
