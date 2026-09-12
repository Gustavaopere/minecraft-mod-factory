'use strict';

const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const assert = require('node:assert/strict');
const sync = require('./sync_blockbench_install_artifact.js');

const ROOT = __dirname;
const CANONICAL_BUNDLE = path.join(ROOT, 'asset_toolkit.js');
const INSTALL_ARTIFACT = path.join(ROOT, 'rpg_asset_toolkit.js');
const PLUGIN_ADAPTER = path.join(ROOT, 'blockbench-plugin', 'plugin_adapter.js');

test('Blockbench install artifact basename matches Plugin.register id', () => {
  const source = fs.readFileSync(PLUGIN_ADAPTER, 'utf8');
  const pluginId = sync.pluginIdFromSource(source);
  assert.equal(pluginId, 'rpg_asset_toolkit');
  assert.equal(sync.installArtifactFilename(), `${pluginId}.js`);
  assert.equal(path.basename(INSTALL_ARTIFACT), sync.installArtifactFilename());
});

test('Blockbench install artifact exists and is byte-identical to the canonical bundle', () => {
  assert.equal(fs.existsSync(INSTALL_ARTIFACT), true, 'rpg_asset_toolkit.js must be committed for local Blockbench installation');
  assert.deepEqual(fs.readFileSync(INSTALL_ARTIFACT), fs.readFileSync(CANONICAL_BUNDLE));
  assert.equal(sync.checkInstallArtifact(), true);
});
