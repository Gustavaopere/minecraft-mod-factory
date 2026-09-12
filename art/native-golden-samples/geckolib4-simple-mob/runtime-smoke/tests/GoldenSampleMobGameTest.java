package dev.example.i3golden;

import net.minecraft.core.BlockPos;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.neoforged.neoforge.gametest.GameTestHolder;
import net.neoforged.neoforge.gametest.PrefixGameTestTemplate;

@PrefixGameTestTemplate(false)
@GameTestHolder("i3_golden_mod")
public final class GoldenSampleMobGameTest {
    private GoldenSampleMobGameTest() {
    }

    @GameTest(template = "geckolib.empty", timeoutTicks = 40)
    public static void goldenSampleMobSpawnsWithGeckoLibCache(GameTestHelper helper) {
        BlockPos relativeSpawn = new BlockPos(1, 1, 1);
        BlockPos absoluteSpawn = helper.absolutePos(relativeSpawn);
        GoldenSampleMob entity = GoldenSampleMobRegistry.GOLDEN_SAMPLE_MOB.get().create(helper.getLevel());

        helper.assertTrue(entity != null, "Golden Sample GeckoLib entity was not created");
        helper.assertTrue(entity.getAnimatableInstanceCache() != null, "Golden Sample GeckoLib cache was not created");

        entity.moveTo(
                absoluteSpawn.getX() + 0.5,
                absoluteSpawn.getY(),
                absoluteSpawn.getZ() + 0.5,
                0.0F,
                0.0F);
        helper.getLevel().addFreshEntity(entity);

        helper.assertEntityPresent(GoldenSampleMobRegistry.GOLDEN_SAMPLE_MOB.get(), relativeSpawn);
        helper.succeed();
    }
}
