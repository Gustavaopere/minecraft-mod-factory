package dev.example.i10multiblock.multiblock;

import java.util.HashSet;
import java.util.Set;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.block.state.BlockState;

public final class MultiblockInvalidation {
    private static final int REVALIDATION_DELAY = 1;

    private MultiblockInvalidation() {
    }

    public static void scheduleAround(ServerLevel level, BlockPos changedPos) {
        Set<BlockPos> scheduled = new HashSet<>();
        for (Direction facing : Direction.Plane.HORIZONTAL) {
            Direction depth = facing.getOpposite();
            Direction right = facing.getClockWise();
            for (int localX = MultiblockPattern.MIN_X; localX <= MultiblockPattern.MAX_X; localX++) {
                for (int localY = MultiblockPattern.MIN_Y; localY <= MultiblockPattern.MAX_Y; localY++) {
                    for (int localZ = MultiblockPattern.MIN_Z; localZ <= MultiblockPattern.MAX_Z; localZ++) {
                        int offsetX = right.getStepX() * localX + depth.getStepX() * localZ;
                        int offsetY = localY - MultiblockPattern.CONTROLLER_LOCAL.getY();
                        int offsetZ = right.getStepZ() * localX + depth.getStepZ() * localZ;
                        BlockPos candidate = changedPos.offset(-offsetX, -offsetY, -offsetZ);
                        if (!scheduled.add(candidate) || !level.hasChunkAt(candidate)) {
                            continue;
                        }
                        BlockState candidateState = level.getBlockState(candidate);
                        if (!candidateState.is(I10MultiblockContent.MULTIBLOCK_CONTROLLER.get())) {
                            continue;
                        }
                        if (level.getBlockEntity(candidate) instanceof MultiblockControllerBlockEntity controller
                                && (controller.runtimeState() == MultiblockRuntimeState.FORMED
                                || controller.lastKnownFormed())) {
                            controller.markPendingRevalidation();
                            Direction controllerFacing = candidateState.getValue(MultiblockControllerBlock.FACING);
                            BlockPos portPos = MultiblockPattern.worldPos(
                                    candidate, controllerFacing, MultiblockPattern.PORT_LOCAL);
                            if (level.hasChunkAt(portPos)) {
                                level.invalidateCapabilities(portPos);
                            }
                        }
                        level.scheduleTick(candidate, I10MultiblockContent.MULTIBLOCK_CONTROLLER.get(), REVALIDATION_DELAY);
                    }
                }
            }
        }
    }
}
