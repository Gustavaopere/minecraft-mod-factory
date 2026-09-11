# Construction C8 Visual QA Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement deterministic offline Construction preview rendering and evidence-gated Visual QA for C2-valid Build IR without claiming Minecraft runtime-render fidelity.

**Architecture:** Add a pure Factory-owned SVG diagnostic renderer under `construction/qa/` and a C8 orchestration/report layer under `construction/core/`. C8 reuses C2/C5/C7 authorities, computes deterministic exact metrics, accepts explicit hash-bound human/agent review evidence for six offline subjective checks, and keeps runtime visual fidelity permanently deferred to C12.

**Tech Stack:** CPython 3.11 standard library (`hashlib`, `json`, `math`, `xml.etree.ElementTree`, `unittest`), existing Construction contracts, deterministic UTF-8 SVG, GitHub Actions on `ubuntu-24.04`, Java 21/Gradle only for inherited C4 NeoForge runtime-probe regression.

**Spec:** `docs/superpowers/specs/2026-09-11-construction-c8-visual-qa-design.md`

## Global Constraints

- Target remains Minecraft Java Edition `1.21.1`, NeoForge `21.1.248`, Java `21` where NeoForge runtime evidence is exercised.
- C2 `construction/core/build_ir.py` remains the only canonical voxel/geometry authority.
- C5 `construction/core/modded_palette.py` may provide optional semantic role labels but never visual-render fidelity.
- C7 `construction/core/structural_qa.py` remains structural QA authority; C7 status never becomes a C8 visual PASS automatically.
- C8 renderer version is exactly `c8-svg-v1`.
- Canonical C8 view order is exactly `front`, `back`, `left`, `right`, `top`, `isometric`, `layers`.
- Canonical SVGs use only deterministic integer geometry, diagnostic pseudo-colors, no scripts/external resources/timestamps/random ids/system-font geometry/GPU state.
- Subjective checks remain `DEFERRED` without matching explicit `review_evidence`.
- `runtime_visual_fidelity` is never resolvable by C8 review evidence and remains `DEFERRED`.
- No Minecraft block-model/texture renderer, client boot, resource-pack rendering, CTM/copycat/dynamic-renderer behavior, in-game screenshot capture, provider runtime integration, C9 MCP, C10 external-provider work, or C12 runtime acceptance is added in C8.
- No new dependency is added to `construction/upstream/harness/schematica-test-lock.txt`; C8 implementation uses Python standard library only.
- The existing Vanilla Golden under `construction/fixtures/vanilla-golden/` is reused; no duplicate Golden build is created.
- `construction/STATUS.md` is not promoted to C8 complete until implementation is merged and post-merge validation succeeds.

---

### Task 1: Freeze the C8 contract and capture RED1 with production modules absent

**Files:**
- Create: `construction/schemas/visual-qa-report.schema.json`
- Create: `construction/tests/test_c8_visual_qa.py`
- Create: `.github/workflows/factory-construction-c8-visual-qa.yml`
- Existing authority: `docs/superpowers/specs/2026-09-11-construction-c8-visual-qa-design.md`

**Interfaces:**
- Consumes: C2 `validate_build_ir(build_ir) -> list[str]`, `build_spec_fingerprint(build_spec) -> str`, `fingerprint_build_ir(build_ir) -> str`, `canonical_block_state_string(state) -> str`.
- Produces: a complete executable C8 test contract and CI gate before production code exists.

- [ ] **Step 1: Write the complete report schema before production code**

Create `construction/schemas/visual-qa-report.schema.json` as Draft 2020-12 with `additionalProperties: false` at every closed contract object. Encode the spec's exact top-level fields:

```json
{
  "schema_version": 1,
  "build_spec_sha256": "64 lowercase hex",
  "build_ir_sha256": "64 lowercase hex",
  "structural_report_sha256": "64 lowercase hex or null",
  "palette_resolution_sha256": "64 lowercase hex or null",
  "review_evidence_sha256": "64 lowercase hex or null",
  "renderer_version": "c8-svg-v1",
  "views": [],
  "metrics": {},
  "checks": [],
  "overall_status": "PASS|FAIL|DEFERRED",
  "content_sha256": "64 lowercase hex"
}
```

The schema must fix view ids/order semantically through item contracts, exact fraction objects `{numerator, denominator}`, allowed check statuses/severities, and all metrics described by the spec. Do not add `jsonschema` as a runtime dependency; the schema is a machine-readable contract while `validate_visual_qa_report` remains the executable validator.

- [ ] **Step 2: Write one C8 test module covering the complete 40-case acceptance matrix**

Create `construction/tests/test_c8_visual_qa.py` using `unittest`. Resolve repository paths with `Path(__file__).resolve().parents[2]`. Load the existing Vanilla Golden BuildSpec/IR as follows:

```python
ROOT = Path(__file__).resolve().parents[2]
GOLDEN = ROOT / "construction" / "fixtures" / "vanilla-golden"
SPEC_PATH = ROOT / "docs" / "superpowers" / "specs" / "2026-09-11-construction-c8-visual-qa-design.md"
PLAN_PATH = ROOT / "docs" / "superpowers" / "plans" / "2026-09-11-construction-c8-visual-qa.md"
RENDERER_PATH = ROOT / "construction" / "qa" / "preview_renderer.py"
VISUAL_QA_PATH = ROOT / "construction" / "core" / "visual_qa.py"
IMPLEMENTATION_READY = RENDERER_PATH.is_file() and VISUAL_QA_PATH.is_file()
```

Use guarded imports only when `IMPLEMENTATION_READY` is true. Keep contract tests unguarded and behavioral tests under `@unittest.skipUnless(IMPLEMENTATION_READY, "C8 production modules not implemented yet")` so RED1 proves the modules are absent while preserving the entire future test matrix in the same committed file.

Required test groups and named methods:

```python
class C8ContractTests(unittest.TestCase):
    def test_spec_plan_schema_and_workflow_exist(self): ...
    def test_production_modules_exist(self): ...  # RED1 expected failure

@unittest.skipUnless(IMPLEMENTATION_READY, "C8 production modules not implemented yet")
class C8RendererTests(unittest.TestCase):
    def test_renderer_rejects_invalid_build_ir(self): ...
    def test_fixed_view_ids_and_byte_determinism(self): ...
    def test_svg_metadata_binds_renderer_and_ir(self): ...
    def test_front_back_occlusion_and_orientation(self): ...
    def test_left_right_occlusion(self): ...
    def test_top_occlusion(self): ...
    def test_orthographic_canvas_and_cell_placement(self): ...
    def test_isometric_geometry_faces_order_and_canvas(self): ...
    def test_layers_include_empty_levels_and_exact_layout(self): ...
    def test_digest_pseudo_colors(self): ...
    def test_svg_safety_contract(self): ...

@unittest.skipUnless(IMPLEMENTATION_READY, "C8 production modules not implemented yet")
class C8MetricsTests(unittest.TestCase):
    def test_occupancy_metrics_empty_and_nonempty(self): ...
    def test_projection_metrics_asymmetric_fixture(self): ...
    def test_palette_distribution_metrics(self): ...
    def test_c5_role_labels_match_selected_states_only(self): ...
    def test_repetition_metrics_without_quality_threshold(self): ...
    def test_facade_depth_metrics_flat_and_stepped(self): ...
    def test_layer_density_includes_empty_levels(self): ...

@unittest.skipUnless(IMPLEMENTATION_READY, "C8 production modules not implemented yet")
class C8EvidenceAndReportTests(unittest.TestCase):
    def test_missing_review_keeps_six_subjective_checks_deferred(self): ...
    def test_valid_review_can_pass_one_subjective_check(self): ...
    def test_valid_review_can_fail_one_subjective_check(self): ...
    def test_partial_review_keeps_overall_deferred_without_fail(self): ...
    def test_stale_view_hash_fails_closed(self): ...
    def test_wrong_build_fingerprints_fail_closed(self): ...
    def test_review_view_records_fail_closed(self): ...
    def test_review_decisions_fail_closed(self): ...
    def test_runtime_visual_fidelity_cannot_be_resolved(self): ...
    def test_matching_c7_is_provenance_only(self): ...
    def test_mismatched_c7_fails_closed(self): ...
    def test_matching_c5_is_provenance_and_labels_only(self): ...
    def test_mismatched_c5_fails_closed(self): ...
    def test_report_content_sha_detects_tampering(self): ...
    def test_report_validator_and_schema_contract(self): ...
    def test_require_determinism_repeats_views_and_report_bytes(self): ...

@unittest.skipUnless(IMPLEMENTATION_READY, "C8 production modules not implemented yet")
class C8GoldenTests(unittest.TestCase):
    def test_vanilla_golden_matches_checked_in_c8_artifacts(self): ...
```

Use minimal inline C2 fixtures for asymmetric projection, flat/stepped facade, empty levels, and repetition math. Build every inline IR through `canonicalize_build_ir(...)` rather than hand-writing invalid C2 fingerprints.

- [ ] **Step 3: Create the dedicated C8 workflow with the final inherited gate sequence from the start**

Create `.github/workflows/factory-construction-c8-visual-qa.yml` with:

```yaml
name: Factory Construction C8 Visual QA

on:
  push:
    branches:
      - main
      - feat/construction-c8-visual-qa
  pull_request:
    branches:
      - main
    paths:
      - '.github/workflows/factory-construction-c8-visual-qa.yml'
      - 'engineering/tooling/import-physical-modlist.py'
      - 'engineering/tests/test_i2_modlist_catalog.py'
      - 'engineering/tests/test_i2_security_review.py'
      - 'engineering/tooling/scaffolder/**'
      - 'engineering/templates/neoforge-mod/**'
      - 'construction/README.md'
      - 'construction/docs/ARCHITECTURE.md'
      - 'construction/core/visual_qa.py'
      - 'construction/qa/**'
      - 'construction/core/structural_qa.py'
      - 'construction/core/build_ir.py'
      - 'construction/core/modded_palette.py'
      - 'construction/core/modpack_registry.py'
      - 'construction/schemas/visual-qa-report.schema.json'
      - 'construction/schemas/structural-qa-report.schema.json'
      - 'construction/schemas/build-spec.schema.json'
      - 'construction/schemas/build-ir.schema.json'
      - 'construction/schemas/modpack-registry.schema.json'
      - 'construction/fixtures/vanilla-golden/c8/**'
      - 'construction/runtime/neoforge-registry-probe/**'
      - 'construction/scripts/prepare_neoforge_registry_probe.py'
      - 'construction/tests/test_c8_visual_qa.py'
      - 'construction/tests/test_c7_architecture_qa.py'
      - 'construction/tests/test_c7_registry_authority.py'
      - 'construction/tests/test_c6_sponge_v3.py'
      - 'construction/tests/test_c5_modded_palette.py'
      - 'construction/tests/test_c4_modpack_registry.py'
      - 'construction/tests/test_c4_runtime_registry_probe.py'
      - 'construction/tests/test_c3_vanilla_golden.py'
      - 'construction/tests/test_c2_build_ir.py'
      - 'construction/tests/test_c0_foundation.py'
      - 'docs/superpowers/specs/2026-09-11-construction-c8-visual-qa-design.md'
      - 'docs/superpowers/plans/2026-09-11-construction-c8-visual-qa.md'

permissions:
  contents: read
```

Use the exact existing pins:

```yaml
- uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262
  with:
    fetch-depth: 2
    submodules: recursive
- uses: actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065
  with:
    python-version: '3.11'
- uses: actions/setup-java@cf277c60eb25467037889841efdb72551f06f6c3
  with:
    distribution: temurin
    java-version: '21'
```

Then run, in this order:

```bash
python3 -m pip install --require-hashes --no-deps -r construction/upstream/harness/schematica-test-lock.txt
python3 -m unittest engineering/tests/test_i2_modlist_catalog.py engineering/tests/test_i2_security_review.py -v
python3 -m unittest construction/tests/test_c8_visual_qa.py -v
python3 -m unittest construction/tests/test_c7_architecture_qa.py construction/tests/test_c7_registry_authority.py -v
python3 -m unittest construction/tests/test_c6_sponge_v3.py -v
python3 -m unittest construction/tests/test_c5_modded_palette.py -v
python3 -m unittest construction/tests/test_c4_modpack_registry.py construction/tests/test_c4_runtime_registry_probe.py -v
python3 construction/scripts/prepare_neoforge_registry_probe.py --output .factory-ci/c8/runtime-probe
chmod +x .factory-ci/c8/runtime-probe/gradlew
cd .factory-ci/c8/runtime-probe
GRADLE_USER_HOME="$GITHUB_WORKSPACE/.factory-ci/c8/gradle-home" ./gradlew test build --no-daemon
cd "$GITHUB_WORKSPACE"
python3 -m unittest construction/tests/test_c3_vanilla_golden.py -v
python3 -m unittest construction/tests/test_c2_build_ir.py -v
python3 -m unittest construction/tests/test_c0_foundation.py -v
python3 construction/scripts/validate_c0.py
```

Finish with C8-scope `git diff --check HEAD^ --` over the C8 workflow, modules, schema, test, Golden `c8/`, spec, plan, README, ARCHITECTURE, and STATUS paths.

- [ ] **Step 4: Commit the RED1 contract**

```bash
git add .github/workflows/factory-construction-c8-visual-qa.yml construction/schemas/visual-qa-report.schema.json construction/tests/test_c8_visual_qa.py
git commit -m "test(construction): define C8 visual QA contract"
```

- [ ] **Step 5: Verify RED1 on the exact branch head**

Expected C8 result:

```text
contract/schema/workflow tests: PASS
production module existence test: FAIL
behavioral C8 tests: SKIP because production modules do not exist
```

Do not create `construction/core/visual_qa.py` or `construction/qa/preview_renderer.py` until this RED is recorded from GitHub Actions on the exact commit SHA.

---

### Task 2: Replace RED1 skips with a behavioral RED2 using minimal public-interface stubs

**Files:**
- Create: `construction/qa/preview_renderer.py`
- Create: `construction/core/visual_qa.py`
- Test: `construction/tests/test_c8_visual_qa.py`

**Interfaces:**
- Produces exactly the approved public classes/functions while deliberately leaving behavior unimplemented.

- [ ] **Step 1: Add the minimal renderer stub**

```python
from __future__ import annotations


class PreviewRenderError(ValueError):
    pass


def render_canonical_views(build_ir: dict) -> dict[str, bytes]:
    raise PreviewRenderError("C8 preview renderer implementation is not available yet")
```

- [ ] **Step 2: Add the minimal Visual QA stub**

```python
from __future__ import annotations


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
    raise VisualQAError("C8 visual QA implementation is not available yet")


def validate_visual_qa_report(report: dict) -> None:
    raise VisualQAError("C8 visual QA implementation is not available yet")
```

- [ ] **Step 3: Commit the stubs**

```bash
git add construction/qa/preview_renderer.py construction/core/visual_qa.py
git commit -m "test(construction): expose C8 behavioral RED"
```

- [ ] **Step 4: Verify RED2 on GitHub Actions**

Run the branch workflow and require:

```text
C8 behavioral tests: execute without SKIP
C8 behavioral tests: FAIL only because public functions still raise deliberate not-available errors
pre-C8 Engineering I2 step: PASS
```

Classify any unrelated failure before implementation. RED2 is complete only when the failures are traceable to the deliberate stubs.

---

### Task 3: Implement deterministic renderer foundations and all orthographic views

**Files:**
- Modify: `construction/qa/preview_renderer.py`
- Test: `construction/tests/test_c8_visual_qa.py`

**Interfaces:**
- Consumes: `validate_build_ir`, `fingerprint_build_ir`, `canonical_block_state_string` from C2.
- Produces: `render_canonical_views(build_ir) -> dict[str, bytes]`, initially with all seven ids while isometric/layers helpers become complete in Task 4.

- [ ] **Step 1: Run renderer-focused RED tests locally/CI before editing**

```bash
python3 -m unittest \
  construction.tests.test_c8_visual_qa.C8RendererTests.test_renderer_rejects_invalid_build_ir \
  construction.tests.test_c8_visual_qa.C8RendererTests.test_fixed_view_ids_and_byte_determinism \
  construction.tests.test_c8_visual_qa.C8RendererTests.test_svg_metadata_binds_renderer_and_ir \
  construction.tests.test_c8_visual_qa.C8RendererTests.test_front_back_occlusion_and_orientation \
  construction.tests.test_c8_visual_qa.C8RendererTests.test_left_right_occlusion \
  construction.tests.test_c8_visual_qa.C8RendererTests.test_top_occlusion \
  construction.tests.test_c8_visual_qa.C8RendererTests.test_orthographic_canvas_and_cell_placement -v
```

Expected: FAIL from the deliberate renderer stub.

- [ ] **Step 2: Implement renderer constants and validation**

Define exact constants:

```python
RENDERER_VERSION = "c8-svg-v1"
VIEW_IDS = ("front", "back", "left", "right", "top", "isometric", "layers")
ORTHO_CELL = 16
ORTHO_PADDING = 16
LAYER_CELL = 8
LAYER_GAP = 8
LAYER_PADDING = 8
ISO_HALF_WIDTH = 8
ISO_HALF_HEIGHT = 4
ISO_VERTICAL = 8
ISO_PADDING = 16
```

Call `validate_build_ir`; if errors exist, raise `PreviewRenderError("invalid C2 Build IR: " + "; ".join(errors))`. Use `fingerprint_build_ir(build_ir)` as the embedded exact Build IR fingerprint.

- [ ] **Step 3: Implement state identity and pseudo-colors exactly**

For each palette entry:

```python
state_key = canonical_block_state_string(state)
digest = hashlib.sha256(state_key.encode("utf-8")).digest()
rgb = tuple(64 + channel % 128 for channel in digest[:3])
```

Serialize lowercase hex `#rrggbb`. For isometric face variants, apply integer `channel * 85 // 100` and `channel * 70 // 100`.

- [ ] **Step 4: Implement a deterministic orthographic projection helper**

Return an internal record containing the full projected grid, winner depth per occupied screen cell, logical width/height, and exact canvas size. Encode the approved winner rules:

```text
front: min z, u=x, v=y
back: max z, u=size_x-1-x, v=y
left: min x, u=size_z-1-z, v=y
right: max x, u=z, v=y
top: max y, u=x, v=size_z-1-z
```

Use full C2 projected bounds even when occupancy is empty.

- [ ] **Step 5: Serialize orthographic SVG bytes without ElementTree reordering**

Build byte content from deterministic escaped strings with a fixed root attribute order. Required root metadata includes:

```xml
<svg xmlns="http://www.w3.org/2000/svg" width="..." height="..." viewBox="0 0 ... ..." data-renderer-version="c8-svg-v1" data-build-ir-sha256="...">
```

Emit visible `<rect>` elements in stable `(v, u)` order, then `</svg>\n`. Do not include XML declarations, stylesheets, scripts, ids, timestamps, paths, URLs, or host metadata.

- [ ] **Step 6: Run the orthographic renderer tests**

Run the exact command from Step 1. Expected: PASS for invalid-input, ids/determinism, metadata, occlusion/orientation, and canvas/placement tests whose isometric/layers assertions are not yet included.

- [ ] **Step 7: Commit the orthographic renderer**

```bash
git add construction/qa/preview_renderer.py construction/tests/test_c8_visual_qa.py
git commit -m "feat(construction): add deterministic C8 orthographic previews"
```

---

### Task 4: Complete `c8-svg-v1` isometric and layers rendering plus SVG safety

**Files:**
- Modify: `construction/qa/preview_renderer.py`
- Test: `construction/tests/test_c8_visual_qa.py`

**Interfaces:**
- Extends: `render_canonical_views` to produce all seven approved canonical SVGs byte-for-byte deterministically.

- [ ] **Step 1: Run the remaining renderer RED tests**

```bash
python3 -m unittest \
  construction.tests.test_c8_visual_qa.C8RendererTests.test_isometric_geometry_faces_order_and_canvas \
  construction.tests.test_c8_visual_qa.C8RendererTests.test_layers_include_empty_levels_and_exact_layout \
  construction.tests.test_c8_visual_qa.C8RendererTests.test_digest_pseudo_colors \
  construction.tests.test_c8_visual_qa.C8RendererTests.test_svg_safety_contract -v
```

Expected: FAIL until isometric/layers contracts are complete.

- [ ] **Step 2: Implement isometric face generation exactly from the spec**

Use:

```python
base_x = (x - z) * 8
base_y = (x + z) * 4 - y * 8
```

Emit only exposed `negative_z`, `negative_x`, `top` faces. Sort blocks by `(x + z, y, z, x)` and faces in that fixed order. Compute occupancy-independent canvas bounds from all three face polygon formulas evaluated over all eight extreme C2 bound coordinates, translate raw minimum to `(16,16)`, then serialize deterministic `<polygon points="...">` elements.

- [ ] **Step 3: Implement the layers contact sheet exactly**

Use integer helpers:

```python
def _ceil_sqrt(value: int) -> int:
    root = math.isqrt(value)
    return root if root * root == value else root + 1


def _ceil_div(value: int, divisor: int) -> int:
    return (value + divisor - 1) // divisor
```

Render every level `0..size_y-1`, including empty levels. Use the spec's tile width/height, gap, outer padding, tile origins, `u=x`, `v=size_z-1-z`, and `data-y="N"` group metadata. Never compact away empty levels.

- [ ] **Step 4: Keep generated SVGs inside the safe subset**

Renderer output may contain only the SVG root, inert `<g>` groups, `<rect>`, `<polygon>`, and inert `data-*` metadata needed by C8. No `script`, `foreignObject`, `style`, event-handler attributes, `href`, `xlink:href`, URLs, or external namespaces beyond the SVG namespace.

- [ ] **Step 5: Run all renderer tests**

```bash
python3 -m unittest construction.tests.test_c8_visual_qa.C8RendererTests -v
```

Expected: all C8 renderer tests PASS.

- [ ] **Step 6: Commit the complete renderer**

```bash
git add construction/qa/preview_renderer.py construction/tests/test_c8_visual_qa.py
git commit -m "feat(construction): complete C8 canonical SVG renderer"
```

---

### Task 5: Implement C8 authority linkage, canonical-view validation, and report foundations

**Files:**
- Modify: `construction/core/visual_qa.py`
- Test: `construction/tests/test_c8_visual_qa.py`

**Interfaces:**
- Consumes: C2 BuildSpec/IR fingerprints; C7 `validate_structural_qa_report`; optional C5 output structure; canonical SVG bytes from Task 4.
- Produces: fail-closed input normalization, view descriptors, provenance hashes, and base report helpers used by metrics/review tasks.

- [ ] **Step 1: Run authority/evidence RED tests**

```bash
python3 -m unittest \
  construction.tests.test_c8_visual_qa.C8EvidenceAndReportTests.test_wrong_build_fingerprints_fail_closed \
  construction.tests.test_c8_visual_qa.C8EvidenceAndReportTests.test_matching_c7_is_provenance_only \
  construction.tests.test_c8_visual_qa.C8EvidenceAndReportTests.test_mismatched_c7_fails_closed \
  construction.tests.test_c8_visual_qa.C8EvidenceAndReportTests.test_matching_c5_is_provenance_and_labels_only \
  construction.tests.test_c8_visual_qa.C8EvidenceAndReportTests.test_mismatched_c5_fails_closed -v
```

Expected: FAIL from the Visual QA stub.

- [ ] **Step 2: Implement canonical JSON/hash helpers**

```python
def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _sha256_json(value: object) -> str:
    return hashlib.sha256(_canonical_json_bytes(value)).hexdigest()
```

File serialization of reports adds exactly one newline after the already-fingerprinted canonical JSON.

- [ ] **Step 3: Validate BuildSpec/Build IR linkage**

Require `build_spec` object with `schema_version == 1`; call `validate_build_ir`; require `build_ir["metadata"]["build_spec_sha256"] == build_spec_fingerprint(build_spec)`. Normalize any C2 exception into `VisualQAError` with deterministic messages.

- [ ] **Step 4: Validate optional C7 provenance**

When supplied:

```python
validate_structural_qa_report(structural_report)
assert structural_report["build_spec_sha256"] == build_spec_fingerprint(build_spec)
assert structural_report["build_ir_sha256"] == fingerprint_build_ir(build_ir)
structural_report_sha256 = _sha256_json(structural_report)
```

A C7 status is provenance only; do not inspect it to resolve visual checks.

- [ ] **Step 5: Validate optional C5 evidence without inventing a new C5 authority**

Require schema version `1`, exact `build_spec_sha256`, `roles` list, unique role names, and selected state objects containing canonical `block` plus `selected_state`. Canonicalize selected states through C2 `canonical_block_state_string`. Build `state_key -> sorted role names` only from exact selected states. Hash the exact supplied C5 object before normalization into `palette_resolution_sha256`.

- [ ] **Step 6: Validate canonical view bytes safely**

Use `xml.etree.ElementTree.fromstring` only for validation; reject malformed XML and any element local name outside `{svg,g,rect,polygon}`. Reject attributes whose lowercase local name starts with `on`, equals `href`, or contains URL-bearing `style`. Require root renderer/build fingerprints, numeric `width`/`height`, exact seven view ids from the mapping, and the SVG namespace. Recompute each view SHA-256/byte length and derive deterministic artifact names.

- [ ] **Step 7: Run the authority/evidence tests**

Run the exact Step 1 command. Expected: PASS.

- [ ] **Step 8: Commit input/provenance handling**

```bash
git add construction/core/visual_qa.py construction/tests/test_c8_visual_qa.py
git commit -m "feat(construction): validate C8 visual evidence authorities"
```

---

### Task 6: Implement all deterministic objective C8 metrics

**Files:**
- Modify: `construction/core/visual_qa.py`
- Test: `construction/tests/test_c8_visual_qa.py`

**Interfaces:**
- Consumes: valid C2 occupancy/palette and the exact orthographic projection rules from the renderer contract.
- Produces: exact integer/fraction `metrics` object with no aesthetic thresholds.

- [ ] **Step 1: Run all metric RED tests**

```bash
python3 -m unittest construction.tests.test_c8_visual_qa.C8MetricsTests -v
```

Expected: FAIL until metric helpers are implemented.

- [ ] **Step 2: Implement exact fraction normalization**

```python
def _fraction(numerator: int, denominator: int) -> dict[str, int]:
    if numerator == 0:
        return {"numerator": 0, "denominator": 1}
    divisor = math.gcd(abs(numerator), abs(denominator))
    return {"numerator": numerator // divisor, "denominator": denominator // divisor}
```

Callers must never pass denominator zero; represent empty aspect ratio as `{0,1}` explicitly.

- [ ] **Step 3: Implement occupancy metrics**

Compute occupied count, palette-state count, min/max per axis or nulls, extent dimensions or zeros, occupied bounding volume, density in occupied bounds, and density in full C2 bounds exactly as integer/fraction objects.

- [ ] **Step 4: Recompute orthographic visible grids and depth winners deterministically in C8 analysis**

Do not parse visual truth from SVG. Reuse the renderer contract mathematically in a focused internal helper so metrics remain tied to C2 rather than image parsing. Keep fixed full projected bounds and the same occlusion winner rules.

- [ ] **Step 5: Implement projection connected components and aspect ratios**

Use cardinal adjacency, lexicographically stable traversal, projected occupied bounding dimensions, component count, dominant size, and exact width/height ratio.

- [ ] **Step 6: Implement palette-distribution metrics**

For each C2 palette state in canonical palette order, emit canonical state string, occupied count, fraction of all occupied blocks, per-view visible count, and sorted C5 matching roles from Task 5.

- [ ] **Step 7: Implement repetition metrics on full projected grids**

Represent each cell signature as canonical state key or a fixed empty sentinel. Derive distinct row/column signature counts, repeated signature counts, longest adjacent identical runs, and exact repeated ratios. Do not turn any metric into PASS/FAIL.

- [ ] **Step 8: Implement facade-depth metrics**

For four facades only, derive distinct visible depth count, min/max/null, depth range, adjacent visible-pair count, transition count, and exact transition ratio.

- [ ] **Step 9: Implement layer-density metrics**

Emit one record for every `y` level including empty levels: occupied cells, `size_x * size_z`, exact density, canonical-order palette counts. Aggregate level count, min, max, and ordered middle pair from sorted occupied counts.

- [ ] **Step 10: Run metric tests**

```bash
python3 -m unittest construction.tests.test_c8_visual_qa.C8MetricsTests -v
```

Expected: PASS.

- [ ] **Step 11: Commit deterministic metrics**

```bash
git add construction/core/visual_qa.py construction/tests/test_c8_visual_qa.py
git commit -m "feat(construction): add deterministic C8 visual metrics"
```

---

### Task 7: Implement review evidence, visual checks, report fingerprinting, and executable report validation

**Files:**
- Modify: `construction/core/visual_qa.py`
- Modify only if contract mismatch is discovered: `construction/schemas/visual-qa-report.schema.json`
- Test: `construction/tests/test_c8_visual_qa.py`

**Interfaces:**
- Produces complete `run_visual_qa(...) -> dict` and `validate_visual_qa_report(report) -> None`.

- [ ] **Step 1: Run review/report RED tests**

```bash
python3 -m unittest construction.tests.test_c8_visual_qa.C8EvidenceAndReportTests -v
```

Expected: review-decision, fingerprint, and report-validator tests still FAIL.

- [ ] **Step 2: Define fixed check metadata in code**

```python
SUBJECTIVE_CHECKS = (
    "silhouette_readability",
    "proportion",
    "material_hierarchy",
    "repetition",
    "facade_readability",
    "interior_density",
)
CHECK_ORDER = (
    "canonical_preview_integrity",
    *SUBJECTIVE_CHECKS,
    "runtime_visual_fidelity",
)
```

Define each check's exact allowed evidence-view set from the spec. `canonical_preview_integrity` is required PASS after successful view validation. Six subjective checks are required and default DEFERRED. `runtime_visual_fidelity` is non-required, severity info, and always DEFERRED.

- [ ] **Step 3: Validate exact review evidence**

Require:

```json
{
  "schema_version": 1,
  "build_spec_sha256": "...",
  "build_ir_sha256": "...",
  "renderer_version": "c8-svg-v1",
  "views": [{"id": "front", "sha256": "..."}],
  "reviewer": {"kind": "human|agent", "id": "stable-nonempty-id"},
  "decisions": [{"check_id": "silhouette_readability", "status": "PASS|FAIL", "evidence_views": ["front"], "summary": "nonempty"}]
}
```

Require all seven view records exactly in canonical order and exact hashes. Reject unknown/missing/duplicate views, unknown/duplicate decisions, invalid evidence-view membership, stale build/view hashes, renderer mismatch, empty reviewer id/summary, or any `runtime_visual_fidelity` decision. Hash the exact supplied evidence object before decision-order normalization.

- [ ] **Step 4: Construct checks and overall status deterministically**

Normalize decision order to `SUBJECTIVE_CHECKS`. Omitted decision => required DEFERRED. FAIL dominates overall; otherwise any required DEFERRED => overall DEFERRED; otherwise PASS. Always append runtime visual fidelity DEFERRED.

- [ ] **Step 5: Construct and self-fingerprint the report**

Build fields in the approved semantic structure, then compute:

```python
payload = dict(report_without_content_sha256)
content_sha256 = hashlib.sha256(_canonical_json_bytes(payload)).hexdigest()
report["content_sha256"] = content_sha256
```

Never include timestamps/CI ids/paths/random data.

- [ ] **Step 6: Implement `validate_visual_qa_report` manually and fail closed**

Validate exact top-level keys, schema version, SHA formats, renderer version, exact view/check ids/order, allowed statuses/severities, integer canvas dimensions, evidence class, all metric object types/fractions, overall-status derivation, and recomputed content SHA. Raise `VisualQAError` with deterministic messages on any mismatch.

The JSON Schema remains a parallel machine-readable contract; executable validation must not import `jsonschema`.

- [ ] **Step 7: Run all evidence/report tests**

```bash
python3 -m unittest construction.tests.test_c8_visual_qa.C8EvidenceAndReportTests -v
```

Expected: PASS, including tamper detection and the invariant that C7/C5 provenance does not resolve subjective checks.

- [ ] **Step 8: Run the entire non-Golden C8 suite**

```bash
python3 -m unittest construction/tests/test_c8_visual_qa.py -v
```

At this stage every test except the not-yet-materialized Golden artifact comparison may PASS. If the Golden test is designed to require files, it must fail explicitly for missing `construction/fixtures/vanilla-golden/c8/` artifacts rather than skip.

- [ ] **Step 9: Commit complete C8 analysis/report behavior**

```bash
git add construction/core/visual_qa.py construction/schemas/visual-qa-report.schema.json construction/tests/test_c8_visual_qa.py
git commit -m "feat(construction): add evidence-gated C8 visual QA"
```

---

### Task 8: Materialize and review the Vanilla Golden C8 evidence

**Files:**
- Create: `construction/fixtures/vanilla-golden/c8/front.svg`
- Create: `construction/fixtures/vanilla-golden/c8/back.svg`
- Create: `construction/fixtures/vanilla-golden/c8/left.svg`
- Create: `construction/fixtures/vanilla-golden/c8/right.svg`
- Create: `construction/fixtures/vanilla-golden/c8/top.svg`
- Create: `construction/fixtures/vanilla-golden/c8/isometric.svg`
- Create: `construction/fixtures/vanilla-golden/c8/layers.svg`
- Create: `construction/fixtures/vanilla-golden/c8/review-evidence.json`
- Create: `construction/fixtures/vanilla-golden/c8/expected-visual-qa-report.json`
- Test: `construction/tests/test_c8_visual_qa.py`

**Interfaces:**
- Consumes: exact existing Vanilla Golden BuildSpec/Build IR and completed C8 renderer/QA APIs.
- Produces: checked-in deterministic offline preview evidence bound to the exact existing Golden.

- [ ] **Step 1: Generate seven canonical Golden views twice and prove identical hashes before writing fixtures**

Use a one-shot Python command from repository root:

```bash
python3 - <<'PY'
import hashlib, json
from pathlib import Path
from construction.qa.preview_renderer import render_canonical_views

root = Path("construction/fixtures/vanilla-golden")
build_ir = json.loads((root / "expected-build-ir.json").read_text(encoding="utf-8"))
a = render_canonical_views(build_ir)
b = render_canonical_views(build_ir)
assert a == b
for name in ("front", "back", "left", "right", "top", "isometric", "layers"):
    print(name, hashlib.sha256(a[name]).hexdigest(), len(a[name]))
PY
```

Expected: equality assertion passes and all seven stable hashes are printed.

- [ ] **Step 2: Write the seven SVG files from renderer output, not hand-authored copies**

```bash
python3 - <<'PY'
import json
from pathlib import Path
from construction.qa.preview_renderer import render_canonical_views

root = Path("construction/fixtures/vanilla-golden")
out = root / "c8"
out.mkdir(parents=True, exist_ok=True)
build_ir = json.loads((root / "expected-build-ir.json").read_text(encoding="utf-8"))
for view_id, data in render_canonical_views(build_ir).items():
    (out / f"{view_id}.svg").write_bytes(data)
PY
```

- [ ] **Step 3: Inspect the actual seven generated SVG artifacts before creating review decisions**

Inspect each named artifact as the rendered diagnostic preview, not metric JSON alone. The reviewer record for the Golden uses:

```json
{"kind":"agent","id":"factory-c8-golden-review-v1"}
```

Record PASS/FAIL only for what the canonical offline preview actually supports. The six decisions must reference only their allowed evidence views and must not mention runtime textures, lighting, CTM, shaders, Minecraft screenshots, or runtime fidelity. If any of the six checks cannot be honestly resolved from the generated canonical SVGs, do not fabricate a PASS: record the observed FAIL if there is a defect, or leave the decision omitted and update the expected Golden overall status to DEFERRED.

- [ ] **Step 4: Create `review-evidence.json` bound to exact view hashes**

Use canonical view order and exact SHA-256 values from generated files. Populate all six offline subjective decisions only when Step 3 actually supports them. Serialize with sorted keys, compact separators, `ensure_ascii=false`, and one final newline.

- [ ] **Step 5: Generate the expected report using production C8 code**

```bash
python3 - <<'PY'
import json
from pathlib import Path
from construction.core.visual_qa import run_visual_qa

root = Path("construction/fixtures/vanilla-golden")
c8 = root / "c8"
build_spec = json.loads((root / "build-spec.json").read_text(encoding="utf-8"))
build_ir = json.loads((root / "expected-build-ir.json").read_text(encoding="utf-8"))
view_ids = ("front", "back", "left", "right", "top", "isometric", "layers")
views = {name: (c8 / f"{name}.svg").read_bytes() for name in view_ids}
review = json.loads((c8 / "review-evidence.json").read_text(encoding="utf-8"))
report = run_visual_qa(build_spec, build_ir, views, review_evidence=review)
payload = json.dumps(report, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"
(c8 / "expected-visual-qa-report.json").write_text(payload, encoding="utf-8")
PY
```

- [ ] **Step 6: Run Golden and full C8 tests**

```bash
python3 -m unittest construction.tests.test_c8_visual_qa.C8GoldenTests -v
python3 -m unittest construction/tests/test_c8_visual_qa.py -v
```

Expected: Golden artifacts and expected report match production output byte-for-byte; `runtime_visual_fidelity` remains DEFERRED even when all six offline subjective decisions are present and PASS.

- [ ] **Step 7: Commit only deterministic Golden evidence**

```bash
git add construction/fixtures/vanilla-golden/c8 construction/tests/test_c8_visual_qa.py
git commit -m "test(construction): add C8 vanilla visual golden evidence"
```

---

### Task 9: Run the complete C8 GREEN matrix and repair only evidence-backed defects

**Files:**
- Modify only files proven defective by the C8 or inherited regression gates.

**Interfaces:**
- Produces: an exact branch head with C8 and inherited C7→C0 gates green before documentation claims are expanded.

- [ ] **Step 1: Run C8 locally where possible**

```bash
python3 -m unittest construction/tests/test_c8_visual_qa.py -v
python3 -m unittest construction/tests/test_c7_architecture_qa.py construction/tests/test_c7_registry_authority.py -v
python3 -m unittest construction/tests/test_c6_sponge_v3.py -v
python3 -m unittest construction/tests/test_c5_modded_palette.py -v
python3 -m unittest construction/tests/test_c4_modpack_registry.py construction/tests/test_c4_runtime_registry_probe.py -v
python3 -m unittest construction/tests/test_c3_vanilla_golden.py -v
python3 -m unittest construction/tests/test_c2_build_ir.py -v
python3 -m unittest construction/tests/test_c0_foundation.py -v
python3 construction/scripts/validate_c0.py
```

- [ ] **Step 2: Push the branch and require the C8 workflow GREEN on the exact SHA**

The workflow must prove:

```text
Engineering I2 PASS
C8 PASS with no SKIP
C7 PASS
C6 PASS
C5 PASS
C4 tests PASS
C4 materialization PASS
NeoForge 21.1.248 / Java 21 Gradle test build PASS
C3 PASS
C2 PASS
C0 + validate_c0 PASS
C8 whitespace PASS
```

- [ ] **Step 3: If a gate fails, classify before editing**

For every failure, identify whether it is:

```text
C8 implementation defect
C8 test defect
C8 workflow defect
inherited regression
concurrent main drift
external GitHub/runner issue
```

Only change repository content for the first four categories and rerun the exact failed gate plus the full C8 workflow before marking GREEN.

- [ ] **Step 4: Commit each real corrective change separately**

Use a specific message such as:

```bash
git commit -m "fix(construction): enforce C8 review evidence binding"
```

Do not squash evidence history during development.

---

### Task 10: Document implemented C8 scope without closing status early

**Files:**
- Modify: `construction/README.md`
- Modify: `construction/docs/ARCHITECTURE.md`
- Do not modify yet: `construction/STATUS.md`

**Interfaces:**
- Consumes: already-green executable C8 evidence from Task 9.
- Produces: documentation of implemented behavior while status remains at the prior formally closed phase until merge/post-merge proof.

- [ ] **Step 1: Add implemented C8 scope to `construction/README.md`**

Document only proven behavior: seven deterministic diagnostic SVGs, pseudo-color/non-Minecraft-render boundary, exact metrics, review-evidence gating, Golden evidence, and C12 runtime-fidelity boundary.

- [ ] **Step 2: Update `construction/docs/ARCHITECTURE.md` QA/determinism sections**

Replace future-C8 language with the implemented C8 contract. Keep C7 structural evidence separate and state that runtime visual fidelity remains C12.

- [ ] **Step 3: Run C8 and whitespace gates on the documentation head**

```bash
python3 -m unittest construction/tests/test_c8_visual_qa.py -v
git diff --check HEAD^ -- construction/README.md construction/docs/ARCHITECTURE.md
```

- [ ] **Step 4: Commit documentation only after the implementation head is green**

```bash
git add construction/README.md construction/docs/ARCHITECTURE.md
git commit -m "docs(construction): document implemented C8 visual QA"
```

- [ ] **Step 5: Re-run the full C8 GitHub Actions workflow on this new exact head**

Do not open the implementation PR until the documentation head also passes the complete Task 9 matrix.

---

### Task 11: Open the real C8 implementation PR and require exact-head repository gates

**Files:**
- No new implementation files unless a review/check exposes a real defect.

**Interfaces:**
- Produces: mergeable PR with exact-head evidence and no unresolved review blockers.

- [ ] **Step 1: Revalidate current `main` and all open PRs immediately before PR creation**

If `main` advanced, compare changed paths. Reconcile the C8 branch only when concurrent commits touch C8/shared authorities or when GitHub reports the branch behind in a way that repository policy requires. Never overwrite concurrent Art/Engineering work.

- [ ] **Step 2: Audit the branch diff against current main**

Expected implementation scope is limited to:

```text
.github/workflows/factory-construction-c8-visual-qa.yml
construction/core/visual_qa.py
construction/qa/preview_renderer.py
construction/schemas/visual-qa-report.schema.json
construction/tests/test_c8_visual_qa.py
construction/fixtures/vanilla-golden/c8/**
construction/README.md
construction/docs/ARCHITECTURE.md
docs/superpowers/specs/2026-09-11-construction-c8-visual-qa-design.md
docs/superpowers/plans/2026-09-11-construction-c8-visual-qa.md
```

`construction/STATUS.md` must not be in this implementation PR.

- [ ] **Step 3: Open a non-draft PR from `feat/construction-c8-visual-qa` to `main`**

Use title:

```text
feat(construction): add C8 visual QA
```

PR body must summarize RED1/RED2 exact run ids, final GREEN run id, C8 test count, inherited regression evidence, NeoForge probe result, Golden evidence boundary, and explicit non-goals.

- [ ] **Step 4: Require all PR-triggered Construction/repository gates**

At minimum validate C8, C7, C6, C5, C4, C3, C2, C1A, C1B, C0, Governance, and Sonar/CodeQL or other repository-global checks that actually trigger. Do not invent a gate that did not run; classify the actual check suite returned by GitHub.

- [ ] **Step 5: Audit reviews and inline threads**

Require no blocking review and no unresolved actionable inline thread. A bot quota/informational comment is not a technical blocker unless it contains an actual finding.

- [ ] **Step 6: Merge only with the exact reviewed head SHA**

Call merge with `expected_head_sha` set to the final PR head. If the head moves, repeat check/review validation before merging.

---

### Task 12: Validate merged C8 and perform a separate status-only closeout

**Files:**
- Modify after post-merge validation only: `construction/STATUS.md`

**Interfaces:**
- Produces: formally closed C8 phase and next frontier `BEGIN_C9_AGENT_MCP` only after merged-main evidence exists.

- [ ] **Step 1: Validate post-merge workflows on the exact merge SHA**

Require the merged `main` SHA to pass the same Construction matrix that is applicable on push: C8/C7/C6/C5/C4/C3/C2/C1A/C1B/C0/Governance plus any repository-global blocker that runs on main. Capture exact run ids and the C8 test/NeoForge evidence from logs.

- [ ] **Step 2: Revalidate `main` and open PRs before closeout**

Create a new branch named:

```text
docs/construction-c8-closeout-status
```

from the then-current exact `main` SHA. If another domain merged first, audit its delta before creating the branch.

- [ ] **Step 3: Update only `construction/STATUS.md`**

Preserve all C0-C7 history. Change the current phase/frontier to:

```text
PHASE=C8_COMPLETE_POSTMERGE_VALIDATED
NEXT_ACTION=BEGIN_C9_AGENT_MCP
```

Append a C8 section containing: design/spec/plan refs, RED1/RED2 evidence, implementation PR number/head/merge SHA, final PR-head gate evidence, merged-main post-merge run ids, exact C8 test count, Golden evidence boundary, and the fact that `runtime_visual_fidelity` remains C12-deferred.

- [ ] **Step 4: Prove the closeout diff is status-only**

```bash
git diff --check
git diff --name-only main...HEAD
```

Expected changed path exactly:

```text
construction/STATUS.md
```

- [ ] **Step 5: Open, validate, and merge the status-only closeout PR**

Require the actual Construction/Governance/Sonar gates triggered by the status-only PR. Merge with `expected_head_sha` only when all applicable gates are green and reviews/threads are clear.

- [ ] **Step 6: Validate the post-closeout main push**

Confirm `construction/STATUS.md` is published with `PHASE=C8_COMPLETE_POSTMERGE_VALIDATED` and `NEXT_ACTION=BEGIN_C9_AGENT_MCP`, then require the applicable post-closeout Construction matrix to succeed on that exact main SHA before declaring C8 formally complete.
