'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const core = require('./core/index.js');
const blockbenchPlugin = require('./blockbench-plugin/plugin_adapter.js');
const standalone = require('./asset_toolkit.js');

const PROFILE_ID = 'animated_java_display_entities';

function availableContext() {
  return {
    physicalProviders: {},
    blockbenchVersion: '5.1.6',
    installedExtensions: [
      {pluginId: 'animated_java', pluginVersion: '1.10.2'},
    ],
    mcpAuthorizedExtensionIds: ['animated_java'],
  };
}

function assertPublicApi(api, surface) {
  const authority = api.ANIMATED_JAVA_AUTHORITY;
  assert.equal(authority?.providerFamily, 'animated_java', `${surface} provider family`);
  assert.equal(authority?.minecraftVersion, '1.21.1', `${surface} Minecraft target`);
  assert.equal(authority?.pluginVersion, '1.10.2', `${surface} Animated Java version`);
  assert.equal(authority?.pluginSource, 'Animated-Java/animated-java', `${surface} plugin source`);
  assert.equal(authority?.pluginRef, 'a5fc548d2a53cc0887fa070db33ccfcef1cd3541', `${surface} plugin source ref`);
  assert.equal(
    authority?.releaseAssetSha256,
    '81aadc4def796d97dab6642ad05b564b470ecadcaf455c8cc5826c9e24759672',
    `${surface} release asset SHA-256`,
  );
  assert.equal(authority?.blockbenchVersion, '5.1.6', `${surface} Blockbench baseline`);
  assert.equal(authority?.blockbenchSource, 'JannisX11/blockbench', `${surface} Blockbench source`);
  assert.equal(authority?.blockbenchRef, '794e964e966b6783b4e9b98ecbdda5152c0620cc', `${surface} Blockbench source ref`);
  assert.equal(authority?.blockbenchMinimumVersion, '5.1.4', `${surface} minimum Blockbench version`);
  assert.equal(authority?.blueprintFormatId, 'animated-java:format/blueprint', `${surface} Blueprint format`);
  assert.equal(authority?.blueprintCodecId, 'animated_java:codec/blueprint', `${surface} Blueprint codec`);
  assert.equal(authority?.sourceExtension, '.ajblueprint', `${surface} source extension`);
  assert.deepEqual(authority?.exportModes, ['folder', 'zip', 'none'], `${surface} export modes`);
  assert.equal(typeof api.validateAnimatedJavaBlueprint, 'function', `${surface} Blueprint validator`);
  assert.equal(typeof api.createAnimatedJavaExportPlan, 'function', `${surface} export plan`);
}

test('PR11 reuses the existing Animated Java profile and exact extension pin', () => {
  const profile = core.getProviderProfile(PROFILE_ID);
  assert.ok(profile);
  assert.equal(profile.family, 'animated_java');
  assert.equal(profile.assetKind, 'display_entities');
  assert.equal(profile.requiredProvider, null);
  assert.deepEqual(profile.requiredExtensions, ['animated_java']);
  for (const capability of ['model', 'rig', 'animation', 'locator', 'variant', 'display_entity_export_handoff']) {
    assert.ok(profile.capabilities.includes(capability), `missing profile capability ${capability}`);
  }

  const extension = core.getExtensionDefinition('animated_java');
  assert.equal(extension?.pluginVersion, '1.10.2');
  assert.equal(extension?.classification, 'OPTIONAL');
  assert.equal(extension?.blockbenchCompatibility?.minInclusive, '5.1.4');
  assert.equal(extension?.mcpPolicy, 'ALLOWLIST');
  assert.equal(extension?.providerFamily, 'animated_java');

  assert.equal(core.resolveProviderProfile(PROFILE_ID, availableContext()).status, 'AVAILABLE');
});

test('PR11 exposes one audited Animated Java authority through core and standalone APIs', () => {
  assertPublicApi(core, 'core');
  assertPublicApi(standalone, 'standalone');
});

test('PR11 Blueprint validator is fail-closed for the audited source format and target', () => {
  const valid = {
    meta: {
      format: 'animated-java:format/blueprint',
      format_version: '1.10.2',
      uuid: '11111111-1111-4111-8111-111111111111',
    },
    blueprint_settings: {
      blueprint_id: 'factory:cutscene/test',
      target_minecraft_version: '1.21.1',
      resource_pack_export_mode: 'folder',
      data_pack_export_mode: 'folder',
      enable_plugin_mode: false,
    },
    variants: {
      default: {
        display_name: 'Default',
        name: 'default',
        uuid: '22222222-2222-4222-8222-222222222222',
        texture_map: {},
        excluded_nodes: [],
        is_default: true,
      },
      list: [],
    },
    elements: [],
    groups: [],
    outliner: [],
    textures: [],
    animations: [],
  };

  const normalized = core.validateAnimatedJavaBlueprint(valid);
  assert.equal(normalized.meta.format, 'animated-java:format/blueprint');
  assert.equal(normalized.blueprint_settings.target_minecraft_version, '1.21.1');

  assert.throws(
    () => core.validateAnimatedJavaBlueprint({...valid, meta: {...valid.meta, format: 'free'}}),
    error => error?.code === 'INVALID_ANIMATED_JAVA_BLUEPRINT_FORMAT',
  );
  assert.throws(
    () => core.validateAnimatedJavaBlueprint({
      ...valid,
      blueprint_settings: {...valid.blueprint_settings, target_minecraft_version: '1.21.2'},
    }),
    error => error?.code === 'UNSUPPORTED_ANIMATED_JAVA_MINECRAFT_VERSION',
  );
  assert.throws(
    () => core.validateAnimatedJavaBlueprint({
      ...valid,
      blueprint_settings: {...valid.blueprint_settings, resource_pack_export_mode: 'raw'},
    }),
    error => error?.code === 'INVALID_ANIMATED_JAVA_EXPORT_MODE',
  );
});

test('PR11 export plan preserves .ajblueprint and stages only explicit audited roots', () => {
  const plan = core.createAnimatedJavaExportPlan({
    sourcePath: '/workspace/cutscene.ajblueprint',
    blueprintId: 'factory:cutscene/test',
    targetMinecraftVersion: '1.21.1',
    resourcePackExportMode: 'folder',
    dataPackExportMode: 'folder',
    resourcePackPath: '/staging/resourcepack',
    dataPackPath: '/staging/datapack',
    enablePluginMode: false,
  });

  assert.equal(plan.sourcePath, '/workspace/cutscene.ajblueprint');
  assert.equal(plan.preserveSource, true);
  assert.equal(plan.requiresAnimatedJavaPlugin, true);
  assert.equal(plan.blueprintId, 'factory:cutscene/test');
  assert.equal(plan.targetMinecraftVersion, '1.21.1');
  assert.equal(plan.resourcePackExportMode, 'folder');
  assert.equal(plan.dataPackExportMode, 'folder');
  assert.equal(plan.resourcePackPath, '/staging/resourcepack');
  assert.equal(plan.dataPackPath, '/staging/datapack');
  assert.equal(plan.modelExportRoot, 'assets/factory/models/blueprint/cutscene/test');
  assert.equal(plan.textureExportRoot, 'assets/factory/textures/blueprint/cutscene/test');
  assert.equal(plan.runtimeEvidence, 'UNPROVEN');
  assert.equal(plan.runtimeValidated, false);
  assert.equal(plan.f4I6Evidence, false);
  assert.equal(plan.implicitProviderConversion, false);

  assert.throws(
    () => core.createAnimatedJavaExportPlan({
      sourcePath: '/workspace/cutscene.bbmodel',
      blueprintId: 'factory:cutscene/test',
      targetMinecraftVersion: '1.21.1',
      resourcePackExportMode: 'folder',
      dataPackExportMode: 'folder',
      resourcePackPath: '/staging/resourcepack',
      dataPackPath: '/staging/datapack',
    }),
    error => error?.code === 'ANIMATED_JAVA_SOURCE_NOT_SAVED',
  );
});

test('PR11 exposes an explicit Blockbench handoff without installing or executing unreviewed code', () => {
  assert.equal(typeof blockbenchPlugin.createBlockbenchAnimatedJavaAdapter, 'function');

  const adapter = blockbenchPlugin.createBlockbenchAnimatedJavaAdapter({
    Blockbench: {isMobile: false},
    Project: {
      save_path: '/workspace/cutscene.ajblueprint',
      format: {id: 'animated-java:format/blueprint'},
      animated_java: {
        blueprint_id: 'factory:cutscene/test',
        target_minecraft_version: '1.21.1',
        resource_pack_export_mode: 'folder',
        data_pack_export_mode: 'folder',
        resource_pack: '/staging/resourcepack',
        data_pack: '/staging/datapack',
        enable_plugin_mode: false,
      },
    },
  });

  const preview = adapter.previewHandoff();
  assert.equal(preview.sourcePath, '/workspace/cutscene.ajblueprint');
  assert.equal(preview.blueprintId, 'factory:cutscene/test');
  assert.equal(preview.requiresAnimatedJavaPlugin, true);
  assert.equal(preview.runtimeEvidence, 'UNPROVEN');
  assert.equal(preview.runtimeValidated, false);
  assert.equal(adapter.installExtension, undefined);
});
