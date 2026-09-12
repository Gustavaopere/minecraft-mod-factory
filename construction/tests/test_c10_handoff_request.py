from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path

from construction.providers.common import canonical_json_bytes, sha256_hex
from construction.providers.errors import C10Error

ROOT = Path(__file__).resolve().parents[2]
PROVIDERS = ROOT / "construction" / "providers"
HANDOFF_MODULE = PROVIDERS / "handoff.py"
PROFILE_MODULE = PROVIDERS / "profiles.py"
PROFILE_DIR = PROVIDERS / "profiles"
REQUEST_SCHEMA = ROOT / "construction" / "schemas" / "provider-handoff-request.schema.json"
UPSTREAM = ROOT / "construction" / "upstream" / "registry.json"
VALID_SHA = "a" * 64
PHYSICAL_SHA = "7c0a23d6013101383d196526e4b6ba6940fb54a0fed10eaed5956ab015cfcc00"
OTHER_PHYSICAL_SHA = "b" * 64


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"unable to load {path.relative_to(ROOT)}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ConstructionC10HandoffRequestTest(unittest.TestCase):
    def require_handoff(self):
        if not HANDOFF_MODULE.is_file():
            self.skipTest("C10 handoff module intentionally absent during RED")
        return load_module(HANDOFF_MODULE, "construction_c10_handoff_request")

    def profiles(self):
        return load_module(PROFILE_MODULE, "construction_c10_request_profiles")

    def upstream_registry(self):
        return json.loads(UPSTREAM.read_text(encoding="utf-8"))

    def baseline_profile(self):
        module = self.profiles()
        return copy.deepcopy(
            module.load_profile_catalog(PROFILE_DIR, self.upstream_registry())["objtoschematic"]
        )

    def operational_profile(self, *, mode: str = "MANUAL_FILE_HANDOFF", api_state: str = "UNVERIFIED_API"):
        module = self.profiles()
        profile = self.baseline_profile()
        profile["proof_level"] = "EP1_HANDOFF_VERIFIED"
        profile["integration_mode"] = mode
        profile["capabilities"] = [
            "IMAGE_TO_STRUCTURE",
            "MESH_TO_STRUCTURE",
            "PROMPT_TO_STRUCTURE",
            "STRUCTURE_EDITING",
        ]
        profile["handoff"] = {
            "accepted_input_kinds": [
                "IMAGE",
                "LITEMATIC_FILE",
                "MESH",
                "SCHEMATIC_FILE",
                "VANILLA_STRUCTURE_NBT",
            ],
            "output_artifact_kinds": ["SCHEMATIC_FILE"],
            "manual_action_required": mode == "MANUAL_FILE_HANDOFF",
            "determinism": "UNKNOWN",
        }
        profile["limits"] = {
            "max_input_bytes": 1_000_000,
            "max_output_bytes": 2_000_000,
            "timeout_seconds": None if mode == "MANUAL_FILE_HANDOFF" else 30,
        }
        if mode == "API_ADAPTER":
            profile["api"] = {
                "state": api_state,
                "auth": "NONE",
                "official_contract": {
                    "kind": "REST",
                    "locator": "https://example.invalid/docs/api",
                    "version": "v1",
                    "origin": "https://api.example.invalid",
                    "protocol": "HTTPS",
                },
            }
        profile["profile_sha256"] = module.profile_fingerprint(profile)
        return profile

    @staticmethod
    def artifact(kind: str) -> dict[str, object]:
        return {
            "kind": kind,
            "sha256": VALID_SHA,
            "byte_length": 123,
            "media_type": "application/octet-stream",
            "repo_relpath": "construction/fixtures/c10/task3/input.bin",
        }

    @staticmethod
    def manual_step() -> dict[str, object]:
        return {
            "required": True,
            "step_id": "submit-input",
            "instruction": "Upload the Factory-owned input artifact to the provider editor.",
            "expected_result": "The provider shows a generated block preview.",
        }

    @staticmethod
    def refresh_request_id(request: dict[str, object]) -> dict[str, object]:
        payload = copy.deepcopy(request)
        payload.pop("request_id", None)
        request["request_id"] = sha256_hex(canonical_json_bytes(payload))
        return request

    def build_request(
        self,
        module,
        profile,
        *,
        operation: str = "MESH_TO_STRUCTURE",
        text_input: str | None = None,
        input_artifacts: list[dict[str, object]] | None = None,
        expected_output_kinds: list[str] | None = None,
        manual_step: dict[str, object] | None = None,
    ):
        if input_artifacts is None:
            input_artifacts = [self.artifact("MESH")]
        if expected_output_kinds is None:
            expected_output_kinds = ["SCHEMATIC_FILE"]
        if manual_step is None and profile["integration_mode"] == "MANUAL_FILE_HANDOFF":
            manual_step = self.manual_step()
        return module.build_handoff_request(
            profile,
            operation=operation,
            text_input=text_input,
            input_artifacts=input_artifacts,
            expected_output_kinds=expected_output_kinds,
            physical_modlist_sha256=PHYSICAL_SHA,
            manual_step=manual_step,
        )

    def assert_invalid_build(self, module, profile, **kwargs):
        with self.assertRaises(C10Error) as raised:
            self.build_request(module, profile, **kwargs)
        self.assertEqual("INVALID_HANDOFF_REQUEST", raised.exception.code)

    def test_required_task3_files_exist(self):
        missing = [
            str(path.relative_to(ROOT))
            for path in (HANDOFF_MODULE, REQUEST_SCHEMA)
            if not path.is_file()
        ]
        self.assertEqual([], missing, f"C10 Task 3 RED: missing required files: {missing}")

    def test_request_schema_is_closed(self):
        if not REQUEST_SCHEMA.is_file():
            self.skipTest("C10 request schema intentionally absent during RED")
        schema = json.loads(REQUEST_SCHEMA.read_text(encoding="utf-8"))
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(1, schema["properties"]["schema_version"]["const"])
        self.assertEqual(4000, schema["properties"]["text_input"]["maxLength"])
        self.assertFalse(schema["properties"]["target"]["additionalProperties"])
        self.assertFalse(schema["properties"]["manual_step"]["additionalProperties"])
        self.assertFalse(schema["properties"]["input_artifacts"]["items"]["additionalProperties"])

    def test_request_id_is_deterministic_and_tamper_evident(self):
        module = self.require_handoff()
        profile = self.operational_profile()
        first = self.build_request(module, profile)
        second = self.build_request(module, profile)
        self.assertEqual(first, second)
        self.assertRegex(first["request_id"], r"^[0-9a-f]{64}$")
        self.assertEqual([], module.validate_handoff_request(first, profile))

        tampered = copy.deepcopy(first)
        tampered["target"]["physical_modlist_sha256"] = OTHER_PHYSICAL_SHA
        errors = module.validate_handoff_request(tampered, profile)
        self.assertTrue(any("request_id" in error.lower() for error in errors), errors)

    def test_research_only_profile_cannot_build_operational_request(self):
        module = self.require_handoff()
        profile = self.baseline_profile()
        profile["proof_level"] = "EP0_DISCOVERED"
        profile["integration_mode"] = "RESEARCH_ONLY"
        profile["handoff"] = {
            "accepted_input_kinds": [],
            "output_artifact_kinds": [],
            "manual_action_required": True,
            "determinism": "UNKNOWN",
        }
        profile["limits"] = {
            "max_input_bytes": None,
            "max_output_bytes": None,
            "timeout_seconds": None,
        }
        profile["profile_sha256"] = self.profiles().profile_fingerprint(profile)
        self.assert_invalid_build(module, profile)

    def test_all_four_operations_enforce_exact_input_shapes(self):
        module = self.require_handoff()
        profile = self.operational_profile()
        cases = (
            ("PROMPT_TO_STRUCTURE", "Build a stone arch.", []),
            ("IMAGE_TO_STRUCTURE", None, [self.artifact("IMAGE")]),
            ("IMAGE_TO_STRUCTURE", "Match the silhouette.", [self.artifact("IMAGE")]),
            ("MESH_TO_STRUCTURE", None, [self.artifact("MESH")]),
            ("STRUCTURE_EDITING", "Add a tower to the east side.", [self.artifact("SCHEMATIC_FILE")]),
        )
        for operation, text_input, artifacts in cases:
            with self.subTest(operation=operation, text_input=text_input):
                request = self.build_request(
                    module,
                    profile,
                    operation=operation,
                    text_input=text_input,
                    input_artifacts=artifacts,
                )
                self.assertEqual([], module.validate_handoff_request(request, profile))

        invalid_cases = (
            {"operation": "PROMPT_TO_STRUCTURE", "text_input": "", "input_artifacts": []},
            {"operation": "PROMPT_TO_STRUCTURE", "text_input": "x" * 4001, "input_artifacts": []},
            {"operation": "PROMPT_TO_STRUCTURE", "text_input": "ok", "input_artifacts": [self.artifact("IMAGE")]},
            {"operation": "IMAGE_TO_STRUCTURE", "text_input": None, "input_artifacts": []},
            {"operation": "IMAGE_TO_STRUCTURE", "text_input": None, "input_artifacts": [self.artifact("MESH")]},
            {"operation": "MESH_TO_STRUCTURE", "text_input": "not allowed", "input_artifacts": [self.artifact("MESH")]},
            {"operation": "MESH_TO_STRUCTURE", "text_input": None, "input_artifacts": [self.artifact("IMAGE")]},
            {"operation": "STRUCTURE_EDITING", "text_input": "", "input_artifacts": [self.artifact("SCHEMATIC_FILE")]},
            {"operation": "STRUCTURE_EDITING", "text_input": "edit", "input_artifacts": [self.artifact("IMAGE")]},
        )
        for kwargs in invalid_cases:
            with self.subTest(kwargs=kwargs):
                self.assert_invalid_build(module, profile, **kwargs)

    def test_operation_capability_and_profile_handoff_lists_are_authoritative(self):
        module = self.require_handoff()
        profile = self.operational_profile()

        without_capability = copy.deepcopy(profile)
        without_capability["capabilities"].remove("MESH_TO_STRUCTURE")
        without_capability["profile_sha256"] = self.profiles().profile_fingerprint(without_capability)
        self.assert_invalid_build(module, without_capability)

        rejected_input = copy.deepcopy(profile)
        rejected_input["handoff"]["accepted_input_kinds"].remove("MESH")
        rejected_input["profile_sha256"] = self.profiles().profile_fingerprint(rejected_input)
        self.assert_invalid_build(module, rejected_input)

        self.assert_invalid_build(module, profile, expected_output_kinds=[])
        self.assert_invalid_build(module, profile, expected_output_kinds=["LITEMATIC_FILE"])
        self.assert_invalid_build(module, profile, operation="SCHEMATIC_EXPORT")

    def test_manual_mode_requires_exactly_one_closed_manual_step(self):
        module = self.require_handoff()
        profile = self.operational_profile()
        request = self.build_request(module, profile)
        self.assertEqual(True, request["manual_step"]["required"])

        for mutate in (
            lambda step: step.__setitem__("unexpected", True),
            lambda step: step.pop("instruction"),
            lambda step: step.__setitem__("required", False),
            lambda step: step.__setitem__("step_id", ""),
            lambda step: step.__setitem__("expected_result", ""),
        ):
            candidate = copy.deepcopy(request)
            mutate(candidate["manual_step"])
            self.refresh_request_id(candidate)
            errors = module.validate_handoff_request(candidate, profile)
            self.assertTrue(errors, candidate)

        with self.assertRaises(C10Error) as raised:
            module.build_handoff_request(
                profile,
                operation="MESH_TO_STRUCTURE",
                text_input=None,
                input_artifacts=[self.artifact("MESH")],
                expected_output_kinds=["SCHEMATIC_FILE"],
                physical_modlist_sha256=PHYSICAL_SHA,
                manual_step=None,
            )
        self.assertEqual("INVALID_HANDOFF_REQUEST", raised.exception.code)

    def test_api_mode_requires_contract_proof_and_no_manual_step(self):
        module = self.require_handoff()
        proven = self.operational_profile(mode="API_ADAPTER", api_state="CONTRACT_PROVEN_API")
        request = self.build_request(module, proven, manual_step=None)
        self.assertIsNone(request["manual_step"])
        self.assertEqual([], module.validate_handoff_request(request, proven))

        smoke_proven = self.operational_profile(mode="API_ADAPTER", api_state="SMOKE_PROVEN_API")
        request = self.build_request(module, smoke_proven, manual_step=None)
        self.assertEqual([], module.validate_handoff_request(request, smoke_proven))

        merely_verified = self.operational_profile(mode="API_ADAPTER", api_state="VERIFIED_API")
        self.assert_invalid_build(module, merely_verified, manual_step=None)
        self.assert_invalid_build(module, proven, manual_step=self.manual_step())

    def test_profile_and_physical_drift_fail_closed(self):
        module = self.require_handoff()
        profile = self.operational_profile()
        request = self.build_request(module, profile)

        changed_profile = copy.deepcopy(profile)
        changed_profile["display_name"] += " changed"
        changed_profile["profile_sha256"] = self.profiles().profile_fingerprint(changed_profile)
        errors = module.validate_handoff_request(request, changed_profile)
        self.assertTrue(any("PROVIDER_DRIFT_DETECTED" in error for error in errors), errors)

        errors = module.validate_handoff_request(
            request,
            profile,
            current_physical_modlist_sha256=OTHER_PHYSICAL_SHA,
        )
        self.assertTrue(any("physical" in error.lower() or "stale" in error.lower() for error in errors), errors)

    def test_target_descriptor_shape_and_unknown_fields_fail_closed(self):
        module = self.require_handoff()
        profile = self.operational_profile()
        baseline = self.build_request(module, profile)
        self.assertEqual(
            {
                "minecraft": "1.21.1",
                "loader": "neoforge",
                "physical_modlist_sha256": PHYSICAL_SHA,
            },
            baseline["target"],
        )

        mutations = (
            lambda r: r.__setitem__("unexpected", True),
            lambda r: r["target"].__setitem__("unexpected", True),
            lambda r: r["target"].__setitem__("minecraft", "1.20.1"),
            lambda r: r["target"].__setitem__("loader", "forge"),
            lambda r: r["target"].__setitem__("physical_modlist_sha256", "bad"),
            lambda r: r["input_artifacts"][0].__setitem__("unexpected", True),
            lambda r: r["input_artifacts"][0].__setitem__("sha256", "bad"),
            lambda r: r["input_artifacts"][0].__setitem__("byte_length", 0),
            lambda r: r["input_artifacts"][0].__setitem__("media_type", ""),
        )
        for mutate in mutations:
            candidate = copy.deepcopy(baseline)
            mutate(candidate)
            self.refresh_request_id(candidate)
            self.assertTrue(module.validate_handoff_request(candidate, profile), candidate)

    def test_build_rejects_invalid_physical_modlist_digest(self):
        module = self.require_handoff()
        profile = self.operational_profile()
        with self.assertRaises(C10Error) as raised:
            module.build_handoff_request(
                profile,
                operation="MESH_TO_STRUCTURE",
                text_input=None,
                input_artifacts=[self.artifact("MESH")],
                expected_output_kinds=["SCHEMATIC_FILE"],
                physical_modlist_sha256="not-a-sha",
                manual_step=self.manual_step(),
            )
        self.assertEqual("INVALID_HANDOFF_REQUEST", raised.exception.code)


if __name__ == "__main__":
    unittest.main()
