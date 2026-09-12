package dev.example.i3golden.client;

import dev.example.i3golden.GoldenSampleMobRegistry;
import net.neoforged.neoforge.client.event.EntityRenderersEvent;

public final class GoldenSampleMobClient {
    private GoldenSampleMobClient() {
    }

    public static void registerRenderers(EntityRenderersEvent.RegisterRenderers event) {
        event.registerEntityRenderer(
                GoldenSampleMobRegistry.GOLDEN_SAMPLE_MOB.get(),
                GoldenSampleMobClientRuntimeProof::createRenderer);
    }
}
