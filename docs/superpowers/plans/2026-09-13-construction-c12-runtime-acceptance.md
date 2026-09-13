# Construction C12 Runtime Acceptance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a fail-closed C12 runtime-acceptance preflight that reuses Engineering I5, packages deterministic evidence, and cannot claim physical acceptance while the final Construction blocker exists.

**Architecture:** Add a focused C12 domain module under `construction/runtime/`, a JSON report schema, and filesystem-safe evidence helpers. Reuse the existing I5 manifest as baseline evidence; do not fork I5. Split CI into green preflight and intentionally blocked final acceptance, and keep `construction/STATUS.md` unchanged.

**Tech Stack:** Python 3.11, JSON, SHA-256, unittest, GitHub Actions, existing Engineering I5 harness, existing Construction authorities C2/C4/C6/C7/C8/C11.

**Spec:** `docs/superpowers/specs/2026-09-13-construction-c12-runtime-acceptance-design.md`

## Global Constraints

- Target is exactly Minecraft `1.21.1`, NeoForge `21.1.248`, Java `21`.
- Exact final blocker is `SUPER_HYPER_URGENT_FINAL_CONSTRUCTION_PHYSICAL_ACCEPTANCE`.
- C12 is an orchestrator over Engineering I5; it must not duplicate or replace I5.
- `PREFLIGHT` can become green but can never produce final acceptance `PASS`.
- Physical-only stages use controlled `DEFERRED`/`BLOCKED` states until real evidence exists.
- C8 offline Visual QA cannot substitute for live runtime visual fidelity.
- Dedicated-server PASS cannot substitute for multiplayer PASS.
- Standalone PASS cannot substitute for full-modpack PASS.
- C11 not accepted means C12 cannot accept.
- Evidence paths must remain inside an approved workspace and reject traversal/symlink escape.
- `construction/STATUS.md` must not change during this plan.
- Final acceptance order remains `C11 -> C12 -> C13 -> Construction`.

---

### Task 1: Establish the stacked C12 branch and RED contract tests

**Files:**
- Create branch: `feat/construction-c12-runtime-acceptance-preflight`
- Create: `construction/tests/test_c12_runtime_acceptance.py`
- Create: `construction/tests/test_c12_runtime_acceptance_security.py`

**Interfaces:**
- Consumes: final blocker state from `construction/fixtures/complex-modded-golden/capture-state.json` and Engineering I5 target/manifest conventions.
- Produces: expected public API names `C12Error`, `build_runtime_acceptance_report`, `validate_runtime_acceptance_report`, `validate_i5_manifest`, `package_evidence`.

- [ ] **Step 1: Create the C12 branch from the exact current C11 preflight head**

Run:
```bash
git switch feat/construction-c11-complex-modded-golden
git pull --ff-only
git switch -c feat/construction-c12-runtime-acceptance-preflight
```

Expected: new branch starts from the C11 head containing both approved C12/C13 specs and the final blocker implementation.

- [ ] **Step 2: Write RED tests for exact target, stage model and blocker propagation**

Create `construction/tests/test_c12_runtime_acceptance.py` with tests equivalent to:

```python
from construction.runtime.c12_runtime_acceptance import (
    C12Error,
    build_runtime_acceptance_report,
    validate_i5_manifest,
    validate_runtime_acceptance_report,
)

TARGET = {"minecraft": "1.21.1", "loader": "neoforge", "neoforge": "21.1.248", "java": 21}
BLOCKER = "SUPER_HYPER_URGENT_FINAL_CONSTRUCTION_PHYSICAL_ACCEPTANCE"


def test_preflight_can_be_ready_but_never_accepted():
    report = build_runtime_acceptance_report(
        mode="PREFLIGHT",
        target=TARGET,
        blocker={"status": BLOCKER, "blocks_c12_acceptance": True},
        authority_fingerprints={
            "i2_physical_snapshot_sha256": None,
            "c4_registry_sha256": None,
            "c11_manifest_sha256": None,
            "c6_schematic_sha256": None,
            "c7_report_sha256": None,
            "c8_report_sha256": None,
        },
        stages={
            "target_environment": "PASS",
            "i5_baseline": "PASS",
            "client_smoke": "DEFERRED",
            "live_placement": "DEFERRED",
            "runtime_visual_fidelity": "DEFERRED",
            "multiplayer": "DEFERRED",
            "full_modpack": "DEFERRED",
            "evidence_packaging": "PASS",
        },
    )
    assert report["overall_readiness"] == "PREFLIGHT_READY"
    assert report["overall_acceptance"] == "BLOCKED"
    assert report["blocker"] == BLOCKER


def test_physical_acceptance_rejects_target_drift():
    bad = dict(TARGET, neoforge="21.1.247")
    try:
        build_runtime_acceptance_report(
            mode="PHYSICAL_ACCEPTANCE",
            target=bad,
            blocker={"status": None, "blocks_c12_acceptance": False},
            authority_fingerprints={},
            stages={},
        )
    except C12Error as exc:
        assert "target drift" in str(exc)
    else:
        raise AssertionError("target drift must fail closed")
```

Add tests for exact stage IDs, C11-not-accepted, C8-not-runtime, dedicated-server-not-multiplayer, and standalone-not-full-modpack.

- [ ] **Step 3: Write RED security tests**

Create `construction/tests/test_c12_runtime_acceptance_security.py` covering:

```python
from pathlib import Path
import pytest
from construction.runtime.c12_evidence import C12EvidenceError, package_evidence


def test_package_evidence_rejects_parent_escape(tmp_path: Path):
    outside = tmp_path.parent / "outside.log"
    outside.write_text("x", encoding="utf-8")
    with pytest.raises(C12EvidenceError):
        package_evidence(tmp_path, [outside])


def test_package_evidence_rejects_symlink(tmp_path: Path):
    real = tmp_path / "real.log"
    real.write_text("x", encoding="utf-8")
    link = tmp_path / "link.log"
    link.symlink_to(real)
    with pytest.raises(C12EvidenceError):
        package_evidence(tmp_path, [link])
```

If the repository standard library runner is used instead of pytest, express the same assertions with `unittest` and `tempfile`; do not add a new dependency solely for these tests.

- [ ] **Step 4: Run RED tests**

Run:
```bash
python3 -m unittest construction/tests/test_c12_runtime_acceptance.py -v
python3 -m unittest construction/tests/test_c12_runtime_acceptance_security.py -v
```

Expected: FAIL because `construction.runtime.c12_runtime_acceptance` and `construction.runtime.c12_evidence` do not yet exist.

- [ ] **Step 5: Commit RED tests**

```bash
git add construction/tests/test_c12_runtime_acceptance.py construction/tests/test_c12_runtime_acceptance_security.py
git commit -m "test(construction): define C12 runtime acceptance contracts"
```

---

### Task 2: Implement the C12 report schema and fail-closed aggregation core

**Files:**
- Create: `construction/schemas/runtime-acceptance-report.schema.json`
- Create: `construction/runtime/c12_runtime_acceptance.py`
- Modify: `construction/tests/test_c12_runtime_acceptance.py`

**Interfaces:**
- Consumes: target dict, blocker dict, six authority fingerprint slots, fixed stage-state mapping.
- Produces:
  - `C12Error(RuntimeError)`
  - `build_runtime_acceptance_report(...) -> dict[str, object]`
  - `validate_runtime_acceptance_report(report: object) -> list[str]`
  - `validate_i5_manifest(manifest: object) -> list[str]`

- [ ] **Step 1: Add the JSON schema**

Define exact enums:

```json
{
  "mode": ["PREFLIGHT", "PHYSICAL_ACCEPTANCE"],
  "stage_state": ["PASS", "FAIL", "BLOCKED", "DEFERRED", "NOT_APPLICABLE"],
  "overall_readiness": ["PREFLIGHT_READY", "BLOCKED"],
  "overall_acceptance": ["PASS", "FAIL", "BLOCKED"]
}
```

Require exact target keys, fixed authority-fingerprint keys, fixed stage IDs, blocker, diagnostics and deterministic evidence arrays. SHA fields are either lowercase 64-hex or `null` where preflight permits missing physical evidence.

- [ ] **Step 2: Implement constants and type guards**

In `construction/runtime/c12_runtime_acceptance.py` implement:

```python
TARGET = {"minecraft": "1.21.1", "loader": "neoforge", "neoforge": "21.1.248", "java": 21}
FINAL_BLOCKER = "SUPER_HYPER_URGENT_FINAL_CONSTRUCTION_PHYSICAL_ACCEPTANCE"
STAGE_IDS = (
    "target_environment",
    "i5_baseline",
    "client_smoke",
    "live_placement",
    "runtime_visual_fidelity",
    "multiplayer",
    "full_modpack",
    "evidence_packaging",
)
STAGE_STATES = frozenset({"PASS", "FAIL", "BLOCKED", "DEFERRED", "NOT_APPLICABLE"})
FINGERPRINT_KEYS = (
    "i2_physical_snapshot_sha256",
    "c4_registry_sha256",
    "c11_manifest_sha256",
    "c6_schematic_sha256",
    "c7_report_sha256",
    "c8_report_sha256",
)

class C12Error(RuntimeError):
    pass
```

Reject bool-as-int target values, extra/missing stage IDs, unknown states and malformed hashes.

- [ ] **Step 3: Implement `validate_i5_manifest`**

Require I5 manifest target to match `TARGET`; require suite IDs `unit`, `gametest`, `dedicated_server`; accept only I5 suite states `PASS`/`BLOCKED`; require overall state to agree with suite states.

Return a deterministic list of error strings instead of throwing for malformed input.

- [ ] **Step 4: Implement report aggregation**

`build_runtime_acceptance_report` must:

```python
if target != TARGET:
    raise C12Error(f"target drift rejected: expected {TARGET}, got {target}")
if mode == "PREFLIGHT":
    overall_acceptance = "BLOCKED"
elif blocker_is_active:
    overall_acceptance = "BLOCKED"
elif any(state == "FAIL" for state in stages.values()):
    overall_acceptance = "FAIL"
elif all(state == "PASS" for state in stages.values()) and all_physical_fingerprints_present:
    overall_acceptance = "PASS"
else:
    overall_acceptance = "BLOCKED"
```

`overall_readiness` is `BLOCKED` when any stage is `FAIL`; otherwise `PREFLIGHT_READY`.

For `PHYSICAL_ACCEPTANCE`, require all six physical fingerprints to be non-null valid SHA-256 values before `PASS` is possible.

- [ ] **Step 5: Run focused tests**

```bash
python3 -m unittest construction/tests/test_c12_runtime_acceptance.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit schema/core**

```bash
git add construction/schemas/runtime-acceptance-report.schema.json construction/runtime/c12_runtime_acceptance.py construction/tests/test_c12_runtime_acceptance.py
git commit -m "feat(construction): add C12 runtime acceptance core"
```

---

### Task 3: Add filesystem-safe deterministic evidence packaging

**Files:**
- Create: `construction/runtime/c12_evidence.py`
- Modify: `construction/tests/test_c12_runtime_acceptance_security.py`

**Interfaces:**
- Produces:
  - `C12EvidenceError(RuntimeError)`
  - `package_evidence(workspace: Path, paths: list[Path]) -> list[dict[str, str]]`
- Output entries: `{"path": "relative/path", "sha256": "<64 hex>"}` sorted by relative path.

- [ ] **Step 1: Implement workspace containment**

Resolve the workspace once and reject any candidate that is absolute outside it, contains symlink components, is not a regular file, or resolves outside the workspace.

- [ ] **Step 2: Implement deterministic hashing**

Use streaming SHA-256 and return POSIX relative paths sorted lexicographically.

- [ ] **Step 3: Add malformed/duplicate evidence tests**

Cover duplicate paths, directory inputs, missing files and ordering determinism.

- [ ] **Step 4: Run security tests**

```bash
python3 -m unittest construction/tests/test_c12_runtime_acceptance_security.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit evidence helper**

```bash
git add construction/runtime/c12_evidence.py construction/tests/test_c12_runtime_acceptance_security.py
git commit -m "feat(construction): package C12 runtime evidence safely"
```

---

### Task 4: Bind C12 preflight to I5 and the shared final blocker

**Files:**
- Create: `construction/runtime/run_c12_preflight.py`
- Create: `construction/tests/fixtures/c12-preflight/i5-manifest.json`
- Create: `construction/tests/fixtures/c12-preflight/evidence/client-smoke-contract.log`
- Modify: `construction/tests/test_c12_runtime_acceptance.py`

**Interfaces:**
- `run_preflight(*, i5_manifest_path: Path, blocker_state_path: Path, evidence_root: Path) -> dict[str, object]`
- CLI writes one canonical report to a caller-specified path inside the workspace.

- [ ] **Step 1: Add a controlled I5 fixture**

Fixture target must be exact and suites must be `unit`, `gametest`, `dedicated_server`, all `PASS`. This proves C12 can consume I5 format without pretending it came from the physical modpack.

- [ ] **Step 2: Implement `run_preflight`**

Load and validate the I5 manifest, load `capture-state.json`, package fixture evidence, and build stage states:

```python
{
    "target_environment": "PASS",
    "i5_baseline": "PASS",
    "client_smoke": "DEFERRED",
    "live_placement": "DEFERRED",
    "runtime_visual_fidelity": "DEFERRED",
    "multiplayer": "DEFERRED",
    "full_modpack": "DEFERRED",
    "evidence_packaging": "PASS",
}
```

Authority fingerprint slots remain `null` in preflight unless real accepted evidence exists; do not synthesize hashes to imitate final physical evidence.

- [ ] **Step 3: Add blocker regression**

Assert the report contains the exact final blocker and `overall_acceptance == "BLOCKED"` while `overall_readiness == "PREFLIGHT_READY"`.

- [ ] **Step 4: Run C12 plus I5 regressions**

```bash
python3 -m unittest construction/tests/test_c12_runtime_acceptance.py construction/tests/test_c12_runtime_acceptance_security.py -v
python3 -m unittest engineering/tests/test_i5_test_harness.py -v
python3 -m unittest construction/tests/test_construction_final_physical_acceptance_gate.py -v
```

Expected: all PASS.

- [ ] **Step 5: Commit preflight runner**

```bash
git add construction/runtime/run_c12_preflight.py construction/tests/fixtures/c12-preflight construction/tests/test_c12_runtime_acceptance.py
git commit -m "feat(construction): add C12 preflight orchestration"
```

---

### Task 5: Add split C12 CI and Sonar coverage

**Files:**
- Create: `.github/workflows/factory-construction-c12-runtime-acceptance.yml`
- Modify: `.github/workflows/factory-sonar-ci.yml`
- Modify: `migration/full-skill-migration/test_sonar_ci_contract.py`
- Create: `construction/tests/test_c12_workflow_contract.py`

**Interfaces:**
- Job `c12-preflight` may pass.
- Job `c12-acceptance` must fail closed on the final blocker before checking physical evidence.

- [ ] **Step 1: Write the workflow contract test first**

Assert the workflow contains both jobs and that the acceptance guard reads `capture-state.json` and checks:

```python
blocker = "SUPER_HYPER_URGENT_FINAL_CONSTRUCTION_PHYSICAL_ACCEPTANCE"
if state.get("status") == blocker and state.get("blocks_c12_acceptance") is True:
    raise SystemExit(f"C12_ACCEPTANCE_BLOCKED: {blocker}")
```

The guard must execute before any check for C11 final manifest or physical C12 evidence.

- [ ] **Step 2: Create the workflow**

`c12-preflight` runs:

```bash
python3 -m unittest construction/tests/test_c12_runtime_acceptance.py -v
python3 -m unittest construction/tests/test_c12_runtime_acceptance_security.py -v
python3 -m unittest construction/tests/test_c12_workflow_contract.py -v
python3 -m unittest engineering/tests/test_i5_test_harness.py -v
python3 -m unittest construction/tests/test_construction_final_physical_acceptance_gate.py -v
python3 -m unittest migration/full-skill-migration/test_sonar_ci_contract.py -v
git diff --check
```

`c12-acceptance` depends on `c12-preflight` and runs the state-first blocker guard. It must intentionally fail while the blocker exists.

- [ ] **Step 3: Extend Sonar contract without removing I9/C10/C11 coverage**

Add C12 source/tests to `.github/workflows/factory-sonar-ci.yml` and assert them in `test_sonar_ci_contract.py`. Preserve every existing I9, C10 and C11 target.

- [ ] **Step 4: Run workflow/Sonar tests**

```bash
python3 -m unittest construction/tests/test_c12_workflow_contract.py -v
python3 -m unittest migration/full-skill-migration/test_sonar_ci_contract.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit CI changes**

```bash
git add .github/workflows/factory-construction-c12-runtime-acceptance.yml .github/workflows/factory-sonar-ci.yml migration/full-skill-migration/test_sonar_ci_contract.py construction/tests/test_c12_workflow_contract.py
git commit -m "ci(construction): gate C12 preflight and acceptance separately"
```

---

### Task 6: Document C12 boundary and prove the stacked PR head

**Files:**
- Modify: `construction/README.md`
- Modify: `construction/docs/ARCHITECTURE.md`
- Do not modify: `construction/STATUS.md`

**Interfaces:**
- Docs must state C12 preflight may be green while final acceptance remains blocked.

- [ ] **Step 1: Update README and ARCHITECTURE**

Document the I5 reuse, stage separation, C8/live-visual boundary, standalone/full-modpack boundary and exact blocker.

- [ ] **Step 2: Run the complete local contract suite**

```bash
python3 -m unittest construction/tests/test_c12_runtime_acceptance.py construction/tests/test_c12_runtime_acceptance_security.py construction/tests/test_c12_workflow_contract.py -v
python3 -m unittest engineering/tests/test_i5_test_harness.py -v
python3 -m unittest construction/tests/test_construction_final_physical_acceptance_gate.py -v
python3 -m unittest migration/full-skill-migration/test_sonar_ci_contract.py -v
git diff --check
```

Expected: all tests PASS and whitespace clean.

- [ ] **Step 3: Verify STATUS is unchanged**

Run:
```bash
git diff feat/construction-c11-complex-modded-golden...HEAD -- construction/STATUS.md
```

Expected: empty diff.

- [ ] **Step 4: Commit docs**

```bash
git add construction/README.md construction/docs/ARCHITECTURE.md
git commit -m "docs(construction): document C12 runtime acceptance boundary"
```

- [ ] **Step 5: Push and open a draft stacked PR**

Push `feat/construction-c12-runtime-acceptance-preflight` and open a draft PR with base `feat/construction-c11-complex-modded-golden`.

PR body must state: C12 implementation/preflight only; no C12 acceptance; no STATUS advancement; expected acceptance job remains blocked by the exact final blocker.

- [ ] **Step 6: Validate exact PR head**

Require C12 preflight, Governance and Sonar to pass. Require only the C12 acceptance gate to remain blocked/fail-closed with:

`C12_ACCEPTANCE_BLOCKED: SUPER_HYPER_URGENT_FINAL_CONSTRUCTION_PHYSICAL_ACCEPTANCE`

Do not merge the stacked PR before the authoritative physical acceptance sequence allows C11 then C12 closeout.
