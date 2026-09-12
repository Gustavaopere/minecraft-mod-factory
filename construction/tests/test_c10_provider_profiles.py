from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROVIDERS = ROOT / "construction" / "providers"
PROFILE_MODULE = PROVIDERS / "profiles.py"
ERROR_MODULE = PROVIDERS / "errors.py"
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

    def baseline_profile(self, module):
        return copy.deepcopy(
            module.load_profile_catalog(PROFILE_DIR, self.upstream_registry())["objtoschematic"]
        )

    @staticmethod
    def refresh_fingerprint(module, profile):
        profile["profile_sha256"] = module.profile_fingerprint(profile)
        return profile

    def test_required_profile_files_exist(self):
        required = [PROFILE_MODULE, ERROR_MODULE, PROFILE_SCHEMA]
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

    def test_validator_rejects_malformed_nested_contracts(self):
        module = self.require_profiles()
        baseline = self.baseline_profile(module)
        upstream = self.upstream_registry()

        self.assertEqual(["profile must be an object"], module.validate_profile([], upstream))

        mutations = {
            "schema": lambda p: p.__setitem__("schema_version", 2),
            "provider id": lambda p: p.__setitem__("provider_id", "Invalid Provider"),
            "display": lambda p: p.__setitem__("display_name", " "),
            "policy": lambda p: p.__setitem__("integration_policy", "VENDORED"),
            "proof": lambda p: p.__setitem__("proof_level", "EP9_IMPOSSIBLE"),
            "mode": lambda p: p.__setitem__("integration_mode", "AUTOMATIC_MAGIC"),
            "capability shape": lambda p: p.__setitem__("capabilities", "MESH_TO_STRUCTURE"),
            "audit shape": lambda p: p.__setitem__("audit", []),
            "audit fields": lambda p: p.__setitem__("audit", {"audited_at": "2026-09-12"}),
            "audit date": lambda p: p["audit"].__setitem__("audited_at", "yesterday"),
            "evidence shape": lambda p: p["audit"].__setitem__("evidence", {}),
            "evidence record shape": lambda p: p["audit"].__setitem__("evidence", ["bad"]),
            "api shape": lambda p: p.__setitem__("api", []),
            "handoff shape": lambda p: p.__setitem__("handoff", []),
            "limits shape": lambda p: p.__setitem__("limits", []),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                profile = copy.deepcopy(baseline)
                mutate(profile)
                self.refresh_fingerprint(module, profile)
                self.assertTrue(module.validate_profile(profile, upstream))

        profile = copy.deepcopy(baseline)
        record = profile["audit"]["evidence"][0]
        record.update({
            "locator": "http://not-https.invalid",
            "observed_at": "bad date",
            "supports": [],
            "sha256": "not-a-sha",
        })
        self.refresh_fingerprint(module, profile)
        errors = module.validate_profile(profile, upstream)
        for expected in ("locator", "observed_at", "supports", "sha256"):
            self.assertTrue(any(expected in error for error in errors), errors)

        profile = copy.deepcopy(baseline)
        profile["api"].update({"state": "UNKNOWN_STATE", "auth": "PASSWORD"})
        self.refresh_fingerprint(module, profile)
        errors = module.validate_profile(profile, upstream)
        self.assertTrue(any("api.state" in error for error in errors), errors)
        self.assertTrue(any("api.auth" in error for error in errors), errors)

        profile = copy.deepcopy(baseline)
        profile["handoff"].update({
            "accepted_input_kinds": ["UNKNOWN"],
            "output_artifact_kinds": "SCHEMATIC_FILE",
            "manual_action_required": "yes",
            "determinism": "MAYBE",
        })
        self.refresh_fingerprint(module, profile)
        errors = module.validate_profile(profile, upstream)
        for expected in ("accepted_input_kinds", "output_artifact_kinds", "manual_action_required", "determinism"):
            self.assertTrue(any(expected in error for error in errors), errors)

        profile = copy.deepcopy(baseline)
        profile["limits"] = {"max_input_bytes": 0, "max_output_bytes": -1, "timeout_seconds": True}
        self.refresh_fingerprint(module, profile)
        errors = module.validate_profile(profile, upstream)
        self.assertGreaterEqual(sum("limits." in error for error in errors), 3)

    def test_evidence_locator_contract_accepts_only_supported_authorities(self):
        module = self.require_profiles()
        baseline = self.baseline_profile(module)
        upstream = self.upstream_registry()
        valid_locators = [
            "owner/repository@" + "a" * 40,
            "repo://construction/providers/profiles/objtoschematic.json",
        ]
        for locator in valid_locators:
            with self.subTest(locator=locator):
                profile = copy.deepcopy(baseline)
                profile["audit"]["evidence"][0]["locator"] = locator
                self.refresh_fingerprint(module, profile)
                errors = module.validate_profile(profile, upstream)
                self.assertFalse(any("locator is invalid" in error for error in errors), errors)

        invalid_locators = [
            None,
            "",
            "repo://construction/../STATUS.md",
            "repo://construction/providers\\profile.json",
            "file:///tmp/profile.json",
        ]
        for locator in invalid_locators:
            with self.subTest(locator=locator):
                profile = copy.deepcopy(baseline)
                profile["audit"]["evidence"][0]["locator"] = locator
                self.refresh_fingerprint(module, profile)
                errors = module.validate_profile(profile, upstream)
                self.assertTrue(any("locator is invalid" in error for error in errors), errors)

    def test_manual_handoff_profile_contract(self):
        module = self.require_profiles()
        upstream = self.upstream_registry()
        manual = self.baseline_profile(module)
        manual["proof_level"] = "EP1_HANDOFF_VERIFIED"
        manual["integration_mode"] = "MANUAL_FILE_HANDOFF"
        manual["handoff"].update({
            "accepted_input_kinds": ["MESH"],
            "output_artifact_kinds": ["SCHEMATIC_FILE"],
            "manual_action_required": True,
        })
        manual["limits"].update({
            "max_input_bytes": 1024,
            "max_output_bytes": 4096,
            "timeout_seconds": None,
        })
        self.refresh_fingerprint(module, manual)
        self.assertEqual([], module.validate_profile(manual, upstream))

        def missing_input(p):
            p["handoff"]["accepted_input_kinds"] = []

        def missing_output(p):
            p["handoff"]["output_artifact_kinds"] = []

        def no_manual_action(p):
            p["handoff"]["manual_action_required"] = False

        def no_input_limit(p):
            p["limits"]["max_input_bytes"] = None

        def no_output_limit(p):
            p["limits"]["max_output_bytes"] = None

        def timeout_present(p):
            p["limits"]["timeout_seconds"] = 30

        for label, mutate in {
            "input kind": missing_input,
            "output kind": missing_output,
            "manual action": no_manual_action,
            "input limit": no_input_limit,
            "output limit": no_output_limit,
            "timeout": timeout_present,
        }.items():
            with self.subTest(label=label):
                profile = copy.deepcopy(manual)
                mutate(profile)
                self.refresh_fingerprint(module, profile)
                self.assertTrue(module.validate_profile(profile, upstream))

    def test_api_contract_and_adapter_require_reconciled_proof(self):
        module = self.require_profiles()
        upstream = self.upstream_registry()
        for provider in upstream["external_providers"]:
            if provider["id"] == "objtoschematic":
                provider["api_state"] = "CONTRACT_PROVEN_API"

        profile = self.baseline_profile(module)
        profile["proof_level"] = "EP1_HANDOFF_VERIFIED"
        profile["integration_mode"] = "API_ADAPTER"
        profile["api"] = {
            "state": "CONTRACT_PROVEN_API",
            "auth": "NONE",
            "official_contract": {
                "kind": "REST",
                "locator": "https://example.invalid/openapi.json",
                "version": "v1",
                "origin": "https://api.example.invalid",
                "protocol": "HTTPS",
            },
        }
        profile["limits"] = {
            "max_input_bytes": 1024,
            "max_output_bytes": 4096,
            "timeout_seconds": 30,
        }
        self.refresh_fingerprint(module, profile)
        self.assertEqual([], module.validate_profile(profile, upstream))

        mutations = {
            "contract shape": lambda p: p["api"].__setitem__("official_contract", []),
            "kind": lambda p: p["api"]["official_contract"].__setitem__("kind", "SOAP"),
            "locator": lambda p: p["api"]["official_contract"].__setitem__("locator", "http://example.invalid"),
            "origin": lambda p: p["api"]["official_contract"].__setitem__("origin", "http://example.invalid"),
            "version": lambda p: p["api"]["official_contract"].__setitem__("version", ""),
            "protocol": lambda p: p["api"]["official_contract"].__setitem__("protocol", "HTTP"),
            "limit": lambda p: p["limits"].__setitem__("timeout_seconds", None),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                candidate = copy.deepcopy(profile)
                mutate(candidate)
                self.refresh_fingerprint(module, candidate)
                self.assertTrue(module.validate_profile(candidate, upstream))

        verified_only = copy.deepcopy(profile)
        verified_only["api"]["state"] = "VERIFIED_API"
        for provider in upstream["external_providers"]:
            if provider["id"] == "objtoschematic":
                provider["api_state"] = "VERIFIED_API"
        self.refresh_fingerprint(module, verified_only)
        errors = module.validate_profile(verified_only, upstream)
        self.assertTrue(any("API_ADAPTER requires" in error for error in errors), errors)

    def test_upstream_reconciliation_fails_closed(self):
        module = self.require_profiles()
        baseline = self.baseline_profile(module)

        self.assertTrue(module.validate_profile(baseline, []))
        self.assertTrue(module.validate_profile(baseline, {"external_providers": {}}))

        upstream = self.upstream_registry()
        for provider in upstream["external_providers"]:
            if provider["id"] == "objtoschematic":
                provider["integration_policy"] = "REFERENCE_ONLY"
                provider["api_state"] = "VERIFIED_API"
        errors = module.validate_profile(baseline, upstream)
        self.assertTrue(any("upstream integration_policy" in error for error in errors), errors)
        self.assertTrue(any("atomically reconciled" in error for error in errors), errors)

    def test_catalog_and_loader_fail_closed_on_malformed_sources(self):
        module = self.require_profiles()
        upstream = self.upstream_registry()
        self.assertEqual(
            ["provider profile catalog must be an array"],
            module.validate_profile_catalog({}, upstream),
        )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaisesRegex(ValueError, "does not exist"):
                module.load_profile_catalog(root / "missing", upstream)

            malformed = root / "malformed"
            malformed.mkdir()
            (malformed / "broken.json").write_text("{", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "invalid C10 profile JSON"):
                module.load_profile_catalog(malformed, upstream)

            non_object = root / "non-object"
            non_object.mkdir()
            (non_object / "array.json").write_text("[]\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "must be an object"):
                module.load_profile_catalog(non_object, upstream)

            invalid = root / "invalid"
            invalid.mkdir()
            profile = self.baseline_profile(module)
            profile["display_name"] = ""
            self.refresh_fingerprint(module, profile)
            (invalid / "profile.json").write_text(
                json.dumps(profile, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "invalid C10 provider catalog"):
                module.load_profile_catalog(invalid, upstream)

    def test_c10_error_contract_is_stable_and_sanitized(self):
        module = load_module(ERROR_MODULE, "construction_c10_errors")
        error = module.C10Error("UNKNOWN_PROVIDER", "provider is unavailable")
        self.assertEqual("UNKNOWN_PROVIDER", error.code)
        self.assertEqual("provider is unavailable", str(error))
        with self.assertRaisesRegex(ValueError, "unknown C10 error code"):
            module.C10Error("NOT_A_CODE", "bad")
        with self.assertRaisesRegex(ValueError, "message must be non-empty"):
            module.C10Error("UNKNOWN_PROVIDER", "")
        with self.assertRaisesRegex(ValueError, "message must be non-empty"):
            module.C10Error("UNKNOWN_PROVIDER", None)

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
