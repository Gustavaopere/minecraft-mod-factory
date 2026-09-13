# CI Queue Control — Design

Date: 2026-09-13
Status: DESIGN APPROVED IN CHAT; IMPLEMENTATION NOT STARTED
Base: `main@8981771689535288e4792d1cba17a95b59c37a03`
Branch: `ci/queue-control`

## 1. Context

The Minecraft Mod Factory currently has a large GitHub Actions queue. The issue is not a failing validator or a specific broken runner request. The steady-state CI trigger topology causes many unrelated workflows to be scheduled for commits that do not touch their domain, and obsolete validation runs remain eligible to consume runners after newer commits supersede them.

This design changes only CI scheduling semantics. It does not change Mod Engineering contracts, Construction semantics, Repo Textura asset authority, runtime code, provider support, acceptance evidence, or milestone completion state.

The current physical modlist authority was rechecked before this design:

- declared top-level mod count: `595`;
- snapshot SHA-256: `7c0a23d6013101383d196526e4b6ba6940fb54a0fed10eaed5956ab015cfcc00`;
- physical loader entry: NeoForge `21.1.248` in the supplied snapshot.

This CI change does not reinterpret that snapshot or change target-version resolution policy.

## 2. Canonical-plan constraints

The Mod Engineering plan treats CI, validators, test harnesses and quality gates as control-plane responsibilities and requires implementation fronts to use TDD, real repository paths and verifiable gates.

The Repo Textura plan requires domain-specific CI after migration blocks and requires paths, links, tests and diffs to be validated before work advances.

Therefore queue reduction must not create fake green states, silently skip required validation, convert skipped checks into PASS, or remove exact-head evidence where that evidence is required.

## 3. Root-cause evidence

### 3.1 Exact docs-only fan-out

PR #104 was documentation-only under `plans/`. Its merge to `main` scheduled 33 workflows.

The audited `main` workflow set explains that number exactly:

- 31 scoped/domain workflows have `pull_request.paths` but have a `push` trigger for `main` without `push.paths`;
- `Factory E1 S1 Governance` is intentionally global;
- `Factory Sonar CI` is intentionally global.

`31 + 2 = 33`.

A docs-only merge therefore schedules every unfiltered domain workflow even when no domain input changed.

### 3.2 The 31 unfiltered domain workflows

Art / Repo Textura — 13:

1. `factory-art-m4-standards-core.yml`
2. `factory-art-m4-templates.yml`
3. `factory-art-m4-visual-style-provenance.yml`
4. `factory-art-pr5-generic-animation-core.yml`
5. `factory-art-pr6-geckolib4-adapter.yml`
6. `factory-art-pr7-azurelib3-adapter.yml`
7. `factory-art-pr8-neoforge-native-animation.yml`
8. `factory-art-pr9-easy-model-entities.yml`
9. `factory-art-pr10-emf-cem.yml`
10. `factory-art-pr11-animated-java.yml`
11. `factory-art-pr12-player-profiles.yml`
12. `factory-art-pr13-epicfight-blender-handoff.yml`
13. `factory-art-pr14-unified-qa-export-manifest.yml`

Construction — 12:

1. `factory-construction-c0-foundation.yml`
2. `factory-construction-c1-minebench-reference.yml`
3. `factory-construction-c1-schematica-upstream.yml`
4. `factory-construction-c2-build-ir.yml`
5. `factory-construction-c3-vanilla-golden.yml`
6. `factory-construction-c4-modpack-registry.yml`
7. `factory-construction-c5-modded-palette.yml`
8. `factory-construction-c6-sponge-v3.yml`
9. `factory-construction-c7-architecture-qa.yml`
10. `factory-construction-c8-visual-qa.yml`
11. `factory-construction-c9-agent-mcp.yml`
12. `factory-construction-c10-external-providers.yml`

Mod Engineering — 6:

1. `factory-engineering-i1-foundation.yml`
2. `factory-engineering-i2-modlist-catalog.yml`
3. `factory-engineering-i3-mod-scaffolder.yml`
4. `factory-engineering-i4-validators.yml`
5. `factory-engineering-i8-feature-generator.yml`
6. `factory-engineering-i9-machine-foundation.yml`

### 3.3 Existing good patterns

The repository already contains workflows that apply path filters symmetrically to `push` and `pull_request`, including:

- `factory-art-blockbench-base-safe.yml`;
- `factory-art-blockbench-install-artifact.yml`;
- `factory-art-geckolib4-native-golden.yml`;
- `factory-engineering-i5-test-harness.yml`;
- `factory-engineering-i6-asset-handoff.yml`;
- `factory-engineering-i7-provider-catalog.yml`;
- `factory-full-skill-migration-validation.yml`.

The solution should generalize this proven repository-local pattern instead of inventing a dispatcher architecture.

### 3.4 Obsolete-head consumption

Concurrent Engineering work showed older PR heads still executing after a newer head existed. Read-only validation runs for superseded non-main refs provide no final evidence for the latest head and can consume scarce runner capacity.

This is a separate root cause from trigger fan-out and requires controlled workflow-level concurrency.

## 4. Goals

1. A change should schedule domain workflows only when that workflow's declared inputs changed.
2. Newer non-main revisions should replace obsolete queued/running read-only validations for the same workflow/ref.
3. Every `main` run that is legitimately scheduled must remain independently preservable as exact-head evidence.
4. Governance and Sonar remain global gates.
5. No write-capable workflow is canceled automatically by the read-only deduplication policy.
6. A permanent validator must prevent trigger/concurrency drift from reintroducing the queue storm.
7. Existing domain acceptance semantics remain unchanged.

## 5. Non-goals

This change does not:

- merge I10 or Construction draft PRs;
- weaken C11/C12/C13 physical acceptance blockers;
- change Sonar quality thresholds;
- change required runtime/GameTest/dedicated-server evidence;
- change provider support or physical-modlist contents;
- centralize all workflows into a new reusable dispatcher;
- cancel current runs in bulk;
- treat `skipped` as `PASS`;
- modify the historical RPG repository.

## 6. Workflow classes

The policy classifies every canonical `factory-*.yml` workflow on `main` into one of three closed classes.

### 6.1 `GLOBAL_READ_ONLY`

Workflows:

- `factory-e1-s1-governance.yml`;
- `factory-sonar-ci.yml`.

Rules:

- continue to run for every relevant PR/main push;
- do not receive domain `paths` filters;
- receive non-main deduplication concurrency;
- every scheduled `main` run remains unique and is never replaced by concurrency.

### 6.2 `SCOPED_READ_ONLY`

All read-only Art, Construction, Engineering and full-skill validation workflows other than the two global workflows.

Rules:

- `pull_request.paths` remains the declared dependency scope;
- `push.paths` must exist for workflows that push to `main`;
- for a scoped validation workflow, `push.paths` and `pull_request.paths` must be semantically equal unless an explicit reviewed exception exists in the policy manifest;
- the workflow file itself remains in its own path set so edits to validation logic self-validate;
- non-main obsolete revisions are deduplicated;
- `main` executions are never deduplicated away.

### 6.3 `MUTATING_EXEMPT`

Initial workflow:

- `factory-full-skill-materialize.yml`.

Reason:

- it has `contents: write`;
- it creates a commit and pushes to `feat/full-skill-migration`.

It is already path-scoped and is not part of the current `main` fan-out. It is exempt from automatic cancel-in-progress behavior in this change. Any future serialization policy for mutating workflows requires its own design because interruption can leave externally visible partial workflow effects.

## 7. Path-filter policy

For each of the 31 identified unfiltered domain workflows, copy the existing `pull_request.paths` dependency set to `push.paths` under the existing push trigger.

Do not broaden or narrow the domain dependency set during this change. The purpose is trigger symmetry, not a new dependency analysis.

Example transformation:

```yaml
on:
  push:
    branches:
      - main
      - feature-branch
    paths:
      - 'domain/path/**'
      - '.github/workflows/this-workflow.yml'
  pull_request:
    paths:
      - 'domain/path/**'
      - '.github/workflows/this-workflow.yml'
```

For workflows whose `pull_request` event also declares `branches: [main]`, preserve that branch filter unchanged.

## 8. Concurrency policy

GitHub Actions supports workflow-level concurrency groups and conditional `cancel-in-progress`. Official documentation also states that a shared concurrency group normally keeps at most one pending run, so `main` must not share a stable group when every exact-head run must be preserved.

For `GLOBAL_READ_ONLY` and `SCOPED_READ_ONLY` workflows, use a group that is stable for non-main refs but unique for `main`:

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}-${{ github.ref == 'refs/heads/main' && github.run_id || 'dedupe' }}
  cancel-in-progress: ${{ github.ref != 'refs/heads/main' }}
```

Semantics:

- PR ref: stable group, stale pending/running revision is replaced by the newest revision;
- feature-branch push: stable group, stale pending/running revision is replaced by the newest revision;
- `main`: `github.run_id` makes the group unique, so an older `main` run is not canceled merely because a newer main commit exists;
- workflow name is part of the group, so one workflow cannot cancel a different workflow.

The `MUTATING_EXEMPT` workflow does not use this policy.

## 9. Machine-readable policy and validator

Implementation will add a closed policy manifest under the existing Engineering control-plane tree and a fail-closed validator.

Expected surfaces:

- `engineering/tooling/ci/queue-control-policy.json`;
- `engineering/tooling/ci/validate_queue_control.py`;
- `engineering/tests/test_ci_queue_control.py`.

The manifest must enumerate every canonical `factory-*.yml` workflow and its class. A newly added workflow that is not classified must fail validation.

The validator must verify at minimum:

1. every canonical Factory workflow is classified exactly once;
2. no policy entry points to a missing workflow;
3. every `SCOPED_READ_ONLY` workflow that pushes to `main` has `push.paths`;
4. scoped `push.paths` equals scoped `pull_request.paths`, unless an explicit manifest exception exists;
5. `GLOBAL_READ_ONLY` workflows are not accidentally domain-filtered;
6. every read-only workflow contains the canonical concurrency semantics;
7. every `MUTATING_EXEMPT` workflow is excluded from read-only cancellation enforcement;
8. the known docs-only synthetic path set `plans/**` resolves to exactly the two global workflows under the steady-state policy;
9. malformed or unsupported trigger structures fail closed instead of being silently accepted.

The validator will use repository-local deterministic parsing sufficient for the controlled workflow subset and must have negative unit tests. It will not introduce a runtime dependency into produced mods.

## 10. Governance integration

`Factory E1 S1 Governance` is the natural global enforcement point.

Its job will additionally run:

- the CI queue-control unit tests;
- the queue-control policy validator.

This keeps the policy checked on every PR/main push without creating another always-on workflow that would itself add to queue pressure.

Governance must remain read-only.

## 11. TDD sequence

Implementation must follow RED -> GREEN -> REFACTOR/VERIFY.

RED:

- add policy/parser tests first;
- run them against the pre-fix workflow topology;
- require deterministic failures showing the missing `push.paths` set and missing read-only concurrency policy.

GREEN:

- add `push.paths` to the 31 known workflows without changing their dependency lists;
- add canonical concurrency to all read-only Factory workflows covered by the policy;
- integrate the validator into Governance;
- rerun the queue-control tests until green.

VERIFY:

- run governance regressions;
- run relevant Engineering regressions for the new validator/tooling;
- run whitespace checks;
- review the complete diff for accidental domain logic changes;
- verify the PR-associated workflow set on the exact head;
- require Sonar Quality Gate success.

## 12. Rollout behavior

Changing many workflow files is itself a relevant workflow change. The queue-control rollout PR can therefore schedule many checks once because each workflow correctly includes its own workflow file in its dependency set.

This one-time rollout fan-out is expected and must not be misclassified as a steady-state failure.

To avoid multiplying that one-time fan-out:

- create the implementation as a small number of batch commits using Git tree/commit operations rather than one API commit per workflow file;
- do not push partially transformed workflow sets;
- after the first complete implementation head exists, subsequent corrections on the same branch are deduplicated by the new non-main concurrency policy.

## 13. Verification and acceptance

### 13.1 Static acceptance before merge

The exact PR head must prove:

- policy manifest closed over every Factory workflow;
- validator PASS;
- unit tests PASS;
- Governance PASS;
- Sonar Quality Gate PASS;
- no runtime/asset/provider semantics changed;
- no unapproved changes to concurrent I10/Construction branches.

### 13.2 Steady-state trigger simulation

Unit tests must simulate changed-path sets and assert at least:

- `plans/**` only -> Governance + Sonar;
- Engineering-only change -> Governance + Sonar + the Engineering workflows whose declared paths match;
- Art-only change -> Governance + Sonar + matching Art workflows;
- Construction-only change -> Governance + Sonar + matching Construction workflows;
- workflow-file change -> that workflow self-validates plus global gates.

### 13.3 Runtime acceptance after merge

The queue-control merge itself is not a valid measurement of steady-state fan-out because it changes workflow files.

The first natural docs/plans-only commit after merge should be observed and must schedule only the two global gates, unless that commit also changes a workflow/policy input.

Do not fabricate a PASS if no representative post-merge event has occurred yet; record the runtime observation as pending until real evidence exists.

## 14. Concurrent-work boundary

Open concurrent PRs observed during design include:

- #100 Construction C11 draft;
- #102 Construction C12 draft;
- #103 Construction C13 draft;
- #105 plans/Textura separation;
- #106 Engineering I10 draft.

This change must not edit those branches or claim their acceptance state.

If any concurrent PR introduces or modifies workflows before queue control merges, reconcile that workflow when the branch is later updated against the new `main`. The queue-control policy validator should make missing classification/filter/concurrency explicit instead of silently accepting drift.

## 15. External syntax references

Verified against current GitHub Actions documentation on 2026-09-13:

- Trigger/path filters: https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow
- Workflow/job concurrency: https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency

## 16. Success definition

The CI queue-control capability is complete only when:

1. the implementation PR is green on its exact head;
2. all 31 unfiltered domain workflows have symmetric main-push path filtering;
3. every classified read-only workflow has safe non-main deduplication while preserving every scheduled `main` run;
4. Governance enforces the policy fail-closed;
5. the mutating materializer remains protected from automatic cancellation;
6. no domain acceptance semantics are weakened;
7. a later representative post-merge event provides real evidence of reduced steady-state fan-out.
