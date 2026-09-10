import importlib.util
import inspect
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HARNESS = ROOT / "engineering/tooling/test-harness/run_test_harness.py"
I1_VALIDATOR = ROOT / "engineering/tooling/validate-i1-foundation.py"
TEST_MANIFEST_SCHEMA = ROOT / "engineering/schemas/test-manifest.schema.json"
TEMPLATE_BUILD = ROOT / "engineering/templates/neoforge-mod/build.gradle.tmpl"
GOLDEN_BUILD = ROOT / "engineering/tests/golden/i3-golden-mod/build.gradle"

EXPECTED_COMMANDS = [
    "./gradlew --no-daemon test",
    "./gradlew --no-daemon runGameTestServer",
    "./gradlew --no-daemon runServer",
]
EXPECTED_SUITES = [
    ("unit", "unit", EXPECTED_COMMANDS[0]),
    ("gametest", "gametest", EXPECTED_COMMANDS[1]),
    ("dedicated_server", "dedicated_server", EXPECTED_COMMANDS[2]),
]


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def write_fake_project(root: Path) -> Path:
    root.mkdir(parents=True)
    (root / "gradle.properties").write_text(
        "\n".join(
            [
                "mod_id=i5_fixture",
                "minecraft_version=1.21.1",
                "neo_version=21.1.248",
                "java_version=21",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    server_run = root / "run" / "server"
    server_run.mkdir(parents=True)
    (server_run / "eula.txt").write_text("eula=true\n", encoding="utf-8")
    wrapper = root / "gradlew"
    wrapper.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
printf '%s\\n' "$*" >> .i5-invocations
case "$*" in
  "--no-daemon test")
    mkdir -p build/test-results/test build/reports/tests/test
    printf '<testsuite tests="1" failures="0"/>\\n' > build/test-results/test/TEST-i5.xml
    printf '<html>i5 unit report</html>\\n' > build/reports/tests/test/index.html
    ;;
  "--no-daemon runGameTestServer")
    if [[ -f .i5-fail-gametest ]]; then
      echo 'synthetic GameTest failure'
      exit 7
    fi
    echo 'synthetic GameTest PASS'
    ;;
  "--no-daemon runServer")
    echo 'Done (0.1s)! For help, type "help"'
    sleep 30
    ;;
  *)
    echo "unexpected Gradle invocation: $*" >&2
    exit 97
    ;;
esac
""",
        encoding="utf-8",
    )
    wrapper.chmod(wrapper.stat().st_mode | stat.S_IXUSR)
    (root / "private-source.txt").write_text("must not be collected\n", encoding="utf-8")
    private_build = root / "build" / "unrelated"
    private_build.mkdir(parents=True)
    (private_build / "private.txt").write_text("must not be collected\n", encoding="utf-8")
    return root


def run_harness_cli(project: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(HARNESS), "--project", str(project), *extra],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=15,
        check=False,
    )


class I5TestHarnessContractTest(unittest.TestCase):
    def require_harness(self):
        if not HARNESS.is_file():
            self.skipTest("production I5 test harness is intentionally absent during RED")
        return load_module(HARNESS, "i5_test_harness")

    def test_production_harness_entrypoint_exists(self):
        self.assertTrue(
            HARNESS.is_file(),
            "I5 RED: production harness engineering/tooling/test-harness/run_test_harness.py is missing",
        )

    def test_golden_scaffold_declares_canonical_gametest_and_datagen_runs(self):
        for path in (TEMPLATE_BUILD, GOLDEN_BUILD):
            text = path.read_text(encoding="utf-8")
            self.assertIn("gameTestServer", text, f"I5 RED: {path} must declare the canonical GameTest server run")
            self.assertRegex(text, r"(?m)^\s*data\s*\{", f"I5 RED: {path} must declare the canonical datagen run")

    def test_harness_public_api_has_no_arbitrary_command_parameter(self):
        module = self.require_harness()
        signature = inspect.signature(module.run_harness)
        self.assertEqual(["project_root"], list(signature.parameters))
        with tempfile.TemporaryDirectory() as tmp:
            project = write_fake_project(Path(tmp) / "project")
            result = run_harness_cli(project, "--command", "echo unsafe")
            self.assertNotEqual(0, result.returncode)
            self.assertFalse((project / ".i5-invocations").exists())

    def test_success_executes_exact_allowlisted_suites_and_writes_canonical_manifest(self):
        self.require_harness()
        with tempfile.TemporaryDirectory() as tmp:
            project = write_fake_project(Path(tmp) / "project")
            result = run_harness_cli(project)
            self.assertEqual(0, result.returncode, result.stdout)

            manifest_path = project / "build/i5-test-harness/test-manifest.json"
            self.assertTrue(manifest_path.is_file())
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual("PASS", manifest["overall_state"])
            self.assertEqual(
                EXPECTED_SUITES,
                [(suite["suite_id"], suite["type"], suite["command"]) for suite in manifest["suites"]],
            )
            self.assertTrue(all(suite["state"] == "PASS" for suite in manifest["suites"]))

            i1 = load_module(I1_VALIDATOR, "i5_i1_validator")
            schema = json.loads(TEST_MANIFEST_SCHEMA.read_text(encoding="utf-8"))
            self.assertEqual([], i1.validate_instance(schema, manifest))

            invocations = (project / ".i5-invocations").read_text(encoding="utf-8").splitlines()
            self.assertEqual([command.removeprefix("./gradlew ") for command in EXPECTED_COMMANDS], invocations)

    def test_dedicated_server_requires_explicit_eula_acceptance_before_any_gradle_run(self):
        self.require_harness()
        with tempfile.TemporaryDirectory() as tmp:
            project = write_fake_project(Path(tmp) / "project")
            (project / "run/server/eula.txt").unlink()

            result = run_harness_cli(project)

            self.assertEqual(2, result.returncode, result.stdout)
            self.assertIn("eula", result.stdout.lower())
            self.assertFalse((project / ".i5-invocations").exists())

    def test_failed_suite_is_reported_fail_closed_without_hiding_other_results(self):
        self.require_harness()
        with tempfile.TemporaryDirectory() as tmp:
            project = write_fake_project(Path(tmp) / "project")
            (project / ".i5-fail-gametest").write_text("fail\n", encoding="utf-8")
            result = run_harness_cli(project)
            self.assertNotEqual(0, result.returncode)

            manifest = json.loads(
                (project / "build/i5-test-harness/test-manifest.json").read_text(encoding="utf-8")
            )
            states = {suite["suite_id"]: suite["state"] for suite in manifest["suites"]}
            self.assertEqual("PASS", states["unit"])
            self.assertEqual("BLOCKED", states["gametest"])
            self.assertEqual("PASS", states["dedicated_server"])
            self.assertEqual("BLOCKED", manifest["overall_state"])

    def test_artifact_collection_is_bounded_to_standard_reports_and_suite_logs(self):
        self.require_harness()
        with tempfile.TemporaryDirectory() as tmp:
            project = write_fake_project(Path(tmp) / "project")
            result = run_harness_cli(project)
            self.assertEqual(0, result.returncode, result.stdout)

            artifact_root = project / "build/i5-test-harness/artifacts"
            expected = {
                "logs/unit.log",
                "logs/gametest.log",
                "logs/dedicated_server.log",
                "test-results/test/TEST-i5.xml",
                "reports/tests/test/index.html",
            }
            collected = {
                path.relative_to(artifact_root).as_posix()
                for path in artifact_root.rglob("*")
                if path.is_file()
            }
            self.assertEqual(expected, collected)
            self.assertNotIn("private-source.txt", collected)
            self.assertFalse(any("unrelated" in path for path in collected))

    def test_artifact_collection_rejects_report_symlinks(self):
        module = self.require_harness()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            project = write_fake_project(tmp_root / "project")
            source = project / "build/test-results/test"
            source.mkdir(parents=True, exist_ok=True)
            outside = tmp_root / "outside.xml"
            outside.write_text("external evidence must not be collected\n", encoding="utf-8")
            (source / "TEST-external.xml").symlink_to(outside)

            with self.assertRaises(module.HarnessError):
                module._collect_tree(
                    project,
                    Path("build/test-results/test"),
                    module.ARTIFACT_RELATIVE / "test-results/test",
                )

            self.assertFalse(
                (project / "build/i5-test-harness/artifacts/test-results/test/TEST-external.xml").exists()
            )

    def test_manifest_evidence_points_only_to_collected_files(self):
        self.require_harness()
        with tempfile.TemporaryDirectory() as tmp:
            project = write_fake_project(Path(tmp) / "project")
            result = run_harness_cli(project)
            self.assertEqual(0, result.returncode, result.stdout)
            manifest = json.loads(
                (project / "build/i5-test-harness/test-manifest.json").read_text(encoding="utf-8")
            )
            for suite in manifest["suites"]:
                self.assertTrue(suite["evidence"])
                for relative in suite["evidence"]:
                    evidence = project / relative
                    self.assertTrue(evidence.is_file(), (suite["suite_id"], relative))
                    self.assertTrue(
                        evidence.resolve().is_relative_to(
                            (project / "build/i5-test-harness/artifacts").resolve()
                        )
                    )

    def test_manifest_is_deterministic_for_identical_successful_runs(self):
        self.require_harness()
        with tempfile.TemporaryDirectory() as tmp:
            first = write_fake_project(Path(tmp) / "first")
            second = write_fake_project(Path(tmp) / "second")
            first_result = run_harness_cli(first)
            second_result = run_harness_cli(second)
            self.assertEqual(0, first_result.returncode, first_result.stdout)
            self.assertEqual(0, second_result.returncode, second_result.stdout)
            self.assertEqual(
                (first / "build/i5-test-harness/test-manifest.json").read_bytes(),
                (second / "build/i5-test-harness/test-manifest.json").read_bytes(),
            )


if __name__ == "__main__":
    unittest.main()
