package dev.example.i10multiblock.multiblock;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.block.state.BlockState;

public final class MultiblockPattern {
    public static final int MIN_X = -1;
    public static final int MAX_X = 1;
    public static final int MIN_Y = 0;
    public static final int MAX_Y = 2;
    public static final int MIN_Z = 0;
    public static final int MAX_Z = 2;

    public static final BlockPos CONTROLLER_LOCAL = new BlockPos(0, 1, 0);
    public static final BlockPos PORT_LOCAL = new BlockPos(0, 1, 2);
    public static final BlockPos INTERIOR_LOCAL = new BlockPos(0, 1, 1);

    private MultiblockPattern() {
    }

    public static BlockPos worldPos(
            BlockPos controllerPos,
            Direction facing,
            int localX,
            int localY,
            int localZ) {
        if (!facing.getAxis().isHorizontal()) {
            throw new IllegalArgumentException("I10 controller facing must be horizontal");
        }
        Direction depth = facing.getOpposite();
        Direction right = facing.getClockWise();
        return controllerPos
                .relative(right, localX)
                .above(localY - CONTROLLER_LOCAL.getY())
                .relative(depth, localZ);
    }

    public static BlockPos worldPos(BlockPos controllerPos, Direction facing, BlockPos localPos) {
        return worldPos(
                controllerPos,
                facing,
                localPos.getX(),
                localPos.getY(),
                localPos.getZ());
    }

    public static MultiblockValidationResult validate(
            ServerLevel level,
            BlockPos controllerPos,
            Direction facing) {
        if (!facing.getAxis().isHorizontal()) {
            return MultiblockValidationResult.INVALID;
        }
        for (int localX = MIN_X; localX <= MAX_X; localX++) {
            for (int localY = MIN_Y; localY <= MAX_Y; localY++) {
                for (int localZ = MIN_Z; localZ <= MAX_Z; localZ++) {
                    BlockPos worldPos = worldPos(controllerPos, facing, localX, localY, localZ);
                    if (!level.hasChunkAt(worldPos)) {
                        return MultiblockValidationResult.UNAVAILABLE;
                    }
                    BlockState state = level.getBlockState(worldPos);
                    if (!matchesRole(state, localX, localY, localZ)) {
                        return MultiblockValidationResult.INVALID;
                    }
                }
            }
        }
        return MultiblockValidationResult.VALID;
    }

    private static boolean matchesRole(BlockState state, int x, int y, int z) {
        if (x == CONTROLLER_LOCAL.getX() && y == CONTROLLER_LOCAL.getY() && z == CONTROLLER_LOCAL.getZ()) {
            return state.is(I10MultiblockContent.MULTIBLOCK_CONTROLLER.get());
        }
        if (x == PORT_LOCAL.getX() && y == PORT_LOCAL.getY() && z == PORT_LOCAL.getZ()) {
            return state.is(I10MultiblockContent.MULTIBLOCK_IO_PORT.get());
        }
        if (x == INTERIOR_LOCAL.getX() && y == INTERIOR_LOCAL.getY() && z == INTERIOR_LOCAL.getZ()) {
            return state.isAir();
        }
        return isBoundary(x, y, z) && state.is(I10MultiblockContent.MULTIBLOCK_CASING.get());
    }

    private static boolean isBoundary(int x, int y, int z) {
        return x == MIN_X || x == MAX_X || y == MIN_Y || y == MAX_Y || z == MIN_Z || z == MAX_Z;
    }
}
