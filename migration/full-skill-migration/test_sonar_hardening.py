#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
MIGRATION = ROOT / "migration/full-skill-migration"
FULL_SKILL_WORKFLOW = ROOT / ".github/workflows/factory-full-skill-migration-validation.yml"
SONAR_PROPERTIES = ROOT / ".sonarcloud.properties"
GENERATED_BUNDLE = "art/tooling/blockbench/asset-toolkit/asset_toolkit.js"
SOURCE_EXACT_VERIFY_PROJECT = "skills/library/minecraft-neoforge-engineering/scripts/verify_project.py"
PR4_ONE_SHOTS = (
    ROOT / ".github/workflows/factory-fix-pr4-green-command-once.yml",
    ROOT / ".github/workflows/factory-pr4-texture-compare-apply.yml",
    ROOT / ".github/workflows/factory-pr4-texture-compare-green-once.yml",
)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SonarHardeningContractTest(unittest.TestCase):
    def test_git_blob_sha_marks_sha1_as_non_security(self) -> None:
        module = load_module("full_skill_validate", MIGRATION / "validate.py")
        calls = []

        class FakeHash:
            def hexdigest(self) -> str:
                return "fake-git-blob-sha"

        def fake_sha1(data: bytes, **kwargs):
            calls.append((data, kwargs))
            return FakeHash()

        with mock.patch.object(module.hashlib, "sha1", side_effect=fake_sha1):
            self.assertEqual(module.git_blob_sha(b"payload"), "fake-git-blob-sha")

        self.assertEqual(len(calls), 1)
        self.assertIs(calls[0][1].get("usedforsecurity"), False)

    def test_check_whitespace_exposes_validated_git_base_resolver(self) -> None:
        module = load_module("full_skill_whitespace", MIGRATION / "check_whitespace.py")
        resolver = getattr(module, "resolve_git_base", None)
        self.assertTrue(callable(resolver), "check_whitespace.py must resolve and validate --base before git diff")

        for unsafe in ("-p", "--stat", "HEAD;echo-pwned", "HEAD\n--stat", "", " " * 4):
            with self.subTest(unsafe=unsafe):
                with self.assertRaises((ValueError, RuntimeError, subprocess.CalledProcessError)):
                    resolver(unsafe)

    def test_m5_rejects_external_factory_root_without_mutation(self) -> None:
        script = MIGRATION / "m5_finalize.py"
        with tempfile.TemporaryDirectory() as tmp:
            external_root = Path(tmp)
            sidecar = external_root / "art/tooling/blockbench/asset-toolkit/mcp-sidecar"
            sidecar.mkdir(parents=True)
            package = sidecar / "package.json"
            lock = sidecar / "package-lock.json"
            package.write_text(json.dumps({"name": "external-package"}) + "\n", encoding="utf-8")
            lock.write_text(json.dumps({"name": "external-package", "packages": {"": {"name": "external-package"}}}) + "\n", encoding="utf-8")
            before_package = package.read_bytes()
            before_lock = lock.read_bytes()

            result = subprocess.run(
                [sys.executable, str(script), "--factory-root", str(external_root)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0, "m5_finalize.py must reject write roots outside its canonical repository")
            self.assertEqual(package.read_bytes(), before_package)
            self.assertEqual(lock.read_bytes(), before_lock)

    def test_sonar_scope_excludes_only_known_non_authoritative_code(self) -> None:
        self.assertTrue(SONAR_PROPERTIES.is_file(), ".sonarcloud.properties must document automatic-analysis scope")
        properties = {}
        for raw in SONAR_PROPERTIES.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            properties[key.strip()] = [item.strip() for item in value.split(",") if item.strip()]

        exclusions = set(properties.get("sonar.exclusions", []))
        self.assertEqual(exclusions, {GENERATED_BUNDLE, SOURCE_EXACT_VERIFY_PROJECT})
        self.assertTrue(all("*" not in path for path in exclusions), "automatic-analysis exclusions must be exact paths")

    def test_active_mcp_install_disables_lifecycle_scripts(self) -> None:
        workflow = FULL_SKILL_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("run: npm ci --ignore-scripts", workflow)
        self.assertNotIn("run: npm ci\n", workflow)

    def test_consumed_pr4_one_shot_workflows_are_removed(self) -> None:
        for workflow in PR4_ONE_SHOTS:
            with self.subTest(workflow=workflow.name):
                self.assertFalse(workflow.exists(), f"consumed one-shot workflow must be removed: {workflow.name}")


if __name__ == "__main__":
    unittest.main()
