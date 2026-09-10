#!/usr/bin/env python3
from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLKIT = ROOT / "art/tooling/blockbench/asset-toolkit"


class M5NamingContractTest(unittest.TestCase):
    def test_toolkit_has_neutral_factory_surface_with_legacy_ids_documented(self) -> None:
        self.assertTrue(TOOLKIT.is_dir(), "Factory Asset Toolkit has not been materialized")
        relative_files = [path.relative_to(TOOLKIT).as_posix() for path in TOOLKIT.rglob("*") if path.is_file()]
        self.assertIn("asset_toolkit.js", relative_files)
        self.assertIn("asset_toolkit.test.js", relative_files)
        self.assertIn("COMPATIBILITY.md", relative_files)
        for relative in relative_files:
            self.assertNotIn("rpg-asset-toolkit", relative.lower())
            self.assertNotIn("rpg_asset_toolkit", relative.lower())

        compatibility = (TOOLKIT / "COMPATIBILITY.md").read_text(encoding="utf-8")
        self.assertIn("rpg_asset_toolkit", compatibility)
        self.assertIn("legacy compatibility", compatibility.lower())

        plugin_adapter = (TOOLKIT / "blockbench-plugin/plugin_adapter.js").read_text(encoding="utf-8")
        self.assertIn("Plugin.register('rpg_asset_toolkit'", plugin_adapter)
        self.assertIn("Minecraft Mod Factory Asset Toolkit", plugin_adapter)
        self.assertNotIn("RPG Asset Toolkit", plugin_adapter)
        self.assertNotIn("RPG Asset MCP", plugin_adapter)

        build_script = (TOOLKIT / "build_toolkit_bundle.js").read_text(encoding="utf-8")
        self.assertIn("asset_toolkit.js", build_script)
        self.assertNotIn("rpg_asset_toolkit.js", build_script)

        package = json.loads((TOOLKIT / "mcp-sidecar/package.json").read_text(encoding="utf-8"))
        self.assertEqual(package.get("name"), "@minecraft-mod-factory/asset-mcp-sidecar")
        lock = json.loads((TOOLKIT / "mcp-sidecar/package-lock.json").read_text(encoding="utf-8"))
        self.assertEqual(lock.get("name"), "@minecraft-mod-factory/asset-mcp-sidecar")
        self.assertEqual(lock.get("packages", {}).get("", {}).get("name"), "@minecraft-mod-factory/asset-mcp-sidecar")


if __name__ == "__main__":
    unittest.main()
