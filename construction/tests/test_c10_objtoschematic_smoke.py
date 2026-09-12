from __future__ import annotations

import json
import unittest
from pathlib import Path

from construction.providers.handoff import build_handoff_request, validate_handoff_request
from construction.providers.profiles import load_profile_catalog
from construction.providers.staging import artifact_descriptor_from_file

ROOT = Path(__file__).resolve().parents[2]
PROFILE_DIR = ROOT / "construction" / "providers" / "profiles"
UPSTREAM = ROOT / "construction" / "upstream" / "registry.json"
FIXTURE_RELPATH = "construction/fixtures/c10/objtoschematic-smoke/input.obj"
FIXTURE = ROOT / FIXTURE_RELPATH
REQUEST = ROOT / "construction" / "fixtures" / "c10" / "objtoschematic-smoke" / "request.json"
PHYSICAL_SHA = "7c0a23d6013101383d196526e4b6ba6940fb54a0fed10eaed5956ab015cfcc00"
MAX_INPUT_BYTES = 16_777_216
MAX_OUTPUT_BYTES = 67_108_864


class ConstructionC10ObjToSchematicSmokeTest(unittest.TestCase):
    def profile(self) -> dict[str, object]:
        upstream = json.loads(UPSTREAM.read_text(encoding="utf-8"))
        return load_profile_catalog(PROFILE_DIR, upstream)["objtoschematic"]

    def test_checked_in_profile_is_ep1_manual_mesh_handoff(self):
        profile = self.profile()
        self.assertEqual("EP1_HANDOFF_VERIFIED", profile["proof_level"])
        self.assertEqual("MANUAL_FILE_HANDOFF", profile["integration_mode"])
        self.assertEqual("UNVERIFIED_API", profile["api"]["state"])
        self.assertIsNone(profile["api"]["official_contract"])
        self.assertEqual(["MESH"], profile["handoff"]["accepted_input_kinds"])
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
            "capability:MESH_TO_STRUCTURE",
            "capability:SCHEMATIC_EXPORT",
            "handoff:MESH",
            "handoff:SCHEMATIC_FILE",
            "proof:EP1_HANDOFF_VERIFIED",
        ):
            self.assertIn(expected, supports)

    def test_checked_in_smoke_request_matches_factory_builder_exactly(self):
        self.assertTrue(FIXTURE.is_file(), f"C10 Task 8 RED: missing {FIXTURE_RELPATH}")
        self.assertTrue(
            REQUEST.is_file(),
            "C10 Task 8 RED: missing construction/fixtures/c10/objtoschematic-smoke/request.json",
        )

        profile = self.profile()
        descriptor = artifact_descriptor_from_file(
            ROOT,
            FIXTURE_RELPATH,
            kind="MESH",
            media_type="model/obj",
            max_bytes=MAX_INPUT_BYTES,
        )
        expected = build_handoff_request(
            profile,
            operation="MESH_TO_STRUCTURE",
            text_input=None,
            input_artifacts=[descriptor],
            expected_output_kinds=["SCHEMATIC_FILE"],
            physical_modlist_sha256=PHYSICAL_SHA,
            manual_step={
                "required": True,
                "step_id": "upload-mesh",
                "instruction": (
                    "Upload the exact Factory C10 input.obj fixture to ObjToSchematic "
                    "using the documented model-upload workflow."
                ),
                "expected_result": (
                    "ObjToSchematic displays a generated block preview derived from the uploaded fixture."
                ),
            },
        )
        checked_in = json.loads(REQUEST.read_text(encoding="utf-8"))
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
