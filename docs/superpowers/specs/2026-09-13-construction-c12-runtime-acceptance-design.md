# Construction — C12 Runtime Acceptance Design

Date: 2026-09-13

Status: approved by delegated architectural decision

## 1. Decision

C12 is a Construction runtime-acceptance orchestrator layered over the already-proven Engineering I5 test harness. It does not replace I5 and it does not create a second runtime authority.

C12 separates two modes:

- `PREFLIGHT`: proves contracts, orchestration, target validation, timeout/log handling, evidence packaging and fail-closed behavior without claiming the physical modpack passed;
- `PHYSICAL_ACCEPTANCE`: runs against the exact physical environment and may produce final runtime acceptance only when all required physical evidence exists and the final Construction blocker has been cleared.

The final Construction blocker remains:

`SUPER_HYPER_URGENT_FINAL_CONSTRUCTION_PHYSICAL_ACCEPTANCE`

While that blocker exists, C12 implementation/preflight may become green, but C12 final acceptance must remain blocked.

## 2. Existing authorities reused

C12 consumes existing authorities rather than redefining them:

- Engineering I2: exact physical modlist/JAR identity and physical snapshot hash;
- Engineering I5: target validation plus baseline unit, GameTest and dedicated-server execution contracts;
- Construction C4: actual modpack block/state existence and registry evidence;
- Construction C5: deterministic palette resolution;
- Construction C2: Canonical Build IR and fingerprints;
- Construction C7: offline structural QA;
- Construction C8: deterministic offline previews and review evidence;
- Construction C6: deterministic Sponge v3 serialization;
- Construction C11: final complex-modded Golden manifest/artifacts;
- individual mod repositories: runtime/gameplay authority.

C12 is authority only for the aggregation and validation of live/full-modpack runtime acceptance evidence produced by these inputs and the runtime campaign.

## 3. Why C12 wraps I5 instead of extending or duplicating it

Engineering I5 already validates the exact target Minecraft `1.21.1`, NeoForge `21.1.248`, Java `21`, and provides controlled unit, GameTest and dedicated-server execution with timeout/log evidence.

Directly widening I5 with Construction-specific Golden placement, runtime visual fidelity and full-modpack semantics would couple generic Mod Engineering infrastructure to a Construction milestone. Building a second harness would duplicate already-proven target and launch behavior.

C12 therefore orchestrates I5 as a lower-level capability and adds only the Construction-specific runtime stages.

## 4. Input contract

The C12 orchestrator must accept or resolve evidence for:

- execution mode: `PREFLIGHT` or `PHYSICAL_ACCEPTANCE`;
- target identity:
  - Minecraft `1.21.1`;
  - NeoForge `21.1.248`;
  - Java `21`;
- Engineering I2 physical snapshot/hash when physical evidence is required;
- C4 registry fingerprint and authority state;
- C11 manifest fingerprint and final artifact identities when available;
- C6 Sponge v3 artifact fingerprint;
- C7 report fingerprint;
- C8 report/review/view fingerprints;
- active final Construction blocker state;
- runtime evidence root constrained to an approved workspace.

Inputs that do not match the expected authority fingerprints fail closed.

## 5. Canonical output

C12 produces a versioned `runtime-acceptance-report`.

The report must contain at least:

- schema version;
- mode;
- target identity;
- physical-environment identity when applicable;
- input authority fingerprints;
- stage results;
- evidence artifact/log paths and hashes;
- blocker state;
- overall readiness state;
- overall acceptance state;
- deterministic diagnostics for blocked/failed stages.

The report is evidence packaging. It does not supersede any upstream authority.

## 6. Stage states

Each stage uses only:

- `PASS`;
- `FAIL`;
- `BLOCKED`;
- `DEFERRED`;
- `NOT_APPLICABLE`.

A stage must not use a vague state such as `READY`, because readiness and acceptance are distinct.

## 7. C12 runtime stages

The orchestrator covers these stages in dependency order:

1. target/environment validation;
2. Engineering I5 baseline execution/reuse;
3. client smoke;
4. live placement;
5. runtime visual fidelity;
6. multiplayer integration;
7. full-modpack boot/integration;
8. deterministic evidence packaging;
9. final acceptance aggregation.

### 7.1 Target/environment validation

Reject target drift from Minecraft `1.21.1`, NeoForge `21.1.248`, Java `21`.

`PHYSICAL_ACCEPTANCE` additionally requires the exact current I2 physical snapshot and rejects stale physical evidence.

### 7.2 I5 baseline

C12 consumes the canonical I5 baseline instead of reproducing it. Required baseline evidence includes the applicable unit, GameTest and dedicated-server results and logs.

A baseline failure blocks downstream acceptance.

### 7.3 Client smoke

Client smoke validates executed runtime evidence for applicable concerns such as:

- resources load;
- models/screens/renderers/particles load where relevant;
- no missing-texture evidence;
- no render exception;
- correct client-only boundary.

C8 offline preview/review evidence cannot substitute for client smoke.

### 7.4 Live placement

Final live-placement acceptance requires the accepted final C11 artifact and its exact fingerprints.

Synthetic fixtures may exercise orchestration during `PREFLIGHT`, but cannot satisfy final placement acceptance.

### 7.5 Runtime visual fidelity

Runtime visual fidelity is a distinct live/in-game evidence stage. It is not inferred from C8 offline Visual QA.

The stage may collect evidence for texture/model/CTM/tint/emissive/shader/lighting or related runtime presentation only when actually executed and applicable.

### 7.6 Multiplayer integration

Multiplayer evidence is independent from dedicated-server boot. Applicable checks include join, initial sync, dimension transition, interaction/concurrency, reconnect and tracking behavior.

A dedicated-server `PASS` cannot promote multiplayer to `PASS`.

### 7.7 Full-modpack integration

Final full-modpack acceptance requires execution with the exact current physical modlist/JAR environment.

It validates relevant conflicts/logs/mixins/tags/recipes/registries/providers/rendering and other integration evidence defined by the final runtime campaign.

Standalone success is insufficient.

## 8. PREFLIGHT semantics

`PREFLIGHT` is allowed while the final Construction blocker exists.

It may prove:

- report/schema validity;
- target drift rejection;
- orchestration order;
- timeout and process cleanup;
- log/evidence capture;
- workspace/path safety;
- deterministic metadata/fingerprints;
- negative-path behavior with controlled fixtures;
- correct propagation of upstream blocked/deferred states.

Physical-only stages remain `DEFERRED` or `BLOCKED` when real evidence is absent.

A `PREFLIGHT` run can never produce final acceptance `PASS`.

## 9. PHYSICAL_ACCEPTANCE semantics

`PHYSICAL_ACCEPTANCE` requires:

- final blocker cleared through the authoritative physical campaign;
- current I2 physical snapshot/hash;
- accepted C11 final evidence;
- exact C4/C5/C2/C7/C8/C6 bindings used by that C11 evidence;
- execution of required live/runtime stages against the current environment;
- no stale or mismatched fingerprints;
- deterministic evidence package validation.

Any relevant environment or authority drift invalidates dependent acceptance evidence and requires rerun.

## 10. Blocker semantics

While the state is:

`SUPER_HYPER_URGENT_FINAL_CONSTRUCTION_PHYSICAL_ACCEPTANCE`

C12 must enforce:

- implementation/preflight may continue;
- `blocks_c12_acceptance = true` remains authoritative;
- overall final acceptance cannot be `PASS`;
- C11-not-accepted cannot be promoted into C12 acceptance;
- synthetic fixtures cannot clear the blocker;
- `construction/STATUS.md` cannot advance to completed C12.

## 11. Security and filesystem boundaries

C12 evidence handling must fail closed for:

- path traversal;
- output outside the approved workspace;
- symlink escape;
- malformed report/log metadata;
- stale/mismatched fingerprints;
- unexpected executable/task selection;
- timeout without process cleanup.

The orchestrator uses fixed/allowlisted runtime operations. It must not expose arbitrary shell execution as a C12 capability.

## 12. Required tests

Implementation must cover at least:

- schema positive and negative cases;
- exact target validation and drift rejection;
- stale authority fingerprint rejection;
- missing required evidence;
- path traversal and symlink escape;
- timeout/process cleanup;
- malformed logs/report metadata;
- blocker propagation;
- synthetic fixture cannot promote acceptance;
- standalone `PASS` cannot imply full-modpack `PASS`;
- dedicated-server `PASS` cannot imply multiplayer `PASS`;
- C8 offline `PASS` cannot imply runtime visual-fidelity `PASS`;
- C11 not accepted implies C12 cannot accept;
- deterministic report/evidence packaging.

## 13. CI semantics

C12 CI is split:

- `c12-preflight`: may be green while the final blocker exists;
- `c12-acceptance`: remains blocked/fail-closed until the authoritative physical campaign satisfies its prerequisites.

Governance and Sonar remain mandatory for implementation/preflight code.

A green preflight workflow must not be presented as runtime acceptance.

## 14. Physical repository placement

The live repository tree decides exact paths at implementation time. The expected minimal placement is:

- report schema under `construction/schemas/`;
- C12 orchestrator/adapters under `construction/runtime/`;
- focused tests under `construction/tests/`;
- a dedicated workflow under `.github/workflows/`.

No new top-level subsystem is required merely to mirror a conceptual plan.

## 15. Acceptance ordering

C12 final acceptance is downstream of C11 final completion.

Authoritative final ordering remains:

`C11 completion -> C12 acceptance -> C13 final acceptance -> Construction final closeout`

Implementation/preflight may exist earlier; acceptance may not invert this dependency.

## 16. Non-goals

C12 does not:

- create a new registry authority;
- create a second test harness replacing I5;
- own gameplay/runtime code of individual mods;
- fabricate physical modpack evidence;
- treat C8 offline QA as live visual fidelity;
- treat dedicated-server boot as multiplayer proof;
- reconstruct the user's physical modpack from unverified external sources;
- advance Construction STATUS during preflight;
- mark C11 complete.
