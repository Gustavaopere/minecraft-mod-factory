package dev.example.i3golden.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import dev.example.i3golden.GoldenSampleMob;
import dev.example.i3golden.I3GoldenMod;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Locale;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.screens.AccessibilityOnboardingScreen;
import net.minecraft.client.gui.screens.ConnectScreen;
import net.minecraft.client.gui.screens.TitleScreen;
import net.minecraft.client.multiplayer.ServerData;
import net.minecraft.client.multiplayer.resolver.ServerAddress;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.resources.ResourceLocation;
import net.neoforged.neoforge.client.event.ClientTickEvent;
import org.jetbrains.annotations.Nullable;
import software.bernie.geckolib.cache.object.BakedGeoModel;
import software.bernie.geckolib.model.DefaultedEntityGeoModel;
import software.bernie.geckolib.renderer.GeoEntityRenderer;

public final class GoldenSampleMobClientRuntimeProof {
    private static final ResourceLocation ASSET = ResourceLocation.fromNamespaceAndPath(
            I3GoldenMod.MOD_ID,
            "golden_sample_mob");
    private static final ResourceLocation EXPECTED_TEXTURE = ResourceLocation.fromNamespaceAndPath(
            I3GoldenMod.MOD_ID,
            "textures/entity/golden_sample_mob.png");
    private static final String SERVER_HOST = "127.0.0.1";
    private static final int SERVER_PORT = 25565;
    private static final float MOTION_EPSILON = 0.0001F;
    private static boolean connectStarted;
    private static boolean clientJoinedLogged;
    private static String lastScreenClass = "";

    private GoldenSampleMobClientRuntimeProof() {
    }

    public static GeoEntityRenderer<GoldenSampleMob> createRenderer(EntityRendererProvider.Context context) {
        return new ProofRenderer(context);
    }

    public static void onClientTick(ClientTickEvent.Post event) {
        Minecraft minecraft = Minecraft.getInstance();
        String screenClass = minecraft.screen == null ? "<null>" : minecraft.screen.getClass().getName();
        if (!screenClass.equals(lastScreenClass)) {
            lastScreenClass = screenClass;
            System.out.println("[GECKOLIB_CLIENT_PROOF] screen=" + screenClass);
        }

        boolean startupReady = minecraft.screen instanceof TitleScreen
                || minecraft.screen instanceof AccessibilityOnboardingScreen;
        if (!connectStarted && startupReady) {
            connectStarted = true;
            String address = SERVER_HOST + ":" + SERVER_PORT;
            ServerData serverData = new ServerData(
                    "Factory GeckoLib client proof",
                    address,
                    ServerData.Type.OTHER);
            ConnectScreen.startConnecting(
                    minecraft.screen,
                    minecraft,
                    ServerAddress.parseString(address),
                    serverData,
                    false,
                    null);
            System.out.println("[GECKOLIB_CLIENT_PROOF] connect_started=true address=" + address);
        }

        if (!clientJoinedLogged && minecraft.player != null && minecraft.getConnection() != null) {
            clientJoinedLogged = true;
            System.out.println("[GECKOLIB_CLIENT_PROOF] client_joined=true");
        }
    }

    private static final class ProofRenderer extends GeoEntityRenderer<GoldenSampleMob> {
        private Float firstHeadRotationY;
        private boolean rendererInvoked;
        private boolean bakedModelObserved;
        private boolean textureResolved;
        private boolean animationMotionObserved;
        private boolean rendererLogged;
        private boolean bakedModelLogged;
        private boolean textureLogged;
        private boolean animationLogged;
        private boolean evidenceWritten;

        private ProofRenderer(EntityRendererProvider.Context context) {
            super(context, new DefaultedEntityGeoModel<>(ASSET));
        }

        @Override
        public void actuallyRender(
                PoseStack poseStack,
                GoldenSampleMob animatable,
                BakedGeoModel model,
                @Nullable RenderType renderType,
                MultiBufferSource bufferSource,
                @Nullable VertexConsumer buffer,
                boolean isReRender,
                float partialTick,
                int packedLight,
                int packedOverlay,
                int colour) {
            super.actuallyRender(
                    poseStack,
                    animatable,
                    model,
                    renderType,
                    bufferSource,
                    buffer,
                    isReRender,
                    partialTick,
                    packedLight,
                    packedOverlay,
                    colour);

            if (isReRender || this.evidenceWritten) {
                return;
            }

            this.rendererInvoked = true;
            if (!this.rendererLogged) {
                System.out.println("[GECKOLIB_CLIENT_PROOF] renderer_invoked=true");
                this.rendererLogged = true;
            }

            var head = model.getBone("head");
            this.bakedModelObserved |= head.isPresent();
            if (this.bakedModelObserved && !this.bakedModelLogged) {
                System.out.println("[GECKOLIB_CLIENT_PROOF] baked_model_observed=true");
                this.bakedModelLogged = true;
            }

            ResourceLocation texture = getTextureLocation(animatable);
            this.textureResolved |= EXPECTED_TEXTURE.equals(texture)
                    && Minecraft.getInstance().getResourceManager().getResource(texture).isPresent();
            if (this.textureResolved && !this.textureLogged) {
                System.out.println("[GECKOLIB_CLIENT_PROOF] texture_resolved=true");
                this.textureLogged = true;
            }

            if (head.isPresent()) {
                float currentRotationY = head.get().getRotY();
                if (this.firstHeadRotationY == null) {
                    this.firstHeadRotationY = currentRotationY;
                } else if (Math.abs(currentRotationY - this.firstHeadRotationY) > MOTION_EPSILON) {
                    this.animationMotionObserved = true;
                }
            }
            if (this.animationMotionObserved && !this.animationLogged) {
                System.out.println("[GECKOLIB_CLIENT_PROOF] animation_motion_observed=true");
                this.animationLogged = true;
            }

            if (this.rendererInvoked
                    && this.bakedModelObserved
                    && this.textureResolved
                    && this.animationMotionObserved) {
                writeEvidence(texture, head.orElseThrow().getRotY());
            }
        }

        private void writeEvidence(ResourceLocation texture, float headRotationY) {
            Path evidence = Path.of(System.getProperty(
                            "i3golden.clientProofPath",
                            "client-runtime-proof.json"))
                    .toAbsolutePath();
            try {
                Files.createDirectories(evidence.getParent());
                String payload = String.format(
                        Locale.ROOT,
                        "{\n"
                                + "  \"renderer_invoked\": true,\n"
                                + "  \"baked_model_observed\": true,\n"
                                + "  \"texture_resolved\": true,\n"
                                + "  \"animation_motion_observed\": true,\n"
                                + "  \"texture\": \"%s\",\n"
                                + "  \"head_rotation_y\": %.8f\n"
                                + "}\n",
                        texture,
                        headRotationY);
                Files.writeString(evidence, payload, StandardCharsets.UTF_8);
                this.evidenceWritten = true;
            } catch (IOException exception) {
                throw new IllegalStateException("cannot write live-client runtime proof", exception);
            }
        }
    }
}
