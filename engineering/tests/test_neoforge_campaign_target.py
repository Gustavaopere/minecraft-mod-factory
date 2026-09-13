import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASELINE = ROOT / "engineering/contracts/target-baseline.json"
RESOLVER = ROOT / "engineering/tooling/resolve-neoforge-campaign-target.py"
MOD_SPEC_SCHEMA = ROOT / "engineering/schemas/mod-spec.schema.json"
TEST_MANIFEST_SCHEMA = ROOT / "engineering/schemas/test-manifest.schema.json"
COMPATIBILITY_SCHEMA = ROOT / "engineering/schemas/compatibility-matrix.schema.json"
SCAFFOLDER = ROOT / "engineering/tooling/scaffolder/scaffold_mod.py"
I5_HARNESS = ROOT / "engineering/tooling/test-harness/run_test_harness.py"
I8_GENERATOR = ROOT / "engineering/tooling/feature-generator/generate_feature.py"
I8_FEATURE_SET = ROOT / "engineering/tests/fixtures/i8-feature-set.json"
GRADLE_PROPERTIES_TEMPLATE = ROOT / "engineering/templates/neoforge-mod/gradle.properties.tmpl"
PROBE_MOD_SPEC = ROOT / "construction/runtime/neoforge-registry-probe/mod-spec.json"
PROBE_SOURCE = ROOT / "construction/runtime/neoforge-registry-probe/FactoryConstructionRegistryProbe.java"
MOD_SPEC_CONTRACT = ROOT / "engineering/contracts/MOD-SPEC-CONTRACT.md"
VERSION_AUTHORITY = ROOT / "skills/VERSION-AUTHORITY.md"

EXPECTED_TARGET = {
    "minecraft": "1.21.1",
    "loader": "neoforge",
    "neoforge_line": "21.1",
    "neoforge": "21.1.250",
    "java": 21,
}
EXPECTED_SOURCE = "https://maven.neoforged.net/releases/net/neoforged/neoforge/maven-metadata.xml"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class NeoForgeCampaignTargetContractTest(unittest.TestCase):
    def require_baseline(self):
        self.assertTrue(
            BASELINE.is_file(),
            "RED: engineering/contracts/target-baseline.json must pin the resolved campaign target",
        )
        return load_json(BASELINE)

    def require_resolver(self):
        self.assertTrue(
            RESOLVER.is_file(),
            "RED: explicit campaign-start NeoForge resolver is missing",
        )
        return load_module(RESOLVER, "neoforge_campaign_target_resolver")

    def test_campaign_target_is_machine_readable_and_pinned_exactly(self):
        baseline = self.require_baseline()
        self.assertEqual(1, baseline.get("schema_version"))
        self.assertEqual("latest-compatible-at-campaign-start", baseline.get("resolution_policy"))
        self.assertEqual(EXPECTED_SOURCE, baseline.get("resolution_source"))
        self.assertEqual(EXPECTED_TARGET, baseline.get("target"))

    def test_resolver_selects_latest_stable_release_only_within_minecraft_line(self):
        resolver = self.require_resolver()
        metadata = """<?xml version="1.0" encoding="UTF-8"?>
<metadata><versioning><versions>
<version>21.1.248</version>
<version>21.1.249</version>
<version>21.1.250</version>
<version>21.1.251-beta</version>
<version>21.2.0-beta</version>
</versions></versioning></metadata>
"""
        versions = resolver.parse_maven_versions(metadata)
        self.assertEqual("21.1.250", resolver.select_latest_compatible(versions, "1.21.1"))
        with self.assertRaises(ValueError):
            resolver.select_latest_compatible(["21.2.0-beta", "21.2.1"], "1.21.1")

    def test_live_schemas_use_the_campaign_pin(self):
        baseline = self.require_baseline()
        target = baseline["target"]
        for path, root_key in (
            (MOD_SPEC_SCHEMA, ("properties", "identity", "properties", "target", "properties")),
            (TEST_MANIFEST_SCHEMA, ("properties", "target", "properties")),
            (COMPATIBILITY_SCHEMA, ("properties", "target", "properties")),
        ):
            value = load_json(path)
            node = value
            for key in root_key:
                node = node[key]
            with self.subTest(path=path.name):
                self.assertEqual(target["minecraft"], node["minecraft"]["const"])
                self.assertEqual(target["loader"], node["loader"]["const"])
                self.assertEqual(target["neoforge"], node["neoforge"]["const"])
                self.assertEqual(target["java"], node["java"]["const"])

    def test_scaffolder_i5_i8_and_template_match_campaign_pin(self):
        baseline = self.require_baseline()
        target = baseline["target"]
        scaffolder = SCAFFOLDER.read_text(encoding="utf-8")
        harness = I5_HARNESS.read_text(encoding="utf-8")
        generator = I8_GENERATOR.read_text(encoding="utf-8")
        template = GRADLE_PROPERTIES_TEMPLATE.read_text(encoding="utf-8")
        self.assertIn("target-baseline.json", scaffolder)
        self.assertIn("target-baseline.json", harness)
        self.assertIn("target-baseline.json", generator)
        self.assertIn(f"neo_version={target['neoforge']}", template)
        self.assertNotIn("21.1.248", scaffolder)
        self.assertNotIn("21.1.248", harness)
        self.assertNotIn("21.1.248", generator)
        self.assertNotIn("neo_version=21.1.248", template)

    def test_live_engineering_fixtures_match_campaign_pin(self):
        target_without_line = {
            "minecraft": EXPECTED_TARGET["minecraft"],
            "loader": EXPECTED_TARGET["loader"],
            "neoforge": EXPECTED_TARGET["neoforge"],
            "java": EXPECTED_TARGET["java"],
        }
        json_targets = (
            ROOT / "engineering/examples/mod-spec.example.json",
            ROOT / "engineering/examples/test-manifest.example.json",
            ROOT / "engineering/examples/compatibility-matrix.example.json",
            ROOT / "engineering/tests/fixtures/i3-golden-mod-spec.json",
            ROOT / "engineering/tests/fixtures/i4-golden-mod-spec.json",
            I8_FEATURE_SET,
            ROOT / "engineering/tests/fixtures/i9-machine-mod-spec.json",
        )
        for path in json_targets:
            data = load_json(path)
            declared = data["identity"]["target"] if "identity" in data else data["target"]
            with self.subTest(path=path.relative_to(ROOT).as_posix()):
                self.assertEqual(target_without_line, declared)
        golden_properties = (ROOT / "engineering/tests/golden/i3-golden-mod/gradle.properties").read_text(encoding="utf-8")
        self.assertIn("neo_version=21.1.250", golden_properties)

    def test_c4_probe_matches_campaign_pin_and_checks_runtime_version(self):
        target = self.require_baseline()["target"]
        probe_spec = load_json(PROBE_MOD_SPEC)
        self.assertEqual(target["neoforge"], probe_spec["identity"]["target"]["neoforge"])
        source = PROBE_SOURCE.read_text(encoding="utf-8")
        self.assertIn(f'NEOFORGE_VERSION = "{target["neoforge"]}"', source)
        self.assertIn("ModList.get()", source)
        self.assertIn('getModContainerById("neoforge")', source)
        self.assertIn("getModInfo().getVersion()", source)
        self.assertIn("NeoForge runtime version mismatch", source)

    def test_live_version_docs_describe_latest_compatible_campaign_pin_policy(self):
        for path in (MOD_SPEC_CONTRACT, VERSION_AUTHORITY):
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.relative_to(ROOT).as_posix()):
                self.assertIn("21.1.250", text)
                self.assertIn("latest-compatible-at-campaign-start", text)


if __name__ == "__main__":
    unittest.main()
