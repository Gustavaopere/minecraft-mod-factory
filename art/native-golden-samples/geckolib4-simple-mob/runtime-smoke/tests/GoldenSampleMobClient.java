package dev.example.i3golden.client;

import dev.example.i3golden.GoldenSampleMob;
import dev.example.i3golden.GoldenSampleMobRegistry;
import dev.example.i3golden.I3GoldenMod;
import net.minecraft.resources.ResourceLocation;
import net.neoforged.neoforge.client.event.EntityRenderersEvent;
import software.bernie.geckolib.model.DefaultedEntityGeoModel;
import software.bernie.geckolib.renderer.GeoEntityRenderer;

public final class GoldenSampleMobClient {
    private GoldenSampleMobClient() {
    }

    public static void registerRenderers(EntityRenderersEvent.RegisterRenderers event) {
        event.registerEntityRenderer(
                GoldenSampleMobRegistry.GOLDEN_SAMPLE_MOB.get(),
                context -> new GeoEntityRenderer<GoldenSampleMob>(
                        context,
                        new DefaultedEntityGeoModel<>(ResourceLocation.fromNamespaceAndPath(
                                I3GoldenMod.MOD_ID,
                                "golden_sample_mob"))));
    }
}
