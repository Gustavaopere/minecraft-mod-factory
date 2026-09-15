package dev.example.i10multiblock.multiblock;

import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderLookup;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.Tag;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.neoforge.items.ItemStackHandler;

public final class MultiblockPortBlockEntity extends BlockEntity {
    private static final String CONTROLLER_POS_TAG = "ControllerPos";
    private static final String LINKED_REVISION_TAG = "LinkedRevision";

    private BlockPos controllerPos;
    private long linkedRevision = -1L;

    public MultiblockPortBlockEntity(BlockPos pos, BlockState state) {
        super(I10MultiblockContent.MULTIBLOCK_IO_PORT_BLOCK_ENTITY.get(), pos, state);
    }

    public void bindToController(BlockPos controllerPos, long revision) {
        if (controllerPos == null || revision <= 0L) {
            clearBinding();
            return;
        }
        this.controllerPos = controllerPos.immutable();
        this.linkedRevision = revision;
        setChanged();
    }

    public void clearBinding() {
        controllerPos = null;
        linkedRevision = -1L;
        setChanged();
    }

    public ItemStackHandler itemHandler() {
        if (level == null || controllerPos == null || linkedRevision <= 0 || !level.hasChunkAt(controllerPos)) {
            return null;
        }
        if (!(level.getBlockEntity(controllerPos) instanceof MultiblockControllerBlockEntity controller)) {
            return null;
        }
        if (controller.runtimeState() != MultiblockRuntimeState.FORMED) {
            return null;
        }
        if (controller.formationRevision() != linkedRevision) {
            return null;
        }
        return controller.itemHandler();
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
