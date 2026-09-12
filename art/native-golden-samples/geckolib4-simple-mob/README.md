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

The `.bbmodel` remains the authoring authority. No provider conversion was performed during the real handoff.

## Real Blockbench evidence

The source project was opened in Blockbench 5.1.6 with GeckoLib 4.2.5 active. A native round-trip copy was saved and reopened successfully, so `editorOpened=true` and `sourceRoundTripValidated=true` are now proven by the manual handoff evidence recorded in `MANIFEST.json`.

The physical GeckoLib exporter produced these files:

- `actual/golden_sample_mob.geo.json`
- `actual/golden_sample_mob.animation.json`

Their byte hashes are pinned in `MANIFEST.json`. The raw exporter filenames use the project identifier with underscores. The additional hyphenated files under `actual/` are explicitly classified as Factory canonical aliases and are byte-identical copies; they are not represented as exporter-origin files.

Observed GeckoLib 4.2.5 model behavior includes exporter-calculated visible bounds and an X-axis mirror for the left/right leg pivots and cube origins. Observed animation behavior uses the Bedrock animation codec shape `{ "vector": [...] }` and the codec coordinate convention that inverts X/Y rotation values relative to Blockbench authoring values. These behaviors are now regression-gated rather than rewritten to match the previous speculative fixtures.

## Expected vs actual exports

`expected/` remains a contract fixture surface and is still classified as `EXPECTED_CONTRACT_NOT_EXPORTER_EVIDENCE`.

After the physical export, the previous fixtures were reconciled to the observed GeckoLib 4.2.5 output. `actual/` remains the evidence authority for what the exporter physically produced; `expected/` is the regression contract derived from that proven behavior. The real-evidence validator requires semantic equality between them and verifies raw exporter SHA-256 hashes independently.

## Current gate

The automated gates prove:

- native `.bbmodel` metadata and authoring structure;
- stable group/element UUID references;
- one locator and four cubes;
- embedded texture bytes equal the committed PNG;
- `idle` and `walk` authoring animations exist;
- provider/runtime/plugin pins match Factory authorities;
- real model and animation export bytes are pinned;
- real `idle` and `walk` outputs match the source through the audited exporter coordinate convention;
- reconciled expected fixtures match actual exporter semantics;
- Factory canonical aliases remain byte-identical to the raw physical exports;
- `.bbmodel` remains the source authority;
- I6 still cannot complete before exported-output reopen and runtime evidence exist.

Run from the repository root:

```bash
node art/native-golden-samples/geckolib4-simple-mob/validate_golden_sample.js
node --test art/native-golden-samples/geckolib4-simple-mob/golden_sample.test.js
node art/native-golden-samples/geckolib4-simple-mob/validate_real_handoff_evidence.js
node --test art/native-golden-samples/geckolib4-simple-mob/real_handoff_evidence.test.js
```

## Handoff boundary

The physical exporter gate is now complete: `exporterProduced=true`.

The remaining gates are deliberately fail-closed:

- `reopenValidated=false`
- `runtimeValidated=false`
- `f4I6Evidence=false`

Do not mark the sample `REAL_HANDOFF_VALIDATED`, do not mark I6 complete, and do not unblock I7 until those remaining gates are proven.
