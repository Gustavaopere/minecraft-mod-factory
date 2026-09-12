# Minecraft Art Golden Samples

Status: **MIXED CORPUS** — legacy samples remain `REFERENCE-ONLY`; the GeckoLib simple-mob sample is a native source prepared for real handoff, not yet runtime/I6 evidence.

This area contains two deliberately different evidence classes:

- reference/process examples that demonstrate Factory contracts without claiming native authoring or runtime proof;
- native Golden Samples whose authoring source is preserved in its original format and whose real handoff state remains fail-closed until physical evidence exists.

## What is authoritative

Repository code/build configuration and the exact physical modlist remain authoritative. Any runtime/provider/API claim not proven by repository, JAR, exact-version provider evidence, or a completed physical handoff stays unresolved or explicitly unproven.

Latest physical-modlist snapshot checked for the reference corpus on 2026-09-08: **595 top-level entries**. Installed candidates relevant to that corpus include:

- GeckoLib 4.9.2 for Minecraft 1.21.1/NeoForge;
- Photon 2.2.6.a;
- Lodestone 1.8.2.

`Particle Effects 1.5.0+1.21.1+neoforge` is also installed, but it is a client-side presentation mod for effect/status particles rather than a general project-owned VFX authoring backend, so it is deliberately excluded from provider selection.

AAA Particles 2.2.3 and AAA Particles World 2.0.0 were present in the earlier creation-time snapshot but are **absent from the latest physical modlist**. Where they remain visible in the VFX matrix, they are retained only as explicit negative drift evidence and must not be selected as providers while absent.

For project-owned VFX, current routing intent is `provider-native → Photon candidate → Lodestone candidate → vanilla/custom particle fallback`. This does not bypass exact-version capability checks or runtime-health gates.

Presence is not API proof. No provider-native method/signature is asserted solely from presence.

## Samples

- `geckolib4-simple-mob/` — `golden_sample_mob_geckolib4`, first project-owned native `.bbmodel` Golden Sample; state `PREPARED_FOR_REAL_HANDOFF`. Its `expected/` files are contract fixtures, not exporter evidence, and I6 remains incomplete until real Blockbench export/reopen/runtime evidence exists.
- `model-asset/` — `golden_reference_focus_relic`, a `REFERENCE-ONLY` normalized structural fixture plus completed model/animation contracts.
- `spell/` — `golden_reference_arcane_bolt`, a `REFERENCE-ONLY` presentation/VFX/audio/QA reference with gameplay/runtime fields intentionally unresolved.

## Reference-only fixture boundary

`model-asset/validator-project-fixture.json` is normalized input for the project-owned Minecraft Mod Factory Asset Toolkit. It is **not** a Blockbench `.bbmodel`, is not an exporter artifact, and is not intended to ship in a resource pack.

The fixture contains metadata for one texture slot so Toolkit texture-reference validation can run; no PNG art is supplied or claimed for that reference sample.

Do not copy or rename the normalized fixture as if it were a native Blockbench source.

## Native Golden Sample boundary

`geckolib4-simple-mob/golden-sample-mob.bbmodel` is the native authoring source and must remain the source of truth. The committed PNG next to it is the canonical texture source. No provider conversion may replace the `.bbmodel` silently.

`geckolib4-simple-mob/expected/` is deterministic contract/reference output only. Real exporter-produced files belong under that sample's `actual/` directory and may be classified as handoff evidence only after the manifest is advanced by verified physical steps.

## How to use this corpus

For the legacy/reference examples:

1. Copy only the relevant brief/contract structure.
2. Replace the `golden_reference_*` identity with the real project identity.
3. Resolve every `UNRESOLVED` field from repository/JAR/exact-version provider evidence.
4. Create real model/texture/audio/VFX sources through the proper pipeline.
5. Run structural validation.
6. Capture actual editor/in-game/multiplayer evidence before changing QA from `PENDING` to `PASS`.

For native Golden Samples, preserve their native source and advance the handoff manifest only when each corresponding editor/export/reopen/runtime gate has objective evidence.

## Validation

The reference corpus remains guarded by:

```bash
node art/golden-samples/validate_golden_samples.js
node art/golden-samples/validate_reference_evidence.js
```

The native GeckoLib sample adds:

```bash
node art/golden-samples/geckolib4-simple-mob/validate_golden_sample.js
node --test art/golden-samples/geckolib4-simple-mob/golden_sample.test.js
```

The native validator reuses the Factory GeckoLib adapter and extension registry and fails closed if source authority, provider pins, expected-output classification, or I6 evidence state drifts.
