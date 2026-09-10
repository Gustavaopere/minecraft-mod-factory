# Exact-version API verification

Minecraft/NeoForge API details are version-sensitive. Before using an unfamiliar or materially version-sensitive contract:

1. identify the exact resolved coordinate/version from Gradle;
2. search current repository usage and analogous code;
3. inspect exact source/decompiled classes from the resolved dependency where possible;
4. consult official NeoForge documentation explicitly covering 1.21.1;
5. use official MDK/examples only when version-compatible;
6. verify signature, lifecycle/event bus, physical/logical side, thread/context, serialization, and registration timing as relevant.

Never copy a Forge 1.20.1, Fabric, NeoForge 1.21.4+, or current-latest snippet verbatim into 1.21.1 without verifying the exact target.

Known official 1.21.1 documentation examples include networking via `RegisterPayloadHandlersEvent`; treat this as a navigation clue, not permission to invent payload/registrar signatures from memory.

For third-party mods, inspect the exact installed/public artifact version. If exact source/API cannot be established, design a narrower integration around stable interfaces/tags/events or explicitly mark the integration blocked rather than guessing.
