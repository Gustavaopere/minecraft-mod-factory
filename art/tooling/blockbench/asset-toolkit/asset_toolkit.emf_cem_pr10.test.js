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
  const authority = api.EMF_CEM_AUTHORITY;
  assert.equal(authority?.providerFamily, 'emf_cem', `${surface} provider family`);
  assert.equal(authority?.minecraftVersion, '1.21.1', `${surface} Minecraft authority`);
  assert.equal(authority?.targetNeoForgeVersion, '21.1.248', `${surface} Factory NeoForge target`);
  assert.equal(authority?.providerVersion, '3.3.5', `${surface} EMF authority`);
  assert.equal(authority?.providerNeoForgeBuildVersion, '21.0.167', `${surface} upstream EMF NeoForge build`);
  assert.equal(authority?.runtimeSource, 'Traben-0/Entity_Model_Features', `${surface} EMF source`);
  assert.equal(authority?.runtimeRef, '02034eb0f102040b16900be7c900eff88da89e9e', `${surface} EMF source ref`);
  assert.equal(authority?.etfMinimumVersion, '7.2.0', `${surface} ETF minimum`);
  assert.equal(authority?.physicalEtfVersion, '7.2.1', `${surface} physical ETF version`);
  assert.equal(authority?.blockbenchVersion, '5.1.6', `${surface} Blockbench version`);
  assert.equal(authority?.blockbenchSource, 'JannisX11/blockbench', `${surface} Blockbench source`);
  assert.equal(authority?.blockbenchRef, '794e964e966b6783b4e9b98ecbdda5152c0620cc', `${surface} Blockbench v5.1.6 ref`);
  assert.equal(authority?.cemCodecId, 'optifine_entity', `${surface} CEM codec`);
  assert.equal(authority?.jpmCodecId, 'optifine_part', `${surface} JPM codec`);
  assert.equal(authority?.cemTemplatePluginVersion, '9.2.0', `${surface} template plugin`);
  assert.equal(authority?.cemTemplatePluginSource, 'ewanhowell5195/blockbenchPlugins', `${surface} template plugin source`);
  assert.equal(authority?.cemTemplatePluginRef, 'bdea1d6c5e8f9fca3dbbeb446e568adb025b5ef2', `${surface} template plugin ref`);
  assert.equal(authority?.emfAnimationAddonVersion, '1.0.5', `${surface} animation addon`);
  assert.equal(authority?.pluginCatalogSource, 'JannisX11/blockbench-plugins', `${surface} catalog source`);
  assert.equal(authority?.pluginCatalogRef, '38862eb66b219995b09926488f7d1084a0fb6b3a', `${surface} catalog ref`);
  assert.equal(typeof api.createEmfCemExportPlan, 'function', `${surface} export plan`);
  assert.equal(typeof api.normalizeBlockbenchEmfCemDocument, 'function', `${surface} Blockbench normalization`);
  assert.equal(typeof api.validateEmfCemJemDocument, 'function', `${surface} JEM validator`);
  assert.equal(typeof api.validateEmfCemJpmDocument, 'function', `${surface} JPM validator`);
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

test('PR10 authority pins the exact runtime, Blockbench codecs, template loader, and optional addon sources', () => {
  assertPublicApi(core, 'core');
  assert.deepEqual(core.EMF_CEM_AUTHORITY.runtimeRoots, {
    optifineCompatible: 'optifine/cem',
    emfOnly: 'emf/cem',
  });
  assert.ok(Object.isFrozen(core.EMF_CEM_AUTHORITY));
  assert.ok(Object.isFrozen(core.EMF_CEM_AUTHORITY.runtimeRoots));
});

test('PR10 preserves native Blockbench shadowSize instead of silently rewriting provider semantics', () => {
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
  assert.equal(normalized.shadowSize, 0.75);
  assert.equal(Object.hasOwn(normalized, 'shadow_size'), false);
  assert.deepEqual(normalized.models[0].animations, [{'head.rx': '0.25'}]);
  assert.ok(Object.isFrozen(normalized));
  assert.ok(Object.isFrozen(normalized.models));
  assert.ok(Object.isFrozen(normalized.models[0]));
});

test('PR10 JEM validator accepts the audited Blockbench subset and gates EMF-only fields explicitly', () => {
  const document = {
    textureSize: [64, 32],
    shadowSize: 0.75,
    models: [{
      part: 'head',
      id: 'head',
      invertAxis: 'xy',
      translate: [0, 0, 0],
      boxes: [{coordinates: [-4, -8, -4, 8, 8, 8], textureOffset: [0, 0]}],
      animations: [{'head.rx': '0.25'}],
    }],
  };
  const result = core.validateEmfCemJemDocument(document, {animationDialect: 'optifine'});
  assert.equal(result.ok, true);
  assert.equal(result.modelCount, 1);
  assert.equal(result.animationExpressionCount, 1);
  assert.equal(result.emfOnly, false);

  assert.throws(() => core.validateEmfCemJemDocument({
    textureSize: [64, 32],
    models: [],
    unprovenField: true,
  }, {animationDialect: 'optifine'}), (error) => error?.code === 'UNPROVEN_EMF_CEM_JEM_FIELD');

  assert.throws(() => core.validateEmfCemJemDocument({
    textureSize: [64, 32],
    models: [{part: 'head', id: 'head', translate: [0, 0, 0], animations: [{'head.rx': 0.25}]}],
  }, {animationDialect: 'optifine'}), (error) => error?.code === 'INVALID_EMF_CEM_ANIMATION_EXPRESSION');

  const emfOnlyDocument = {
    textureSize: [64, 32],
    models: [{
      part: 'body', id: 'body', translate: [0, 0, 0],
      boxes: [{coordinates: [0, 0, 0, 2, 2, 2], textureOffset: [0, 0], sizeAddX: 0.25}],
    }],
  };
  assert.throws(
    () => core.validateEmfCemJemDocument(emfOnlyDocument, {animationDialect: 'optifine'}),
    (error) => error?.code === 'EMF_ONLY_FIELD_REQUIRES_EMF_DIALECT',
  );
  const emfOnlyResult = core.validateEmfCemJemDocument(emfOnlyDocument, {animationDialect: 'emf'});
  assert.equal(emfOnlyResult.ok, true);
  assert.equal(emfOnlyResult.emfOnly, true);
});

test('PR10 validates audited JPM part output separately from a JEM entity document', () => {
  const result = core.validateEmfCemJpmDocument({
    id: 'head_part',
    invertAxis: 'xy',
    translate: [0, 0, 0],
    boxes: [{coordinates: [-4, -8, -4, 8, 8, 8], textureOffset: [0, 0]}],
    animations: [{'head_part.rx': '0.25'}],
  }, {animationDialect: 'optifine'});
  assert.equal(result.ok, true);
  assert.equal(result.animationExpressionCount, 1);
  assert.equal(result.emfOnly, false);
});

test('PR10 export plan requires an explicit compatibility root, layout, and animation dialect', () => {
  const plan = core.createEmfCemExportPlan({
    profileId: PROFILE_ID,
    sourcePath: '/workspace/zombie.bbmodel',
    namespace: 'minecraft',
    resourceName: 'zombie',
    compatibilityMode: 'optifine_compatible',
    directoryLayout: 'flat',
    animationDialect: 'optifine',
  });
  assert.deepEqual(plan, {
    profileId: PROFILE_ID,
    sourcePath: '/workspace/zombie.bbmodel',
    preserveSource: true,
    namespace: 'minecraft',
    resourceName: 'zombie',
    compatibilityMode: 'optifine_compatible',
    directoryLayout: 'flat',
    animationDialect: 'optifine',
    jemPath: 'assets/minecraft/optifine/cem/zombie.jem',
    partModelDirectory: 'assets/minecraft/optifine/cem',
    blockbenchCodecId: 'optifine_entity',
    requiresCemTemplateLoader: true,
    requiresEmfAnimationAddon: false,
    resourcepackFileName: 'zombie_emf_cem_resourcepack.zip',
    runtimeEvidence: 'UNPROVEN',
    runtimeValidated: false,
    f4I6Evidence: false,
  });
  assert.ok(Object.isFrozen(plan));

  const emfOnly = core.createEmfCemExportPlan({
    profileId: PROFILE_ID,
    sourcePath: 'C:\\models\\wisp.bbmodel',
    namespace: 'example',
    resourceName: 'wisp',
    compatibilityMode: 'emf_only',
    directoryLayout: 'subfolder',
    animationDialect: 'emf',
  });
  assert.equal(emfOnly.sourcePath, 'C:/models/wisp.bbmodel');
  assert.equal(emfOnly.jemPath, 'assets/example/emf/cem/wisp/wisp.jem');
  assert.equal(emfOnly.partModelDirectory, 'assets/example/emf/cem/wisp');
  assert.equal(emfOnly.requiresEmfAnimationAddon, true);

  assert.throws(() => core.createEmfCemExportPlan({
    profileId: PROFILE_ID,
    sourcePath: '/workspace/zombie.bbmodel',
    namespace: 'minecraft',
    resourceName: 'zombie',
  }), (error) => error?.code === 'EMF_CEM_COMPATIBILITY_MODE_REQUIRED');

  assert.throws(() => core.createEmfCemExportPlan({
    profileId: PROFILE_ID,
    sourcePath: '/workspace/zombie.bbmodel',
    namespace: 'minecraft',
    resourceName: 'zombie',
    compatibilityMode: 'optifine_compatible',
    directoryLayout: 'flat',
    animationDialect: 'emf',
  }), (error) => error?.code === 'EMF_ONLY_ANIMATION_REQUIRES_EMF_MODE');

  assert.throws(() => core.createEmfCemExportPlan({
    profileId: PROFILE_ID,
    sourcePath: '/workspace/zombie.jem',
    namespace: 'minecraft',
    resourceName: 'zombie',
    compatibilityMode: 'optifine_compatible',
    directoryLayout: 'flat',
    animationDialect: 'optifine',
  }), (error) => error?.code === 'EMF_CEM_SOURCE_NOT_SAVED');
});

test('PR10 Blockbench handoff delegates to the native OptiFine Entity codec without replacing .bbmodel source authority', () => {
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
      optifine_part: {compile() { return {}; }},
    },
  };
  const adapter = blockbenchPlugin.createBlockbenchEmfCemAdapter(bb);
  const preview = adapter.previewHandoff({
    namespace: 'minecraft',
    resourceName: 'zombie',
    compatibilityMode: 'optifine_compatible',
    directoryLayout: 'flat',
    animationDialect: 'optifine',
  });
  assert.deepEqual(compileOptions, {raw: true});
  assert.equal(preview.plan.jemPath, 'assets/minecraft/optifine/cem/zombie.jem');
  assert.equal(preview.document.shadowSize, 0.75);
  assert.equal(Object.hasOwn(preview.document, 'shadow_size'), false);
  assert.equal(preview.plan.preserveSource, true);
  assert.equal(preview.codecId, 'optifine_entity');
  assert.equal(preview.requiresCemTemplateLoader, true);
  assert.equal(preview.requiresEmfAnimationAddon, false);
  assert.equal(preview.runtimeEvidence, 'UNPROVEN');
  assert.equal(preview.runtimeValidated, false);
  assert.equal(preview.f4I6Evidence, false);
  assert.ok(Object.isFrozen(preview));

  assert.throws(() => blockbenchPlugin.createBlockbenchEmfCemAdapter({
    Blockbench: {isWeb: false, Project: {save_path: '/workspace/zombie.bbmodel'}},
    Format: {id: 'geckolib_model'},
    Codecs: {optifine_entity: {compile() { return {}; }}},
  }), (error) => error?.code === 'EMF_CEM_FORMAT_REQUIRED');

  assert.throws(() => blockbenchPlugin.createBlockbenchEmfCemAdapter({
    Blockbench: {isWeb: false, Project: {save_path: ''}},
    Format: {id: 'optifine_entity'},
    Codecs: {optifine_entity: {compile() { return {}; }}},
  }), (error) => error?.code === 'EMF_CEM_SOURCE_NOT_SAVED');
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
  assert.match(workflow, /Existing provider profile regressions/);
  assert.match(workflow, /if:\s*always\(\)/);
});
