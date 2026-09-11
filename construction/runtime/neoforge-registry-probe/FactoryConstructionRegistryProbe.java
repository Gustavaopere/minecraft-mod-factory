package dev.minecraftmodfactory.constructionprobe;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Locale;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.EntityBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.Property;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.ModContainer;
import net.neoforged.fml.common.Mod;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.event.server.ServerStartedEvent;

@Mod(FactoryConstructionRegistryProbe.MOD_ID)
public final class FactoryConstructionRegistryProbe {
    public static final String MOD_ID = "factory_construction_registry_probe";
    private static final String MINECRAFT_VERSION = "1.21.1";
    private static final String NEOFORGE_VERSION = "21.1.248";
    private static final String OUTPUT_PROPERTY = "factory.construction.registryOutput";
    private static final String PHYSICAL_SHA_PROPERTY = "factory.construction.physicalSnapshotSha256";
    private static final Gson GSON = new GsonBuilder().disableHtmlEscaping().setPrettyPrinting().create();

    public FactoryConstructionRegistryProbe(IEventBus modBus, ModContainer container) {
        NeoForge.EVENT_BUS.addListener(this::onServerStarted);
    }

    private void onServerStarted(ServerStartedEvent event) {
        Path output = requiredOutputPath();
        String physicalSnapshotSha256 = requiredPhysicalSnapshotSha256();
        JsonObject root = buildRuntimeSnapshot(physicalSnapshotSha256);
        try {
            Path parent = output.getParent();
            if (parent != null) {
                Files.createDirectories(parent);
            }
            Files.writeString(output, GSON.toJson(root) + System.lineSeparator(), StandardCharsets.UTF_8);
        } catch (IOException exception) {
            throw new IllegalStateException("Failed to write Construction runtime registry snapshot to " + output, exception);
        }
    }

    private static JsonObject buildRuntimeSnapshot(String physicalSnapshotSha256) {
        JsonObject root = new JsonObject();
        root.addProperty("schema_version", 1);
        root.addProperty("captured_at", Instant.now().toString());
        root.addProperty("physical_snapshot_sha256", physicalSnapshotSha256);

        JsonObject target = new JsonObject();
        target.addProperty("minecraft", MINECRAFT_VERSION);
        target.addProperty("loader", "neoforge");
        target.addProperty("loader_version", NEOFORGE_VERSION);
        root.add("target", target);

        JsonArray blocks = new JsonArray();
        List<ResourceLocation> blockIds = BuiltInRegistries.BLOCK.keySet().stream()
                .sorted(Comparator.comparing(ResourceLocation::toString))
                .toList();
        for (ResourceLocation blockId : blockIds) {
            Block block = BuiltInRegistries.BLOCK.get(blockId);
            if (block == null) {
                continue;
            }
            JsonObject blockJson = new JsonObject();
            blockJson.addProperty("id", blockId.toString());
            blockJson.addProperty("safety", block instanceof EntityBlock ? "block_entity" : "ordinary");

            JsonArray states = new JsonArray();
            for (BlockState state : block.getStateDefinition().getPossibleStates()) {
                JsonObject stateJson = new JsonObject();
                List<Property<?>> properties = new ArrayList<>(state.getProperties());
                properties.sort(Comparator.comparing(property -> property.getName()));
                for (Property<?> property : properties) {
                    appendProperty(stateJson, state, property);
                }
                states.add(stateJson);
            }
            blockJson.add("states", states);
            blocks.add(blockJson);
        }
        root.add("blocks", blocks);
        return root;
    }

    private static <T extends Comparable<T>> void appendProperty(JsonObject target, BlockState state, Property<T> property) {
        T value = state.getValue(property);
        target.addProperty(property.getName(), property.getName(value));
    }

    private static Path requiredOutputPath() {
        String value = System.getProperty(OUTPUT_PROPERTY);
        if (value == null || value.isBlank()) {
            throw new IllegalStateException("Missing required system property: " + OUTPUT_PROPERTY);
        }
        return Path.of(value).toAbsolutePath().normalize();
    }

    private static String requiredPhysicalSnapshotSha256() {
        String value = System.getProperty(PHYSICAL_SHA_PROPERTY);
        if (value == null || !value.matches("[0-9a-fA-F]{64}")) {
            throw new IllegalStateException("Missing or invalid required SHA-256 system property: " + PHYSICAL_SHA_PROPERTY);
        }
        return value.toLowerCase(Locale.ROOT);
    }
}
