# Mod Engineering / Integration Control Plane

Status: canonical engineering entrypoint for `Gustavaopere/minecraft-mod-factory`.

## Authorities

- Shared engineering control plane: `engineering/` in this repository.
- Visual and asset authority (Repo Textura domain): `art/` in this repository.
- Shared reusable project skills: `skills/`.
- Runtime authority for each mod: that mod's own repository.
- RPG runtime authority and historical migration source: `Gustavaopere/neoforge-rpg-skilltree`.
- Provider/mod presence and exact installed version: the latest physical modlist/JAR evidence, currently referenced externally from the RPG/modpack repository.

The Factory coordinates contracts, schemas, templates, generators, validators, catalogs, compatibility evidence, CI/test harnesses, asset handoff and release preparation. It must not become a mega-mod or silently absorb the runtime of generated mods.

## Canonical plans

1. `../plans/PLANO-MESTRE-MINECRAFT-MOD-FACTORY-MOD-ENGINEERING-NEOFORGE-1.21.1-V1.1.md`
   - SHA-256: `29fc7f4b949b2b8dba327eb3f022f4cd84b11a352430ca821bdaec13072b8744`
2. `../plans/PLANO-MESTRE-UNIFICADO-MINECRAFT-MOD-FACTORY-REPO-TEXTURA-BLOCKBENCH-ASSET-MCP-V5.1.md`
   - SHA-256: `723bb083d5b646812cd44a03a1ef50e8505b366923b64aba5931ee4b7b63befb`

`../STATUS.md` is the operational boundary. `../migration/MIGRATION-MATRIX-F1-M3.md` is the frozen migration classification for the current transfer from historical infrastructure.

## Execution order

Before relevant implementation: read both plans and `STATUS.md`; confirm the latest physical modlist; inspect live GitHub main/open PRs/concurrent branches; inspect the actual tree; identify already-proven historical work; create an isolated branch from the exact verified base; implement the smallest missing capability; run the applicable validator/test/build/runtime/QA gates; resynchronize with current main; open a PR; and update status when the frontier changes.

Historical capabilities are migrated, reconciled and revalidated. They are not reimplemented merely because authority moved to this repository.
