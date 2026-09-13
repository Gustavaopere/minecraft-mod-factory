package dev.example.i9machine.machine;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.RecipeType;
import net.minecraft.world.item.crafting.SingleRecipeInput;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.neoforge.items.ItemStackHandler;

public final class MachineBlockEntity extends BlockEntity {
    public static final int INPUT_SLOT = 0;
    public static final int OUTPUT_SLOT = 1;
    public static final int ENERGY_PER_TICK = 20;
    public static final int MAX_PROGRESS = 100;

    private final ItemStackHandler itemHandler = new ItemStackHandler(2) {
        @Override
        protected void onContentsChanged(int slot) {
            MachineBlockEntity.this.setChanged();
        }

        @Override
        public boolean isItemValid(int slot, ItemStack stack) {
            if (slot == OUTPUT_SLOT || slot != INPUT_SLOT || stack.isEmpty()) {
                return false;
            }
            if (!(level instanceof ServerLevel serverLevel)) {
                return false;
            }
            return serverLevel.getRecipeManager()
                    .getRecipeFor(RecipeType.SMELTING, new SingleRecipeInput(stack), serverLevel)
                    .isPresent();
        }
    };
    private final MachineEnergyStorage energyStorage = new MachineEnergyStorage(this::setChanged);

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
