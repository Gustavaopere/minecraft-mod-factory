'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const core = require('./core/index.js');
const plugin = require('./blockbench-plugin/plugin_adapter.js');
const standalone = require('./asset_toolkit.js');

function assertGeckoCoreApi(api, surface) {
  assert.equal(api.GECKOLIB4_AUTHORITY?.runtimeVersion, '4.9.2', `${surface} authority pin`);
  assert.equal(typeof api.validateGeckoLib4GeoDocument, 'function', `${surface} geo validator`);
  assert.equal(typeof api.validateGeckoLib4AnimationDocument, 'function', `${surface} animation validator`);
  assert.equal(typeof api.serializeGeckoLib4EffectMarker, 'function', `${surface} effect serializer`);
  assert.equal(typeof api.createGeckoLib4ExportPlan, 'function', `${surface} export planner`);
}

test('PR6 GeckoLib core contract is exported by modular core', () => {
  assertGeckoCoreApi(core, 'core');
});

test('PR6 Blockbench adapter is exported by plugin adapter', () => {
  assert.equal(typeof plugin.createBlockbenchGeckoLib4Adapter, 'function');
});

test('PR6 GeckoLib core and Blockbench adapter are exported by deterministic standalone bundle', () => {
  assertGeckoCoreApi(standalone, 'standalone');
  assert.equal(typeof standalone.createBlockbenchGeckoLib4Adapter, 'function');
});
