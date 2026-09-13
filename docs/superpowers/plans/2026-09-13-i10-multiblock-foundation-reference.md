# I10 Multiblock Foundation Reference Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an independent I10 Golden proving controller, parts, orientation, formation, invalidation, unload/reload, IO capability, visual formed state, I6 asset handoff, GameTest, persistence, and multiplayer on Minecraft 1.21.1 / Java 21 with the cycle-resolved stable NeoForge 21.1.x target (`21.1.250` for this implementation cycle).

**Architecture:** Generate a fresh I3 scaffold for `i10_multiblock` (`dev.example.i10multiblock`) and apply an I10-owned deterministic overlay. The controller is the sole gameplay/storage authority. A fixed 3×3×3 hollow pattern uses one canonical rotation transform. A rear IO port delegates controller-owned item capability only while controller/revision/state are valid. Runtime state is `UNFORMED`, `PENDING_REVALIDATION`, or `FORMED`; unavailable chunks suspend operation instead of dissolving the structure. I6 schema v2 remains the only asset-handoff schema.

**Tech Stack:** Python 3 unittest/tooling; Java 21; Minecraft 1.21.1; latest stable NeoForge 21.1.x compatible with Minecraft 1.21.1, resolved and pinned exactly per implementation/validation cycle (`21.1.250` for this cycle); NeoGradle userdev 7.1.26 inherited from I3; NeoForge BlockEntity/item capabilities; GameTest; existing I5 harness; existing I6 validator; GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-13-i10-multiblock-foundation-reference-design.md`

## Global Constraints

- Fresh I3 scaffold only; no I9 runtime/materialized-project dependency.
- I8 remains generic and receives no multiblock feature.
- Pattern: local X `-1..1`, Y `0..2`, Z `0..2`; controller `(0,1,0)`; IO `(0,1,2)`; interior air `(0,1,1)`; every other boundary cell casing.
- Four horizontal facings through one transform; no four copied patterns.
- No per-tick full validation. Part mutation schedules bounded/coalesced candidate revalidation.
- Validation result is exactly `VALID`, `INVALID`, `UNAVAILABLE`.
- Public IO exists only at the rear port and only for a loaded `FORMED` controller with exact formation revision.
- Persist controller historical formed flag, non-negative revision, one item slot, and port link/revision. Persisted formed history never grants runtime operation without revalidation.
- Required visual inputs: `formed: bool`, `facing: string`.
- Reuse `engineering/schemas/asset-handoff.schema.json` v2 and `engineering/tooling/asset-handoff/validate_asset_handoff.py`.
- Repo Textura owns source visuals under `art/`; Engineering owns runtime binding/delivery.
- No silent provider/source conversion.
- Dedicated-server startup and GameTest are not multiplayer proof.
- `STATUS.md` changes only after merge and current-main evidence.

## File Map

Composition/tooling:
- `engineering/tests/fixtures/i10-multiblock-mod-spec.json`
- `engineering/tests/fixtures/i10-multiblock-scaffold-config.json`
- `engineering/tests/test_i10_multiblock_foundation.py`
- `engineering/tests/test_i10_multiblock_foundation_composition.py`
- `engineering/tests/test_i10_chunk_acceptance.py`
- `engineering/tooling/multiblock-foundation/materialize_i10.py`
- `engineering/tooling/multiblock-foundation/run_i10_chunk_acceptance.py`
- `engineering/tests/golden/i10-multiblock-foundation/manifest.json`
- `engineering/tests/golden/i10-multiblock-foundation/asset-handoff.json`
- `.github/workflows/factory-engineering-i10-multiblock-foundation.yml`

Runtime overlay under `engineering/tests/golden/i10-multiblock-foundation/overlay/`:
- `src/main/java/dev/example/i10multiblock/multiblock/I10MultiblockContent.java`
- `.../MultiblockPattern.java`
- `.../MultiblockValidationResult.java`
- `.../MultiblockRuntimeState.java`
- `.../MultiblockControllerBlock.java`
- `.../MultiblockControllerBlockEntity.java`
- `.../MultiblockPortBlock.java`
- `.../MultiblockPortBlockEntity.java`
- `.../MultiblockInvalidation.java`
- `src/main/java/dev/example/i10multiblock/gametest/I10MultiblockGameTests.java`
- `src/main/java/dev/example/i10multiblock/acceptance/I10AcceptanceCommands.java`
- `src/main/resources/data/i10_multiblock/structure/multiblock_test.nbt`

Repo Textura source:
- `art/golden-samples/i10-multiblock-visual/README.md`
- `art/golden-samples/i10-multiblock-visual/models/controller_unformed.json`
- `art/golden-samples/i10-multiblock-visual/models/controller_formed.json`
- `art/golden-samples/i10-multiblock-visual/models/casing.json`
- `art/golden-samples/i10-multiblock-visual/models/io_port_unformed.json`
- `art/golden-samples/i10-multiblock-visual/models/io_port_formed.json`

## Task 1 — Composition RED

**Interfaces:** fixed identity `i10_multiblock`; future `materialize_i10(output_dir: Path | str) -> Path`.

- [ ] Create fixed I3 fixture JSONs using the same schema as I9 but I10 identity/package and only required scaffold features.
- [ ] Create failing composition contract:

```python
REPO = Path(__file__).resolve().parents[2]
MATERIALIZER = REPO / "engineering/tooling/multiblock-foundation/materialize_i10.py"
GOLDEN = REPO / "engineering/tests/golden/i10-multiblock-foundation"

class I10CompositionContract(unittest.TestCase):
    def test_composition_authority_exists(self):
        self.assertTrue(MATERIALIZER.is_file())
        self.assertTrue((GOLDEN / "manifest.json").is_file())
        self.assertTrue((GOLDEN / "overlay").is_dir())
```

- [ ] Add assertions forbidding `materialize_i9`, `i9-machine-foundation`, and `dev.example.i9machine` in the I10 composition/runtime output.
- [ ] Add first runtime-surface RED requiring controller, port, pattern, validation/result enums, controller BE and port BE source paths.
- [ ] Add initial I10 workflow that runs only these RED contracts on the I10 branch.
- [ ] Run the two I10 unittest modules and capture expected failure caused by missing production composition authority.
- [ ] Commit only tests/fixtures/workflow. This failing run is the first I10 RED evidence.

## Task 2 — Materializer GREEN

**Interfaces:** consume canonical I3 `generate_project(...)`; produce safe deterministic I10 output.

- [ ] Extend tests first for workspace containment, existing-output rejection, closed manifest keys, POSIX bounded paths, traversal/absolute/backslash/drive rejection, duplicate source/destination rejection, symlink rejection, exact one-anchor main-class patch, no scaffold overwrite, staged publish/cleanup, deterministic bytes.
- [ ] Implement `MaterializationError` and `materialize_i10(...)` using I9's proven security structure but I10 constants/messages.
- [ ] Initial overlay authority contains only `README.md -> I10-MULTIBLOCK-FOUNDATION.md`; later tasks expand it under tests.
- [ ] Exact generated constructor result:

```java
public I10MultiblockMod(IEventBus modBus, ModContainer container) {
    dev.example.i10multiblock.multiblock.I10MultiblockContent.register(modBus);
    modBus.addListener(dev.example.i10multiblock.multiblock.I10MultiblockContent::registerCapabilities);
}
```

- [ ] Run composition/security/determinism tests to GREEN and commit.

## Task 3 — Pattern, Rotation and Registries

**Interfaces:** `MultiblockPattern.worldPos(controllerPos, facing, localX, localY, localZ)`; `validate(ServerLevel, controllerPos, facing)` returns `VALID|INVALID|UNAVAILABLE`.

- [ ] Add RED requiring one transform and exact local roles/coordinates, four horizontal directions, both enums and all registration surfaces.
- [ ] Implement `MultiblockPattern` as the only geometry authority. Local +Z is inward (`facing.getOpposite()`); local +X is controller-right horizontal perpendicular. Reject vertical facings.
- [ ] Validation checks chunk availability before block identity; one unavailable required coordinate returns `UNAVAILABLE`; loaded mismatch returns `INVALID`.
- [ ] Register controller + item, casing + item, port + item, controller BE and port BE through canonical I3 event bus. Casing has no BE.
- [ ] Expand composition manifest/materializer only for newly created I10 files.
- [ ] Materialize fresh I10, run Python contracts, then target-exact `test build`; fix only compiler-proven API mismatches. Commit GREEN.

## Task 4 — Controller/Port Authority, Capability and Persistence

**Interfaces:** controller owns stable `ItemStackHandler(1)`; port persists linked controller/revision and delegates only to live matching `FORMED` controller.

- [ ] Write capability/persistence RED first: stable handler; no public controller IO; port-only item capability; revision guards; `loadAdditional`/`saveAdditional` required.
- [ ] Controller fields:

```java
private final ItemStackHandler items = new ItemStackHandler(1) { /* setChanged on mutation */ };
private boolean lastKnownFormed;
private long formationRevision;
private MultiblockRuntimeState runtimeState = MultiblockRuntimeState.UNFORMED;
```

- [ ] Port binding is writable only by controller after successful complete validation.
- [ ] Capability lookup verifies same server level, controller chunk already loaded, controller BE exists, state is `FORMED`, revision matches. Never force-load.
- [ ] Negative/malformed revision loads fail closed; item contents survive regardless of formed state.
- [ ] Run tests + fresh materialization + target-exact build and commit.

## Task 5 — Formation, Invalidation and Visual State

**Interfaces:** controller `tryForm()` server-only; fixed-footprint candidate invalidation; controller/port `FORMED` blockstate; controller horizontal `FACING`.

- [ ] Add lifecycle RED before implementation: explicit server formation; no client authority; bounded candidate discovery; no tick-wide scan; `VALID/INVALID/UNAVAILABLE` transitions; revision increments only on successful explicit formation/reformation.
- [ ] `tryForm()`: on VALID increment revision once, bind rear port, set controller/port formed presentation, set `lastKnownFormed=true`, state `FORMED`, mark changed/update clients atomically. INVALID => unformed. UNAVAILABLE => pending. No partial binding.
- [ ] Implement `MultiblockInvalidation` by inverse fixed-footprint candidate derivation across four horizontal facings, deduplicated and coalesced. Affected formed controller becomes pending immediately, closing IO before scheduled recheck.
- [ ] Server owns `FORMED`/`FACING`; clients never infer formed by scanning.
- [ ] Run contracts/build and commit.

## Task 6 — Repo Textura Source + I6 Handoff

**Interfaces:** use I6 `validate_manifest_data(...)`; provider profile `java_block_item`; visual inputs `formed` and `facing`.

- [ ] Add RED that loads I6 schema v2 and I10 handoff, validates with repository `source_root` and fresh generated `runtime_root`, requiring zero errors.
- [ ] Create simple source-native Java block-model JSONs under `art/golden-samples/i10-multiblock-visual/` using only vanilla texture references. These are Repo Textura authority; overlay wiring is not relabeled as art.
- [ ] Create schema-v2 handoff with `source_authority="Repo Textura"`, source repository Factory, runtime authority I10 Golden, `java_block_item`, explicit runtime bindings `MultiblockControllerBlock.FORMED`, `MultiblockPortBlock.FORMED`, `MultiblockControllerBlock.FACING`, exact source/delivery hashes, and explicit no-conversion record.
- [ ] Keep unperformed visual/Blockbench/runtime QA `PENDING`; structural success never upgrades it automatically.
- [ ] Materializer copies only declared handoff artifacts to `src/main/resources/assets/i10_multiblock/...`, then canonical I6 validator verifies source and delivery hashes/namespace.
- [ ] Run I6 validation + I10 tests + target-exact build and commit.

## Task 7 — GameTests

**Interfaces:** native template `multiblock_test`; pinned SHA-256; required target-exact lifecycle suite.

- [ ] Add RED requiring methods `northFormation`, `rotationEastSouth`, `missingCasing`, `blockedInterior`, `wrongPortPosition`, `invalidation`, `repairAndReformation`, `ioDelegation`, `persistence`, `staleBinding`, `visualState`.
- [ ] Check in native `.nbt`, compute/pin SHA-256 in closed composition authority and reject drift.
- [ ] Implement tests using `MultiblockPattern.worldPos(...)` for rotated setup, not copied coordinate maps.
- [ ] Persistence test uses real target serialization/load APIs. IO test mutates controller storage only through rear port capability.
- [ ] Run fresh materialization, `test build`, and `runGameTestServer`; capture exact discovered/pass count. GameTest does not close chunk or multiplayer gates.
- [ ] Commit only after target-exact GameTests pass.

## Task 8 — Real Chunk Unload/Reload Acceptance

**Interfaces:** Golden command `i10probe setup|status|break_required_part`; Python server-console driver; real target server evidence.

- [ ] Add pure harness RED for allowlisted argv/commands, workspace containment, timeout cleanup, no shell execution, server-ready marker and strict machine-readable marker parser. Unit mocks do not count as runtime acceptance.
- [ ] Add Golden acceptance command using fixed controller `(159,80,160)` facing west so the 3-block depth crosses from chunk X=9 into X=10. `setup` builds via canonical pattern, forms, inserts one diamond sentinel, prints revision/state/item/capability. `status` prints validation/runtime state/revision/sentinel/capability. `break_required_part` removes one fixed required casing through normal world mutation.
- [ ] Implement `run_i10_chunk_acceptance.py` using `subprocess.Popen` without `shell=True`, stdin console commands and concurrent stdout capture. It must: start server; forceload controller+adjacent chunks; setup/verify formed; remove adjacent forceload and poll until `PENDING_REVALIDATION` + `UNAVAILABLE` + capability absent; re-add and require `FORMED` with same revision/sentinel; stop/restart same world and prove persisted recovery; break casing; stop/restart and prove stale persisted formed history resolves to `UNFORMED/INVALID`; save logs under generated `build/i10-acceptance/`; always terminate on timeout/failure.
- [ ] If physical server shows another ticket prevents unload, diagnose real ticket ownership and revise the runtime mechanism from evidence; do not substitute serialization-only proof.
- [ ] Add this target-exact acceptance to permanent I10 workflow and commit after PASS.

## Task 9 — Multiplayer Gate

**Interfaces:** real server + two real clients, or an existing Factory harness that truly provides equivalent client observations.

- [ ] Audit current Factory for an existing two-client Minecraft automation harness. Fake players, server-only tests and GameTests are insufficient.
- [ ] If no real two-client harness exists, create `engineering/tests/i10-multiplayer-acceptance.md` with exact protocol: start tested I10 server; connect Client A+B; both see unformed; A forms through normal interaction; both see formed; server-authoritatively break casing; both see unformed and no port IO; disconnect/reconnect B; B receives current unformed state without historical replay; capture server+A+B logs/screenshots with commit SHA.
- [ ] Keep state `PENDING_MANUAL_MULTIPLAYER_ACCEPTANCE` until real artifacts exist. Do not mark I10 PASS or treat dedicated-server startup as multiplayer evidence.
- [ ] Commit the protocol/guard contract. Manual execution, if required, is later guided one user action at a time.

## Task 10 — Permanent CI and Closeout

**Interfaces:** permanent I10 workflow + post-merge `STATUS.md` update only after all acceptance evidence.

- [ ] Workflow-contract RED must require relevant I3/I4/I5/I6/I8/I9 regressions, I10 contracts, chunk-harness unit tests, fresh materialization, I6 source/runtime validation, `test build`, `runGameTestServer`, real chunk acceptance, I5 dedicated-server harness, whitespace. Multiplayer is not encoded green without real evidence.
- [ ] Complete pinned permanent workflow for main/I10 branch/PR relevant paths.
- [ ] Pre-merge gate: I10 contracts PASS; deterministic materialization PASS; I6 handoff PASS; build PASS; GameTests PASS; chunk acceptance PASS; I5 manifest unit/GameTest/dedicated-server PASS; multiplayer PASS; whitespace PASS; Sonar Quality Gate PASS; no pending/failing/skipped-as-pass required checks.
- [ ] Fix review findings with regression evidence or prove non-applicability.
- [ ] Merge with expected head SHA only after policy allows the acceptance boundary.
- [ ] Verify current-main post-merge workflows, main Sonar, fresh materialization, chunk and multiplayer evidence.
- [ ] Create dedicated status-closeout branch and record actual PR/head/merge/run/evidence values plus `I10_MULTIBLOCK_FOUNDATION_STATE=PASS`; then advance frontier to I11. Never commit unresolved placeholders.

## Acceptance Mapping

| Gate | Evidence |
|---|---|
| Controller | Tasks 3–5 registered controller BE owns structure state |
| Parts | Tasks 3/5/7 canonical controller+casing+port role map |
| Orientation | Tasks 3/7 one transform + rotated GameTests |
| Formation | Tasks 5/7 explicit server atomic formation |
| Invalidation | Tasks 5/7 bounded scheduling + dissolution tests |
| Unload/reload | Task 8 real adjacent-chunk unload/reload + restart |
| IO capability | Tasks 4/7/8 guarded port delegation |
| Visual formed state | Tasks 5/6/7 + Task 9 client convergence |
| Asset manifest | Task 6 canonical I6 schema v2/hash validation |
| GameTest | Task 7 target-exact suite |
| Persistence | Tasks 4/7/8 serialization + restart survival |
| Multiplayer | Task 9 real two-client/reconnect evidence |

## Self-Review Gate

Before Task 1 production work: verify all 12 gates map above; no I9 runtime dependency; I8 unchanged; `UNAVAILABLE != INVALID`; no tick-wide scan; one transform authority; controller remains storage owner; persisted formed never grants operation; Repo Textura owns source art; I6 v2 reused; chunk gate is real runtime; multiplayer is not server-only inference; no TODO/TBD/silent conversion is present.

## Execution Choice

Use inline execution with `superpowers:executing-plans` in this ChatGPT context because no callable subagent executor is available. Preserve TDD and review checkpoints task-by-task. The user delegated architectural/execution decisions on 2026-09-13; interrupt only for a genuine blocker, material scope change, or required manual action.
