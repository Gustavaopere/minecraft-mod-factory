package dev.example.i9machine.machine;

import dev.example.i9machine.I9MachineMod;
import java.util.function.Supplier;
import net.minecraft.core.registries.Registries;
import net.minecraft.world.flag.FeatureFlags;
import net.minecraft.world.inventory.MenuType;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.neoforge.capabilities.Capabilities;
import net.neoforged.neoforge.capabilities.RegisterCapabilitiesEvent;
import net.neoforged.neoforge.registries.DeferredRegister;

public final class I9MachineContent {
    public static final DeferredRegister.Blocks BLOCKS = DeferredRegister.createBlocks(I9MachineMod.MOD_ID);
    public static final DeferredRegister.Items ITEMS = DeferredRegister.createItems(I9MachineMod.MOD_ID);
    public static final DeferredRegister<BlockEntityType<?>> BLOCK_ENTITY_TYPES =
            DeferredRegister.create(Registries.BLOCK_ENTITY_TYPE, I9MachineMod.MOD_ID);
    public static final DeferredRegister<MenuType<?>> MENUS =
            DeferredRegister.create(Registries.MENU, I9MachineMod.MOD_ID);

    public static final Supplier<MachineBlock> MACHINE = BLOCKS.registerBlock(
            "machine", MachineBlock::new, BlockBehaviour.Properties.of());
    public static final Supplier<BlockItem> MACHINE_ITEM = ITEMS.registerSimpleBlockItem("machine", MACHINE);
    public static final Supplier<BlockEntityType<MachineBlockEntity>> MACHINE_BLOCK_ENTITY =
            BLOCK_ENTITY_TYPES.register("machine", () -> BlockEntityType.Builder.of(
                    MachineBlockEntity::new, MACHINE.get()).build(null));
    public static final Supplier<MenuType<MachineMenu>> MACHINE_MENU =
            MENUS.register("machine", () -> new MenuType<>(MachineMenu::new, FeatureFlags.DEFAULT_FLAGS));

    private I9MachineContent() {
    }

    public static void register(IEventBus modBus) {
        BLOCKS.register(modBus);
        ITEMS.register(modBus);
        BLOCK_ENTITY_TYPES.register(modBus);
        MENUS.register(modBus);
    }

    public static void registerCapabilities(RegisterCapabilitiesEvent event) {
        event.registerBlockEntity(
                Capabilities.ItemHandler.BLOCK,
                MACHINE_BLOCK_ENTITY.get(),
                (blockEntity, side) -> blockEntity.itemHandler());
        event.registerBlockEntity(
                Capabilities.EnergyStorage.BLOCK,
                MACHINE_BLOCK_ENTITY.get(),
                (blockEntity, side) -> blockEntity.energyStorage());
    }
}
