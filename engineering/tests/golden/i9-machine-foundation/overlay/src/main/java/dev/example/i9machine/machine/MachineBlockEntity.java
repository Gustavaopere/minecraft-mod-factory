package dev.example.i9machine.machine;

import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderLookup;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.Tag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.inventory.ContainerData;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.RecipeType;
import net.minecraft.world.item.crafting.SingleRecipeInput;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.neoforge.items.ItemStackHandler;

public final class MachineBlockEntity extends BlockEntity {
    public static final int INPUT_SLOT = 0;
    public static final int OUTPUT_SLOT = 1;
    public static final int ENERGY_PER_TICK = 20;
    public static final int MAX_PROGRESS = 100;

    private static final String INVENTORY_TAG = "Inventory";
    private static final String ENERGY_TAG = "Energy";
    private static final String PROGRESS_TAG = "Progress";

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
    private int progress;
    private final ContainerData data = new ContainerData() {
        @Override
        public int get(int index) {
            return switch (index) {
                case 0 -> progress;
                case 1 -> MAX_PROGRESS;
                case 2 -> energyStorage.getEnergyStored();
                default -> 0;
            };
        }

        @Override
        public void set(int index, int value) {
            if (index == 0) {
                progress = Math.max(0, Math.min(MAX_PROGRESS - 1, value));
            }
        }

        @Override
        public int getCount() {
            return 3;
        }
    };

    public MachineBlockEntity(BlockPos pos, BlockState state) {
        super(I9MachineContent.MACHINE_BLOCK_ENTITY.get(), pos, state);
    }

    public static void serverTick(Level level, BlockPos pos, BlockState state, MachineBlockEntity blockEntity) {
        if (level instanceof ServerLevel serverLevel) {
            blockEntity.tickServer(serverLevel);
        }
    }

    private void tickServer(ServerLevel serverLevel) {
        ItemStack inputStack = itemHandler.getStackInSlot(INPUT_SLOT);
        if (inputStack.isEmpty()) {
            resetProgress();
            return;
        }

        SingleRecipeInput recipeInput = new SingleRecipeInput(inputStack);
        var recipe = serverLevel.getRecipeManager().getRecipeFor(RecipeType.SMELTING, recipeInput, serverLevel);
        if (recipe.isEmpty()) {
            resetProgress();
            return;
        }

        ItemStack result = recipe.get().value().assemble(recipeInput, serverLevel.registryAccess());
        if (result.isEmpty() || !canAcceptOutput(result) || energyStorage.getEnergyStored() < ENERGY_PER_TICK) {
            resetProgress();
            return;
        }

        if (!energyStorage.consumeInternal(ENERGY_PER_TICK)) {
            resetProgress();
            return;
        }

        progress++;
        setChanged();
        if (progress < MAX_PROGRESS) {
            return;
        }

        itemHandler.extractItem(INPUT_SLOT, 1, false);
        ItemStack outputStack = itemHandler.getStackInSlot(OUTPUT_SLOT);
        if (outputStack.isEmpty()) {
            itemHandler.setStackInSlot(OUTPUT_SLOT, result.copy());
        } else {
            ItemStack merged = outputStack.copy();
            merged.grow(result.getCount());
            itemHandler.setStackInSlot(OUTPUT_SLOT, merged);
        }
        progress = 0;
        setChanged();
    }

    private boolean canAcceptOutput(ItemStack result) {
        ItemStack outputStack = itemHandler.getStackInSlot(OUTPUT_SLOT);
        if (outputStack.isEmpty()) {
            return result.getCount() <= Math.min(result.getMaxStackSize(), itemHandler.getSlotLimit(OUTPUT_SLOT));
        }
        if (!ItemStack.isSameItemSameComponents(outputStack, result)) {
            return false;
        }
        int limit = Math.min(outputStack.getMaxStackSize(), itemHandler.getSlotLimit(OUTPUT_SLOT));
        return outputStack.getCount() + result.getCount() <= limit;
    }

    private void resetProgress() {
        if (progress != 0) {
            progress = 0;
            setChanged();
        }
    }

    @Override
    protected void loadAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.loadAdditional(tag, registries);
        if (tag.contains(INVENTORY_TAG, Tag.TAG_COMPOUND)) {
            itemHandler.deserializeNBT(registries, tag.getCompound(INVENTORY_TAG));
        }
        energyStorage.loadClamped(tag.getInt(ENERGY_TAG));
        progress = Math.max(0, Math.min(MAX_PROGRESS - 1, tag.getInt(PROGRESS_TAG)));
    }

    @Override
    protected void saveAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.saveAdditional(tag, registries);
        tag.put(INVENTORY_TAG, itemHandler.serializeNBT(registries));
        tag.putInt(ENERGY_TAG, energyStorage.getEnergyStored());
        tag.putInt(PROGRESS_TAG, progress);
    }

    public ItemStackHandler itemHandler() {
        return itemHandler;
    }

    public MachineEnergyStorage energyStorage() {
        return energyStorage;
    }

    public ContainerData data() {
        return data;
    }
}
