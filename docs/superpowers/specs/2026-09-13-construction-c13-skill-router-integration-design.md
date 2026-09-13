# Construction — C13 Skill/Router Integration Design

Date: 2026-09-13

Status: approved by delegated architectural decision

## 1. Decision

C13 integrates Construction capabilities into the existing Minecraft Mod Factory skill/router authority without creating a second router.

`skills/ROUTER.md` remains the canonical human-facing router. `engineering/REPO-ROUTING.md` remains the canonical repository/authority boundary contract. `skills/VERSION-AUTHORITY.md` remains the version-sensitive fail-closed authority order.

C13 adds a machine-readable capability index and validator layer that describes which existing authority/surface is legitimate for a given intent and whether that capability is implementation-ready and/or finally accepted.

The final Construction blocker remains:

`SUPER_HYPER_URGENT_FINAL_CONSTRUCTION_PHYSICAL_ACCEPTANCE`

C13 implementation/preflight may become green while this blocker exists, but C13 final acceptance must remain blocked until accepted C11/C12 capabilities exist.

## 2. C13 is integration, not a new authority

C13 does not own registry facts, palettes, Build IR, structural QA, visual QA, exports, provider APIs, runtime acceptance, gameplay code or art authoring.

It routes to authorities that already own those concerns.

The initial authority map includes:

- Construction C2: Canonical Build IR;
- Construction C4: block/state registry facts;
- Construction C5: semantic palette resolution;
- Construction C6: Sponge v3 export;
- Construction C7: structural QA;
- Construction C8: offline visual QA;
- Construction C9: capability-limited MCP façade over C2/C4/C5/C6/C7/C8;
- Construction C10: external-provider handoff/profile boundary;
- Construction C11: complex-modded Golden readiness/completion;
- Construction C12: live/full-modpack runtime acceptance;
- Mod Engineering: shared runtime engineering contracts/tooling;
- Repo Textura / `art/`: visual/asset authoring authority;
- individual mod repositories: runtime/gameplay authority;
- physical modlist/JAR evidence: installed provider/mod presence and exact versions.

C13 references these authorities; it does not supersede them.

## 3. Existing router authorities preserved

C13 must preserve:

- `skills/ROUTER.md` as the shared skills entrypoint;
- `skills/VERSION-AUTHORITY.md` as the version-sensitive order of evidence;
- `skills/USER-GUIDED-WORKFLOW.md` for one-verifiable-manual-step-at-a-time flows;
- `engineering/REPO-ROUTING.md` for Factory/art/skills/mod-runtime authority boundaries;
- the existing skill repository validator and active-vs-`REFERENCE_ONLY` classification.

C13 may update those documents only to reference the new capability contract where useful. It must not replace them with a competing routing system.

## 4. Machine-readable capability index

C13 introduces a versioned capability index.

Each capability declaration contains at least:

- stable `capability_id`;
- intent/category;
- owning authority;
- canonical entrypoint/surface;
- required evidence classes;
- readiness state;
- acceptance state;
- active blocker, when applicable;
- physical/version-proof requirement;
- fallback policy;
- forbidden-promotion rules.

The index is routing metadata. It is not a database of mutable runtime facts and must not duplicate full upstream evidence payloads.

## 5. Readiness and acceptance are separate axes

Readiness states:

- `AVAILABLE`;
- `PREFLIGHT_READY`;
- `UNAVAILABLE`.

Acceptance states:

- `ACCEPTED`;
- `BLOCKED`;
- `NOT_APPLICABLE`.

These axes must not be collapsed into one vague status such as `READY`.

Examples while the final physical blocker exists:

- C9 offline tools: `AVAILABLE / ACCEPTED` within their already-proven contracts;
- C11: `PREFLIGHT_READY / BLOCKED`;
- C12 after preflight implementation: `PREFLIGHT_READY / BLOCKED`;
- C13 itself after implementation/preflight: `PREFLIGHT_READY / BLOCKED` until its downstream final prerequisites are accepted.

## 6. Stable blocker propagation

The exact blocker string is propagated where applicable:

`SUPER_HYPER_URGENT_FINAL_CONSTRUCTION_PHYSICAL_ACCEPTANCE`

C13 must not normalize it into a vague `pending` state that loses the acceptance boundary.

While this blocker exists:

- C11 cannot be routed/presented as complete;
- C12 cannot be routed/presented as runtime accepted;
- C13 cannot be presented as finally accepted;
- Construction cannot be presented as finally complete.

## 7. Initial deterministic intent routes

The capability index should cover at least these route classes:

- registry/block lookup -> C4/C9;
- palette resolution -> C5/C9;
- canonical construction/edit -> C2/C9;
- structural QA -> C7/C9;
- offline preview/visual QA -> C8/C9;
- Sponge v3 export -> C6/C9;
- external-provider handoff -> C10;
- complex-modded Golden readiness/completion -> C11;
- live/full-modpack/runtime acceptance -> C12;
- Java/gameplay/runtime modification -> Mod Engineering plus the target mod runtime repository;
- model/texture/rig/animation/VFX visual authoring -> Repo Textura / `art/`;
- unsupported or version-unproven provider behavior -> fail-closed `UNAVAILABLE`.

Routing is by declared intent/capability contract, not free-form invention of a provider/tool name.

## 8. Provider/profile semantics

Provider profiles are data/contracts, not one new skill per provider.

Provider routing must require exact-version evidence where behavior is version-sensitive.

Nominal presence in the physical modlist does not prove an API. A provider capability remains unavailable until the exact target source/JAR/official documentation evidence required by `skills/VERSION-AUTHORITY.md` is satisfied.

No implicit cross-provider conversion or silent fallback is allowed.

## 9. Fallback semantics

Fallback is permitted only when:

- the fallback is semantically equivalent for the requested intent;
- the capability contract explicitly allows it;
- it does not cross an authority boundary that changes runtime or source-format semantics;
- all required evidence for the fallback exists.

Forbidden silent fallback examples include:

- provider A -> provider B conversion;
- native source format -> different provider format;
- physical runtime evidence -> synthetic fixture;
- C8 offline preview -> C12 runtime fidelity;
- static/unconfirmed registry fact -> runtime-confirmed fact.

## 10. Forbidden promotions

C13 must fail closed against any attempted promotion of:

- C11 preflight -> C11 complete;
- C12 preflight -> C12 accepted;
- offline C8 Visual QA -> live runtime visual fidelity;
- C4 static/unconfirmed evidence -> runtime-confirmed evidence;
- provider presence -> API support;
- synthetic fixture -> physical/final acceptance;
- `REFERENCE_ONLY` skill/material -> active authority;
- compile/build success -> runtime/multiplayer/visual/full-modpack success.

## 11. Manual-action routing

Capabilities requiring manual user action inherit `skills/USER-GUIDED-WORKFLOW.md`.

C13 may identify that a manual action is required and which authority owns the next step, but it must not batch multiple manual operations. One atomic action is issued, evidence is validated, then the next action may be selected.

If the agent has an authorized tool capable of executing the operation safely, the operation should be executed directly instead of delegated to the user.

## 12. Capability-path integrity

The capability index must validate that declared canonical entrypoints exist and match expected authority classes.

CI must fail for:

- missing paths;
- unknown authorities;
- duplicate capability IDs;
- ambiguous deterministic routes that lack an explicit precedence rule;
- route to a `REFERENCE_ONLY` skill as active authority;
- invalid readiness/acceptance combinations;
- acceptance `ACCEPTED` while a declared blocking prerequisite remains blocked;
- provider-specific route lacking required version-proof semantics.

## 13. C9 and C10 integration

C13 routes to the existing C9 façade rather than adding duplicate wrappers around its tools.

C9 currently provides capability-limited surfaces over C2/C4/C5/C6/C7/C8. C13 identifies those as valid routes but does not expand C9 into arbitrary shell/code execution.

C10 remains the external-provider handoff/profile boundary. C13 may route a provider intent to C10 only when its evidence/profile contract supports that route.

## 14. C11/C12 integration

C13 must consume C11/C12 state without owning their mutable evidence.

Before final physical acceptance:

- C11 may be `PREFLIGHT_READY / BLOCKED`;
- C12 may be `PREFLIGHT_READY / BLOCKED`;
- route results must expose that distinction honestly.

After the final campaign, C13 final acceptance revalidates the capability index against the now-accepted C11/C12 states before closeout.

## 15. Preflight fixtures and tests

C13 preflight may use controlled synthetic fixtures for routing logic only.

Required coverage includes:

- intent -> correct authority;
- unsupported intent -> `UNAVAILABLE`;
- ambiguous route rejection or explicit precedence;
- blocked downstream propagation;
- missing evidence;
- stale capability declaration;
- target drift;
- provider absent;
- provider present without API proof;
- `REFERENCE_ONLY` material cannot activate;
- manual-action route selects the user-guided protocol;
- C11 blocker propagation;
- C12 blocker propagation;
- invalid readiness/acceptance combinations;
- capability path/entrypoint integrity;
- deterministic index serialization/validation.

Pure routing logic must remain testable without booting Minecraft.

## 16. CI semantics

C13 CI is split:

- `c13-router-preflight`: schema/index validation, deterministic routing, authority/path integrity, negative cases and blocker propagation;
- `c13-final-acceptance`: remains blocked/fail-closed until required downstream acceptance exists.

The preflight workflow also runs the existing skill repository validator and relevant C9/C10/C12 contract regressions.

Governance and Sonar remain mandatory.

A green C13 preflight does not mean C13 final acceptance.

## 17. Final acceptance prerequisites

C13 final acceptance requires at least:

- the final physical blocker cleared through authoritative evidence;
- C11 final completion accepted;
- C12 runtime acceptance accepted;
- current capability index validates against the accepted authorities;
- no required route remains `BLOCKED` or `UNAVAILABLE`;
- exact target/version evidence remains current;
- deterministic routing tests pass;
- governance/Sonar pass;
- implementation merge and post-merge validation complete.

Only then may C13 move to final accepted state.

## 18. Repository placement

The live repository tree decides final implementation paths.

Expected minimal placement is:

- a machine-readable capability schema/index near existing shared routing/integration contracts;
- focused validator/tests without duplicating the current skill validator;
- narrow references in `skills/ROUTER.md` or `engineering/REPO-ROUTING.md` only where needed;
- dedicated C13 CI.

No new large top-level hierarchy is required solely to match a conceptual plan.

## 19. Acceptance ordering

C13 final acceptance is downstream of accepted C11 and C12.

Authoritative closeout order remains:

`C11 completion -> C12 acceptance -> C13 final acceptance -> Construction final closeout`

C13 preflight may be implemented earlier, but acceptance dependency inversion is forbidden.

## 20. STATUS semantics

`construction/STATUS.md` remains at the last actually completed/post-merge-validated phase during C13 preflight.

C13 implementation readiness is not a STATUS completion event.

## 21. Non-goals

C13 does not:

- create a second router;
- create one skill per Construction phase;
- create one skill per provider;
- execute arbitrary shell or JavaScript;
- install arbitrary provider extensions;
- become a provider API authority;
- own mutable C11/C12 runtime evidence;
- promote `REFERENCE_ONLY` material;
- change individual mod runtime authority;
- advance Construction STATUS during preflight;
- bypass C11/C12 acceptance ordering.
