package dev.example.i10multiblock.multiblock;

import net.minecraft.core.BlockPos;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;

public final class MultiblockControllerBlockEntity extends BlockEntity {
    public MultiblockControllerBlockEntity(BlockPos pos, BlockState state) {
        super(I10MultiblockContent.MULTIBLOCK_CONTROLLER_BLOCK_ENTITY.get(), pos, state);
    }
}
