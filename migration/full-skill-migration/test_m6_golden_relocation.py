#!/usr/bin/env python3
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GOLDEN = ROOT / "art/golden-samples"


class M6GoldenRelocationTest(unittest.TestCase):
    def test_golden_validators_resolve_relocated_factory_tooling(self) -> None:
        golden_validator = (GOLDEN / "validate_golden_samples.js").read_text(encoding="utf-8")
        self.assertIn("require('../tooling/blockbench/asset-toolkit/asset_toolkit.js')", golden_validator)
        self.assertNotIn("require('../art/", golden_validator)

        evidence_validator = (GOLDEN / "validate_reference_evidence.js").read_text(encoding="utf-8")
        self.assertIn("require('../tooling/validators/validate_golden_reference_rendered_edges.js')", evidence_validator)
        self.assertNotIn("require('../scripts/", evidence_validator)


if __name__ == "__main__":
    unittest.main()
