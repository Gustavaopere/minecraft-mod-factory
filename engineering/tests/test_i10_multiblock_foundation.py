from __future__ import annotations

import json
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
OVERLAY = REPO / "engineering/tests/golden/i10-multiblock-foundation/overlay"
JAVA_ROOT = OVERLAY / "src/main/java/dev/example/i10multiblock/multiblock"
MOD_SPEC = REPO / "engineering/tests/fixtures/i10-multiblock-mod-spec.json"
SCAFFOLD_CONFIG = REPO / "engineering/tests/fixtures/i10-multiblock-scaffold-config.json"


class I10RuntimeSurfaceContract(unittest.TestCase):
    def test_i10_fixture_identity_is_target_exact(self) -> None:
        mod_spec = json.loads(MOD_SPEC.read_text(encoding="utf-8"))
        config = json.loads(SCAFFOLD_CONFIG.read_text(encoding="utf-8"))
        self.assertEqual(
            {
                "minecraft": "1.21.1",
                "loader": "neoforge",
                "neoforge": "21.1.248",
                "java": 21,
            },
            mod_spec["identity"]["target"],
        )
        self.assertEqual("i10_multiblock", mod_spec["identity"]["mod_id"])
        self.assertEqual("dev.example.i10multiblock", config["java_package"])
        self.assertEqual("I10MultiblockMod", config["main_class"])

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
        self.assertEqual([], missing, f"I10 RED: missing runtime surfaces: {missing}")

    def test_validation_and_runtime_state_enums_are_exact(self) -> None:
        validation = JAVA_ROOT / "MultiblockValidationResult.java"
        runtime = JAVA_ROOT / "MultiblockRuntimeState.java"
        self.assertTrue(validation.is_file(), "I10 RED: validation enum is missing")
        self.assertTrue(runtime.is_file(), "I10 RED: runtime-state enum is missing")
        validation_text = validation.read_text(encoding="utf-8")
        runtime_text = runtime.read_text(encoding="utf-8")
        for token in ("VALID", "INVALID", "UNAVAILABLE"):
            self.assertIn(token, validation_text)
        for token in ("UNFORMED", "PENDING_REVALIDATION", "FORMED"):
            self.assertIn(token, runtime_text)

    def test_pattern_is_single_geometry_and_rotation_authority(self) -> None:
        pattern = JAVA_ROOT / "MultiblockPattern.java"
        self.assertTrue(pattern.is_file(), "I10 RED: MultiblockPattern.java must exist")
        text = pattern.read_text(encoding="utf-8")
        required = (
            "MIN_X = -1",
            "MAX_X = 1",
            "MIN_Y = 0",
            "MAX_Y = 2",
            "MIN_Z = 0",
            "MAX_Z = 2",
            "CONTROLLER_LOCAL",
            "new BlockPos(0, 1, 0)",
            "PORT_LOCAL",
            "new BlockPos(0, 1, 2)",
            "INTERIOR_LOCAL",
            "new BlockPos(0, 1, 1)",
            "worldPos",
            "facing.getOpposite()",
            "facing.getClockWise()",
            "isHorizontal",
            "hasChunkAt",
            "MultiblockValidationResult.UNAVAILABLE",
            "MultiblockValidationResult.INVALID",
            "MultiblockValidationResult.VALID",
        )
        missing = [token for token in required if token not in text]
        self.assertEqual([], missing, f"I10 RED: canonical geometry/rotation contract incomplete: {missing}")
        self.assertNotIn("switch (facing)", text, "I10 must not duplicate four hard-coded rotated patterns")
        self.assertNotIn("switch(facing)", text, "I10 must not duplicate four hard-coded rotated patterns")

    def test_registry_surface_is_minimal_and_casing_has_no_block_entity(self) -> None:
        content = JAVA_ROOT / "I10MultiblockContent.java"
        self.assertTrue(content.is_file(), "I10 RED: I10MultiblockContent.java must exist")
        text = content.read_text(encoding="utf-8")
        required = (
            "DeferredRegister.createBlocks",
            "DeferredRegister.createItems",
            "Registries.BLOCK_ENTITY_TYPE",
            '"multiblock_controller"',
            '"multiblock_casing"',
            '"multiblock_io_port"',
            "MultiblockControllerBlockEntity::new",
            "MultiblockPortBlockEntity::new",
            "registerCapabilities",
        )
        missing = [token for token in required if token not in text]
        self.assertEqual([], missing, f"I10 RED: registry contract incomplete: {missing}")
        self.assertEqual(3, text.count("BLOCKS.registerBlock("), "I10 must register exactly three blocks")
        self.assertEqual(3, text.count("ITEMS.registerSimpleBlockItem("), "I10 must register exactly three block items")
        self.assertEqual(2, text.count('BLOCK_ENTITY_TYPES.register("'), "I10 must register only controller and port BEs")
        self.assertNotIn('BLOCK_ENTITY_TYPES.register("multiblock_casing"', text)

    def test_controller_owns_single_slot_and_persistent_formation_authority(self) -> None:
        source = JAVA_ROOT / "MultiblockControllerBlockEntity.java"
        text = source.read_text(encoding="utf-8")
        required = (
            "new ItemStackHandler(1)",
            "lastKnownFormed",
            "formationRevision",
            "MultiblockRuntimeState.UNFORMED",
            "MultiblockRuntimeState.PENDING_REVALIDATION",
            "MultiblockRuntimeState.FORMED",
            "markPendingRevalidation",
            "markFormed",
            "markUnformed",
            "runtimeState()",
            "formationRevision()",
            "itemHandler()",
            "loadAdditional",
            "saveAdditional",
            "serializeNBT",
            "deserializeNBT",
            "Math.max(0L",
        )
        missing = [token for token in required if token not in text]
        self.assertEqual([], missing, f"I10 RED: controller storage/persistence contract incomplete: {missing}")

    def test_controller_load_is_fail_closed_until_revalidation(self) -> None:
        source = JAVA_ROOT / "MultiblockControllerBlockEntity.java"
        text = source.read_text(encoding="utf-8")
        required = (
            "lastKnownFormed ? MultiblockRuntimeState.PENDING_REVALIDATION : MultiblockRuntimeState.UNFORMED",
            "formationRevision++",
            "lastKnownFormed = true",
            "lastKnownFormed = false",
        )
        missing = [token for token in required if token not in text]
        self.assertEqual([], missing, f"I10 RED: controller fail-closed lifecycle incomplete: {missing}")

    def test_port_binding_persists_position_revision_and_rejects_stale_links(self) -> None:
        source = JAVA_ROOT / "MultiblockPortBlockEntity.java"
        text = source.read_text(encoding="utf-8")
        required = (
            "controllerPos",
            "linkedRevision",
            "bindToController",
            "clearBinding",
            "linkedRevision <= 0",
            "level.hasChunkAt(controllerPos)",
            "instanceof MultiblockControllerBlockEntity controller",
            "controller.runtimeState() != MultiblockRuntimeState.FORMED",
            "controller.formationRevision() != linkedRevision",
            "return controller.itemHandler()",
            "BlockPos.of",
            ".asLong()",
            "loadAdditional",
            "saveAdditional",
        )
        missing = [token for token in required if token not in text]
        self.assertEqual([], missing, f"I10 RED: port binding/capability guard incomplete: {missing}")

    def test_item_capability_is_exposed_only_by_io_port(self) -> None:
        content = JAVA_ROOT / "I10MultiblockContent.java"
        text = content.read_text(encoding="utf-8")
        capability_body = text.split("public static void registerCapabilities", 1)[1]
        required = (
            "Capabilities.ItemHandler.BLOCK",
            "MULTIBLOCK_IO_PORT_BLOCK_ENTITY.get()",
            "blockEntity.itemHandler()",
        )
        missing = [token for token in required if token not in capability_body]
        self.assertEqual([], missing, f"I10 RED: IO-port capability registration incomplete: {missing}")
        self.assertEqual(1, capability_body.count("event.registerBlockEntity("))
        self.assertNotIn("MULTIBLOCK_CONTROLLER_BLOCK_ENTITY.get()", capability_body)

    def test_task5_visual_state_and_explicit_controller_interaction_contract(self) -> None:
        controller = (JAVA_ROOT / "MultiblockControllerBlock.java").read_text(encoding="utf-8")
        port = (JAVA_ROOT / "MultiblockPortBlock.java").read_text(encoding="utf-8")
        controller_required = (
            "HorizontalDirectionalBlock.FACING",
            'BooleanProperty.create("formed")',
            "getStateForPlacement",
            "createBlockStateDefinition",
            "useWithoutItem",
            "instanceof ServerLevel",
            "controller.tryForm",
            "protected void tick",
            "controller.revalidate",
        )
        port_required = (
            "HorizontalDirectionalBlock.FACING",
            'BooleanProperty.create("formed")',
            "createBlockStateDefinition",
        )
        missing = [f"controller:{token}" for token in controller_required if token not in controller]
        missing.extend(f"port:{token}" for token in port_required if token not in port)
        self.assertEqual([], missing, f"I10 RED: formed/facing interaction contract incomplete: {missing}")

    def test_task5_controller_formation_and_revalidation_are_fail_closed(self) -> None:
        source = (JAVA_ROOT / "MultiblockControllerBlockEntity.java").read_text(encoding="utf-8")
        required = (
            "tryForm(ServerLevel",
            "revalidate(ServerLevel",
            "MultiblockPattern.validate",
            "MultiblockValidationResult.VALID",
            "MultiblockValidationResult.INVALID",
            "MultiblockValidationResult.UNAVAILABLE",
            "MultiblockPattern.PORT_LOCAL",
            "bindToController",
            "markPendingRevalidation",
            "markRevalidatedFormed",
            "markUnformed",
            "setVisualFormed",
            "Block.UPDATE_CLIENTS",
            "level.invalidateCapabilities(portPos)",
        )
        missing = [token for token in required if token not in source]
        self.assertEqual([], missing, f"I10 RED: formation/revalidation lifecycle incomplete: {missing}")

    def test_task5_mutations_schedule_only_bounded_candidate_revalidation(self) -> None:
        invalidation = JAVA_ROOT / "MultiblockInvalidation.java"
        casing = JAVA_ROOT / "MultiblockCasingBlock.java"
        self.assertTrue(invalidation.is_file(), "I10 RED: MultiblockInvalidation.java is missing")
        self.assertTrue(casing.is_file(), "I10 RED: MultiblockCasingBlock.java is missing")
        if invalidation.is_file():
            text = invalidation.read_text(encoding="utf-8")
            required = (
                "Direction.Plane.HORIZONTAL",
                "MultiblockPattern.MIN_X",
                "MultiblockPattern.MAX_X",
                "MultiblockPattern.MIN_Y",
                "MultiblockPattern.MAX_Y",
                "MultiblockPattern.MIN_Z",
                "MultiblockPattern.MAX_Z",
                "changedPos.offset",
                "level.hasChunkAt",
                "MULTIBLOCK_CONTROLLER.get()",
                "level.scheduleTick",
            )
            missing = [token for token in required if token not in text]
            self.assertEqual([], missing, f"I10 RED: bounded invalidation helper incomplete: {missing}")
            self.assertNotIn("getAllEntities", text)
            self.assertNotIn("getChunkSource().force", text)
        if casing.is_file():
            text = casing.read_text(encoding="utf-8")
            for token in ("onPlace", "onRemove", "MultiblockInvalidation.scheduleAround"):
                self.assertIn(token, text)

    def test_task5_all_structure_blocks_participate_in_mutation_invalidation(self) -> None:
        for filename in ("MultiblockControllerBlock.java", "MultiblockPortBlock.java"):
            text = (JAVA_ROOT / filename).read_text(encoding="utf-8")
            missing = [token for token in ("onPlace", "onRemove", "MultiblockInvalidation.scheduleAround") if token not in text]
            self.assertEqual([], missing, f"I10 RED: {filename} mutation hooks incomplete: {missing}")
        content = (JAVA_ROOT / "I10MultiblockContent.java").read_text(encoding="utf-8")
        self.assertIn("MultiblockCasingBlock::new", content, "I10 casing must remain non-BE but participate in invalidation")


if __name__ == "__main__":
    unittest.main()
