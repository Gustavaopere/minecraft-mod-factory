# Registries and lifecycle

Prefer the project's established registration pattern. Verify exact NeoForge 1.21.1 APIs from resolved source/docs before adding new registries or lifecycle listeners.

Check:

- which event bus receives the registration/lifecycle event;
- registration timing and deferred holders;
- namespace/resource location correctness;
- bootstrap ordering between referenced objects;
- client-only registration isolation;
- tags/datagen dependencies;
- data-driven/custom registry reload behavior when applicable.

Do not resolve registry objects too early merely because a holder exists. Avoid static initialization that reaches client classes or runtime registries before their lifecycle allows it.

For custom registries or data-driven content, define stable IDs and serialization before exposing them to saves/network packets.
