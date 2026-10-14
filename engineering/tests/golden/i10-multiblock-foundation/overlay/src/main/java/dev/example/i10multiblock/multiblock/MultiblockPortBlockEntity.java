package dev.example.i10multiblock.multiblock;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.HolderLookup;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.Tag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.neoforge.items.IItemHandler;
import net.neoforged.neoforge.items.ItemStackHandler;

public final class MultiblockPortBlockEntity extends BlockEntity {
    private static final String CONTROLLER_POS_TAG = "ControllerPos";
    private static final String LINKED_REVISION_TAG = "LinkedRevision";

    private BlockPos controllerPos;
    private long linkedRevision = -1L;
    private long handlerEpoch;
    private IItemHandler guardedItemHandler;

    public MultiblockPortBlockEntity(BlockPos pos, BlockState state) {
        super(I10MultiblockContent.MULTIBLOCK_IO_PORT_BLOCK_ENTITY.get(), pos, state);
    }

    public void bindToController(BlockPos controllerPos, long revision) {
        if (controllerPos == null || revision <= 0L) {
            clearBinding();
            return;
        }
        if (controllerPos.equals(this.controllerPos) && linkedRevision == revision) {
            return;
        }
        this.controllerPos = controllerPos.immutable();
        this.linkedRevision = revision;
        handlerEpoch++;
        guardedItemHandler = null;
        setChanged();
    }

    public void clearBinding() {
        controllerPos = null;
        linkedRevision = -1L;
        handlerEpoch++;
        guardedItemHandler = null;
        setChanged();
    }

    /**
     * A cached capability must never expose the controller inventory after a
     * required casing chunk unloads. Each operation rechecks the footprint,
     * without requesting/loading missing chunks, and denies mutations if the
     * controller is unavailable, invalid, pending, or revision-stale.
     */
    public IItemHandler itemHandler() {
        if (activeBacking() == null) {
            return null;
        }
        if (guardedItemHandler == null) {
            guardedItemHandler = createGuardedHandler(handlerEpoch);
        }
        return guardedItemHandler;
    }

    private ItemStackHandler activeBacking() {
        if (!(level instanceof ServerLevel serverLevel) || controllerPos == null
                || linkedRevision <= 0 || !serverLevel.hasChunkAt(controllerPos)) {
            return null;
        }
        if (!(serverLevel.getBlockEntity(controllerPos) instanceof MultiblockControllerBlockEntity controller)) {
            return null;
        }
        BlockState controllerState = serverLevel.getBlockState(controllerPos);
        if (!controllerState.is(I10MultiblockContent.MULTIBLOCK_CONTROLLER.get())) {
            return null;
        }
        Direction facing = controllerState.getValue(MultiblockControllerBlock.FACING);
        if (controller.runtimeState() == MultiblockRuntimeState.PENDING_REVALIDATION
                && controller.lastKnownFormed()) {
            controller.revalidate(serverLevel, facing);
        }
        if (controller.runtimeState() != MultiblockRuntimeState.FORMED
                || controller.formationRevision() != linkedRevision) {
            return null;
        }
        if (MultiblockPattern.validate(serverLevel, controllerPos, facing) != MultiblockValidationResult.VALID) {
            controller.revalidate(serverLevel, facing);
            return null;
        }
        return controller.itemHandler();
    }

    private IItemHandler createGuardedHandler(long expectedEpoch) {
        return new IItemHandler() {
            private ItemStackHandler backing() {
                return handlerEpoch == expectedEpoch ? activeBacking() : null;
            }

            @Override
            public int getSlots() {
                return 1;
            }

            @Override
            public ItemStack getStackInSlot(int slot) {
                ItemStackHandler storage = backing();
                return storage == null ? ItemStack.EMPTY : storage.getStackInSlot(slot);
            }

            @Override
            public ItemStack insertItem(int slot, ItemStack stack, boolean simulate) {
                ItemStackHandler storage = backing();
                return storage == null ? stack : storage.insertItem(slot, stack, simulate);
            }

            @Override
            public ItemStack extractItem(int slot, int amount, boolean simulate) {
                ItemStackHandler storage = backing();
                return storage == null ? ItemStack.EMPTY : storage.extractItem(slot, amount, simulate);
            }

            @Override
            public int getSlotLimit(int slot) {
                ItemStackHandler storage = backing();
                return storage == null ? 0 : storage.getSlotLimit(slot);
            }

            @Override
            public boolean isItemValid(int slot, ItemStack stack) {
                ItemStackHandler storage = backing();
                return storage != null && storage.isItemValid(slot, stack);
            }
        };
    }

    public BlockPos controllerPos() {
        return controllerPos;
    }

    public long linkedRevision() {
        return linkedRevision;
    }

    @Override
    protected void loadAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.loadAdditional(tag, registries);
        controllerPos = null;
        linkedRevision = -1L;
        handlerEpoch++;
        guardedItemHandler = null;
        if (!tag.contains(CONTROLLER_POS_TAG, Tag.TAG_LONG) || !tag.contains(LINKED_REVISION_TAG, Tag.TAG_LONG)) {
            return;
        }
        long revision = tag.getLong(LINKED_REVISION_TAG);
        if (revision <= 0L) {
            return;
        }
        controllerPos = BlockPos.of(tag.getLong(CONTROLLER_POS_TAG));
        linkedRevision = revision;
    }

    @Override
    protected void saveAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.saveAdditional(tag, registries);
        if (controllerPos != null && linkedRevision > 0L) {
            tag.putLong(CONTROLLER_POS_TAG, controllerPos.asLong());
            tag.putLong(LINKED_REVISION_TAG, linkedRevision);
        }
    }
}
