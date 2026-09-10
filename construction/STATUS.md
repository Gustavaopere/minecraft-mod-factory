# STATUS — Construction

UPDATED_AT=2026-09-10
PHASE=C0_FOUNDATION_IMPLEMENTED_PENDING_GREEN
REPOSITORY=Gustavaopere/minecraft-mod-factory
BRANCH=feat/construction-c0-foundation
BASE_SHA=47ccda543dbc20ca52db9ed0fdd43ed9cb2b88b2
RED_HEAD=c77c34ab82c2739b1be9051bbd2343043e94df4c
RED_RUN=34521743874
HEAD_SHA=RESOLVE_FROM_GIT
OPEN_PR=NONE
TARGET_MINECRAFT=1.21.1
TARGET_LOADER=NeoForge
CANONICAL_OUTPUT=SPONGE_SCHEMATIC_V3
LATEST_MODLIST_SNAPSHOT=2026-09-09_595_TOP_LEVEL
MANUAL_ACTION_REQUIRED=NO
BLOCKERS=NONE
NEXT_ACTION=RUN_C0_GREEN_GATES_ON_IMPLEMENTATION_HEAD

## Audited upstream candidates

- Schematica: `tester2024/schematica@0c88770005e7bbd7246997c81e810ba935c8e4cf` — MIT — planned immutable snapshot in C1.
- MineBench: `Ammaar-Alam/minebench@c96abbd4c4098aa9c264490c80a1c6544a64ba85` — MIT — planned immutable snapshot/reference in C1.
- Minecraft Builder MCP: `joshdevous/minecraft-builder-claude-mcp-server@5c3bc03dea82395f85926a2c3d3f814f312f7452` — MIT — planned immutable snapshot/reference in C1.
- mcschematic: `Sloimayyy/mcschematic@912bd88877aa44eeb7426f6e42e5811e9f5be98d` — Apache-2.0 — planned immutable snapshot/reference in C1.
- Promptcraft: `cgoulart35/Promptcraft@a960575be921c072550c5a9e7206d3dfa192a6d1` — all rights reserved at audit — `REFERENCE_ONLY`, never vendored without changed permission.

## External providers

ObjToSchematic, Structmatic, Schematic Helper and BlockGPT are currently treated as `EXTERNAL_PROVIDER`. Their local integration state is `UNVERIFIED_API`; no claim of programmatic API support is made by C0.

## C0 acceptance

- [x] authority documentation exists
- [x] architecture document exists
- [x] upstream registry materialized
- [x] initial schemas materialized
- [x] expected RED obtained from missing validator
- [x] C0 validator implemented
- [ ] contract tests pass on implementation head
- [ ] C0 validator passes on implementation head
- [ ] whitespace gate passes on implementation head
- [ ] PR CI passes on exact head
