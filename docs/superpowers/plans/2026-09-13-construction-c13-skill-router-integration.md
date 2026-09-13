# Construction C13 Skill/Router Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a deterministic C13 capability index and validator that integrates Construction capabilities into the existing Factory router without creating a second authority or falsely promoting preflight readiness to final acceptance.

**Architecture:** Keep `skills/ROUTER.md`, `skills/VERSION-AUTHORITY.md`, `skills/USER-GUIDED-WORKFLOW.md` and `engineering/REPO-ROUTING.md` as canonical authorities. Add a small machine-readable capability index plus pure-Python validation/resolution. C13 consumes the C12 contract from `construction/runtime/c12_runtime_acceptance.py` and, after the blocker is cleared, the final physical report at `construction/fixtures/complex-modded-golden/c12-runtime-acceptance-report.json`.

**Tech Stack:** Python 3.11 stdlib, JSON, unittest, existing skill repository validator, Construction C9/C10/C12 contracts, GitHub Actions, Sonar/Governance.

**Spec:** `docs/superpowers/specs/2026-09-13-construction-c13-skill-router-integration-design.md`

## Global Constraints

- Preserve `skills/ROUTER.md` as the canonical human-facing router.
- Preserve `engineering/REPO-ROUTING.md` as the repository/authority boundary contract.
- Preserve `skills/VERSION-AUTHORITY.md` for version-sensitive proof.
- Preserve `skills/USER-GUIDED-WORKFLOW.md` for one manual action at a time.
- Do not create one skill per Construction phase or provider.
- Provider presence does not prove provider API support.
- `REFERENCE_ONLY` material cannot become active authority through C13.
- Readiness and acceptance remain separate axes.
- Exact blocker is `SUPER_HYPER_URGENT_FINAL_CONSTRUCTION_PHYSICAL_ACCEPTANCE`.
- C11/C12 preflight readiness cannot be promoted to accepted.
- C13 final acceptance must require the canonical final C12 report path after the blocker is cleared.
- `construction/STATUS.md` must not change.
- C13 branch is stacked on the exact validated C12 preflight branch.

---

### Task 1: Create the stacked branch and RED C13 contracts

**Files:**
- Create branch: `feat/construction-c13-skill-router-preflight`
- Create: `construction/tests/test_c13_skill_router_integration.py`

**Interfaces:**
- Expected public API in `skills/scripts/capability_router.py`: `CapabilityIndexError`, `load_capability_index`, `validate_capability_index`, `resolve_intent`.

- [ ] **Step 1: Create C13 branch from validated C12 head**

```bash
git switch feat/construction-c12-runtime-acceptance-preflight
git pull --ff-only
git switch -c feat/construction-c13-skill-router-preflight
```

- [ ] **Step 2: Write RED routing tests**

```python
from pathlib import Path
import unittest
from skills.scripts.capability_router import load_capability_index, resolve_intent, validate_capability_index

ROOT = Path(__file__).resolve().parents[2]
INDEX = ROOT / "skills/capabilities/capability-index.json"
BLOCKER = "SUPER_HYPER_URGENT_FINAL_CONSTRUCTION_PHYSICAL_ACCEPTANCE"


class C13RoutingTest(unittest.TestCase):
    def test_c11_and_c12_are_preflight_ready_but_blocked(self):
        index = load_capability_index(INDEX)
        c11 = resolve_intent(index, "construction.complex_modded_golden")
        c12 = resolve_intent(index, "construction.runtime_acceptance")
        self.assertEqual((c11["readiness"], c11["acceptance"], c11["blocker"]), ("PREFLIGHT_READY", "BLOCKED", BLOCKER))
        self.assertEqual((c12["readiness"], c12["acceptance"], c12["blocker"]), ("PREFLIGHT_READY", "BLOCKED", BLOCKER))

    def test_unknown_intent_fails_closed(self):
        index = load_capability_index(INDEX)
        route = resolve_intent(index, "provider.unproven.magic_api")
        self.assertEqual(route["readiness"], "UNAVAILABLE")
        self.assertEqual(route["acceptance"], "BLOCKED")
```

Add in-memory mutation tests for duplicate IDs/intents, unknown authority, missing entrypoint, `REFERENCE_ONLY` promotion, accepted-with-blocker, and provider route lacking exact-API proof semantics.

- [ ] **Step 3: Run RED tests**

```bash
python3 -m unittest construction/tests/test_c13_skill_router_integration.py -v
```

Expected: import failure because the capability router/index do not exist.

- [ ] **Step 4: Commit RED tests**

```bash
git add construction/tests/test_c13_skill_router_integration.py
git commit -m "test(construction): define C13 router integration contracts"
```

---

### Task 2: Add the machine-readable capability index and pure resolver

**Files:**
- Create: `skills/capabilities/capability-index.schema.json`
- Create: `skills/capabilities/capability-index.json`
- Create: `skills/scripts/capability_router.py`
- Modify: `construction/tests/test_c13_skill_router_integration.py`

**Interfaces:**
- Capability fields:
  - `capability_id: str`
  - `intent: str`
  - `authority: str`
  - `entrypoint: str`
  - `required_evidence: list[str]`
  - `readiness: AVAILABLE | PREFLIGHT_READY | UNAVAILABLE`
  - `acceptance: ACCEPTED | BLOCKED | NOT_APPLICABLE`
  - `blocker: str | null`
  - `version_proof: NOT_REQUIRED | REQUIRED_PHYSICAL | REQUIRED_EXACT_API`
  - `fallback_policy: NONE | EXPLICIT_EQUIVALENT_ONLY`
  - `forbidden_promotions: list[str]`

- [ ] **Step 1: Define closed schema and constants**

```python
TARGET = {"minecraft": "1.21.1", "loader": "neoforge", "neoforge": "21.1.248", "java": 21}
READINESS = frozenset({"AVAILABLE", "PREFLIGHT_READY", "UNAVAILABLE"})
ACCEPTANCE = frozenset({"ACCEPTED", "BLOCKED", "NOT_APPLICABLE"})
VERSION_PROOF = frozenset({"NOT_REQUIRED", "REQUIRED_PHYSICAL", "REQUIRED_EXACT_API"})
FALLBACK = frozenset({"NONE", "EXPLICIT_EQUIVALENT_ONLY"})
FINAL_BLOCKER = "SUPER_HYPER_URGENT_FINAL_CONSTRUCTION_PHYSICAL_ACCEPTANCE"
```

- [ ] **Step 2: Populate canonical routes**

At minimum:

```text
construction.registry_search            -> C4 / construction/mcp/server.py#registry_search
construction.palette_resolve            -> C5 / construction/mcp/server.py#palette_resolve
construction.build_canonicalize         -> C2 / construction/mcp/server.py#build_canonicalize
construction.structural_qa              -> C7 / construction/mcp/server.py#qa_structural
construction.offline_visual_qa          -> C8 / construction/mcp/server.py#qa_visual
construction.sponge_v3_export           -> C6 / construction/mcp/server.py#export_sponge_v3
construction.external_provider_handoff  -> C10 / construction/providers
construction.complex_modded_golden      -> C11 / construction/fixtures/complex-modded-golden/capture-state.json
construction.runtime_acceptance         -> C12 / construction/runtime/c12_runtime_acceptance.py
engineering.runtime_modification        -> ENGINEERING / engineering/AGENT-WORKFLOW.md
art.visual_authoring                    -> ART / art/
```

C11 and C12 are exactly `PREFLIGHT_READY / BLOCKED` with the final blocker. Already-proven offline C9-backed capabilities may be `AVAILABLE / ACCEPTED`. Cross-domain authority routes may be `AVAILABLE / NOT_APPLICABLE`.

- [ ] **Step 3: Encode forbidden-promotion tokens**

Use the stable tokens:

```json
[
  "NO_PREFLIGHT_TO_FINAL_ACCEPTANCE",
  "NO_STATIC_TO_RUNTIME_CONFIRMED",
  "NO_OFFLINE_VISUAL_TO_RUNTIME_FIDELITY",
  "NO_PROVIDER_PRESENCE_TO_API_SUPPORT",
  "NO_REFERENCE_ONLY_TO_ACTIVE_AUTHORITY"
]
```

Only attach rules relevant to each capability.

- [ ] **Step 4: Implement path and semantic validation**

`validate_capability_index(index, repo_root=...)` rejects duplicate IDs/intents, unknown authority, invalid enums, accepted-with-blocker, unavailable-and-accepted, absolute/escaping entrypoints, missing paths, active routes into `migration/provenance/historical-skills/`, and provider/API declarations missing `REQUIRED_EXACT_API` plus `NO_PROVIDER_PRESENCE_TO_API_SUPPORT`.

For `path#symbol`, require the path to exist and the source text to define the named symbol.

- [ ] **Step 5: Implement exact intent resolution**

For one exact intent return a copy of its declaration. For no route return:

```python
{
    "capability_id": None,
    "intent": intent,
    "authority": None,
    "entrypoint": None,
    "required_evidence": [],
    "readiness": "UNAVAILABLE",
    "acceptance": "BLOCKED",
    "blocker": "NO_DECLARED_CAPABILITY_ROUTE",
    "version_proof": "NOT_REQUIRED",
    "fallback_policy": "NONE",
    "forbidden_promotions": [],
}
```

The validator makes duplicate intents invalid, so the resolver never guesses precedence.

- [ ] **Step 6: Run focused tests**

```bash
python3 -m unittest construction/tests/test_c13_skill_router_integration.py -v
```

Expected: PASS.

- [ ] **Step 7: Commit capability core**

```bash
git add skills/capabilities/capability-index.schema.json skills/capabilities/capability-index.json skills/scripts/capability_router.py construction/tests/test_c13_skill_router_integration.py
git commit -m "feat(skills): add Construction capability routing"
```

---

### Task 3: Integrate existing router authorities without replacing them

**Files:**
- Modify: `skills/ROUTER.md`
- Modify: `skills/README.md`
- Modify: `engineering/REPO-ROUTING.md`
- Modify: `construction/tests/test_c13_skill_router_integration.py`

**Interfaces:**
- Existing prose files remain canonical authorities.
- Capability index remains machine-readable routing metadata only.

- [ ] **Step 1: Add RED documentation assertions**

Require text equivalent to:

```text
skills/ROUTER.md remains the canonical router
capability-index.json is routing metadata, not a second authority
readiness does not imply acceptance
```

- [ ] **Step 2: Update `skills/ROUTER.md` narrowly**

Add a capability-index section. Preserve current Engineering, Art, VFX and `REFERENCE_ONLY` sections.

- [ ] **Step 3: Update `skills/README.md`**

Document `skills/capabilities/` and `skills/scripts/capability_router.py` while preserving active-vs-`REFERENCE_ONLY` classification.

- [ ] **Step 4: Update `engineering/REPO-ROUTING.md` narrowly**

Reference the capability index as metadata that cannot override runtime authority, physical evidence or exact provider API proof.

- [ ] **Step 5: Run router + skill validation**

```bash
python3 -m unittest construction/tests/test_c13_skill_router_integration.py -v
python3 skills/scripts/validate_skill_repository.py
```

Expected: PASS.

- [ ] **Step 6: Commit authority integration**

```bash
git add skills/ROUTER.md skills/README.md engineering/REPO-ROUTING.md construction/tests/test_c13_skill_router_integration.py
git commit -m "docs(skills): integrate Construction capability index"
```

---

### Task 4: Add C13 CI, exact C12 final-report dependency, docs and stacked PR validation

**Files:**
- Create: `.github/workflows/factory-construction-c13-skill-router.yml`
- Create: `construction/tests/test_c13_workflow_contract.py`
- Modify: `.github/workflows/factory-sonar-ci.yml`
- Modify: `migration/full-skill-migration/test_sonar_ci_contract.py`
- Modify: `construction/README.md`
- Modify: `construction/docs/ARCHITECTURE.md`
- Do not modify: `construction/STATUS.md`

**Interfaces:**
- Job `c13-router-preflight`: green-capable.
- Job `c13-final-acceptance`: state-first fail-closed.
- Final C12 evidence path: `construction/fixtures/complex-modded-golden/c12-runtime-acceptance-report.json`.

- [ ] **Step 1: Write workflow RED test**

Require this ordering:

```python
blocker = "SUPER_HYPER_URGENT_FINAL_CONSTRUCTION_PHYSICAL_ACCEPTANCE"
if c11_state.get("status") == blocker and c11_state.get("blocks_c13_final_acceptance") is True:
    raise SystemExit(f"C13_FINAL_ACCEPTANCE_BLOCKED: {blocker}")
```

Only after the blocker is cleared may the workflow require `construction/fixtures/complex-modded-golden/c12-runtime-acceptance-report.json`, validate that report, and require `overall_acceptance == "PASS"`.

- [ ] **Step 2: Create C13 workflow**

`c13-router-preflight` runs:

```bash
python3 -m unittest construction/tests/test_c13_skill_router_integration.py construction/tests/test_c13_workflow_contract.py -v
python3 skills/scripts/validate_skill_repository.py
python3 -m unittest construction/tests/test_c9_agent_mcp.py construction/tests/test_c9_mcp_stdio.py -v
python3 -m unittest construction/tests/test_c10_provider_profiles.py construction/tests/test_c10_handoff_request.py construction/tests/test_c10_handoff_receipt.py -v
python3 -m unittest construction/tests/test_c12_runtime_acceptance.py construction/tests/test_c12_runtime_acceptance_security.py -v
python3 -m unittest construction/tests/test_construction_final_physical_acceptance_gate.py -v
python3 -m unittest migration/full-skill-migration/test_sonar_ci_contract.py -v
git diff --check
```

`c13-final-acceptance` depends on preflight and intentionally fails on the exact blocker while it exists.

- [ ] **Step 3: Extend Sonar coverage without deleting I9/C10/C11/C12 targets**

Add `skills/scripts/capability_router.py`, C13 tests and workflow-contract coverage. Update `test_sonar_ci_contract.py` with exact assertions.

- [ ] **Step 4: Update Construction docs**

Document preserved router authorities, readiness-vs-acceptance, provider-presence-vs-API proof, exact C12 final-report dependency, and closeout order.

- [ ] **Step 5: Run complete C13 preflight verification**

```bash
python3 -m unittest construction/tests/test_c13_skill_router_integration.py construction/tests/test_c13_workflow_contract.py -v
python3 skills/scripts/validate_skill_repository.py
python3 -m unittest construction/tests/test_c9_agent_mcp.py construction/tests/test_c9_mcp_stdio.py -v
python3 -m unittest construction/tests/test_c10_provider_profiles.py construction/tests/test_c10_handoff_request.py construction/tests/test_c10_handoff_receipt.py -v
python3 -m unittest construction/tests/test_c12_runtime_acceptance.py construction/tests/test_c12_runtime_acceptance_security.py -v
python3 -m unittest construction/tests/test_construction_final_physical_acceptance_gate.py -v
python3 -m unittest migration/full-skill-migration/test_sonar_ci_contract.py -v
git diff --check
git diff feat/construction-c12-runtime-acceptance-preflight...HEAD -- construction/STATUS.md
```

Expected: preflight tests PASS, whitespace clean, STATUS diff empty.

- [ ] **Step 6: Commit CI/docs**

```bash
git add .github/workflows/factory-construction-c13-skill-router.yml .github/workflows/factory-sonar-ci.yml migration/full-skill-migration/test_sonar_ci_contract.py construction/tests/test_c13_workflow_contract.py construction/README.md construction/docs/ARCHITECTURE.md
git commit -m "ci(construction): gate C13 router preflight separately"
```

- [ ] **Step 7: Push and open a draft stacked PR**

Push `feat/construction-c13-skill-router-preflight` and open a draft PR with base `feat/construction-c12-runtime-acceptance-preflight`.

Require C13 router preflight, skill validator, relevant C9/C10/C12 regressions, Governance and Sonar green. Require only final acceptance to remain fail-closed with:

`C13_FINAL_ACCEPTANCE_BLOCKED: SUPER_HYPER_URGENT_FINAL_CONSTRUCTION_PHYSICAL_ACCEPTANCE`

Do not merge or advance STATUS before C11 and C12 are accepted in the authoritative physical campaign.
