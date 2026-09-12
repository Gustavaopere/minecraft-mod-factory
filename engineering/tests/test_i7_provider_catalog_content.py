import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "engineering" / "schemas" / "provider-catalog.schema.json"
CATALOG = ROOT / "engineering" / "catalog" / "providers" / "PROVIDER-CATALOG.json"

PHYSICAL_SNAPSHOT_SHA256 = "7c0a23d6013101383d196526e4b6ba6940fb54a0fed10eaed5956ab015cfcc00"
SOURCE_REGISTRY_ID = "latest_physical_modlist_2026_09_09"

SEED_PHYSICAL_PROVIDERS = {
    "geckolib": ("4.9.2", "MOD_METADATA"),
    "azurelib": ("3.1.11", "MOD_METADATA"),
    "easy_model_entities": ("2.3.0", "JAR_FILENAME"),
    "entity_model_features": ("3.3.5", "MOD_METADATA"),
    "cpm": ("0.6.27a", "MOD_METADATA"),
    "player_animation_library": ("1.1.6+mc.1.21.1", "MOD_METADATA"),
    "playeranimator": ("2.0.4+1.21.1", "MOD_METADATA"),
    "epicfight": ("21.17.3.1", "MOD_METADATA"),
    "create": ("6.0.10", "MOD_METADATA"),
    "irons_spellbooks": ("1.21.1-3.16.3", "MOD_METADATA"),
    "ars_nouveau": ("5.13.1", "MOD_METADATA"),
}

PROOF_LEVELS = [
    "P0 PRESENCE_ONLY",
    "P1 METADATA_VERIFIED",
    "P2 SOURCE/DOC_VERIFIED",
    "P3 COMPILE_PROVEN",
    "P4 RUNTIME_SMOKE",
    "P5 INTEGRATION_TESTED",
    "P6 MULTIPLAYER/PERF_PROVEN",
]
PROOF_RANK = {level: index for index, level in enumerate(PROOF_LEVELS)}

EXPECTED_PROOF_CEILINGS = {
    "geckolib": "P5 INTEGRATION_TESTED",
    "azurelib": "P2 SOURCE/DOC_VERIFIED",
    "easy_model_entities": "P4 RUNTIME_SMOKE",
    "entity_model_features": "P2 SOURCE/DOC_VERIFIED",
    "cpm": "P2 SOURCE/DOC_VERIFIED",
    "player_animation_library": "P2 SOURCE/DOC_VERIFIED",
    "playeranimator": "P2 SOURCE/DOC_VERIFIED",
    "epicfight": "P2 SOURCE/DOC_VERIFIED",
    "create": "P0 PRESENCE_ONLY",
    "irons_spellbooks": "P0 PRESENCE_ONLY",
    "ars_nouveau": "P0 PRESENCE_ONLY",
}


class I7ProviderCatalogContentRedTest(unittest.TestCase):
    def load_catalog(self):
        return json.loads(CATALOG.read_text(encoding="utf-8"))

    def providers_by_id(self):
        providers = self.load_catalog().get("providers", [])
        return {provider["mod_id"]: provider for provider in providers if isinstance(provider, dict) and "mod_id" in provider}

    def test_schema_requires_source_and_license_metadata(self):
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        provider = schema["$defs"]["provider"]
        required = set(provider.get("required", []))
        properties = provider.get("properties", {})
        self.assertTrue({"source", "license"}.issubset(required), "I7 RED: provider schema must require source and license metadata")
        self.assertIn("source", properties)
        self.assertIn("license", properties)

    def test_catalog_seeds_exact_priority_physical_mapping(self):
        providers = self.providers_by_id()
        self.assertEqual(set(SEED_PHYSICAL_PROVIDERS), set(providers), "I7 RED: priority provider seed set is incomplete")
        for mod_id, (version, evidence) in SEED_PHYSICAL_PROVIDERS.items():
            physical = providers[mod_id]["physical"]
            with self.subTest(mod_id=mod_id):
                self.assertEqual(version, physical["version"])
                self.assertEqual(evidence, physical["version_evidence"])
                self.assertEqual(SOURCE_REGISTRY_ID, physical["source_registry_id"])
                self.assertEqual(PHYSICAL_SNAPSHOT_SHA256, physical["source_sha256"])

    def test_seed_records_have_source_license_and_nonempty_api_evidence(self):
        providers = self.providers_by_id()
        self.assertEqual(set(SEED_PHYSICAL_PROVIDERS), set(providers), "I7 RED: seed records must exist before provenance can be validated")
        for mod_id, provider in providers.items():
            with self.subTest(mod_id=mod_id):
                source = provider.get("source")
                license_info = provider.get("license")
                self.assertIsInstance(source, dict)
                self.assertIn(source.get("state"), {"CONFIRMED", "UNRESOLVED", "REFERENCE_ONLY"})
                self.assertTrue(source.get("evidence"))
                self.assertIsInstance(license_info, dict)
                self.assertIn(license_info.get("state"), {"CONFIRMED", "UNRESOLVED", "REFERENCE_ONLY"})
                self.assertTrue(license_info.get("evidence"))
                self.assertTrue(provider.get("api_surface"), "every curated seed must declare at least one explicit proof surface")

    def test_seed_proof_levels_match_existing_evidence_ceiling(self):
        providers = self.providers_by_id()
        self.assertEqual(set(EXPECTED_PROOF_CEILINGS), set(providers), "I7 RED: proof ceilings require the complete seed set")
        for mod_id, expected_ceiling in EXPECTED_PROOF_CEILINGS.items():
            surfaces = providers[mod_id].get("api_surface", [])
            levels = [surface.get("proof_level") for surface in surfaces if isinstance(surface, dict)]
            self.assertTrue(levels, f"{mod_id} must expose at least one proof surface")
            self.assertTrue(all(level in PROOF_RANK for level in levels), f"{mod_id} contains an unknown proof level")
            actual_ceiling = max(levels, key=PROOF_RANK.__getitem__)
            with self.subTest(mod_id=mod_id):
                self.assertEqual(expected_ceiling, actual_ceiling)

    def test_presence_only_seeds_are_not_marked_supported(self):
        providers = self.providers_by_id()
        for mod_id in ("create", "irons_spellbooks", "ars_nouveau"):
            self.assertIn(mod_id, providers, f"I7 RED: missing P0 seed {mod_id}")
            with self.subTest(mod_id=mod_id):
                self.assertFalse(providers[mod_id].get("supported"), "P0 presence alone must never imply supported integration")


if __name__ == "__main__":
    unittest.main()
