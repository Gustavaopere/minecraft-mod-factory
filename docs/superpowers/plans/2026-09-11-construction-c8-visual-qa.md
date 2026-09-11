# Construction C8 Visual QA Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement deterministic offline Construction preview rendering and evidence-gated Visual QA for C2-valid Build IR without claiming Minecraft runtime-render fidelity.

**Architecture:** Add a pure Factory-owned SVG diagnostic renderer under `construction/qa/` and a C8 orchestration/report layer under `construction/core/`. C8 reuses C2/C5/C7 authorities, computes deterministic exact metrics, accepts explicit hash-bound human/agent review evidence for six offline subjective checks, and keeps runtime visual fidelity deferred to C12.

**Tech Stack:** CPython 3.11 standard library (`hashlib`, `json`, `math`, `xml.etree.ElementTree`, `unittest`), existing Construction contracts, deterministic UTF-8 SVG, GitHub Actions on `ubuntu-24.04`, Java 21/Gradle only for inherited C4 NeoForge runtime-probe regression.

**Spec:** `docs/superpowers/specs/2026-09-11-construction-c8-visual-qa-design.md`

## Global Constraints

- Target remains Minecraft Java Edition `1.21.1`, NeoForge `21.1.248`, Java `21` where NeoForge runtime evidence is exercised.
- C2 `construction/core/build_ir.py` remains canonical voxel/geometry authority.
- C5 `construction/core/modded_palette.py` may provide optional semantic role labels but never real render fidelity.
- C7 `construction/core/structural_qa.py` remains structural QA authority; C7 status never resolves a C8 subjective check.
- Renderer version is exactly `c8-svg-v1`.
- Canonical view order is exactly `front`, `back`, `left`, `right`, `top`, `isometric`, `layers`.
- Canonical SVG uses deterministic integer geometry and diagnostic pseudo-colors only; no scripts, external resources, timestamps, random ids, system-font geometry, GPU state, or host paths.
- Six offline subjective checks remain `DEFERRED` without matching explicit `review_evidence`.
- `runtime_visual_fidelity` is always `DEFERRED` in C8 and cannot be resolved by C8 review evidence.
- C8 does not add a Minecraft model/texture renderer, client boot, resource-pack rendering, CTM/copycat/dynamic-renderer semantics, in-game capture, C9 MCP, C10 external providers, or C12 runtime acceptance.
- No dependency is added to `construction/upstream/harness/schematica-test-lock.txt`; C8 production code uses the Python standard library only.
- Reuse `construction/fixtures/vanilla-golden/`; do not create a duplicate Golden build.
- Do not promote `construction/STATUS.md` until implementation is merged and exact-main post-merge validation succeeds.

---

### Task 1: Freeze the C8 contract and capture RED1 with production modules absent

**Files:**
- Create: `construction/schemas/visual-qa-report.schema.json`
- Create: `construction/tests/test_c8_visual_qa.py`
- Create: `.github/workflows/factory-construction-c8-visual-qa.yml`

**Interfaces:**
- Consumes: C2 `validate_build_ir`, `build_spec_fingerprint`, `fingerprint_build_ir`, `canonical_block_state_string`, and `canonicalize_build_ir`.
- Produces: complete C8 executable test contract and CI gate before production modules exist.

- [ ] **Step 1: Write the complete report schema**

Create Draft 2020-12 schema with closed objects and reusable SHA/fraction definitions:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/Gustavaopere/minecraft-mod-factory/construction/schemas/visual-qa-report.schema.json",
  "title": "Construction C8 Visual QA Report",
  "type": "object",
  "additionalProperties": false,
  "$defs": {
    "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
    "fraction": {
      "type": "object",
      "additionalProperties": false,
      "required": ["numerator", "denominator"],
      "properties": {
        "numerator": {"type": "integer"},
        "denominator": {"type": "integer", "minimum": 1}
      }
    }
  },
  "required": [
    "schema_version", "build_spec_sha256", "build_ir_sha256",
    "structural_report_sha256", "palette_resolution_sha256",
    "review_evidence_sha256", "renderer_version", "views", "metrics",
    "checks", "overall_status", "content_sha256"
  ]
}
```

Complete `properties`, `views`, `metrics`, and `checks` from the approved spec. The executable validator remains Factory-owned; do not import `jsonschema`.

- [ ] **Step 2: Create the complete RED-first C8 test module**

Use:

```python
ROOT = Path(__file__).resolve().parents[2]
GOLDEN = ROOT / "construction" / "fixtures" / "vanilla-golden"
RENDERER_PATH = ROOT / "construction" / "qa" / "preview_renderer.py"
VISUAL_QA_PATH = ROOT / "construction" / "core" / "visual_qa.py"
IMPLEMENTATION_READY = RENDERER_PATH.is_file() and VISUAL_QA_PATH.is_file()

class C8ContractTests(unittest.TestCase):
    def test_production_modules_exist(self):
        self.assertTrue(RENDERER_PATH.is_file(), "C8 preview renderer is not implemented")
        self.assertTrue(VISUAL_QA_PATH.is_file(), "C8 visual QA engine is not implemented")
```

Keep contract/schema/workflow tests unguarded. Put behavioral classes under:

```python
@unittest.skipUnless(IMPLEMENTATION_READY, "C8 production modules not implemented yet")
```

Implement exact test methods covering all spec matrix items. Required renderer methods are:

```text
test_renderer_rejects_invalid_build_ir
test_fixed_view_ids_and_byte_determinism
test_svg_metadata_binds_renderer_and_ir
test_front_back_occlusion_and_orientation
test_left_right_occlusion
test_top_occlusion
test_orthographic_canvas_and_cell_placement
test_isometric_geometry_faces_order_and_canvas
test_layers_include_empty_levels_and_exact_layout
test_digest_pseudo_colors
test_svg_safety_contract
```

Required metric methods are:

```text
test_occupancy_metrics_empty_and_nonempty
test_projection_metrics_asymmetric_fixture
test_palette_distribution_metrics
test_c5_role_labels_match_selected_states_only
test_repetition_metrics_without_quality_threshold
test_facade_depth_metrics_flat_and_stepped
test_layer_density_includes_empty_levels
```

Required evidence/report methods are:

```text
test_missing_review_keeps_six_subjective_checks_deferred
test_valid_review_can_pass_one_subjective_check
test_valid_review_can_fail_one_subjective_check
test_partial_review_keeps_overall_deferred_without_fail
test_stale_view_hash_fails_closed
test_wrong_build_fingerprints_fail_closed
test_review_view_records_fail_closed
test_review_decisions_fail_closed
test_runtime_visual_fidelity_cannot_be_resolved
test_matching_c7_is_provenance_only
test_mismatched_c7_fails_closed
test_matching_c5_is_provenance_and_labels_only
test_mismatched_c5_fails_closed
test_report_content_sha_detects_tampering
test_report_validator_and_schema_contract
test_require_determinism_repeats_views_and_report_bytes
```

Required Golden method is `test_vanilla_golden_matches_checked_in_c8_artifacts`. Build every inline IR through `canonicalize_build_ir` so C2 fingerprints remain authoritative.

- [ ] **Step 3: Create the final C8 workflow before production code**

Workflow name: `Factory Construction C8 Visual QA`. Trigger on `main`, `feat/construction-c8-visual-qa`, and PRs to `main` for C8/shared Construction paths. Use exact pins:

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

Run in this exact order:

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

Finish with `git diff --check HEAD^ --` over C8 workflow, modules, schema, test, Golden C8 paths, spec, plan, README, ARCHITECTURE, and STATUS.

- [ ] **Step 4: Commit RED1**

```bash
git add .github/workflows/factory-construction-c8-visual-qa.yml construction/schemas/visual-qa-report.schema.json construction/tests/test_c8_visual_qa.py
git commit -m "test(construction): define C8 visual QA contract"
```

- [ ] **Step 5: Prove RED1 on the exact commit SHA**

Expected result: contract/schema/workflow tests PASS, `test_production_modules_exist` FAILS, behavioral tests SKIP because production modules are absent. Do not create production files before this Actions evidence exists.

---

### Task 2: Capture behavioral RED2 with minimal public-interface stubs

**Files:**
- Create: `construction/qa/preview_renderer.py`
- Create: `construction/core/visual_qa.py`

**Interfaces:**
- Produces approved public symbols while deliberately keeping behavior red.

- [ ] **Step 1: Add renderer stub**

```python
from __future__ import annotations

class PreviewRenderError(ValueError):
    pass

def render_canonical_views(build_ir: dict) -> dict[str, bytes]:
    raise PreviewRenderError("C8 preview renderer implementation is not available yet")
```

- [ ] **Step 2: Add Visual QA stub**

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

- [ ] **Step 3: Commit and prove RED2**

```bash
git add construction/qa/preview_renderer.py construction/core/visual_qa.py
git commit -m "test(construction): expose C8 behavioral RED"
```

Expected Actions result: behavioral tests execute without SKIP and fail only through the deliberate not-available exceptions; Engineering I2 remains PASS.

---

### Task 3: Implement deterministic orthographic rendering foundations

**Files:**
- Modify: `construction/qa/preview_renderer.py`
- Test: `construction/tests/test_c8_visual_qa.py`

**Interfaces:**
- Consumes C2 Build IR validation/fingerprinting/state canonicalization.
- Produces deterministic orthographic grids/SVGs and shared renderer constants.

- [ ] **Step 1: Run orthographic RED tests**

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

- [ ] **Step 2: Add exact renderer constants and input validation**

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

Call C2 `validate_build_ir`; raise `PreviewRenderError` on any error. Embed `fingerprint_build_ir(build_ir)` in every SVG.

- [ ] **Step 3: Implement exact diagnostic pseudo-colors**

```python
def _base_rgb(state_key: str) -> tuple[int, int, int]:
    digest = hashlib.sha256(state_key.encode("utf-8")).digest()
    return tuple(64 + value % 128 for value in digest[:3])
```

Use lowercase six-digit hex. Isometric negative-x uses `channel * 85 // 100`; negative-z uses `channel * 70 // 100`.

- [ ] **Step 4: Implement orthographic projection winner rules**

Use full projected C2 bounds and exactly:

```text
front: smallest z; u=x; v=y
back: largest z; u=size_x-1-x; v=y
left: smallest x; u=size_z-1-z; v=y
right: largest x; u=z; v=y
top: largest y; u=x; v=size_z-1-z
```

- [ ] **Step 5: Serialize deterministic orthographic SVG**

Construct root bytes from computed variables, not textual placeholders:

```python
root_open = (
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
    f'viewBox="0 0 {width} {height}" data-renderer-version="{RENDERER_VERSION}" '
    f'data-build-ir-sha256="{build_ir_sha256}">\n'
)
```

Emit visible rectangles in stable `(v, u)` order and close with `</svg>\n`.

- [ ] **Step 6: Run orthographic tests and commit**

Run Step 1 command; require PASS. Then:

```bash
git add construction/qa/preview_renderer.py construction/tests/test_c8_visual_qa.py
git commit -m "feat(construction): add deterministic C8 orthographic previews"
```

---

### Task 4: Complete isometric, layers, and SVG safety

**Files:**
- Modify: `construction/qa/preview_renderer.py`
- Test: `construction/tests/test_c8_visual_qa.py`

- [ ] **Step 1: Run remaining renderer RED tests**

```bash
python3 -m unittest \
  construction.tests.test_c8_visual_qa.C8RendererTests.test_isometric_geometry_faces_order_and_canvas \
  construction.tests.test_c8_visual_qa.C8RendererTests.test_layers_include_empty_levels_and_exact_layout \
  construction.tests.test_c8_visual_qa.C8RendererTests.test_digest_pseudo_colors \
  construction.tests.test_c8_visual_qa.C8RendererTests.test_svg_safety_contract -v
```

- [ ] **Step 2: Implement isometric geometry exactly**

Use `base_x=(x-z)*8`, `base_y=(x+z)*4-y*8`; emit only exposed `negative_z`, `negative_x`, `top` faces. Sort blocks by `(x+z, y, z, x)` and faces `negative_z`, `negative_x`, `top`. Compute occupancy-independent canvas from all three face polygons at all eight extreme bound coordinates and translate raw minimum to `(16,16)`.

- [ ] **Step 3: Implement layers contact sheet exactly**

```python
def _ceil_sqrt(value: int) -> int:
    root = math.isqrt(value)
    return root if root * root == value else root + 1

def _ceil_div(value: int, divisor: int) -> int:
    return (value + divisor - 1) // divisor
```

Render every level `0..size_y-1`, including empty levels, with the spec's 8-unit cells/gaps/padding and `data-y` metadata.

- [ ] **Step 4: Enforce renderer safe subset**

Renderer output contains only root `svg`, inert `g`, `rect`, and `polygon` elements plus inert `data-*` metadata. No `script`, `foreignObject`, `style`, event handlers, `href`, external URLs, timestamps, or filesystem paths.

- [ ] **Step 5: Run all renderer tests and commit**

```bash
python3 -m unittest construction.tests.test_c8_visual_qa.C8RendererTests -v
git add construction/qa/preview_renderer.py construction/tests/test_c8_visual_qa.py
git commit -m "feat(construction): complete C8 canonical SVG renderer"
```

---

### Task 5: Implement authority linkage and canonical-view validation

**Files:**
- Modify: `construction/core/visual_qa.py`
- Test: `construction/tests/test_c8_visual_qa.py`

- [ ] **Step 1: Run authority RED tests**

```bash
python3 -m unittest \
  construction.tests.test_c8_visual_qa.C8EvidenceAndReportTests.test_wrong_build_fingerprints_fail_closed \
  construction.tests.test_c8_visual_qa.C8EvidenceAndReportTests.test_matching_c7_is_provenance_only \
  construction.tests.test_c8_visual_qa.C8EvidenceAndReportTests.test_mismatched_c7_fails_closed \
  construction.tests.test_c8_visual_qa.C8EvidenceAndReportTests.test_matching_c5_is_provenance_and_labels_only \
  construction.tests.test_c8_visual_qa.C8EvidenceAndReportTests.test_mismatched_c5_fails_closed -v
```

- [ ] **Step 2: Add canonical JSON/hash helpers**

```python
def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

def _sha256_json(value: object) -> str:
    return hashlib.sha256(_canonical_json_bytes(value)).hexdigest()
```

- [ ] **Step 3: Validate BuildSpec/IR linkage and optional C7**

Require BuildSpec schema version 1, valid C2 IR, and exact BuildSpec fingerprint link. For supplied C7 call `validate_structural_qa_report`, require exact BuildSpec/IR fingerprints, and hash the exact supplied report. Never use C7 status to resolve visual checks.

- [ ] **Step 4: Validate optional C5 evidence**

Require C5 schema version 1, exact BuildSpec fingerprint, unique roles, selected canonical states, and exact selected-state-to-role mapping. Hash the supplied C5 object before normalization. Do not infer textures/material appearance.

- [ ] **Step 5: Validate canonical view bytes safely**

Parse with `xml.etree.ElementTree.fromstring`. Allow only local element names `svg`, `g`, `rect`, `polygon`. Reject event attributes, `href`, external namespaces/resources, malformed XML, wrong root fingerprints/version, missing/extra views, and non-integer canvas dimensions. Recompute SHA-256 and byte length for each view.

- [ ] **Step 6: Run authority tests and commit**

Run Step 1 command; require PASS. Then:

```bash
git add construction/core/visual_qa.py construction/tests/test_c8_visual_qa.py
git commit -m "feat(construction): validate C8 visual evidence authorities"
```

---

### Task 6: Implement deterministic exact objective metrics

**Files:**
- Modify: `construction/core/visual_qa.py`
- Test: `construction/tests/test_c8_visual_qa.py`

- [ ] **Step 1: Run metric RED tests**

```bash
python3 -m unittest construction.tests.test_c8_visual_qa.C8MetricsTests -v
```

- [ ] **Step 2: Implement exact fractions**

```python
def _fraction(numerator: int, denominator: int) -> dict[str, int]:
    if numerator == 0:
        return {"numerator": 0, "denominator": 1}
    divisor = math.gcd(abs(numerator), abs(denominator))
    return {"numerator": numerator // divisor, "denominator": denominator // divisor}
```

Callers never pass denominator zero; empty aspect ratio is `{0,1}`.

- [ ] **Step 3: Implement occupancy/projection metrics**

Compute occupied counts/extents/volumes/densities, visible-cell counts, projected occupied bounds, exact aspect ratios, cardinal connected components, and dominant projected component size.

- [ ] **Step 4: Implement palette/repetition metrics**

Emit C2 canonical palette-state counts/fractions/per-view visible counts and exact C5 matching role labels. Build row/column signatures across full projected bounds, with a fixed empty sentinel, and compute distinct/repeated counts plus longest adjacent identical runs and exact ratios.

- [ ] **Step 5: Implement facade-depth/layer-density metrics**

For four facades emit depth count/min/max/range/adjacent pair transitions and exact ratio. For every C2 y level, including empty levels, emit occupied cells, footprint area, exact density, canonical palette counts, plus aggregate min/max/ordered middle pair.

- [ ] **Step 6: Run metric tests and commit**

```bash
python3 -m unittest construction.tests.test_c8_visual_qa.C8MetricsTests -v
git add construction/core/visual_qa.py construction/tests/test_c8_visual_qa.py
git commit -m "feat(construction): add deterministic C8 visual metrics"
```

---

### Task 7: Implement review evidence, checks, report hashing, and report validation

**Files:**
- Modify: `construction/core/visual_qa.py`
- Modify only if tests prove schema mismatch: `construction/schemas/visual-qa-report.schema.json`
- Test: `construction/tests/test_c8_visual_qa.py`

- [ ] **Step 1: Run evidence/report RED tests**

```bash
python3 -m unittest construction.tests.test_c8_visual_qa.C8EvidenceAndReportTests -v
```

- [ ] **Step 2: Define fixed check order**

```python
SUBJECTIVE_CHECKS = (
    "silhouette_readability",
    "proportion",
    "material_hierarchy",
    "repetition",
    "facade_readability",
    "interior_density",
)
CHECK_ORDER = ("canonical_preview_integrity", *SUBJECTIVE_CHECKS, "runtime_visual_fidelity")
```

Use exact evidence-view sets from the spec. Preview integrity is required PASS after successful view validation. Six subjective checks are required DEFERRED by default. Runtime visual fidelity is non-required DEFERRED with info severity.

- [ ] **Step 3: Validate review evidence with real input variables**

Tests construct evidence from current authoritative values:

```python
review_evidence = {
    "schema_version": 1,
    "build_spec_sha256": build_spec_fingerprint(build_spec),
    "build_ir_sha256": fingerprint_build_ir(build_ir),
    "renderer_version": RENDERER_VERSION,
    "views": [
        {"id": view_id, "sha256": hashlib.sha256(views[view_id]).hexdigest()}
        for view_id in VIEW_IDS
    ],
    "reviewer": {"kind": "agent", "id": "c8-test-reviewer"},
    "decisions": [
        {
            "check_id": "silhouette_readability",
            "status": "PASS",
            "evidence_views": ["front", "isometric"],
            "summary": "Canonical preview silhouette is readable in the cited views."
        }
    ]
}
```

Require exact BuildSpec/IR/version/all seven hashes; reject missing, extra, duplicate, stale, or out-of-order view records; reject unknown/duplicate decisions; reject disallowed evidence views; reject runtime visual fidelity decisions. Hash the exact supplied evidence before decision-order normalization.

- [ ] **Step 4: Build deterministic checks/overall status/report fingerprint**

FAIL dominates; otherwise any required DEFERRED yields overall DEFERRED; otherwise PASS. Build report, omit `content_sha256`, hash canonical JSON, then add the hash. Never include timestamps, CI ids, random values, or paths.

- [ ] **Step 5: Implement executable report validator**

Validate exact top-level keys/types, SHA formats, renderer version, exact view/check order, statuses, severities, fractions, metric structures, overall-status derivation, and recomputed content SHA. Raise `VisualQAError` deterministically. Do not use `jsonschema`.

- [ ] **Step 6: Run evidence/report and full non-Golden tests, then commit**

```bash
python3 -m unittest construction.tests.test_c8_visual_qa.C8EvidenceAndReportTests -v
python3 -m unittest construction/tests/test_c8_visual_qa.py -v
```

At this point the Golden comparison must fail only because `construction/fixtures/vanilla-golden/c8/` is not materialized; it must not skip.

```bash
git add construction/core/visual_qa.py construction/schemas/visual-qa-report.schema.json construction/tests/test_c8_visual_qa.py
git commit -m "feat(construction): add evidence-gated C8 visual QA"
```

---

### Task 8: Materialize and review Vanilla Golden C8 evidence

**Files:**
- Create seven SVGs plus `review-evidence.json` and `expected-visual-qa-report.json` under `construction/fixtures/vanilla-golden/c8/`.
- Test: `construction/tests/test_c8_visual_qa.py`

- [ ] **Step 1: Prove renderer repeatability before fixture writes**

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
for view_id in ("front", "back", "left", "right", "top", "isometric", "layers"):
    print(view_id, hashlib.sha256(a[view_id]).hexdigest(), len(a[view_id]))
PY
```

- [ ] **Step 2: Materialize SVGs only from production renderer output**

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

- [ ] **Step 3: Inspect the actual generated SVG previews before review decisions**

Review all seven rendered diagnostic artifacts. Use reviewer `{"kind":"agent","id":"factory-c8-golden-review-v1"}`. Resolve only observations supported by the canonical previews. If a check cannot be honestly resolved, omit that decision and let it remain DEFERRED; never fabricate PASS. Do not claim Minecraft textures, lighting, CTM, shaders, or runtime fidelity.

- [ ] **Step 4: Write hash-bound review evidence**

Construct all seven view hashes from the actual generated bytes and serialize canonical JSON plus one final newline. Include six offline decisions only when Step 3 supports all six; otherwise include exactly the supported subset.

- [ ] **Step 5: Generate expected report through production code**

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
views = {view_id: (c8 / f"{view_id}.svg").read_bytes() for view_id in view_ids}
review = json.loads((c8 / "review-evidence.json").read_text(encoding="utf-8"))
report = run_visual_qa(build_spec, build_ir, views, review_evidence=review)
text = json.dumps(report, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"
(c8 / "expected-visual-qa-report.json").write_text(text, encoding="utf-8")
PY
```

- [ ] **Step 6: Run Golden/full C8 and commit**

```bash
python3 -m unittest construction.tests.test_c8_visual_qa.C8GoldenTests -v
python3 -m unittest construction/tests/test_c8_visual_qa.py -v
git add construction/fixtures/vanilla-golden/c8 construction/tests/test_c8_visual_qa.py
git commit -m "test(construction): add C8 vanilla visual golden evidence"
```

Expected: Golden artifacts/report match byte-for-byte and `runtime_visual_fidelity` is still DEFERRED.

---

### Task 9: Prove the complete C8 GREEN matrix

**Files:**
- Modify only files whose defect is proven by a failed gate.

- [ ] **Step 1: Run Python regressions**

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

- [ ] **Step 2: Require C8 Actions GREEN on exact branch head**

Require Engineering I2, C8 with zero SKIP, C7, C6, C5, C4 tests, C4 materialization, Java 21/NeoForge Gradle `test build`, C3, C2, C0 validator, and whitespace all PASS.

- [ ] **Step 3: Classify failures before editing**

Classify each failure as C8 implementation, C8 test, C8 workflow, inherited regression, concurrent main drift, or external runner/service issue. Edit repository content only for proven repository defects, then rerun the failed gate and full C8 workflow.

- [ ] **Step 4: Commit every real corrective change separately**

Use a specific message such as:

```bash
git commit -m "fix(construction): enforce C8 review evidence binding"
```

---

### Task 10: Document implemented C8 scope without closing status early

**Files:**
- Modify: `construction/README.md`
- Modify: `construction/docs/ARCHITECTURE.md`
- Keep unchanged: `construction/STATUS.md`

- [ ] **Step 1: Document only proven C8 behavior**

Add seven deterministic diagnostic SVGs, pseudo-color/non-Minecraft-render boundary, exact metrics, review-evidence gating, Vanilla Golden evidence, and explicit C12 runtime-fidelity boundary to README/ARCHITECTURE.

- [ ] **Step 2: Validate documentation head**

```bash
python3 -m unittest construction/tests/test_c8_visual_qa.py -v
git diff --check HEAD^ -- construction/README.md construction/docs/ARCHITECTURE.md
```

- [ ] **Step 3: Commit and rerun full C8 workflow**

```bash
git add construction/README.md construction/docs/ARCHITECTURE.md
git commit -m "docs(construction): document implemented C8 visual QA"
```

Do not open the implementation PR until this exact documentation head passes the complete Task 9 workflow.

---

### Task 11: Open and gate the real C8 implementation PR

**Files:**
- No new files unless a check/review proves a defect.

- [ ] **Step 1: Revalidate `main`, open PRs, and branch diff immediately before PR creation**

Expected C8 scope is limited to:

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

`construction/STATUS.md` must not be changed in the implementation PR. Audit and reconcile concurrent work without overwriting other domains.

- [ ] **Step 2: Open non-draft PR**

Use title `feat(construction): add C8 visual QA`. Body records RED1/RED2 run ids, final GREEN run id, exact C8 test count, inherited regression evidence, NeoForge probe result, Golden evidence boundary, and C12 non-goals.

- [ ] **Step 3: Require actual PR-head gates**

Validate C8, C7, C6, C5, C4, C3, C2, C1A, C1B, C0, Governance, Sonar/CodeQL and any other repository-global checks that actually trigger. Do not invent absent checks. Require no blocking review and no unresolved actionable review thread.

- [ ] **Step 4: Merge only with exact head SHA**

Use `expected_head_sha` equal to the fully validated PR head. If head changes, repeat gate/review validation before merge.

---

### Task 12: Validate merged C8 and perform separate status-only closeout

**Files:**
- Modify after post-merge proof only: `construction/STATUS.md`

- [ ] **Step 1: Validate implementation post-merge on exact main SHA**

Require applicable C8/C7/C6/C5/C4/C3/C2/C1A/C1B/C0/Governance and repository-global push gates on the merge SHA. Capture exact run ids, C8 test count, Golden evidence, and NeoForge build evidence.

- [ ] **Step 2: Create closeout branch from then-current main**

Use branch `docs/construction-c8-closeout-status`. If main advanced, audit the delta first.

- [ ] **Step 3: Update only `construction/STATUS.md`**

Preserve all C0-C7 history and set:

```text
PHASE=C8_COMPLETE_POSTMERGE_VALIDATED
NEXT_ACTION=BEGIN_C9_AGENT_MCP
```

Append C8 design/spec/plan refs, RED1/RED2 evidence, implementation PR/head/merge SHA, final PR-head gates, post-merge run ids, exact C8 test count, Golden evidence boundary, and permanent C12 deferral of runtime visual fidelity.

- [ ] **Step 4: Prove status-only diff**

```bash
git diff --check
git diff --name-only main...HEAD
```

Expected changed path is exactly `construction/STATUS.md`.

- [ ] **Step 5: Open, gate, and merge closeout PR with exact head**

Require actual Construction/Governance/Sonar gates triggered by the status-only PR and clear reviews/threads. Merge only with `expected_head_sha`.

- [ ] **Step 6: Validate post-closeout main**

Confirm published `PHASE=C8_COMPLETE_POSTMERGE_VALIDATED` and `NEXT_ACTION=BEGIN_C9_AGENT_MCP`, then require applicable post-closeout Construction gates to succeed on that exact main SHA before declaring C8 complete.
