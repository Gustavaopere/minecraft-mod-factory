# Events, sides, and classloading

Distinguish:

- physical side: client process vs dedicated server;
- logical side: authoritative server logic vs client simulation/view;
- mod event bus vs game/NeoForge event bus;
- initialization thread vs runtime/game/network context.

Gameplay authority normally belongs on the logical server. The client may request actions and render projections; it must not be trusted to authoritatively set combat/progression/economy/world state.

Client-only types (`net.minecraft.client...`, renderers, screens, key mappings, local player UI state) must not enter classloading paths used by dedicated servers. Package names alone do not guarantee safe loading; inspect references and initialization paths.

Before subscribing to an event, verify the exact event exists in 1.21.1, which bus emits it, cancellation/result semantics, and side/context.
