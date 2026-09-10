# Golden Sample — Animation Brief

Status: **REFERENCE-ONLY — not a runtime registration and not evidence of shipped gameplay.**

Asset ID: `golden_reference_focus_relic`

## Required animation identities

- `animation.golden_reference_focus_relic.idle`
- `animation.golden_reference_focus_relic.cast`

The normalized fixture declares names, lengths, loop modes, and animator targets only. It does not contain native Blockbench keyframes.

## Idle intent

- Purpose: subtle readability while held without competing with combat animation.
- Fixture duration: 1.0 s, loop.
- Production amplitude/easing/keyframes: `UNRESOLVED`.
- Player-hand synchronization: `UNRESOLVED`.

## Cast intent

- Purpose: communicate wind-up, release, and settle around a future server-authoritative cast.
- Fixture duration: 0.6 s, once.
- Intended timing landmarks for later real animation:
  - 0.00–0.20: anticipation;
  - around 0.20: release landmark;
  - 0.20–0.45: recoil/follow-through;
  - 0.45–0.60: settle.
- Exact keyframes/easing: `UNRESOLVED`.
- Exact event marker/API linking release to gameplay: `UNRESOLVED`.

## Bone ownership

- `root`: stable base.
- `cast_hand`: primary cast-motion target.
- `vfx_anchor`: attachment parent; avoid decorative motion that makes the future spawn point causally ambiguous.
- `spell_muzzle`: Locator-like point; not an animation bone.

## Runtime boundary

- GeckoLib presence is verified as a candidate at 4.9.2.
- Animation controller class/API: `UNRESOLVED`.
- Trigger/network synchronization: `UNRESOLVED`.
- Client prediction policy: `UNRESOLVED`.
- Dedicated-server behavior: no animation code exists in this reference.

## Acceptance

- Fixture name/target validation: deterministic.
- Native Blockbench playback: `PENDING`.
- First-person cast readability: `PENDING`.
- Third-person cast readability: `PENDING`.
- Multiplayer timing against server-confirmed release: `PENDING`.
