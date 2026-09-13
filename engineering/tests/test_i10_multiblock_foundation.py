from __future__ import annotations

import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
OVERLAY = REPO / "engineering/tests/golden/i10-multiblock-foundation/overlay"
JAVA_ROOT = OVERLAY / "src/main/java/dev/example/i10multiblock/multiblock"


class I10RuntimeSurfaceContract(unittest.TestCase):
    def test_required_runtime_surfaces_exist(self) -> None:
        required = [
            "I10MultiblockContent.java",
            "MultiblockPattern.java",
            "MultiblockValidationResult.java",
            "MultiblockRuntimeState.java",
            "MultiblockControllerBlock.java",
            "MultiblockControllerBlockEntity.java",
            "MultiblockPortBlock.java",
            "MultiblockPortBlockEntity.java",
        ]
        missing = [name for name in required if not (JAVA_ROOT / name).is_file()]
        self.assertEqual([], missing, f"missing I10 runtime surfaces: {missing}")

    def test_pattern_is_single_geometry_authority(self) -> None:
        pattern = JAVA_ROOT / "MultiblockPattern.java"
        self.assertTrue(pattern.is_file(), "MultiblockPattern.java must exist")
        text = pattern.read_text(encoding="utf-8")
        for token in ["-1", "0", "1", "2", "worldPos", "VALID", "INVALID", "UNAVAILABLE"]:
            self.assertIn(token, text)


if __name__ == "__main__":
    unittest.main()
