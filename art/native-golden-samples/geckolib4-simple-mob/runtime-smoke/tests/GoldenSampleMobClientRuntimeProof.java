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
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.resources.ResourceLocation;
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
    private static final float MOTION_EPSILON = 0.0001F;

    private GoldenSampleMobClientRuntimeProof() {
    }

    public static GeoEntityRenderer<GoldenSampleMob> createRenderer(EntityRendererProvider.Context context) {
        return new ProofRenderer(context);
    }

    private static final class ProofRenderer extends GeoEntityRenderer<GoldenSampleMob> {
        private Float firstHeadRotationY;
        private boolean rendererInvoked;
        private boolean bakedModelObserved;
        private boolean textureResolved;
        private boolean animationMotionObserved;
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
            var head = model.getBone("head");
            this.bakedModelObserved |= head.isPresent();

            ResourceLocation texture = getTextureLocation(animatable);
            this.textureResolved |= EXPECTED_TEXTURE.equals(texture)
                    && Minecraft.getInstance().getResourceManager().getResource(texture).isPresent();

            if (head.isPresent()) {
                float currentRotationY = head.get().getRotY();
                if (this.firstHeadRotationY == null) {
                    this.firstHeadRotationY = currentRotationY;
                } else if (Math.abs(currentRotationY - this.firstHeadRotationY) > MOTION_EPSILON) {
                    this.animationMotionObserved = true;
                }
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
