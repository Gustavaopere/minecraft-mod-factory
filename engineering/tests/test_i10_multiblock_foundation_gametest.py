import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GOLDEN = ROOT / "engineering/tests/golden/i10-multiblock-foundation"
OVERLAY = GOLDEN / "overlay"
GAME_TEST = OVERLAY / "src/main/java/dev/example/i10multiblock/gametest/I10MultiblockGameTests.java"
TEMPLATE_RELATIVE = "src/main/resources/data/i10_multiblock/structure/multiblock_test.nbt"
TEMPLATE = OVERLAY / TEMPLATE_RELATIVE
MANIFEST = GOLDEN / "manifest.json"
MATERIALIZER = ROOT / "engineering/tooling/multiblock-foundation/materialize_i10.py"
WORKFLOW = ROOT / ".github/workflows/factory-engineering-i10-multiblock-foundation.yml"
EXPECTED_TEMPLATE_SHA256 = "75b23fb80317d88bbde1a2aff7121cfd903b8a1010878e0327ce26fd4d3f1c99"

REQUIRED_METHODS = (
    "northFormation",
    "rotationEastSouth",
    "missingCasing",
    "blockedInterior",
    "wrongPortPosition",
    "invalidation",
    "repairAndReformation",
    "ioDelegation",
    "persistence",
    "staleBinding",
    "visualState",
)


class I10GameTestContract(unittest.TestCase):
    def test_native_gametest_source_declares_required_suite(self):
        self.assertTrue(GAME_TEST.is_file(), "I10 RED: I10MultiblockGameTests.java is missing")
        text = GAME_TEST.read_text(encoding="utf-8")
        for token in (
            "@GameTestHolder(I10MultiblockMod.MOD_ID)",
            "@PrefixGameTestTemplate(false)",
            '@GameTest(template = "multiblock_test"',
        ):
            self.assertIn(token, text)
        for method in REQUIRED_METHODS:
            self.assertIn(f"void {method}(GameTestHelper helper)", text, f"I10 RED: missing GameTest {method}")

    def test_suite_uses_canonical_rotation_capability_and_real_serialization_surfaces(self):
        self.assertTrue(GAME_TEST.is_file(), "I10 RED: I10MultiblockGameTests.java is missing")
        text = GAME_TEST.read_text(encoding="utf-8")
        for token in (
            "MultiblockPattern.worldPos(",
            "Capabilities.ItemHandler.BLOCK",
            "saveWithFullMetadata(helper.getLevel().registryAccess())",
            "BlockEntity.loadStatic(",
            "MultiblockRuntimeState.PENDING_REVALIDATION",
            "MultiblockControllerBlock.FORMED",
            "MultiblockPortBlock.FORMED",
        ):
            self.assertIn(token, text, f"I10 RED: GameTest suite missing proven runtime token {token!r}")
        self.assertNotIn("materialize_i9", text)
        self.assertNotIn("dev.example.i9machine", text)

    def test_native_template_is_pinned_byte_exact(self):
        self.assertTrue(TEMPLATE.is_file(), "I10 RED: native multiblock_test.nbt is missing")
        actual = hashlib.sha256(TEMPLATE.read_bytes()).hexdigest()
        self.assertEqual(EXPECTED_TEMPLATE_SHA256, actual, "I10 RED: native GameTest template drifted")

    def test_closed_composition_authority_pins_gametest_template(self):
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        matching = [
            item for item in manifest.get("files", [])
            if item.get("source") == TEMPLATE_RELATIVE and item.get("destination") == TEMPLATE_RELATIVE
        ]
        self.assertEqual(1, len(matching), "I10 RED: GameTest template mapping missing from closed manifest")
        self.assertEqual(EXPECTED_TEMPLATE_SHA256, matching[0].get("sha256"))

        materializer = MATERIALIZER.read_text(encoding="utf-8")
        for token in (
            f'GAMETEST_STRUCTURE_RELATIVE = "{TEMPLATE_RELATIVE}"',
            f'GAMETEST_STRUCTURE_SHA256 = "{EXPECTED_TEMPLATE_SHA256}"',
            "CANONICAL_FILE_SHA256",
            "hashlib.sha256",
            "I10 overlay source SHA-256 mismatch",
        ):
            self.assertIn(token, materializer, f"I10 RED: materializer does not pin template: {token}")

    def test_permanent_i10_workflow_runs_target_exact_gametest_server(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("engineering/tests/test_i10_multiblock_foundation_gametest.py", text)
        self.assertIn("./gradlew runGameTestServer --no-daemon", text)


if __name__ == "__main__":
    unittest.main()
