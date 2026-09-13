from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CAPTURE_STATE_PATH = ROOT / "construction" / "fixtures" / "complex-modded-golden" / "capture-state.json"
STABILIZED_STATUS = "MODLIST_STABILIZED_AWAITING_RUNTIME_CAPTURE"
PHYSICAL_MODLIST_SHA256 = "7c0a23d6013101383d196526e4b6ba6940fb54a0fed10eaed5956ab015cfcc00"


class ConstructionC11ModlistStabilizationTransitionTest(unittest.TestCase):
    def test_capture_state_records_stabilized_modlist_and_runtime_capture_blocker(self) -> None:
        state = json.loads(CAPTURE_STATE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(STABILIZED_STATUS, state["status"])
        self.assertIs(True, state["blocks_c11_completion"])
        self.assertEqual(
            "physical modlist declared stable; runtime registry capture is still pending",
            state["reason"],
        )
        self.assertEqual(
            [
                "run the C4 registry probe on the stabilized modpack",
                "produce c11-runtime-snapshot.json",
                "compose and validate registry.json through C4",
            ],
            state["required_before_completion"],
        )
        self.assertEqual(
            PHYSICAL_MODLIST_SHA256,
            state["last_observed_physical_modlist_sha256"],
        )
        self.assertIs(False, state["requires_recapture_after_modlist_stabilizes"])


if __name__ == "__main__":
    unittest.main()
