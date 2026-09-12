from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROVIDERS = ROOT / "construction" / "providers"
PROFILE_MODULE = PROVIDERS / "profiles.py"
PROFILE_DIR = PROVIDERS / "profiles"
UPSTREAM = ROOT / "construction" / "upstream" / "registry.json"
PROFILE_SCHEMA = ROOT / "construction" / "schemas" / "external-provider-profile.schema.json"
EXPECTED_IDS = ["blockgpt", "objtoschematic", "schematic-helper", "structmatic"]


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"unable to load {path.relative_to(ROOT)}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ConstructionC10ProviderProfileTest(unittest.TestCase):
    def require_profiles(self):
        if not PROFILE_MODULE.is_file():
            self.skipTest("C10 profile module intentionally absent during RED")
        return load_module(PROFILE_MODULE, "construction_c10_profiles")

    def upstream_registry(self):
        return json.loads(UPSTREAM.read_text(encoding="utf-8"))

    def test_required_profile_files_exist(self):
        required = [PROFILE_MODULE, PROFILE_SCHEMA]
        required += [PROFILE_DIR / f"{provider_id}.json" for provider_id in EXPECTED_IDS]
        missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
        self.assertEqual([], missing, f"C10 RED: missing required files: {missing}")

    def test_profile_schema_is_closed(self):
        if not PROFILE_SCHEMA.is_file():
            self.skipTest("C10 profile schema intentionally absent during RED")
        schema = json.loads(PROFILE_SCHEMA.read_text(encoding="utf-8"))
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(1, schema["properties"]["schema_version"]["const"])

    def test_catalog_reconciles_with_c0_and_is_deterministic(self):
        module = self.require_profiles()
        catalog = module.load_profile_catalog(PROFILE_DIR, self.upstream_registry())
        self.assertEqual(EXPECTED_IDS, list(catalog))
        for provider_id, profile in catalog.items():
            self.assertEqual(provider_id, profile["provider_id"])
            self.assertEqual("EXTERNAL_PROVIDER", profile["integration_policy"])
            self.assertRegex(profile["profile_sha256"], r"^[0-9a-f]{64}$")

    def test_baseline_api_state_is_unverified(self):
        module = self.require_profiles()
        catalog = module.load_profile_catalog(PROFILE_DIR, self.upstream_registry())
        for profile in catalog.values():
            self.assertEqual("UNVERIFIED_API", profile["api"]["state"])
            self.assertIsNone(profile["api"]["official_contract"])

    def test_profile_fingerprint_is_deterministic_and_tamper_evident(self):
        module = self.require_profiles()
        catalog = module.load_profile_catalog(PROFILE_DIR, self.upstream_registry())
        profile = copy.deepcopy(catalog["objtoschematic"])
        expected = profile["profile_sha256"]
        self.assertEqual(expected, module.profile_fingerprint(profile))
        profile["display_name"] += " changed"
        self.assertNotEqual(expected, module.profile_fingerprint(profile))

    def test_profile_mutations_fail_closed(self):
        module = self.require_profiles()
        catalog = module.load_profile_catalog(PROFILE_DIR, self.upstream_registry())
        baseline = copy.deepcopy(catalog["objtoschematic"])

        def extra_field(profile):
            profile["unexpected"] = True

        def unknown_provider(profile):
            profile["provider_id"] = "not-registered"

        def duplicate_capability(profile):
            profile["capabilities"] = ["MESH_TO_STRUCTURE", "MESH_TO_STRUCTURE"]

        def unsorted_capability(profile):
            profile["capabilities"] = ["PROMPT_TO_STRUCTURE", "MESH_TO_STRUCTURE"]

        def invalid_evidence_kind(profile):
            profile["audit"]["evidence"] = [{
                "kind": "BLOG_POST",
                "locator": "https://example.invalid/",
                "observed_at": "2026-09-12",
                "supports": ["capability:MESH_TO_STRUCTURE"],
                "sha256": None,
            }]

        def api_contract_without_api(profile):
            profile["api"]["official_contract"] = {
                "kind": "REST",
                "locator": "https://example.invalid/docs",
                "version": "v1",
                "origin": "https://api.example.invalid",
                "protocol": "HTTPS",
            }

        def manual_below_ep1(profile):
            profile["integration_mode"] = "MANUAL_FILE_HANDOFF"
            profile["handoff"]["accepted_input_kinds"] = ["MESH"]
            profile["handoff"]["output_artifact_kinds"] = ["SCHEMATIC_FILE"]
            profile["limits"]["max_input_bytes"] = 1024
            profile["limits"]["max_output_bytes"] = 4096

        def api_adapter_unproven(profile):
            profile["proof_level"] = "EP1_HANDOFF_VERIFIED"
            profile["integration_mode"] = "API_ADAPTER"

        mutations = {
            "unknown field": extra_field,
            "unknown provider": unknown_provider,
            "duplicate capability": duplicate_capability,
            "unsorted capability": unsorted_capability,
            "invalid evidence kind": invalid_evidence_kind,
            "official contract with unverified API": api_contract_without_api,
            "manual handoff below EP1": manual_below_ep1,
            "API adapter without contract proof": api_adapter_unproven,
        }

        for label, mutate in mutations.items():
            with self.subTest(label=label):
                profile = copy.deepcopy(baseline)
                mutate(profile)
                profile["profile_sha256"] = module.profile_fingerprint(profile)
                errors = module.validate_profile(profile, self.upstream_registry())
                self.assertTrue(errors, f"mutation should fail closed: {label}")

    def test_catalog_rejects_duplicate_provider_ids(self):
        module = self.require_profiles()
        if not hasattr(module, "validate_profile_catalog"):
            self.fail("C10 profile module must expose validate_profile_catalog")
        catalog = module.load_profile_catalog(PROFILE_DIR, self.upstream_registry())
        documents = [copy.deepcopy(profile) for profile in catalog.values()]
        documents.append(copy.deepcopy(documents[0]))
        errors = module.validate_profile_catalog(documents, self.upstream_registry())
        self.assertTrue(any("duplicate" in error.lower() for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
