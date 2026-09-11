'use strict';

const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const assert = require('node:assert/strict');

const core = require('./core/index.js');
const blockbenchPlugin = require('./blockbench-plugin/plugin_adapter.js');
const standalone = require('./asset_toolkit.js');

function assertAzureCoreApi(api, surface) {
  assert.equal(api.AZURELIB3_AUTHORITY?.runtimeVersion, '3.1.11', `${surface} runtime authority pin`);
  assert.equal(api.AZURELIB3_AUTHORITY?.blockbenchPluginVersion, '2.1.5', `${surface} authoring plugin authority pin`);
  assert.equal(typeof api.validateAzureLib3GeoDocument, 'function', `${surface} geo validator`);
  assert.equal(typeof api.validateAzureLib3AnimationDocument, 'function', `${surface} animation validator`);
  assert.equal(typeof api.serializeAzureLib3EffectMarker, 'function', `${surface} effect serializer`);
  assert.equal(typeof api.createAzureLib3ExportPlan, 'function', `${surface} export planner`);
}

function assertAzureBlockbenchApi(api, surface) {
  assert.equal(typeof api.createBlockbenchAzureLib3Adapter, 'function', `${surface} Blockbench adapter`);
}

test('PR7 AzureLib core contract is exported by modular core', () => {
  assertAzureCoreApi(core, 'core');
});

test('PR7 AzureLib Blockbench adapter is exported by the modular plugin surface', () => {
  assertAzureBlockbenchApi(blockbenchPlugin, 'blockbench-plugin');
});

test('PR7 AzureLib core and Blockbench contracts are exported by deterministic standalone bundle', () => {
  assertAzureCoreApi(standalone, 'standalone');
  assertAzureBlockbenchApi(standalone, 'standalone');
});

test('PR7 workflow revalidates AzureLib provider gates after merge to main', () => {
  const workflowPath = path.resolve(__dirname, '../../../../.github/workflows/factory-art-pr7-azurelib3-adapter.yml');
  const workflow = fs.readFileSync(workflowPath, 'utf8');
  const pushBlock = workflow.match(/push:\s*\n\s*branches:\s*\n((?:\s*-\s*[^\n]+\n?)+)/);
  assert.ok(pushBlock, 'PR7 workflow must declare explicit push branches');
  const branches = Array.from(pushBlock[1].matchAll(/^\s*-\s*([^\s#]+)\s*$/gm), (match) => match[1]);
  assert.ok(branches.includes('feat/art-pr7-azurelib3-adapter'));
  assert.ok(branches.includes('main'), 'PR7 workflow must run on main for post-merge provider validation');
});
