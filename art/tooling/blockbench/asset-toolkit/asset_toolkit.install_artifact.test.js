'use strict';

const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const assert = require('node:assert/strict');

const ROOT = __dirname;
const CANONICAL_BUNDLE = path.join(ROOT, 'asset_toolkit.js');
const INSTALL_ARTIFACT = path.join(ROOT, 'rpg_asset_toolkit.js');
const PLUGIN_ADAPTER = path.join(ROOT, 'blockbench-plugin', 'plugin_adapter.js');

test('Blockbench install artifact basename matches Plugin.register id', () => {
  const source = fs.readFileSync(PLUGIN_ADAPTER, 'utf8');
  const match = source.match(/Plugin\.register\(['"]([^'"]+)['"]/);
  assert.ok(match, 'Plugin.register id must be statically discoverable');
  assert.equal(path.basename(INSTALL_ARTIFACT, '.js'), match[1]);
});

test('Blockbench install artifact exists and is byte-identical to the canonical bundle', () => {
  assert.equal(fs.existsSync(INSTALL_ARTIFACT), true, 'rpg_asset_toolkit.js must be committed for local Blockbench installation');
  assert.deepEqual(fs.readFileSync(INSTALL_ARTIFACT), fs.readFileSync(CANONICAL_BUNDLE));
});
