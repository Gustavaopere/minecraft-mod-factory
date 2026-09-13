package dev.example.i9machine.machine;

import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ContainerData;
import net.minecraft.world.inventory.ContainerLevelAccess;
import net.minecraft.world.inventory.SimpleContainerData;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.ItemStack;
import net.neoforged.neoforge.items.IItemHandler;
import net.neoforged.neoforge.items.ItemStackHandler;
import net.neoforged.neoforge.items.SlotItemHandler;

public final class MachineMenu extends AbstractContainerMenu {
    private static final int MACHINE_SLOT_COUNT = 2;
    private static final int PLAYER_INVENTORY_END = 38;

    private final ContainerLevelAccess access;

    public MachineMenu(int containerId, Inventory inventory) {
        this(
                containerId,
                inventory,
                new ItemStackHandler(MACHINE_SLOT_COUNT),
                new SimpleContainerData(3),
                ContainerLevelAccess.NULL);
    }

    public MachineMenu(
            int containerId,
            Inventory playerInventory,
            IItemHandler machineInventory,
            ContainerData data,
            ContainerLevelAccess access) {
        super(I9MachineContent.MACHINE_MENU.get(), containerId);
        checkContainerDataCount(data, 3);
        this.access = access;

        addSlot(new SlotItemHandler(machineInventory, MachineBlockEntity.INPUT_SLOT, 44, 35));
        addSlot(new SlotItemHandler(machineInventory, MachineBlockEntity.OUTPUT_SLOT, 116, 35));

        for (int row = 0; row < 3; row++) {
            for (int column = 0; column < 9; column++) {
                addSlot(new Slot(playerInventory, column + row * 9 + 9, 8 + column * 18, 84 + row * 18));
            }
        }
        for (int column = 0; column < 9; column++) {
            addSlot(new Slot(playerInventory, column, 8 + column * 18, 142));
        }
        addDataSlots(data);
    }

    @Override
    public ItemStack quickMoveStack(Player player, int index) {
        if (index < 0 || index >= slots.size()) {
            return ItemStack.EMPTY;
        }
        Slot slot = slots.get(index);
        if (!slot.hasItem()) {
            return ItemStack.EMPTY;
        }

        ItemStack stack = slot.getItem();
        ItemStack original = stack.copy();
        if (index < MACHINE_SLOT_COUNT) {
            if (!moveItemStackTo(stack, MACHINE_SLOT_COUNT, PLAYER_INVENTORY_END, true)) {
                return ItemStack.EMPTY;
            }
        } else if (!moveItemStackTo(stack, MachineBlockEntity.INPUT_SLOT, MachineBlockEntity.INPUT_SLOT + 1, false)) {
            return ItemStack.EMPTY;
        }

        if (stack.isEmpty()) {
            slot.setByPlayer(ItemStack.EMPTY);
        } else {
            slot.setChanged();
        }
        if (stack.getCount() == original.getCount()) {
            return ItemStack.EMPTY;
        }
        slot.onTake(player, stack);
        return original;
    }

    @Override
    public boolean stillValid(Player player) {
        return stillValid(access, player, I9MachineContent.MACHINE_BLOCK.get());
    }
}
