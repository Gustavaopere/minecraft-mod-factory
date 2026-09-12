from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from construction.providers.handoff import build_handoff_request, validate_handoff_request
from construction.providers.profiles import load_profile_catalog
from construction.providers.staging import artifact_descriptor_from_file

ROOT = Path(__file__).resolve().parents[2]
PROFILE_DIR = ROOT / "construction" / "providers" / "profiles"
UPSTREAM = ROOT / "construction" / "upstream" / "registry.json"
FIXTURE_RELPATH = "construction/fixtures/c10/blockgpt-smoke/reference.png"
FIXTURE = ROOT / FIXTURE_RELPATH
REQUEST = ROOT / "construction" / "fixtures" / "c10" / "blockgpt-smoke" / "request.json"
OBJ_FAILURE = ROOT / "construction" / "fixtures" / "c10" / "objtoschematic-smoke" / "failure.json"
PHYSICAL_SHA = "7c0a23d6013101383d196526e4b6ba6940fb54a0fed10eaed5956ab015cfcc00"
REFERENCE_SHA = "48d733bcb320b57417c7c507d514c5470092baf2c9671586d8ea6fd7d448af8e"
OBJ_INPUT_SHA = "b6101561fb2594ce731ea8ecb02c0d25862ca24abdd776cfe10cac2fe088c4a9"
OBJ_REQUEST_ID = "4ee4be7e0d3d89b0690aeb2da3794f28689dad61a246be873e7194b140d021de"
PROMPT = (
    "Generate a plain solid cube that matches the uploaded reference image, using basic full "
    "Minecraft blocks only, with no decorations or surrounding terrain."
)
MAX_INPUT_BYTES = 16_777_216
MAX_OUTPUT_BYTES = 67_108_864


class ConstructionC10BlockGPTSmokeTest(unittest.TestCase):
    def profile(self) -> dict[str, object]:
        upstream = json.loads(UPSTREAM.read_text(encoding="utf-8"))
        return load_profile_catalog(PROFILE_DIR, upstream)["blockgpt"]

    def test_objtoschematic_failed_manual_preview_is_recorded(self):
        self.assertTrue(
            OBJ_FAILURE.is_file(),
            "C10 fallback RED: missing ObjToSchematic manual-smoke failure record",
        )
        failure = json.loads(OBJ_FAILURE.read_text(encoding="utf-8"))
        self.assertEqual(
            {
                "schema_version": 1,
                "provider_id": "objtoschematic",
                "request_id": OBJ_REQUEST_ID,
                "observed_at": "2026-09-12",
                "input_sha256": OBJ_INPUT_SHA,
                "stage": "UPLOAD_PREVIEW",
                "outcome": "FAIL",
                "observation": (
                    "The exact input.obj was selected in the official ObjToSchematic editor, "
                    "but the Import control remained disabled and no block preview appeared."
                ),
            },
            failure,
        )

    def test_checked_in_profile_is_ep1_manual_image_handoff(self):
        profile = self.profile()
        self.assertEqual("EP1_HANDOFF_VERIFIED", profile["proof_level"])
        self.assertEqual("MANUAL_FILE_HANDOFF", profile["integration_mode"])
        self.assertEqual("UNVERIFIED_API", profile["api"]["state"])
        self.assertIsNone(profile["api"]["official_contract"])
        self.assertIn("IMAGE_TO_STRUCTURE", profile["capabilities"])
        self.assertEqual(["IMAGE"], profile["handoff"]["accepted_input_kinds"])
        self.assertEqual(["SCHEMATIC_FILE"], profile["handoff"]["output_artifact_kinds"])
        self.assertIs(profile["handoff"]["manual_action_required"], True)
        self.assertEqual("UNKNOWN", profile["handoff"]["determinism"])
        self.assertEqual(MAX_INPUT_BYTES, profile["limits"]["max_input_bytes"])
        self.assertEqual(MAX_OUTPUT_BYTES, profile["limits"]["max_output_bytes"])
        self.assertIsNone(profile["limits"]["timeout_seconds"])

        supports = {
            support
            for evidence in profile["audit"]["evidence"]
            for support in evidence["supports"]
        }
        for expected in (
            "capability:IMAGE_TO_STRUCTURE",
            "capability:SCHEMATIC_EXPORT",
            "handoff:IMAGE",
            "handoff:SCHEMATIC_FILE",
            "proof:EP1_HANDOFF_VERIFIED",
        ):
            self.assertIn(expected, supports)

    def test_checked_in_reference_and_request_match_factory_builder_exactly(self):
        self.assertTrue(FIXTURE.is_file(), f"C10 fallback RED: missing {FIXTURE_RELPATH}")
        self.assertEqual(REFERENCE_SHA, hashlib.sha256(FIXTURE.read_bytes()).hexdigest())
        self.assertTrue(
            REQUEST.is_file(),
            "C10 fallback RED: missing construction/fixtures/c10/blockgpt-smoke/request.json",
        )

        profile = self.profile()
        descriptor = artifact_descriptor_from_file(
            ROOT,
            FIXTURE_RELPATH,
            kind="IMAGE",
            media_type="image/png",
            max_bytes=MAX_INPUT_BYTES,
        )
        expected = build_handoff_request(
            profile,
            operation="IMAGE_TO_STRUCTURE",
            text_input=PROMPT,
            input_artifacts=[descriptor],
            expected_output_kinds=["SCHEMATIC_FILE"],
            physical_modlist_sha256=PHYSICAL_SHA,
            manual_step={
                "required": True,
                "step_id": "submit-reference-image",
                "instruction": (
                    "Upload the exact Factory C10 reference.png fixture to BlockGPT, paste the exact "
                    "Factory prompt recorded in text_input, and start one image-to-build generation."
                ),
                "expected_result": (
                    "BlockGPT displays a 3D preview of a generated Minecraft structure derived from "
                    "the uploaded reference image and exact Factory prompt."
                ),
            },
        )
        checked_in = json.loads(REQUEST.read_text(encoding="utf-8"))
        self.assertEqual(PROMPT, checked_in["text_input"])
        self.assertEqual(expected, checked_in)
        self.assertEqual(
            [],
            validate_handoff_request(
                checked_in,
                profile,
                current_physical_modlist_sha256=PHYSICAL_SHA,
            ),
        )


if __name__ == "__main__":
    unittest.main()
