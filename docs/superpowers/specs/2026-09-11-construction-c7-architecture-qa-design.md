# Construction C7 Architecture QA Design

## Purpose

C7 adds deterministic, offline structural QA for Construction artifacts after Canonical Build IR generation and before visual QA or runtime acceptance. It must prove only properties that are derivable from the current BuildSpec, Canonical Build IR, and optional C4 runtime registry evidence. It must not claim visual quality, full runtime correctness, modpack launch health, or semantic room correctness that the current contracts cannot encode.

## Scope and authority

C7 consumes the existing Construction authorities rather than creating a parallel representation:

- `construction/schemas/build-spec.schema.json` remains the intent contract.
- `construction/core/build_ir.py` and `construction/schemas/build-ir.schema.json` remain the canonical voxel/placement authority.
- `construction/core/modpack_registry.py` and `construction/schemas/modpack-registry.schema.json` remain the runtime-confirmed block/state authority when a registry is supplied.
- `construction/core/modded_palette.py` remains palette selection authority and is not duplicated by C7.
- C6 Sponge serialization remains downstream export validation and is not part of structural QA.

C7 is explicitly separate from C8 Visual QA and C12 Runtime Acceptance.

## Design choice

The selected design is a conservative offline validator over Canonical Build IR, with optional C4 registry evidence. It favors evidence that can be proven deterministically from current contracts and reports unsupported semantic checks explicitly instead of guessing.

Rejected alternatives:

1. Expanding BuildSpec first with room coordinates, entrances, floors, and connector semantics. This could provide stronger architectural meaning but would broaden the canonical intent contract before a concrete consumer requires it.
2. Performing C7 primarily through NeoForge/GameTest placement. That would provide stronger runtime evidence but would collapse C7 into the later runtime-acceptance layer and violate the current phase separation.

## New files

C7 will introduce these focused units:

- `construction/core/structural_qa.py` — deterministic structural QA engine and report validator.
- `construction/schemas/structural-qa-report.schema.json` — stable machine-readable report contract.
- `construction/tests/test_c7_architecture_qa.py` — C7 contract, algorithm, determinism, and failure-mode tests.
- `.github/workflows/factory-construction-c7-architecture-qa.yml` — dedicated C7 CI plus prior-phase regressions.

Existing BuildSpec, Build IR, C4 registry, C5 palette, and C6 serializer contracts are reused and are not redefined.

## Public interface

`construction/core/structural_qa.py` will expose:

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

`run_structural_qa` validates its inputs against the existing Construction contracts before analysis. Invalid or tampered Build IR, invalid BuildSpec input, or malformed supplied registry evidence must fail closed with `StructuralQAError`; they must not be converted into a passing QA report.

## Report contract

The report is deterministic and contains:

- `schema_version`: fixed at `1`.
- `build_spec_sha256`: canonical fingerprint of the exact BuildSpec input.
- `build_ir_sha256`: canonical fingerprint of the exact Build IR input.
- `registry_fingerprint`: the C4 `content_sha256` when registry evidence is supplied, otherwise `null`.
- `overall_status`: `PASS` or `FAIL`.
- `checks`: ordered results for the C7 checks below.
- `metrics`: deterministic structural counts used to explain the result.

Each check result contains:

- `id`: stable check identifier.
- `status`: one of `PASS`, `FAIL`, `DEFERRED`, `NOT_APPLICABLE`.
- `severity`: `error`, `warning`, or `info`.
- `summary`: deterministic short explanation.
- `findings`: deterministically ordered machine-readable findings.

A `FAIL` check makes `overall_status=FAIL`. `DEFERRED` and `NOT_APPLICABLE` are not silently promoted to PASS and do not by themselves fail the report.

## Canonical occupancy model

C7 derives a dense occupancy lookup from Canonical Build IR without creating a second persisted voxel format.

- Any coordinate absent from sparse Build IR placements is treated as air.
- A placed `minecraft:air` state is also treated as air.
- Any non-air state is treated as occupied for purely geometric checks.
- Coordinates are evaluated only inside the Build IR dimensions.
- Iteration and finding order are canonicalized as `(y, z, x)` unless a check explicitly requires another stable key.

This model is geometric only. It does not infer collision boxes, render shapes, door-open state behavior, or provider-specific movement semantics.

## C7 checks

### 1. `bounds`

Purpose: prove that the analyzed artifact remains inside the canonical dimensions and that Build IR structural invariants are intact.

Authority: reuse C2 `validate_build_ir`; C7 does not implement a competing bounds parser.

Behavior:

- valid C2 Build IR produces `PASS` for this check;
- invalid/tampered Build IR causes `run_structural_qa` to raise `StructuralQAError` before report emission.

### 2. `runtime_state_validity`

Purpose: prove that used block states are present in the supplied C4 runtime-confirmed registry snapshot.

Behavior when `registry` is supplied:

- validate the registry contract first;
- for every distinct non-air Build IR state, locate the exact block id;
- require `available=true`;
- require `authority=runtime_confirmed`;
- require an exact property-map match in the block's `states` array;
- emit deterministic findings for missing block ids, unavailable/static-only blocks, or missing property combinations;
- any such finding is `FAIL`.

Behavior when no registry is supplied:

- status is `DEFERRED`;
- the report states that C7 has no runtime-state authority for this invocation.

C7 does not infer state validity from namespace names, static JAR discovery, or C5 alternatives.

### 3. `head_clearance`

Purpose: detect walkable candidate cells that do not provide the minimum two-block-high empty column required by the conservative offline model.

Definitions:

- a candidate foot cell is an air cell whose cell directly below is occupied;
- a candidate has head clearance only when both the foot cell and the cell immediately above it are air and inside bounds;
- candidate cells at the top layer cannot satisfy two-block clearance.

Behavior:

- metrics include candidate count, clear candidate count, and blocked candidate count;
- if BuildSpec `qa.require_walkability=true`, any blocked candidate that participates in the selected walkable surface set contributes a failing finding;
- if walkability is not required, the check still reports metrics but is `NOT_APPLICABLE` for gating.

The check does not inspect voxel collision shapes. Two blocks of geometric air are the only C7 guarantee.

### 4. `walkable_surface_graph`

Purpose: construct the deterministic graph used by circulation checks.

A walkable node is a candidate foot cell with two-block head clearance. Horizontal edges connect cardinally adjacent nodes at the same `y`. Vertical-step edges connect cardinally adjacent nodes whose foot `y` differs by exactly one block and where both endpoints independently satisfy head clearance.

The graph is an analysis product only and is not persisted as a new Construction authority.

Metrics include:

- walkable node count;
- horizontal edge count;
- vertical-step edge count;
- connected-component count;
- component sizes in descending order with deterministic tie-breaking.

If BuildSpec `qa.require_walkability=true` and the graph has zero nodes, this check is `FAIL`; otherwise it is `PASS` when applicable. If walkability is not required, it is `NOT_APPLICABLE` for gating while metrics may still be emitted.

### 5. `circulation_components`

Purpose: detect fragmented conservative walkable space without inventing room semantics.

Behavior:

- uses the walkable graph connected components;
- when `qa.require_walkability=true`, more than one non-trivial component is a failure;
- isolated walkable nodes are reported as findings and count as components;
- when walkability is not required, the check is `NOT_APPLICABLE`.

C7 does not claim that every named item in `geometry.required_spaces` is connected, because BuildSpec currently supplies names but no spatial mapping from those names to voxels.

### 6. `vertical_step_connectivity`

Purpose: expose whether the conservative graph contains one-block vertical transitions between walkable surfaces.

Behavior:

- reports the count and endpoints of vertical-step edges;
- if the walkable graph spans multiple `y` levels and `qa.require_walkability=true`, absence of any vertical-step edge is `FAIL`;
- if all walkable nodes occupy one `y` level, status is `NOT_APPLICABLE`;
- otherwise it is `PASS`.

This check does not treat ladders, elevators, trapdoors, scaffolding, modded lifts, or provider-specific traversal as valid vertical access because current C7 inputs do not contain authoritative traversal semantics for those blocks.

## Explicitly deferred structural semantics

The following architectural concepts remain visible in the report as `DEFERRED` checks rather than being guessed:

### `enclosure`

Current BuildSpec can request `qa.require_complete_interior`, but it does not encode entrances, windows, intentional openings, room volumes, or interior/exterior labels. A generic flood-fill "sealed volume" rule would misclassify legitimate architecture. C7 therefore reports enclosure as `DEFERRED` until the intent contract can identify spaces/openings precisely enough for deterministic validation.

### `floor_continuity_semantic`

The walkable graph proves geometric traversability, not whether a designer-intended floor is complete. BuildSpec does not map named spaces or floor regions to coordinates. Semantic floor continuity remains `DEFERRED`.

### `unsupported_placement`

Minecraft support behavior varies by block and mod provider. The C4 registry currently identifies broad safety categories but does not provide authoritative support-face/gravity/attachment rules. C7 therefore does not invent them. Provider-aware unsupported-placement validation remains `DEFERRED` until such metadata has an explicit authority.

## BuildSpec policy handling

C7 reads existing BuildSpec QA fields conservatively:

- `qa.require_walkability=true` enables gating for geometric walkability, circulation, and vertical-step connectivity.
- absent or false `qa.require_walkability` leaves those checks measurable but non-gating where defined above.
- `qa.require_complete_interior=true` does not fabricate an enclosure algorithm; the enclosure check remains `DEFERRED` and the report makes the missing semantic authority explicit.
- `qa.require_determinism=true` is satisfied only if two executions over byte-equivalent canonicalized inputs produce byte-equivalent canonical JSON reports.

`geometry.required_spaces` is preserved as intent evidence but is not marked satisfied by C7 because no coordinate mapping exists in the current schema.

## Determinism

C7 output must be reproducible.

- Canonical JSON serialization uses UTF-8, sorted object keys, compact separators, and a final newline where serialized to disk in tests/tools.
- Fingerprints are SHA-256 over canonical JSON bytes.
- All set/dictionary-derived outputs are sorted before report construction.
- Graph traversal begins from the lexicographically smallest remaining `(y, z, x)` node and visits neighbors in a fixed order.
- Findings are sorted by check-specific stable keys.
- Reports contain no wall-clock timestamps, random identifiers, machine paths, or environment-dependent ordering.

## Error handling

C7 fails closed on malformed authoritative inputs.

Examples that raise `StructuralQAError` rather than returning PASS/FAIL reports:

- BuildSpec does not conform to the existing schema/contract;
- Build IR fails C2 validation;
- supplied registry is malformed or its own content fingerprint is inconsistent;
- dimensions or placements cannot be interpreted under the canonical C2 contract.

Expected structural deficiencies in otherwise valid inputs are represented as report findings and `FAIL`, not exceptions.

## Testing strategy

The C7 test suite will use TDD and must cover at least:

1. module absence/contract RED before implementation;
2. valid single-floor walkable structure;
3. zero-walkable-node failure when required;
4. blocked two-block head clearance;
5. connected versus disconnected circulation components;
6. one-block vertical-step connectivity;
7. multi-level structure without vertical-step connectivity;
8. exact runtime-confirmed state acceptance from C4 registry;
9. missing/static-only/mismatched runtime state rejection;
10. registry-absent `DEFERRED` behavior;
11. enclosure/floor-semantic/unsupported-placement remain explicitly `DEFERRED`;
12. deterministic report equality across repeated executions;
13. report-schema validation;
14. tampered Build IR fails closed;
15. malformed registry fails closed;
16. BuildSpec flags control gating without changing deterministic metrics.

The vanilla golden fixture should be reused where it fits. Additional minimal fixtures may be built inline in tests when a specific graph topology is clearer than adding another persisted golden construction.

## CI gate

`.github/workflows/factory-construction-c7-architecture-qa.yml` will run on C7-related paths and on `main`.

The gate must execute:

1. C7 dedicated tests;
2. C6 Sponge v3 regression;
3. C5 modded palette regression;
4. C4 registry regression, including the existing NeoForge runtime registry probe path where the established workflow pattern requires it;
5. C3 vanilla golden regression;
6. C2 Build IR regression;
7. C0 Construction foundation regression;
8. Construction validator if applicable under the current repository workflow pattern;
9. whitespace validation for the C7 scope.

No C7 phase is considered complete from local reasoning alone; the dedicated workflow and inherited regressions must be green.

## Non-goals

C7 does not:

- score silhouette, proportion, material hierarchy, repetition, facade readability, or interior visual density;
- render images or canonical views;
- prove full NeoForge/modpack runtime health;
- place the structure in a live world;
- infer collision boxes or traversal behavior from block names;
- claim named required spaces exist or are connected without spatial authority;
- modify C4/C5 provider authority rules;
- replace C6 Sponge validation;
- convert source/authoring formats.

Those responsibilities remain in their existing or later roadmap phases.

## Acceptance criteria

C7 is implementation-complete only when all of the following are true:

- the report schema is versioned and validated;
- `run_structural_qa` is deterministic for identical canonical inputs;
- valid C2 Build IR is the only voxel authority consumed;
- exact C4 runtime state evidence is used when supplied and absence is visible as `DEFERRED`;
- walkability, head-clearance, circulation, and conservative vertical-step behavior are covered by positive and negative tests;
- enclosure, semantic floor continuity, and provider-aware support are explicitly `DEFERRED`, never silently passed;
- C8 visual and C12 runtime claims remain out of scope;
- the C7 workflow and all required Construction regressions pass on the exact PR head;
- repository documentation and `construction/STATUS.md` are updated only after the implementation gates provide evidence.
