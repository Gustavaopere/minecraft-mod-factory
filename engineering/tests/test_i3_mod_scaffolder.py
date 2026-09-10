import importlib.util
import inspect
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCAFFOLDER = ROOT / "engineering" / "tooling" / "scaffolder" / "scaffold_mod.py"
I1_VALIDATOR = ROOT / "engineering" / "tooling" / "validate-i1-foundation.py"
MOD_SPEC = ROOT / "engineering" / "tests" / "fixtures" / "i3-golden-mod-spec.json"
SCAFFOLD_CONFIG = ROOT / "engineering" / "tests" / "fixtures" / "i3-golden-scaffold-config.json"
GOLDEN = ROOT / "engineering" / "tests" / "golden" / "i3-golden-mod"
WRAPPER_FILES = {
    "gradlew",
    "gradlew.bat",
    "gradle/wrapper/gradle-wrapper.properties",
    "gradle/wrapper/gradle-wrapper.jar",
}


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def file_map(root, *, include_wrapper=True):
    result = {}
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if not include_wrapper and relative in WRAPPER_FILES:
            continue
        result[relative] = path.read_bytes()
    return result


def create_synthetic_wrapper_source(root):
    root.mkdir(parents=True, exist_ok=True)
    (root / "gradle/wrapper").mkdir(parents=True, exist_ok=True)
    (root / "gradlew").write_text("#!/bin/sh\necho synthetic wrapper\n", encoding="utf-8", newline="\n")
    (root / "gradlew.bat").write_text("@echo off\r\necho synthetic wrapper\r\n", encoding="utf-8", newline="")
    (root / "gradle/wrapper/gradle-wrapper.properties").write_text(
        "distributionBase=GRADLE_USER_HOME\n"
        "distributionPath=wrapper/dists\n"
        "distributionUrl=https\\://services.gradle.org/distributions/gradle-8.14-bin.zip\n"
        "networkTimeout=10000\n"
        "validateDistributionUrl=true\n"
        "zipStoreBase=GRADLE_USER_HOME\n"
        "zipStorePath=wrapper/dists\n",
        encoding="utf-8",
        newline="\n",
    )
    (root / "gradle/wrapper/gradle-wrapper.jar").write_bytes(b"synthetic-gradle-wrapper-8.14\n")
    return root


class I3ModScaffolderContractTest(unittest.TestCase):
    def setUp(self):
        self.mod_spec = json.loads(MOD_SPEC.read_text(encoding="utf-8"))
        self.config = json.loads(SCAFFOLD_CONFIG.read_text(encoding="utf-8"))

    def require_scaffolder(self):
        if not SCAFFOLDER.is_file():
            self.skipTest("production scaffolder is intentionally absent during I3 RED")
        return load_module(SCAFFOLDER, "i3_scaffold_mod")

    def generate(self, root, output):
        module = self.require_scaffolder()
        wrapper_source = create_synthetic_wrapper_source(root / "wrapper-authority")
        module.generate_project(MOD_SPEC, SCAFFOLD_CONFIG, output, wrapper_source)
        return output, wrapper_source

    def test_scaffolder_production_entrypoint_exists(self):
        self.assertTrue(
            SCAFFOLDER.is_file(),
            "I3 RED: production scaffolder engineering/tooling/scaffolder/scaffold_mod.py is missing",
        )

    def test_scaffolder_wrapper_authority_is_internal_not_caller_supplied(self):
        module = self.require_scaffolder()
        self.assertEqual(
            ["mod_spec_path", "scaffold_config_path", "output_dir"],
            list(inspect.signature(module.generate_project).parameters),
            "I3 security RED: wrapper authority must be Factory-owned, not supplied by callers",
        )

    def test_golden_mod_spec_is_valid_i1_contract(self):
        validator = load_module(I1_VALIDATOR, "i1_validator_for_i3")
        schema = json.loads((ROOT / "engineering/schemas/mod-spec.schema.json").read_text(encoding="utf-8"))
        self.assertEqual([], validator.validate_instance(schema, self.mod_spec))

    def test_generated_project_matches_checked_in_golden_text_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            generated, _ = self.generate(root, root / "generated")
            self.assertEqual(file_map(GOLDEN, include_wrapper=False), file_map(generated, include_wrapper=False))

    def test_generation_is_deterministic(self):
        module = self.require_scaffolder()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            wrapper_source = create_synthetic_wrapper_source(root / "wrapper-authority")
            first = module.generate_project(MOD_SPEC, SCAFFOLD_CONFIG, root / "first", wrapper_source)
            second = module.generate_project(MOD_SPEC, SCAFFOLD_CONFIG, root / "second", wrapper_source)
            self.assertEqual(file_map(first), file_map(second))

    def test_non_empty_target_is_rejected_without_overwrite(self):
        module = self.require_scaffolder()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "existing"
            target.mkdir()
            marker = target / "keep.txt"
            marker.write_text("preserve", encoding="utf-8")
            wrapper_source = create_synthetic_wrapper_source(root / "wrapper-authority")
            with self.assertRaises(FileExistsError):
                module.generate_project(MOD_SPEC, SCAFFOLD_CONFIG, target, wrapper_source)
            self.assertEqual("preserve", marker.read_text(encoding="utf-8"))

    def test_generated_project_uses_exact_audited_stack_and_no_optional_providers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            generated, _ = self.generate(root, root / "generated")
            gradle_properties = (generated / "gradle.properties").read_text(encoding="utf-8")
            build_gradle = (generated / "build.gradle").read_text(encoding="utf-8")
            wrapper = (generated / "gradle/wrapper/gradle-wrapper.properties").read_text(encoding="utf-8")
            metadata = (generated / "src/main/resources/META-INF/neoforge.mods.toml").read_text(encoding="utf-8")
            self.assertIn("minecraft_version=1.21.1", gradle_properties)
            self.assertIn("neo_version=21.1.248", gradle_properties)
            self.assertIn("java_version=21", gradle_properties)
            self.assertIn("junit_version=5.14.3", gradle_properties)
            self.assertIn("net.neoforged.gradle.userdev' version '7.1.26", build_gradle)
            self.assertIn("JavaLanguageVersion.of(Integer.parseInt(java_version))", build_gradle)
            self.assertIn("gradle-8.14-bin.zip", wrapper)
            self.assertIn('modId="${mod_id}"', metadata)
            self.assertIn('modId="neoforge"', metadata)
            self.assertIn('modId="minecraft"', metadata)
            forbidden = ("create", "sable", "minecolonies", "ars_nouveau", "epicfight", "irons_spellbooks")
            lowered = "\n".join((build_gradle, metadata)).lower()
            for provider in forbidden:
                self.assertNotIn(provider, lowered)

    def test_common_and_client_entrypoints_are_physically_separated(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            generated, _ = self.generate(root, root / "generated")
            package_path = Path(*self.config["java_package"].split("."))
            common = generated / "src/main/java" / package_path / f'{self.config["main_class"]}.java'
            client = generated / "src/main/java" / package_path / "client" / f'{self.config["client_class"]}.java'
            common_text = common.read_text(encoding="utf-8")
            client_text = client.read_text(encoding="utf-8")
            self.assertIn("@Mod(I3GoldenMod.MOD_ID)", common_text)
            self.assertNotIn("net.minecraft.client", common_text)
            self.assertIn("@Mod(value = I3GoldenMod.MOD_ID, dist = Dist.CLIENT)", client_text)
            self.assertIn("package dev.example.i3golden.client;", client_text)

    def test_wrapper_files_are_copied_byte_for_byte_from_explicit_authority(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            generated, wrapper_source = self.generate(root, root / "generated")
            for relative in WRAPPER_FILES:
                self.assertEqual((wrapper_source / relative).read_bytes(), (generated / relative).read_bytes(), relative)

    def test_missing_wrapper_authority_is_rejected(self):
        module = self.require_scaffolder()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaises(ValueError):
                module.generate_project(MOD_SPEC, SCAFFOLD_CONFIG, root / "generated", root / "missing-wrapper")

    def test_target_drift_is_rejected_instead_of_silently_retargeted(self):
        module = self.require_scaffolder()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            drifted = json.loads(MOD_SPEC.read_text(encoding="utf-8"))
            drifted["identity"]["target"]["neoforge"] = "21.1.247"
            drifted_path = root / "drifted-mod-spec.json"
            drifted_path.write_text(json.dumps(drifted), encoding="utf-8")
            wrapper_source = create_synthetic_wrapper_source(root / "wrapper-authority")
            with self.assertRaises(ValueError):
                module.generate_project(drifted_path, SCAFFOLD_CONFIG, root / "output", wrapper_source)

    def test_missing_explicit_java_identity_is_rejected_instead_of_guessed(self):
        module = self.require_scaffolder()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            incomplete = json.loads(SCAFFOLD_CONFIG.read_text(encoding="utf-8"))
            incomplete.pop("java_package")
            incomplete_path = root / "incomplete-scaffold-config.json"
            incomplete_path.write_text(json.dumps(incomplete), encoding="utf-8")
            wrapper_source = create_synthetic_wrapper_source(root / "wrapper-authority")
            with self.assertRaises(ValueError):
                module.generate_project(MOD_SPEC, incomplete_path, root / "output", wrapper_source)

    def test_no_unresolved_template_tokens_remain(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            generated, _ = self.generate(root, root / "generated")
            unresolved = []
            for relative, data in file_map(generated).items():
                if relative.endswith(".jar"):
                    continue
                text = data.decode("utf-8")
                if "{{" in text or "}}" in text or "@@" in text:
                    unresolved.append(relative)
            self.assertEqual([], unresolved)


if __name__ == "__main__":
    unittest.main()
