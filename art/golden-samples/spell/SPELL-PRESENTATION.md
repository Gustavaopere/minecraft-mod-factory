# Golden Sample — Spell Presentation Contract

Status: **REFERENCE-ONLY — not a runtime registration and not evidence of shipped gameplay.**

Reference ID: `golden_reference_arcane_bolt`

## Anticipation

Presentation intent:
- small hand/focus glow;
- restrained inward motion/charge particles;
- optional low-volume charge cue.

Authority rule:
- anticipation may communicate input/intent only;
- exact prediction policy is `UNRESOLVED`;
- it must not communicate damage, hit, or successful resource spend before authoritative confirmation.

## Release

Presentation intent:
- one clear release flash at the proven attachment point;
- cast animation release landmark;
- release audio transient.

Authority rule:
- begin authoritative release presentation from a server-confirmed cast event/path;
- exact event/network message/API is `UNRESOLVED`.

## Travel / Active

Presentation intent:
- bright compact projectile core;
- secondary halo/sparks;
- narrow trail with short lifetime so silhouettes and targets remain readable.

Authority rule:
- authoritative projectile/active-state owner is `UNRESOLVED`;
- client visuals follow confirmed state rather than inventing target results;
- interpolation/snapshot policy is `UNRESOLVED`.

## Impact / Resolve

Presentation intent:
- central impact flash;
- radial secondary fragments/ring;
- outcome-specific variation only when the authoritative outcome is known.

Authority rule:
- hit/miss/block/resist/damage owner is `UNRESOLVED` and must be server authoritative;
- the client must not emit a hit-confirmation impact solely from local collision guess;
- deduplication/causal event key is `UNRESOLVED`.

## Decay

Presentation intent:
- short residual motes/fade;
- optional quiet tail audio;
- no persistent screen obstruction.

Authority rule:
- decay is cosmetic after a confirmed terminal presentation state;
- lifecycle cleanup hooks are `UNRESOLVED` until runtime integration exists.

## Audio map

- anticipation cue asset/event: `UNRESOLVED`;
- release cue asset/event: `UNRESOLVED`;
- travel loop: optional, `UNRESOLVED`;
- impact cue asset/event: `UNRESOLVED`;
- decay tail: optional, `UNRESOLVED`.

## Camera/targeting

- camera shake: optional and `UNRESOLVED`; must respect accessibility/config policy if implemented.
- crosshair/target lock integration: `UNRESOLVED`.
- first-person obstruction budget: `UNRESOLVED` pending real visual evidence.

## Causality and multiplayer

Required future proof before approval:
- server owns cast legality/resource/cooldown/target/result;
- one authoritative cast/result maps to one client presentation sequence;
- duplicate packets/events do not duplicate impact or audio;
- late join/dimension/death/logout cleanup semantics are defined where relevant;
- fake-player behavior is defined if the gameplay owner can be invoked by fake players.

Exact implementation for all points above is `UNRESOLVED` in this reference.

## Technical limits

- provider selection/API: `UNRESOLVED`;
- particle count/lifetime/distance culling budgets: `UNRESOLVED` until the chosen provider and real effect are profiled;
- multiplayer concurrency target: `UNRESOLVED`;
- fallback when optional provider is absent/incompatible: `UNRESOLVED` and must fail safely.

## Evidence state

No in-game implementation exists in this sample. Editor screenshots, gameplay capture, multiplayer capture, profiler evidence, and audio mix evidence are all `PENDING`.
