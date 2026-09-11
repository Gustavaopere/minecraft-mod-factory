package dev.example.i3golden;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.google.gson.JsonParser;
import com.mojang.serialization.JsonOps;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import net.neoforged.neoforge.client.entity.animation.json.AnimationParser;
import org.junit.jupiter.api.Test;

final class NeoForgeNativeAnimationRuntimeSmokeTest {
    private static final String RESOURCE =
            "/assets/i3_golden_mod/neoforge/animations/entity/pr8_runtime_smoke.json";

    @Test
    void factoryExportDecodesWithNeoForgeRuntimeCodec() throws Exception {
        try (var stream = NeoForgeNativeAnimationRuntimeSmokeTest.class.getResourceAsStream(RESOURCE)) {
            assertNotNull(stream, "Factory PR8 runtime resource must be staged into the generated I3 project");
            final var json = JsonParser.parseReader(new InputStreamReader(stream, StandardCharsets.UTF_8));
            final var animation = AnimationParser.CODEC.parse(JsonOps.INSTANCE, json).getOrThrow();

            assertEquals(1.0F, animation.lengthInSeconds(), 0.0001F);
            assertTrue(animation.looping());
            assertTrue(animation.boneAnimations().containsKey("root"));
            assertEquals(1, animation.boneAnimations().get("root").size());
        }
    }
}
