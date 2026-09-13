package dev.example.i9machine.machine;

import net.minecraft.core.BlockPos;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.neoforge.items.ItemStackHandler;

public final class MachineBlockEntity extends BlockEntity {
    private final ItemStackHandler itemHandler = new ItemStackHandler(2);
    private final MachineEnergyStorage energyStorage = new MachineEnergyStorage();

    public MachineBlockEntity(BlockPos pos, BlockState state) {
        super(I9MachineContent.MACHINE_BLOCK_ENTITY.get(), pos, state);
    }

    public ItemStackHandler itemHandler() {
        return itemHandler;
    }

    public MachineEnergyStorage energyStorage() {
        return energyStorage;
    }
}
