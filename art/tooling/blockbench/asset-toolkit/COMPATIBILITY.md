# Asset Toolkit legacy compatibility

M5 moved the canonical Toolkit to `art/tooling/blockbench/asset-toolkit/` and neutralized repository/path naming and user-facing branding to **Minecraft Mod Factory Asset Toolkit**.

For legacy compatibility, the Blockbench plugin ID `rpg_asset_toolkit` and existing action IDs prefixed `rpg_asset_toolkit_` are intentionally retained. They are compatibility identifiers only; they do not make the RPG repository an authority and must not be used as new repository/path naming. Changing those IDs requires an explicit compatibility migration.

The canonical generated source bundle remains `asset_toolkit.js`. It is derived from modular source via `build_toolkit_bundle.js` and must never be edited by hand.

Blockbench 5.1.6 physical installation proved that a local plugin file must use a basename matching the ID passed to `Plugin.register(...)`. The local-install artifact is therefore named `rpg_asset_toolkit.js`. It is not a second implementation and is intentionally not committed: generate it on demand with `node sync_blockbench_install_artifact.js --write`. The generated file must remain byte-for-byte identical to `asset_toolkit.js` and is ignored by Git.

When modular source changes require bundle regeneration, run `node build_toolkit_bundle.js --write` first. Before local Blockbench installation, run `node sync_blockbench_install_artifact.js --write`; `node sync_blockbench_install_artifact.js --check` verifies the generated artifact. CI regenerates and validates the install artifact from the canonical bundle so packaging drift fails closed without storing duplicate generated code in Git.
