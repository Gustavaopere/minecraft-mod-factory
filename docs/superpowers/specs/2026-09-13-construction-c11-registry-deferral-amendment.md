# Construction C11 — Registry Capture Deferral Amendment

Date: 2026-09-13

Status: approved execution amendment

Applies to:

- `docs/superpowers/specs/2026-09-12-construction-c11-complex-modded-golden-design.md`
- `docs/superpowers/plans/2026-09-12-construction-c11-complex-modded-golden.md`

## Decision

The physical modpack is still expected to change. Capturing the complete C4 runtime registry now would create disposable evidence and would need to be repeated after the modlist stabilizes.

The physical registry capture is therefore deferred intentionally.

This amendment does **not** remove, weaken, simulate, or replace the real C4 evidence requirement. It changes only the execution ordering so that C11 preflight/tooling work may continue while the final physical evidence remains unavailable.

## Explicit pending state

Until the physical modlist is declared stable, C11 uses the exact pending state:

`MANUAL_URGENT_PENDING_MODLIST_STABILIZATION`

The state means:

- manual action is required before C11 can complete;
- the action is urgent once the physical modlist becomes stable;
- no action is required while the user is still changing mods;
- the last observed physical modlist SHA is historical/preflight evidence only and is not automatically the final C11 snapshot;
- a new C4 runtime capture must be made against the stabilized physical modpack.

The fixture records this state in:

`construction/fixtures/complex-modded-golden/capture-state.json`

That document is temporary preflight evidence. It must be removed or replaced as part of the same evidence-freezing change that checks in the final canonical `registry.json`.

## C11 preflight authority

C11 is now split operationally into two gates without creating a new Construction authority.

### C11_PREFLIGHT

Preflight may be implemented and validated before physical capture. It may include only:

- the fixture-local `capture_registry.py` helper that delegates to Engineering I2 and C4;
- tests proving the helper fails closed on missing physical JARs and invalid evidence;
- materialization/build of the existing C4 NeoForge registry probe under Java 21 / NeoForge 21.1.248;
- publication of the compiled probe as a CI artifact;
- exact probe artifact/JAR hashes;
- machine-readable deferred-capture state;
- CI workflow wiring that distinguishes preflight from completion;
- Sonar coverage for new preflight Python source;
- Construction README/architecture documentation of the pending boundary;
- a draft PR that is explicitly blocked on the real registry.

A green preflight proves only that the capture tooling and fail-closed boundary are ready. It is not C11 acceptance.

### C11_COMPLETION

Completion remains fail-closed and requires the original approved design in full.

It cannot pass until all of the following exist from the stabilized physical modpack:

1. fresh runtime snapshot from the C4 probe;
2. complete exact physical JAR set matching the stabilized I2 snapshot;
3. canonical composed C4 `registry.json`;
4. C4 canonical validation success;
5. evidence-backed C5 palette request/resolution;
6. deterministic C2 Build IR;
7. C7 structural QA evidence;
8. C8 canonical previews and hash-bound review/Visual QA evidence;
9. C6 deterministic Sponge v3 bytes;
10. closed C11 manifest and mutation coverage.

No preflight gate can substitute for any item above.

## Forbidden before physical capture

While `capture-state.json.status` is `MANUAL_URGENT_PENDING_MODLIST_STABILIZATION`, implementation must not:

- create or hand-author `registry.json`;
- invent or freeze modded block IDs;
- treat mod presence as block/state existence;
- freeze `palette-request.json` or `expected-palette-resolution.json` using synthetic C4 data;
- freeze the final modded `expected-build-ir.json`;
- freeze C7/C8/C6 Golden outputs derived from fabricated/synthetic registry data;
- create the final C11 manifest;
- claim C11 PASS/COMPLETE;
- advance `construction/STATUS.md`;
- claim any C12 runtime acceptance.

## Probe evidence already proven

The existing C4 probe was materialized and built successfully in GitHub Actions on the C11 branch under Java 21 / NeoForge 21.1.248.

Preflight artifact evidence:

- workflow run: `34735133220`;
- artifact name: `c11-registry-probe`;
- artifact ZIP SHA-256: `399ee102ac5fb94c4bf25bd840a8d942bb5a8dc9ad44a17b41eaa2a546c94a77`;
- compiled JAR: `factory_construction_registry_probe-0.1.0.jar`;
- compiled JAR SHA-256: `ea9d2b89b3ae774e6e3fcc0b9b8a4a48a62ffa95c961cd41becff45c6f9ed943`.

These hashes prove the prepared probe artifact only. They do not prove any physical modpack registry contents.

## CI semantics during deferral

The dedicated C11 workflow must expose the distinction between readiness and completion.

- preflight tests may pass while capture is deferred;
- completion must remain blocked whenever final `registry.json` is absent;
- the workflow or PR description must not present a preflight-only green state as C11 completion;
- the C4 probe build remains a required preflight regression;
- provider execution/payment remains irrelevant and prohibited as an acceptance dependency.

## STATUS semantics

`construction/STATUS.md` remains unchanged during this deferred/preflight implementation.

There is no transition to `C11_COMPLETE_POSTMERGE_VALIDATED` until the stabilized physical registry exists, the full original C11 acceptance suite is green, the implementation merge is validated on `main`, and the separate STATUS-only closeout is performed.
