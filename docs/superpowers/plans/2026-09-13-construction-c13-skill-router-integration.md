# Construction C13 Skill/Router Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a deterministic C13 capability index and validator that integrates Construction capabilities into the existing Factory router without creating a second authority or falsely promoting preflight readiness to final acceptance.

**Architecture:** Keep `skills/ROUTER.md`, `skills/VERSION-AUTHORITY.md`, `skills/USER-GUIDED-WORKFLOW.md` and `engineering/REPO-ROUTING.md` as canonical authorities. Add a small machine-readable capability index, pure-Python resolver/validator and Construction-focused tests. C13 consumes C12 readiness/acceptance semantics and propagates the final blocker fail-closed.

**Tech Stack:** Python 3.11, JSON, unittest, existing skill repository validator, existing Construction C9/C10 surfaces, GitHub Actions, Sonar/Governance.

**Spec:** `docs/superpowers/specs/2026-09-13-construction-c13-skill-router-integration-design.md`

## Global Constraints

- Preserve `skills/ROUTER.md` as the canonical human-facing router; do not create a second router.
- Preserve `engineering/REPO-ROUTING.md` as the repository/authority boundary contract.
- Preserve `skills/VERSION-AUTHORITY.md` for exact-version proof and fail-closed provider behavior.
- Preserve `skills/USER-GUIDED-WORKFLOW.md` for one-verifiable-manual-step-at-a-time routing.
- Do not create one skill per Construction phase or provider.
- Provider presence does not prove provider API support.
- `REFERENCE_ONLY` material cannot become active authority through C13.
- Readiness and acceptance are separate axes.
- Exact final blocker is `SUPER_HYPER_URGENT_FINAL_CONSTRUCTION_PHYSICAL_ACCEPTANCE`.
- C11/C12 preflight readiness cannot be promoted to accepted.
- `construction/STATUS.md` must not change during C13 preflight.
- C13 branch is stacked on the exact validated C12 preflight branch and PR base is the C12 branch.

---

### Task 1: Establish the stacked C13 branch and RED routing contracts

**Files:**
- Create branch: `feat/construction-c13-skill-router-preflight`
- Create: `construction/tests/test_c13_skill_router_integration.py`

**Interfaces:**
- Consumes: C12 runtime acceptance contract and existing skill/router authority files.
- Produces expected public API names in `skills/scripts/capability_router.py`: `CapabilityIndexError`, `load_capability_index`, `validate_capability_index`, `resolve_intent`.

- [ ] **Step 1: Create C13 branch from the exact validated C12 preflight head**

Run:
```bash
git switch feat/construction-c12-runtime-acceptance-preflight
git pull --ff-only
git switch -c feat/construction-c13-skill-router-preflight
```

Expected: C13 starts from the C12 preflight implementation and therefore can validate the real C12 entrypoint/path.

- [ ] **Step 2: Write RED tests for authority preservation and exact blocker propagation**

Create `construction/tests/test_c13_skill_router_integration.py` with tests equivalent to:

```python
from pathlib import Path
from skills.scripts.capability_router import (
    load_capability_index,
    resolve_intent,
    validate_capability_index,
)

ROOT = Path(__file__).resolve().parents[2]
INDEX = ROOT / "skills/capabilities/capability-index.json"
BLOCKER = "SUPER_HYPER_URGENT_FINAL_CONSTRUCTION_PHYSICAL_ACCEPTANCE"


def test_c11_and_c12_routes_are_preflight_ready_but_blocked():
    index = load_capability_index(INDEX)
    c11 = resolve_intent(index, "construction.complex_modded_golden")
    c12 = resolve_intent(index, "construction.runtime_acceptance")
    assert (c11["readiness"], c11["acceptance"], c11["blocker"]) == (
        "PREFLIGHT_READY", "BLOCKED", BLOCKER
    )
    assert (c12["readiness"], c12["acceptance"], c12["blocker"]) == (
        "PREFLIGHT_READY", "BLOCKED", BLOCKER
    )


def test_unknown_intent_fails_closed():
    index = load_capability_index(INDEX)
    result = resolve_intent(index, "provider.unproven.magic_api")
    assert result["readiness"] == "UNAVAILABLE"
    assert result["acceptance"] == "BLOCKED"
```

Add tests that router/version/user-guided/repo-routing files remain canonical and that no C13 file declares a replacement router authority.

- [ ] **Step 3: Add RED cases for duplicate intents and `REFERENCE_ONLY` promotion**

Mutate an in-memory index and assert `validate_capability_index()` returns stable errors for:

- duplicate `capability_id`;
- duplicate intent;
- unknown authority;
- missing entrypoint path;
- active route into `migration/provenance/historical-skills/`;
- `ACCEPTED` capability with an active blocker;
- provider route marked available without exact-version proof semantics.

- [ ] **Step 4: Run RED tests**

```bash
python3 -m unittest construction/tests/test_c13_skill_router_integration.py -v
```

Expected: FAIL because `skills/scripts/capability_router.py` and `skills/capabilities/capability-index.json` do not exist.

- [ ] **Step 5: Commit RED tests**

```bash
git add construction/tests/test_c13_skill_router_integration.py
git commit -m "test(construction): define C13 router integration contracts"
```

---

### Task 2: Add the machine-readable capability schema and canonical index

**Files:**
- Create: `skills/capabilities/capability-index.schema.json`
- Create: `skills/capabilities/capability-index.json`

**Interfaces:**
- Capability declaration fields:
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

- [ ] **Step 1: Define the schema**

Require exact root target:

```json
{
  "minecraft": "1.21.1",
  "loader": "neoforge",
  "neoforge": "21.1.248",
  "java": 21
}
```

Require unique capability IDs/intents at validator level and closed objects (`additionalProperties: false`).

- [ ] **Step 2: Populate the canonical index with existing authorities**

Create entries at minimum for:

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

C11 and C12 must be `PREFLIGHT_READY / BLOCKED` with the exact final blocker. C9-backed offline capabilities that are already accepted may be `AVAILABLE / ACCEPTED` within their documented contract. Cross-domain routing entries that represent an authority boundary rather than a completion gate may use `AVAILABLE / NOT_APPLICABLE`.

- [ ] **Step 3: Encode forbidden promotions explicitly**

Use stable tokens such as:

```json
[
  "NO_PREFLIGHT_TO_FINAL_ACCEPTANCE",
  "NO_STATIC_TO_RUNTIME_CONFIRMED",
  "NO_OFFLINE_VISUAL_TO_RUNTIME_FIDELITY",
  "NO_PROVIDER_PRESENCE_TO_API_SUPPORT",
  "NO_REFERENCE_ONLY_TO_ACTIVE_AUTHORITY"
]
```

Only include rules relevant to each capability; do not invent provider-specific support.

- [ ] **Step 4: Commit schema/index**

```bash
git add skills/capabilities/capability-index.schema.json skills/capabilities/capability-index.json
git commit -m "feat(skills): add Construction capability index"
```

---

### Task 3: Implement pure deterministic capability validation and routing

**Files:**
- Create: `skills/scripts/capability_router.py`
- Modify: `construction/tests/test_c13_skill_router_integration.py`

**Interfaces:**
- `CapabilityIndexError(RuntimeError)`
- `load_capability_index(path: Path) -> dict[str, object]`
- `validate_capability_index(index: object, *, repo_root: Path | None = None) -> list[str]`
- `resolve_intent(index: object, intent: str) -> dict[str, object]`

- [ ] **Step 1: Implement closed enum/constants**

```python
TARGET = {"minecraft": "1.21.1", "loader": "neoforge", "neoforge": "21.1.248", "java": 21}
READINESS = frozenset({"AVAILABLE", "PREFLIGHT_READY", "UNAVAILABLE"})
ACCEPTANCE = frozenset({"ACCEPTED", "BLOCKED", "NOT_APPLICABLE"})
VERSION_PROOF = frozenset({"NOT_REQUIRED", "REQUIRED_PHYSICAL", "REQUIRED_EXACT_API"})
FALLBACK = frozenset({"NONE", "EXPLICIT_EQUIVALENT_ONLY"})
FINAL_BLOCKER = "SUPER_HYPER_URGENT_FINAL_CONSTRUCTION_PHYSICAL_ACCEPTANCE"
```

- [ ] **Step 2: Implement entrypoint integrity validation**

For an entrypoint `path#symbol`, require the path to exist under repo root and require the source text to define the named function/tool symbol. Reject absolute paths, `..`, symlink escape and paths outside repo root.

Directory entrypoints such as `art/` or `construction/providers` must exist and remain inside repo root.

- [ ] **Step 3: Implement semantic validation**

Reject:

```python
if capability["acceptance"] == "ACCEPTED" and capability["blocker"] is not None:
    errors.append(...)
if capability["readiness"] == "UNAVAILABLE" and capability["acceptance"] == "ACCEPTED":
    errors.append(...)
if capability["version_proof"] == "REQUIRED_EXACT_API" and "NO_PROVIDER_PRESENCE_TO_API_SUPPORT" not in capability["forbidden_promotions"]:
    errors.append(...)
```

Reject duplicate IDs/intents, unknown authorities and active entrypoints under `migration/provenance/historical-skills/`.

- [ ] **Step 4: Implement `resolve_intent`**

For one exact matching intent, return a copy of the capability declaration.

For no match, return the stable fail-closed sentinel:

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

The validator must prevent duplicate intents, so `resolve_intent` never silently picks between ambiguous capabilities.

- [ ] **Step 5: Run focused tests**

```bash
python3 -m unittest construction/tests/test_c13_skill_router_integration.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit router core**

```bash
git add skills/scripts/capability_router.py construction/tests/test_c13_skill_router_integration.py
git commit -m "feat(skills): validate and resolve Factory capabilities"
```

---

### Task 4: Integrate the capability index with existing router authorities without replacing them

**Files:**
- Modify: `skills/ROUTER.md`
- Modify: `engineering/REPO-ROUTING.md`
- Modify: `skills/README.md`
- Modify: `construction/tests/test_c13_skill_router_integration.py`

**Interfaces:**
- Existing router files remain canonical prose authorities.
- New docs only reference `skills/capabilities/capability-index.json` as machine-readable routing metadata.

- [ ] **Step 1: Add RED assertions for non-replacement semantics**

Assert docs contain language equivalent to:

```text
skills/ROUTER.md remains the canonical router
capability-index.json is machine-readable routing metadata, not a second authority
readiness does not imply acceptance
```

Assert `REFERENCE_ONLY` remains non-active.

- [ ] **Step 2: Update `skills/ROUTER.md` narrowly**

Add one section explaining how the capability index supplements routing decisions and preserves version/API evidence requirements. Do not rewrite existing Engineering/Art/VFX sections.

- [ ] **Step 3: Update `engineering/REPO-ROUTING.md` narrowly**

Add the machine-readable index to the shared reusable routing metadata row/rules while preserving runtime authority in individual mod repos.

- [ ] **Step 4: Update `skills/README.md`**

Document `capabilities/` and the validator/resolver entrypoint. Preserve the existing active/REFERENCE_ONLY classification.

- [ ] **Step 5: Run routing and skill repository validation**

```bash
python3 -m unittest construction/tests/test_c13_skill_router_integration.py -v
python3 skills/scripts/validate_skill_repository.py
```

Expected: PASS.

- [ ] **Step 6: Commit docs integration**

```bash
git add skills/ROUTER.md engineering/REPO-ROUTING.md skills/README.md construction/tests/test_c13_skill_router_integration.py
git commit -m "docs(skills): integrate Construction capability routing"
```

---

### Task 5: Add C13 CI, downstream regressions and final-acceptance guard

**Files:**
- Create: `.github/workflows/factory-construction-c13-skill-router.yml`
- Create: `construction/tests/test_c13_workflow_contract.py`
- Modify: `.github/workflows/factory-sonar-ci.yml`
- Modify: `migration/full-skill-migration/test_sonar_ci_contract.py`

**Interfaces:**
- Job `c13-router-preflight` may pass.
- Job `c13-final-acceptance` remains fail-closed while C11/C12 are blocked.

- [ ] **Step 1: Write workflow contract RED tests**

Require the final-acceptance guard to read the C11 blocker state and a C12 preflight/final state source, then fail before any completion claim when the final blocker is active:

```python
blocker = "SUPER_HYPER_URGENT_FINAL_CONSTRUCTION_PHYSICAL_ACCEPTANCE"
if c11_state.get("status") == blocker and c11_state.get("blocks_c13_final_acceptance") is True:
    raise SystemExit(f"C13_FINAL_ACCEPTANCE_BLOCKED: {blocker}")
```

Do not treat C12 `PREFLIGHT_READY` as accepted.

- [ ] **Step 2: Create `c13-router-preflight` workflow job**

Run:

```bash
python3 -m unittest construction/tests/test_c13_skill_router_integration.py -v
python3 -m unittest construction/tests/test_c13_workflow_contract.py -v
python3 skills/scripts/validate_skill_repository.py
python3 -m unittest construction/tests/test_c9_agent_mcp.py construction/tests/test_c9_mcp_stdio.py -v
python3 -m unittest construction/tests/test_c10_provider_profiles.py construction/tests/test_c10_handoff_request.py construction/tests/test_c10_handoff_receipt.py -v
python3 -m unittest construction/tests/test_c12_runtime_acceptance.py construction/tests/test_c12_runtime_acceptance_security.py -v
python3 -m unittest migration/full-skill-migration/test_sonar_ci_contract.py -v
git diff --check
```

- [ ] **Step 3: Add `c13-final-acceptance` state-first guard**

Depend on preflight and fail with the exact final blocker while C11/C12 final prerequisites are not accepted.

- [ ] **Step 4: Extend Sonar coverage without removing earlier targets**

Add `skills/scripts/capability_router.py`, C13 tests and any new capability validator paths. Preserve I9, C10, C11 and C12 coverage.

- [ ] **Step 5: Run workflow/Sonar tests**

```bash
python3 -m unittest construction/tests/test_c13_workflow_contract.py -v
python3 -m unittest migration/full-skill-migration/test_sonar_ci_contract.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit CI**

```bash
git add .github/workflows/factory-construction-c13-skill-router.yml .github/workflows/factory-sonar-ci.yml migration/full-skill-migration/test_sonar_ci_contract.py construction/tests/test_c13_workflow_contract.py
git commit -m "ci(construction): gate C13 router preflight separately"
```

---

### Task 6: Document C13 Construction boundary and validate the stacked PR

**Files:**
- Modify: `construction/README.md`
- Modify: `construction/docs/ARCHITECTURE.md`
- Do not modify: `construction/STATUS.md`

**Interfaces:**
- Docs must show C13 as integration over existing router/authorities, with readiness distinct from acceptance.

- [ ] **Step 1: Update Construction README/ARCHITECTURE**

Document the capability index, preserved router authorities, C11/C12 blocker propagation, no provider-presence-to-API promotion, and final closeout ordering.

- [ ] **Step 2: Run the complete C13 contract set**

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

Expected: all preflight/contract tests PASS.

- [ ] **Step 3: Verify STATUS is unchanged**

```bash
git diff feat/construction-c12-runtime-acceptance-preflight...HEAD -- construction/STATUS.md
```

Expected: empty diff.

- [ ] **Step 4: Commit docs**

```bash
git add construction/README.md construction/docs/ARCHITECTURE.md
git commit -m "docs(construction): document C13 router integration boundary"
```

- [ ] **Step 5: Push and open a draft stacked PR**

Push `feat/construction-c13-skill-router-preflight` and open a draft PR with base `feat/construction-c12-runtime-acceptance-preflight`.

PR body must state: C13 implementation/preflight only; no C13 final acceptance; C11/C12 remain blocked; no STATUS advancement.

- [ ] **Step 6: Validate exact PR head**

Require router preflight, skill validator, relevant C9/C10/C12 regressions, Governance and Sonar to pass. Require only `c13-final-acceptance` to remain fail-closed with:

`C13_FINAL_ACCEPTANCE_BLOCKED: SUPER_HYPER_URGENT_FINAL_CONSTRUCTION_PHYSICAL_ACCEPTANCE`

Do not merge before C11 and C12 can be accepted in the authoritative final physical campaign.
