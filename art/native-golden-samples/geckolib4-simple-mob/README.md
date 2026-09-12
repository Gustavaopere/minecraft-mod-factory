# GeckoLib 4 native Golden Sample — simple mob

Status: **PREPARED_FOR_REAL_HANDOFF**.

The legacy/reference corpus under `art/golden-samples/` remains explicitly `REFERENCE-ONLY`; this directory is the separate native handoff candidate and must not be conflated with that reference evidence.

This is the first production-shaped native Blockbench Golden Sample in the Factory. It is intentionally small: one GeckoLib entity model with a root/body/head/two-leg rig, one locator, one canonical PNG texture, and two authoring animations (`idle` and `walk`).

## Authority

- native source of truth: `golden-sample-mob.bbmodel`
- canonical texture source: `golden-sample-mob.png`
- Blockbench baseline: `5.1.6`
- Blockbench project format: `5.0`
- GeckoLib Blockbench model format: `geckolib_model`
- Factory profile: `geckolib4_entity`
- physical/runtime contract: GeckoLib `4.9.2`
- Blockbench extension contract: `geckolib@4.2.5`

The `.bbmodel` structure is grounded in the Blockbench 5.1.6 project codec and the GeckoLib 4.2.5 plugin model-format/property contracts. It is project-authored; no third-party model geometry or texture is copied into this sample.

## Expected vs actual exports

`expected/` contains contract fixtures for geometry and animation. They are deliberately classified as `EXPECTED_CONTRACT_NOT_EXPORTER_EVIDENCE`.

They prove that the expected resource shapes remain accepted by the audited Factory GeckoLib adapter. They do **not** prove that Blockbench exported those exact files.

Real Blockbench output belongs under `actual/` only after the physical handoff. `MANIFEST.json` remains fail-closed until that evidence exists.

## Current gate

The automated gate proves:

- native `.bbmodel` metadata and authoring structure;
- stable group/element UUID references;
- one locator and four cubes;
- embedded texture bytes equal the committed PNG;
- `idle` and `walk` authoring animations exist;
- provider/runtime/plugin pins match Factory authorities;
- expected `.geo.json` and `.animation.json` pass the audited GeckoLib 4 adapter validators;
- the adapter export plan preserves `.bbmodel` as source authority;
- I6 cannot be marked complete before real editor/export/reopen/runtime evidence exists.

Run from the repository root:

```bash
node art/native-golden-samples/geckolib4-simple-mob/validate_golden_sample.js
node --test art/native-golden-samples/geckolib4-simple-mob/golden_sample.test.js
```

## Handoff boundary

Do not edit the source by converting it to another provider format. The next physical gate is a real Blockbench 5.1.6 open/export/reopen cycle using the already-installed GeckoLib 4.2.5 extension and Asset Toolkit. Until that happens, `exporterProduced`, `reopenValidated`, `runtimeValidated`, and `f4I6Evidence` remain false.
