'use strict';

class EpicFightDccContractError extends Error {
  constructor(code, message) {
    super(message);
    this.name = 'EpicFightDccContractError';
    this.code = code;
  }
}

function fail(code, message) {
  throw new EpicFightDccContractError(code, message);
}

const EPIC_FIGHT_DCC_AUTHORITY = Object.freeze({
  minecraftVersion: '1.21.1',
  targetNeoForgeVersion: '21.1.248',
  runtimeModId: 'epicfight',
  runtimeVersion: '21.17.3.1',
  physicalArtifact: 'epic-fight-21.17.3.1-mc1.21.1-neoforge.jar',
  physicalArtifactHash: 'c21b394dc6a51f43089f068a5a5bda6eac4c1ce4',
  sourceRepository: 'Antikythera-Studios/epicfight',
  sourceRef: 'a78aa24b72e90a9d09f5fd61925e4369d117abaf',
  sourceModVersion: '21.17.3',
  sourceMinecraftVersion: '1.21.1',
  sourceNeoForgeVersion: '21.1.219',
  sourceJavaVersion: '21',
  exporterRepository: 'Antikythera-Studios/blender-json-addon',
  exporterRef: 'b9c6844193074f8c21b35513052d61c82cc2c207',
  exporterAddonVersion: '1.0.0',
  exporterExtension: '.json',
  blenderSourceExtension: '.blend',
  blockbenchReferenceExtension: '.bbmodel',
  runtimeResourceDirectory: 'animmodels/animations',
  blenderAuthoritative: true,
  directBlockbenchAnimationExport: false,
  runtimeEvidence: 'UNPROVEN',
  runtimeValidated: false,
  f4I6Evidence: false,
});

const NAMESPACE_PATTERN = /^[a-z0-9_.-]+$/;
const PATH_PATTERN = /^[a-z0-9._-]+(?:\/[a-z0-9._-]+)*$/;

function requireString(value, code, label) {
  if (typeof value !== 'string' || value.length === 0) fail(code, `${label} must be a non-empty string.`);
  return value;
}

function validateNamespace(namespace) {
  requireString(namespace, 'EPIC_FIGHT_NAMESPACE_INVALID', 'namespace');
  if (!NAMESPACE_PATTERN.test(namespace)) fail('EPIC_FIGHT_NAMESPACE_INVALID', 'Epic Fight namespace must be a lowercase Minecraft namespace.');
  return namespace;
}

function validateAnimationId(animationId) {
  requireString(animationId, 'EPIC_FIGHT_ANIMATION_ID_INVALID', 'animationId');
  if (!PATH_PATTERN.test(animationId) || animationId.split('/').some((segment) => segment === '.' || segment === '..')) {
    fail('EPIC_FIGHT_ANIMATION_ID_INVALID', 'Epic Fight animationId must be a safe lowercase resource path.');
  }
  return animationId;
}

function validateBlockbenchReferencePath(sourceReferencePath) {
  requireString(sourceReferencePath, 'EPIC_FIGHT_SOURCE_REFERENCE_REQUIRED', 'sourceReferencePath');
  if (!sourceReferencePath.toLowerCase().endsWith(EPIC_FIGHT_DCC_AUTHORITY.blockbenchReferenceExtension)) {
    fail('EPIC_FIGHT_SOURCE_REFERENCE_REQUIRED', 'Epic Fight Blockbench reference source must remain a .bbmodel file.');
  }
  return sourceReferencePath;
}

function validateBlenderSourcePath(blenderSourcePath) {
  requireString(blenderSourcePath, 'EPIC_FIGHT_BLENDER_SOURCE_REQUIRED', 'blenderSourcePath');
  if (!blenderSourcePath.toLowerCase().endsWith(EPIC_FIGHT_DCC_AUTHORITY.blenderSourceExtension)) {
    fail('EPIC_FIGHT_BLENDER_SOURCE_REQUIRED', 'Epic Fight final authoring source must be a .blend file.');
  }
  return blenderSourcePath;
}

function copyBoneMappings(value) {
  if (value === undefined) return Object.freeze([]);
  if (!Array.isArray(value)) fail('EPIC_FIGHT_BONE_MAPPINGS_INVALID', 'boneMappings must be an array.');
  return Object.freeze(value.map((entry) => {
    if (!entry || typeof entry !== 'object' || Array.isArray(entry)) fail('EPIC_FIGHT_BONE_MAPPING_INVALID', 'Each bone mapping must be an object.');
    const source = requireString(entry.source, 'EPIC_FIGHT_BONE_MAPPING_INVALID', 'boneMappings[].source');
    const target = requireString(entry.target, 'EPIC_FIGHT_BONE_MAPPING_INVALID', 'boneMappings[].target');
    return Object.freeze({source, target});
  }));
}

function copyTextureReferences(value) {
  if (value === undefined) return Object.freeze([]);
  if (!Array.isArray(value)) fail('EPIC_FIGHT_TEXTURE_REFERENCES_INVALID', 'textureReferences must be an array.');
  return Object.freeze(value.map((entry) => requireString(entry, 'EPIC_FIGHT_TEXTURE_REFERENCE_INVALID', 'textureReferences[]')));
}

function createEpicFightBlenderHandoffManifest(input = {}) {
  if (!input || typeof input !== 'object' || Array.isArray(input)) fail('EPIC_FIGHT_HANDOFF_INPUT_INVALID', 'Epic Fight handoff input must be an object.');

  const namespace = validateNamespace(input.namespace);
  const animationId = validateAnimationId(input.animationId);
  const sourceReferencePath = validateBlockbenchReferencePath(input.sourceReferencePath);
  const blenderSourcePath = validateBlenderSourcePath(input.blenderSourcePath);
  const boneMappings = copyBoneMappings(input.boneMappings);
  const textureReferences = copyTextureReferences(input.textureReferences);

  return Object.freeze({
    profileId: 'epicfight_blender_handoff',
    authoritativeEditor: 'BLENDER',
    namespace,
    animationId,
    sourceReferencePath,
    blenderSourcePath,
    preserveSourceReference: true,
    preserveBlenderSource: true,
    boneMappings,
    textureReferences,
    runtimeTargetPath: `assets/${namespace}/${EPIC_FIGHT_DCC_AUTHORITY.runtimeResourceDirectory}/${animationId}.json`,
    exporterOutputExtension: EPIC_FIGHT_DCC_AUTHORITY.exporterExtension,
    requiresExternalExporter: true,
    directBlockbenchAnimationExport: false,
    implicitProviderConversion: false,
    runtimeEvidence: 'UNPROVEN',
    runtimeValidated: false,
    f4I6Evidence: false,
  });
}

function validateEpicFightAnimationJson(document) {
  if (!document || typeof document !== 'object' || Array.isArray(document)) {
    fail('EPIC_FIGHT_ANIMATION_JSON_REQUIRED', 'Epic Fight animation JSON root must be an object.');
  }
  if (!Array.isArray(document.animation)) {
    fail('EPIC_FIGHT_ANIMATION_ARRAY_REQUIRED', 'Epic Fight animation JSON root must contain an animation array.');
  }
  if (document.format !== undefined && typeof document.format !== 'string') {
    fail('EPIC_FIGHT_ANIMATION_FORMAT_INVALID', 'Epic Fight format, when present, must be a string.');
  }

  return Object.freeze({
    valid: true,
    format: document.format === undefined ? 'MATRIX' : document.format,
    animationCount: document.animation.length,
    runtimeResourceDirectory: EPIC_FIGHT_DCC_AUTHORITY.runtimeResourceDirectory,
    runtimeEvidence: 'UNPROVEN',
    runtimeValidated: false,
    f4I6Evidence: false,
  });
}

module.exports = {
  EpicFightDccContractError,
  EPIC_FIGHT_DCC_AUTHORITY,
  createEpicFightBlenderHandoffManifest,
  validateEpicFightAnimationJson,
};
