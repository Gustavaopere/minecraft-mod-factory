# Blockbench Base Safe preset

`Base Safe` is the provider-neutral Blockbench authoring/QA preset required before any provider-specific preset is installed.

Canonical target for the current physical workstation: **Blockbench 5.1.6**.

The preset contract is `base-safe.json`. `preset.schema.json` defines its structural shape and `validate_base_safe.js` enforces the pinned catalog metadata and fail-closed policy.

## Authority and source pin

Third-party plugin metadata is pinned to the official Blockbench plugin catalog repository:

- repository: `JannisX11/blockbench-plugins`
- commit: `a33b2d88621cffc119f8e3d94795a2ec350c7290`
- catalog: `plugins.json`

A catalog update is not adopted implicitly. Version, minimum Blockbench version, variant and source path must be re-audited and updated in the preset and validator together.

## Components

The local `rpg_asset_toolkit` is first and remains governed by its own source/install-artifact contract. The third-party Base Safe set is exactly:

1. `asset_browser`
2. `reference_models`
3. `bone_view`
4. `cameras`
5. `resource_pack_utilities`
6. `uv_locker`
7. `missing_texture_highlighter`
8. `grayscale_preview`
9. `code_view`
10. `brush_tuna`
11. `colour_gradient_generator`

No provider-specific extension is allowed in this preset.

## Installation policy

Installation is always human and explicit. The MCP/Live Bridge never installs or executes these third-party extensions. Only one manual action is requested at a time and every installed extension requires a smoke before the next installation step.

`missing_texture_highlighter` and `code_view` do not declare an upstream `min_version` in the audited source. The Factory therefore records `SMOKE_REQUIRED_NO_MIN_VERSION`; it does not invent a minimum-version compatibility claim.

For entries that do declare `min_version`, the validator only proves the static numeric gate against Blockbench 5.1.6. It does not replace the physical post-install smoke.

## Risk and rollback

All entries are third-party local plugins. `asset_browser` and `resource_pack_utilities` explicitly request local filesystem access in their audited source and are classified accordingly. Rollback is removal through Blockbench's plugin interface. The local Asset Toolkit rollback is removal of its side-loaded artifact followed by a Blockbench restart.

## Validation

From the repository root:

```bash
node art/tooling/blockbench/base-safe/validate_base_safe.js --check
node --test art/tooling/blockbench/base-safe/base_safe.test.js
```

The dedicated CI workflow also revalidates the canonical Asset Toolkit bundle/install-artifact contract because the Toolkit is part of Base Safe.

A green contract/CI result authorizes only the next human installation step. It does not claim that all Base Safe plugins are physically installed or healthy.
