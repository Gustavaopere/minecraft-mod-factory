# Asset Toolkit legacy compatibility

M5 moved the canonical Toolkit to `art/tooling/blockbench/asset-toolkit/` and neutralized filenames and user-facing branding to **Minecraft Mod Factory Asset Toolkit**.

For legacy compatibility, the Blockbench plugin ID `rpg_asset_toolkit` and existing action IDs prefixed `rpg_asset_toolkit_` are intentionally retained. They are compatibility identifiers only; they do not make the RPG repository an authority and must not be used as new repository/path naming. Changing those IDs requires an explicit compatibility migration.

The canonical generated plugin filename is `asset_toolkit.js`. The generated bundle remains derived from modular source via `build_toolkit_bundle.js` and must never be edited by hand.
