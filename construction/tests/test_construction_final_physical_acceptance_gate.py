from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STATE_PATH = ROOT / "construction" / "fixtures" / "complex-modded-golden" / "capture-state.json"
STATUS_PATH = ROOT / "construction" / "STATUS.md"
FINAL_BLOCKER = "SUPER_HYPER_URGENT_FINAL_CONSTRUCTION_PHYSICAL_ACCEPTANCE"
HISTORICAL_MODLIST_SHA256 = "7c0a23d6013101383d196526e4b6ba6940fb54a0fed10eaed5956ab015cfcc00"


class ConstructionFinalPhysicalAcceptanceGateTest(unittest.TestCase):
    def test_state_blocks_all_final_acceptance_surfaces(self) -> None:
        state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(FINAL_BLOCKER, state["status"])
        self.assertIs(True, state["blocks_c11_completion"])
        self.assertIs(True, state["blocks_c12_acceptance"])
        self.assertIs(True, state["blocks_c13_final_acceptance"])
        self.assertIs(True, state["blocks_construction_final_acceptance"])
        self.assertEqual(HISTORICAL_MODLIST_SHA256, state["last_observed_physical_modlist_sha256"])
        self.assertIs(True, state["final_gate_requires_fresh_physical_modlist_rehash"])
        self.assertIs(True, state["final_gate_requires_fresh_c4_runtime_capture"])

    def test_status_remains_last_completed_construction_phase(self) -> None:
        status = STATUS_PATH.read_text(encoding="utf-8")
        self.assertIn("PHASE=C10_COMPLETE_POSTMERGE_VALIDATED", status)
        self.assertNotIn("PHASE=C11_", status)
        self.assertNotIn("PHASE=C12_", status)
        self.assertNotIn("PHASE=C13_", status)


if __name__ == "__main__":
    unittest.main()
