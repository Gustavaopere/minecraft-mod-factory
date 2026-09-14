# Construction C11 — Deferred Registry Preflight Plan

> Execution addendum for the approved C11 design. The original completion plan remains authoritative once the physical modlist stabilizes.

**Goal:** Finish every C11 preflight/tooling task that does not require fabricated runtime evidence, while keeping C11 completion fail-closed until the stabilized physical modpack is captured by C4.

**Approved pending state:** `MANUAL_URGENT_PENDING_MODLIST_STABILIZATION`

**Amendment:** `docs/superpowers/specs/2026-09-13-construction-c11-registry-deferral-amendment.md`

## Constraints

- Do not create `registry.json` before a real stabilized capture.
- Do not freeze modded palette IDs, Build IR, C7/C8/C6 Golden evidence, or final manifest before `registry.json` exists and validates.
- Keep `construction/STATUS.md` unchanged.
- Keep providers/payment/network generation out of C11 acceptance.
- Every code change remains TDD-first.
- Preflight success is readiness evidence only; it is never C11 completion.

## Task P1 — Version the explicit manual-pending state

- [ ] Add a RED test requiring `construction/fixtures/complex-modded-golden/capture-state.json`.
- [ ] Observe failure because the file is absent.
- [ ] Create the closed JSON state with exact pending status, blocker semantics, probe hashes, and last-observed modlist hash.
- [ ] Re-run and require the pending-state test GREEN.
- [ ] Keep the separate real-registry completion test RED/blocked.

## Task P2 — Harden capture helper preflight behavior

Add tests before implementation for:

- [ ] missing physical top-level JAR -> fail;
- [ ] runtime snapshot missing -> fail;
- [ ] malformed runtime JSON -> fail;
- [ ] runtime physical snapshot SHA mismatch -> fail through C4;
- [ ] wrong Minecraft/loader/NeoForge target -> fail through C4;
- [ ] output path escapes workspace -> fail if the helper exposes a CLI output path contract;
- [ ] canonical output bytes revalidate after write.

Do not mock C4 semantics when the real Python authority can be invoked with temporary fixtures.

## Task P3 — Split CI semantics into preflight and completion

The dedicated C11 workflow must make the distinction visible.

### Preflight job

May pass when the pending state is valid. It must run:

- capture-helper tests that do not require `registry.json`;
- pending-state contract;
- C4 runtime-probe tests;
- probe materialization;
- Java 21 / NeoForge 21.1.248 `./gradlew test build --no-daemon`;
- pinned probe artifact publication;
- `git diff --check`.

### Completion job

Must not report success while the pending state exists.

Until `registry.json` is captured, it should terminate with an explicit blocked/failure message equivalent to:

`C11_COMPLETION_BLOCKED: MANUAL_URGENT_PENDING_MODLIST_STABILIZATION`

After real capture, this job is replaced/expanded by the original full C11 workflow contract covering I2 + C0–C10 regressions and the complete Golden chain.

## Task P4 — Sonar coverage for preflight source

- [ ] Add RED governance assertions for C11 preflight coverage.
- [ ] Cover `construction/fixtures/complex-modded-golden/capture_registry.py` through focused helper tests that are GREEN without `registry.json`.
- [ ] Do not run the blocked completion test as the Sonar coverage command during deferral.
- [ ] Keep the final plan requirement to cover all later C11 fixture Python source once those files exist.

## Task P5 — Document the boundary

Through RED documentation-presence assertions, require Construction docs to state:

- `C11 Complex Modded Golden`;
- `MANUAL_URGENT_PENDING_MODLIST_STABILIZATION`;
- real C4 capture is deferred until modlist stabilization;
- preflight green != C11 completion;
- `C12 Runtime Acceptance` remains separate;
- STATUS does not advance.

Update only `construction/README.md` and `construction/docs/ARCHITECTURE.md`; do not update STATUS.

## Task P6 — Draft PR and verification

Before opening/updating the draft PR:

- [ ] re-audit `main` and all open PRs;
- [ ] confirm no Construction overlap from concurrent work;
- [ ] prove changed files do not include `construction/STATUS.md`;
- [ ] run/inspect preflight CI terminal result;
- [ ] confirm completion remains explicitly blocked, not silently skipped as PASS;
- [ ] open draft PR with the manual blocker and exact probe evidence in the body.

Draft PR title:

`feat(construction): prepare C11 complex modded golden preflight`

The PR must remain draft and must not be represented as complete C11 implementation while `capture-state.json` is pending.

## Resume condition

Resume the original C11 implementation plan only after the user declares the physical modlist stable.

At that point:

1. re-audit and hash the new physical modlist;
2. rebuild/revalidate the C4 probe if upstream inputs changed;
3. run the probe in the exact stabilized physical modpack;
4. compose canonical `registry.json` using exact physical JARs;
5. remove/replace the pending capture state;
6. require the original C11 real-registry test GREEN;
7. continue original Tasks 3–11 in order.
