# Golden Sample — Model Asset Contract

Status: **REFERENCE-ONLY — not a runtime registration and not evidence of shipped gameplay.**

Asset ID: `golden_reference_focus_relic`

## Source of truth

- Project-owned native `.bbmodel`: `UNRESOLVED`.
- Normalized structural fixture: `validator-project-fixture.json`.
- Toolkit profile: `TOOLKIT-PROFILE.json`.
- Real texture source: `UNRESOLVED`.
- Exported GeckoLib geometry/animation resources: `UNRESOLVED`.

The JSON fixture is not a Blockbench file and cannot be promoted to source-of-truth art.

## Model hierarchy contract

| Bone | Purpose | Pivot intent | Runtime dependency |
|---|---|---|---|
| `root` | stable model root | reference origin | `UNRESOLVED` |
| `cast_hand` | animation control for cast motion | upper/forward control region | `UNRESOLVED` |
| `vfx_anchor` | presentation attachment parent | near forward/top cast region | `UNRESOLVED` |

Locator-like attachment:

- `spell_muzzle` → parent `vfx_anchor`.
- Intended use: future cast/trail spawn reference point.
- Exact provider consumer/API: `UNRESOLVED`.

Bone names are lower_snake_case and should remain stable once a real runtime consumer exists.

## Geometry contract

The normalized fixture carries one cube-like element, `focus_core`, solely to exercise bounds, pivot, face, UV, texture-reference, and max-span validation.

- Fixture `from`: `[-2, 0, -2]`
- Fixture `to`: `[2, 8, 2]`
- Fixture span: `4 x 8 x 4`
- Production cube count/topology: `UNRESOLVED`
- Production scale: `UNRESOLVED`

No universal project geometry budget is inferred from this sample.

## UV and texture contract

- Fixture texture metadata: `golden_reference_focus_relic.png`, 64 x 64, UUID `tex-main`.
- Actual PNG asset: `UNRESOLVED` and intentionally absent.
- Final palette/material separation: `UNRESOLVED`.
- Final texel density: `UNRESOLVED`.
- UV approval requires a real source model and image evidence.

## Animation contract

Required names:

- `animation.golden_reference_focus_relic.idle`
- `animation.golden_reference_focus_relic.cast`

Fixture lengths/loop modes are structural metadata for validator coverage, not approved final keyframe timing. Real keyframes/easing/controller wiring remain `UNRESOLVED`.

## Transform and attachment contract

- Pivots must remain finite and intentional.
- `spell_muzzle` must stay Locator-like rather than being converted into fake cube geometry solely for validation.
- Any future hand/item transform needs first- and third-person visual evidence.
- Any future VFX attachment must consume a proven provider-native hook or project bridge; exact hook is `UNRESOLVED`.

## Export/runtime contract

- Blockbench GeckoLib plugin/exporter version: `UNRESOLVED`.
- Geometry export path: `UNRESOLVED`.
- Animation export path: `UNRESOLVED`.
- Renderer/model class: `UNRESOLVED`.
- Client registration: `UNRESOLVED`.
- Dedicated-server classloading boundary: `UNRESOLVED` until runtime integration exists.

## QA state

Structural fixture validation can PASS deterministically. Native editor, texture, first-person, third-person, animation playback, lighting, combat, and multiplayer visual acceptance remain `PENDING` because no production asset is supplied.
