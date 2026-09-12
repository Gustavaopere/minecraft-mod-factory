from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FAILURE = ROOT / "construction" / "fixtures" / "c10" / "blockgpt-smoke" / "failure.json"
REQUEST_ID = "c3b7eb8c50ef4df484193cbc1c723ee4ca4c26551373bd342b0aed1eb81dd256"
INPUT_SHA = "48d733bcb320b57417c7c507d514c5470092baf2c9671586d8ea6fd7d448af8e"


class ConstructionC10BlockGPTPaywallTest(unittest.TestCase):
    def test_blockgpt_manual_preview_failure_is_recorded(self):
        self.assertTrue(FAILURE.is_file(), "C10 RED: missing BlockGPT manual-smoke failure record")
        self.assertEqual(
            {
                "schema_version": 1,
                "provider_id": "blockgpt",
                "request_id": REQUEST_ID,
                "observed_at": "2026-09-12",
                "input_sha256": INPUT_SHA,
                "stage": "UPLOAD_PREVIEW",
                "outcome": "FAIL",
                "observation": (
                    "The exact reference.png was accepted by the official BlockGPT image-to-structure UI, "
                    "but starting generation required payment before any 3D preview was produced."
                ),
            },
            json.loads(FAILURE.read_text(encoding="utf-8")),
        )


if __name__ == "__main__":
    unittest.main()
