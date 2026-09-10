# Repository Routing and Authority Contract

Status: canonical routing contract for the Minecraft Mod Factory.

## Authority matrix

| Concern | Source of truth |
| --- | --- |
| Shared engineering contracts, tooling, validators, catalogs and integration automation | `Gustavaopere/minecraft-mod-factory`, root `engineering/` |
| Art direction, native source models, textures, UV, rigs, animations, VFX and visual QA | `Gustavaopere/minecraft-mod-factory`, root `art/` |
| Shared reusable project skills/instructions | `Gustavaopere/minecraft-mod-factory`, root `skills/` |
| Runtime/gameplay code for a specific mod | That mod repository — its runtime authority |
| RPG Skill Tree runtime | `Gustavaopere/neoforge-rpg-skilltree` |
| Exact installed mod/provider presence and version | Latest physical modlist/JAR evidence |
| Exact third-party API behavior | Exact target source/JAR plus matching official documentation |

## Routing rules

1. The Factory is a control plane, not the default runtime repository for generated mods.
2. `engineering/` and `art/` are distinct logical authorities even though they share one Git repository.
3. Provider-native authoring formats such as `.bbmodel` remain source artifacts. Cross-pipeline conversion must be explicit and loss-audited.
4. A generated mod's Java code, registries, persistence, networking, gameplay, packaging and release remain in its runtime authority repository.
5. Shared runtime libraries require an explicit architecture and versioned API boundary; they are not implied by the Factory.
6. Presence in a modlist is not API proof. Provider adapters require exact-version evidence and absence-safe behavior.
7. Historical RPG infrastructure is a migration source only for reusable capabilities. RPG-specific runtime, gameplay and the physical modlist corpus stay in the RPG repository.
8. Paths described in plans are conceptual until reconciled with the live Factory tree.
9. Before writes, inspect current branches/PRs and never overwrite concurrent work.
