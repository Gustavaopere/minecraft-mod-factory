'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const core = require('./core/index.js');
const blockbenchPlugin = require('./blockbench-plugin/plugin_adapter.js');
const standalone = require('./asset_toolkit.js');

const PROFILE_ID = 'epicfight_blender_handoff';

function sampleHandoffInput() {
  return {
    namespace: 'factory',
    animationId: 'combat/heavy_slash',
    sourceReferencePath: '/workspace/combat_reference.bbmodel',
    blenderSourcePath: '/workspace/combat.blend',
    boneMappings: [{source: 'body', target: 'Chest'}],
    textureReferences: ['textures/entity/combat.png'],
  };
}

test('PR13 physical snapshot pins the exact Epic Fight runtime authority', () => {
  assert.deepEqual(core.CURRENT_PHYSICAL_PROVIDER_SNAPSHOT.epicfight, {
    modId: 'epicfight',
    version: '21.17.3.1',
    presence: 'PRESENT',
    health: 'UNPROVEN',
  });
});

test('PR13 registers a Blender-authoritative Epic Fight handoff profile', () => {
  const profile = core.getProviderProfile(PROFILE_ID);
  assert.equal(profile?.family, 'epicfight');
  assert.equal(profile?.requiredProvider?.modId, 'epicfight');
  assert.deepEqual(profile?.requiredProvider?.exactVersions, ['21.17.3.1']);
  assert.deepEqual(profile?.requiredExtensions, []);

  for (const capability of [
    'external_dcc_handoff',
    'blender_authoritative_animation',
    'source_reference',
    'bone_mapping',
    'texture_reference',
    'handoff_manifest',
    'epicfight_json_runtime',
  ]) {
    assert.ok(profile?.capabilities.includes(capability), `missing Epic Fight capability ${capability}`);
  }
});

test('PR13 exposes separately audited binary, source, exporter, and target authorities', () => {
  const authority = core.EPIC_FIGHT_DCC_AUTHORITY;
  assert.equal(authority?.minecraftVersion, '1.21.1');
  assert.equal(authority?.targetNeoForgeVersion, '21.1.248');
  assert.equal(authority?.runtimeModId, 'epicfight');
  assert.equal(authority?.runtimeVersion, '21.17.3.1');
  assert.equal(authority?.physicalArtifact, 'epic-fight-21.17.3.1-mc1.21.1-neoforge.jar');
  assert.equal(authority?.physicalArtifactHash, 'c21b394dc6a51f43089f068a5a5bda6eac4c1ce4');

  assert.equal(authority?.sourceRepository, 'Antikythera-Studios/epicfight');
  assert.equal(authority?.sourceRef, 'a78aa24b72e90a9d09f5fd61925e4369d117abaf');
  assert.equal(authority?.sourceModVersion, '21.17.3');
  assert.equal(authority?.sourceNeoForgeVersion, '21.1.219');

  assert.equal(authority?.exporterRepository, 'Antikythera-Studios/blender-json-addon');
  assert.equal(authority?.exporterRef, 'b9c6844193074f8c21b35513052d61c82cc2c207');
  assert.equal(authority?.exporterAddonVersion, '1.0.0');
  assert.equal(authority?.exporterExtension, '.json');
  assert.equal(authority?.blenderSourceExtension, '.blend');

  assert.equal(authority?.runtimeResourceDirectory, 'animmodels/animations');
  assert.equal(authority?.blenderAuthoritative, true);
  assert.equal(authority?.directBlockbenchAnimationExport, false);
});

test('PR13 handoff manifest preserves Blockbench reference and Blender source without implicit conversion', () => {
  assert.equal(typeof core.createEpicFightBlenderHandoffManifest, 'function');
  const manifest = core.createEpicFightBlenderHandoffManifest(sampleHandoffInput());

  assert.equal(manifest.profileId, PROFILE_ID);
  assert.equal(manifest.authoritativeEditor, 'BLENDER');
  assert.equal(manifest.sourceReferencePath, '/workspace/combat_reference.bbmodel');
  assert.equal(manifest.blenderSourcePath, '/workspace/combat.blend');
  assert.equal(manifest.preserveSourceReference, true);
  assert.equal(manifest.preserveBlenderSource, true);
  assert.deepEqual(manifest.boneMappings, [{source: 'body', target: 'Chest'}]);
  assert.deepEqual(manifest.textureReferences, ['textures/entity/combat.png']);
  assert.equal(manifest.runtimeTargetPath, 'assets/factory/animmodels/animations/combat/heavy_slash.json');
  assert.equal(manifest.directBlockbenchAnimationExport, false);
  assert.equal(manifest.implicitProviderConversion, false);
  assert.equal(manifest.runtimeEvidence, 'UNPROVEN');
  assert.equal(manifest.runtimeValidated, false);
  assert.equal(manifest.f4I6Evidence, false);
});

test('PR13 rejects non-Blender final authoring sources and invalid namespaces', () => {
  assert.throws(
    () => core.createEpicFightBlenderHandoffManifest({...sampleHandoffInput(), blenderSourcePath: '/workspace/combat.bbmodel'}),
    error => error?.code === 'EPIC_FIGHT_BLENDER_SOURCE_REQUIRED',
  );
  assert.throws(
    () => core.createEpicFightBlenderHandoffManifest({...sampleHandoffInput(), namespace: 'Factory Invalid'}),
    error => error?.code === 'EPIC_FIGHT_NAMESPACE_INVALID',
  );
});

test('PR13 validates only the proven Epic Fight animation JSON root contract', () => {
  assert.equal(typeof core.validateEpicFightAnimationJson, 'function');
  const validation = core.validateEpicFightAnimationJson({
    format: 'MATRIX',
    animation: [{name: 'Root', time: [0], transform: []}],
  });
  assert.equal(validation.valid, true);
  assert.equal(validation.runtimeResourceDirectory, 'animmodels/animations');

  assert.throws(
    () => core.validateEpicFightAnimationJson({format: 'MATRIX'}),
    error => error?.code === 'EPIC_FIGHT_ANIMATION_ARRAY_REQUIRED',
  );
});

test('PR13 Blockbench surface creates reference handoff only and exposes no direct Epic Fight animation export', () => {
  assert.equal(typeof blockbenchPlugin.createBlockbenchEpicFightReferenceHandoffAdapter, 'function');
  assert.equal(typeof standalone.createBlockbenchEpicFightReferenceHandoffAdapter, 'function');
  assert.equal(blockbenchPlugin.exportEpicFightAnimation, undefined);
  assert.equal(standalone.exportEpicFightAnimation, undefined);
  assert.equal(blockbenchPlugin.createEpicFightAnimationExport, undefined);
  assert.equal(standalone.createEpicFightAnimationExport, undefined);

  const adapter = blockbenchPlugin.createBlockbenchEpicFightReferenceHandoffAdapter({
    Project: {save_path: '/workspace/combat_reference.bbmodel'},
  });
  const manifest = adapter.createHandoff({
    namespace: 'factory',
    animationId: 'combat/heavy_slash',
    blenderSourcePath: '/workspace/combat.blend',
    boneMappings: [{source: 'body', target: 'Chest'}],
    textureReferences: ['textures/entity/combat.png'],
  });

  assert.equal(manifest.sourceReferencePath, '/workspace/combat_reference.bbmodel');
  assert.equal(manifest.authoritativeEditor, 'BLENDER');
  assert.equal(manifest.directBlockbenchAnimationExport, false);
  assert.equal(adapter.exportAnimation, undefined);
});

test('PR13 does not create an automatic conversion lane from Blockbench/provider profiles into Epic Fight', () => {
  for (const sourceProfile of [
    'geckolib4_entity',
    'azurelib3_entity',
    'animated_java_display_entities',
    'player_animation_library_player',
    'player_animator_player',
  ]) {
    assert.equal(core.canConvertProfile(sourceProfile, PROFILE_ID), false);
    assert.equal(core.canConvertProfile(PROFILE_ID, sourceProfile), false);
  }
});
