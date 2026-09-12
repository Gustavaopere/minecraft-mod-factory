# Asset Toolkit legacy compatibility

M5 moved the canonical Toolkit to `art/tooling/blockbench/asset-toolkit/` and neutralized repository/path naming and user-facing branding to **Minecraft Mod Factory Asset Toolkit**.

For legacy compatibility, the Blockbench plugin ID `rpg_asset_toolkit` and existing action IDs prefixed `rpg_asset_toolkit_` are intentionally retained. They are compatibility identifiers only; they do not make the RPG repository an authority and must not be used as new repository/path naming. Changing those IDs requires an explicit compatibility migration.

The canonical generated source bundle remains `asset_toolkit.js`. It is derived from modular source via `build_toolkit_bundle.js` and must never be edited by hand.

Blockbench 5.1.6 physical installation proved that a local plugin file must use a basename matching the ID passed to `Plugin.register(...)`. Therefore the committed local-install artifact is `rpg_asset_toolkit.js`. It is not an independent implementation: it must remain byte-for-byte identical to `asset_toolkit.js` and is synchronized with `sync_blockbench_install_artifact.js`.

When source changes require bundle regeneration, run `node build_toolkit_bundle.js --write` followed by `node sync_blockbench_install_artifact.js --write`. CI fails closed if either the canonical bundle is stale or the install artifact is missing, stale, or no longer filename-compatible with the registered plugin ID.
