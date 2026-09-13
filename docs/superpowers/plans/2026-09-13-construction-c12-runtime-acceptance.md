# Construction C12 Runtime Acceptance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a fail-closed C12 runtime-acceptance preflight that reuses Engineering I5, packages deterministic evidence, and cannot claim physical acceptance while the final Construction blocker exists.

**Architecture:** Add a focused C12 domain module under `construction/runtime/`, a JSON report schema, and filesystem-safe evidence helpers. Reuse the existing I5 manifest as baseline evidence; do not fork I5. Split CI into green preflight and intentionally blocked final acceptance, and keep `construction/STATUS.md` unchanged.

**Tech Stack:** Python 3.11 stdlib, JSON, SHA-256, unittest, GitHub Actions, Engineering I5, existing Construction authorities C2/C4/C6/C7/C8/C11.

**Spec:** `docs/superpowers/specs/2026-09-13-construction-c12-runtime-acceptance-design.md`

## Global Constraints

- Target is exactly Minecraft `1.21.1`, NeoForge `21.1.248`, Java `21`.
- Exact final blocker is `SUPER_HYPER_URGENT_FINAL_CONSTRUCTION_PHYSICAL_ACCEPTANCE`.
- C12 wraps Engineering I5; it must not duplicate or replace I5.
- `PREFLIGHT` can become green but can never produce final acceptance `PASS`.
- C8 offline Visual QA cannot substitute for live runtime visual fidelity.
- Dedicated-server PASS cannot substitute for multiplayer PASS.
- Standalone PASS cannot substitute for full-modpack PASS.
- C11 not accepted means C12 cannot accept.
- Evidence paths must reject traversal and symlink escape.
- Final physical report path is `construction/fixtures/complex-modded-golden/c12-runtime-acceptance-report.json`.
- `construction/STATUS.md` must not change.
- Final closeout order remains `C11 -> C12 -> C13 -> Construction`.

---

### Task 1: Create the stacked branch and RED C12 contracts

**Files:**
- Create branch: `feat/construction-c12-runtime-acceptance-preflight`
- Create: `construction/tests/test_c12_runtime_acceptance.py`
- Create: `construction/tests/test_c12_runtime_acceptance_security.py`

**Interfaces:**
- Produces expected public API names: `C12Error`, `build_runtime_acceptance_report`, `validate_runtime_acceptance_report`, `validate_i5_manifest`, `C12EvidenceError`, `package_evidence`.

- [ ] **Step 1: Create the C12 branch from the exact C11 preflight head**

```bash
git switch feat/construction-c11-complex-modded-golden
git pull --ff-only
git switch -c feat/construction-c12-runtime-acceptance-preflight
```

- [ ] **Step 2: Write RED domain tests**

Create `construction/tests/test_c12_runtime_acceptance.py` with exact target/blocker tests. Core cases:

```python
from construction.runtime.c12_runtime_acceptance import C12Error, build_runtime_acceptance_report

TARGET = {"minecraft": "1.21.1", "loader": "neoforge", "neoforge": "21.1.248", "java": 21}
BLOCKER = "SUPER_HYPER_URGENT_FINAL_CONSTRUCTION_PHYSICAL_ACCEPTANCE"
FINGERPRINTS = {
    "i2_physical_snapshot_sha256": None,
    "c4_registry_sha256": None,
    "c11_manifest_sha256": None,
    "c6_schematic_sha256": None,
    "c7_report_sha256": None,
    "c8_report_sha256": None,
}
STAGES = {
    "target_environment": "PASS",
    "i5_baseline": "PASS",
    "client_smoke": "DEFERRED",
    "live_placement": "DEFERRED",
    "runtime_visual_fidelity": "DEFERRED",
    "multiplayer": "DEFERRED",
    "full_modpack": "DEFERRED",
    "evidence_packaging": "PASS",
}


def test_preflight_ready_is_not_acceptance():
    report = build_runtime_acceptance_report(
        mode="PREFLIGHT",
        target=TARGET,
        blocker={"status": BLOCKER, "blocks_c12_acceptance": True},
        authority_fingerprints=FINGERPRINTS,
        stages=STAGES,
    )
    assert report["overall_readiness"] == "PREFLIGHT_READY"
    assert report["overall_acceptance"] == "BLOCKED"
    assert report["blocker"] == BLOCKER


def test_target_drift_fails_closed():
    bad = dict(TARGET, neoforge="21.1.247")
    try:
        build_runtime_acceptance_report(
            mode="PREFLIGHT",
            target=bad,
            blocker={"status": BLOCKER, "blocks_c12_acceptance": True},
            authority_fingerprints=FINGERPRINTS,
            stages=STAGES,
        )
    except C12Error as exc:
        assert "target drift" in str(exc)
    else:
        raise AssertionError("target drift must fail closed")
```

Also test exact stage IDs, unknown states, malformed SHA fields, C11-not-accepted, C8-not-runtime, dedicated-server-not-multiplayer, and standalone-not-full-modpack.

- [ ] **Step 3: Write RED security tests using stdlib only**

```python
import tempfile
import unittest
from pathlib import Path
from construction.runtime.c12_evidence import C12EvidenceError, package_evidence


class EvidenceSecurityTest(unittest.TestCase):
    def test_parent_escape_is_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            workspace = Path(raw) / "workspace"
            workspace.mkdir()
            outside = Path(raw) / "outside.log"
            outside.write_text("x", encoding="utf-8")
            with self.assertRaises(C12EvidenceError):
                package_evidence(workspace, [outside])

    def test_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            workspace = Path(raw)
            real = workspace / "real.log"
            real.write_text("x", encoding="utf-8")
            link = workspace / "link.log"
            link.symlink_to(real)
            with self.assertRaises(C12EvidenceError):
                package_evidence(workspace, [link])
```

- [ ] **Step 4: Run RED tests**

```bash
python3 -m unittest construction/tests/test_c12_runtime_acceptance.py -v
python3 -m unittest construction/tests/test_c12_runtime_acceptance_security.py -v
```

Expected: import failures because the C12 modules do not exist yet.

- [ ] **Step 5: Commit RED tests**

```bash
git add construction/tests/test_c12_runtime_acceptance.py construction/tests/test_c12_runtime_acceptance_security.py
git commit -m "test(construction): define C12 runtime acceptance contracts"
```

---

### Task 2: Implement the report schema, aggregation core and safe evidence packaging

**Files:**
- Create: `construction/schemas/runtime-acceptance-report.schema.json`
- Create: `construction/runtime/c12_runtime_acceptance.py`
- Create: `construction/runtime/c12_evidence.py`
- Modify: `construction/tests/test_c12_runtime_acceptance.py`
- Modify: `construction/tests/test_c12_runtime_acceptance_security.py`

**Interfaces:**
- `C12Error(RuntimeError)`
- `build_runtime_acceptance_report(...) -> dict[str, object]`
- `validate_runtime_acceptance_report(report: object) -> list[str]`
- `validate_i5_manifest(manifest: object) -> list[str]`
- `C12EvidenceError(RuntimeError)`
- `package_evidence(workspace: Path, paths: list[Path]) -> list[dict[str, str]]`

- [ ] **Step 1: Add exact constants and enums**

```python
TARGET = {"minecraft": "1.21.1", "loader": "neoforge", "neoforge": "21.1.248", "java": 21}
FINAL_BLOCKER = "SUPER_HYPER_URGENT_FINAL_CONSTRUCTION_PHYSICAL_ACCEPTANCE"
STAGE_IDS = (
    "target_environment", "i5_baseline", "client_smoke", "live_placement",
    "runtime_visual_fidelity", "multiplayer", "full_modpack", "evidence_packaging",
)
STAGE_STATES = frozenset({"PASS", "FAIL", "BLOCKED", "DEFERRED", "NOT_APPLICABLE"})
FINGERPRINT_KEYS = (
    "i2_physical_snapshot_sha256", "c4_registry_sha256", "c11_manifest_sha256",
    "c6_schematic_sha256", "c7_report_sha256", "c8_report_sha256",
)
```

- [ ] **Step 2: Add the JSON schema**

Require closed objects, exact target fields, the fixed stage IDs, stage-state enum, `overall_readiness` in `PREFLIGHT_READY|BLOCKED`, `overall_acceptance` in `PASS|FAIL|BLOCKED`, deterministic diagnostics/evidence arrays, and SHA values as lowercase 64-hex or `null` where preflight permits missing physical evidence.

- [ ] **Step 3: Implement I5 manifest validation**

Require exact target, suite IDs `unit`, `gametest`, `dedicated_server`, suite states `PASS|BLOCKED`, and an `overall_state` consistent with the suites. Return deterministic error strings.

- [ ] **Step 4: Implement report aggregation**

Use this ordering:

```python
if target != TARGET:
    raise C12Error(...)
if any(state == "FAIL" for state in stages.values()):
    overall_readiness = "BLOCKED"
    overall_acceptance = "FAIL"
elif mode == "PREFLIGHT":
    overall_readiness = "PREFLIGHT_READY"
    overall_acceptance = "BLOCKED"
elif blocker_is_active:
    overall_readiness = "PREFLIGHT_READY"
    overall_acceptance = "BLOCKED"
elif all(state == "PASS" for state in stages.values()) and all_physical_fingerprints_present:
    overall_readiness = "PREFLIGHT_READY"
    overall_acceptance = "PASS"
else:
    overall_readiness = "PREFLIGHT_READY"
    overall_acceptance = "BLOCKED"
```

`PHYSICAL_ACCEPTANCE` can reach `PASS` only with all six non-null valid physical fingerprints and every required stage `PASS`.

- [ ] **Step 5: Implement safe evidence packaging**

Reject missing files, directories, duplicate paths, symlinks, path escape and any resolved path outside the workspace. Hash regular files with streaming SHA-256 and return entries sorted by POSIX relative path.

- [ ] **Step 6: Run focused tests**

```bash
python3 -m unittest construction/tests/test_c12_runtime_acceptance.py construction/tests/test_c12_runtime_acceptance_security.py -v
```

Expected: PASS.

- [ ] **Step 7: Commit core**

```bash
git add construction/schemas/runtime-acceptance-report.schema.json construction/runtime/c12_runtime_acceptance.py construction/runtime/c12_evidence.py construction/tests/test_c12_runtime_acceptance.py construction/tests/test_c12_runtime_acceptance_security.py
git commit -m "feat(construction): add C12 runtime acceptance core"
```

---

### Task 3: Bind preflight to I5 and preserve the physical-final boundary

**Files:**
- Create: `construction/runtime/run_c12_preflight.py`
- Create: `construction/tests/fixtures/c12-preflight/i5-manifest.json`
- Create: `construction/tests/fixtures/c12-preflight/evidence/preflight-contract.log`
- Modify: `construction/tests/test_c12_runtime_acceptance.py`

**Interfaces:**
- `run_preflight(*, i5_manifest_path: Path, blocker_state_path: Path, evidence_root: Path) -> dict[str, object]`
- Generated preflight report path: `build/c12-runtime-acceptance/preflight-report.json`
- Reserved final physical report path: `construction/fixtures/complex-modded-golden/c12-runtime-acceptance-report.json`

- [ ] **Step 1: Add a controlled I5 fixture**

Use exact target and three PASS suites: `unit`, `gametest`, `dedicated_server`. Mark the fixture clearly as synthetic preflight evidence.

- [ ] **Step 2: Implement `run_preflight`**

Validate the I5 fixture, load `construction/fixtures/complex-modded-golden/capture-state.json`, package the controlled evidence file, and build these stages:

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

All six physical fingerprint slots remain `null` in preflight. Do not synthesize final hashes.

- [ ] **Step 3: Add regression assertions**

Assert `overall_readiness == "PREFLIGHT_READY"`, `overall_acceptance == "BLOCKED"`, exact blocker propagation, and absence of a checked-in final physical report.

- [ ] **Step 4: Run C12 and I5 regressions**

```bash
python3 -m unittest construction/tests/test_c12_runtime_acceptance.py construction/tests/test_c12_runtime_acceptance_security.py -v
python3 -m unittest engineering/tests/test_i5_test_harness.py -v
python3 -m unittest construction/tests/test_construction_final_physical_acceptance_gate.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit preflight runner**

```bash
git add construction/runtime/run_c12_preflight.py construction/tests/fixtures/c12-preflight construction/tests/test_c12_runtime_acceptance.py
git commit -m "feat(construction): add C12 preflight orchestration"
```

---

### Task 4: Add split CI, docs and exact stacked-PR validation

**Files:**
- Create: `.github/workflows/factory-construction-c12-runtime-acceptance.yml`
- Create: `construction/tests/test_c12_workflow_contract.py`
- Modify: `.github/workflows/factory-sonar-ci.yml`
- Modify: `migration/full-skill-migration/test_sonar_ci_contract.py`
- Modify: `construction/README.md`
- Modify: `construction/docs/ARCHITECTURE.md`
- Do not modify: `construction/STATUS.md`

**Interfaces:**
- Job `c12-preflight`: green-capable.
- Job `c12-acceptance`: state-first fail-closed.

- [ ] **Step 1: Write workflow RED test**

Assert the acceptance job checks the blocker before the final report path:

```python
blocker = "SUPER_HYPER_URGENT_FINAL_CONSTRUCTION_PHYSICAL_ACCEPTANCE"
if state.get("status") == blocker and state.get("blocks_c12_acceptance") is True:
    raise SystemExit(f"C12_ACCEPTANCE_BLOCKED: {blocker}")
```

Only after this guard is cleared may the workflow require `construction/fixtures/complex-modded-golden/c12-runtime-acceptance-report.json`.

- [ ] **Step 2: Create C12 workflow**

`c12-preflight` runs:

```bash
python3 -m unittest construction/tests/test_c12_runtime_acceptance.py construction/tests/test_c12_runtime_acceptance_security.py construction/tests/test_c12_workflow_contract.py -v
python3 -m unittest engineering/tests/test_i5_test_harness.py -v
python3 -m unittest construction/tests/test_construction_final_physical_acceptance_gate.py -v
python3 -m unittest migration/full-skill-migration/test_sonar_ci_contract.py -v
git diff --check
```

`c12-acceptance` depends on preflight and intentionally fails on the exact blocker while it exists.

- [ ] **Step 3: Extend Sonar coverage without deleting I9/C10/C11 targets**

Add C12 source/tests to `.github/workflows/factory-sonar-ci.yml` and add exact assertions to `migration/full-skill-migration/test_sonar_ci_contract.py`.

- [ ] **Step 4: Update README and ARCHITECTURE**

Document I5 reuse, preflight-vs-acceptance, C8-vs-live-visual boundary, dedicated-vs-multiplayer boundary, standalone-vs-full-modpack boundary, final report path and exact blocker.

- [ ] **Step 5: Run complete C12 preflight verification**

```bash
python3 -m unittest construction/tests/test_c12_runtime_acceptance.py construction/tests/test_c12_runtime_acceptance_security.py construction/tests/test_c12_workflow_contract.py -v
python3 -m unittest engineering/tests/test_i5_test_harness.py -v
python3 -m unittest construction/tests/test_construction_final_physical_acceptance_gate.py -v
python3 -m unittest migration/full-skill-migration/test_sonar_ci_contract.py -v
git diff --check
git diff feat/construction-c11-complex-modded-golden...HEAD -- construction/STATUS.md
```

Expected: tests PASS, whitespace clean, STATUS diff empty.

- [ ] **Step 6: Commit CI/docs**

```bash
git add .github/workflows/factory-construction-c12-runtime-acceptance.yml .github/workflows/factory-sonar-ci.yml migration/full-skill-migration/test_sonar_ci_contract.py construction/tests/test_c12_workflow_contract.py construction/README.md construction/docs/ARCHITECTURE.md
git commit -m "ci(construction): gate C12 preflight separately"
```

- [ ] **Step 7: Push and open a draft stacked PR**

Push `feat/construction-c12-runtime-acceptance-preflight` and open a draft PR with base `feat/construction-c11-complex-modded-golden`.

Require C12 preflight, Governance and Sonar green. Require only final acceptance to remain fail-closed with:

`C12_ACCEPTANCE_BLOCKED: SUPER_HYPER_URGENT_FINAL_CONSTRUCTION_PHYSICAL_ACCEPTANCE`

Do not merge or advance STATUS before the authoritative physical campaign.
