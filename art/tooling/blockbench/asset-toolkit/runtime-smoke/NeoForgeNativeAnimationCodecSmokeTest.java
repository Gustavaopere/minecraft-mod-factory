import static org.junit.jupiter.api.Assertions.assertNotNull;

import com.google.gson.JsonElement;
import com.google.gson.JsonParser;
import com.mojang.serialization.JsonOps;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import net.minecraft.client.animation.AnimationDefinition;
import net.neoforged.neoforge.client.entity.animation.json.AnimationParser;
import org.junit.jupiter.api.Test;

final class NeoForgeNativeAnimationCodecSmokeTest {
    private static final String RESOURCE_PATH =
            "assets/factorypr8/neoforge/animations/entity/native_smoke.json";

    @Test
    void animationParserCodecParsesTargetExactRuntimeResource() throws Exception {
        ClassLoader loader = NeoForgeNativeAnimationCodecSmokeTest.class.getClassLoader();
        try (InputStream stream = loader.getResourceAsStream(RESOURCE_PATH)) {
            assertNotNull(stream, "target-exact NeoForge animation JSON fixture must be on the test classpath");
            JsonElement json = JsonParser.parseReader(new InputStreamReader(stream, StandardCharsets.UTF_8));
            AnimationDefinition definition = AnimationParser.CODEC.parse(JsonOps.INSTANCE, json).getOrThrow();
            assertNotNull(definition, "NeoForge 21.1.248 AnimationParser.CODEC must parse the fixture");
        }
    }
}
