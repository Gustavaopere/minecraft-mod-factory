'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const core = require('./core/index.js');
const blockbenchPlugin = require('./blockbench-plugin/plugin_adapter.js');
const standalone = require('./asset_toolkit.js');

const PROFILE_ID = 'epicfight_blender_handoff';

function validHandoffInput() {
  return {
    blockbenchReferencePath: '/workspace/combat_reference.bbmodel',
    blenderSourcePath: '/workspace/combat_animation.blend',
    targetMinecraftVersion: '1.21.1',
    boneMapping: [
      {referenceBone: 'reference_root', blenderRigBone: 'rig_root'},
      {referenceBone: 'reference_hand', blenderRigBone: 'rig_hand'},
    ],
    textureReferences: [
      '/workspace/combat_reference.png',
      '/workspace/combat_emissive.png',
    ],
  };
}

function assertAuthority(authority, surface) {
  assert.equal(authority?.providerFamily, 'epicfight', `${surface} provider family`);
  assert.equal(authority?.runtimeVersion, '21.17.3.1', `${surface} runtime version`);
  assert.equal(authority?.minecraftVersion, '1.21.1', `${surface} Minecraft target`);
  assert.equal(authority?.physicalJar, 'epic-fight-21.17.3.1-mc1.21.1-neoforge.jar', `${surface} physical jar`);
  assert.equal(authority?.sourceArtifactName, 'epic-fight-21.17.3.1-mc1.21.1-neoforge-sources.jar', `${surface} source artifact`);
  assert.equal(authority?.sourceArtifactProvider, 'CurseForge', `${surface} source artifact provider`);
  assert.equal(authority?.sourceArtifactFileId, '8175610', `${surface} source artifact file id`);
  assert.equal(authority?.sourceAuditRepository, 'Antikythera-Studios/epicfight', `${surface} source audit repository`);
  assert.equal(authority?.sourceAuditRef, 'a78aa24b72e90a9d09f5fd61925e4369d117abaf', `${surface} source audit ref`);
  assert.equal(authority?.binaryToGitCommitMapping, 'UNPROVEN', `${surface} binary/git mapping boundary`);
  assert.equal(authority?.docsRepository, 'Antikythera-Studios/epic-fight.github.io', `${surface} docs repository`);
  assert.equal(authority?.docsRef, '1c055a4b2500a9a0ba6be04f9b5ec7361bcf84e1', `${surface} docs ref`);
  assert.equal(authority?.customCombatAnimationAuthority, 'BLENDER', `${surface} DCC authority`);
  assert.equal(authority?.exporterRepository, 'Antikythera-Studios/blender-json-addon', `${surface} exporter repository`);
  assert.equal(authority?.exporterRef, 'b9c6844193074f8c21b35513052d61c82cc2c207', `${surface} exporter ref`);
  assert.equal(authority?.exporterOutputExtension, '.json', `${surface} exporter output`);
  assert.equal(authority?.rigRepository, 'Antikythera-Studios/atk-resources', `${surface} rig repository`);
  assert.equal(authority?.rigRef, '1d0455bc3d87b613be77c43250363220facad19f', `${surface} rig ref`);
  assert.equal(authority?.rigPath, 'EpicFight Animation Rig.blend', `${surface} rig path`);
  assert.equal(authority?.rigBlobSha, '0f093f8e3f29281a5b8d248d6ce6d5653f7cf22a', `${surface} rig blob`);
  assert.equal(authority?.factoryNeoForgeVersion, '21.1.248', `${surface} Factory NeoForge target`);
  assert.equal(authority?.upstreamReleaseTestedNeoForgeVersion, '21.1.219', `${surface} upstream tested NeoForge`);
  assert.equal(authority?.targetExactRuntimeCompatibility, 'UNPROVEN', `${surface} target-exact runtime boundary`);
  assert.deepEqual(authority?.knownRuntimeRisks, [
    {
      repository: 'Antikythera-Studios/epicfight',
      issue: 2572,
      scope: 'multiplayer_animation_handling',
      state: 'OPEN',
    },
  ], `${surface} known runtime risks`);
}

test('PR13 physical snapshot pins Epic Fight 21.17.3.1 exactly without promoting presence to runtime proof', () => {
  assert.deepEqual(core.CURRENT_PHYSICAL_PROVIDER_SNAPSHOT.epicfight, {
    modId: 'epicfight', version: '21.17.3.1', presence: 'PRESENT', health: 'UNPROVEN',
  });
});

test('PR13 registers an external-DCC Epic Fight profile with Blender-authoritative combat animation', () => {
  const profile = core.getProviderProfile(PROFILE_ID);
  assert.ok(profile);
  assert.equal(profile.family, 'epicfight');
  assert.equal(profile.assetKind, 'custom_combat_animation_handoff');
  assert.deepEqual(profile.requiredProvider, {modId: 'epicfight', exactVersions: ['21.17.3.1']});
  assert.deepEqual(profile.requiredExtensions, []);
  for (const capability of [
    'blockbench_reference',
    'external_dcc_handoff',
    'blender_source',
    'epicfight_rig',
    'epicfight_blender_export',
    'runtime_qa_handoff',
  ]) {
    assert.ok(profile.capabilities.includes(capability), `missing Epic Fight handoff capability ${capability}`);
  }
  assert.equal(core.canConvertProfile('player_animation_library_player', PROFILE_ID), false);
  assert.equal(core.canConvertProfile(PROFILE_ID, 'player_animation_library_player'), false);
});

test('PR13 exposes exact physical, source, docs, exporter, rig, and runtime-risk authorities', () => {
  assertAuthority(core.EPIC_FIGHT_BLENDER_AUTHORITY, 'core');
});

test('PR13 handoff preserves native Blockbench and Blender sources and forbids fake direct export', () => {
  assert.equal(typeof core.createEpicFightBlenderHandoff, 'function');
  const handoff = core.createEpicFightBlenderHandoff(validHandoffInput());

  assert.equal(handoff.blockbenchReferencePath, '/workspace/combat_reference.bbmodel');
  assert.equal(handoff.blenderSourcePath, '/workspace/combat_animation.blend');
  assert.equal(handoff.preserveBlockbenchSource, true);
  assert.equal(handoff.preserveBlenderSource, true);
  assert.equal(handoff.customCombatAnimationAuthority, 'BLENDER');
  assert.equal(handoff.exporterOutputExtension, '.json');
  assert.deepEqual(handoff.workflow, [
    'BLOCKBENCH_CONCEPT_REFERENCE_MODEL',
    'HANDOFF_MANIFEST',
    'BLENDER_EPIC_FIGHT_RIG',
    'EPIC_FIGHT_BLENDER_EXPORTER',
    'EPIC_FIGHT_RUNTIME',
  ]);
  assert.equal(handoff.directBlockbenchEpicFightAnimationExport, false);
  assert.equal(handoff.implicitProviderConversion, false);
  assert.equal(handoff.runtimeEvidence, 'UNPROVEN');
  assert.equal(handoff.runtimeValidated, false);
  assert.equal(handoff.f4I6Evidence, false);
});

test('PR13 handoff preserves explicit bone-name mapping and texture references without inventing provider data', () => {
  const input = validHandoffInput();
  const handoff = core.createEpicFightBlenderHandoff(input);

  assert.deepEqual(handoff.boneMapping, input.boneMapping);
  assert.deepEqual(handoff.textureReferences, input.textureReferences);
  assert.notStrictEqual(handoff.boneMapping, input.boneMapping);
  assert.notStrictEqual(handoff.boneMapping[0], input.boneMapping[0]);
  assert.notStrictEqual(handoff.textureReferences, input.textureReferences);
  assert.equal(Object.isFrozen(handoff.boneMapping), true);
  assert.equal(Object.isFrozen(handoff.boneMapping[0]), true);
  assert.equal(Object.isFrozen(handoff.textureReferences), true);
});

test('PR13 handoff fails closed when explicit bone mapping or texture references are absent', () => {
  assert.throws(
    () => core.createEpicFightBlenderHandoff({...validHandoffInput(), boneMapping: []}),
    error => error?.code === 'EPIC_FIGHT_BONE_MAPPING_REQUIRED',
  );
  assert.throws(
    () => core.createEpicFightBlenderHandoff({...validHandoffInput(), textureReferences: []}),
    error => error?.code === 'EPIC_FIGHT_TEXTURE_REFERENCES_REQUIRED',
  );
});

test('PR13 handoff fails closed when Blender native source is absent or the target changes', () => {
  assert.throws(
    () => core.createEpicFightBlenderHandoff({...validHandoffInput(), blenderSourcePath: '/workspace/combat_animation.json'}),
    error => error?.code === 'EPIC_FIGHT_BLENDER_SOURCE_REQUIRED',
  );
  assert.throws(
    () => core.createEpicFightBlenderHandoff({...validHandoffInput(), targetMinecraftVersion: '1.21.2'}),
    error => error?.code === 'UNSUPPORTED_EPIC_FIGHT_MINECRAFT_VERSION',
  );
});

test('PR13 Blockbench surface only previews the external-DCC handoff and cannot export Epic Fight animation directly', () => {
  assert.equal(typeof blockbenchPlugin.createBlockbenchEpicFightHandoffAdapter, 'function');
  const input = validHandoffInput();
  const adapter = blockbenchPlugin.createBlockbenchEpicFightHandoffAdapter({
    Blockbench: {isWeb: false, isMobile: false},
    Project: {
      save_path: '/workspace/combat_reference.bbmodel',
      format: {id: 'free'},
    },
  }, {
    blenderSourcePath: input.blenderSourcePath,
    targetMinecraftVersion: input.targetMinecraftVersion,
    boneMapping: input.boneMapping,
    textureReferences: input.textureReferences,
  });

  const preview = adapter.previewHandoff();
  assert.equal(preview.customCombatAnimationAuthority, 'BLENDER');
  assert.equal(preview.directBlockbenchEpicFightAnimationExport, false);
  assert.equal(preview.runtimeEvidence, 'UNPROVEN');
  assert.deepEqual(preview.boneMapping, input.boneMapping);
  assert.deepEqual(preview.textureReferences, input.textureReferences);
  assert.equal(adapter.exportEpicFightAnimation, undefined);
  assert.equal(blockbenchPlugin.exportEpicFightAnimation, undefined);
});

test('PR13 standalone bundle exposes the same audited external-DCC boundary', () => {
  assertAuthority(standalone.EPIC_FIGHT_BLENDER_AUTHORITY, 'standalone');
  assert.equal(typeof standalone.createEpicFightBlenderHandoff, 'function');
  assert.equal(typeof standalone.createBlockbenchEpicFightHandoffAdapter, 'function');
  assert.equal(standalone.exportEpicFightAnimation, undefined);
});
