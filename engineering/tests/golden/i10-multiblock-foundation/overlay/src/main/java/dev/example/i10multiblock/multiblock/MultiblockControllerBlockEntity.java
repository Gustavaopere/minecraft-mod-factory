package dev.example.i10multiblock.multiblock;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.HolderLookup;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.Tag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Block;
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

    @Override
    public void onLoad() {
        super.onLoad();
        if (level instanceof ServerLevel serverLevel && lastKnownFormed) {
            serverLevel.scheduleTick(worldPosition, getBlockState().getBlock(), 1);
        }
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

    public void markRevalidatedFormed() {
        if (!lastKnownFormed || formationRevision <= 0L) {
            markUnformed();
            return;
        }
        runtimeState = MultiblockRuntimeState.FORMED;
        setChanged();
    }

    public void markUnformed() {
        lastKnownFormed = false;
        runtimeState = MultiblockRuntimeState.UNFORMED;
        setChanged();
    }

    public MultiblockValidationResult tryForm(ServerLevel level, Direction facing) {
        MultiblockValidationResult validation = MultiblockPattern.validate(level, worldPosition, facing);
        if (validation == MultiblockValidationResult.UNAVAILABLE) {
            if (lastKnownFormed || runtimeState == MultiblockRuntimeState.FORMED) {
                markPendingRevalidation();
            }
            setVisualFormed(level, facing, false);
            return validation;
        }
        if (validation == MultiblockValidationResult.INVALID) {
            dissolve(level, facing);
            return validation;
        }

        BlockPos portPos = MultiblockPattern.worldPos(worldPosition, facing, MultiblockPattern.PORT_LOCAL);
        if (!(level.getBlockEntity(portPos) instanceof MultiblockPortBlockEntity port)) {
            dissolve(level, facing);
            return MultiblockValidationResult.INVALID;
        }

        long revision = markFormed();
        port.bindToController(worldPosition, revision);
        setVisualFormed(level, facing, true);
        return MultiblockValidationResult.VALID;
    }

    public MultiblockValidationResult revalidate(ServerLevel level, Direction facing) {
        MultiblockValidationResult validation = MultiblockPattern.validate(level, worldPosition, facing);
        if (validation == MultiblockValidationResult.UNAVAILABLE) {
            if (lastKnownFormed || runtimeState == MultiblockRuntimeState.FORMED
                    || runtimeState == MultiblockRuntimeState.PENDING_REVALIDATION) {
                markPendingRevalidation();
            }
            setVisualFormed(level, facing, false);
            return validation;
        }
        if (validation == MultiblockValidationResult.INVALID) {
            dissolve(level, facing);
            return validation;
        }

        if (!lastKnownFormed || formationRevision <= 0L) {
            dissolve(level, facing);
            return MultiblockValidationResult.VALID;
        }

        BlockPos portPos = MultiblockPattern.worldPos(worldPosition, facing, MultiblockPattern.PORT_LOCAL);
        if (!(level.getBlockEntity(portPos) instanceof MultiblockPortBlockEntity port)) {
            dissolve(level, facing);
            return MultiblockValidationResult.INVALID;
        }

        markRevalidatedFormed();
        port.bindToController(worldPosition, formationRevision);
        setVisualFormed(level, facing, true);
        return MultiblockValidationResult.VALID;
    }

    public void beforeControllerRemoval(ServerLevel level, Direction facing) {
        BlockPos portPos = MultiblockPattern.worldPos(worldPosition, facing, MultiblockPattern.PORT_LOCAL);
        if (!level.hasChunkAt(portPos)) {
            return;
        }
        if (level.getBlockEntity(portPos) instanceof MultiblockPortBlockEntity port) {
            port.clearBinding();
        }
        BlockState portState = level.getBlockState(portPos);
        if (portState.is(I10MultiblockContent.MULTIBLOCK_IO_PORT.get())) {
            level.setBlock(
                    portPos,
                    portState.setValue(MultiblockPortBlock.FACING, facing).setValue(MultiblockPortBlock.FORMED, false),
                    Block.UPDATE_CLIENTS);
        }
        level.invalidateCapabilities(portPos);
    }

    private void dissolve(ServerLevel level, Direction facing) {
        BlockPos portPos = MultiblockPattern.worldPos(worldPosition, facing, MultiblockPattern.PORT_LOCAL);
        if (level.hasChunkAt(portPos)
                && level.getBlockEntity(portPos) instanceof MultiblockPortBlockEntity port) {
            port.clearBinding();
        }
        markUnformed();
        setVisualFormed(level, facing, false);
    }

    private void setVisualFormed(ServerLevel level, Direction facing, boolean formed) {
        BlockState controllerState = level.getBlockState(worldPosition);
        if (controllerState.is(I10MultiblockContent.MULTIBLOCK_CONTROLLER.get())) {
            level.setBlock(
                    worldPosition,
                    controllerState
                            .setValue(MultiblockControllerBlock.FACING, facing)
                            .setValue(MultiblockControllerBlock.FORMED, formed),
                    Block.UPDATE_CLIENTS);
        }

        BlockPos portPos = MultiblockPattern.worldPos(worldPosition, facing, MultiblockPattern.PORT_LOCAL);
        if (!level.hasChunkAt(portPos)) {
            return;
        }
        BlockState portState = level.getBlockState(portPos);
        if (portState.is(I10MultiblockContent.MULTIBLOCK_IO_PORT.get())) {
            level.setBlock(
                    portPos,
                    portState
                            .setValue(MultiblockPortBlock.FACING, facing)
                            .setValue(MultiblockPortBlock.FORMED, formed),
                    Block.UPDATE_CLIENTS);
        }
        level.invalidateCapabilities(portPos);
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
