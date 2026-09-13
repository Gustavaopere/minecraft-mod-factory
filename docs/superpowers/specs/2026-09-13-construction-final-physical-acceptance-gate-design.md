# Construction — Final Physical Acceptance Gate Design

Date: 2026-09-13

Status: approved architectural direction; implementation plan not yet written

Applies to:

- `docs/superpowers/specs/2026-09-12-construction-c11-complex-modded-golden-design.md`
- `docs/superpowers/specs/2026-09-13-construction-c11-registry-deferral-amendment.md`
- future C12 Runtime Acceptance design/implementation
- future C13 Skill/Router Integration design/implementation

## 1. Decision

Physical modpack evidence is intentionally moved to the final Construction acceptance sequence instead of blocking intermediate implementation work.

The exact pending state is:

`SUPER_HYPER_URGENT_FINAL_CONSTRUCTION_PHYSICAL_ACCEPTANCE`

This is an ordering change only. It does not remove, weaken, simulate, fabricate, or replace any physical evidence requirement.

Construction may continue through C11 implementation/preflight, C12 implementation/preflight, and C13 implementation/preflight where the work can be proven without the physical modpack. Final acceptance remains fail-closed until the physical gate is executed in full.

## 2. Authorities remain unchanged

This design does not create a new Construction authority.

- Engineering I2 remains authority for the physical modlist and physical mod/JAR identities.
- C4 remains authority for actual modpack block/state existence and the current conservative safety evidence.
- C5 remains authority for deterministic semantic palette resolution.
- C2 remains authority for Canonical Build IR validation and fingerprinting.
- C7 remains authority for offline structural QA.
- C8 remains authority for deterministic offline previews and Visual QA evidence.
- C6 remains authority for Sponge Schematic v3 serialization and validation.
- C11 remains the complex modded offline Golden integration phase.
- C12 remains full-modpack/live-world/runtime acceptance.
- C13 remains Skill/Router integration.

The final physical gate coordinates those authorities; it does not supersede them.

## 3. Why the gate moves to the end

Stopping all Construction work at the C11 physical capture would serialize unrelated implementation behind a manual runtime action. That is unnecessary for work whose contracts can be proven independently.

The chosen strategy therefore separates:

1. implementation/preflight readiness; and
2. physical/final acceptance.

This lets the Factory continue building deterministic tooling, validators, harnesses, CI, routing contracts and fail-closed boundaries while preserving the real modpack evidence as an explicit final blocker.

No preflight result is promoted into physical acceptance.

## 4. Machine-readable blocker semantics

The Construction pending state must record at least these semantics:

- `status = "SUPER_HYPER_URGENT_FINAL_CONSTRUCTION_PHYSICAL_ACCEPTANCE"`;
- `blocks_c11_completion = true`;
- `blocks_c12_acceptance = true`;
- `blocks_c13_final_acceptance = true`;
- `blocks_construction_final_acceptance = true`.

The state is intentionally severe and durable. It exists to prevent a later agent, CI change, router, or maintainer from mistaking implementation readiness for completed Construction acceptance.

The state must also retain the last observed physical modlist hash as historical evidence while explicitly requiring a fresh re-hash at the final gate. A previously observed hash is not automatically final evidence if the physical environment changes before acceptance.

## 5. Allowed work before the final physical gate

### 5.1 C11

C11 may continue only with work that does not require real final C4 contents.

Allowed examples:

- capture helper hardening;
- runtime probe build/materialization;
- validators and mutation tests;
- CI separation between preflight and completion;
- deterministic fixture-generation infrastructure that does not freeze fabricated modded IDs;
- manifest tooling whose final values remain unfrozen until real evidence exists;
- documentation and governance.

C11 may reach an implementation/preflight-ready state, but not `C11_COMPLETE`.

### 5.2 C12

C12 may be designed and implemented in preflight form before the physical gate.

Allowed examples:

- runtime acceptance contract and report schema;
- target validation for Minecraft 1.21.1 / NeoForge 21.1.248 / Java 21;
- harness orchestration;
- launch/timeout/log-capture contracts;
- live-placement test scaffolding;
- evidence packaging and deterministic metadata contracts;
- negative-path tests using controlled fixtures;
- CI that proves the harness itself without claiming the full physical modpack passed.

C12 preflight must not claim:

- successful full physical modpack boot;
- successful placement of the final C11 Golden;
- runtime block/state existence not already proven by real C4 evidence;
- in-game texture/CTM/tint/emissive/shader fidelity;
- multiplayer/dedicated-server compatibility of the final Golden unless actually executed at the final gate.

### 5.3 C13

C13 may be designed and implemented against capability contracts before the physical gate.

Allowed examples:

- Skill/Router capability declarations;
- routing to existing C0-C10 authorities;
- routing to C11/C12 preflight surfaces with explicit readiness state;
- fail-closed propagation of deferred/blocked acceptance;
- deterministic router tests using controlled fixtures;
- documentation and CI for the integration layer.

C13 must not advertise C11 or C12 as accepted while the final physical blocker exists. Any status/capability surface must preserve the distinction between implementation readiness and final acceptance.

## 6. Forbidden work before the final physical gate

While the pending state is `SUPER_HYPER_URGENT_FINAL_CONSTRUCTION_PHYSICAL_ACCEPTANCE`, implementation must not:

- hand-author or fabricate the final C4 `registry.json`;
- invent or freeze modded block IDs as runtime facts;
- infer block/state existence from mod/JAR presence alone;
- freeze the final C5 palette against synthetic C4 data;
- freeze the final C11 modded Build IR against fabricated registry data;
- freeze final C7/C8/C6 C11 Golden outputs derived from fabricated registry data;
- claim C11 complete;
- claim C12 runtime acceptance;
- claim C13 final acceptance;
- advance `construction/STATUS.md` to a completed C11/C12/C13 state;
- mark Construction itself complete.

Synthetic fixtures remain valid only for unit/negative/preflight coverage where they are explicitly identified as synthetic and do not masquerade as final modpack evidence.

## 7. Final physical acceptance sequence

When Construction implementation/preflight work through C13 is ready, the physical gate runs as one final acceptance campaign.

The required sequence is:

1. re-audit the current physical modlist;
2. compute and freeze the final Engineering I2 physical snapshot/hash;
3. verify the target remains Minecraft 1.21.1 / NeoForge 21.1.248 / Java 21;
4. execute the C4 NeoForge registry probe against that exact physical modpack;
5. produce `c11-runtime-snapshot.json`;
6. compose and validate the canonical C4 `registry.json` against the exact physical JAR set;
7. resolve and freeze the evidence-backed C5 palette;
8. generate and freeze the deterministic C2 C11 Build IR;
9. execute/freeze C7 structural QA evidence;
10. regenerate/freeze all seven C8 canonical previews and bound review/Visual QA evidence;
11. export and validate deterministic C6 Sponge v3 bytes;
12. freeze the final closed C11 manifest and mutation/determinism evidence;
13. execute C12 full physical runtime acceptance, including the final C11 artifact where required by the C12 design;
14. validate C13 routing/skill behavior against the now-accepted C11/C12 capabilities;
15. run the full Construction regression, governance, Sonar and target-specific acceptance gates;
16. merge the implementation changes only under the repository's proven PR/gate policy;
17. revalidate the exact merged head on `main`;
18. perform dedicated STATUS-only closeouts in the authoritative completion order.

Manual actions inside this final campaign remain one action at a time. The fact that they are concentrated at the end does not permit batching unverified manual claims.

## 8. Completion ordering remains authoritative

Implementation work may proceed out of acceptance order, but completion semantics do not.

The authoritative closeout order remains:

`C11 completion -> C12 acceptance -> C13 final acceptance -> Construction final closeout`

C12 cannot be marked accepted before C11 final evidence exists. C13 cannot be marked finally accepted before the accepted capabilities it routes to exist. Construction cannot be marked complete before all three are closed with post-merge evidence.

This distinction is central to the design: implementation concurrency is allowed; acceptance dependency inversion is not.

## 9. STATUS semantics

`construction/STATUS.md` must not claim phase completion merely because C11/C12/C13 preflight implementation exists.

Until the final physical gate is satisfied, the canonical completed phase remains the last actually completed/post-merge-validated Construction phase. The urgent pending state is recorded in the C11/Construction acceptance evidence and associated PR/spec documentation rather than by falsely advancing the phase.

After the final gate succeeds, phase closeouts remain separate evidence-gated changes. A STATUS transition requires the exact implementation merge and post-merge gates appropriate to that phase.

## 10. CI semantics

CI before final physical acceptance must expose readiness and acceptance separately.

Required rules:

- preflight jobs may be green;
- physical/final acceptance jobs must remain blocked, skipped with an explicit blocker state, or fail-closed according to their phase contract;
- a green workflow summary must not imply C11/C12/C13 final acceptance while the blocker exists;
- CI must not reconstruct the user's physical modpack from unverified external sources;
- provider payment/API execution remains irrelevant to this gate;
- Sonar/security/governance remain mandatory for implementation/preflight code.

The blocker string must be stable enough for tests and CI assertions:

`SUPER_HYPER_URGENT_FINAL_CONSTRUCTION_PHYSICAL_ACCEPTANCE`

## 11. Drift handling at the final gate

The final gate always re-audits the physical environment.

If the modlist, JAR set, target versions, or relevant authority contracts changed since preflight:

- prior physical hashes are historical evidence only;
- C4 capture is performed against the new exact environment;
- any downstream evidence that depends on the changed input is regenerated;
- no stale C11 Golden artifact is grandfathered into acceptance;
- C12/C13 preflight code is revalidated against the current accepted authorities before closeout.

This design therefore tolerates implementation work continuing while the environment evolves, without pretending stale evidence remains current.

## 12. PR and branch strategy

The existing C11 draft PR remains preflight/implementation evidence, not C11 completion.

Because Engineering PR #99 merged into `main` after the C11 branch diverged and both touched the shared Sonar workflow, the C11 branch must be reconciled against the current `main` before any future integration. Reconciliation must preserve both I9 and C11 Sonar coverage rather than overwriting either side.

Future C12 and C13 work should use their own approved design/spec, implementation plan and branch/PR boundaries unless the later repository audit proves a narrower approach is safer. They must consume, not redefine, the final physical acceptance blocker.

## 13. Acceptance criteria for this architectural change

This ordering change is correctly implemented only when all of the following are true:

- the exact blocker `SUPER_HYPER_URGENT_FINAL_CONSTRUCTION_PHYSICAL_ACCEPTANCE` is machine-readable;
- it blocks C11 completion, C12 acceptance, C13 final acceptance and Construction final closeout;
- it does not block independent C12/C13 design/implementation/preflight work;
- no final C11 artifact is fabricated to bypass C4;
- C12/C13 preflight surfaces propagate deferred/blocked acceptance honestly;
- `construction/STATUS.md` is not falsely advanced;
- final acceptance re-hashes/re-captures the physical environment rather than trusting stale preflight hashes;
- closeouts happen in C11 -> C12 -> C13 -> Construction order;
- the physical/manual campaign remains one manual action at a time.

## 14. Non-goals

This design does not:

- implement C12;
- implement C13;
- define the complete C12 runtime acceptance schema;
- define the complete C13 router/skill schema;
- execute the physical probe now;
- create final C11 `registry.json`;
- create final C11 palette/Build IR/QA/schematic artifacts;
- change individual mod runtime authority;
- turn the Factory into a mega-mod or runtime monorepo.
