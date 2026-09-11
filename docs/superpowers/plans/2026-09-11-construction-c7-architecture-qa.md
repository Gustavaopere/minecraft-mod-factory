# Construction C7 Architecture QA Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement deterministic, conservative offline Architecture QA for Construction C7 without claiming visual or runtime properties that current authorities cannot prove.

**Architecture:** Add a focused `structural_qa.py` engine that consumes existing BuildSpec, C2 Canonical Build IR, and optional C4 registry evidence. The engine emits a versioned deterministic report with explicit `PASS`, `FAIL`, `DEFERRED`, and `NOT_APPLICABLE` check states and an overall `PASS`, `FAIL`, or `DEFERRED` result. Existing C2/C4/C5/C6 authorities remain authoritative; C7 does not create a second voxel or palette model.

**Tech Stack:** Python 3.11 standard library, `unittest`, JSON/JSON-Schema documents already used by Construction, GitHub Actions on `ubuntu-24.04`, Java 21 for inherited C4 runtime-probe regression.

**Spec:** `docs/superpowers/specs/2026-09-11-construction-c7-architecture-qa-design.md`

## Global Constraints

- Target remains Minecraft `1.21.1`, NeoForge `21.1.248`, Java `21`.
- `construction/core/build_ir.py` remains the only canonical voxel/placement authority.
- C4 registry `content_sha256` remains runtime block/state evidence authority when supplied.
- C5 palette authority is not duplicated.
- C6 Sponge v3 export/validation remains downstream and is not part of C7 correctness.
- C8 visual QA and C12 runtime acceptance claims are explicitly out of scope.
- C7 must fail closed on malformed/tampered authoritative inputs.
- C7 output must be deterministic and contain no timestamps, random ids, machine paths, or environment-dependent ordering.
- `enclosure`, semantic floor continuity, and provider-aware support remain explicit `DEFERRED` checks until sufficient authority exists.
- Documentation and `construction/STATUS.md` are updated only after implementation gates are green.

---

### Task 1: Establish the C7 contract RED

**Files:**
- Create: `construction/schemas/structural-qa-report.schema.json`
- Create: `construction/tests/test_c7_architecture_qa.py`
- Create: `.github/workflows/factory-construction-c7-architecture-qa.yml`

**Interfaces:**
- Consumes: `construction/core/build_ir.py`, BuildSpec v1, C4 registry v1.
- Produces expected public API: `StructuralQAError`, `run_structural_qa(build_spec, build_ir, registry=None)`, `validate_structural_qa_report(report)`.

- [ ] **Step 1: Write the report schema**

Define schema version `1` with exact top-level fields:

```json
{
  "schema_version": 1,
  "build_spec_sha256": "<64 lowercase hex>",
  "build_ir_sha256": "<64 lowercase hex>",
  "registry_fingerprint": null,
  "overall_status": "PASS|FAIL|DEFERRED",
  "checks": [],
  "metrics": {}
}
```

Each check object must require `id`, `status`, `severity`, `summary`, and `findings`; `status` is one of `PASS`, `FAIL`, `DEFERRED`, `NOT_APPLICABLE`; `severity` is `error`, `warning`, or `info`. `additionalProperties` is false at every stable contract object boundary.

- [ ] **Step 2: Write the module-existence RED**

In `test_c7_architecture_qa.py`, mirror the C6 loading pattern:

```python
MODULE_PATH = CONSTRUCTION / "core" / "structural_qa.py"
IMPLEMENTATION_READY = MODULE_PATH.is_file()

class ConstructionC7ArchitectureQATest(unittest.TestCase):
    def test_required_c7_production_file_exists(self) -> None:
        self.assertTrue(
            MODULE_PATH.is_file(),
            "C7 production module is required at construction/core/structural_qa.py",
        )
```

All behavioral tests that require the module must use `@unittest.skipUnless(IMPLEMENTATION_READY, ...)` so RED1 proves only the missing production file and workflow/schema contract can still be checked.

- [ ] **Step 3: Add contract tests for the workflow and schema**

Assert the C7 workflow contains pinned checkout/setup actions, Python 3.11, Java 21, hashed lock installation, Engineering I2 regressions, C4 runtime-probe materialization/build, C7→C0 test commands, `validate_c0.py`, and scoped `git diff --check`.

- [ ] **Step 4: Run RED1**

Run:

```bash
python3 -m unittest construction/tests/test_c7_architecture_qa.py -v
```

Expected: exactly the production-file existence assertion fails; behavioral tests are skipped; schema/workflow contract tests pass.

- [ ] **Step 5: Commit RED1**

```bash
git add construction/schemas/structural-qa-report.schema.json construction/tests/test_c7_architecture_qa.py .github/workflows/factory-construction-c7-architecture-qa.yml
git commit -m "test(construction): define C7 architecture QA contract"
```

---

### Task 2: Implement authoritative input validation and deterministic report primitives

**Files:**
- Create: `construction/core/structural_qa.py`
- Modify: `construction/tests/test_c7_architecture_qa.py`

**Interfaces:**
- Consumes: `build_ir.validate_build_ir`, `build_ir.build_spec_fingerprint`, `build_ir.fingerprint_build_ir`.
- Produces: `StructuralQAError`, canonical JSON hashing helpers, strict C7 BuildSpec consumption validation, C4 registry fingerprint validation, report validator.

- [ ] **Step 1: Add failing tests for malformed/tampered inputs**

Cover:

```python
with self.assertRaises(module.StructuralQAError):
    module.run_structural_qa(invalid_build_spec, valid_ir)

with self.assertRaises(module.StructuralQAError):
    module.run_structural_qa(valid_spec, tampered_ir)

with self.assertRaises(module.StructuralQAError):
    module.run_structural_qa(valid_spec, valid_ir, malformed_registry)
```

Also assert the BuildSpec fingerprint must equal `build_ir["metadata"]["build_spec_sha256"]`.

- [ ] **Step 2: Run targeted tests and confirm RED**

```bash
python3 -m unittest construction.tests.test_c7_architecture_qa.ConstructionC7ArchitectureQATest.test_invalid_authoritative_inputs_fail_closed -v
```

Expected: FAIL because production behavior is not implemented.

- [ ] **Step 3: Implement minimal fail-closed validation**

`structural_qa.py` must load sibling `build_ir.py` using the same repository-local import pattern used by C5/C6 and convert C2 validation failures into `StructuralQAError`.

Validate every BuildSpec field C7 consumes and the closed top-level/subobject shapes from the current BuildSpec v1 contract, including `qa.require_walkability`, `qa.require_complete_interior`, and `qa.require_determinism` boolean types when present. Reject unsupported keys instead of ignoring them.

For registry evidence:

```python
payload = copy.deepcopy(registry)
claimed = payload.pop("content_sha256")
expected = hashlib.sha256(canonical_json_bytes(payload)).hexdigest()
if claimed != expected:
    raise StructuralQAError("registry content_sha256 does not match canonical content")
```

Validate the consumed C4 fields: schema version, block ids, `available`, `authority`, state property maps, and unique block ids.

- [ ] **Step 4: Implement report validator**

`validate_structural_qa_report(report) -> list[str]` must return deterministic errors for contract violations and `[]` for canonical reports. It must verify fixed check ids/order and consistency between check statuses and `overall_status`.

- [ ] **Step 5: Run targeted tests to GREEN**

```bash
python3 -m unittest construction/tests/test_c7_architecture_qa.py -v
```

Expected: input/report validation tests pass; later structural tests may still fail only for not-yet-implemented checks.

- [ ] **Step 6: Commit validation primitives**

```bash
git add construction/core/structural_qa.py construction/tests/test_c7_architecture_qa.py
git commit -m "feat(construction): add C7 QA input validation"
```

---

### Task 3: Implement state validity and conservative occupancy metrics

**Files:**
- Modify: `construction/core/structural_qa.py`
- Modify: `construction/tests/test_c7_architecture_qa.py`

**Interfaces:**
- Consumes: validated Build IR palette/blocks and optional validated C4 registry.
- Produces checks: `bounds`, `runtime_state_validity`, occupancy metrics, `head_clearance` metrics.

- [ ] **Step 1: Add failing registry-state tests**

Create one runtime-confirmed matching registry fixture and negative variants:

```python
self.assertEqual(check(report, "runtime_state_validity")["status"], "PASS")
self.assertEqual(check(no_registry_report, "runtime_state_validity")["status"], "DEFERRED")
self.assertEqual(check(mismatch_report, "runtime_state_validity")["status"], "FAIL")
```

Negative cases must distinguish missing block id, `available=false`, `static_only_unconfirmed`, and exact property-map mismatch.

- [ ] **Step 2: Add failing head-clearance metric tests**

Use a small Build IR with a solid floor and controlled roof blocks. Assert deterministic counts for candidate support cells, clear two-block columns, and blocked candidate columns. Do not assert semantic interior correctness.

- [ ] **Step 3: Run targeted RED**

```bash
python3 -m unittest construction/tests/test_c7_architecture_qa.py -v
```

Expected: new state/head-clearance assertions fail for missing behavior.

- [ ] **Step 4: Implement runtime state validity**

Resolve each distinct C2 palette state to a C4 block by exact id and exact property dictionary. Never infer validity from namespace, static discovery, or C5 alternatives.

- [ ] **Step 5: Implement conservative occupancy/head-clearance metrics**

Treat only coordinates absent from sparse C2 blocks as air. C2 forbids explicit air placements; do not add a second air-state interpretation. A geometric candidate is a free cell with an occupied cell directly below and an in-bounds free cell above.

- [ ] **Step 6: Run tests to GREEN and commit**

```bash
python3 -m unittest construction/tests/test_c7_architecture_qa.py -v
git add construction/core/structural_qa.py construction/tests/test_c7_architecture_qa.py
git commit -m "feat(construction): validate C7 states and clearance"
```

---

### Task 4: Implement conservative walkability graph and evidence semantics

**Files:**
- Modify: `construction/core/structural_qa.py`
- Modify: `construction/tests/test_c7_architecture_qa.py`

**Interfaces:**
- Produces checks: `walkable_surface_graph`, `circulation_components`, `vertical_step_connectivity`, plus explicit deferred checks `enclosure`, `floor_continuity_semantic`, `unsupported_placement`.

- [ ] **Step 1: Add failing graph tests**

Cover:

```python
# single connected level
self.assertEqual(metrics["walkable_component_count"], 1)

# disconnected geometry
self.assertGreater(metrics["walkable_component_count"], 1)

# one-block step
self.assertGreater(metrics["vertical_step_edge_count"], 0)

# multi-level with no conservative step
self.assertEqual(metrics["vertical_step_edge_count"], 0)
```

- [ ] **Step 2: Add failing evidence-policy tests**

Required semantics:

```python
# no authoritative mapping from walkable graph to intended circulation
self.assertEqual(check(report, "circulation_components")["status"], "DEFERRED")

# complete interior requested but not semantically provable
self.assertEqual(check(report, "enclosure")["status"], "DEFERRED")
self.assertEqual(report["overall_status"], "DEFERRED")
```

A pure measurable graph may be `PASS` as an analysis primitive while semantic circulation remains `DEFERRED` when no intent mapping can prove which surface is intended circulation.

- [ ] **Step 3: Implement graph construction**

Nodes are clear candidate foot cells. Same-level cardinal neighbors create horizontal edges. Cardinal neighbors one `y` apart create vertical-step edges only when both endpoints independently satisfy the conservative clearance rule. Traverse components from the lexicographically smallest `(y, z, x)` node with fixed neighbor order.

- [ ] **Step 4: Implement explicit deferred checks**

Always emit `enclosure`, `floor_continuity_semantic`, and `unsupported_placement`. Never silently omit or promote them to PASS. Mark a deferred check as required when its existing BuildSpec flag makes it mandatory; required `DEFERRED` propagates to `overall_status=DEFERRED` unless any check is `FAIL`.

- [ ] **Step 5: Implement overall-status precedence**

Use exact precedence:

```text
any FAIL -> FAIL
else any required DEFERRED -> DEFERRED
else PASS
```

`NOT_APPLICABLE` never fails the report.

- [ ] **Step 6: Run C7 suite to GREEN and commit**

```bash
python3 -m unittest construction/tests/test_c7_architecture_qa.py -v
git add construction/core/structural_qa.py construction/tests/test_c7_architecture_qa.py
git commit -m "feat(construction): add C7 conservative walkability graph"
```

---

### Task 5: Prove determinism, schema validity, and vanilla-golden compatibility

**Files:**
- Modify: `construction/tests/test_c7_architecture_qa.py`
- Modify only if required by failing evidence: `construction/core/structural_qa.py`

**Interfaces:**
- Consumes: `construction/fixtures/vanilla-golden/build-spec.json` and `expected-build-ir.json`.
- Produces: deterministic canonical report evidence.

- [ ] **Step 1: Add deterministic repeated-run test**

```python
first = module.run_structural_qa(spec, ir, registry)
second = module.run_structural_qa(copy.deepcopy(spec), copy.deepcopy(ir), copy.deepcopy(registry))
self.assertEqual(first, second)
self.assertEqual(canonical_json(first), canonical_json(second))
```

- [ ] **Step 2: Add vanilla-golden test**

Load the existing C3 golden without modifying it. Assert C7 can analyze it, its C2 fingerprints remain unchanged, visual quality is not claimed, and checks that lack semantic authority remain explicit.

- [ ] **Step 3: Add report mutation rejection tests**

Mutate check order, status enum, SHA shape, and overall-status consistency and assert `validate_structural_qa_report` returns errors.

- [ ] **Step 4: Run C7 and C3/C2 regressions**

```bash
python3 -m unittest construction/tests/test_c7_architecture_qa.py -v
python3 -m unittest construction/tests/test_c3_vanilla_golden.py -v
python3 -m unittest construction/tests/test_c2_build_ir.py -v
```

Expected: all PASS.

- [ ] **Step 5: Commit deterministic/golden evidence**

```bash
git add construction/core/structural_qa.py construction/tests/test_c7_architecture_qa.py
git commit -m "test(construction): prove C7 determinism and golden compatibility"
```

---

### Task 6: Validate the dedicated C7 workflow and inherited regressions

**Files:**
- Modify if contract evidence requires correction: `.github/workflows/factory-construction-c7-architecture-qa.yml`
- Test: all Construction suites listed below.

**Interfaces:**
- Produces: exact-HEAD CI evidence for C7 and prior phases.

- [ ] **Step 1: Run local/connector-visible test matrix where executable**

```bash
python3 -m unittest construction/tests/test_c7_architecture_qa.py -v
python3 -m unittest construction/tests/test_c6_sponge_v3.py -v
python3 -m unittest construction/tests/test_c5_modded_palette.py -v
python3 -m unittest construction/tests/test_c4_modpack_registry.py construction/tests/test_c4_runtime_registry_probe.py -v
python3 -m unittest construction/tests/test_c3_vanilla_golden.py -v
python3 -m unittest construction/tests/test_c2_build_ir.py -v
python3 -m unittest construction/tests/test_c0_foundation.py -v
python3 construction/scripts/validate_c0.py
```

- [ ] **Step 2: Ensure workflow performs the exact C4 runtime probe path**

It must run:

```bash
python3 construction/scripts/prepare_neoforge_registry_probe.py --output .factory-ci/c7/runtime-probe
chmod +x .factory-ci/c7/runtime-probe/gradlew
cd .factory-ci/c7/runtime-probe
GRADLE_USER_HOME="$GITHUB_WORKSPACE/.factory-ci/c7/gradle-home" ./gradlew test build --no-daemon
```

- [ ] **Step 3: Run whitespace validation**

```bash
git diff --check <base>..HEAD -- .github/workflows/factory-construction-c7-architecture-qa.yml construction docs/superpowers/specs/2026-09-11-construction-c7-architecture-qa-design.md docs/superpowers/plans/2026-09-11-construction-c7-architecture-qa.md
```

- [ ] **Step 4: Commit workflow corrections only if needed**

```bash
git add .github/workflows/factory-construction-c7-architecture-qa.yml
git commit -m "ci(construction): gate C7 architecture QA"
```

---

### Task 7: Document verified C7 implementation and open the real PR

**Files:**
- Modify: `construction/README.md`
- Modify: `construction/docs/ARCHITECTURE.md`
- Modify: `construction/STATUS.md`

**Interfaces:**
- Consumes: exact successful C7 workflow run ids and exact branch HEAD.
- Produces: repository status/evidence only after gates exist.

- [ ] **Step 1: Update README/architecture boundaries**

Document what C7 proves and explicitly preserve C8 Visual QA and C12 Runtime Acceptance as later phases. Do not claim enclosure/provider-support semantics as complete while they are `DEFERRED`.

- [ ] **Step 2: Update STATUS with exact evidence**

Record branch/head, RED evidence, GREEN workflow id, inherited regression results, and `NEXT_ACTION=BEGIN_C8_VISUAL_QA` only after all required C7 gates are green.

- [ ] **Step 3: Re-run C7 workflow-sensitive tests after docs changes**

```bash
python3 -m unittest construction/tests/test_c7_architecture_qa.py -v
python3 -m unittest construction/tests/test_c0_foundation.py -v
python3 construction/scripts/validate_c0.py
```

- [ ] **Step 4: Commit verified documentation**

```bash
git add construction/README.md construction/docs/ARCHITECTURE.md construction/STATUS.md
git commit -m "docs(construction): record C7 architecture QA evidence"
```

- [ ] **Step 5: Revalidate `main`, open PR, and require exact-head checks**

Before opening the real PR, audit `main`, open PRs, and any concurrent changes. Open the C7 PR only when implementation evidence is already present. Do not merge until dedicated C7, inherited Construction workflows, Governance, and applicable Sonar checks are green on the exact PR head.
