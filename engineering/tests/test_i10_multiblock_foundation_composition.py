from __future__ import annotations

import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
MATERIALIZER = REPO / "engineering/tooling/multiblock-foundation/materialize_i10.py"
GOLDEN = REPO / "engineering/tests/golden/i10-multiblock-foundation"
SPEC = REPO / "docs/superpowers/specs/2026-09-13-i10-multiblock-foundation-reference-design.md"
PLAN = REPO / "docs/superpowers/plans/2026-09-13-i10-multiblock-foundation-reference.md"


class I10CompositionContract(unittest.TestCase):
    def test_design_and_plan_exist(self) -> None:
        self.assertTrue(SPEC.is_file())
        self.assertTrue(PLAN.is_file())

    def test_composition_authority_exists(self) -> None:
        self.assertTrue(MATERIALIZER.is_file(), "I10 materializer must exist")
        self.assertTrue((GOLDEN / "manifest.json").is_file(), "I10 manifest must exist")
        self.assertTrue((GOLDEN / "overlay").is_dir(), "I10 overlay must exist")

    def test_i10_is_independent_from_i9_runtime(self) -> None:
        candidates = [MATERIALIZER, GOLDEN / "manifest.json"]
        text = "\n".join(path.read_text(encoding="utf-8") for path in candidates if path.is_file())
        self.assertNotIn("materialize_i9", text)
        self.assertNotIn("i9-machine-foundation", text)
        self.assertNotIn("dev.example.i9machine", text)


if __name__ == "__main__":
    unittest.main()
