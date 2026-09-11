# Construction C7 Architecture QA Design

## Purpose

C7 adds deterministic, offline structural QA for Construction artifacts after Canonical Build IR generation and before visual QA or runtime acceptance. It proves only properties derivable from the current BuildSpec, Canonical Build IR, and optional C4 runtime registry evidence. It must not claim visual quality, full runtime correctness, full-modpack launch health, or semantic room correctness that current contracts cannot encode.

## Scope and authority

C7 consumes existing Construction authorities rather than creating a parallel representation:

- `construction/schemas/build-spec.schema.json` remains the intent contract.
- `construction/core/build_ir.py` and `construction/schemas/build-ir.schema.json` remain the canonical voxel/placement authority.
- `construction/core/modpack_registry.py` and `construction/schemas/modpack-registry.schema.json` remain the runtime-confirmed block/state authority when registry evidence is supplied.
- `construction/core/modded_palette.py` remains palette-selection authority.
- C6 Sponge serialization remains downstream export validation.

C7 is explicitly separate from C8 Visual QA and C12 Runtime Acceptance.

## Selected design

The selected design is a conservative offline validator over Canonical Build IR, with optional C4 registry evidence. It favors claims that can be proven from current contracts and reports unsupported semantics explicitly instead of guessing.

Rejected alternatives:

1. Expanding BuildSpec first with room coordinates, entrances, floors, and connector semantics. This could provide stronger architectural meaning but would broaden the canonical intent contract before a concrete consumer requires it.
2. Performing C7 primarily through NeoForge/GameTest placement. That would provide stronger runtime evidence but would collapse C7 into the later runtime-acceptance layer.

## New files

C7 introduces these focused units:

- `construction/core/structural_qa.py` — deterministic structural QA engine and report validator.
- `construction/schemas/structural-qa-report.schema.json` — stable machine-readable report contract.
- `construction/tests/test_c7_architecture_qa.py` — C7 contract, algorithm, determinism, and failure-mode tests.
- `.github/workflows/factory-construction-c7-architecture-qa.yml` — dedicated C7 CI plus prior-phase regressions.

Existing BuildSpec, Build IR, C4 registry, C5 palette, and C6 serializer contracts are reused and are not redefined.

## Public interface

`construction/core/structural_qa.py` exposes:

```python
class StructuralQAError(ValueError):
    pass


def run_structural_qa(
    build_spec: dict,
    build_ir: dict,
    registry: dict | None = None,
) -> dict:
    ...


def validate_structural_qa_report(report: dict) -> None:
    ...
```

`run_structural_qa` fails closed when authoritative inputs are malformed or inconsistent. Structural deficiencies in otherwise valid inputs become report findings instead of exceptions.

## Input validation and cross-authority checks

C7 does not add a second general-purpose BuildSpec validator. It performs the checks needed to prove that the analyzed inputs belong together:

- `build_spec` must be an object with `schema_version=1` and valid C7-consumed fields under the existing BuildSpec contract.
- `build_ir` must pass C2 `validate_build_ir` with zero errors.
- `build_ir.metadata.build_spec_sha256` must equal C2 `build_spec_fingerprint(build_spec)`.
- C7 uses C2 bounds, palette, blocks, and coordinate-system data exactly as validated by C2.
- if `registry` is supplied, C7 validates the C4 fields it consumes, verifies `content_sha256` against canonical C4 JSON bytes with the fingerprint field omitted from the hashed payload, and rejects inconsistent evidence.

C0 remains authority for the BuildSpec schema file itself. C4 remains authority for creating the registry. C7 only proves that supplied evidence is internally consistent enough for C7 checks.

## Report contract

The report is deterministic and contains:

- `schema_version`: fixed at `1`.
- `build_spec_sha256`: C2 fingerprint of the exact BuildSpec input.
- `build_ir_sha256`: C2 canonical Build IR fingerprint.
- `registry_fingerprint`: C4 `content_sha256` when registry evidence is supplied, otherwise `null`.
- `overall_status`: one of `PASS`, `FAIL`, `DEFERRED`.
- `checks`: results in a fixed check order.
- `metrics`: deterministic structural counts.

Each check result contains:

- `id`: stable check identifier.
- `required`: boolean stating whether this invocation requires the check for overall completion.
- `status`: one of `PASS`, `FAIL`, `DEFERRED`, `NOT_APPLICABLE`.
- `severity`: `error`, `warning`, or `info`.
- `summary`: deterministic short explanation.
- `findings`: deterministically ordered machine-readable findings.

Overall status is derived as follows:

1. `FAIL` if any required check is `FAIL`.
2. otherwise `DEFERRED` if any required check is `DEFERRED`.
3. otherwise `PASS`.

A required check can therefore never disappear behind a nominal PASS when current evidence is insufficient.

## Canonical occupancy model

C7 derives an in-memory occupancy lookup from valid C2 Build IR; it does not persist another voxel format.

- C2 sparse Build IR forbids explicit `minecraft:air`, `minecraft:cave_air`, and `minecraft:void_air` placements.
- coordinates absent from `build_ir.blocks` are therefore the only air cells in the C7 geometric model.
- any coordinate present in `build_ir.blocks` is occupied for purely geometric checks.
- coordinates are evaluated only inside `build_ir.bounds.size`.
- iteration and finding order use `(y, z, x)` unless a check defines another stable key.

This model does not infer collision boxes, render shapes, door-open behavior, ladders, elevators, trapdoors, scaffolding, or provider-specific traversal semantics.

## C7 checks

### 1. `bounds`

Purpose: prove that the artifact satisfies canonical C2 spatial invariants.

Authority: C2 `validate_build_ir`.

Behavior:

- valid C2 Build IR yields `PASS`;
- invalid/tampered Build IR raises `StructuralQAError` before report emission.

This check is always required.

### 2. `runtime_state_validity`

Purpose: prove that used block states exist in supplied C4 runtime-confirmed evidence.

When `registry` is supplied:

- every distinct Build IR state must resolve to the exact block id;
- the registry block must have `available=true`;
- authority must be `runtime_confirmed`;
- the exact C2 property map must exist in the block `states` array;
- missing ids, static-only blocks, unavailable blocks, or missing property combinations are `FAIL` findings.

When no registry is supplied:

- if `build_spec.target.loader == "neoforge"` or `build_spec.palette.allow_modded == true`, this check is required and `DEFERRED`;
- otherwise it is not required and `NOT_APPLICABLE`.

C7 never infers runtime validity from namespace names, static JAR discovery, or C5 alternatives.

### 3. `head_clearance`

Purpose: determine whether conservative two-block-high walkable positions exist and quantify geometrically blocked supported cells.

Definitions:

- a supported foot cell is an air cell whose coordinate directly below is occupied;
- a clear foot cell is a supported foot cell whose coordinate immediately above is also air and in bounds;
- a blocked supported cell is a supported foot cell without that second air cell.

Metrics include supported, clear, and blocked counts.

Behavior:

- when `qa.require_walkability=true`, this check is required;
- if no clear foot cell exists, status is `FAIL`;
- if at least one clear foot cell exists, status is `PASS` and blocked supported cells remain informational findings rather than automatic failures because C7 cannot know whether those cells were intended as circulation space;
- when walkability is not required, status is `NOT_APPLICABLE` for gating while metrics remain available.

This avoids false failures on roofs, decorative ledges, crawl spaces, or other non-circulation geometry.

### 4. `walkable_surface_graph`

Purpose: build the deterministic graph used by circulation metrics.

A graph node is a clear foot cell. Horizontal edges connect cardinally adjacent nodes at the same `y`. Conservative vertical-step edges connect cardinally adjacent nodes whose `y` differs by exactly one and whose endpoints are both independently clear.

Metrics include:

- walkable node count;
- horizontal edge count;
- vertical-step edge count;
- connected-component count;
- component sizes sorted descending with deterministic tie-breaking;
- walkable `y` levels.

Behavior:

- when `qa.require_walkability=true`, this check is required and is `FAIL` only when node count is zero;
- otherwise it is `PASS` when at least one node exists;
- when walkability is not required, it is `NOT_APPLICABLE` for gating.

The graph is an analysis product only and is not a new persisted authority.

### 5. `circulation_components`

Purpose: expose geometric fragmentation without pretending that every walkable surface belongs to the same intended circulation network.

Behavior:

- if the graph has zero nodes and walkability is required, status is `FAIL`;
- if the graph has exactly one connected component, status is `PASS` when required;
- if the graph has more than one component and walkability is required, status is `DEFERRED`, not `FAIL`, because roofs, exterior platforms, landscaping, and intentionally isolated surfaces cannot be distinguished from intended interior circulation using current contracts;
- when walkability is not required, status is `NOT_APPLICABLE`.

All components and isolated nodes remain visible in deterministic metrics/findings.

C7 does not claim that names in `geometry.required_spaces` are connected because BuildSpec does not map those names to coordinates.

### 6. `vertical_step_connectivity`

Purpose: expose conservative one-block vertical transitions between clear walkable surfaces.

Behavior:

- if the graph occupies one `y` level, status is `NOT_APPLICABLE`;
- if multiple walkable `y` levels exist and at least one vertical-step edge exists, status is `PASS`;
- if multiple walkable `y` levels exist and no vertical-step edge exists, status is `DEFERRED`, not `FAIL`, because current C7 inputs cannot distinguish intended floors from roofs/exterior surfaces and cannot recognize ladder/elevator/provider traversal semantics.

This check is required only when `qa.require_walkability=true` and the graph spans multiple `y` levels.

## Explicitly deferred structural semantics

### `enclosure`

`qa.require_complete_interior=true` expresses intent, but BuildSpec does not encode entrances, windows, intentional openings, room volumes, or interior/exterior labels. A generic sealed-volume rule would misclassify legitimate architecture.

- if `require_complete_interior=true`, `enclosure` is required and `DEFERRED`, causing overall status to remain `DEFERRED` unless another required check fails;
- otherwise `enclosure` is not required and remains `DEFERRED` as an informational roadmap limitation.

### `floor_continuity_semantic`

The walkable graph proves geometric surfaces, not whether a designer-intended floor region is complete. BuildSpec does not map floor regions or required spaces to coordinates. This check is not required by current BuildSpec fields and remains `DEFERRED`.

### `unsupported_placement`

C4 safety classes do not provide support-face, gravity, attachment, or neighbor-rule semantics. Provider-aware unsupported-placement validation therefore remains `DEFERRED`; C7 must not infer physics from block ids.

## BuildSpec policy handling

C7 reads existing BuildSpec QA fields without broadening their meaning:

- `qa.require_walkability=true` requires the geometric walkability checks described above.
- absent or false `require_walkability` leaves their metrics available but non-gating.
- `qa.require_complete_interior=true` makes the unsupported enclosure proof visible as a required `DEFERRED` check rather than silently passing it.
- `qa.require_determinism=true` requires repeated canonical executions to produce byte-identical canonical JSON reports in tests.

`geometry.required_spaces` is preserved as intent evidence but is never marked satisfied by C7 because no coordinate mapping exists in the current schema.

## Determinism

C7 output must be reproducible.

- canonical JSON uses UTF-8, sorted object keys, compact separators, and a final newline when serialized to disk;
- fingerprints use SHA-256 over canonical JSON bytes according to the owning contract;
- set/dictionary-derived outputs are sorted before report construction;
- graph traversal starts at the lexicographically smallest remaining `(y, z, x)` node and visits neighbors in a fixed order;
- findings use stable check-specific sort keys;
- reports contain no wall-clock timestamps, random identifiers, machine paths, or environment-dependent ordering.

## Error handling

C7 raises `StructuralQAError` for authoritative-input defects, including:

- non-object or unsupported BuildSpec version;
- malformed C7-consumed BuildSpec QA/target/palette fields;
- Build IR failing C2 validation;
- Build IR fingerprinting or BuildSpec fingerprint linkage mismatch;
- malformed supplied registry fields consumed by C7;
- C4 registry fingerprint mismatch.

Expected structural deficiencies in otherwise valid inputs become report findings and statuses.

## Testing strategy

The C7 TDD suite must cover at least:

1. RED contract before production module exists;
2. valid single-floor walkable structure;
3. zero-clear-cell failure when walkability is required;
4. blocked supported cells reported without false-failing a structure that still has valid walkable space;
5. single-component circulation PASS;
6. multi-component circulation DEFERRED when walkability is required;
7. one-block vertical-step PASS;
8. multi-level geometry without a conservative step becomes DEFERRED rather than a fabricated FAIL;
9. exact runtime-confirmed state acceptance from C4 registry;
10. missing/static-only/unavailable/mismatched runtime state rejection;
11. modded/NeoForge invocation without registry evidence becomes required DEFERRED;
12. vanilla/no-loader invocation without registry is NOT_APPLICABLE for runtime-state validation;
13. `require_complete_interior=true` makes enclosure required DEFERRED and prevents overall PASS;
14. semantic floor continuity and unsupported placement remain explicit DEFERRED checks;
15. deterministic report equality across repeated executions;
16. report-schema validation;
17. tampered Build IR fails closed;
18. mismatched BuildSpec fingerprint fails closed;
19. malformed or fingerprint-tampered registry fails closed;
20. BuildSpec flags alter gating/status without changing deterministic geometry metrics.

The existing vanilla golden fixture is reused where suitable. Minimal topology-specific BuildSpecs/IRs may be assembled in tests when a graph shape is clearer than adding another persisted golden artifact.

## CI gate

`.github/workflows/factory-construction-c7-architecture-qa.yml` runs on C7-related paths and on `main` and follows the established pinned-action Construction pattern.

The job must execute, in order:

1. checkout with recursive preserved upstreams;
2. Python 3.11 using the existing pinned `actions/setup-python` commit;
3. Java 21 using the existing pinned `actions/setup-java` commit because the inherited C4 runtime probe is part of the gate;
4. install `construction/upstream/harness/schematica-test-lock.txt` with `--require-hashes --no-deps`;
5. C7 dedicated tests;
6. C6 `test_c6_sponge_v3.py` regression;
7. C5 `test_c5_modded_palette.py` regression;
8. shared Engineering I2 regressions used by C4;
9. C4 `test_c4_modpack_registry.py` and `test_c4_runtime_registry_probe.py` regressions;
10. materialize the C4 runtime probe with `construction/scripts/prepare_neoforge_registry_probe.py`;
11. build the materialized runtime probe with Java 21 using the same established Gradle command/pattern as the C4 workflow;
12. C3 `test_c3_vanilla_golden.py` regression;
13. C2 `test_c2_build_ir.py` regression;
14. C0 `test_c0_foundation.py` regression;
15. `python3 construction/scripts/validate_c0.py`;
16. `git diff --check` over the C7 scope.

C7 is not complete from local reasoning alone; the dedicated workflow and inherited regressions must be green on the exact PR head.

## Non-goals

C7 does not:

- score silhouette, proportion, material hierarchy, repetition, facade readability, or visual interior density;
- render images or canonical visual views;
- prove full NeoForge/full-modpack runtime health;
- place the final structure in a live world;
- infer collision boxes or traversal behavior from block names;
- claim named required spaces exist or are connected without spatial authority;
- modify C4/C5 provider authority rules;
- replace C6 Sponge validation;
- convert native authoring/source formats.

## Acceptance criteria

C7 is implementation-complete only when:

- the report schema is versioned and validated;
- `run_structural_qa` is deterministic for identical canonical inputs;
- valid C2 Build IR is the only voxel authority consumed;
- BuildSpec-to-Build-IR fingerprint linkage is enforced;
- exact C4 runtime-state evidence is used when supplied;
- absence of required registry evidence is visible as `DEFERRED`, never silently passed;
- walkability, head clearance, circulation components, and conservative vertical-step behavior have positive and negative tests with the evidence semantics above;
- `require_complete_interior=true` cannot produce overall PASS while enclosure remains unprovable;
- enclosure, semantic floor continuity, and provider-aware support are never silently promoted to PASS;
- C8 visual and C12 runtime claims remain out of scope;
- the exact C7 PR head passes the dedicated C7 workflow and inherited Construction regressions;
- repository documentation and `construction/STATUS.md` are updated only after implementation gates provide evidence.
