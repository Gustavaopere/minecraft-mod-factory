'use strict';

const fs = require('node:fs');
const path = require('node:path');
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

test('PR6 workflow revalidates GeckoLib provider gates after merge to main', () => {
  const workflowPath = path.resolve(__dirname, '../../../../.github/workflows/factory-art-pr6-geckolib4-adapter.yml');
  const workflow = fs.readFileSync(workflowPath, 'utf8');
  const pushBlock = workflow.match(/push:\s*\n\s*branches:\s*\n((?:\s*-\s*[^\n]+\n?)+)/);
  assert.ok(pushBlock, 'PR6 workflow must declare explicit push branches');
  const branches = Array.from(pushBlock[1].matchAll(/^\s*-\s*([^\s#]+)\s*$/gm), (match) => match[1]);
  assert.ok(branches.includes('feat/art-pr6-geckolib4-adapter'));
  assert.ok(branches.includes('main'), 'PR6 workflow must run on main for post-merge provider validation');
});
