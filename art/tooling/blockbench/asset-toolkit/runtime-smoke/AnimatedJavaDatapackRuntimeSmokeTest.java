package dev.example.i3golden;

import net.minecraft.core.BlockPos;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.phys.Vec3;
import net.neoforged.neoforge.gametest.GameTestHolder;
import net.neoforged.neoforge.gametest.PrefixGameTestTemplate;

@PrefixGameTestTemplate(false)
@GameTestHolder("i3_golden_mod")
public final class AnimatedJavaDatapackRuntimeSmokeTest {
    private AnimatedJavaDatapackRuntimeSmokeTest() {}

    @GameTest(template = "pr11.empty", timeoutTicks = 40)
    public static void animatedJavaDatapackFunctionSummonsDisplayEntity(GameTestHelper helper) {
        BlockPos relativeSpawn = new BlockPos(1, 1, 1);
        var server = helper.getLevel().getServer();
        var source = server.createCommandSourceStack()
                .withLevel(helper.getLevel())
                .withPosition(Vec3.atCenterOf(helper.absolutePos(relativeSpawn)));

        server.getCommands().performPrefixedCommand(source, "function factorypr11:smoke/summon");

        helper.assertEntityPresent(EntityType.ITEM_DISPLAY, relativeSpawn);
        helper.succeed();
    }
}
