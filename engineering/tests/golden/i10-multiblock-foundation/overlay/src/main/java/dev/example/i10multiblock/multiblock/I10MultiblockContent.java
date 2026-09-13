package dev.example.i10multiblock.multiblock;

import dev.example.i10multiblock.I10MultiblockMod;
import java.util.function.Supplier;
import net.minecraft.core.registries.Registries;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.neoforge.capabilities.Capabilities;
import net.neoforged.neoforge.capabilities.RegisterCapabilitiesEvent;
import net.neoforged.neoforge.registries.DeferredRegister;

public final class I10MultiblockContent {
    public static final DeferredRegister.Blocks BLOCKS = DeferredRegister.createBlocks(I10MultiblockMod.MOD_ID);
    public static final DeferredRegister.Items ITEMS = DeferredRegister.createItems(I10MultiblockMod.MOD_ID);
    public static final DeferredRegister<BlockEntityType<?>> BLOCK_ENTITY_TYPES =
            DeferredRegister.create(Registries.BLOCK_ENTITY_TYPE, I10MultiblockMod.MOD_ID);

    public static final Supplier<MultiblockControllerBlock> MULTIBLOCK_CONTROLLER = BLOCKS.registerBlock(
            "multiblock_controller", MultiblockControllerBlock::new, BlockBehaviour.Properties.of());
    public static final Supplier<MultiblockCasingBlock> MULTIBLOCK_CASING = BLOCKS.registerBlock(
            "multiblock_casing", MultiblockCasingBlock::new, BlockBehaviour.Properties.of());
    public static final Supplier<MultiblockPortBlock> MULTIBLOCK_IO_PORT = BLOCKS.registerBlock(
            "multiblock_io_port", MultiblockPortBlock::new, BlockBehaviour.Properties.of());

    public static final Supplier<BlockItem> MULTIBLOCK_CONTROLLER_ITEM =
            ITEMS.registerSimpleBlockItem("multiblock_controller", MULTIBLOCK_CONTROLLER);
    public static final Supplier<BlockItem> MULTIBLOCK_CASING_ITEM =
            ITEMS.registerSimpleBlockItem("multiblock_casing", MULTIBLOCK_CASING);
    public static final Supplier<BlockItem> MULTIBLOCK_IO_PORT_ITEM =
            ITEMS.registerSimpleBlockItem("multiblock_io_port", MULTIBLOCK_IO_PORT);

    public static final Supplier<BlockEntityType<MultiblockControllerBlockEntity>> MULTIBLOCK_CONTROLLER_BLOCK_ENTITY =
            BLOCK_ENTITY_TYPES.register("multiblock_controller", () -> BlockEntityType.Builder.of(
                    MultiblockControllerBlockEntity::new, MULTIBLOCK_CONTROLLER.get()).build(null));
    public static final Supplier<BlockEntityType<MultiblockPortBlockEntity>> MULTIBLOCK_IO_PORT_BLOCK_ENTITY =
            BLOCK_ENTITY_TYPES.register("multiblock_io_port", () -> BlockEntityType.Builder.of(
                    MultiblockPortBlockEntity::new, MULTIBLOCK_IO_PORT.get()).build(null));

    private I10MultiblockContent() {
    }

    public static void register(IEventBus modBus) {
        BLOCKS.register(modBus);
        ITEMS.register(modBus);
        BLOCK_ENTITY_TYPES.register(modBus);
    }

    public static void registerCapabilities(RegisterCapabilitiesEvent event) {
        event.registerBlockEntity(
                Capabilities.ItemHandler.BLOCK,
                MULTIBLOCK_IO_PORT_BLOCK_ENTITY.get(),
                (blockEntity, side) -> blockEntity.itemHandler());
    }
}
