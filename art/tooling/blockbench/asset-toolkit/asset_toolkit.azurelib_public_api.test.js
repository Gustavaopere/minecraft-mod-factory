'use strict';

const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const assert = require('node:assert/strict');

const core = require('./core/index.js');
const plugin = require('./blockbench-plugin/plugin_adapter.js');
const standalone = require('./asset_toolkit.js');

function assertAzureCoreApi(api, surface) {
  assert.equal(api.AZURELIB_AUTHORITY?.runtimeVersion, '3.1.11', `${surface} authority pin`);
  assert.equal(api.AZURELIB_AUTHORITY?.blockbenchPluginVersion, '2.1.5', `${surface} plugin pin`);
  assert.equal(api.AZURELIB_AUTHORITY?.blockbenchFormatId, 'azure_model', `${surface} Blockbench format`);
  assert.equal(api.AZURELIB_AUTHORITY?.animationCodecId, 'azure_animation', `${surface} animation codec`);
  assert.equal(typeof api.validateAzureLibGeoDocument, 'function', `${surface} geo validator`);
  assert.equal(typeof api.validateAzureLibAnimationDocument, 'function', `${surface} animation validator`);
  assert.equal(typeof api.serializeAzureLibEffectMarker, 'function', `${surface} effect serializer`);
  assert.equal(typeof api.createAzureLibExportPlan, 'function', `${surface} export planner`);
}

test('PR7 AzureLib core contract is exported by modular core', () => {
  assertAzureCoreApi(core, 'core');
});

test('PR7 Blockbench adapter is exported by plugin adapter', () => {
  assert.equal(typeof plugin.createBlockbenchAzureLibAdapter, 'function');
});

test('PR7 AzureLib core and Blockbench adapter are exported by deterministic standalone bundle', () => {
  assertAzureCoreApi(standalone, 'standalone');
  assert.equal(typeof standalone.createBlockbenchAzureLibAdapter, 'function');
});

test('PR7 workflow revalidates AzureLib provider gates after merge to main', () => {
  const workflowPath = path.resolve(__dirname, '../../../../.github/workflows/factory-art-pr7-azurelib-adapter.yml');
  const workflow = fs.readFileSync(workflowPath, 'utf8');
  const pushBlock = workflow.match(/push:\s*\n\s*branches:\s*\n((?:\s*-\s*[^\n]+\n?)+)/);
  assert.ok(pushBlock, 'PR7 workflow must declare explicit push branches');
  const branches = Array.from(pushBlock[1].matchAll(/^\s*-\s*([^\s#]+)\s*$/gm), (match) => match[1]);
  assert.ok(branches.includes('feat/art-pr7-azurelib-adapter'));
  assert.ok(branches.includes('main'), 'PR7 workflow must run on main for post-merge provider validation');
});
