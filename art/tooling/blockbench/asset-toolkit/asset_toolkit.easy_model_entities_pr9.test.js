'use strict';

const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const assert = require('node:assert/strict');

const core = require('./core/index.js');
const blockbenchPlugin = require('./blockbench-plugin/plugin_adapter.js');
const standalone = require('./asset_toolkit.js');

const ENTITY_PROFILE_ID = 'easy_model_entities_entity';
const BLOCK_ENTITY_PROFILE_ID = 'easy_model_entities_block_entity';

function availableContext() {
  return {
    physicalProviders: {
      easy_model_entities: {
        modId: 'easy_model_entities',
        version: '2.3.0',
        presence: 'PRESENT',
        health: 'UNPROVEN',
      },
    },
    blockbenchVersion: '5.1.6',
    installedExtensions: [
      {pluginId: 'easy_model_entities', pluginVersion: '1.0.0'},
    ],
    mcpAuthorizedExtensionIds: ['easy_model_entities'],
  };
}

function assertCoreApi(api, surface) {
  assert.equal(api.EASY_MODEL_ENTITIES_AUTHORITY?.minecraftVersion, '1.21.1', `${surface} Minecraft authority`);
  assert.equal(api.EASY_MODEL_ENTITIES_AUTHORITY?.providerVersion, '2.3.0', `${surface} provider authority`);
  assert.equal(api.EASY_MODEL_ENTITIES_AUTHORITY?.runtimeRef, '8c912371838c2a26bbb383008ad3999280f075d1', `${surface} runtime ref`);
  assert.equal(api.EASY_MODEL_ENTITIES_AUTHORITY?.blockbenchPluginId, 'easy_model_entities', `${surface} exporter id`);
  assert.equal(api.EASY_MODEL_ENTITIES_AUTHORITY?.blockbenchPluginVersion, '1.0.0', `${surface} exporter version`);
  assert.equal(api.EASY_MODEL_ENTITIES_AUTHORITY?.blockbenchPluginRef, '99c0bb118d1ef70fac7016c423b528c317e282dc', `${surface} exporter ref`);
  assert.equal(api.EASY_MODEL_ENTITIES_AUTHORITY?.schemaVersion, '0.2.0', `${surface} schema authority`);
  assert.equal(typeof api.createEasyModelEntitiesExportPlan, 'function', `${surface} export plan`);
  assert.equal(typeof api.validateEasyModelEntitiesServerProfile, 'function', `${surface} server profile validator`);
  assert.equal(typeof api.validateEasyModelEntitiesRenderProfile, 'function', `${surface} render profile validator`);
}

test('PR9 registers the official Easy Model Entities 1.0.0 exporter for audited Blockbench 5.1.6', () => {
  const definition = core.getExtensionDefinition('easy_model_entities');
  assert.ok(definition);
  assert.equal(definition.pluginVersion, '1.0.0');
  assert.equal(definition.classification, 'REQUIRED_PROFILE');
  assert.deepEqual(definition.blockbenchCompatibility?.auditedExact, ['5.1.6']);
  assert.equal(definition.mcpPolicy, 'ALLOWLIST');
  assert.equal(definition.providerFamily, 'easy_model_entities');
});

test('PR9 records the physical Easy Model Entities 2.3.0 provider and separate entity/block-entity profiles', () => {
  assert.deepEqual(core.CURRENT_PHYSICAL_PROVIDER_SNAPSHOT.easy_model_entities, {
    modId: 'easy_model_entities',
    version: '2.3.0',
    presence: 'PRESENT',
    health: 'UNPROVEN',
  });

  const entity = core.getProviderProfile(ENTITY_PROFILE_ID);
  const blockEntity = core.getProviderProfile(BLOCK_ENTITY_PROFILE_ID);
  for (const [profile, assetKind] of [[entity, 'entity'], [blockEntity, 'block_entity']]) {
    assert.ok(profile);
    assert.equal(profile.family, 'easy_model_entities');
    assert.equal(profile.assetKind, assetKind);
    assert.deepEqual(profile.requiredProvider, {
      modId: 'easy_model_entities',
      exactVersions: ['2.3.0'],
    });
    assert.deepEqual(profile.requiredExtensions, ['easy_model_entities']);
    assert.ok(profile.capabilities.includes('bbmodel_source'));
    assert.ok(profile.capabilities.includes('server_profile'));
    assert.ok(profile.capabilities.includes('render_profile'));
    assert.ok(profile.capabilities.includes('datapack_resourcepack_handoff'));
  }
});

test('PR9 provider resolution fails closed on provider/editor/exporter/authorization mismatch', () => {
  const context = availableContext();
  assert.equal(core.resolveProviderProfile(ENTITY_PROFILE_ID, context).status, 'AVAILABLE');
  assert.equal(core.resolveProviderProfile(BLOCK_ENTITY_PROFILE_ID, context).status, 'AVAILABLE');

  const wrongProvider = availableContext();
  wrongProvider.physicalProviders.easy_model_entities.version = '2.4.0';
  assert.equal(core.resolveProviderProfile(ENTITY_PROFILE_ID, wrongProvider).status, 'UNAVAILABLE');

  const wrongExtension = availableContext();
  wrongExtension.installedExtensions[0].pluginVersion = '1.0.1';
  assert.equal(core.resolveProviderProfile(ENTITY_PROFILE_ID, wrongExtension).status, 'UNAVAILABLE');

  const unauthorized = availableContext();
  unauthorized.mcpAuthorizedExtensionIds = [];
  assert.equal(core.resolveProviderProfile(ENTITY_PROFILE_ID, unauthorized).status, 'UNAVAILABLE');

  const wrongEditor = availableContext();
  wrongEditor.blockbenchVersion = '5.1.5';
  assert.equal(core.resolveProviderProfile(ENTITY_PROFILE_ID, wrongEditor).status, 'UNAVAILABLE');

  assert.equal(core.canConvertProfile(ENTITY_PROFILE_ID, BLOCK_ENTITY_PROFILE_ID), false);
  assert.equal(core.canConvertProfile(ENTITY_PROFILE_ID, 'geckolib4_entity'), false);
  assert.equal(core.canConvertProfile('azurelib_entity', ENTITY_PROFILE_ID), false);
});

test('PR9 export plan preserves .bbmodel and matches the audited runtime/exporter paths', () => {
  assert.equal(typeof core.createEasyModelEntitiesExportPlan, 'function');

  const entity = core.createEasyModelEntitiesExportPlan({
    profileId: ENTITY_PROFILE_ID,
    sourcePath: '/workspace/lizard.bbmodel',
    namespace: 'example',
    resourceName: 'lizard',
  });
  assert.deepEqual(entity, {
    profileId: ENTITY_PROFILE_ID,
    modelType: 'entity',
    sourcePath: '/workspace/lizard.bbmodel',
    preserveSource: true,
    namespace: 'example',
    resourceName: 'lizard',
    serverProfilePath: 'data/example/easy_model_entities/profiles/entity/lizard.json',
    renderProfilePath: 'assets/example/easy_model_entities/render_profiles/entity/lizard.json',
    modelPath: 'assets/example/easy_model_entities/models/lizard.bbmodel',
    datapackFileName: 'lizard_datapack.zip',
    resourcepackFileName: 'lizard_resourcepack.zip',
    runtimeEvidence: 'UNPROVEN',
  });
  assert.ok(Object.isFrozen(entity));

  const blockEntity = core.createEasyModelEntitiesExportPlan({
    profileId: BLOCK_ENTITY_PROFILE_ID,
    sourcePath: 'C:\\models\\shrine.bbmodel',
    namespace: 'example',
    resourceName: 'shrine',
  });
  assert.equal(blockEntity.modelType, 'block_entity');
  assert.equal(blockEntity.sourcePath, 'C:/models/shrine.bbmodel');
  assert.equal(blockEntity.serverProfilePath, 'data/example/easy_model_entities/profiles/block_entity/shrine.json');
  assert.equal(blockEntity.renderProfilePath, 'assets/example/easy_model_entities/render_profiles/block_entity/shrine.json');
  assert.equal(blockEntity.modelPath, 'assets/example/easy_model_entities/models/shrine.bbmodel');

  assert.throws(() => core.createEasyModelEntitiesExportPlan({
    profileId: ENTITY_PROFILE_ID,
    sourcePath: '/workspace/lizard.geo.json',
    namespace: 'example',
    resourceName: 'lizard',
  }), (error) => error?.code === 'EASY_MODEL_ENTITIES_SOURCE_NOT_SAVED');
  assert.throws(() => core.createEasyModelEntitiesExportPlan({
    profileId: ENTITY_PROFILE_ID,
    sourcePath: '/workspace/lizard.bbmodel',
    namespace: 'Example',
    resourceName: 'lizard',
  }), (error) => error?.code === 'INVALID_EASY_MODEL_ENTITIES_NAMESPACE');
  assert.throws(() => core.createEasyModelEntitiesExportPlan({
    profileId: ENTITY_PROFILE_ID,
    sourcePath: '/workspace/lizard.bbmodel',
    namespace: 'example',
    resourceName: '../lizard',
  }), (error) => error?.code === 'INVALID_EASY_MODEL_ENTITIES_RESOURCE_NAME');
});

test('PR9 validates audited 0.2.0 entity and block-entity server profiles fail-closed', () => {
  assert.equal(typeof core.validateEasyModelEntitiesServerProfile, 'function');

  assert.equal(core.validateEasyModelEntitiesServerProfile({
    schema_version: '0.2.0',
    model_type: 'entity',
    preset_type: 'quadruped_wandering',
    version: 'a1b2c3d4',
  }, {modelType: 'entity'}).ok, true);

  assert.equal(core.validateEasyModelEntitiesServerProfile({
    schema_version: '0.2.0',
    model_type: 'block_entity',
    preset_type: 'animated_randomly',
    version: 'b1c2d3e4',
  }, {modelType: 'block_entity'}).ok, true);

  assert.throws(() => core.validateEasyModelEntitiesServerProfile({
    schema_version: '9.9.9',
    model_type: 'entity',
    preset_type: 'quadruped_wandering',
  }, {modelType: 'entity'}), (error) => error?.code === 'EASY_MODEL_ENTITIES_SCHEMA_UNSUPPORTED');

  assert.throws(() => core.validateEasyModelEntitiesServerProfile({
    schema_version: '0.2.0',
    model_type: 'entity',
    preset_type: 'quadruped_wandering',
    unproven: true,
  }, {modelType: 'entity'}), (error) => error?.code === 'UNPROVEN_EASY_MODEL_ENTITIES_PROFILE_FIELD');

  assert.throws(() => core.validateEasyModelEntitiesServerProfile({
    schema_version: '0.2.0',
    model_type: 'block_entity',
    preset_type: 'animated_randomly',
  }, {modelType: 'entity'}), (error) => error?.code === 'EASY_MODEL_ENTITIES_MODEL_TYPE_MISMATCH');
});

test('PR9 validates audited render profiles and binds model references to the preserved .bbmodel handoff', () => {
  assert.equal(typeof core.validateEasyModelEntitiesRenderProfile, 'function');

  assert.equal(core.validateEasyModelEntitiesRenderProfile({
    schema_version: '0.2.0',
    preset_type: 'quadruped_wandering',
    version: 'a1b2c3d4',
    model: 'example:easy_model_entities/models/lizard',
  }, {namespace: 'example', resourceName: 'lizard'}).ok, true);

  assert.equal(core.validateEasyModelEntitiesRenderProfile({
    schema_version: '0.2.0',
    preset_type: 'static',
    version: 'b1c2d3e4',
    model: 'example:easy_model_entities/models/shrine',
    rendering: {shadow_radius: 0.5},
    animation: {mode: 'random_idle'},
  }, {namespace: 'example', resourceName: 'shrine'}).ok, true);

  assert.throws(() => core.validateEasyModelEntitiesRenderProfile({
    schema_version: '0.2.0',
    preset_type: 'static',
    model: 'other:easy_model_entities/models/shrine',
  }, {namespace: 'example', resourceName: 'shrine'}), (error) => error?.code === 'EASY_MODEL_ENTITIES_MODEL_PATH_MISMATCH');

  assert.throws(() => core.validateEasyModelEntitiesRenderProfile({
    schema_version: '0.2.0',
    preset_type: 'static',
    model: 'example:easy_model_entities/models/shrine',
    unknown_render_contract: true,
  }, {namespace: 'example', resourceName: 'shrine'}), (error) => error?.code === 'UNPROVEN_EASY_MODEL_ENTITIES_RENDER_FIELD');
});

test('PR9 API is exported by modular core, Blockbench plugin, and deterministic standalone bundle', () => {
  assertCoreApi(core, 'core');
  assertCoreApi(standalone, 'standalone');
  assert.equal(typeof blockbenchPlugin.createBlockbenchEasyModelEntitiesAdapter, 'function', 'blockbench-plugin adapter');
  assert.equal(typeof standalone.createBlockbenchEasyModelEntitiesAdapter, 'function', 'standalone Blockbench adapter');
});

test('PR9 Blockbench handoff is desktop-only, source-preserving, and delegates to the audited core plan', () => {
  assert.equal(typeof blockbenchPlugin.createBlockbenchEasyModelEntitiesAdapter, 'function');
  const bb = {
    Blockbench: {
      isWeb: false,
      Project: {save_path: '/workspace/lizard.bbmodel'},
    },
  };
  const adapter = blockbenchPlugin.createBlockbenchEasyModelEntitiesAdapter(bb);
  assert.equal(adapter.sourcePath(), '/workspace/lizard.bbmodel');
  const preview = adapter.previewHandoff({
    profileId: ENTITY_PROFILE_ID,
    namespace: 'example',
    resourceName: 'lizard',
  });
  assert.equal(preview.plan.modelPath, 'assets/example/easy_model_entities/models/lizard.bbmodel');
  assert.equal(preview.plan.preserveSource, true);
  assert.equal(preview.requiresOfficialExporter, true);
  assert.equal(preview.exporterPluginId, 'easy_model_entities');
  assert.equal(preview.exporterPluginVersion, '1.0.0');
  assert.equal(preview.runtimeEvidence, 'UNPROVEN');
  assert.ok(Object.isFrozen(preview));

  assert.throws(() => blockbenchPlugin.createBlockbenchEasyModelEntitiesAdapter({
    Blockbench: {isWeb: true, Project: {save_path: '/workspace/lizard.bbmodel'}},
  }), (error) => error?.code === 'EASY_MODEL_ENTITIES_DESKTOP_REQUIRED');
});

test('PR9 workflow is permanent on feature branch and main', () => {
  const workflowPath = path.resolve(__dirname, '../../../../.github/workflows/factory-art-pr9-easy-model-entities.yml');
  const workflow = fs.readFileSync(workflowPath, 'utf8');
  const pushBlock = workflow.match(/push:\s*\n\s*branches:\s*\n((?:\s*-\s*[^\n]+\n?)+)/);
  assert.ok(pushBlock, 'PR9 workflow must declare explicit push branches');
  const branches = Array.from(pushBlock[1].matchAll(/^\s*-\s*([^\s#]+)\s*$/gm), (match) => match[1]);
  assert.ok(branches.includes('feat/art-pr9-easy-model-entities'));
  assert.ok(branches.includes('main'));
  assert.match(workflow, /asset_toolkit\.easy_model_entities_pr9\.test\.js/);
});
