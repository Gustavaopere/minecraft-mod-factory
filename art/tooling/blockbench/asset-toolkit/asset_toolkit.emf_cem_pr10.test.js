'use strict';

const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const assert = require('node:assert/strict');

const core = require('./core/index.js');
const blockbenchPlugin = require('./blockbench-plugin/plugin_adapter.js');
const standalone = require('./asset_toolkit.js');

const PROFILE_ID = 'emf_cem_entity';

function availableContext({withAddon = true} = {}) {
  const installedExtensions = [
    {pluginId: 'cem_template_loader', pluginVersion: '9.2.0'},
  ];
  const authorized = ['cem_template_loader'];
  if (withAddon) {
    installedExtensions.push({pluginId: 'emf_animation_addon', pluginVersion: '1.0.5'});
    authorized.push('emf_animation_addon');
  }
  return {
    physicalProviders: {
      entity_model_features: {
        modId: 'entity_model_features',
        version: '3.3.5',
        presence: 'PRESENT',
        health: 'UNPROVEN',
      },
    },
    blockbenchVersion: '5.1.6',
    installedExtensions,
    mcpAuthorizedExtensionIds: authorized,
  };
}

function assertPublicApi(api, surface) {
  assert.equal(api.EMF_CEM_AUTHORITY?.minecraftVersion, '1.21.1', `${surface} Minecraft authority`);
  assert.equal(api.EMF_CEM_AUTHORITY?.providerVersion, '3.3.5', `${surface} EMF authority`);
  assert.equal(api.EMF_CEM_AUTHORITY?.runtimeRef, '02034eb0f102040b16900be7c900eff88da89e9e', `${surface} EMF source ref`);
  assert.equal(api.EMF_CEM_AUTHORITY?.etfMinimumVersion, '7.2.0', `${surface} ETF minimum`);
  assert.equal(api.EMF_CEM_AUTHORITY?.physicalEtfVersion, '7.2.1', `${surface} physical ETF version`);
  assert.equal(api.EMF_CEM_AUTHORITY?.blockbenchVersion, '5.1.6', `${surface} Blockbench version`);
  assert.equal(api.EMF_CEM_AUTHORITY?.blockbenchRef, '47e633e4a1338f957ee7baa0acbcf54da11e77df', `${surface} Blockbench ref`);
  assert.equal(api.EMF_CEM_AUTHORITY?.cemCodecId, 'optifine_entity', `${surface} CEM codec`);
  assert.equal(api.EMF_CEM_AUTHORITY?.cemTemplatePluginVersion, '9.2.0', `${surface} template plugin`);
  assert.equal(api.EMF_CEM_AUTHORITY?.cemTemplatePluginRef, 'bdea1d6c5e8f9fca3dbbeb446e568adb025b5ef2', `${surface} template plugin ref`);
  assert.equal(api.EMF_CEM_AUTHORITY?.emfAnimationAddonVersion, '1.0.5', `${surface} animation addon`);
  assert.equal(api.EMF_CEM_AUTHORITY?.pluginCatalogRef, '38862eb66b219995b09926488f7d1084a0fb6b3a', `${surface} catalog ref`);
  assert.equal(typeof api.createEmfCemExportPlan, 'function', `${surface} export plan`);
  assert.equal(typeof api.normalizeBlockbenchEmfCemDocument, 'function', `${surface} Blockbench normalization`);
  assert.equal(typeof api.validateEmfCemJemDocument, 'function', `${surface} JEM validator`);
}

test('PR10 reuses the existing exact EMF/CEM profile and extension registry contract', () => {
  const profile = core.getProviderProfile(PROFILE_ID);
  assert.ok(profile);
  assert.equal(profile.family, 'emf_cem');
  assert.equal(profile.assetKind, 'entity');
  assert.deepEqual(profile.requiredProvider, {
    modId: 'entity_model_features',
    exactVersions: ['3.3.5'],
  });
  assert.deepEqual(profile.requiredExtensions, ['cem_template_loader']);
  assert.ok(profile.capabilities.includes('resource_pack_cem'));
  assert.ok(profile.capabilities.includes('animation_authoring'));

  const template = core.getExtensionDefinition('cem_template_loader');
  assert.equal(template?.pluginVersion, '9.2.0');
  assert.equal(template?.blockbenchCompatibility?.minInclusive, '5.0.0');
  assert.equal(template?.classification, 'REQUIRED_PROFILE');

  const addon = core.getExtensionDefinition('emf_animation_addon');
  assert.equal(addon?.pluginVersion, '1.0.5');
  assert.equal(addon?.classification, 'PREFERRED');
  assert.equal(addon?.blockbenchCompatibility?.minInclusive, '4.9.0');

  assert.equal(core.resolveProviderProfile(PROFILE_ID, availableContext()).status, 'AVAILABLE');
  assert.equal(core.resolveProviderProfile(PROFILE_ID, availableContext({withAddon: false})).status, 'AVAILABLE');
});

test('PR10 profile remains fail-closed and never implies a GeckoLib/AzureLib conversion', () => {
  const wrongProvider = availableContext();
  wrongProvider.physicalProviders.entity_model_features.version = '3.3.4';
  assert.equal(core.resolveProviderProfile(PROFILE_ID, wrongProvider).status, 'UNAVAILABLE');

  const missingTemplate = availableContext();
  missingTemplate.installedExtensions = [];
  missingTemplate.mcpAuthorizedExtensionIds = [];
  assert.equal(core.resolveProviderProfile(PROFILE_ID, missingTemplate).status, 'UNAVAILABLE');

  const wrongTemplate = availableContext();
  wrongTemplate.installedExtensions[0].pluginVersion = '9.1.0';
  assert.equal(core.resolveProviderProfile(PROFILE_ID, wrongTemplate).status, 'UNAVAILABLE');

  assert.equal(core.canConvertProfile('geckolib4_entity', PROFILE_ID), false);
  assert.equal(core.canConvertProfile('azurelib_entity', PROFILE_ID), false);
  assert.equal(core.canConvertProfile('easy_model_entities_entity', PROFILE_ID), false);
});

test('PR10 authority pins runtime, Blockbench core codec, template loader, and optional addon sources', () => {
  assertPublicApi(core, 'core');
  assert.deepEqual(core.EMF_CEM_AUTHORITY.runtimeRoots, Object.freeze(['emf/cem', 'optifine/cem']));
  assert.ok(Object.isFrozen(core.EMF_CEM_AUTHORITY));
  assert.ok(Object.isFrozen(core.EMF_CEM_AUTHORITY.runtimeRoots));
});

test('PR10 explicitly normalizes Blockbench shadowSize to the audited EMF 3.3.5 shadow_size field', () => {
  assert.equal(typeof core.normalizeBlockbenchEmfCemDocument, 'function');
  const normalized = core.normalizeBlockbenchEmfCemDocument({
    textureSize: [64, 32],
    shadowSize: 0.75,
    models: [{
      part: 'head',
      id: 'head',
      invertAxis: 'xy',
      translate: [0, 0, 0],
      animations: [{'head.rx': '0.25'}],
    }],
  });
  assert.equal(normalized.shadow_size, 0.75);
  assert.equal(Object.hasOwn(normalized, 'shadowSize'), false);
  assert.deepEqual(normalized.models[0].animations, [{'head.rx': '0.25'}]);
  assert.ok(Object.isFrozen(normalized));
  assert.ok(Object.isFrozen(normalized.models));
  assert.ok(Object.isFrozen(normalized.models[0]));

  assert.throws(() => core.normalizeBlockbenchEmfCemDocument({
    textureSize: [64, 32],
    shadowSize: 0.5,
    shadow_size: 0.75,
    models: [],
  }), (error) => error?.code === 'AMBIGUOUS_EMF_CEM_SHADOW_FIELD');
});

test('PR10 JEM validator accepts the proven conservative model/animation subset and rejects unknown semantics', () => {
  assert.equal(typeof core.validateEmfCemJemDocument, 'function');
  const result = core.validateEmfCemJemDocument({
    textureSize: [64, 32],
    shadow_size: 0.75,
    models: [{
      part: 'head',
      id: 'head',
      invertAxis: 'xy',
      translate: [0, 0, 0],
      boxes: [{coordinates: [-4, -8, -4, 8, 8, 8], textureOffset: [0, 0]}],
      animations: [{'head.rx': '0.25'}],
    }],
  });
  assert.equal(result.ok, true);
  assert.equal(result.modelCount, 1);
  assert.equal(result.animationExpressionCount, 1);

  assert.throws(() => core.validateEmfCemJemDocument({
    textureSize: [64, 32],
    models: [],
    unprovenField: true,
  }), (error) => error?.code === 'UNPROVEN_EMF_CEM_JEM_FIELD');

  assert.throws(() => core.validateEmfCemJemDocument({
    textureSize: [64, 32],
    models: [{part: 'head', id: 'head', translate: [0, 0, 0], animations: [{'head.rx': 0.25}]}],
  }), (error) => error?.code === 'INVALID_EMF_CEM_ANIMATION_EXPRESSION');
});

test('PR10 export plan preserves the .bbmodel source and stages the EMF-specific primary resource-pack path', () => {
  assert.equal(typeof core.createEmfCemExportPlan, 'function');
  const plan = core.createEmfCemExportPlan({
    profileId: PROFILE_ID,
    sourcePath: '/workspace/zombie.bbmodel',
    namespace: 'minecraft',
    resourceName: 'zombie',
  });
  assert.deepEqual(plan, {
    profileId: PROFILE_ID,
    sourcePath: '/workspace/zombie.bbmodel',
    preserveSource: true,
    namespace: 'minecraft',
    resourceName: 'zombie',
    jemPath: 'assets/minecraft/emf/cem/zombie.jem',
    fallbackReadPath: 'assets/minecraft/optifine/cem/zombie.jem',
    resourcepackFileName: 'zombie_emf_cem_resourcepack.zip',
    runtimeEvidence: 'UNPROVEN',
  });
  assert.ok(Object.isFrozen(plan));

  const modded = core.createEmfCemExportPlan({
    profileId: PROFILE_ID,
    sourcePath: 'C:\\models\\beast.bbmodel',
    namespace: 'example',
    resourceName: 'beast',
  });
  assert.equal(modded.sourcePath, 'C:/models/beast.bbmodel');
  assert.equal(modded.jemPath, 'assets/example/emf/cem/beast.jem');

  assert.throws(() => core.createEmfCemExportPlan({
    profileId: PROFILE_ID,
    sourcePath: '/workspace/zombie.jem',
    namespace: 'minecraft',
    resourceName: 'zombie',
  }), (error) => error?.code === 'EMF_CEM_SOURCE_NOT_SAVED');
  assert.throws(() => core.createEmfCemExportPlan({
    profileId: PROFILE_ID,
    sourcePath: '/workspace/zombie.bbmodel',
    namespace: 'Minecraft',
    resourceName: 'zombie',
  }), (error) => error?.code === 'INVALID_EMF_CEM_NAMESPACE');
  assert.throws(() => core.createEmfCemExportPlan({
    profileId: PROFILE_ID,
    sourcePath: '/workspace/zombie.bbmodel',
    namespace: 'minecraft',
    resourceName: '../zombie',
  }), (error) => error?.code === 'INVALID_EMF_CEM_RESOURCE_NAME');
});

test('PR10 Blockbench handoff requires the native OptiFine Entity codec and preserves source authority', () => {
  assert.equal(typeof blockbenchPlugin.createBlockbenchEmfCemAdapter, 'function');
  let compileOptions = null;
  const bb = {
    Blockbench: {
      isWeb: false,
      Project: {save_path: '/workspace/zombie.bbmodel'},
    },
    Format: {id: 'optifine_entity'},
    Codecs: {
      optifine_entity: {
        compile(options) {
          compileOptions = options;
          return {
            textureSize: [64, 32],
            shadowSize: 0.75,
            models: [{
              part: 'head', id: 'head', invertAxis: 'xy', translate: [0, 0, 0],
              animations: [{'head.rx': '0.25'}],
            }],
          };
        },
      },
    },
  };
  const adapter = blockbenchPlugin.createBlockbenchEmfCemAdapter(bb);
  const preview = adapter.previewHandoff({namespace: 'minecraft', resourceName: 'zombie'});
  assert.deepEqual(compileOptions, {raw: true});
  assert.equal(preview.plan.jemPath, 'assets/minecraft/emf/cem/zombie.jem');
  assert.equal(preview.document.shadow_size, 0.75);
  assert.equal(preview.plan.preserveSource, true);
  assert.equal(preview.runtimeEvidence, 'UNPROVEN');
  assert.ok(Object.isFrozen(preview));

  assert.throws(() => blockbenchPlugin.createBlockbenchEmfCemAdapter({
    Blockbench: {isWeb: true, Project: {save_path: '/workspace/zombie.bbmodel'}},
    Format: {id: 'optifine_entity'},
    Codecs: {optifine_entity: {compile() { return {}; }}},
  }), (error) => error?.code === 'EMF_CEM_DESKTOP_REQUIRED');

  assert.throws(() => blockbenchPlugin.createBlockbenchEmfCemAdapter({
    Blockbench: {isWeb: false, Project: {save_path: '/workspace/zombie.bbmodel'}},
    Format: {id: 'geckolib_model'},
    Codecs: {optifine_entity: {compile() { return {}; }}},
  }), (error) => error?.code === 'EMF_CEM_FORMAT_REQUIRED');
});

test('PR10 API is exported by core, Blockbench plugin, standalone bundle, and permanent workflow', () => {
  assertPublicApi(core, 'core');
  assertPublicApi(standalone, 'standalone');
  assert.equal(typeof blockbenchPlugin.createBlockbenchEmfCemAdapter, 'function');
  assert.equal(typeof standalone.createBlockbenchEmfCemAdapter, 'function');

  const workflowPath = path.resolve(__dirname, '../../../../.github/workflows/factory-art-pr10-emf-cem.yml');
  const workflow = fs.readFileSync(workflowPath, 'utf8');
  const pushBlock = workflow.match(/push:\s*\n\s*branches:\s*\n((?:\s*-\s*[^\n]+\n?)+)/);
  assert.ok(pushBlock, 'PR10 workflow must declare explicit push branches');
  const branches = Array.from(pushBlock[1].matchAll(/^\s*-\s*([^\s#]+)\s*$/gm), (match) => match[1]);
  assert.ok(branches.includes('feat/art-pr10-emf-cem'));
  assert.ok(branches.includes('main'));
  assert.match(workflow, /asset_toolkit\.emf_cem_pr10\.test\.js/);
  assert.match(workflow, /runtime pack.*animation smoke/i);
});
