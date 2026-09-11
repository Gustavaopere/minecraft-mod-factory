const test = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const bundleBuilder = require('./build_toolkit_bundle.js');

const REQUIRED_LIVE_MODULES = [
  'live-bridge/protocol.js',
  'live-bridge/project_snapshot.js',
  'live-bridge/fingerprint.js',
  'live-bridge/read_only_router.js',
  'live-bridge/blockbench_bridge_client.js',
  'blockbench-plugin/live_bridge_adapter.js',
];

const REQUIRED_MUTATION_MODULES = [
  'core/mutations/mutation_engine.js',
  'blockbench-plugin/modeling_adapter.js',
];

const REQUIRED_UV_TEXTURE_MODULES = [
  'core/uv-texture/uv_texture_engine.js',
  'blockbench-plugin/uv_texture_adapter.js',
];

const REQUIRED_ANIMATION_MODULES = [
  'core/animation/animation_engine.js',
  'blockbench-plugin/animation_adapter.js',
];

function runBundle({isWeb, nativeRequire}) {
  const actions = new Map();
  let metadata = null;
  class FakeAction {
    constructor(id, definition = {}) {
      this.id = id;
      this.definition = definition;
      actions.set(id, this);
    }
    delete() { actions.delete(this.id); }
  }
  const context = {
    module: {exports: {}},
    require: nativeRequire,
    Plugin: {
      register(id, definition) {
        assert.equal(id, 'rpg_asset_toolkit');
        metadata = definition;
        definition.onload();
      },
    },
    Action: FakeAction,
    MenuBar: {menus: {tools: {addAction() {}}}},
    Blockbench: {
      isWeb,
      version: '5.1.6',
      Project: null,
      showMessageBox() {},
      showQuickMessage() {},
      textPrompt() {},
    },
    Plugins: {installed: []},
    console,
    setTimeout,
    clearTimeout,
    setInterval,
    clearInterval,
    TextEncoder,
    TextDecoder,
  };
  vm.runInNewContext(bundleBuilder.buildBundle(), context, {filename: 'asset_toolkit.generated.js'});
  return {context, metadata, actions};
}

test('standalone bundle includes approved live bridge, modeling, UV/texture, and generic animation modules with only explicit safe native crypto', () => {
  for (const moduleId of REQUIRED_LIVE_MODULES.concat(
    REQUIRED_MUTATION_MODULES,
    REQUIRED_UV_TEXTURE_MODULES,
    REQUIRED_ANIMATION_MODULES,
  )) {
    assert.ok(bundleBuilder.SOURCE_MODULES.includes(moduleId), `bundle missing ${moduleId}`);
  }
  assert.deepEqual(bundleBuilder.NATIVE_MODULE_ALLOWLIST, ['node:crypto']);
  assert.equal(bundleBuilder.validateExternalRequires(), true);
});

test('bundle generator rejects native imports outside the explicit allowlist', () => {
  assert.equal(bundleBuilder.isAllowedNativeModule('node:crypto'), true);
  for (const moduleId of ['fs', 'node:fs', 'process', 'child_process', 'https', 'net', 'tls', 'electron']) {
    assert.equal(bundleBuilder.isAllowedNativeModule(moduleId), false, `unexpected native allowlist entry: ${moduleId}`);
  }
});

test('web Blockbench can load the both-variant toolkit without native require or desktop mutation/live bridge actions', () => {
  const {context, metadata, actions} = runBundle({isWeb: true, nativeRequire: undefined});
  assert.ok(metadata);
  assert.equal(metadata.variant, 'both');
  assert.equal(typeof context.module.exports.createBridgeConnection, 'function');
  assert.equal(typeof context.module.exports.buildBridgeUrl, 'function');
  assert.equal(typeof context.module.exports.validateMutationBatch, 'function');
  assert.equal(typeof context.module.exports.applyMutationBatch, 'function');
  assert.equal(typeof context.module.exports.validateUvTextureBatch, 'function');
  assert.equal(typeof context.module.exports.applyUvTextureBatch, 'function');
  assert.equal(typeof context.module.exports.validateAnimationBatch, 'function');
  assert.equal(typeof context.module.exports.applyAnimationBatch, 'function');
  assert.equal(typeof context.module.exports.validateLoopSeam, 'function');
  assert.equal(typeof context.module.exports.diagnoseFootSlide, 'function');
  assert.ok(actions.has('rpg_asset_toolkit_validate'));
  assert.ok(actions.has('rpg_asset_toolkit_validate_profile'));
  assert.equal(actions.has('rpg_asset_toolkit_modeling_mutation_batch'), false);
  assert.equal(actions.has('rpg_asset_toolkit_uv_texture_batch'), false);
  assert.equal(actions.has('rpg_asset_toolkit_animation_batch'), false);
  assert.equal([...actions.keys()].some((id) => id.includes('live_bridge')), false);
});

test('desktop Blockbench registers lazy local mutation and live bridge controls without touching native crypto at plugin load', () => {
  const nativeCalls = [];
  const nativeRequire = (moduleId) => {
    nativeCalls.push(moduleId);
    if (moduleId !== 'node:crypto') throw new Error(`unexpected native module ${moduleId}`);
    return require('node:crypto');
  };
  const {metadata, actions} = runBundle({isWeb: false, nativeRequire});
  assert.equal(metadata.variant, 'both');
  assert.equal(metadata.version, '0.6.0');
  for (const id of [
    'rpg_asset_toolkit_modeling_mutation_batch',
    'rpg_asset_toolkit_uv_texture_batch',
    'rpg_asset_toolkit_animation_batch',
    'rpg_asset_toolkit_live_bridge_connect',
    'rpg_asset_toolkit_live_bridge_disconnect',
    'rpg_asset_toolkit_live_bridge_status',
  ]) assert.ok(actions.has(id), `missing desktop action ${id}`);
  assert.deepEqual(nativeCalls, [], 'desktop plugin load must not request native crypto before a mutation or connection attempt');
});
