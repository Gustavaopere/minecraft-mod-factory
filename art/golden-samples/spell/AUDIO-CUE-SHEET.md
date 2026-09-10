# Golden Sample — Audio Cue Sheet

Status: **REFERENCE-ONLY — not a runtime registration and not evidence of shipped gameplay.**

Reference ID: `golden_reference_arcane_bolt`

No OGG or `SoundEvent` is registered by this sample.

| Phase | Conceptual cue | Trigger authority | Asset/Event | Spatial notes | Status |
|---|---|---|---|---|---|
| Anticipation | restrained charge texture | input/intent policy `UNRESOLVED` | `UNRESOLVED` | local/3D policy `UNRESOLVED` | PENDING |
| Release | short bright transient | server-confirmed cast | `UNRESOLVED` | attach to caster/release point; attenuation `UNRESOLVED` | PENDING |
| Travel | optional subtle loop | authoritative active projectile state | `UNRESOLVED` | only if mix remains readable; loop lifecycle `UNRESOLVED` | PENDING |
| Impact | distinct impact transient | server-confirmed resolve outcome | `UNRESOLVED` | impact position; attenuation `UNRESOLVED` | PENDING |
| Decay | optional quiet tail | cosmetic terminal state | `UNRESOLVED` | short and unobtrusive | PENDING |

## Variation and mixing

- Variant count: `UNRESOLVED`.
- Pitch randomization: `UNRESOLVED`.
- Volume: `UNRESOLVED`.
- Attenuation distance/model: `UNRESOLVED`.
- Mono/stereo choice: `UNRESOLVED` until actual asset and spatial use are known.
- Start/loop/end implementation for travel: `UNRESOLVED`.

## Multiplayer causality

A future implementation must prevent duplicate release/impact cues from duplicate network/event delivery. The authoritative event identity and client deduplication mechanism are `UNRESOLVED`.

## Provenance

Actual audio source/author/license: `UNRESOLVED` because no sound asset is included.

## Acceptance

No waveform, OGG validation, in-game attenuation test, multiplayer mix test, or loudness evidence exists. Audio QA remains `PENDING`.
