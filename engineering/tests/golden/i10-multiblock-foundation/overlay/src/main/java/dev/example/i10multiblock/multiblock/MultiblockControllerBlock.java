package dev.example.i10multiblock.multiblock;

import com.mojang.serialization.MapCodec;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.BlockState;

public final class MultiblockControllerBlock extends BaseEntityBlock {
    public static final MapCodec<MultiblockControllerBlock> CODEC = simpleCodec(MultiblockControllerBlock::new);

    public MultiblockControllerBlock(BlockBehaviour.Properties properties) {
        super(properties);
    }

    @Override
    protected MapCodec<? extends BaseEntityBlock> codec() {
        return CODEC;
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new MultiblockControllerBlockEntity(pos, state);
    }
}
