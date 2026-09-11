# Construction C8 Visual QA Design

## Purpose

C8 adds deterministic offline preview generation and evidence-gated visual QA for Construction artifacts after C7 Architecture QA and before C12 Runtime Acceptance.

C8 keeps three evidence classes separate:

1. **structural evidence** — owned by C7;
2. **canonical offline preview evidence** — owned by C8;
3. **actual Minecraft runtime capture** — reserved for C12 or a later explicit runtime visual handoff.

The selected design is **Conservative Offline Preview + Evidence-Gated Visual QA**. C8 must never convert structural validity, palette selection, or the mere existence of preview files into an aesthetic `PASS`.

## Scope and authority

C8 consumes existing authorities rather than creating parallel representations:

- `construction/schemas/build-spec.schema.json` remains the intent contract.
- `construction/core/build_ir.py` and `construction/schemas/build-ir.schema.json` remain canonical voxel authority.
- `construction/core/structural_qa.py` remains structural QA authority.
- `construction/core/modded_palette.py` remains palette-role selection authority when C5 evidence is supplied.
- `construction/core/modpack_registry.py` remains block/state runtime-evidence authority.
- `construction/core/sponge_v3.py` remains schematic serialization authority.
- `art/standards/VISUAL-QA.md` remains the cross-domain visual-evidence standard; C8 follows its fail-closed evidence policy without moving Construction authority into `art/`.
- `art/golden-samples/` remains reference evidence for the rule that visual acceptance stays pending/deferred when rendered evidence does not exist. Construction does not duplicate those Art fixtures.

C8 is explicitly separate from C7 Architecture QA and C12 Runtime Acceptance.

## Selected design

C8 renders Canonical Build IR into deterministic diagnostic SVG views with a Factory-owned renderer. This renderer is intentionally **not** a Minecraft block renderer. It does not resolve real block models, textures, connected textures, multipart runtime models, copycat/material-bearing blocks, dynamic renderers, biome tint, lighting, emissive layers, translucent sorting, shaders, or provider-specific rendering.

Preview colors are stable diagnostic pseudo-colors derived from canonical block-state identity. They exist to distinguish regions and palette states reproducibly. They are never described as Minecraft material colors or texture fidelity.

C8 computes objective metrics from Build IR and projections. Subjective visual checks become `PASS` or `FAIL` only through explicit `review_evidence` bound to the exact BuildSpec, Build IR, renderer version, and canonical view hashes. Missing subjective evidence remains `DEFERRED`.

Rejected alternatives:

1. **Full offline Minecraft block renderer.** Exact physical-modpack rendering would immediately require provider/CTM/dynamic-renderer semantics that belong to later provider/runtime work and would create a competing renderer authority.
2. **In-game automated capture in C8.** Client boot, resource loading, placement, graphics automation, lighting, and runtime health belong to C12 Runtime Acceptance.

## Files introduced by C8

Implementation creates only the focused units below:

- `construction/core/visual_qa.py` — C8 orchestration, validation, metrics, review-evidence handling, and report construction.
- `construction/qa/preview_renderer.py` — deterministic diagnostic SVG renderer.
- `construction/schemas/visual-qa-report.schema.json` — versioned C8 report contract.
- `construction/tests/test_c8_visual_qa.py` — renderer, metric, evidence, determinism, and failure-mode tests.
- `.github/workflows/factory-construction-c8-visual-qa.yml` — dedicated C8 CI plus inherited regressions.

`construction/qa/` does not exist before C8 and is created only when C8 implementation starts.

The existing Vanilla Golden is reused. C8 adds these exact fixture paths:

- `construction/fixtures/vanilla-golden/c8/front.svg`
- `construction/fixtures/vanilla-golden/c8/back.svg`
- `construction/fixtures/vanilla-golden/c8/left.svg`
- `construction/fixtures/vanilla-golden/c8/right.svg`
- `construction/fixtures/vanilla-golden/c8/top.svg`
- `construction/fixtures/vanilla-golden/c8/isometric.svg`
- `construction/fixtures/vanilla-golden/c8/layers.svg`
- `construction/fixtures/vanilla-golden/c8/review-evidence.json`
- `construction/fixtures/vanilla-golden/c8/expected-visual-qa-report.json`

No second BuildSpec, Build IR, palette, registry, structural-report, or runtime-render schema is introduced.

## Public interfaces

`construction/qa/preview_renderer.py` exposes:

```python
class PreviewRenderError(ValueError):
    pass


def render_canonical_views(build_ir: dict) -> dict[str, bytes]:
    ...
```

The returned mapping contains exactly seven SVG byte payloads keyed by stable view id.

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

`render_canonical_views` is pure with respect to repository and machine state: identical valid Build IR produces byte-identical SVG bytes.

`run_visual_qa` fails closed for malformed or inconsistent authority/evidence inputs. Aesthetic rejection of otherwise valid evidence becomes a report `FAIL`, not an exception.

## Input validation and cross-authority checks

### BuildSpec and Build IR

- `build_spec` must be an object with `schema_version=1` and valid fields consumed by C8.
- `build_ir` must pass C2 `validate_build_ir` with zero errors.
- `build_ir.metadata.build_spec_sha256` must equal C2 `build_spec_fingerprint(build_spec)`.
- geometry, palette, coordinates, and occupancy come only from C2 Build IR.
- absent sparse coordinates remain air exactly as defined by C2.

### Structural report

`structural_report` is optional provenance/context. When supplied:

- C8 calls the existing C7 report validator rather than inventing a second structural validator;
- its `build_spec_sha256` must match the current BuildSpec;
- its `build_ir_sha256` must match C2 `fingerprint_build_ir(build_ir)`;
- C8 computes `structural_report_sha256` as SHA-256 of canonical JSON of the supplied C7 report;
- a C7 `PASS` does not resolve any C8 visual check.

C8 does **not** require C7 to publish a report fingerprint field that does not currently exist.

Malformed or mismatched supplied C7 evidence raises `VisualQAError`.

### C5 palette resolution

`palette_resolution` is optional semantic context. When supplied:

- `schema_version` must be `1`;
- its `build_spec_sha256` must equal C2 `build_spec_fingerprint(build_spec)`; C2 and C5 currently use the same canonical JSON SHA-256 rule for BuildSpec;
- role names and selected states consumed by C8 must satisfy the current C5 output structure;
- C8 computes `palette_resolution_sha256` as SHA-256 of canonical JSON of the exact supplied C5 object;
- matching C5 roles may label palette-distribution evidence but never prove real texture/material appearance.

Malformed or mismatched supplied C5 evidence raises `VisualQAError`.

### Canonical views

`views` must contain exactly these ids and no others, in the report's fixed order:

1. `front`
2. `back`
3. `left`
4. `right`
5. `top`
6. `isometric`
7. `layers`

Every payload must be non-empty UTF-8 SVG bytes produced by renderer version `c8-svg-v1`. C8 parses SVG with standard-library XML facilities, rejects script/external-resource elements or attributes, verifies embedded Build IR fingerprint metadata, recomputes each SHA-256, and records it in the report.

Missing, extra, malformed, unsafe, or fingerprint-mismatched views raise `VisualQAError` before report emission.

## Renderer version `c8-svg-v1`

### Global constants

- orthographic cell size: `16` SVG units;
- orthographic outer padding: `16` SVG units;
- layer cell size: `8` SVG units;
- layer tile gap: `8` SVG units;
- layer outer padding: `8` SVG units;
- isometric half-width: `8` SVG units;
- isometric half-height: `4` SVG units;
- isometric vertical height: `8` SVG units;
- isometric outer padding: `16` SVG units;
- SVG numeric geometry uses integers only.

### Orthographic orientation, occlusion, and canvas

For a C2 block `(x, y, z)` and bounds `(size_x, size_y, size_z)`:

- `front`: viewer at negative `z` looking positive `z`; logical `u=x`, `v=y`; smallest `z` wins.
- `back`: viewer at positive `z` looking negative `z`; logical `u=size_x-1-x`, `v=y`; largest `z` wins.
- `left`: viewer at negative `x` looking positive `x`; logical `u=size_z-1-z`, `v=y`; smallest `x` wins.
- `right`: viewer at positive `x` looking negative `x`; logical `u=z`, `v=y`; largest `x` wins.
- `top`: viewer above positive `y` looking negative `y`; logical `u=x`, `v=size_z-1-z`; largest `y` wins.

Canvas dimensions are fixed from full C2 bounds:

- `front`/`back`: width `size_x*16 + 32`, height `size_y*16 + 32`;
- `left`/`right`: width `size_z*16 + 32`, height `size_y*16 + 32`;
- `top`: width `size_x*16 + 32`, height `size_z*16 + 32`.

Rectangle placement:

- cardinal vertical views: `px=16 + u*16`, `py=16 + (size_y-1-v)*16`;
- top view: `px=16 + u*16`, `py=16 + v*16`.

Every visible block occupies one `16x16` rectangle. Full-bounds canvases prevent host-dependent cropping and keep dimensions stable when occupancy changes inside the same bounds.

### Isometric projection and canvas

For block origin `(x, y, z)`:

```text
base_x = (x - z) * 8
base_y = (x + z) * 4 - y * 8
```

Visible diagnostic faces use these exact vertices before global canvas translation:

- `top`: `(base_x,base_y-4)`, `(base_x+8,base_y)`, `(base_x,base_y+4)`, `(base_x-8,base_y)`;
- `negative_x`: `(base_x-8,base_y)`, `(base_x,base_y+4)`, `(base_x,base_y+12)`, `(base_x-8,base_y+8)`;
- `negative_z`: `(base_x+8,base_y)`, `(base_x,base_y+4)`, `(base_x,base_y+12)`, `(base_x+8,base_y+8)`.

A face is emitted only when the immediately adjacent block in that face direction is absent from C2 occupancy. Top checks `(x,y+1,z)`, negative-`x` checks `(x-1,y,z)`, and negative-`z` checks `(x,y,z-1)`; coordinates outside C2 bounds are absent.

Blocks are processed in fixed painter order `(x + z, y, z, x)`. For each block, emitted faces use fixed order `negative_z`, `negative_x`, `top`.

The canvas is occupancy-independent. To calculate its raw min/max bounds, evaluate the three face polygons above for the eight extreme C2 block coordinates formed by:

- `x` in `{0, size_x-1}`;
- `y` in `{0, size_y-1}`;
- `z` in `{0, size_z-1}`.

Take min/max across all resulting vertices, then translate all rendered vertices so raw `(min_x,min_y)` maps to `(16,16)`. Final width is `(max_x-min_x)+32`; final height is `(max_y-min_y)+32`.

This rule applies even when Build IR has zero occupied blocks, so empty output still has a fully defined deterministic canvas.

The projection is diagnostic and does not claim Minecraft camera/perspective fidelity.

### Layers contact sheet

Every C2 `y` level from `0` through `size_y-1` is represented exactly once, including empty levels.

Each tile is top-down with:

- tile width `size_x*8`;
- tile height `size_z*8`;
- cell logical `u=x`, `v=size_z-1-z`;
- cell placement within tile `px=u*8`, `py=v*8`.

Tiles are ordered by ascending `y`. Let `cols=ceil_sqrt(size_y)` using integer arithmetic and `rows=ceil_div(size_y, cols)`.

Contact-sheet canvas:

- width `16 + cols*(size_x*8) + (cols-1)*8`;
- height `16 + rows*(size_z*8) + (rows-1)*8`.

Tile at zero-based index `i` uses column `i % cols`, row `i // cols`, with origin:

- `tile_x = 8 + column*(size_x*8 + 8)`;
- `tile_y = 8 + row*(size_z*8 + 8)`.

No font metrics or text labels affect geometry. Each tile group carries its `y` value as inert SVG data metadata. Including empty levels prevents layout changes merely because a layer becomes empty.

### Diagnostic pseudo-colors

For canonical block-state string `S`:

1. compute `SHA-256(UTF-8(S))`;
2. let the first three digest bytes be `b0`, `b1`, `b2`;
3. base RGB is `(64 + b0 % 128, 64 + b1 % 128, 64 + b2 % 128)`;
4. orthographic and layers use base RGB;
5. isometric `top` uses base RGB, `negative_x` uses `floor(channel*85/100)`, `negative_z` uses `floor(channel*70/100)`;
6. serialize colors as lowercase six-digit hex.

This algorithm is diagnostic identity mapping only. Color collisions do not imply semantic equality, and colors never claim actual Minecraft texture/material appearance.

### SVG safety and byte determinism

Canonical SVG:

- is UTF-8 with one final newline;
- has fixed XML/SVG element and attribute order controlled by Factory code;
- uses no scripts, event handlers, foreign objects, external URLs, network resources, filesystem paths, timestamps, random ids, stylesheets, or environment-derived content;
- stores renderer version and exact C2 Build IR SHA-256 in inert metadata/data attributes;
- does not use geometry dependent on system fonts, DPI, locale, browser layout, GPU state, or OS theme.

Tests compare canonical bytes/hashes, not rasterized font behavior.

## Objective metrics

Metrics are descriptive evidence, never aesthetic truth.

### Occupancy metrics

- occupied block count;
- canonical palette-state count;
- occupied min/max coordinate per axis, or `null` min/max when empty;
- occupied extent dimensions, or zeros when empty;
- occupied bounding-box volume;
- occupied density inside occupied bounding box as exact fraction;
- occupied density inside full C2 bounds as exact fraction.

Fractions use reduced `{numerator, denominator}` integers. Zero numerator uses denominator `1`.

### Projection metrics

For each `front`, `back`, `left`, `right`, `top`:

- projected occupied-cell count;
- projected occupied bounding width/height, zero when empty;
- projected occupancy ratio as exact fraction;
- cardinal connected-component count on projected occupied cells;
- dominant component size;
- aspect ratio as reduced `{numerator, denominator}` using width/height; empty height yields `{0,1}`.

These metrics support silhouette review but do not define aesthetic thresholds.

### Palette-distribution metrics

For each C2 palette state in canonical order:

- canonical state string;
- occupied block count;
- fraction of all occupied blocks as exact fraction;
- visible-cell count per orthographic/top view;
- sorted matching C5 role labels when optional C5 evidence is supplied.

C8 does not invent material names from block ids.

### Repetition metrics

For every orthographic/top visible grid:

- distinct row-signature count;
- distinct column-signature count;
- repeated row-signature count;
- repeated column-signature count;
- longest adjacent identical-row run;
- longest adjacent identical-column run;
- repeated-row and repeated-column ratios as exact fractions.

Signatures include canonical visible palette identity plus empty cells across full projected C2 bounds. Metrics expose repetition but do not decide whether repetition is desirable.

### Facade-depth metrics

For `front`, `back`, `left`, `right`, retain winning ray depth per visible projected cell and derive:

- distinct visible depth count;
- minimum/maximum visible depth, or `null` when empty;
- depth range, zero when fewer than two depths exist;
- cardinal adjacent visible-pair count;
- adjacent depth-transition count;
- transition ratio as exact fraction.

This is a depth/readability proxy only. It does not model lighting, textures, connected models, bevels, transparency, or dynamic-renderer depth.

### Layer-density metrics

For every `y` in `0..size_y-1`:

- occupied cells;
- footprint area `size_x*size_z`;
- density as exact fraction;
- palette-state counts in canonical palette order.

Aggregate values include level count, minimum occupied cells, maximum occupied cells, and the ordered middle pair used as exact median representation. No floating-point median is emitted.

These metrics support interior-density review but do not identify rooms or intentional interior volumes.

## Visual QA report contract

Top-level fields:

- `schema_version`: `1`;
- `build_spec_sha256`;
- `build_ir_sha256`;
- `structural_report_sha256`: canonical SHA-256 of supplied C7 report or `null`;
- `palette_resolution_sha256`: canonical SHA-256 of supplied C5 object or `null`;
- `review_evidence_sha256`: canonical SHA-256 of supplied review evidence or `null`;
- `renderer_version`: `c8-svg-v1`;
- `views`: fixed-order view descriptors;
- `metrics`;
- `checks`: fixed-order check results;
- `overall_status`: `PASS`, `FAIL`, or `DEFERRED`;
- `content_sha256`: report fingerprint from canonical report JSON with only `content_sha256` omitted.

Canonical object hashing uses UTF-8 JSON with sorted keys, compact separators, `ensure_ascii=false`, and no final newline in the hashed payload, matching the C2/C5 JSON fingerprint convention. File serialization adds one final newline after hashing.

Each view descriptor:

- `id`;
- deterministic `artifact_name` (`front.svg`, `back.svg`, `left.svg`, `right.svg`, `top.svg`, `isometric.svg`, `layers.svg`);
- `media_type`: `image/svg+xml`;
- `sha256`;
- `byte_length`;
- integer canvas `width` and `height`;
- `evidence_class`: `canonical_offline_preview`.

SVG bytes are separate artifacts, not embedded in report JSON.

Each check:

- `id`;
- `required`;
- `status`: `PASS`, `FAIL`, `DEFERRED`, `NOT_APPLICABLE`;
- `severity`: `error`, `warning`, `info`;
- deterministic `summary`;
- fixed/sorted `evidence_views`;
- deterministic machine-readable `findings`.

Overall status:

1. `FAIL` if any required check is `FAIL`;
2. otherwise `DEFERRED` if any required check is `DEFERRED`;
3. otherwise `PASS`.

## C8 checks

### `canonical_preview_integrity`

Always required. A complete, safe, fingerprint-matching canonical view set yields `PASS`. Malformed view input raises `VisualQAError` before report emission.

### `silhouette_readability`

Always required. Evidence set: `front`, `back`, `left`, `right`, `top`, `isometric`, plus projection metrics.

No bound decision => `DEFERRED`; review `PASS` => `PASS`; review `FAIL` => `FAIL`. No projection-density threshold automatically decides quality.

### `proportion`

Always required. Evidence set: `front`, `back`, `left`, `right`, `top`, `isometric`, plus occupied extents/aspect ratios and `geometry.architectural_brief` when present.

No bound decision => `DEFERRED`; bound review decides `PASS` or `FAIL`. If the brief is absent, review may assess internal massing consistency but cannot invent a requested style target.

### `material_hierarchy`

Always required. Evidence set: all seven views, canonical block-state legend, palette-distribution metrics, optional C5 role labels.

No bound decision => `DEFERRED`; bound review decides `PASS` or `FAIL`.

A `PASS` proves only offline palette/state distribution hierarchy. It does not prove texture quality, real material appearance, CTM, emissive, transparency, tint, shader, or lighting fidelity.

### `repetition`

Always required. Evidence set: `front`, `back`, `left`, `right`, `top`, `isometric`, plus repetition metrics.

No bound decision => `DEFERRED`; bound review decides `PASS` or `FAIL`. No universal repetition threshold exists because repetition may be intentional.

### `facade_readability`

Always required. Evidence set: `front`, `back`, `left`, `right`, `isometric`, plus facade-depth metrics.

No bound decision => `DEFERRED`; bound review decides `PASS` or `FAIL`. `PASS` is limited to diagnostic mass/depth organization, not runtime lighting/texture readability.

### `interior_density`

Always required. Evidence set: `layers`, `isometric`, `top`, plus layer-density metrics and `geometry.required_spaces` names as non-spatial intent only.

No bound decision => `DEFERRED`; bound review decides `PASS` or `FAIL`. C8 never marks a named required space satisfied because BuildSpec v1 does not map spaces to coordinates.

### `runtime_visual_fidelity`

Not required for C8 completion. Always `DEFERRED` with severity `info`. C8 review evidence is forbidden from resolving it; it is the explicit handoff to C12/runtime visual evidence.

## Review evidence contract

`review_evidence` is optional and is the only authority that may resolve C8 subjective checks.

Required fields when supplied:

- `schema_version`: `1`;
- `build_spec_sha256`;
- `build_ir_sha256`;
- `renderer_version`: `c8-svg-v1`;
- `views`: exactly seven `{id, sha256}` records in canonical C8 view order, all matching current artifacts;
- `reviewer`: `kind` in `human|agent` plus non-empty stable `id`;
- `decisions`: unique subjective-check decisions in fixed C8 check order after normalization.

Each decision:

- `check_id`: one of `silhouette_readability`, `proportion`, `material_hierarchy`, `repetition`, `facade_readability`, `interior_density`;
- `status`: only `PASS` or `FAIL`;
- `evidence_views`: non-empty unique list whose members belong to that check's evidence set above;
- `summary`: non-empty review statement.

Validation rules:

- BuildSpec, Build IR, renderer version, and all seven view hashes must match current C8 inputs exactly.
- unknown, missing, duplicate, or out-of-order canonical view records fail closed.
- unknown or duplicate check decisions fail closed; decision input order is normalized to fixed C8 check order before report construction.
- `runtime_visual_fidelity` is not a legal decision.
- a decision must reference at least one allowed view for its check.
- omitted subjective checks remain `DEFERRED`.
- `review_evidence_sha256` is SHA-256 of canonical JSON of the exact supplied evidence object before decision-order normalization, preserving exact evidence provenance.

A human or agent review is valid process evidence only when the reviewer actually inspects the named rendered artifacts. Reading metric JSON alone is insufficient for subjective visual acceptance.

## Determinism

### SVG artifacts

- seven fixed ids and fixed renderer version;
- integer projection geometry only;
- canonical C2 state identity and fixed pseudo-color algorithm;
- fixed occlusion, traversal, face, row, tile, and polygon ordering;
- no timestamps, random ids, machine paths, external resources, GPU state, OS fonts, locale, or environment-derived configuration;
- one final newline;
- each SHA-256 recorded in the report.

### JSON report

- canonical sorted compact JSON;
- exact integer/fraction objects instead of floating-point ratios;
- fixed view/check ordering;
- deterministic findings/role labels;
- no wall-clock timestamps or transient CI metadata;
- `content_sha256` excludes only itself from the hashed payload;
- serialized file ends with one final newline.

When `qa.require_determinism=true`, tests render/analyze the same authoritative inputs at least twice and prove byte-identical SVG artifacts plus byte-identical canonical report JSON.

## Error handling

C8 raises `PreviewRenderError` or `VisualQAError` for malformed/inconsistent authority or evidence inputs, including:

- invalid BuildSpec type/version in consumed fields;
- invalid/tampered C2 Build IR;
- BuildSpec/Build IR fingerprint mismatch;
- malformed/mismatched C7 structural report;
- malformed/mismatched C5 palette resolution;
- missing/extra canonical views;
- malformed/unsafe SVG;
- renderer-version mismatch;
- embedded Build IR fingerprint mismatch;
- stale review evidence;
- wrong BuildSpec/Build IR/view hashes in review evidence;
- missing/duplicate/unknown review view records;
- unknown/duplicate review decisions;
- attempt to resolve `runtime_visual_fidelity`.

Aesthetic rejection of valid evidence is a report `FAIL`. Missing subjective review evidence is `DEFERRED`.

## Vanilla Golden policy

C8 reuses:

- `construction/fixtures/vanilla-golden/build-spec.json`
- `construction/fixtures/vanilla-golden/expected-build-ir.json`
- `construction/fixtures/vanilla-golden/generate.py`

It adds only the `construction/fixtures/vanilla-golden/c8/` artifacts listed earlier.

Golden acceptance proves:

- all seven canonical SVGs render;
- repeated rendering is byte-identical;
- view hashes and embedded metadata bind to expected Build IR;
- objective metrics are stable;
- no-review invocation yields `DEFERRED` subjective checks;
- stale/tampered review evidence fails closed;
- checked-in review evidence binds to exact canonical view hashes and resolves all six offline subjective checks to deterministic PASS/FAIL for the Golden artifact;
- expected report matches canonical output byte-for-byte;
- `runtime_visual_fidelity` remains `DEFERRED` even if all offline visual checks pass.

The Golden review record is evidence about C8 diagnostic preview only, never Minecraft runtime appearance.

## TDD acceptance matrix

The implementation plan must include RED-first coverage for at least:

1. C8 modules absent before implementation.
2. Renderer rejects invalid/tampered C2 Build IR.
3. Renderer emits exactly seven fixed view ids.
4. Repeated rendering produces byte-identical SVG bytes.
5. SVG metadata contains exact Build IR fingerprint and renderer version.
6. `front` selects smallest-`z` occlusion winner.
7. `back` selects largest-`z` winner and mirrored `x` screen orientation.
8. `left` selects smallest-`x` winner.
9. `right` selects largest-`x` winner.
10. `top` selects largest-`y` winner.
11. Orthographic canvases/placement follow exact full-bounds formulas.
12. Isometric polygons, exposed-face logic, painter order, and occupancy-independent canvas follow `c8-svg-v1`.
13. Layers contact sheet includes every `0..size_y-1` level exactly once, including empty levels, with exact layout formulas.
14. Diagnostic colors match digest algorithm.
15. SVG safety rejects scripts/external resources/event handlers.
16. Occupancy metrics are correct for empty/non-empty fixtures.
17. Projection metrics are correct for asymmetric fixture.
18. Palette-distribution metrics match C2 counts.
19. Optional C5 role labels attach only to matching selected states.
20. Repetition metrics distinguish repeated/non-repeated patterns without quality thresholds.
21. Facade-depth metrics distinguish flat/stepped facades.
22. Layer-density metrics are exact and include empty levels.
23. Missing review evidence leaves six subjective checks `DEFERRED`.
24. Valid review evidence resolves one subjective check to `PASS`.
25. Valid review evidence resolves one subjective check to `FAIL`, making overall `FAIL`.
26. Partial review leaves omitted required checks `DEFERRED`, making overall `DEFERRED` unless another required check fails.
27. Stale view hash fails closed.
28. Wrong BuildSpec/Build IR fingerprint fails closed.
29. Missing/unknown/duplicate/out-of-order review view records fail closed.
30. Unknown/duplicate review decisions fail closed.
31. Review evidence cannot resolve `runtime_visual_fidelity`.
32. Matching C7 report records provenance only and does not alter visual decisions.
33. Mismatched C7 report fails closed.
34. Matching C5 evidence records deterministic provenance/labels only.
35. Mismatched C5 evidence fails closed.
36. Report `content_sha256` detects tampering.
37. Report validates against `visual-qa-report.schema.json`.
38. `qa.require_determinism=true` proves byte-identical views/report.
39. Vanilla Golden matches checked-in C8 artifacts and expected report.
40. C7/C6/C5/C4/C3/C2/C0 regressions remain green.

Minimal inline fixtures are allowed for projection/math tests. The existing Vanilla Golden is the C8 end-to-end fixture.

## CI design

Dedicated workflow: `.github/workflows/factory-construction-c8-visual-qa.yml`.

It reuses action pins/environment conventions already present in Construction workflows rather than inventing versions.

Minimum sequence:

1. recursive checkout preserving upstream references;
2. Python 3.11 using current pinned Construction action;
3. Java 21 using current pinned Construction action because C4 runtime-probe regression is inherited;
4. install hashed Construction environment with `--require-hashes --no-deps`;
5. C8 visual QA tests;
6. C7 regression;
7. C6 regression;
8. C5 regression;
9. shared Engineering I2 regression;
10. C4 registry/runtime-probe tests;
11. materialize C4 NeoForge runtime registry probe;
12. Gradle `test build --no-daemon` with the same isolated `GRADLE_USER_HOME` convention as C4/C7;
13. C3 regression;
14. C2 regression;
15. C0 tests;
16. `python3 construction/scripts/validate_c0.py`;
17. C8-scope `git diff --check`.

C1A/C1B, Governance, Sonar, and repository-wide checks remain independent PR/repository gates. C8 does not weaken them.

C8 completes only after exact PR-head gates are green and merged `main` passes post-merge Construction validation under the same evidence discipline used by prior phases.

## Documentation and status policy

Only after executable C8 evidence exists:

- `construction/README.md` may add implemented C8 scope;
- `construction/docs/ARCHITECTURE.md` may replace future-C8 language with implemented contract;
- `construction/STATUS.md` is updated after implementation/PR/post-merge evidence while preserving history.

Code existence alone is insufficient to mark C8 complete.

## Non-goals

C8 does not:

- render actual Minecraft block models/textures;
- resolve CTM, multipart runtime rendering, copycats/material-bearing blocks, dynamic renderers, shaders, biome tint, emissive behavior, or translucent sorting;
- load resource packs/provider render pipelines;
- boot Minecraft client;
- place structures in live world;
- capture in-game screenshots;
- prove multiplayer visual consistency;
- prove client/server separation or runtime performance;
- prove real lighting/material/texture fidelity;
- infer semantic rooms from `geometry.required_spaces`;
- replace C7 structural QA;
- replace C12 Runtime Acceptance;
- change C4/C5 authority;
- change C6 schematic authority;
- introduce C9 MCP/agent operations;
- integrate C10 external providers;
- silently convert native authoring formats.

## Acceptance criteria

C8 implementation is accepted only when it proves:

1. canonical diagnostic rendering consumes only C2-valid Build IR;
2. seven fixed SVG views are deterministic, safe, and fingerprint-bound;
3. cardinal orientation/occlusion, isometric geometry/canvas, and layers geometry/canvas follow `c8-svg-v1` exactly;
4. report is schema-versioned, canonical, and self-fingerprinted;
5. objective metrics are deterministic exact evidence and remain proxies where appropriate;
6. structural evidence cannot become visual `PASS` automatically;
7. C5 role evidence may annotate palette hierarchy but cannot claim real render fidelity;
8. subjective checks remain `DEFERRED` without explicit review evidence;
9. stale/tampered review evidence fails closed;
10. explicit bound review evidence can resolve six offline visual checks to PASS/FAIL;
11. `runtime_visual_fidelity` remains `DEFERRED` regardless of offline review outcome;
12. existing Vanilla Golden gains deterministic C8 evidence without duplicating the fixture;
13. no C12/runtime/provider responsibility is pulled into C8;
14. C7 through C0 regressions remain green;
15. exact PR-head CI/repository gates pass;
16. post-merge validation confirms merged C8 before status closeout.
