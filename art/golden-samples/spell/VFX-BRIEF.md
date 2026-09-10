# Golden Sample — VFX Brief

Status: **REFERENCE-ONLY — not a runtime registration and not evidence of shipped gameplay.**

Reference ID: `golden_reference_arcane_bolt`

## Readability goal

Make phase changes obvious without using one oversized emitter for every job. The effect should read as charge → release → moving projectile → confirmed impact → short decay while preserving target silhouette and combat readability.

## Layer plan

### Anticipation
- Layer A: compact emissive core at hand/focus.
- Layer B: sparse inward particles.
- Layer C: optional small ring only if it does not obscure first-person view.

### Release
- Layer A: short flash at `spell_muzzle`-equivalent attachment.
- Layer B: directional streak/cone supporting travel direction.
- Layer C: minimal burst debris/sparks.

### Travel / Active
- Layer A: compact projectile core.
- Layer B: subtle halo.
- Layer C: narrow short-lived trail.

### Impact / Resolve
- Layer A: central flash.
- Layer B: radial ring/fragments.
- Layer C: outcome-specific residue only after authoritative result.

### Decay
- sparse residual motes/fade; no gameplay effect.

## Provider matrix

Latest physical-modlist snapshot checked on 2026-09-08 contains 595 top-level entries. Rows retained for removed providers are explicit negative drift evidence, not selectable backends.

| Candidate | Verified presence | Use decision | Exact API/asset format |
|---|---|---|---|
| Photon 2.2.6.a | yes | `UNRESOLVED` | `UNRESOLVED` |
| Lodestone 1.8.2 | yes | `UNRESOLVED` | `UNRESOLVED` |
| AAA Particles 2.2.3 | no — removed from current physical modlist | `UNRESOLVED` | `UNRESOLVED` |
| AAA Particles World 2.0.0 | no — removed from current physical modlist | `UNRESOLVED` | `UNRESOLVED` |

`Particle Effects 1.5.0+1.21.1+neoforge` is installed, but it is a client-side visual mod for status/effect particles rather than an authoring backend for project-owned VFX; it is therefore not a selectable provider in this matrix.

Provider-native first. For project-owned effects without a provider-native VFX path, the intended routing order is:

`provider-native → Photon candidate → Lodestone candidate → vanilla/custom particle fallback`

This is a capability preference, not proof that either optional backend is operational for a particular effect. Photon must pass runtime-health and exact-version capability checks before selection. Lodestone must pass exact-version code/API verification before selection. Removed providers remain unavailable while absent.

Blockbench remains an authoring/handoff surface for model geometry, anchors, timing markers, transforms, captures and briefs. No Blockbench extension is treated as a replacement Minecraft particle runtime unless an exact extension/runtime contract is later proven.

## Causality

- Anticipation may be local intent only.
- Release/travel authoritative start condition: `UNRESOLVED`.
- Impact must consume authoritative result evidence; exact event/hook is `UNRESOLVED`.
- Deduplication token/event identity: `UNRESOLVED`.

## Performance contract

- particle/emitter budgets: `UNRESOLVED` pending real provider profiling;
- max visible distance/culling: `UNRESOLVED`;
- simultaneous caster stress target: `UNRESOLVED`;
- fallback behavior: `UNRESOLVED`, fail-safe required.

## Evidence

No provider graph/effect file, screenshot, capture, or profiler trace is supplied. Visual/performance acceptance remains `PENDING`.
