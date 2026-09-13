package dev.example.i9machine.gametest;

import dev.example.i9machine.I9MachineMod;
import dev.example.i9machine.machine.I9MachineContent;
import dev.example.i9machine.machine.MachineBlockEntity;
import dev.example.i9machine.machine.MachineEnergyStorage;
import net.minecraft.core.BlockPos;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.neoforged.neoforge.capabilities.Capabilities;
import net.neoforged.neoforge.energy.IEnergyStorage;
import net.neoforged.neoforge.gametest.GameTestHolder;
import net.neoforged.neoforge.gametest.PrefixGameTestTemplate;
import net.neoforged.neoforge.items.IItemHandler;

@GameTestHolder(I9MachineMod.MOD_ID)
@PrefixGameTestTemplate(false)
public final class I9MachineGameTests {
    private static final BlockPos MACHINE_POS = new BlockPos(1, 1, 1);

    private I9MachineGameTests() {
    }

    @GameTest(template = "machine_test", timeoutTicks = 160)
    public static void inventoryCapability(GameTestHelper helper) {
        placeMachine(helper);
        IItemHandler items = requireItemCapability(helper);

        ItemStack acceptedInput = items.insertItem(
                MachineBlockEntity.INPUT_SLOT, new ItemStack(Items.RAW_IRON), true);
        if (!acceptedInput.isEmpty()) {
            helper.fail("Expected raw iron to be accepted by the input slot", MACHINE_POS);
        }

        ItemStack invalidInput = items.insertItem(
                MachineBlockEntity.INPUT_SLOT, new ItemStack(Items.COBBLESTONE), true);
        if (invalidInput.isEmpty()) {
            helper.fail("Expected non-smeltable cobblestone to be rejected by the input slot", MACHINE_POS);
        }

        ItemStack rejectedOutput = items.insertItem(
                MachineBlockEntity.OUTPUT_SLOT, new ItemStack(Items.IRON_INGOT), true);
        if (rejectedOutput.isEmpty()) {
            helper.fail("Expected manual output insertion to be rejected", MACHINE_POS);
        }

        helper.succeed();
    }

    @GameTest(template = "machine_test", timeoutTicks = 160)
    public static void energyCapability(GameTestHelper helper) {
        placeMachine(helper);
        IEnergyStorage energy = requireEnergyCapability(helper);

        if (energy.getMaxEnergyStored() != MachineEnergyStorage.ENERGY_CAPACITY) {
            helper.fail("Unexpected machine energy capacity", MACHINE_POS);
        }
        if (!energy.canReceive() || energy.canExtract()) {
            helper.fail("Unexpected external energy IO policy", MACHINE_POS);
        }

        int accepted = energy.receiveEnergy(2_000, false);
        if (accepted != MachineEnergyStorage.MAX_RECEIVE || energy.getEnergyStored() != 1_000) {
            helper.fail("External receive must be capped at 1000 per call", MACHINE_POS);
        }
        if (energy.extractEnergy(1_000, false) != 0 || energy.getEnergyStored() != 1_000) {
            helper.fail("External extraction must remain disabled", MACHINE_POS);
        }

        helper.succeed();
    }

    @GameTest(template = "machine_test", timeoutTicks = 160)
    public static void successfulProcessing(GameTestHelper helper) {
        MachineBlockEntity machine = placeMachine(helper);
        machine.itemHandler().setStackInSlot(
                MachineBlockEntity.INPUT_SLOT, new ItemStack(Items.RAW_IRON));
        charge(machine, 2_000, helper);

        helper.runAtTickTime(110, () -> {
            ItemStack input = machine.itemHandler().getStackInSlot(MachineBlockEntity.INPUT_SLOT);
            ItemStack output = machine.itemHandler().getStackInSlot(MachineBlockEntity.OUTPUT_SLOT);
            if (!input.isEmpty()) {
                helper.fail("Successful processing must consume one raw iron", MACHINE_POS);
            }
            if (!output.is(Items.IRON_INGOT) || output.getCount() != 1) {
                helper.fail("Successful processing must produce one iron ingot", MACHINE_POS);
            }
            if (machine.data().get(0) != 0 || machine.energyStorage().getEnergyStored() != 0) {
                helper.fail("Successful processing must reset progress and consume 2000 energy", MACHINE_POS);
            }
            helper.succeed();
        });
    }

    @GameTest(template = "machine_test", timeoutTicks = 160)
    public static void insufficientEnergy(GameTestHelper helper) {
        MachineBlockEntity machine = placeMachine(helper);
        machine.itemHandler().setStackInSlot(
                MachineBlockEntity.INPUT_SLOT, new ItemStack(Items.RAW_IRON));
        charge(machine, MachineBlockEntity.ENERGY_PER_TICK - 1, helper);

        helper.runAtTickTime(10, () -> {
            ItemStack input = machine.itemHandler().getStackInSlot(MachineBlockEntity.INPUT_SLOT);
            ItemStack output = machine.itemHandler().getStackInSlot(MachineBlockEntity.OUTPUT_SLOT);
            if (!input.is(Items.RAW_IRON) || input.getCount() != 1) {
                helper.fail("Insufficient energy must not consume input", MACHINE_POS);
            }
            if (!output.isEmpty() || machine.data().get(0) != 0) {
                helper.fail("Insufficient energy must not produce output or retain progress", MACHINE_POS);
            }
            helper.succeed();
        });
    }

    @GameTest(template = "machine_test", timeoutTicks = 160)
    public static void blockedOutput(GameTestHelper helper) {
        MachineBlockEntity machine = placeMachine(helper);
        machine.itemHandler().setStackInSlot(
                MachineBlockEntity.INPUT_SLOT, new ItemStack(Items.RAW_IRON));
        machine.itemHandler().setStackInSlot(
                MachineBlockEntity.OUTPUT_SLOT, new ItemStack(Items.DIAMOND));
        charge(machine, 2_000, helper);

        helper.runAtTickTime(10, () -> {
            ItemStack input = machine.itemHandler().getStackInSlot(MachineBlockEntity.INPUT_SLOT);
            ItemStack output = machine.itemHandler().getStackInSlot(MachineBlockEntity.OUTPUT_SLOT);
            if (!input.is(Items.RAW_IRON) || input.getCount() != 1) {
                helper.fail("Blocked output must not consume input", MACHINE_POS);
            }
            if (!output.is(Items.DIAMOND) || output.getCount() != 1) {
                helper.fail("Blocked output must not be overwritten", MACHINE_POS);
            }
            if (machine.data().get(0) != 0 || machine.energyStorage().getEnergyStored() != 2_000) {
                helper.fail("Blocked output must not retain progress or consume energy", MACHINE_POS);
            }
            helper.succeed();
        });
    }

    @GameTest(template = "machine_test", timeoutTicks = 160)
    public static void persistence(GameTestHelper helper) {
        MachineBlockEntity machine = placeMachine(helper);
        machine.itemHandler().setStackInSlot(
                MachineBlockEntity.INPUT_SLOT, new ItemStack(Items.RAW_IRON));
        charge(machine, 1_000, helper);
        machine.data().set(0, 42);

        CompoundTag saved = machine.saveWithFullMetadata(helper.getLevel().registryAccess());
        MachineBlockEntity restored = loadMachine(helper, machine, saved);
        assertPersistedState(helper, restored, 1_000, 42);

        CompoundTag high = saved.copy();
        high.putInt("Energy", 50_000);
        high.putInt("Progress", 500);
        MachineBlockEntity highClamped = loadMachine(helper, machine, high);
        if (highClamped.energyStorage().getEnergyStored() != MachineEnergyStorage.ENERGY_CAPACITY
                || highClamped.data().get(0) != MachineBlockEntity.MAX_PROGRESS - 1) {
            helper.fail("Persisted high numeric values must clamp to machine bounds", MACHINE_POS);
        }

        CompoundTag low = saved.copy();
        low.putInt("Energy", -1);
        low.putInt("Progress", -1);
        MachineBlockEntity lowClamped = loadMachine(helper, machine, low);
        if (lowClamped.energyStorage().getEnergyStored() != 0 || lowClamped.data().get(0) != 0) {
            helper.fail("Persisted negative numeric values must clamp to zero", MACHINE_POS);
        }

        helper.succeed();
    }

    @GameTest(template = "machine_test", timeoutTicks = 160)
    public static void progressReset(GameTestHelper helper) {
        MachineBlockEntity machine = placeMachine(helper);
        machine.itemHandler().setStackInSlot(
                MachineBlockEntity.INPUT_SLOT, new ItemStack(Items.RAW_IRON));
        charge(machine, 1_000, helper);

        helper.runAtTickTime(5, () -> {
            if (machine.data().get(0) <= 0) {
                helper.fail("Expected processing progress before invalidating input", MACHINE_POS);
            }
            machine.itemHandler().setStackInSlot(
                    MachineBlockEntity.INPUT_SLOT, new ItemStack(Items.COBBLESTONE));
        });

        helper.runAtTickTime(7, () -> {
            if (machine.data().get(0) != 0) {
                helper.fail("Invalidated input must reset progress to zero", MACHINE_POS);
            }
            if (!machine.itemHandler().getStackInSlot(MachineBlockEntity.OUTPUT_SLOT).isEmpty()) {
                helper.fail("Invalidated input must not create output", MACHINE_POS);
            }
            helper.succeed();
        });
    }

    private static MachineBlockEntity placeMachine(GameTestHelper helper) {
        helper.setBlock(MACHINE_POS, I9MachineContent.MACHINE.get());
        BlockEntity blockEntity = helper.getBlockEntity(MACHINE_POS);
        if (!(blockEntity instanceof MachineBlockEntity machine)) {
            helper.fail("Expected MachineBlockEntity", MACHINE_POS);
            throw new IllegalStateException("GameTest machine BlockEntity missing");
        }
        return machine;
    }

    private static IItemHandler requireItemCapability(GameTestHelper helper) {
        IItemHandler capability = helper.getLevel().getCapability(
                Capabilities.ItemHandler.BLOCK, helper.absolutePos(MACHINE_POS), null);
        if (capability == null) {
            helper.fail("Expected item handler capability", MACHINE_POS);
            throw new IllegalStateException("GameTest item capability missing");
        }
        return capability;
    }

    private static IEnergyStorage requireEnergyCapability(GameTestHelper helper) {
        IEnergyStorage capability = helper.getLevel().getCapability(
                Capabilities.EnergyStorage.BLOCK, helper.absolutePos(MACHINE_POS), null);
        if (capability == null) {
            helper.fail("Expected energy storage capability", MACHINE_POS);
            throw new IllegalStateException("GameTest energy capability missing");
        }
        return capability;
    }

    private static void charge(MachineBlockEntity machine, int amount, GameTestHelper helper) {
        int remaining = amount;
        while (remaining > 0) {
            int accepted = machine.energyStorage().receiveEnergy(remaining, false);
            if (accepted <= 0) {
                helper.fail("Machine could not receive requested test energy", MACHINE_POS);
                return;
            }
            remaining -= accepted;
        }
    }

    private static MachineBlockEntity loadMachine(
            GameTestHelper helper, MachineBlockEntity source, CompoundTag tag) {
        BlockEntity loaded = BlockEntity.loadStatic(
                source.getBlockPos(),
                source.getBlockState(),
                tag,
                helper.getLevel().registryAccess());
        if (!(loaded instanceof MachineBlockEntity machine)) {
            helper.fail("Serialized machine could not be loaded", MACHINE_POS);
            throw new IllegalStateException("GameTest serialized machine failed to load");
        }
        return machine;
    }

    private static void assertPersistedState(
            GameTestHelper helper, MachineBlockEntity machine, int energy, int progress) {
        ItemStack input = machine.itemHandler().getStackInSlot(MachineBlockEntity.INPUT_SLOT);
        if (!input.is(Items.RAW_IRON) || input.getCount() != 1) {
            helper.fail("Persisted inventory did not survive serialization", MACHINE_POS);
        }
        if (machine.energyStorage().getEnergyStored() != energy || machine.data().get(0) != progress) {
            helper.fail("Persisted energy/progress did not survive serialization", MACHINE_POS);
        }
    }
}
