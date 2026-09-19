package dev.example.i10multiblock.acceptance;

import com.mojang.brigadier.CommandDispatcher;
import com.mojang.logging.LogUtils;
import dev.example.i10multiblock.I10MultiblockMod;
import dev.example.i10multiblock.multiblock.I10MultiblockContent;
import dev.example.i10multiblock.multiblock.MultiblockControllerBlock;
import dev.example.i10multiblock.multiblock.MultiblockControllerBlockEntity;
import dev.example.i10multiblock.multiblock.MultiblockPattern;
import dev.example.i10multiblock.multiblock.MultiblockPortBlock;
import dev.example.i10multiblock.multiblock.MultiblockPortBlockEntity;
import dev.example.i10multiblock.multiblock.MultiblockRuntimeState;
import dev.example.i10multiblock.multiblock.MultiblockValidationResult;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.capabilities.Capabilities;
import net.neoforged.neoforge.event.RegisterCommandsEvent;
import net.neoforged.neoforge.items.IItemHandler;
import org.slf4j.Logger;

@EventBusSubscriber(modid = I10MultiblockMod.MOD_ID)
public final class I10AcceptanceCommands {
    private static final Logger LOGGER = LogUtils.getLogger();
    private static final BlockPos CONTROLLER_POS = new BlockPos(159, 80, 160);
    private static final Direction FACING = Direction.WEST;
    private static final BlockPos REQUIRED_CASING_LOCAL = new BlockPos(-1, 0, 0);

    private I10AcceptanceCommands() {
    }

    @SubscribeEvent
    public static void registerCommands(RegisterCommandsEvent event) {
        CommandDispatcher<CommandSourceStack> dispatcher = event.getDispatcher();
        dispatcher.register(
                Commands.literal("i10probe")
                        .requires(source -> source.hasPermission(2))
                        .then(Commands.literal("baseline")
                                .executes(context -> baseline(context.getSource())))
                        .then(Commands.literal("setup")
                                .executes(context -> setup(context.getSource())))
                        .then(Commands.literal("status")
                                .executes(context -> status(context.getSource())))
                        .then(Commands.literal("break_required_part")
                                .executes(context -> breakRequiredPart(context.getSource()))));
    }

    private static int baseline(CommandSourceStack source) {
        ServerLevel level = source.getLevel();
        clearStructure(level);
        buildStructure(level);

        BlockEntity blockEntity = level.getBlockEntity(CONTROLLER_POS);
        if (!(blockEntity instanceof MultiblockControllerBlockEntity controller)) {
            emit(level, "baseline", null);
            return 0;
        }

        controller.markUnformed();
        BlockPos portPos = MultiblockPattern.worldPos(
                CONTROLLER_POS, FACING, MultiblockPattern.PORT_LOCAL);
        if (level.hasChunkAt(portPos)
                && level.getBlockEntity(portPos) instanceof MultiblockPortBlockEntity port) {
            port.clearBinding();
            level.invalidateCapabilities(portPos);
        }

        emit(level, "baseline", controller);
        return 1;
    }

    private static int setup(CommandSourceStack source) {
        ServerLevel level = source.getLevel();
        buildStructure(level);

        BlockEntity blockEntity = level.getBlockEntity(CONTROLLER_POS);
        if (!(blockEntity instanceof MultiblockControllerBlockEntity controller)) {
            emit(level, "setup", null);
            return 0;
        }

        controller.tryForm(level, FACING);
        BlockPos portPos = MultiblockPattern.worldPos(
                CONTROLLER_POS, FACING, MultiblockPattern.PORT_LOCAL);
        IItemHandler capability = level.hasChunkAt(portPos)
                ? level.getCapability(Capabilities.ItemHandler.BLOCK, portPos, null)
                : null;
        if (capability != null && controller.itemHandler().getStackInSlot(0).isEmpty()) {
            capability.insertItem(0, new ItemStack(Items.DIAMOND), false);
        }

        emit(level, "setup", controller);
        return 1;
    }

    private static int status(CommandSourceStack source) {
        ServerLevel level = source.getLevel();
        BlockEntity blockEntity = level.hasChunkAt(CONTROLLER_POS)
                ? level.getBlockEntity(CONTROLLER_POS)
                : null;
        emit(
                level,
                "status",
                blockEntity instanceof MultiblockControllerBlockEntity controller ? controller : null);
        return 1;
    }

    private static int breakRequiredPart(CommandSourceStack source) {
        ServerLevel level = source.getLevel();
        BlockPos required = MultiblockPattern.worldPos(
                CONTROLLER_POS, FACING, REQUIRED_CASING_LOCAL);
        if (level.hasChunkAt(required)) {
            level.setBlock(required, Blocks.AIR.defaultBlockState(), Block.UPDATE_ALL);
        }

        BlockEntity blockEntity = level.hasChunkAt(CONTROLLER_POS)
                ? level.getBlockEntity(CONTROLLER_POS)
                : null;
        emit(
                level,
                "break_required_part",
                blockEntity instanceof MultiblockControllerBlockEntity controller ? controller : null);
        return 1;
    }

    private static void clearStructure(ServerLevel level) {
        for (int localX = MultiblockPattern.MIN_X; localX <= MultiblockPattern.MAX_X; localX++) {
            for (int localY = MultiblockPattern.MIN_Y; localY <= MultiblockPattern.MAX_Y; localY++) {
                for (int localZ = MultiblockPattern.MIN_Z; localZ <= MultiblockPattern.MAX_Z; localZ++) {
                    BlockPos local = new BlockPos(localX, localY, localZ);
                    BlockPos world = MultiblockPattern.worldPos(CONTROLLER_POS, FACING, local);
                    if (level.hasChunkAt(world)) {
                        level.setBlock(world, Blocks.AIR.defaultBlockState(), Block.UPDATE_ALL);
                    }
                }
            }
        }
    }

    private static void buildStructure(ServerLevel level) {
        for (int localX = MultiblockPattern.MIN_X; localX <= MultiblockPattern.MAX_X; localX++) {
            for (int localY = MultiblockPattern.MIN_Y; localY <= MultiblockPattern.MAX_Y; localY++) {
                for (int localZ = MultiblockPattern.MIN_Z; localZ <= MultiblockPattern.MAX_Z; localZ++) {
                    BlockPos local = new BlockPos(localX, localY, localZ);
                    BlockState state;
                    if (local.equals(MultiblockPattern.CONTROLLER_LOCAL)) {
                        state = I10MultiblockContent.MULTIBLOCK_CONTROLLER.get().defaultBlockState()
                                .setValue(MultiblockControllerBlock.FACING, FACING)
                                .setValue(MultiblockControllerBlock.FORMED, false);
                    } else if (local.equals(MultiblockPattern.PORT_LOCAL)) {
                        state = I10MultiblockContent.MULTIBLOCK_IO_PORT.get().defaultBlockState()
                                .setValue(MultiblockPortBlock.FACING, FACING)
                                .setValue(MultiblockPortBlock.FORMED, false);
                    } else if (local.equals(MultiblockPattern.INTERIOR_LOCAL)) {
                        state = Blocks.AIR.defaultBlockState();
                    } else {
                        state = I10MultiblockContent.MULTIBLOCK_CASING.get().defaultBlockState();
                    }
                    BlockPos world = MultiblockPattern.worldPos(CONTROLLER_POS, FACING, local);
                    level.setBlock(world, state, Block.UPDATE_ALL);
                }
            }
        }
    }

    private static void emit(
            ServerLevel level,
            String action,
            MultiblockControllerBlockEntity controller) {
        MultiblockValidationResult validation = MultiblockPattern.validate(
                level, CONTROLLER_POS, FACING);
        MultiblockRuntimeState runtime = controller == null
                ? MultiblockRuntimeState.UNFORMED
                : controller.runtimeState();
        if (runtime == MultiblockRuntimeState.PENDING_REVALIDATION) {
            runtime = MultiblockRuntimeState.PENDING_REVALIDATION;
        }
        long revision = controller == null ? 0L : controller.formationRevision();
        boolean lastKnownFormed = controller != null && controller.lastKnownFormed();

        ItemStack sentinel = controller == null
                ? ItemStack.EMPTY
                : controller.itemHandler().getStackInSlot(0);
        String sentinelId = sentinel.isEmpty()
                ? "empty"
                : BuiltInRegistries.ITEM.getKey(sentinel.getItem()).toString();
        int count = sentinel.isEmpty() ? 0 : sentinel.getCount();

        BlockPos portPos = MultiblockPattern.worldPos(
                CONTROLLER_POS, FACING, MultiblockPattern.PORT_LOCAL);
        boolean capability = level.hasChunkAt(portPos)
                && level.getCapability(Capabilities.ItemHandler.BLOCK, portPos, null) != null;

        LOGGER.info(
                "I10_PROBE action={} validation={} runtime={} revision={} sentinel={} count={} capability={} last_known_formed={}",
                action,
                validation.name(),
                runtime.name(),
                Math.max(0L, revision),
                sentinelId,
                count,
                capability,
                lastKnownFormed);
    }
}
