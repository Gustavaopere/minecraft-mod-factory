# CI Queue Control Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduce GitHub Actions queue amplification while preserving fail-closed validation, exact-head evidence on `main`, and all existing domain acceptance semantics.

**Architecture:** Introduce a closed machine-readable classification of every canonical `factory-*.yml` workflow, a deterministic validator under the Engineering control plane, symmetric `push.paths`/`pull_request.paths` for scoped read-only workflows, and safe workflow-level concurrency that deduplicates only non-main read-only revisions. Governance remains the global enforcement point; Sonar remains a global quality gate; the write-capable full-skill materializer remains exempt from automatic cancellation.

**Tech Stack:** GitHub Actions YAML, Python 3.12 standard library, JSON policy manifest, `unittest`, existing Factory Governance workflow.

**Spec:** `docs/superpowers/specs/2026-09-13-ci-queue-control-design.md`

## Global Constraints

- Base authority is `main@8981771689535288e4792d1cba17a95b59c37a03` unless `main` advances; if it advances, re-audit before applying changes.
- Physical modlist authority remains the supplied 595-entry snapshot with SHA-256 `7c0a23d6013101383d196526e4b6ba6940fb54a0fed10eaed5956ab015cfcc00`.
- Governance and Sonar remain global read-only gates.
- `factory-full-skill-materialize.yml` is `MUTATING_EXEMPT`; do not add automatic `cancel-in-progress` to it.
- Do not alter Mod Engineering runtime contracts, Construction acceptance semantics, Repo Textura asset/provider semantics, or milestone completion state.
- Never treat skipped checks as PASS.
- Preserve every legitimately scheduled `main` run as independent exact-head evidence.
- Do not edit concurrent PR branches #100, #102, #103, #105 or #106 directly.
- Apply workflow changes in one batch commit after tests/validator surfaces exist, to avoid multiplying rollout fan-out.

---

### Task 1: Add the closed CI queue-control policy and RED contract tests

**Files:**
- Create: `engineering/tooling/ci/queue-control-policy.json`
- Create: `engineering/tests/test_ci_queue_control.py`

**Interfaces:**
- Consumes: canonical workflows under `.github/workflows/factory-*.yml`.
- Produces: JSON manifest with top-level `schema_version`, `classes`, and `workflows`; test helpers `load_policy()`, `factory_workflow_paths()`, and assertions that later validator code must satisfy.

- [ ] **Step 1: Create the policy manifest with all current canonical Factory workflows classified exactly once**

Use this schema shape:

```json
{
  "schema_version": 1,
  "classes": ["GLOBAL_READ_ONLY", "SCOPED_READ_ONLY", "MUTATING_EXEMPT"],
  "workflows": {
    ".github/workflows/factory-e1-s1-governance.yml": {"class": "GLOBAL_READ_ONLY"},
    ".github/workflows/factory-sonar-ci.yml": {"class": "GLOBAL_READ_ONLY"},
    ".github/workflows/factory-full-skill-materialize.yml": {"class": "MUTATING_EXEMPT"}
  }
}
```

Then enumerate every remaining canonical `factory-*.yml` file from `main` as `SCOPED_READ_ONLY`. No wildcard entries are allowed; the manifest is intentionally closed.

- [ ] **Step 2: Write failing tests for policy closure and known classifications**

Add tests equivalent to:

```python
class QueueControlPolicyTest(unittest.TestCase):
    def test_policy_is_closed_over_factory_workflows(self) -> None:
        policy = load_policy()
        actual = {str(path.relative_to(ROOT)).replace("\\", "/") for path in factory_workflow_paths()}
        declared = set(policy["workflows"])
        self.assertEqual(declared, actual)

    def test_global_and_mutating_classifications_are_exact(self) -> None:
        policy = load_policy()["workflows"]
        self.assertEqual(policy[".github/workflows/factory-e1-s1-governance.yml"]["class"], "GLOBAL_READ_ONLY")
        self.assertEqual(policy[".github/workflows/factory-sonar-ci.yml"]["class"], "GLOBAL_READ_ONLY")
        self.assertEqual(policy[".github/workflows/factory-full-skill-materialize.yml"]["class"], "MUTATING_EXEMPT")
```

- [ ] **Step 3: Add RED tests for the current broken trigger/concurrency topology**

The tests must invoke the validator entry point that will be created in Task 2 and assert the current branch fails before workflow transformation. Required failure categories:

```python
self.assertIn("missing push.paths", result.errors_text)
self.assertIn("missing canonical concurrency", result.errors_text)
```

Use exact workflow names from the current known set so the RED state is deterministic.

- [ ] **Step 4: Run the queue-control tests and prove RED**

Run:

```bash
python3 -m unittest engineering/tests/test_ci_queue_control.py -v
```

Expected: FAIL because `validate_queue_control.py` does not yet exist and/or the known workflows still lack required `push.paths` and concurrency.

- [ ] **Step 5: Commit the RED policy/tests**

```bash
git add engineering/tooling/ci/queue-control-policy.json engineering/tests/test_ci_queue_control.py
git commit -m "test(ci): define queue control policy contracts"
```

---

### Task 2: Implement the deterministic fail-closed queue-control validator

**Files:**
- Create: `engineering/tooling/ci/validate_queue_control.py`
- Modify: `engineering/tests/test_ci_queue_control.py`

**Interfaces:**
- Consumes: `queue-control-policy.json` and `.github/workflows/factory-*.yml`.
- Produces: `ValidationResult(errors: tuple[str, ...])`, `validate_repository(root: Path) -> ValidationResult`, and CLI exit status `0` on PASS / `1` on any violation.

- [ ] **Step 1: Define the validator result type and policy loader**

Implement:

```python
@dataclass(frozen=True)
class ValidationResult:
    errors: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.errors

    @property
    def errors_text(self) -> str:
        return "\n".join(self.errors)


def load_policy(path: Path) -> dict[str, object]:
    ...
```

Fail on malformed JSON, unknown class values, duplicate logical entries, unsupported schema version, or missing required keys.

- [ ] **Step 2: Implement a bounded YAML-text parser for the controlled workflow trigger surface**

Do not add PyYAML. Parse only the repository-controlled top-level blocks required by this policy:

- `on:`
- `push:` / `pull_request:`
- nested `branches:` / `types:` / `paths:` string lists
- top-level `permissions:`
- top-level `concurrency:`

Expose:

```python
@dataclass(frozen=True)
class WorkflowTrigger:
    push_branches: tuple[str, ...]
    push_paths: tuple[str, ...]
    pull_request_paths: tuple[str, ...]
    has_pull_request: bool
    has_push: bool


def parse_workflow_contract(text: str, workflow_path: str) -> WorkflowContract:
    ...
```

Unsupported indentation/structure relevant to these fields must produce a validation error instead of silently returning an empty set.

- [ ] **Step 3: Implement policy closure and trigger symmetry checks**

`validate_repository(root)` must verify:

```text
- actual factory-*.yml set == manifest workflow set
- GLOBAL_READ_ONLY: no push.paths and no pull_request.paths domain filtering
- SCOPED_READ_ONLY: if push includes main, push.paths exists
- SCOPED_READ_ONLY: push.paths == pull_request.paths unless manifest entry explicitly carries allowed_path_difference=true
- MUTATING_EXEMPT: excluded from read-only concurrency requirement
```

No `allowed_path_difference` exception should exist in the initial manifest unless a concrete workflow proves one is necessary during implementation.

- [ ] **Step 4: Implement canonical concurrency checks**

For every read-only workflow require the exact semantic expressions:

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}-${{ github.ref == 'refs/heads/main' && github.run_id || 'dedupe' }}
  cancel-in-progress: ${{ github.ref != 'refs/heads/main' }}
```

Whitespace may vary, but expression values must be exact after trimming/quote normalization.

- [ ] **Step 5: Implement docs-only steady-state simulation**

Add a deterministic matcher for the simple path patterns used by the Factory (`literal`, `dir/**`, and repository workflow-file literals are sufficient for current policy). Expose:

```python
def workflows_for_changed_paths(root: Path, changed_paths: Sequence[str]) -> tuple[str, ...]:
    ...
```

Assert `changed_paths=("plans/example.md",)` produces exactly:

```python
(
    ".github/workflows/factory-e1-s1-governance.yml",
    ".github/workflows/factory-sonar-ci.yml",
)
```

- [ ] **Step 6: Add negative tests**

Use temporary repositories/workflow text fixtures to prove failures for:

- unclassified workflow;
- manifest entry pointing to missing file;
- missing `push.paths`;
- mismatched push/PR paths;
- missing concurrency on read-only workflow;
- concurrency accidentally canceling `main`;
- global workflow accidentally domain-filtered;
- mutating workflow incorrectly forced into read-only cancellation;
- malformed relevant trigger block.

- [ ] **Step 7: Run tests; expect workflow-topology failures only**

Run:

```bash
python3 -m unittest engineering/tests/test_ci_queue_control.py -v
```

Expected: validator implementation tests PASS, while repository-state tests still FAIL specifically for existing workflow trigger/concurrency violations.

- [ ] **Step 8: Commit validator implementation**

```bash
git add engineering/tooling/ci/validate_queue_control.py engineering/tests/test_ci_queue_control.py
git commit -m "feat(ci): add fail-closed queue control validator"
```

---

### Task 3: Add symmetric `push.paths` to the 31 unfiltered domain workflows

**Files:**
- Modify exactly the 31 workflows enumerated in Section 3.2 of the spec.

**Interfaces:**
- Consumes: each workflow's existing `pull_request.paths` list.
- Produces: the same path set under that workflow's existing `push` trigger; no domain list broadening or narrowing.

- [ ] **Step 1: Transform the 13 unfiltered Art workflows**

For each file, copy its existing `pull_request.paths` list under `push.paths` while preserving existing push branches:

```text
factory-art-m4-standards-core.yml
factory-art-m4-templates.yml
factory-art-m4-visual-style-provenance.yml
factory-art-pr5-generic-animation-core.yml
factory-art-pr6-geckolib4-adapter.yml
factory-art-pr7-azurelib3-adapter.yml
factory-art-pr8-neoforge-native-animation.yml
factory-art-pr9-easy-model-entities.yml
factory-art-pr10-emf-cem.yml
factory-art-pr11-animated-java.yml
factory-art-pr12-player-profiles.yml
factory-art-pr13-epicfight-blender-handoff.yml
factory-art-pr14-unified-qa-export-manifest.yml
```

- [ ] **Step 2: Transform the 12 unfiltered Construction workflows**

Apply the same exact-list copy to:

```text
factory-construction-c0-foundation.yml
factory-construction-c1-minebench-reference.yml
factory-construction-c1-schematica-upstream.yml
factory-construction-c2-build-ir.yml
factory-construction-c3-vanilla-golden.yml
factory-construction-c4-modpack-registry.yml
factory-construction-c5-modded-palette.yml
factory-construction-c6-sponge-v3.yml
factory-construction-c7-architecture-qa.yml
factory-construction-c8-visual-qa.yml
factory-construction-c9-agent-mcp.yml
factory-construction-c10-external-providers.yml
```

- [ ] **Step 3: Transform the 6 unfiltered Engineering workflows**

Apply the same exact-list copy to:

```text
factory-engineering-i1-foundation.yml
factory-engineering-i2-modlist-catalog.yml
factory-engineering-i3-mod-scaffolder.yml
factory-engineering-i4-validators.yml
factory-engineering-i8-feature-generator.yml
factory-engineering-i9-machine-foundation.yml
```

- [ ] **Step 4: Run policy tests and confirm missing-path failures disappear**

```bash
python3 -m unittest engineering/tests/test_ci_queue_control.py -v
```

Expected: no `missing push.paths` or push/PR path mismatch failures; concurrency failures may remain until Task 4.

---

### Task 4: Add safe non-main concurrency to all read-only Factory workflows

**Files:**
- Modify: all `GLOBAL_READ_ONLY` and `SCOPED_READ_ONLY` workflows enumerated by the policy manifest.
- Do not modify concurrency in: `.github/workflows/factory-full-skill-materialize.yml`.

**Interfaces:**
- Consumes: policy class of each workflow.
- Produces: canonical top-level concurrency block for every read-only workflow.

- [ ] **Step 1: Add the canonical block after `on:` and before `permissions:` (or equivalent top-level location)**

Use exactly:

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}-${{ github.ref == 'refs/heads/main' && github.run_id || 'dedupe' }}
  cancel-in-progress: ${{ github.ref != 'refs/heads/main' }}
```

Do this for Governance, Sonar, all Art read-only workflows, all Construction workflows, Engineering I1-I9 workflows present on `main`, full-skill migration validation, Blockbench base-safe/install/native-golden, and every other manifest entry classified read-only.

- [ ] **Step 2: Prove the mutating materializer is untouched by cancellation policy**

Test must assert:

```python
materializer = (ROOT / ".github/workflows/factory-full-skill-materialize.yml").read_text(encoding="utf-8")
self.assertNotIn("cancel-in-progress:", materializer)
```

- [ ] **Step 3: Run the complete queue-control tests**

```bash
python3 -m unittest engineering/tests/test_ci_queue_control.py -v
```

Expected: PASS for policy closure, trigger symmetry, concurrency safety, and docs-only simulation.

- [ ] **Step 4: Commit Tasks 3-4 as one workflow batch**

Use one tree/commit batch containing every workflow change:

```bash
git add .github/workflows/factory-*.yml
git commit -m "ci: scope and deduplicate factory validations"
```

---

### Task 5: Integrate queue-control enforcement into global Governance

**Files:**
- Modify: `.github/workflows/factory-e1-s1-governance.yml`
- Modify: `engineering/tests/test_e1_s1_governance.py`
- Test: `engineering/tests/test_ci_queue_control.py`

**Interfaces:**
- Consumes: `validate_queue_control.py` and queue-control unit tests.
- Produces: always-on enforcement on every Governance execution.

- [ ] **Step 1: Write the Governance RED assertion**

In `test_e1_s1_governance.py`, require the workflow to contain both commands:

```text
python3 -m unittest engineering/tests/test_ci_queue_control.py -v
python3 engineering/tooling/ci/validate_queue_control.py
```

Run:

```bash
python3 -m unittest engineering/tests/test_e1_s1_governance.py -v
```

Expected: FAIL before editing Governance.

- [ ] **Step 2: Add Governance steps**

Add after existing E1 S1 regression tests and before whitespace validation:

```yaml
      - name: Validate CI queue-control contracts
        run: python3 -m unittest engineering/tests/test_ci_queue_control.py -v

      - name: Validate CI queue-control policy
        run: python3 engineering/tooling/ci/validate_queue_control.py
```

- [ ] **Step 3: Run Governance and queue-control tests**

```bash
python3 -m unittest engineering/tests/test_e1_s1_governance.py engineering/tests/test_ci_queue_control.py -v
python3 engineering/tooling/validate-e1-s1-governance.py
python3 engineering/tooling/ci/validate_queue_control.py
```

Expected: all PASS.

- [ ] **Step 4: Commit Governance integration**

```bash
git add .github/workflows/factory-e1-s1-governance.yml engineering/tests/test_e1_s1_governance.py
git commit -m "ci(governance): enforce queue control policy"
```

---

### Task 6: Full verification, diff audit, and pull request

**Files:**
- No new production files expected; only corrections discovered by verification.

**Interfaces:**
- Consumes: complete branch implementation.
- Produces: exact-head evidence suitable for PR review.

- [ ] **Step 1: Revalidate current `main` and concurrent work before finalizing**

Confirm the current base SHA and open PRs. If `main` advanced, compare and reconcile only relevant overlapping workflow/policy changes; do not overwrite concurrent feature work.

- [ ] **Step 2: Run all deterministic local repository gates available without a Minecraft runtime launch**

```bash
python3 -m unittest engineering/tests/test_ci_queue_control.py -v
python3 -m unittest engineering/tests/test_e1_s1_governance.py -v
python3 engineering/tooling/ci/validate_queue_control.py
python3 engineering/tooling/validate-e1-s1-governance.py
git diff --check main...HEAD
```

Expected: PASS / no whitespace errors.

- [ ] **Step 3: Audit changed-file scope**

Allowed changes are limited to:

```text
docs/superpowers/specs/2026-09-13-ci-queue-control-design.md
docs/superpowers/plans/2026-09-13-ci-queue-control.md
engineering/tooling/ci/queue-control-policy.json
engineering/tooling/ci/validate_queue_control.py
engineering/tests/test_ci_queue_control.py
engineering/tests/test_e1_s1_governance.py
.github/workflows/factory-*.yml
```

Any runtime, asset, provider, Construction acceptance, STATUS, or canonical plan change is a blocker.

- [ ] **Step 4: Verify policy cardinalities**

Require the validator/report to confirm current-main cardinality:

```text
TOTAL_FACTORY_WORKFLOWS=41
GLOBAL_READ_ONLY=2
SCOPED_READ_ONLY=38
MUTATING_EXEMPT=1
UNFILTERED_MAIN_DOMAIN_WORKFLOWS_AFTER_FIX=0
```

If concurrent `main` changes add/remove canonical workflows, update these expected cardinalities from the re-audited tree before claiming PASS.

- [ ] **Step 5: Open a dedicated PR**

Title:

```text
ci: control Factory workflow queue fan-out
```

Body must state:

```text
- root cause: 31 domain workflows lacked main-push path filters;
- fix: symmetric paths + safe non-main read-only concurrency;
- Governance/Sonar remain global;
- main executions are never canceled by concurrency;
- mutating materializer remains exempt;
- queue-control validator is fail-closed;
- no runtime/asset/provider/acceptance semantics changed;
- one-time rollout fan-out is expected because workflow files themselves changed.
```

- [ ] **Step 6: Require exact-head PR gates**

Before merge require:

```text
Factory E1 S1 Governance = SUCCESS
Factory Sonar CI = SUCCESS
Queue-control validator/tests = PASS within Governance
No unresolved review findings attributable to this PR
```

Do not merge on queued/pending evidence.

- [ ] **Step 7: Post-merge steady-state measurement**

Do not use the queue-control merge itself as the fan-out measurement. On the first natural later `plans/**`-only change, verify only Governance + Sonar are scheduled. Until such an event exists, record runtime steady-state evidence as pending rather than inventing PASS.
