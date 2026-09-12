from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path

from construction.providers.errors import C10Error
from construction.providers.handoff import build_handoff_request
from construction.providers.profiles import load_profile_catalog, profile_fingerprint

ROOT = Path(__file__).resolve().parents[2]
PROVIDERS = ROOT / "construction" / "providers"
HANDOFF_MODULE = PROVIDERS / "handoff.py"
PROFILE_DIR = PROVIDERS / "profiles"
RECEIPT_SCHEMA = ROOT / "construction" / "schemas" / "provider-handoff-receipt.schema.json"
UPSTREAM = ROOT / "construction" / "upstream" / "registry.json"
VALID_SHA = "a" * 64
SECOND_SHA = "b" * 64
PHYSICAL_SHA = "7c0a23d6013101383d196526e4b6ba6940fb54a0fed10eaed5956ab015cfcc00"
RECEIPT_FUNCTIONS = (
    "build_handoff_receipt",
    "validate_handoff_receipt",
    "advance_validation_state",
)


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"unable to load {path.relative_to(ROOT)}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ConstructionC10HandoffReceiptTest(unittest.TestCase):
    def handoff_module(self):
        return load_module(HANDOFF_MODULE, "construction_c10_handoff_receipt")

    def require_receipt(self):
        module = self.handoff_module()
        missing = [name for name in RECEIPT_FUNCTIONS if not hasattr(module, name)]
        if missing or not RECEIPT_SCHEMA.is_file():
            self.skipTest("C10 receipt implementation intentionally absent during RED")
        return module

    def upstream_registry(self):
        return json.loads(UPSTREAM.read_text(encoding="utf-8"))

    def operational_profile(self):
        profile = copy.deepcopy(
            load_profile_catalog(PROFILE_DIR, self.upstream_registry())["objtoschematic"]
        )
        profile["proof_level"] = "EP1_HANDOFF_VERIFIED"
        profile["integration_mode"] = "MANUAL_FILE_HANDOFF"
        profile["capabilities"] = ["MESH_TO_STRUCTURE"]
        profile["handoff"] = {
            "accepted_input_kinds": ["MESH"],
            "output_artifact_kinds": ["SCHEMATIC_FILE"],
            "manual_action_required": True,
            "determinism": "UNKNOWN",
        }
        profile["limits"] = {
            "max_input_bytes": 1_000_000,
            "max_output_bytes": 2_000_000,
            "timeout_seconds": None,
        }
        profile["profile_sha256"] = profile_fingerprint(profile)
        return profile

    @staticmethod
    def artifact(
        *,
        kind: str = "SCHEMATIC_FILE",
        sha256: str = VALID_SHA,
        repo_relpath: str | None = "construction/fixtures/c10/task4/output.schem",
    ) -> dict[str, object]:
        return {
            "kind": kind,
            "sha256": sha256,
            "byte_length": 321,
            "media_type": "application/octet-stream",
            "repo_relpath": repo_relpath,
        }

    @staticmethod
    def input_artifact() -> dict[str, object]:
        return {
            "kind": "MESH",
            "sha256": SECOND_SHA,
            "byte_length": 123,
            "media_type": "application/octet-stream",
            "repo_relpath": "construction/fixtures/c10/task4/input.obj",
        }

    @staticmethod
    def manual_step() -> dict[str, object]:
        return {
            "required": True,
            "step_id": "submit-input",
            "instruction": "Upload the Factory-owned mesh fixture to the provider editor.",
            "expected_result": "The provider shows a generated block preview.",
        }

    def request(self, profile):
        return build_handoff_request(
            profile,
            operation="MESH_TO_STRUCTURE",
            text_input=None,
            input_artifacts=[self.input_artifact()],
            expected_output_kinds=["SCHEMATIC_FILE"],
            physical_modlist_sha256=PHYSICAL_SHA,
            manual_step=self.manual_step(),
        )

    @staticmethod
    def validator(
        stage: str,
        *,
        artifact_sha256: str = VALID_SHA,
        result: str = "PASS",
        authority: str | None = None,
    ) -> dict[str, object]:
        default_authority = {
            "FORMAT": "construction.core.sponge_v3.validate_sponge_v3",
            "NORMALIZE": "construction.providers.normalizer",
            "GOLDEN": "construction.providers.golden_gate",
        }[stage]
        return {
            "stage": stage,
            "authority": authority or default_authority,
            "artifact_sha256": artifact_sha256,
            "result": result,
            "evidence_ref": f"repo://construction/fixtures/c10/task4/{stage.lower()}-{artifact_sha256[:8]}.json",
        }

    def baseline_receipt(self, module, profile=None):
        if profile is None:
            profile = self.operational_profile()
        request = self.request(profile)
        receipt = module.build_handoff_receipt(
            request,
            profile,
            received_artifacts=[self.artifact()],
        )
        return profile, request, receipt

    def test_required_task4_contract_exists(self):
        module = self.handoff_module()
        missing = []
        if not RECEIPT_SCHEMA.is_file():
            missing.append(str(RECEIPT_SCHEMA.relative_to(ROOT)))
        missing.extend(name for name in RECEIPT_FUNCTIONS if not hasattr(module, name))
        self.assertEqual([], missing, f"C10 Task 4 RED: missing receipt contract: {missing}")

    def test_receipt_schema_is_closed(self):
        self.require_receipt()
        schema = json.loads(RECEIPT_SCHEMA.read_text(encoding="utf-8"))
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(1, schema["properties"]["schema_version"]["const"])
        provider_metadata = schema["properties"]["provider_metadata"]
        self.assertFalse(provider_metadata["additionalProperties"])
        self.assertEqual({}, provider_metadata.get("properties", {}))
        validation = schema["properties"]["factory_validation"]
        self.assertFalse(validation["additionalProperties"])
        self.assertEqual(
            {"UNVALIDATED", "FORMAT_VALIDATED", "FACTORY_NORMALIZED", "GOLDEN_ACCEPTED"},
            set(validation["properties"]["state"]["enum"]),
        )
        validator = validation["properties"]["validators"]["items"]
        self.assertFalse(validator["additionalProperties"])
        self.assertEqual({"FORMAT", "NORMALIZE", "GOLDEN"}, set(validator["properties"]["stage"]["enum"]))
        self.assertEqual({"PASS", "FAIL"}, set(validator["properties"]["result"]["enum"]))

    def test_receipt_id_is_deterministic_and_tamper_evident(self):
        module = self.require_receipt()
        profile = self.operational_profile()
        request = self.request(profile)
        first = module.build_handoff_receipt(request, profile, received_artifacts=[self.artifact()])
        second = module.build_handoff_receipt(request, profile, received_artifacts=[self.artifact()])
        self.assertEqual(first, second)
        self.assertRegex(first["receipt_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual([], module.validate_handoff_receipt(first, request, profile))

        tampered = copy.deepcopy(first)
        tampered["received_artifacts"][0]["byte_length"] += 1
        errors = module.validate_handoff_receipt(tampered, request, profile)
        self.assertTrue(any("receipt_sha256" in error for error in errors), errors)

    def test_receipt_identity_must_match_request_and_current_profile(self):
        module = self.require_receipt()
        profile, request, receipt = self.baseline_receipt(module)
        mutations = (
            ("request_id", "0" * 64),
            ("provider_id", "structmatic"),
            ("mode", "API_ADAPTER"),
            ("provider_profile_sha256", "1" * 64),
        )
        for field, value in mutations:
            with self.subTest(field=field):
                candidate = copy.deepcopy(receipt)
                candidate[field] = value
                errors = module.validate_handoff_receipt(candidate, request, profile)
                self.assertTrue(errors, candidate)

        changed_profile = copy.deepcopy(profile)
        changed_profile["display_name"] += " drift"
        changed_profile["profile_sha256"] = profile_fingerprint(changed_profile)
        errors = module.validate_handoff_receipt(receipt, request, changed_profile)
        self.assertTrue(any("PROVIDER_DRIFT_DETECTED" in error for error in errors), errors)

    def test_expected_output_kinds_constrain_received_artifacts(self):
        module = self.require_receipt()
        profile = self.operational_profile()
        request = self.request(profile)
        with self.assertRaises(C10Error) as raised:
            module.build_handoff_receipt(
                request,
                profile,
                received_artifacts=[self.artifact(kind="LITEMATIC_FILE")],
            )
        self.assertEqual("INVALID_HANDOFF_RECEIPT", raised.exception.code)

    def test_provider_metadata_must_be_exactly_empty(self):
        module = self.require_receipt()
        profile, request, receipt = self.baseline_receipt(module)
        candidate = copy.deepcopy(receipt)
        candidate["provider_metadata"] = {"provider_filename": "output.schem"}
        errors = module.validate_handoff_receipt(candidate, request, profile)
        self.assertTrue(any("provider_metadata" in error for error in errors), errors)

    def test_received_artifact_shape_fails_closed(self):
        module = self.require_receipt()
        profile, request, receipt = self.baseline_receipt(module)
        mutations = (
            lambda a: a.__setitem__("unexpected", True),
            lambda a: a.__setitem__("kind", "UNKNOWN"),
            lambda a: a.__setitem__("sha256", "bad"),
            lambda a: a.__setitem__("byte_length", 0),
            lambda a: a.__setitem__("media_type", ""),
            lambda a: a.__setitem__("repo_relpath", "/tmp/provider-output.schem"),
        )
        for mutate in mutations:
            candidate = copy.deepcopy(receipt)
            mutate(candidate["received_artifacts"][0])
            with self.subTest(candidate=candidate["received_artifacts"][0]):
                self.assertTrue(module.validate_handoff_receipt(candidate, request, profile))

    def test_format_validation_requires_pass_for_every_received_artifact(self):
        module = self.require_receipt()
        profile = self.operational_profile()
        request = self.request(profile)
        receipt = module.build_handoff_receipt(
            request,
            profile,
            received_artifacts=[
                self.artifact(sha256=VALID_SHA, repo_relpath="construction/fixtures/c10/task4/a.schem"),
                self.artifact(sha256=SECOND_SHA, repo_relpath="construction/fixtures/c10/task4/b.schem"),
            ],
        )
        with self.assertRaisesRegex(ValueError, "FORMAT"):
            module.advance_validation_state(
                receipt,
                "FORMAT_VALIDATED",
                [self.validator("FORMAT", artifact_sha256=VALID_SHA)],
            )

        advanced = module.advance_validation_state(
            receipt,
            "FORMAT_VALIDATED",
            [
                self.validator("FORMAT", artifact_sha256=SECOND_SHA, authority="z.validator"),
                self.validator("FORMAT", artifact_sha256=VALID_SHA, authority="a.validator"),
            ],
        )
        self.assertEqual("FORMAT_VALIDATED", advanced["factory_validation"]["state"])
        self.assertEqual("UNVALIDATED", receipt["factory_validation"]["state"])
        self.assertEqual([], receipt["factory_validation"]["validators"])
        self.assertEqual(
            sorted(advanced["factory_validation"]["validators"], key=lambda value: (value["stage"], value["authority"], value["artifact_sha256"], value["evidence_ref"])),
            advanced["factory_validation"]["validators"],
        )

    def test_validation_state_advances_monotonically_without_skips(self):
        module = self.require_receipt()
        _, _, receipt = self.baseline_receipt(module)

        with self.assertRaisesRegex(ValueError, "FORMAT"):
            module.advance_validation_state(receipt, "FORMAT_VALIDATED", [])
        with self.assertRaisesRegex(ValueError, "FORMAT"):
            module.advance_validation_state(
                receipt,
                "FORMAT_VALIDATED",
                [self.validator("FORMAT", result="FAIL")],
            )
        with self.assertRaisesRegex(ValueError, "skip|FORMAT_VALIDATED"):
            module.advance_validation_state(
                receipt,
                "FACTORY_NORMALIZED",
                [self.validator("NORMALIZE")],
            )

        formatted = module.advance_validation_state(
            receipt,
            "FORMAT_VALIDATED",
            [self.validator("FORMAT")],
        )
        with self.assertRaisesRegex(ValueError, "NORMALIZE"):
            module.advance_validation_state(formatted, "FACTORY_NORMALIZED", [])
        normalized = module.advance_validation_state(
            formatted,
            "FACTORY_NORMALIZED",
            [self.validator("NORMALIZE")],
        )
        with self.assertRaisesRegex(ValueError, "GOLDEN"):
            module.advance_validation_state(normalized, "GOLDEN_ACCEPTED", [])
        golden = module.advance_validation_state(
            normalized,
            "GOLDEN_ACCEPTED",
            [self.validator("GOLDEN")],
        )
        self.assertEqual("GOLDEN_ACCEPTED", golden["factory_validation"]["state"])
        self.assertEqual(3, len(golden["factory_validation"]["validators"]))
        self.assertNotEqual(receipt["receipt_sha256"], formatted["receipt_sha256"])
        self.assertNotEqual(formatted["receipt_sha256"], normalized["receipt_sha256"])
        self.assertNotEqual(normalized["receipt_sha256"], golden["receipt_sha256"])

    def test_validator_records_are_closed_and_bound_to_received_artifacts(self):
        module = self.require_receipt()
        _, _, receipt = self.baseline_receipt(module)
        invalid_records = (
            {**self.validator("FORMAT"), "unexpected": True},
            {**self.validator("FORMAT"), "stage": "UNKNOWN"},
            {**self.validator("FORMAT"), "artifact_sha256": SECOND_SHA},
            {**self.validator("FORMAT"), "result": "MAYBE"},
            {**self.validator("FORMAT"), "authority": ""},
            {**self.validator("FORMAT"), "evidence_ref": "https://example.invalid/evidence"},
        )
        for record in invalid_records:
            with self.subTest(record=record):
                with self.assertRaises(ValueError):
                    module.advance_validation_state(receipt, "FORMAT_VALIDATED", [record])


if __name__ == "__main__":
    unittest.main()
