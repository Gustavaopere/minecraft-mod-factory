package dev.example.i10multiblock.multiblock;

import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderLookup;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.Tag;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.neoforge.items.ItemStackHandler;

public final class MultiblockControllerBlockEntity extends BlockEntity {
    private static final String INVENTORY_TAG = "Inventory";
    private static final String LAST_KNOWN_FORMED_TAG = "LastKnownFormed";
    private static final String FORMATION_REVISION_TAG = "FormationRevision";

    private final ItemStackHandler itemHandler = new ItemStackHandler(1) {
        @Override
        protected void onContentsChanged(int slot) {
            MultiblockControllerBlockEntity.this.setChanged();
        }

        @Override
        public boolean isItemValid(int slot, ItemStack stack) {
            return slot == 0 && !stack.isEmpty();
        }
    };

    private boolean lastKnownFormed;
    private long formationRevision;
    private MultiblockRuntimeState runtimeState = MultiblockRuntimeState.UNFORMED;

    public MultiblockControllerBlockEntity(BlockPos pos, BlockState state) {
        super(I10MultiblockContent.MULTIBLOCK_CONTROLLER_BLOCK_ENTITY.get(), pos, state);
    }

    public void markPendingRevalidation() {
        runtimeState = MultiblockRuntimeState.PENDING_REVALIDATION;
        setChanged();
    }

    public long markFormed() {
        if (formationRevision < Long.MAX_VALUE) {
            formationRevision++;
        }
        lastKnownFormed = true;
        runtimeState = MultiblockRuntimeState.FORMED;
        setChanged();
        return formationRevision;
    }

    public void markUnformed() {
        lastKnownFormed = false;
        runtimeState = MultiblockRuntimeState.UNFORMED;
        setChanged();
    }

    public MultiblockRuntimeState runtimeState() {
        return runtimeState;
    }

    public boolean lastKnownFormed() {
        return lastKnownFormed;
    }

    public long formationRevision() {
        return formationRevision;
    }

    public ItemStackHandler itemHandler() {
        return itemHandler;
    }

    @Override
    protected void loadAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.loadAdditional(tag, registries);
        if (tag.contains(INVENTORY_TAG, Tag.TAG_COMPOUND)) {
            itemHandler.deserializeNBT(registries, tag.getCompound(INVENTORY_TAG));
        }
        lastKnownFormed = tag.getBoolean(LAST_KNOWN_FORMED_TAG);
        formationRevision = Math.max(0L, tag.getLong(FORMATION_REVISION_TAG));
        runtimeState = lastKnownFormed ? MultiblockRuntimeState.PENDING_REVALIDATION : MultiblockRuntimeState.UNFORMED;
    }

    @Override
    protected void saveAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.saveAdditional(tag, registries);
        tag.put(INVENTORY_TAG, itemHandler.serializeNBT(registries));
        tag.putBoolean(LAST_KNOWN_FORMED_TAG, lastKnownFormed);
        tag.putLong(FORMATION_REVISION_TAG, formationRevision);
    }
}
