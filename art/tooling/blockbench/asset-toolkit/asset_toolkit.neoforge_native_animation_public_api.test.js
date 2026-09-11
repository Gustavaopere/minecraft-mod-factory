'use strict';

const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const assert = require('node:assert/strict');

const core = require('./core/index.js');
const blockbenchPlugin = require('./blockbench-plugin/plugin_adapter.js');
const standalone = require('./asset_toolkit.js');

function assertCoreApi(api, surface) {
  assert.equal(api.NEOFORGE_NATIVE_ANIMATION_AUTHORITY?.neoforgeVersion, '21.1.248', `${surface} authority`);
  assert.equal(typeof api.validateNeoForgeNativeAnimationDocument, 'function', `${surface} validator`);
  assert.equal(typeof api.serializeNeoForgeNativeAnimation, 'function', `${surface} serializer`);
  assert.equal(typeof api.createNeoForgeNativeAnimationExportPlan, 'function', `${surface} export plan`);
}

function assertBlockbenchApi(api, surface) {
  assert.equal(typeof api.createBlockbenchNeoForgeNativeAnimationAdapter, 'function', `${surface} Blockbench adapter`);
}

test('PR8 core contract is exported by modular core', () => {
  assertCoreApi(core, 'core');
});

test('PR8 Blockbench adapter is exported by the modular plugin surface', () => {
  assertBlockbenchApi(blockbenchPlugin, 'blockbench-plugin');
});

test('PR8 core and Blockbench contracts are exported by deterministic standalone bundle', () => {
  assertCoreApi(standalone, 'standalone');
  assertBlockbenchApi(standalone, 'standalone');
});

test('PR8 workflow revalidates NeoForge native animation gates after merge to main', () => {
  const workflowPath = path.resolve(__dirname, '../../../../.github/workflows/factory-art-pr8-neoforge-native-animation.yml');
  const workflow = fs.readFileSync(workflowPath, 'utf8');
  const pushBlock = workflow.match(/push:\s*\n\s*branches:\s*\n((?:\s*-\s*[^\n]+\n?)+)/);
  assert.ok(pushBlock, 'PR8 workflow must declare explicit push branches');
  const branches = Array.from(pushBlock[1].matchAll(/^\s*-\s*([^\s#]+)\s*$/gm), (match) => match[1]);
  assert.ok(branches.includes('feat/art-pr8-neoforge-native-animation'));
  assert.ok(branches.includes('main'), 'PR8 workflow must run on main for post-merge provider validation');
});
