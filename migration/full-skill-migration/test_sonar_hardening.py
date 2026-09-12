#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import inspect
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MIGRATION = ROOT / "migration/full-skill-migration"
FULL_SKILL_WORKFLOW = ROOT / ".github/workflows/factory-full-skill-migration-validation.yml"
FULL_SKILL_MATERIALIZER = ROOT / ".github/workflows/factory-full-skill-materialize.yml"
FULL_SKILL_MANIFEST = ROOT / "migration/provenance/FULL-SKILL-MIGRATION-MANIFEST.json"
CONSTRUCTION_REGISTRY = ROOT / "construction/upstream/registry.json"
GITMODULES = ROOT / ".gitmodules"
SONAR_PROPERTIES = ROOT / ".sonarcloud.properties"
GENERATED_BUNDLE = "art/tooling/blockbench/asset-toolkit/asset_toolkit.js"
SOURCE_EXACT_VERIFY_PROJECT = "skills/library/minecraft-neoforge-engineering/scripts/verify_project.py"
VENDORED_JS_YAML = "skills/library/minecraft-ci-release/scripts/vendor/js-yaml.min.cjs"
IMMUTABLE_SNAPSHOT_ROOT = "construction/upstream/snapshots"
ENGINE_REFERENCE_ROOT = "construction/upstream/references"
NON_AUTHORITATIVE_CLASSIFICATIONS = {"REFERENCE_ONLY", "SUPERSEDED"}
SONAR_EXECUTABLE_SUFFIXES = {".py", ".js", ".mjs", ".cjs", ".sh"}
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
    def test_git_blob_sha_uses_git_plumbing_without_direct_sha1(self) -> None:
        script = MIGRATION / "validate.py"
        source = script.read_text(encoding="utf-8")
        self.assertNotIn("hashlib.sha1", source)
        self.assertNotIn("hashlib.new(\"sha1\"", source)

        module = load_module("full_skill_validate", script)
        self.assertEqual(
            module.git_blob_sha(b"payload"),
            "47d05ff6403c8e6c3cf635ea6eb9263738432773",
            "Git plumbing must preserve the canonical Git blob object id",
        )

    def test_check_whitespace_uses_fixed_parent_boundary_and_fixed_diff_argv(self) -> None:
        module = load_module("full_skill_whitespace", MIGRATION / "check_whitespace.py")
        resolver = getattr(module, "resolve_git_base", None)
        self.assertTrue(callable(resolver), "check_whitespace.py must verify its fixed Git base")
        self.assertEqual(tuple(inspect.signature(resolver).parameters), ())
        self.assertEqual(tuple(inspect.signature(module.git_changed_paths).parameters), ())
        self.assertEqual(tuple(inspect.signature(module.run_whitespace_check).parameters), ("preserved_paths",))

        run_source = inspect.getsource(module.run_whitespace_check)
        self.assertIn('["git", "diff", "--check", FIXED_BASE_REF, "--"]', run_source)
        self.assertNotIn("*paths", run_source)

        workflow = FULL_SKILL_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("run: python migration/full-skill-migration/check_whitespace.py\n", workflow)
        self.assertNotIn("check_whitespace.py --base", workflow)

    def test_source_exact_whitespace_diagnostics_are_filtered_after_fixed_diff(self) -> None:
        module = load_module("full_skill_whitespace_filter", MIGRATION / "check_whitespace.py")
        filter_diagnostics = getattr(module, "filter_whitespace_diagnostics", None)
        self.assertTrue(callable(filter_diagnostics), "check_whitespace.py must filter fixed-diff diagnostics in Python")

        output = (
            "skills/library/legacy/SKILL.md:2: trailing whitespace.\n"
            "+legacy payload   \n"
            "engineering/tooling/example.py:7: trailing whitespace.\n"
            "+bad   \n"
        )
        filtered = filter_diagnostics(output, {"skills/library/legacy/SKILL.md"})
        self.assertNotIn("skills/library/legacy/SKILL.md", filtered)
        self.assertNotIn("+legacy payload", filtered)
        self.assertIn("engineering/tooling/example.py:7: trailing whitespace.", filtered)
        self.assertIn("+bad   ", filtered)

        preserved_only = (
            "skills/library/legacy/SKILL.md:2: trailing whitespace.\n"
            "+legacy payload   \n"
        )
        self.assertEqual(filter_diagnostics(preserved_only, {"skills/library/legacy/SKILL.md"}), "")

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

    def test_m5_does_not_expose_factory_root_cli_override(self) -> None:
        script = MIGRATION / "m5_finalize.py"
        result = subprocess.run(
            [sys.executable, str(script), "--help"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("--factory-root", result.stdout)
        materializer = FULL_SKILL_MATERIALIZER.read_text(encoding="utf-8")
        self.assertNotIn("m5_finalize.py --factory-root", materializer)

    def test_sonar_scope_excludes_only_known_non_authoritative_code(self) -> None:
        self.assertTrue(SONAR_PROPERTIES.is_file(), ".sonarcloud.properties must document automatic-analysis scope")
        properties = {}
        for raw in SONAR_PROPERTIES.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            properties[key.strip()] = [item.strip() for item in value.split(",") if item.strip()]

        manifest = json.loads(FULL_SKILL_MANIFEST.read_text(encoding="utf-8"))
        historical_executable_exclusions = {
            entry["destination"]
            for entry in manifest["entries"]
            if entry["classification"] in NON_AUTHORITATIVE_CLASSIFICATIONS
            and entry["materialization_mode"] == "SOURCE_EXACT"
            and entry["destination"].startswith("migration/provenance/historical-skills/")
            and Path(entry["destination"]).suffix in SONAR_EXECUTABLE_SUFFIXES
        }
        self.assertTrue(historical_executable_exclusions, "manifest must expose preserved non-authoritative executable provenance")

        construction_registry = json.loads(CONSTRUCTION_REGISTRY.read_text(encoding="utf-8"))
        gitmodules_text = GITMODULES.read_text(encoding="utf-8")
        construction_gitlink_roots = {
            "IMMUTABLE_SNAPSHOT": IMMUTABLE_SNAPSHOT_ROOT,
            "ENGINE_REFERENCE": ENGINE_REFERENCE_ROOT,
        }
        immutable_gitlink_exclusions = set()
        for source in construction_registry["sources"]:
            root = construction_gitlink_roots.get(source.get("integration_policy"))
            if root is None:
                continue
            candidate = f"{root}/{source['id']}"
            if f"\tpath = {candidate}" in gitmodules_text:
                immutable_gitlink_exclusions.add(candidate)

        self.assertIn(
            "construction/upstream/snapshots/schematica",
            immutable_gitlink_exclusions,
            "Schematica immutable snapshot must remain a registered gitlink",
        )
        self.assertIn(
            "construction/upstream/references/minebench",
            immutable_gitlink_exclusions,
            "MineBench immutable engine reference must remain a registered gitlink",
        )

        active_vendor = next(entry for entry in manifest["entries"] if entry["destination"] == VENDORED_JS_YAML)
        historical_vendor = next(
            entry
            for entry in manifest["entries"]
            if entry["destination"] == "migration/provenance/historical-skills/library/minecraft-plugin-dev/scripts/vendor/js-yaml.min.cjs"
        )
        self.assertEqual(active_vendor["materialization_mode"], "SOURCE_EXACT")
        self.assertEqual(active_vendor["source_blob_sha"], historical_vendor["source_blob_sha"], "vendored js-yaml copies must remain byte-identical provenance")

        expected_exclusions = {
            GENERATED_BUNDLE,
            SOURCE_EXACT_VERIFY_PROJECT,
            VENDORED_JS_YAML,
            *historical_executable_exclusions,
            *immutable_gitlink_exclusions,
        }
        exclusions = set(properties.get("sonar.exclusions", []))
        self.assertEqual(exclusions, expected_exclusions)
        self.assertTrue(all("*" not in path for path in exclusions), "automatic-analysis exclusions must be exact paths")
        for path in exclusions - immutable_gitlink_exclusions:
            self.assertTrue((ROOT / path).is_file(), f"Sonar exclusion must resolve to a real file: {path}")

        canonical_authorities = {
            "migration/full-skill-migration/validate.py",
            "migration/full-skill-migration/check_whitespace.py",
            "skills/scripts/validate_skill_repository.py",
            "art/tooling/blockbench/asset-toolkit/core/validator/validator.js",
        }
        self.assertTrue(exclusions.isdisjoint(canonical_authorities), "Factory-authored canonical authorities must remain analyzed")

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
