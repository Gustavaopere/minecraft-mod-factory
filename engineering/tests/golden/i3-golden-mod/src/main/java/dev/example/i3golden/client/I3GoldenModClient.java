package dev.example.i3golden.client;

import dev.example.i3golden.I3GoldenMod;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.common.Mod;

@Mod(value = I3GoldenMod.MOD_ID, dist = Dist.CLIENT)
public final class I3GoldenModClient {
    public I3GoldenModClient(IEventBus modBus) {
    }
}
