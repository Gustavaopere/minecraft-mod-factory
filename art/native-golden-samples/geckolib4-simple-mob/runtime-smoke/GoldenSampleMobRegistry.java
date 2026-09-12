package dev.example.i3golden;

import java.util.function.Supplier;
import net.minecraft.core.registries.Registries;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.neoforge.registries.DeferredRegister;

public final class GoldenSampleMobRegistry {
    public static final DeferredRegister<EntityType<?>> ENTITY_TYPES =
            DeferredRegister.create(Registries.ENTITY_TYPE, I3GoldenMod.MOD_ID);

    public static final Supplier<EntityType<GoldenSampleMob>> GOLDEN_SAMPLE_MOB = ENTITY_TYPES.register(
            "golden_sample_mob",
            () -> EntityType.Builder.of(GoldenSampleMob::new, MobCategory.MISC)
                    .sized(0.75F, 1.5F)
                    .build(I3GoldenMod.MOD_ID + ":golden_sample_mob"));

    private GoldenSampleMobRegistry() {
    }

    public static void register(IEventBus modBus) {
        ENTITY_TYPES.register(modBus);
    }
}
