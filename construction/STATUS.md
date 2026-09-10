# STATUS — Construction

UPDATED_AT=2026-09-10
PHASE=C1_SCHEMATICA_PRESERVATION_RED
REPOSITORY=Gustavaopere/minecraft-mod-factory
BRANCH=feat/construction-c1-schematica-upstream
BASE_SHA=8e65289223d4b8a5728fa735a6d72b30a5e4b52e
C0_PR=19
C0_MERGE_SHA=a850627e1a9e012221e4fbabeeb50c22880af51f
C0_PR_HEAD=7626ca96bc9d5a6422308cd6f79c4c46d59efb22
C0_PR_GATE=PASS
C0_GOVERNANCE=PASS
C0_SONARCLOUD=PASS
HEAD_SHA=PENDING_C1_RED_COMMIT
OPEN_PR=NONE
TARGET_MINECRAFT=1.21.1
TARGET_LOADER=NeoForge
CANONICAL_OUTPUT=SPONGE_SCHEMATIC_V3
LATEST_MODLIST_SNAPSHOT=2026-09-09_595_TOP_LEVEL
MANUAL_ACTION_REQUIRED=NO
BLOCKERS=NONE
NEXT_ACTION=OBTAIN_C1_RED_THEN_MATERIALIZE_SCHEMATICA_GITLINK

## C1A target

Preserve Schematica exactly as audited upstream source using a Git submodule/gitlink. The Factory superproject must not contain an editable copied Schematica payload.

UPSTREAM_REPOSITORY=tester2024/schematica
UPSTREAM_URL=https://github.com/tester2024/schematica.git
UPSTREAM_PIN=0c88770005e7bbd7246997c81e810ba935c8e4cf
UPSTREAM_PATH=construction/upstream/snapshots/schematica
UPSTREAM_POLICY=IMMUTABLE_SNAPSHOT
UPSTREAM_LICENSE_DECLARATION=MIT

## C1A acceptance

- [x] upstream commit independently resolves on GitHub
- [x] upstream package metadata declares MIT
- [x] preservation contract test authored
- [x] dedicated C1 workflow authored
- [ ] expected RED obtained before gitlink exists
- [ ] `.gitmodules` declares the exact upstream URL and path
- [ ] gitlink mode is `160000`
- [ ] gitlink SHA equals audited upstream pin
- [ ] upstream native tests pass from submodule checkout
- [ ] Factory C0 regression remains green
- [ ] C1 PR CI passes on exact head
