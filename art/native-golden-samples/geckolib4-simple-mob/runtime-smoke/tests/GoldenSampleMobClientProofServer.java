package dev.example.i3golden;

import net.minecraft.server.level.ServerPlayer;
import net.neoforged.neoforge.event.entity.player.PlayerEvent;

public final class GoldenSampleMobClientProofServer {
    private GoldenSampleMobClientProofServer() {
    }

    public static void onPlayerLoggedIn(PlayerEvent.PlayerLoggedInEvent event) {
        if (!(event.getEntity() instanceof ServerPlayer player)) {
            return;
        }

        GoldenSampleMob mob = new GoldenSampleMob(
                GoldenSampleMobRegistry.GOLDEN_SAMPLE_MOB.get(),
                player.serverLevel());
        mob.setPos(player.getX(), player.getY(), player.getZ() + 3.0D);
        player.serverLevel().addFreshEntity(mob);
    }
}
