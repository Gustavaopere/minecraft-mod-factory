package dev.example.i10multiblock.gametest;

import dev.example.i10multiblock.I10MultiblockMod;
import dev.example.i10multiblock.multiblock.I10MultiblockContent;
import dev.example.i10multiblock.multiblock.MultiblockControllerBlock;
import dev.example.i10multiblock.multiblock.MultiblockControllerBlockEntity;
import dev.example.i10multiblock.multiblock.MultiblockPattern;
import dev.example.i10multiblock.multiblock.MultiblockPortBlock;
import dev.example.i10multiblock.multiblock.MultiblockPortBlockEntity;
import dev.example.i10multiblock.multiblock.MultiblockRuntimeState;
import dev.example.i10multiblock.multiblock.MultiblockValidationResult;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.neoforge.capabilities.Capabilities;
import net.neoforged.neoforge.gametest.GameTestHolder;
import net.neoforged.neoforge.gametest.PrefixGameTestTemplate;
import net.neoforged.neoforge.items.IItemHandler;

@GameTestHolder(I10MultiblockMod.MOD_ID)
@PrefixGameTestTemplate(false)
public final class I10MultiblockGameTests {
    private static final BlockPos REQUIRED_CASING_LOCAL = new BlockPos(-1, 0, 0);
    private static final BlockPos WRONG_PORT_LOCAL = new BlockPos(-1, 1, 2);

    private I10MultiblockGameTests() {
    }

    @GameTest(template = "multiblock_test", timeoutTicks = 160)
    public static void northFormation(GameTestHelper helper) {
        Direction facing = Direction.NORTH;
        MultiblockControllerBlockEntity controller = buildStructure(helper, facing);
        MultiblockValidationResult result = controller.tryForm(helper.getLevel(), facing);
        require(result == MultiblockValidationResult.VALID, helper, facing, "North formation must validate");
        require(controller.runtimeState() == MultiblockRuntimeState.FORMED, helper, facing, "North controller must be formed");
        require(controller.formationRevision() == 1L, helper, facing, "First formation must create revision 1");
        MultiblockPortBlockEntity port = requirePort(helper, facing);
        require(port.controllerPos().equals(controller.getBlockPos()), helper, facing, "Rear port must link to controller");
        require(port.linkedRevision() == controller.formationRevision(), helper, facing, "Rear port revision must match controller");
        helper.succeed();
    }

    @GameTest(template = "multiblock_test", timeoutTicks = 160)
    public static void rotationEastSouth(GameTestHelper helper) {
        Direction east = Direction.EAST;
        MultiblockControllerBlockEntity eastController = buildStructure(helper, east);
        require(eastController.tryForm(helper.getLevel(), east) == MultiblockValidationResult.VALID,
                helper, east, "East formation must validate through canonical transform");
        require(eastController.runtimeState() == MultiblockRuntimeState.FORMED,
                helper, east, "East controller must be formed");

        clearStructure(helper, east);

        Direction south = Direction.SOUTH;
        MultiblockControllerBlockEntity southController = buildStructure(helper, south);
        require(southController.tryForm(helper.getLevel(), south) == MultiblockValidationResult.VALID,
                helper, south, "South formation must validate through canonical transform");
        require(southController.runtimeState() == MultiblockRuntimeState.FORMED,
                helper, south, "South controller must be formed");
        helper.succeed();
    }

    @GameTest(template = "multiblock_test", timeoutTicks = 160)
    public static void missingCasing(GameTestHelper helper) {
        Direction facing = Direction.NORTH;
        MultiblockControllerBlockEntity controller = buildStructure(helper, facing);
        setLocal(helper, facing, REQUIRED_CASING_LOCAL, Blocks.AIR.defaultBlockState());
        require(controller.tryForm(helper.getLevel(), facing) == MultiblockValidationResult.INVALID,
                helper, facing, "Missing casing must prevent formation");
        require(controller.runtimeState() == MultiblockRuntimeState.UNFORMED,
                helper, facing, "Invalid structure must remain unformed");
        helper.succeed();
    }

    @GameTest(template = "multiblock_test", timeoutTicks = 160)
    public static void blockedInterior(GameTestHelper helper) {
        Direction facing = Direction.NORTH;
        MultiblockControllerBlockEntity controller = buildStructure(helper, facing);
        setLocal(helper, facing, MultiblockPattern.INTERIOR_LOCAL, Blocks.STONE.defaultBlockState());
        require(controller.tryForm(helper.getLevel(), facing) == MultiblockValidationResult.INVALID,
                helper, facing, "Blocked interior must prevent formation");
        require(controller.runtimeState() == MultiblockRuntimeState.UNFORMED,
                helper, facing, "Blocked interior must remain unformed");
        helper.succeed();
    }

    @GameTest(template = "multiblock_test", timeoutTicks = 160)
    public static void wrongPortPosition(GameTestHelper helper) {
        Direction facing = Direction.NORTH;
        MultiblockControllerBlockEntity controller = buildStructure(helper, facing);
        setLocal(helper, facing, MultiblockPattern.PORT_LOCAL,
                I10MultiblockContent.MULTIBLOCK_CASING.get().defaultBlockState());
        setLocal(helper, facing, WRONG_PORT_LOCAL,
                I10MultiblockContent.MULTIBLOCK_IO_PORT.get().defaultBlockState()
                        .setValue(MultiblockPortBlock.FACING, facing)
                        .setValue(MultiblockPortBlock.FORMED, false));
        require(controller.tryForm(helper.getLevel(), facing) == MultiblockValidationResult.INVALID,
                helper, facing, "Port at the wrong local role must prevent formation");
        helper.succeed();
    }

    @GameTest(template = "multiblock_test", timeoutTicks = 160)
    public static void invalidation(GameTestHelper helper) {
        Direction facing = Direction.NORTH;
        MultiblockControllerBlockEntity controller = buildStructure(helper, facing);
        require(controller.tryForm(helper.getLevel(), facing) == MultiblockValidationResult.VALID,
                helper, facing, "Precondition formation failed");
        requireItemCapability(helper, facing);

        setLocal(helper, facing, REQUIRED_CASING_LOCAL, Blocks.AIR.defaultBlockState());
        require(controller.runtimeState() == MultiblockRuntimeState.PENDING_REVALIDATION,
                helper, facing, "Mutation must close operation immediately by entering pending");
        require(itemCapability(helper, facing) == null,
                helper, facing, "Port capability must disappear immediately while pending");

        helper.runAtTickTime(3, () -> {
            require(controller.runtimeState() == MultiblockRuntimeState.UNFORMED,
                    helper, facing, "Scheduled bounded revalidation must dissolve invalid structure");
            require(MultiblockPattern.validate(helper.getLevel(), controller.getBlockPos(), facing)
                            == MultiblockValidationResult.INVALID,
                    helper, facing, "Broken structure must validate INVALID");
            helper.succeed();
        });
    }

    @GameTest(template = "multiblock_test", timeoutTicks = 160)
    public static void repairAndReformation(GameTestHelper helper) {
        Direction facing = Direction.NORTH;
        MultiblockControllerBlockEntity controller = buildStructure(helper, facing);
        require(controller.tryForm(helper.getLevel(), facing) == MultiblockValidationResult.VALID,
                helper, facing, "Initial formation failed");
        long firstRevision = controller.formationRevision();

        setLocal(helper, facing, REQUIRED_CASING_LOCAL, Blocks.AIR.defaultBlockState());
        require(controller.revalidate(helper.getLevel(), facing) == MultiblockValidationResult.INVALID,
                helper, facing, "Broken structure must dissolve on revalidation");
        setLocal(helper, facing, REQUIRED_CASING_LOCAL,
                I10MultiblockContent.MULTIBLOCK_CASING.get().defaultBlockState());
        require(controller.runtimeState() == MultiblockRuntimeState.UNFORMED,
                helper, facing, "Repair alone must not auto-form the structure");
        require(controller.tryForm(helper.getLevel(), facing) == MultiblockValidationResult.VALID,
                helper, facing, "Explicit reformation must succeed after repair");
        require(controller.formationRevision() == firstRevision + 1L,
                helper, facing, "Explicit reformation must advance revision exactly once");
        helper.succeed();
    }

    @GameTest(template = "multiblock_test", timeoutTicks = 160)
    public static void ioDelegation(GameTestHelper helper) {
        Direction facing = Direction.NORTH;
        MultiblockControllerBlockEntity controller = buildStructure(helper, facing);
        require(itemCapability(helper, facing) == null,
                helper, facing, "Unformed port must expose no public item capability");
        require(controller.tryForm(helper.getLevel(), facing) == MultiblockValidationResult.VALID,
                helper, facing, "Formation failed before IO proof");

        IItemHandler items = requireItemCapability(helper, facing);
        ItemStack remainder = items.insertItem(0, new ItemStack(Items.DIAMOND), false);
        require(remainder.isEmpty(), helper, facing, "Rear port must accept the sentinel item");
        ItemStack controllerStack = controller.itemHandler().getStackInSlot(0);
        require(controllerStack.is(Items.DIAMOND) && controllerStack.getCount() == 1,
                helper, facing, "Port capability must delegate to the controller-owned slot");
        helper.succeed();
    }

    @GameTest(template = "multiblock_test", timeoutTicks = 160)
    public static void persistence(GameTestHelper helper) {
        Direction facing = Direction.NORTH;
        MultiblockControllerBlockEntity controller = buildStructure(helper, facing);
        require(controller.tryForm(helper.getLevel(), facing) == MultiblockValidationResult.VALID,
                helper, facing, "Formation failed before persistence proof");
        requireItemCapability(helper, facing).insertItem(0, new ItemStack(Items.DIAMOND), false);
        MultiblockPortBlockEntity port = requirePort(helper, facing);

        CompoundTag controllerTag = controller.saveWithFullMetadata(helper.getLevel().registryAccess());
        BlockEntity loadedControllerRaw = BlockEntity.loadStatic(
                controller.getBlockPos(), controller.getBlockState(), controllerTag, helper.getLevel().registryAccess());
        require(loadedControllerRaw instanceof MultiblockControllerBlockEntity,
                helper, facing, "Serialized controller must load as the correct BlockEntity type");
        MultiblockControllerBlockEntity loadedController = (MultiblockControllerBlockEntity) loadedControllerRaw;
        require(loadedController.lastKnownFormed(), helper, facing, "Historical formed flag must survive serialization");
        require(loadedController.formationRevision() == controller.formationRevision(),
                helper, facing, "Formation revision must survive serialization");
        require(loadedController.runtimeState() == MultiblockRuntimeState.PENDING_REVALIDATION,
                helper, facing, "Loaded formed history must fail closed to pending revalidation");
        require(loadedController.itemHandler().getStackInSlot(0).is(Items.DIAMOND),
                helper, facing, "Controller-owned item must survive serialization");

        CompoundTag portTag = port.saveWithFullMetadata(helper.getLevel().registryAccess());
        BlockEntity loadedPortRaw = BlockEntity.loadStatic(
                port.getBlockPos(), port.getBlockState(), portTag, helper.getLevel().registryAccess());
        require(loadedPortRaw instanceof MultiblockPortBlockEntity,
                helper, facing, "Serialized port must load as the correct BlockEntity type");
        MultiblockPortBlockEntity loadedPort = (MultiblockPortBlockEntity) loadedPortRaw;
        require(controller.getBlockPos().equals(loadedPort.controllerPos()),
                helper, facing, "Port controller position must survive serialization");
        require(controller.formationRevision() == loadedPort.linkedRevision(),
                helper, facing, "Port revision must survive serialization");
        helper.succeed();
    }

    @GameTest(template = "multiblock_test", timeoutTicks = 160)
    public static void staleBinding(GameTestHelper helper) {
        Direction facing = Direction.NORTH;
        MultiblockControllerBlockEntity controller = buildStructure(helper, facing);
        require(controller.tryForm(helper.getLevel(), facing) == MultiblockValidationResult.VALID,
                helper, facing, "Formation failed before stale-binding proof");
        MultiblockPortBlockEntity port = requirePort(helper, facing);
        port.bindToController(controller.getBlockPos(), controller.formationRevision() + 1L);
        helper.getLevel().invalidateCapabilities(port.getBlockPos());
        require(itemCapability(helper, facing) == null,
                helper, facing, "Mismatched linked revision must fail closed without capability");
        helper.succeed();
    }

    @GameTest(template = "multiblock_test", timeoutTicks = 160)
    public static void visualState(GameTestHelper helper) {
        Direction facing = Direction.NORTH;
        MultiblockControllerBlockEntity controller = buildStructure(helper, facing);
        require(controller.tryForm(helper.getLevel(), facing) == MultiblockValidationResult.VALID,
                helper, facing, "Formation failed before visual-state proof");
        BlockPos controllerPos = controller.getBlockPos();
        BlockPos portPos = portWorld(controllerPos, facing);
        BlockState controllerState = helper.getLevel().getBlockState(controllerPos);
        BlockState portState = helper.getLevel().getBlockState(portPos);
        require(controllerState.getValue(MultiblockControllerBlock.FORMED),
                helper, facing, "Controller formed visual state must be server-authored");
        require(portState.getValue(MultiblockPortBlock.FORMED),
                helper, facing, "Port formed visual state must be server-authored");
        require(controllerState.getValue(MultiblockControllerBlock.FACING) == facing
                        && portState.getValue(MultiblockPortBlock.FACING) == facing,
                helper, facing, "Facing visual state must match server formation orientation");

        setLocal(helper, facing, REQUIRED_CASING_LOCAL, Blocks.AIR.defaultBlockState());
        controller.revalidate(helper.getLevel(), facing);
        require(!helper.getLevel().getBlockState(controllerPos).getValue(MultiblockControllerBlock.FORMED),
                helper, facing, "Invalidation must clear controller formed visual state");
        require(!helper.getLevel().getBlockState(portPos).getValue(MultiblockPortBlock.FORMED),
                helper, facing, "Invalidation must clear port formed visual state");
        helper.succeed();
    }

    private static MultiblockControllerBlockEntity buildStructure(GameTestHelper helper, Direction facing) {
        BlockPos controllerPos = helper.absolutePos(controllerRelative(facing));
        for (int localX = MultiblockPattern.MIN_X; localX <= MultiblockPattern.MAX_X; localX++) {
            for (int localY = MultiblockPattern.MIN_Y; localY <= MultiblockPattern.MAX_Y; localY++) {
                for (int localZ = MultiblockPattern.MIN_Z; localZ <= MultiblockPattern.MAX_Z; localZ++) {
                    BlockPos local = new BlockPos(localX, localY, localZ);
                    BlockState state;
                    if (local.equals(MultiblockPattern.CONTROLLER_LOCAL)) {
                        state = I10MultiblockContent.MULTIBLOCK_CONTROLLER.get().defaultBlockState()
                                .setValue(MultiblockControllerBlock.FACING, facing)
                                .setValue(MultiblockControllerBlock.FORMED, false);
                    } else if (local.equals(MultiblockPattern.PORT_LOCAL)) {
                        state = I10MultiblockContent.MULTIBLOCK_IO_PORT.get().defaultBlockState()
                                .setValue(MultiblockPortBlock.FACING, facing)
                                .setValue(MultiblockPortBlock.FORMED, false);
                    } else if (local.equals(MultiblockPattern.INTERIOR_LOCAL)) {
                        state = Blocks.AIR.defaultBlockState();
                    } else {
                        state = I10MultiblockContent.MULTIBLOCK_CASING.get().defaultBlockState();
                    }
                    BlockPos world = MultiblockPattern.worldPos(controllerPos, facing, local);
                    helper.getLevel().setBlock(world, state, Block.UPDATE_CLIENTS);
                }
            }
        }
        BlockEntity blockEntity = helper.getLevel().getBlockEntity(controllerPos);
        require(blockEntity instanceof MultiblockControllerBlockEntity,
                helper, facing, "Expected controller BlockEntity after structure placement");
        return (MultiblockControllerBlockEntity) blockEntity;
    }

    private static void clearStructure(GameTestHelper helper, Direction facing) {
        BlockPos controllerPos = helper.absolutePos(controllerRelative(facing));
        for (int localX = MultiblockPattern.MIN_X; localX <= MultiblockPattern.MAX_X; localX++) {
            for (int localY = MultiblockPattern.MIN_Y; localY <= MultiblockPattern.MAX_Y; localY++) {
                for (int localZ = MultiblockPattern.MIN_Z; localZ <= MultiblockPattern.MAX_Z; localZ++) {
                    BlockPos world = MultiblockPattern.worldPos(controllerPos, facing, localX, localY, localZ);
                    helper.getLevel().setBlock(world, Blocks.AIR.defaultBlockState(), Block.UPDATE_CLIENTS);
                }
            }
        }
    }

    private static void setLocal(GameTestHelper helper, Direction facing, BlockPos local, BlockState state) {
        BlockPos controllerPos = helper.absolutePos(controllerRelative(facing));
        BlockPos world = MultiblockPattern.worldPos(controllerPos, facing, local);
        helper.getLevel().setBlock(world, state, Block.UPDATE_CLIENTS);
    }

    private static MultiblockPortBlockEntity requirePort(GameTestHelper helper, Direction facing) {
        BlockPos controllerPos = helper.absolutePos(controllerRelative(facing));
        BlockPos portPos = portWorld(controllerPos, facing);
        BlockEntity blockEntity = helper.getLevel().getBlockEntity(portPos);
        require(blockEntity instanceof MultiblockPortBlockEntity,
                helper, facing, "Expected rear port BlockEntity");
        return (MultiblockPortBlockEntity) blockEntity;
    }

    private static IItemHandler itemCapability(GameTestHelper helper, Direction facing) {
        BlockPos controllerPos = helper.absolutePos(controllerRelative(facing));
        return helper.getLevel().getCapability(Capabilities.ItemHandler.BLOCK, portWorld(controllerPos, facing), null);
    }

    private static IItemHandler requireItemCapability(GameTestHelper helper, Direction facing) {
        IItemHandler capability = itemCapability(helper, facing);
        require(capability != null, helper, facing, "Expected formed rear-port item capability");
        return capability;
    }

    private static BlockPos portWorld(BlockPos controllerPos, Direction facing) {
        return MultiblockPattern.worldPos(controllerPos, facing, MultiblockPattern.PORT_LOCAL);
    }

    private static BlockPos controllerRelative(Direction facing) {
        return switch (facing) {
            case NORTH -> new BlockPos(1, 1, 0);
            case EAST -> new BlockPos(2, 1, 1);
            case SOUTH -> new BlockPos(1, 1, 2);
            case WEST -> new BlockPos(0, 1, 1);
            default -> throw new IllegalArgumentException("I10 GameTest facing must be horizontal");
        };
    }

    private static void require(boolean condition, GameTestHelper helper, Direction facing, String message) {
        if (!condition) {
            helper.fail(message, controllerRelative(facing));
        }
    }
}
