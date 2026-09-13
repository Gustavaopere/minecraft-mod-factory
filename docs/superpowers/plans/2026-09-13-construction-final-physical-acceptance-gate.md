# Construction Final Physical Acceptance Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the temporary C11 runtime-capture blocker with the approved final Construction physical-acceptance blocker while preserving fail-closed C11 completion, allowing independent C12/C13 preflight work, and keeping `construction/STATUS.md` at the last actually completed phase.

**Architecture:** Reuse `construction/fixtures/complex-modded-golden/capture-state.json` as the machine-readable pending state; do not create a parallel authority. Reconcile the C11 branch with current `main` first so Engineering I9 and C11 Sonar coverage coexist. CI must evaluate the blocker before registry presence so checking in `registry.json` cannot bypass final acceptance.

**Tech Stack:** Python 3.11 `unittest`, JSON state, GitHub Actions, Markdown governance/docs, existing Factory Sonar CI, Minecraft 1.21.1 / NeoForge 21.1.248 / Java 21 probe contract.

**Spec:** `docs/superpowers/specs/2026-09-13-construction-final-physical-acceptance-gate-design.md`

## Global Constraints

- Exact blocker: `SUPER_HYPER_URGENT_FINAL_CONSTRUCTION_PHYSICAL_ACCEPTANCE`.
- `blocks_c11_completion = true`.
- `blocks_c12_acceptance = true`.
- `blocks_c13_final_acceptance = true`.
- `blocks_construction_final_acceptance = true`.
- C4 remains authority for actual modpack block/state existence.
- Preflight readiness never becomes final acceptance.
- `construction/STATUS.md` remains at the last actually completed/post-merge-validated phase.
- Final acceptance re-audits and re-hashes the physical environment.
- Closeout order remains `C11 -> C12 -> C13 -> Construction`.
- Synthetic fixtures are preflight/test evidence only.

---

### Task 1: Reconcile the C11 branch with current main

**Files:** `.github/workflows/factory-sonar-ci.yml`

- [ ] Merge current `main` into `feat/construction-c11-complex-modded-golden` without rebasing away C11 history.
- [ ] Preserve the I9 coverage block containing `engineering/tooling/machine-foundation/materialize_i9.py`.
- [ ] Preserve the C11 coverage block containing `construction/fixtures/complex-modded-golden/capture_registry.py` after C10 coverage.
- [ ] Verify `git merge-base --is-ancestor origin/main HEAD` and `git diff --check origin/main...HEAD` both succeed.

### Task 2: Write RED tests for the final blocker

**Files:**
- Create: `construction/tests/test_construction_final_physical_acceptance_gate.py`
- Modify: `construction/tests/test_c11_complex_modded_golden.py`
- Supersede: `construction/tests/test_c11_modlist_stabilization_transition.py`

- [ ] Add a focused test requiring the exact blocker, all four blocking booleans, historical modlist SHA `7c0a23d6013101383d196526e4b6ba6940fb54a0fed10eaed5956ab015cfcc00`, and fresh final re-hash/C4 capture flags.
- [ ] Require `construction/STATUS.md` to remain `PHASE=C10_COMPLETE_POSTMERGE_VALIDATED` and not claim C11/C12/C13 completion.
- [ ] Replace the old C11 blocker constant with `SUPER_HYPER_URGENT_FINAL_CONSTRUCTION_PHYSICAL_ACCEPTANCE`.
- [ ] Make completion-only registry validation skip only when the exact final blocker is present and `blocks_c11_completion` is true.
- [ ] Run the focused test and C11 module; expected RED must come from the old state/docs/workflow semantics.

### Task 3: Transition the machine-readable state

**File:** `construction/fixtures/complex-modded-golden/capture-state.json`

- [ ] Set schema version to 2 and status to `SUPER_HYPER_URGENT_FINAL_CONSTRUCTION_PHYSICAL_ACCEPTANCE`.
- [ ] Record all four blocking booleans as true.
- [ ] Preserve the existing probe artifact/run/JAR SHA and historical modlist hash.
- [ ] Add `final_gate_requires_fresh_physical_modlist_rehash = true` and `final_gate_requires_fresh_c4_runtime_capture = true`.
- [ ] Replace the old completion list with the final campaign requirements: fresh I2/C4 evidence, evidence-backed C5/C2/C7/C8/C6 outputs, C12 physical runtime acceptance, C13 validation, ordered closeout.
- [ ] Run the focused state test; expected PASS.

### Task 4: Harden C11 CI against blocker bypass

**Files:**
- Modify: `.github/workflows/factory-construction-c11-complex-modded-golden.yml`
- Modify: `construction/tests/test_c11_complex_modded_golden.py`
- Delete: `construction/tests/test_c11_modlist_stabilization_transition.py`

- [ ] Replace the old stabilization-transition test path/invocation with `construction/tests/test_construction_final_physical_acceptance_gate.py`.
- [ ] Rename the completion step to `Require final physical acceptance gate to be cleared`.
- [ ] Parse `capture-state.json` before checking `registry.json`; if the final blocker is active with `blocks_c11_completion = true`, fail with `C11_COMPLETION_BLOCKED: SUPER_HYPER_URGENT_FINAL_CONSTRUCTION_PHYSICAL_ACCEPTANCE`.
- [ ] Only after the blocker is cleared, require final canonical `registry.json` and execute the C11 completion suite.
- [ ] Update workflow assertions and preserve all pinned action SHAs.
- [ ] Run final-gate, C11 path-security, C11 main, and shared Sonar governance tests.

### Task 5: Update docs without advancing STATUS

**Files:**
- Modify: `construction/README.md`
- Modify: `construction/docs/ARCHITECTURE.md`
- Do not modify: `construction/STATUS.md`

- [ ] Replace `MODLIST_STABILIZED_AWAITING_RUNTIME_CAPTURE` wording with the final blocker.
- [ ] State that C11 completion, C12 acceptance, C13 final acceptance, and Construction final closeout are blocked.
- [ ] State that C12/C13 design/implementation/preflight may continue independently.
- [ ] State that final acceptance re-audits/re-hashes the physical modlist and performs fresh C4 capture.
- [ ] Preserve I2/C4/C5/C2/C7/C8/C6 authorities and closeout order `C11 -> C12 -> C13 -> Construction`.
- [ ] Strengthen documentation tests and verify `construction/STATUS.md` has no branch diff.

### Task 6: Verify the C11 preflight branch and update PR #100

- [ ] Run final-gate, C11 path-security, C11 main, C4 runtime-probe, shared Sonar governance, and whitespace checks.
- [ ] Materialize/build the C4 NeoForge probe with Java 21 / NeoForge 21.1.248 exactly as the existing workflow does.
- [ ] Push the branch only when preflight tests are green.
- [ ] Require preflight/governance/Sonar jobs to pass while `c11-completion` remains the single intentional failure with the exact final blocker.
- [ ] Update PR #100 body to remove stale stabilization wording, record the exact blocker, preserve C10 STATUS, and record validated head/run evidence.
- [ ] Do not merge or label C11 complete.

### Task 7: Start C12/C13 preflight after Task 6 is green

- [ ] Re-audit current `main`, branches, PRs, and Construction tree.
- [ ] Design C12 preflight so harness/report/schema/negative-path implementation may proceed while `blocks_c12_acceptance = true` remains authoritative.
- [ ] Design C13 preflight so capability/router implementation may proceed while `blocks_c13_final_acceptance = true` remains authoritative.
- [ ] Stop before any physical/manual final campaign; do not claim final C11/C12/C13 acceptance without the real final evidence sequence.
