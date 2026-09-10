# TESTING — Minecraft Mod Factory

Status: canonical testing/evidence strategy for reusable Factory infrastructure.

A green static check is necessary but is not equivalent to a generated-mod build, NeoForge runtime, multiplayer, provider-present, visual or release result.

## Factory test layers

- F-T0 — static contracts: Markdown/link/path policy, JSON parse/schema checks, deterministic manifests and migration invariants.
- F-T1 — unit tests: pure validators, generators, parsers, routing and provider-profile logic.
- F-T2 — generated sample: scaffold a disposable mod from canonical templates and require deterministic output plus a clean diff.
- F-T3 — target-repository build: Java 21 / Minecraft 1.21.1 / NeoForge build in the generated or integrated runtime repository.
- F-T4 — NeoForge runtime: GameTests and dedicated-server smoke for runtime-sensitive changes.
- F-T5 — provider matrices: provider-absent and exact-version provider-present evidence for integrations.
- F-T6 — client/visual: client startup, UI and in-game visual QA where the capability is client-facing or asset-facing.
- F-T7 — performance/release: measured hot-path/regression evidence, packaging, reproducibility and release readiness.

## Evidence vocabulary

`validator passes`, `unit tests pass`, `generated sample builds`, `GameTest passes`, `server smoke passes`, `provider integration works`, `visual QA passes` and `release ready` are distinct claims. Never promote one evidence level into a stronger one.

## Determinism

Generators and migrations must be deterministic. Applicable CI should run `git diff --check` and, after deterministic generators, `git diff --exit-code`. Native source assets must not be rewritten by a validation-only gate.

## Runtime boundary

Runtime-specific tests execute in the mod's runtime authority repository or in a disposable generated sample that explicitly models that target. The Factory itself must not fake a NeoForge runtime merely to obtain a green badge.

## Migration rule

Historical tests are reused when their semantics are generic. RPG-only assertions are removed from Factory gates rather than copied blindly. A migrated capability is complete only after the adapted test proves the same relevant contract in the Factory layout.
