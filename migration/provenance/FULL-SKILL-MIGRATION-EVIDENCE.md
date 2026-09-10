# Full Skill Migration — Execution Evidence

Status: IN PROGRESS

## Frozen source boundary

- Source repository: `Gustavaopere/neoforge-rpg-skilltree`
- Source revision: `2ecea4178aa7ac80f99955ab045e296da25376ec`
- Source scope: `PROJECT-INSTRUCTIONS/skills/**`
- Coverage authority: `migration/provenance/FULL-SKILL-MIGRATION-MANIFEST.json`

## Coverage and classification

The migration validator requires every blob under the frozen source scope to have exactly one source-to-Factory mapping. Active project-authored art skills are materialized under `art/skills/**`, promoted shared skills under `skills/library/**`, and deferred historical skills under `migration/provenance/historical-skills/**` as `REFERENCE_ONLY`.

Coverage was exercised in GitHub Actions before materialization commits were accepted. The migration does not promote deferred material merely because it is preserved.

## M5 — Asset Toolkit neutralization

The historical Blockbench toolkit is materialized as `art/tooling/blockbench/asset-toolkit/**` with neutral canonical filenames and Minecraft Mod Factory branding. The legacy Blockbench plugin/action identifiers prefixed with `rpg_asset_toolkit` remain compatibility identifiers only and are documented in `art/tooling/blockbench/asset-toolkit/COMPATIBILITY.md`.

The MCP sidecar package identity is finalized as `@minecraft-mod-factory/asset-mcp-sidecar` during materialization. M5 naming is guarded by `migration/full-skill-migration/test_m5_naming.py`.

## M6 — Golden Samples relocation

Golden Samples remain `REFERENCE-ONLY`. A dedicated RED was captured after relocation because historical relative imports no longer resolved from `art/golden-samples/**`.

- Dedicated failing workflow run: `34438470531`
- Root cause: relocation-sensitive imports were being adapted as if they remained under the historical `PROJECT-INSTRUCTIONS/skills/**` tree.
- Source fix commit: `f0a7c840386ab1e5206e9b9f4d286999ff9cea44`
- Materializer run with coverage + M5 + M6 pre-commit gates: `34438930797` — SUCCESS
- Persisted materialized commit: `c3a431dba55200ace26329d0227f6f1f35d5452f`

The materialized validators resolve:

- `art/golden-samples/validate_golden_samples.js` -> `../tooling/blockbench/asset-toolkit/asset_toolkit.js`
- `art/golden-samples/validate_reference_evidence.js` -> `../tooling/validators/validate_golden_reference_rendered_edges.js`

M6 relocation is guarded by `migration/full-skill-migration/test_m6_golden_relocation.py` and by the materializer before it commits generated output.

## Completion boundary

This document does not claim final migration completion. Final PASS still requires the persisted branch state to pass the aggregate skill/tooling/Golden Sample validation, MCP sidecar install/check/tests, reconciliation of the stable PR4 acceptance delta, final PR CI/merge-ref validation, and post-merge validation before any historical source cleanup is performed.
