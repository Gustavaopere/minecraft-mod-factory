# Construction C8 Visual QA Design

## Purpose

C8 adds deterministic offline preview generation and evidence-gated visual QA for Construction artifacts after C7 Architecture QA and before C12 Runtime Acceptance. It provides canonical diagnostic views, reproducible visual metrics, and a machine-readable visual QA report without pretending that offline voxel projections are equivalent to Minecraft runtime rendering.

C8 must distinguish three evidence classes:

1. **structural evidence** — owned by C7 and never reinterpreted as visual quality;
2. **canonical offline preview evidence** — owned by C8 and derived deterministically from Canonical Build IR;
3. **actual Minecraft runtime capture** — reserved for C12 or a later explicit runtime visual handoff.

The selected design is **Conservative Offline Preview + Evidence-Gated Visual QA**.

## Scope and authority

C8 consumes existing Construction authorities rather than creating a second geometry, palette, or runtime representation:

- `construction/schemas/build-spec.schema.json` remains the intent contract.
- `construction/core/build_ir.py` and `construction/schemas/build-ir.schema.json` remain the canonical voxel authority.
- `construction/core/structural_qa.py` remains structural QA authority.
- `construction/core/modded_palette.py` remains palette-role selection authority when a C5 resolution is supplied.
- `construction/core/modpack_registry.py` remains block/state runtime-evidence authority.
- `construction/core/sponge_v3.py` remains canonical schematic serialization authority.
- `art/standards/VISUAL-QA.md` remains the cross-domain visual-evidence standard. C8 follows its fail-closed evidence policy but does not move Construction authority into `art/`.
- `art/golden-samples/` remains reference evidence for how visual claims stay `PENDING` when captures do not exist. Construction does not copy those fixtures into C8.

C8 is explicitly separate from C7 Architecture QA and C12 Runtime Acceptance.

## Selected design

C8 renders Canonical Build IR into deterministic diagnostic SVG views using a Factory-owned renderer. The renderer is intentionally not a Minecraft block renderer: it does not resolve block models, textures, CTM, connected textures, copycat materials, dynamic renderers, shader behavior, lighting, emissive layers, translucent sorting, or provider-specific rendering.

The preview uses stable pseudo-colors derived from canonical block-state identity so that block-state regions are visually distinguishable across repeated runs. These colors are diagnostic labels only. They must never be described as Minecraft material colors or texture fidelity.

C8 computes objective metrics from Build IR and preview projections, but subjective quality checks such as silhouette readability or facade readability become `PASS` or `FAIL` only when explicit `review_evidence` is supplied and cryptographically bound to the exact BuildSpec, Build IR, and canonical view hashes. Missing subjective evidence remains `DEFERRED`.

Rejected alternatives:

1. **Full offline Minecraft block renderer.** Resolving exact blockstate/model/texture rendering for the physical modpack would immediately require connected-texture semantics, dynamic renderer/provider behavior, copycat/material-bearing blocks, and other later-provider responsibilities. That scope is too large for C8 and would create a parallel renderer authority.
2. **In-game automated capture as C8.** This would produce stronger fidelity, but it requires real client boot, resource loading, lighting, placement, graphics automation, and runtime health. Those concerns belong to C12 Runtime Acceptance.

## New files

C8 introduces focused units only when implementation begins:

- `construction/core/visual_qa.py` — visual QA orchestration, input validation, deterministic metrics, review-evidence validation, and report construction.
- `construction/qa/preview_renderer.py` — Factory-owned deterministic diagnostic SVG renderer.
- `construction/schemas/visual-qa-report.schema.json` — machine-readable C8 report contract, including canonical view fingerprints.
- `construction/tests/test_c8_visual_qa.py` — renderer, metric, evidence, determinism, and failure-mode tests.
- `.github/workflows/factory-construction-c8-visual-qa.yml` — dedicated C8 CI with prior-phase regressions.

`construction/qa/` does not exist before C8 and is created only when this implementation starts.

No second BuildSpec, Build IR, palette, registry, or structural-report schema is introduced.

## Public interfaces

`construction/qa/preview_renderer.py` exposes:

```python
class PreviewRenderError(ValueError):
    pass


def render_canonical_views(build_ir: dict) -> dict[str, bytes]:
    ...
```

The returned mapping contains canonical SVG bytes keyed by stable view id.

`construction/core/visual_qa.py` exposes:

```python
class VisualQAError(ValueError):
    pass


def run_visual_qa(
    build_spec: dict,
    build_ir: dict,
    views: dict[str, bytes],
    structural_report: dict | None = None,
    palette_resolution: dict | None = None,
    review_evidence: dict | None = None,
) -> dict:
    ...


def validate_visual_qa_report(report: dict) -> None:
    ...
```

`render_canonical_views` is pure with respect to repository state: identical valid Build IR produces byte-identical SVG bytes.

`run_visual_qa` fails closed when authoritative inputs are malformed, inconsistent, or not cryptographically linked. Visual deficiencies in valid evidence become report findings instead of exceptions.

## Input validation and cross-authority checks

C8 validates only the fields it consumes and reuses owning authorities wherever available.

### BuildSpec and Build IR

- `build_spec` must be an object with `schema_version=1` and valid C8-consumed fields.
- `build_ir` must pass C2 `validate_build_ir` with zero errors.
- `build_ir.metadata.build_spec_sha256` must equal C2 `build_spec_fingerprint(build_spec)`.
- C8 geometry always comes from C2 bounds, palette, blocks, and coordinate system.
- C8 does not reinterpret absent sparse cells: absent coordinates are air exactly as defined by C2.

### Structural report

`structural_report` is optional context, not a prerequisite for rendering.

When supplied:

- it must satisfy the C7 report contract consumed by C8;
- `build_spec_sha256` must match the exact BuildSpec;
- `build_ir_sha256` must match the exact C2 Build IR fingerprint;
- C8 may expose C7 status/fingerprints as provenance only;
- C8 never promotes a C7 `PASS` into any visual `PASS`.

A malformed or mismatched supplied structural report raises `VisualQAError`.

### C5 palette resolution

`palette_resolution` is optional semantic context for labels and palette-role metrics.

When supplied:

- `schema_version` must be `1`;
- its `build_spec_sha256` must equal C2 `build_spec_fingerprint(build_spec)`; C2 and C5 currently use the same canonical JSON SHA-256 rule;
- role names and selected canonical block states consumed by C8 must be structurally valid;
- C8 may annotate palette usage with matching C5 roles;
- C8 does not treat a C5 selection as evidence that textures, materials, connected models, or provider rendering look correct.

Malformed or mismatched supplied C5 evidence raises `VisualQAError`.

### Canonical views

The `views` argument must contain exactly the required view ids produced by the C8 renderer. Each value must be non-empty UTF-8 SVG bytes matching the deterministic SVG contract. `run_visual_qa` recomputes SHA-256 for every view and records those hashes in the report.

A view set with missing ids, unknown ids, invalid media bytes, or mismatched embedded Build IR fingerprint raises `VisualQAError`.

## Canonical view set

C8 version 1 renders these exact view ids in fixed order:

1. `front`
2. `back`
3. `left`
4. `right`
5. `top`
6. `isometric`
7. `layers`

The orthographic views provide repeatable exterior projections. `isometric` provides a deterministic three-quarter diagnostic view. `layers` is a deterministic contact sheet of horizontal occupied layers, enabling review of internal distribution without inventing semantic room boundaries.

C8 does not claim that `layers` is a human first-person interior view.

## Renderer contract

### Projection and camera

The renderer is deterministic and contains no floating camera state.

Orthographic views use integer-grid projection of C2 block coordinates. `front`, `back`, `left`, and `right` use fixed cardinal axes; `top` looks down the negative `y` axis. Occlusion selects the nearest occupied block along the fixed view ray.

`isometric` uses a fixed axonometric projection implemented from integer/rational geometry so repeated runs do not depend on platform-specific 3D libraries or GPU state. Only exposed top/side faces are emitted.

`layers` renders every occupied `y` level in ascending `y` order into a deterministic grid contact sheet. Grid placement depends only on level count and C2 bounds.

### Canvas and padding

- canvas dimensions are derived from C2 bounds and a fixed renderer version constant;
- a fixed integer padding is applied around projected occupied extents;
- empty unused space is deterministic;
- no machine DPI, font discovery, browser layout, system theme, clock, random seed, or filesystem path affects output.

### Labels and fonts

Canonical SVG bytes must not depend on host-installed fonts. Any textual metadata included in SVG uses generic SVG text only if byte output remains independent of font metrics. Geometry layout must not depend on rendered text size.

Tests compare bytes, not rasterized font appearance.

### Diagnostic pseudo-color mapping

Each canonical C2 palette state receives a stable diagnostic base color derived from SHA-256 of its canonical block-state string. Conversion from digest bytes to RGB uses a versioned algorithm with bounded channel ranges to avoid extremely dark or extremely bright colors.

- identical canonical state => identical diagnostic color;
- different state identity should normally produce different colors, but collisions are not treated as impossible or as semantic equality;
- isometric face shading uses fixed integer channel multipliers for top/side distinction;
- colors do not claim texture, biome tint, material, emissive, lighting, transparency, or runtime appearance fidelity.

The report records `renderer_version` so future renderer changes are explicit rather than silently changing visual evidence.

### SVG safety and determinism

SVG output:

- is UTF-8;
- contains no scripts, external resources, network URLs, embedded filesystem paths, timestamps, random ids, or data fetched from the environment;
- uses a fixed element ordering;
- serializes integer geometry deterministically;
- contains the Build IR SHA-256 as inert metadata for cross-checking;
- ends with a final newline.

## Objective metrics

C8 metrics are descriptive evidence, not aesthetic truth.

### Occupancy metrics

Derived from valid C2 Build IR:

- occupied block count;
- canonical palette-state count;
- occupied minimum and maximum coordinate on each axis;
- occupied extent dimensions;
- occupied bounding-box volume;
- occupied density inside that occupied bounding box;
- occupied density inside full C2 bounds.

Empty Build IR is valid only if C2 allows it; C8 still renders deterministic empty views and exposes zero occupancy metrics. Subjective checks remain `DEFERRED` unless explicit review evidence addresses the empty result.

### Projection metrics

For each cardinal/top view:

- projected occupied-cell count;
- projected bounding width and height;
- projected occupancy ratio inside projected bounds;
- number of projected connected components using cardinal adjacency;
- dominant projected component size;
- aspect ratio represented as reduced integer numerator/denominator rather than a platform-dependent float.

These metrics support silhouette review but do not themselves prove that a silhouette is visually good.

### Palette-distribution metrics

For every C2 palette state:

- canonical state string;
- occupied block count;
- fraction as exact integer numerator/denominator;
- per-view visible-cell counts;
- optional matching C5 role labels when supplied.

C8 never names a palette entry a real-world material unless that semantic role is explicit in supplied C5 evidence.

### Repetition metrics

C8 records deterministic repetition proxies on projected visible grids:

- repeated row-signature counts;
- repeated column-signature counts;
- longest identical adjacent row run;
- longest identical adjacent column run;
- per-view repeated-signature ratio as exact integer numerator/denominator.

These metrics expose repetition; they do not define whether repetition is desirable.

### Facade-depth metrics

For `front`, `back`, `left`, and `right`, C8 records the visible ray depth index for each projected occupied cell and derives:

- distinct visible depth values;
- depth range;
- count of depth transitions between cardinally adjacent projected cells;
- flat-cell ratio and transition ratio as exact fractions.

This is a facade-depth/readability proxy only. It does not model Minecraft lighting, texture detail, bevels, connected models, or dynamic renderer depth.

### Layer-density metrics

For every occupied `y` level:

- occupied cells;
- horizontal footprint area;
- density as exact numerator/denominator;
- palette-state counts.

Aggregate metrics include minimum, maximum, median-by-order pair, and level count without floating-point dependence.

These metrics support interior-density review but do not identify rooms or intentional interior volumes.

## Visual QA report contract

The report is deterministic and schema-versioned.

Top-level fields:

- `schema_version`: fixed at `1`.
- `build_spec_sha256`: exact C2 BuildSpec fingerprint.
- `build_ir_sha256`: exact C2 Build IR fingerprint.
- `structural_report_fingerprint`: supplied C7 provenance fingerprint or `null`.
- `palette_resolution_fingerprint`: deterministic fingerprint of supplied C5 resolution or `null`.
- `renderer_version`: fixed C8 renderer contract version.
- `views`: fixed-order canonical view descriptors.
- `metrics`: deterministic objective metric object.
- `checks`: fixed-order visual check results.
- `overall_status`: `PASS`, `FAIL`, or `DEFERRED`.

Each view descriptor contains:

- `id`;
- `media_type`: fixed `image/svg+xml`;
- `sha256`;
- `byte_length`;
- deterministic canvas `width` and `height`;
- `evidence_class`: fixed `canonical_offline_preview`.

Actual SVG bytes are artifacts, not embedded in the JSON report.

Each check result contains:

- `id`;
- `required`;
- `status`: `PASS`, `FAIL`, `DEFERRED`, or `NOT_APPLICABLE`;
- `severity`: `error`, `warning`, or `info`;
- `summary`;
- `evidence_views`: fixed/sorted list of canonical view ids;
- `findings`: deterministic machine-readable findings.

Overall status:

1. `FAIL` if any required check is `FAIL`;
2. otherwise `DEFERRED` if any required check is `DEFERRED`;
3. otherwise `PASS`.

A required visual property therefore cannot silently pass because preview files exist.

## C8 checks

### 1. `canonical_preview_integrity`

Purpose: prove that the required C8 diagnostic views correspond exactly to the analyzed Build IR and satisfy the renderer contract.

- always required;
- valid complete canonical view set => `PASS`;
- malformed, missing, unexpected, or fingerprint-mismatched views raise `VisualQAError` before report emission.

### 2. `silhouette_readability`

Purpose: review whether the structure has a readable silhouette across canonical exterior views.

Objective evidence includes projection metrics and `front`, `back`, `left`, `right`, `top`, and `isometric` views.

- always required for C8 visual completion;
- without matching explicit review evidence => `DEFERRED`;
- matching review `PASS` => `PASS`;
- matching review `FAIL` => `FAIL`.

C8 does not convert projection density or component counts directly into an aesthetic PASS/FAIL threshold.

### 3. `proportion`

Purpose: review visual massing and relative proportions against the BuildSpec architectural brief and geometry constraints.

Evidence includes occupied extents, aspect-ratio metrics, all exterior views, and the BuildSpec `geometry.architectural_brief` when present.

- always required;
- without explicit review evidence => `DEFERRED`;
- explicit bound review decides `PASS` or `FAIL`.

C8 does not invent an expected architectural style when `architectural_brief` is absent.

### 4. `material_hierarchy`

Purpose: review whether palette/state regions form a coherent hierarchy rather than visually undifferentiated distribution.

Evidence includes diagnostic pseudo-color views, palette-distribution metrics, block-state legends, and optional C5 role labels.

- always required;
- without explicit review evidence => `DEFERRED`;
- explicit bound review decides `PASS` or `FAIL`.

A C8 `PASS` proves hierarchy/distribution in the diagnostic preview only. It does **not** prove actual texture quality, Minecraft material appearance, CTM behavior, emissive behavior, translucency, biome tint, or shader appearance.

### 5. `repetition`

Purpose: review whether repeated visual modules/patterns are intentional and appropriately varied for the requested build.

Evidence includes deterministic row/column repetition proxies and exterior/isometric views.

- always required;
- without explicit review evidence => `DEFERRED`;
- explicit bound review decides `PASS` or `FAIL`.

No universal repetition threshold is encoded because repetition can be intentional architecture.

### 6. `facade_readability`

Purpose: review whether facades have readable mass/depth organization in canonical offline projection.

Evidence includes cardinal views and facade-depth metrics.

- always required;
- without explicit review evidence => `DEFERRED`;
- explicit bound review decides `PASS` or `FAIL`.

C8 does not claim runtime lighting or texture readability.

### 7. `interior_density`

Purpose: review whether internal layer occupancy appears appropriately sparse/dense for the requested build without claiming semantic room correctness.

Evidence includes `layers`, layer-density metrics, `isometric`, and BuildSpec `geometry.required_spaces` names as non-spatial intent only.

- always required;
- without explicit review evidence => `DEFERRED`;
- explicit bound review decides `PASS` or `FAIL`.

C8 never marks a named required space as satisfied because BuildSpec v1 does not map spaces to coordinates.

### 8. `runtime_visual_fidelity`

Purpose: keep the gap between offline diagnostic preview and actual Minecraft rendering visible.

- not required for C8 completion;
- always `DEFERRED` in C8;
- severity `info`;
- points forward to C12 Runtime Acceptance or another explicit runtime visual handoff.

C8 must never change this check to `PASS` based on SVG output or reviewer opinion about SVG output.

## Review evidence contract

`review_evidence` is optional input. It is the only authority that may resolve C8 subjective checks from `DEFERRED` to `PASS` or `FAIL`.

Version 1 shape:

```json
{
  "schema_version": 1,
  "build_spec_sha256": "<sha256>",
  "build_ir_sha256": "<sha256>",
  "renderer_version": "c8-svg-v1",
  "views": [
    {"id": "front", "sha256": "<sha256>"}
  ],
  "reviewer": {
    "kind": "human|agent",
    "id": "<non-empty stable label>"
  },
  "decisions": [
    {
      "check_id": "silhouette_readability",
      "status": "PASS|FAIL",
      "evidence_views": ["front", "isometric"],
      "summary": "<non-empty review statement>"
    }
  ]
}
```

Validation rules:

- BuildSpec, Build IR, renderer version, and every referenced view hash must match current C8 inputs exactly.
- Unknown view ids or unknown check ids fail closed.
- Duplicate decisions for the same check fail closed.
- `status` may only be `PASS` or `FAIL`; omission means C8 keeps that subjective check `DEFERRED`.
- every decision must reference at least one canonical view relevant to that check;
- `runtime_visual_fidelity` cannot be resolved by C8 review evidence;
- review strings are preserved as evidence but do not change objective metrics.

Review evidence can be produced by a human or an agent capable of actually inspecting the canonical rendered artifacts. Merely reading metric JSON without inspecting the named view artifacts is insufficient process evidence for a subjective visual decision.

## Determinism

C8 output must be reproducible for identical authoritative inputs.

### SVG artifacts

- fixed view ids and order;
- fixed renderer version;
- fixed integer/rational projection geometry;
- canonical C2 palette order;
- stable pseudo-color algorithm;
- stable visible-cell and polygon ordering;
- no timestamps, random ids, machine paths, external resources, GPU state, OS fonts, locale, or environment-derived configuration;
- final newline;
- SHA-256 recorded in report.

### JSON report

- canonical JSON uses UTF-8, sorted object keys, compact separators, and final newline when serialized to disk;
- all dictionary/set-derived lists are sorted by explicit stable keys;
- fractions are represented as exact integer numerator/denominator objects, not floats;
- findings have fixed ordering;
- review decisions are sorted by C8 fixed check order;
- report contains no wall-clock timestamps or transient CI metadata.

`qa.require_determinism=true` requires tests to render and analyze identical inputs at least twice and prove byte-identical SVG artifacts plus byte-identical canonical report JSON.

## Error handling

C8 raises `PreviewRenderError` or `VisualQAError` for malformed or inconsistent authority/evidence inputs, including:

- non-object or unsupported BuildSpec;
- invalid/tampered C2 Build IR;
- BuildSpec/Build IR fingerprint mismatch;
- malformed or mismatched supplied C7 report;
- malformed or mismatched supplied C5 palette resolution;
- missing/extra canonical views;
- invalid SVG bytes;
- embedded Build IR fingerprint mismatch;
- malformed review evidence;
- stale review evidence bound to different view hashes;
- duplicate/unknown subjective decisions.

Aesthetic rejection of otherwise valid evidence is not an exception; it is a `FAIL` check in the report.

Missing subjective review evidence is not an exception; it is `DEFERRED`.

## Golden Sample policy

C8 reuses `construction/fixtures/vanilla-golden/`. It does not create a second pavilion fixture or duplicate C3 evidence.

C8 adds only C8-specific expected artifacts/evidence alongside or under that existing fixture according to the tree that exists at implementation time. Exact paths are chosen in the implementation plan after re-auditing the fixture contents.

The Golden acceptance proves:

- canonical renderer emits all seven views;
- repeated rendering is byte-identical;
- view hashes bind to the expected Build IR;
- objective metrics are stable;
- no-review invocation yields `DEFERRED` subjective checks rather than fabricated PASS;
- stale/tampered review evidence fails closed;
- a checked-in review record bound to exact canonical view hashes can resolve all C8 subjective checks to deterministic PASS/FAIL for that Golden artifact;
- `runtime_visual_fidelity` remains `DEFERRED` even when all offline subjective checks pass.

The Golden review record is evidence about the offline diagnostic preview only and is not evidence of Minecraft runtime appearance.

## TDD acceptance matrix

The implementation plan must include, at minimum, RED-first tests for these scenarios:

1. C8 module import absent before implementation.
2. Canonical renderer rejects invalid/tampered C2 Build IR.
3. Renderer emits exactly seven fixed view ids.
4. Repeated rendering produces byte-identical SVG bytes.
5. View SVGs contain exact Build IR fingerprint metadata.
6. Orthographic occlusion selects the correct nearest visible state.
7. Opposite views reverse occlusion authority correctly.
8. Top view uses correct `y` visibility.
9. Isometric output order is deterministic.
10. Layers view includes every occupied `y` level exactly once.
11. Diagnostic colors are stable by canonical state identity.
12. Objective occupancy metrics are correct on a minimal fixture.
13. Projection metrics are correct on a minimal asymmetric fixture.
14. Palette-distribution metrics match C2 block counts.
15. Optional C5 role labels bind only to matching selected states.
16. Repetition metrics distinguish repeated and non-repeated projected patterns.
17. Facade-depth metrics distinguish flat and stepped facades.
18. Layer-density metrics are deterministic and exact-fraction based.
19. Missing review evidence leaves all subjective checks `DEFERRED`.
20. Valid review evidence resolves one subjective check to `PASS`.
21. Valid review evidence resolves one subjective check to `FAIL` and overall status to `FAIL`.
22. Partial review leaves omitted required subjective checks `DEFERRED` and overall `DEFERRED`.
23. Stale view hash in review evidence fails closed.
24. Wrong BuildSpec or Build IR fingerprint in review evidence fails closed.
25. Unknown/duplicate review decisions fail closed.
26. Review evidence cannot resolve `runtime_visual_fidelity`.
27. Supplied mismatched C7 structural report fails closed.
28. Supplied matching C7 report is provenance only and does not alter visual decisions.
29. Supplied malformed/mismatched C5 palette resolution fails closed.
30. Report validates against `visual-qa-report.schema.json`.
31. `qa.require_determinism=true` proves byte-identical views and canonical report JSON.
32. Vanilla Golden renders and matches checked-in expected C8 evidence.
33. C7/C6/C5/C4/C3/C2/C0 regressions remain green.

Minimal inline fixtures may be used for projection/math tests. The canonical vanilla Golden remains the end-to-end C8 fixture.

## CI design

The dedicated workflow is `.github/workflows/factory-construction-c8-visual-qa.yml`.

It follows existing Construction workflow pinning and environment conventions rather than inventing new action versions.

Minimum C8 workflow sequence:

1. recursive checkout with the same preserved-upstream behavior used by current Construction workflows;
2. Python 3.11 setup using the existing pinned action revision;
3. Java 21 setup using the existing pinned action revision because the inherited C4 runtime probe regression remains part of the gate;
4. install the hashed Construction test environment with `--require-hashes --no-deps`;
5. run C8 visual QA tests;
6. run C7 regression;
7. run C6 regression;
8. run C5 regression;
9. run shared Engineering I2 regression;
10. run C4 registry tests including runtime-registry probe tests;
11. materialize the C4 NeoForge runtime registry probe;
12. run its Gradle `test build --no-daemon` with the same isolated CI `GRADLE_USER_HOME` convention as C4/C7;
13. run C3 regression;
14. run C2 regression;
15. run C0 tests;
16. run `python3 construction/scripts/validate_c0.py`;
17. run C8-scope whitespace validation with `git diff --check`.

C1A/C1B, Governance, Sonar, and any repository-wide required checks remain PR/repository gates. C8 does not weaken or replace them.

C8 is complete only when the exact PR head is green across its dedicated workflow and all required repository checks, followed by the same post-merge validation discipline used for prior Construction phases.

## Documentation and status policy

Implementation documentation updates occur only after executable evidence exists.

When C8 implementation is proven:

- `construction/README.md` may add a C8 scope section;
- `construction/docs/ARCHITECTURE.md` may replace its future-C8 wording with the implemented contract;
- `construction/STATUS.md` is updated only after implementation/PR/post-merge evidence, preserving historical records.

The implementation PR must not prematurely mark C8 complete merely because code exists.

## Non-goals

C8 does not:

- render actual Minecraft block models/textures;
- resolve connected textures, multipart runtime rendering, copycat/material-bearing blocks, dynamic renderers, shader state, biome tint, emissive layers, or translucent sorting;
- load resource packs or provider render pipelines;
- boot a Minecraft client;
- place the structure in a live world;
- capture in-game screenshots;
- prove multiplayer visual consistency;
- prove client/server separation;
- prove runtime performance;
- prove real lighting/material/texture fidelity;
- infer semantic rooms from `geometry.required_spaces`;
- replace C7 structural QA;
- replace C12 Runtime Acceptance;
- modify C4/C5 authority;
- modify C6 schematic authority;
- introduce C9 MCP/agent operations;
- integrate C10 external providers;
- silently convert native authoring formats.

## Acceptance criteria

C8 design is satisfied when implementation proves all of the following:

1. canonical diagnostic rendering consumes only C2-valid Build IR;
2. seven fixed SVG views are deterministic and fingerprint-bound;
3. report contract is schema-versioned and independently validated;
4. objective metrics are deterministic, exact, and explicitly described as proxies where appropriate;
5. structural evidence cannot become visual PASS automatically;
6. C5 role evidence may annotate palette hierarchy but cannot claim real render fidelity;
7. subjective visual checks remain `DEFERRED` without explicit bound review evidence;
8. stale/tampered review evidence fails closed;
9. explicit review evidence can resolve offline visual checks to PASS/FAIL;
10. `runtime_visual_fidelity` remains `DEFERRED` in C8 regardless of offline review outcome;
11. vanilla Golden provides deterministic preview/report regression without duplicating the construction fixture;
12. no runtime/client/render-provider responsibility is stolen from C12 or later provider phases;
13. C7 through C0 regressions remain green;
14. exact PR-head CI/repository gates are green;
15. post-merge validation confirms the merged C8 state before status is closed.
