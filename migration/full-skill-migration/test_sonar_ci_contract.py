#!/usr/bin/env python3
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUTO_PROPERTIES = ROOT / ".sonarcloud.properties"
CI_PROPERTIES = ROOT / "sonar-project.properties"
SONAR_WORKFLOW = ROOT / ".github/workflows/factory-sonar-ci.yml"
SONAR_COVERAGE_LOCK = ROOT / "construction/upstream/harness/sonar-coverage-lock.txt"

CHECKOUT_SHA = "11d5960a326750d5838078e36cf38b85af677262"
SETUP_PYTHON_SHA = "a26af69be951a213d495a4c3e4e4022e16d87065"
SONAR_SCAN_SHA = "22918119ff8e1ca75a623e15c8296b6ea4fbe28f"
SONAR_PROJECT_VERSION = "ci-baseline-v1"
COVERAGE_LOCK_LINE = "coverage==7.16.0 --hash=sha256:7cae7715afa51dd7c9c42e6603bb46daf424c3449fdf06519cc658aa8d46e2e4"
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

    def test_ci_analysis_generates_and_imports_python_coverage_before_scan(self) -> None:
        self.assertTrue(
            SONAR_COVERAGE_LOCK.is_file(),
            "Sonar CI must install coverage from a dedicated hash-pinned lock",
        )
        lock_lines = [
            line.strip()
            for line in SONAR_COVERAGE_LOCK.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        self.assertEqual(lock_lines, [COVERAGE_LOCK_LINE])

        ci = parse_properties(CI_PROPERTIES)
        self.assertEqual(
            ci.get("sonar.python.coverage.reportPaths"),
            "coverage.xml",
            "Sonar CI must import the Cobertura XML generated by the C10 provider tests",
        )
        self.assertNotIn("sonar.coverage.exclusions", ci)

        workflow = SONAR_WORKFLOW.read_text(encoding="utf-8")
        install = (
            "python3 -m pip install --require-hashes --no-deps "
            "-r construction/upstream/harness/sonar-coverage-lock.txt"
        )
        coverage_run = (
            "python3 -m coverage run --branch --source=construction/providers,construction/scripts "
            "-m unittest discover -s construction/tests -p 'test_c10_*.py' -v"
        )
        coverage_xml = "python3 -m coverage xml -o coverage.xml"
        scanner = f"uses: SonarSource/sonarqube-scan-action@{SONAR_SCAN_SHA}"

        self.assertIn(f"uses: actions/setup-python@{SETUP_PYTHON_SHA}", workflow)
        self.assertIn("python-version: '3.11'", workflow)
        self.assertIn(install, workflow)
        self.assertIn(coverage_run, workflow)
        self.assertIn(coverage_xml, workflow)
        self.assertIn(scanner, workflow)
        self.assertLess(workflow.index(install), workflow.index(coverage_run))
        self.assertLess(workflow.index(coverage_run), workflow.index(coverage_xml))
        self.assertLess(workflow.index(coverage_xml), workflow.index(scanner))

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
