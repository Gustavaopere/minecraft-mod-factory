# Native Golden Samples

This directory is the source-authority area for project-owned native authoring samples. It is intentionally separate from `art/golden-samples/`, which remains the closed `REFERENCE-ONLY` process/reference corpus.

Native formats such as `.bbmodel` must remain authoritative and must not be silently converted to another provider or intermediate format. Provider-specific exported artifacts are derived handoff outputs, not replacements for the native source.

## Samples

- `geckolib4-simple-mob/` — first project-owned native GeckoLib 4 sample using the `geckolib4_entity` profile, Blockbench 5.1.6, project format 5.0, `geckolib_model`, GeckoLib runtime 4.9.2, and `geckolib@4.2.5`.

The sample starts at `PREPARED_FOR_REAL_HANDOFF`. Files under `expected/` are deterministic contract fixtures classified as `EXPECTED_CONTRACT_NOT_EXPORTER_EVIDENCE`; they are not proof that Blockbench exported them. Real exporter output belongs under the sample's `actual/` directory only after the physical handoff.

`I6_REAL_HANDOFF` remains incomplete until the native source is opened in the real editor, round-tripped, exported, reopened, and backed by the required runtime evidence. The manifest must remain fail-closed until those gates have objective evidence.

## Validation

From the repository root:

```bash
node art/native-golden-samples/geckolib4-simple-mob/validate_golden_sample.js
node --test art/native-golden-samples/geckolib4-simple-mob/golden_sample.test.js
```
