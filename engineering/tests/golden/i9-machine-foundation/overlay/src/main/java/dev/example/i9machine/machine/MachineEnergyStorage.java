package dev.example.i9machine.machine;

import net.neoforged.neoforge.energy.IEnergyStorage;

public final class MachineEnergyStorage implements IEnergyStorage {
    public static final int ENERGY_CAPACITY = 10_000;
    public static final int MAX_RECEIVE = 1_000;

    private final Runnable onChanged;
    private int energy;

    public MachineEnergyStorage(Runnable onChanged) {
        this.onChanged = onChanged;
    }

    @Override
    public int receiveEnergy(int maxReceive, boolean simulate) {
        if (maxReceive <= 0) {
            return 0;
        }
        int accepted = Math.min(Math.min(maxReceive, MAX_RECEIVE), ENERGY_CAPACITY - energy);
        if (!simulate && accepted > 0) {
            energy += accepted;
            onChanged.run();
        }
        return accepted;
    }

    @Override
    public int extractEnergy(int maxExtract, boolean simulate) {
        return 0;
    }

    @Override
    public int getEnergyStored() {
        return energy;
    }

    @Override
    public int getMaxEnergyStored() {
        return ENERGY_CAPACITY;
    }

    @Override
    public boolean canExtract() {
        return false;
    }

    @Override
    public boolean canReceive() {
        return true;
    }

    public boolean consumeInternal(int amount) {
        if (amount <= 0 || energy < amount) {
            return false;
        }
        energy -= amount;
        onChanged.run();
        return true;
    }

    public void loadClamped(int value) {
        int clamped = Math.max(0, Math.min(ENERGY_CAPACITY, value));
        if (energy != clamped) {
            energy = clamped;
            onChanged.run();
        }
    }
}
