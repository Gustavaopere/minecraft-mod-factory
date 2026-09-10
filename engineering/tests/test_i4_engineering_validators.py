import importlib.util
import json
import shutil
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "engineering/tooling/validators/validate_mod_project.py"
GOLDEN = ROOT / "engineering/tests/golden/i3-golden-mod"
MOD_SPEC = ROOT / "engineering/tests/fixtures/i4-golden-mod-spec.json"
ASSET_HANDOFF = ROOT / "engineering/tests/fixtures/i4-golden-asset-handoff.json"


def load_validator():
    spec = importlib.util.spec_from_file_location("i4_validate_mod_project", VALIDATOR)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def copy_golden(target: Path) -> Path:
    shutil.copytree(GOLDEN, target)
    return target


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def make_jar(path: Path, include_common: bool = True) -> Path:
    with zipfile.ZipFile(path, "w") as jar:
        jar.writestr("META-INF/neoforge.mods.toml", 'modId="i3_golden_mod"\n')
        if include_common:
            jar.writestr("dev/example/i3golden/I3GoldenMod.class", b"synthetic-class")
        jar.writestr("dev/example/i3golden/client/I3GoldenModClient.class", b"synthetic-client-class")
    return path


def install_synthetic_datagen_wrapper(project: Path) -> None:
    wrapper = project / "gradlew"
    wrapper.write_text(
        """#!/usr/bin/env python3
import sys
from pathlib import Path

if sys.argv[1:] != ["runData", "--no-daemon"]:
    raise SystemExit(2)
if Path(".i4-trigger-drift").exists():
    Path("src/main/resources/i4-datagen-marker.txt").write_text("after\\n", encoding="utf-8")
""",
        encoding="utf-8",
    )
    wrapper.chmod(0o755)


class I4EngineeringValidatorsContractTest(unittest.TestCase):
    def require_validator(self):
        if not VALIDATOR.is_file():
            self.skipTest("production I4 validator is intentionally absent during RED")
        return load_validator()

    def test_validator_production_entrypoint_exists(self):
        self.assertTrue(
            VALIDATOR.is_file(),
            "I4 RED: production validator engineering/tooling/validators/validate_mod_project.py is missing",
        )

    def test_package_validator_rejects_java_package_path_drift(self):
        module = self.require_validator()
        with tempfile.TemporaryDirectory() as tmp:
            project = copy_golden(Path(tmp) / "project")
            self.assertEqual([], module.validate_package(project))
            common = project / "src/main/java/dev/example/i3golden/I3GoldenMod.java"
            text = common.read_text(encoding="utf-8").replace(
                "package dev.example.i3golden;",
                "package dev.example.wrong;",
            )
            common.write_text(text, encoding="utf-8")
            self.assertTrue(module.validate_package(project))

    def test_mod_id_validator_rejects_identity_drift(self):
        module = self.require_validator()
        with tempfile.TemporaryDirectory() as tmp:
            project = copy_golden(Path(tmp) / "project")
            self.assertEqual([], module.validate_mod_id(project, MOD_SPEC))
            properties = project / "gradle.properties"
            text = properties.read_text(encoding="utf-8").replace(
                "mod_id=i3_golden_mod",
                "mod_id=drifted_mod",
            )
            properties.write_text(text, encoding="utf-8")
            self.assertTrue(module.validate_mod_id(project, MOD_SPEC))

    def test_dependency_validator_rejects_metadata_drift(self):
        module = self.require_validator()
        with tempfile.TemporaryDirectory() as tmp:
            project = copy_golden(Path(tmp) / "project")
            self.assertEqual([], module.validate_dependencies(project, MOD_SPEC))
            metadata = project / "src/main/resources/META-INF/neoforge.mods.toml"
            text = metadata.read_text(encoding="utf-8").replace(
                'modId="minecraft"',
                'modId="create"',
            )
            metadata.write_text(text, encoding="utf-8")
            self.assertTrue(module.validate_dependencies(project, MOD_SPEC))

    def test_dependency_block_regex_groups_lookahead_alternation_explicitly(self):
        module = self.require_validator()
        self.assertEqual(
            r"(?ms)^\s*\[\[dependencies\.[^\]]+\]\]\s*(.*?)(?=(?:^\s*\[\[|\Z))",
            module.DEPENDENCY_BLOCK_RE.pattern,
        )
        metadata = """[[dependencies.i3_golden_mod]]
modId="neoforge"
type="required"

[[dependencies.i3_golden_mod]]
modId="minecraft"
type="required"""
        self.assertEqual(
            [("neoforge", "required"), ("minecraft", "required")],
            module._metadata_dependencies(metadata)[0],
        )

    def test_resource_path_validator_rejects_noncanonical_resource_location(self):
        module = self.require_validator()
        with tempfile.TemporaryDirectory() as tmp:
            project = copy_golden(Path(tmp) / "project")
            self.assertEqual([], module.validate_resource_paths(project))
            bad = project / "src/main/resources/assets/i3_golden_mod/textures/BadName.png"
            bad.parent.mkdir(parents=True, exist_ok=True)
            bad.write_bytes(b"synthetic")
            self.assertTrue(module.validate_resource_paths(project))

    def test_side_boundary_validator_rejects_client_import_in_common_source(self):
        module = self.require_validator()
        with tempfile.TemporaryDirectory() as tmp:
            project = copy_golden(Path(tmp) / "project")
            self.assertEqual([], module.validate_side_boundaries(project))
            common = project / "src/main/java/dev/example/i3golden/I3GoldenMod.java"
            text = common.read_text(encoding="utf-8").replace(
                "package dev.example.i3golden;\n",
                "package dev.example.i3golden;\n\nimport net.minecraft.client.Minecraft;\n",
            )
            common.write_text(text, encoding="utf-8")
            self.assertTrue(module.validate_side_boundaries(project))

    def test_assets_manifest_validator_rejects_mod_id_drift(self):
        module = self.require_validator()
        with tempfile.TemporaryDirectory() as tmp:
            project = copy_golden(Path(tmp) / "project")
            self.assertEqual([], module.validate_assets_manifest(project, MOD_SPEC, ASSET_HANDOFF))
            manifest = json.loads(ASSET_HANDOFF.read_text(encoding="utf-8"))
            manifest["mod_id"] = "drifted_mod"
            bad_manifest = Path(tmp) / "bad-asset-handoff.json"
            write_json(bad_manifest, manifest)
            self.assertTrue(module.validate_assets_manifest(project, MOD_SPEC, bad_manifest))

    def test_datagen_drift_validator_requires_clean_diff_after_official_generator(self):
        module = self.require_validator()
        with tempfile.TemporaryDirectory() as tmp:
            project = copy_golden(Path(tmp) / "project")
            marker = project / "src/main/resources/i4-datagen-marker.txt"
            marker.write_text("before\n", encoding="utf-8")
            install_synthetic_datagen_wrapper(project)
            subprocess.run(["git", "init", "-q"], cwd=project, check=True)
            subprocess.run(["git", "config", "user.name", "I4 Contract"], cwd=project, check=True)
            subprocess.run(["git", "config", "user.email", "i4-contract@example.invalid"], cwd=project, check=True)
            subprocess.run(["git", "add", "."], cwd=project, check=True)
            subprocess.run(["git", "commit", "-qm", "baseline"], cwd=project, check=True)

            self.assertEqual([], module.validate_datagen_drift(project))

            (project / ".i4-trigger-drift").write_text("trigger\n", encoding="utf-8")
            self.assertTrue(module.validate_datagen_drift(project))

    def test_jar_inspection_rejects_missing_common_entrypoint(self):
        module = self.require_validator()
        with tempfile.TemporaryDirectory() as tmp:
            project = copy_golden(Path(tmp) / "project")
            valid_jar = make_jar(Path(tmp) / "valid.jar")
            self.assertEqual([], module.inspect_jar(project, valid_jar))
            bad_jar = make_jar(Path(tmp) / "bad.jar", include_common=False)
            self.assertTrue(module.inspect_jar(project, bad_jar))


if __name__ == "__main__":
    unittest.main()
