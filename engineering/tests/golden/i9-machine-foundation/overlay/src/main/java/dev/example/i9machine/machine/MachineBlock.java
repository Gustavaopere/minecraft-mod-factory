package dev.example.i9machine.machine;

import com.mojang.serialization.MapCodec;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.SimpleMenuProvider;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.ContainerLevelAccess;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;

public final class MachineBlock extends BaseEntityBlock {
    public static final MapCodec<MachineBlock> CODEC = simpleCodec(MachineBlock::new);

    public MachineBlock(BlockBehaviour.Properties properties) {
        super(properties);
    }

    @Override
    protected MapCodec<? extends BaseEntityBlock> codec() {
        return CODEC;
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new MachineBlockEntity(pos, state);
    }

    @Override
    protected InteractionResult useWithoutItem(
            BlockState state,
            Level level,
            BlockPos pos,
            Player player,
            BlockHitResult hitResult) {
        if (!level.isClientSide && level.getBlockEntity(pos) instanceof MachineBlockEntity machine) {
            player.openMenu(new SimpleMenuProvider(
                    (containerId, inventory, menuPlayer) -> new MachineMenu(
                            containerId,
                            inventory,
                            machine.itemHandler(),
                            machine.data(),
                            ContainerLevelAccess.create(level, pos)),
                    Component.translatable("container.i9_machine.machine")));
        }
        return InteractionResult.sidedSuccess(level.isClientSide);
    }

    @Override
    public <T extends BlockEntity> BlockEntityTicker<T> getTicker(
            Level level,
            BlockState state,
            BlockEntityType<T> blockEntityType) {
        if (level.isClientSide) {
            return null;
        }
        return createTickerHelper(
                blockEntityType,
                I9MachineContent.MACHINE_BLOCK_ENTITY.get(),
                MachineBlockEntity::serverTick);
    }
}
