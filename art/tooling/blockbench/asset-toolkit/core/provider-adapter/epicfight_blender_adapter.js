'use strict';

class EpicFightBlenderContractError extends Error {
  constructor(code, message) {
    super(message);
    this.name = 'EpicFightBlenderContractError';
    this.code = code;
  }
}

function fail(code, message) {
  throw new EpicFightBlenderContractError(code, message);
}

function frozenRisk(value) {
  return Object.freeze({...value});
}

const EPIC_FIGHT_BLENDER_AUTHORITY = Object.freeze({
  providerFamily: 'epicfight',
  runtimeVersion: '21.17.3.1',
  minecraftVersion: '1.21.1',
  physicalJar: 'epic-fight-21.17.3.1-mc1.21.1-neoforge.jar',
  sourceArtifactName: 'epic-fight-21.17.3.1-mc1.21.1-neoforge-sources.jar',
  sourceArtifactProvider: 'CurseForge',
  sourceArtifactFileId: '8175610',
  sourceAuditRepository: 'Antikythera-Studios/epicfight',
  sourceAuditRef: 'a78aa24b72e90a9d09f5fd61925e4369d117abaf',
  binaryToGitCommitMapping: 'UNPROVEN',
  docsRepository: 'Antikythera-Studios/epic-fight.github.io',
  docsRef: '1c055a4b2500a9a0ba6be04f9b5ec7361bcf84e1',
  customCombatAnimationAuthority: 'BLENDER',
  exporterRepository: 'Antikythera-Studios/blender-json-addon',
  exporterRef: 'b9c6844193074f8c21b35513052d61c82cc2c207',
  exporterOutputExtension: '.json',
  rigRepository: 'Antikythera-Studios/atk-resources',
  rigRef: '1d0455bc3d87b613be77c43250363220facad19f',
  rigPath: 'EpicFight Animation Rig.blend',
  rigBlobSha: '0f093f8e3f29281a5b8d248d6ce6d5653f7cf22a',
  factoryNeoForgeVersion: '21.1.248',
  upstreamReleaseTestedNeoForgeVersion: '21.1.219',
  targetExactRuntimeCompatibility: 'UNPROVEN',
  knownRuntimeRisks: Object.freeze([
    frozenRisk({
      repository: 'Antikythera-Studios/epicfight',
      issue: 2572,
      scope: 'multiplayer_animation_handling',
      state: 'OPEN',
    }),
  ]),
});

const EPIC_FIGHT_BLENDER_WORKFLOW = Object.freeze([
  'BLOCKBENCH_CONCEPT_REFERENCE_MODEL',
  'HANDOFF_MANIFEST',
  'BLENDER_EPIC_FIGHT_RIG',
  'EPIC_FIGHT_BLENDER_EXPORTER',
  'EPIC_FIGHT_RUNTIME',
]);

function requireNonEmptyString(value, code, label) {
  if (typeof value !== 'string' || !value.trim()) fail(code, `${label} is required.`);
  return value.trim();
}

function requireExtension(value, extension, code, label) {
  const path = requireNonEmptyString(value, code, label);
  if (!path.toLowerCase().endsWith(extension)) {
    fail(code, `${label} must preserve the native ${extension} source.`);
  }
  return path;
}

function requireBoneMapping(value) {
  if (!Array.isArray(value) || value.length === 0) {
    fail('EPIC_FIGHT_BONE_MAPPING_REQUIRED', 'Explicit Blockbench-reference to Blender-rig bone mapping is required.');
  }
  return Object.freeze(value.map((entry, index) => {
    if (!entry || typeof entry !== 'object' || Array.isArray(entry)) {
      fail('EPIC_FIGHT_BONE_MAPPING_INVALID', `Bone mapping entry ${index} must be an object.`);
    }
    const referenceBone = requireNonEmptyString(
      entry.referenceBone,
      'EPIC_FIGHT_BONE_MAPPING_INVALID',
      `Bone mapping entry ${index} referenceBone`,
    );
    const blenderRigBone = requireNonEmptyString(
      entry.blenderRigBone,
      'EPIC_FIGHT_BONE_MAPPING_INVALID',
      `Bone mapping entry ${index} blenderRigBone`,
    );
    return Object.freeze({referenceBone, blenderRigBone});
  }));
}

function requireTextureReferences(value) {
  if (!Array.isArray(value) || value.length === 0) {
    fail('EPIC_FIGHT_TEXTURE_REFERENCES_REQUIRED', 'At least one explicit texture reference is required.');
  }
  return Object.freeze(value.map((entry, index) => requireNonEmptyString(
    entry,
    'EPIC_FIGHT_TEXTURE_REFERENCES_INVALID',
    `Texture reference ${index}`,
  )));
}

function createEpicFightBlenderHandoff(input = {}) {
  const blockbenchReferencePath = requireExtension(
    input.blockbenchReferencePath,
    '.bbmodel',
    'EPIC_FIGHT_BLOCKBENCH_REFERENCE_REQUIRED',
    'Blockbench reference path',
  );
  const blenderSourcePath = requireExtension(
    input.blenderSourcePath,
    '.blend',
    'EPIC_FIGHT_BLENDER_SOURCE_REQUIRED',
    'Epic Fight Blender source path',
  );
  if (input.targetMinecraftVersion !== EPIC_FIGHT_BLENDER_AUTHORITY.minecraftVersion) {
    fail(
      'UNSUPPORTED_EPIC_FIGHT_MINECRAFT_VERSION',
      `Epic Fight handoff is audited only for Minecraft ${EPIC_FIGHT_BLENDER_AUTHORITY.minecraftVersion}.`,
    );
  }
  const boneMapping = requireBoneMapping(input.boneMapping);
  const textureReferences = requireTextureReferences(input.textureReferences);

  return Object.freeze({
    blockbenchReferencePath,
    blenderSourcePath,
    boneMapping,
    textureReferences,
    targetMinecraftVersion: input.targetMinecraftVersion,
    runtimeVersion: EPIC_FIGHT_BLENDER_AUTHORITY.runtimeVersion,
    preserveBlockbenchSource: true,
    preserveBlenderSource: true,
    customCombatAnimationAuthority: EPIC_FIGHT_BLENDER_AUTHORITY.customCombatAnimationAuthority,
    exporterOutputExtension: EPIC_FIGHT_BLENDER_AUTHORITY.exporterOutputExtension,
    workflow: EPIC_FIGHT_BLENDER_WORKFLOW,
    directBlockbenchEpicFightAnimationExport: false,
    implicitProviderConversion: false,
    binaryToGitCommitMapping: EPIC_FIGHT_BLENDER_AUTHORITY.binaryToGitCommitMapping,
    targetExactRuntimeCompatibility: EPIC_FIGHT_BLENDER_AUTHORITY.targetExactRuntimeCompatibility,
    runtimeEvidence: 'UNPROVEN',
    runtimeValidated: false,
    f4I6Evidence: false,
  });
}

module.exports = {
  EpicFightBlenderContractError,
  EPIC_FIGHT_BLENDER_AUTHORITY,
  EPIC_FIGHT_BLENDER_WORKFLOW,
  createEpicFightBlenderHandoff,
};
