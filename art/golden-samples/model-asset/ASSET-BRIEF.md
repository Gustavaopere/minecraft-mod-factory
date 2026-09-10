# Golden Sample — Asset Brief

Status: **REFERENCE-ONLY — not a runtime registration and not evidence of shipped gameplay.**

## Identity

- Asset ID: `golden_reference_focus_relic`
- Asset type: animated held/focus relic reference
- Gameplay owner: `UNRESOLVED`
- Runtime consumer/class: `UNRESOLVED`
- Registry/resource ID: `UNRESOLVED`
- Intended source editor: Blockbench + GeckoLib workflow
- Multiplayer authority impact: none in this reference; runtime ownership is `UNRESOLVED`

## Purpose

Demonstrate a compact model contract with intentional hierarchy, one cast-hand control bone, one VFX attachment bone, one Locator-like muzzle point, one texture slot, and named idle/cast animations.

This describes an art-production reference only. It does not create an item, entity, renderer, animation controller, or network path.

## Visual intent

- Readable silhouette at held-item scale: compact vertical focus with a distinct central core.
- Shape language: simple primary mass, restrained secondary frame, clear forward-facing cast point.
- Material intent: dark mineral/metal body with a limited arcane-emissive accent; final palette is `UNRESOLVED` pending real art direction execution.
- Detail policy: macro silhouette first, then material separation, then controlled accent details.
- First-person obstruction target: `UNRESOLVED` until an actual model is rendered in game.

## Structural intent

- Required bones: `root`, `cast_hand`, `vfx_anchor`.
- Required Locator-like point: `spell_muzzle`, parented to `vfx_anchor`.
- Required animations: `animation.golden_reference_focus_relic.idle`, `animation.golden_reference_focus_relic.cast`.
- Normalized fixture cube span: 4 x 8 x 4 model units; this is validator data, not an approved production dimension budget.
- Production dimensions/scale: `UNRESOLVED`.

## Texture/UV intent

- Fixture texture slot: 64 x 64 metadata only.
- Real texture file: `UNRESOLVED`.
- Texel density: `UNRESOLVED` until a real source model/texture exists.
- UV rule: no overlap unless deliberate and documented; preserve readable material islands.

## Provider/export boundary

- GeckoLib presence: verified candidate, 4.9.2.
- Exact exporter/plugin version: `UNRESOLVED`.
- Runtime renderer/controller: `UNRESOLVED`.
- Export destination: `UNRESOLVED`.
- VFX provider/API for `spell_muzzle`: `UNRESOLVED`.

## Acceptance evidence

- Normalized Toolkit fixture: deterministic structural validation only.
- Native `.bbmodel`: `UNRESOLVED` / not supplied.
- Texture screenshot: `UNRESOLVED` / not supplied.
- First-person screenshot: `UNRESOLVED` / not supplied.
- Third-person screenshot: `UNRESOLVED` / not supplied.
- Multiplayer/dedicated-server impact: no runtime code in this sample.

Final visual acceptance remains `PENDING` until real asset evidence exists.
