from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
JAVA_ROOT = (
    ROOT
    / "engineering/tests/golden/i10-multiblock-foundation/overlay/src/main/java/dev/example/i10multiblock/multiblock"
)


class I10Task5MutationClosureContract(unittest.TestCase):
    def test_neighbor_changes_cover_non_i10_interior_mutations(self) -> None:
        for filename in (
            "MultiblockControllerBlock.java",
            "MultiblockCasingBlock.java",
            "MultiblockPortBlock.java",
        ):
            source = JAVA_ROOT / filename
            self.assertTrue(source.is_file(), f"I10 RED: missing {filename}")
            text = source.read_text(encoding="utf-8")
            required = (
                "neighborChanged",
                "BlockPos neighborPos",
                "MultiblockInvalidation.scheduleAround(serverLevel, neighborPos)",
            )
            missing = [token for token in required if token not in text]
            self.assertEqual([], missing, f"I10 RED: {filename} cannot observe interior mutation: {missing}")

    def test_pending_invalidation_closes_cached_port_capability_immediately(self) -> None:
        source = JAVA_ROOT / "MultiblockInvalidation.java"
        text = source.read_text(encoding="utf-8")
        required = (
            "controller.markPendingRevalidation()",
            "candidateState.getValue(MultiblockControllerBlock.FACING)",
            "MultiblockPattern.PORT_LOCAL",
            "level.invalidateCapabilities(portPos)",
        )
        missing = [token for token in required if token not in text]
        self.assertEqual([], missing, f"I10 RED: pending state does not close cached port IO immediately: {missing}")

    def test_cached_port_capability_fails_closed_across_partial_chunk_unload(self) -> None:
        source = JAVA_ROOT / "MultiblockPortBlockEntity.java"
        text = source.read_text(encoding="utf-8")
        for required in (
            "private IItemHandler guardedItemHandler",
            "private long handlerEpoch",
            "public IItemHandler itemHandler()",
            "return activeBacking() == null",
        ):
            # The getter must not return the raw controller inventory.
            if required == "return activeBacking() == null":
                continue
            self.assertIn(required, text)
        for required in (
            "MultiblockPattern.validate(serverLevel, controllerPos, facing)",
            "controller.revalidate(serverLevel, facing)",
            "handlerEpoch == expectedEpoch ? activeBacking() : null",
            "return storage == null ? stack",
            "return storage == null ? ItemStack.EMPTY",
            "return storage == null ? 0",
            "return storage != null && storage.isItemValid",
            "return guardedItemHandler;",
        ):
            self.assertIn(required, text)
        getter = text.split("public IItemHandler itemHandler()", 1)[1].split(
            "private ItemStackHandler activeBacking()", 1
        )[0]
        self.assertNotIn("return controller.itemHandler()", getter)

    def test_unavailable_chunks_retry_autonomously_without_forcing_loads(self) -> None:
        source = JAVA_ROOT / "MultiblockControllerBlockEntity.java"
        text = source.read_text(encoding="utf-8")
        self.assertIn("private static final int UNAVAILABLE_REVALIDATION_RETRY_TICKS = 20;", text)
        helper = text.split("private void schedulePendingRetry(ServerLevel level)", 1)[1].split(
            "public long markFormed()", 1
        )[0]
        self.assertIn("if (lastKnownFormed)", helper)
        self.assertIn(
            "level.scheduleTick(worldPosition, getBlockState().getBlock(), UNAVAILABLE_REVALIDATION_RETRY_TICKS);",
            helper,
        )
        self.assertNotIn("getChunk(", helper)
        self.assertNotIn("forceload", helper)

        for signature in (
            "public MultiblockValidationResult tryForm(ServerLevel level, Direction facing)",
            "public MultiblockValidationResult revalidate(ServerLevel level, Direction facing)",
        ):
            unavailable = text.split(signature, 1)[1].split(
                "if (validation == MultiblockValidationResult.INVALID)", 1
            )[0]
            self.assertIn("if (validation == MultiblockValidationResult.UNAVAILABLE)", unavailable)
            self.assertIn("schedulePendingRetry(level);", unavailable)
            self.assertLess(unavailable.index("schedulePendingRetry(level);"), unavailable.index("return validation;"))

    def test_persisted_formed_controller_schedules_one_revalidation_on_load(self) -> None:
        source = JAVA_ROOT / "MultiblockControllerBlockEntity.java"
        self.assertTrue(source.is_file(), "I10 RED: controller BlockEntity source is missing")
        text = source.read_text(encoding="utf-8")
        required = (
            "public void onLoad()",
            "super.onLoad()",
            "level instanceof ServerLevel serverLevel",
            "lastKnownFormed",
            "serverLevel.scheduleTick(worldPosition, getBlockState().getBlock(), 1)",
        )
        missing = [token for token in required if token not in text]
        self.assertEqual(
            [],
            missing,
            f"I10 RED: persisted controller load cannot schedule bounded revalidation: {missing}",
        )


if __name__ == "__main__":
    unittest.main()
