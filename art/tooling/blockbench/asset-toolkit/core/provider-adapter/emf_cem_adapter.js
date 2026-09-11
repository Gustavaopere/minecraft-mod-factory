'use strict';

const {
  isPlainObject,
  validateMinecraftNamespace,
  validateSafeResourceName,
  normalizeBbmodelSourcePath,
} = require('../common/contract_utils.js');

const EMF_CEM_RUNTIME_ROOTS = Object.freeze({
  optifineCompatible: 'optifine/cem',
  emfOnly: 'emf/cem',
});

const EMF_CEM_AUTHORITY = Object.freeze({
  providerFamily: 'emf_cem',
  minecraftVersion: '1.21.1',
  targetNeoForgeVersion: '21.1.248',
  providerVersion: '3.3.5',
  providerNeoForgeBuildVersion: '21.0.167',
  runtimeSource: 'Traben-0/Entity_Model_Features',
  runtimeRef: '02034eb0f102040b16900be7c900eff88da89e9e',
  etfMinimumVersion: '7.2.0',
  physicalEtfVersion: '7.2.1',
  blockbenchVersion: '5.1.6',
  blockbenchSource: 'JannisX11/blockbench',
  blockbenchRef: '794e964e966b6783b4e9b98ecbdda5152c0620cc',
  cemCodecId: 'optifine_entity',
  jpmCodecId: 'optifine_part',
  cemTemplatePluginId: 'cem_template_loader',
  cemTemplatePluginVersion: '9.2.0',
  cemTemplatePluginSource: 'ewanhowell5195/blockbenchPlugins',
  cemTemplatePluginRef: 'bdea1d6c5e8f9fca3dbbeb446e568adb025b5ef2',
  emfAnimationAddonId: 'emf_animation_addon',
  emfAnimationAddonVersion: '1.0.5',
  pluginCatalogSource: 'JannisX11/blockbench-plugins',
  pluginCatalogRef: '38862eb66b219995b09926488f7d1084a0fb6b3a',
  runtimeRoots: EMF_CEM_RUNTIME_ROOTS,
});

const PROFILE_ID = 'emf_cem_entity';
const JEM_FIELDS = new Set(['credit', 'texture', 'textureSize', 'shadowSize', 'models']);
const PART_FIELDS = new Set([
  'credit', 'texture', 'textureSize', 'invertAxis', 'translate', 'rotate', 'mirrorTexture',
  'boxes', 'submodel', 'submodels', 'baseId', 'model', 'id', 'part', 'attach', 'scale',
  'attachments', 'animations',
]);
const BOX_COMMON_FIELDS = new Set([
  'textureOffset', 'uvDown', 'uvUp', 'uvFront', 'uvBack', 'uvLeft', 'uvRight',
  'uvNorth', 'uvSouth', 'uvWest', 'uvEast', 'coordinates', 'sizeAdd',
]);
const BOX_EMF_ONLY_FIELDS = new Set(['sizeAddX', 'sizeAddY', 'sizeAddZ', 'sizesAdd']);
const BOX_FIELDS = new Set([...BOX_COMMON_FIELDS, ...BOX_EMF_ONLY_FIELDS]);
const EMF_ONLY_PART_FIELDS = new Set(['attachments']);
const UV_FIELDS = [
  'uvDown', 'uvUp', 'uvFront', 'uvBack', 'uvLeft', 'uvRight',
  'uvNorth', 'uvSouth', 'uvWest', 'uvEast',
];

class EmfCemContractError extends Error {
  constructor(code, message) {
    super(`${code}: ${message}`);
    this.name = 'EmfCemContractError';
    this.code = code;
  }
}

function fail(code, message) {
  throw new EmfCemContractError(code, message);
}

function requireObject(value, field, code = 'INVALID_EMF_CEM_DOCUMENT') {
  if (!isPlainObject(value)) fail(code, `${field} must be a plain object.`);
  return value;
}

function rejectUnknownFields(value, allowed, code, field) {
  for (const key of Object.keys(value)) {
    if (!allowed.has(key)) fail(code, `${field}.${key} is outside the audited EMF/CEM contract.`);
  }
}

function cloneAndFreeze(value, field = 'document') {
  if (Array.isArray(value)) {
    return Object.freeze(value.map((item, index) => cloneAndFreeze(item, `${field}[${index}]`)));
  }
  if (isPlainObject(value)) {
    const output = {};
    for (const [key, item] of Object.entries(value)) output[key] = cloneAndFreeze(item, `${field}.${key}`);
    return Object.freeze(output);
  }
  if (value === null || ['string', 'number', 'boolean'].includes(typeof value)) return value;
  fail('INVALID_EMF_CEM_DOCUMENT_VALUE', `${field} contains a value that cannot be preserved in audited JSON output.`);
}

function normalizeBlockbenchEmfCemDocument(value) {
  requireObject(value, 'Blockbench CEM document');
  return cloneAndFreeze(value, 'Blockbench CEM document');
}

function finiteNumber(value, field) {
  if (!Number.isFinite(value)) fail('INVALID_EMF_CEM_NUMBER', `${field} must be finite.`);
  return value;
}

function numericArray(value, field, lengths, {positive = false} = {}) {
  if (!Array.isArray(value) || !lengths.includes(value.length) || !value.every(Number.isFinite)) {
    fail('INVALID_EMF_CEM_ARRAY', `${field} must contain ${lengths.join(' or ')} finite numeric values.`);
  }
  if (positive && value.some((entry) => entry <= 0)) {
    fail('INVALID_EMF_CEM_ARRAY', `${field} values must be positive.`);
  }
  return value;
}

function optionalString(object, key, field) {
  if (object[key] !== undefined && typeof object[key] !== 'string') {
    fail('INVALID_EMF_CEM_STRING', `${field}.${key} must be a string.`);
  }
}

function optionalBoolean(object, key, field) {
  if (object[key] !== undefined && typeof object[key] !== 'boolean') {
    fail('INVALID_EMF_CEM_BOOLEAN', `${field}.${key} must be boolean.`);
  }
}

function validateAnimationDialect(value) {
  if (value !== 'optifine' && value !== 'emf') {
    fail('INVALID_EMF_CEM_ANIMATION_DIALECT', 'animationDialect must be explicitly optifine or emf.');
  }
  return value;
}

function markEmfOnly(state, dialect, field) {
  if (dialect !== 'emf') {
    fail('EMF_ONLY_FIELD_REQUIRES_EMF_DIALECT', `${field} is EMF-only and requires animationDialect=emf.`);
  }
  state.emfOnly = true;
}

function validateAnimations(value, field, state) {
  if (value === undefined || value === null) return;
  if (!Array.isArray(value)) fail('INVALID_EMF_CEM_ANIMATIONS', `${field} must be an array.`);
  for (let index = 0; index < value.length; index += 1) {
    const expressionMap = requireObject(value[index], `${field}[${index}]`, 'INVALID_EMF_CEM_ANIMATIONS');
    for (const [key, expression] of Object.entries(expressionMap)) {
      if (!key.trim() || typeof expression !== 'string') {
        fail('INVALID_EMF_CEM_ANIMATION_EXPRESSION', `${field}[${index}] must map non-empty animation keys to string expressions.`);
      }
      state.animationExpressionCount += 1;
    }
  }
}

function validateTextureSize(value, field) {
  if (value !== undefined) numericArray(value, field, [2], {positive: true});
}

function validateOptionalVector3(value, field) {
  if (value !== undefined) numericArray(value, field, [3]);
}

function validateOptionalUv(value, field) {
  if (value !== undefined) numericArray(value, field, [0, 4]);
}

function validateBox(value, field, dialect, state) {
  const box = requireObject(value, field, 'INVALID_EMF_CEM_BOX');
  rejectUnknownFields(box, BOX_FIELDS, 'UNPROVEN_EMF_CEM_BOX_FIELD', field);
  if (box.coordinates !== undefined) numericArray(box.coordinates, `${field}.coordinates`, [6]);
  if (box.textureOffset !== undefined) numericArray(box.textureOffset, `${field}.textureOffset`, [0, 2]);
  for (const uvField of UV_FIELDS) validateOptionalUv(box[uvField], `${field}.${uvField}`);
  if (box.sizeAdd !== undefined) finiteNumber(box.sizeAdd, `${field}.sizeAdd`);
  for (const key of ['sizeAddX', 'sizeAddY', 'sizeAddZ']) {
    if (box[key] !== undefined) {
      markEmfOnly(state, dialect, `${field}.${key}`);
      finiteNumber(box[key], `${field}.${key}`);
    }
  }
  if (box.sizesAdd !== undefined) {
    markEmfOnly(state, dialect, `${field}.sizesAdd`);
    numericArray(box.sizesAdd, `${field}.sizesAdd`, [0, 3]);
  }
}

function validateAttachments(value, field, dialect, state) {
  if (value === undefined) return;
  markEmfOnly(state, dialect, field);
  const attachments = requireObject(value, field, 'INVALID_EMF_CEM_ATTACHMENTS');
  for (const [name, vector] of Object.entries(attachments)) {
    if (!name.trim()) fail('INVALID_EMF_CEM_ATTACHMENTS', `${field} attachment names must not be blank.`);
    numericArray(vector, `${field}.${name}`, [3]);
  }
}

function validatePart(value, field, dialect, state, {jpmRoot = false} = {}) {
  const part = requireObject(value, field, 'INVALID_EMF_CEM_PART');
  rejectUnknownFields(part, PART_FIELDS, 'UNPROVEN_EMF_CEM_PART_FIELD', field);

  if (!jpmRoot && part.credit !== undefined) {
    fail('UNPROVEN_EMF_CEM_PART_FIELD', `${field}.credit is only audited for a JPM root export.`);
  }
  optionalString(part, 'credit', field);
  optionalString(part, 'texture', field);
  optionalString(part, 'invertAxis', field);
  optionalString(part, 'mirrorTexture', field);
  optionalString(part, 'baseId', field);
  optionalString(part, 'model', field);
  optionalString(part, 'id', field);
  optionalString(part, 'part', field);
  optionalBoolean(part, 'attach', field);
  if (part.scale !== undefined) finiteNumber(part.scale, `${field}.scale`);
  validateTextureSize(part.textureSize, `${field}.textureSize`);
  validateOptionalVector3(part.translate, `${field}.translate`);
  validateOptionalVector3(part.rotate, `${field}.rotate`);

  if (typeof part.model === 'string' && (part.model.includes('..') || part.model.includes('\\'))) {
    fail('INVALID_EMF_CEM_MODEL_REFERENCE', `${field}.model must not contain traversal or backslash path segments.`);
  }

  if (part.boxes !== undefined) {
    if (!Array.isArray(part.boxes)) fail('INVALID_EMF_CEM_BOXES', `${field}.boxes must be an array.`);
    part.boxes.forEach((box, index) => validateBox(box, `${field}.boxes[${index}]`, dialect, state));
  }

  validateAttachments(part.attachments, `${field}.attachments`, dialect, state);
  validateAnimations(part.animations, `${field}.animations`, state);

  if (part.submodel !== undefined && part.submodel !== null) {
    validatePart(part.submodel, `${field}.submodel`, dialect, state);
  }
  if (part.submodels !== undefined) {
    if (!Array.isArray(part.submodels)) fail('INVALID_EMF_CEM_SUBMODELS', `${field}.submodels must be an array.`);
    part.submodels.forEach((submodel, index) => validatePart(submodel, `${field}.submodels[${index}]`, dialect, state));
  }
}

function validateEmfCemJemDocument(value, options = {}) {
  const dialect = validateAnimationDialect(options.animationDialect);
  const document = requireObject(value, 'JEM document');
  rejectUnknownFields(document, JEM_FIELDS, 'UNPROVEN_EMF_CEM_JEM_FIELD', 'JEM document');
  optionalString(document, 'credit', 'JEM document');
  optionalString(document, 'texture', 'JEM document');
  validateTextureSize(document.textureSize, 'JEM document.textureSize');
  if (document.shadowSize !== undefined) finiteNumber(document.shadowSize, 'JEM document.shadowSize');
  if (!Array.isArray(document.models)) fail('INVALID_EMF_CEM_MODELS', 'JEM document.models must be an array.');

  const state = {animationExpressionCount: 0, emfOnly: false};
  document.models.forEach((part, index) => validatePart(part, `JEM document.models[${index}]`, dialect, state));
  return Object.freeze({
    ok: true,
    modelCount: document.models.length,
    animationExpressionCount: state.animationExpressionCount,
    emfOnly: state.emfOnly,
  });
}

function validateEmfCemJpmDocument(value, options = {}) {
  const dialect = validateAnimationDialect(options.animationDialect);
  const state = {animationExpressionCount: 0, emfOnly: false};
  validatePart(value, 'JPM document', dialect, state, {jpmRoot: true});
  return Object.freeze({
    ok: true,
    animationExpressionCount: state.animationExpressionCount,
    emfOnly: state.emfOnly,
  });
}

function createEmfCemExportPlan(input) {
  requireObject(input, 'exportPlan', 'INVALID_EMF_CEM_EXPORT_PLAN');
  if (input.profileId !== PROFILE_ID) {
    fail('EMF_CEM_PROFILE_REQUIRED', `profileId must be exactly ${PROFILE_ID}.`);
  }
  const sourcePath = normalizeBbmodelSourcePath(
    input.sourcePath,
    fail,
    'EMF_CEM_SOURCE_NOT_SAVED',
    'Source project must be saved as a .bbmodel before EMF/CEM handoff.',
    'EMF/CEM source authority must remain a saved .bbmodel file.',
  );
  const namespace = validateMinecraftNamespace(
    input.namespace,
    fail,
    'INVALID_EMF_CEM_NAMESPACE',
    'namespace must match the lowercase Minecraft namespace grammar.',
  );
  const resourceName = validateSafeResourceName(
    input.resourceName,
    fail,
    'INVALID_EMF_CEM_RESOURCE_NAME',
    'resourceName must be a safe lowercase CEM id without path traversal.',
  );

  if (input.compatibilityMode !== 'optifine_compatible' && input.compatibilityMode !== 'emf_only') {
    fail('EMF_CEM_COMPATIBILITY_MODE_REQUIRED', 'compatibilityMode must be explicitly optifine_compatible or emf_only.');
  }
  if (input.directoryLayout !== 'flat' && input.directoryLayout !== 'subfolder') {
    fail('EMF_CEM_DIRECTORY_LAYOUT_REQUIRED', 'directoryLayout must be explicitly flat or subfolder.');
  }
  const animationDialect = validateAnimationDialect(input.animationDialect);
  if (input.compatibilityMode === 'optifine_compatible' && animationDialect === 'emf') {
    fail('EMF_ONLY_ANIMATION_REQUIRES_EMF_MODE', 'EMF-only animation semantics cannot be staged under the OptiFine-compatible root.');
  }

  const runtimeRoot = input.compatibilityMode === 'emf_only'
    ? EMF_CEM_AUTHORITY.runtimeRoots.emfOnly
    : EMF_CEM_AUTHORITY.runtimeRoots.optifineCompatible;
  const base = `assets/${namespace}/${runtimeRoot}`;
  const partModelDirectory = input.directoryLayout === 'subfolder' ? `${base}/${resourceName}` : base;
  const jemPath = input.directoryLayout === 'subfolder'
    ? `${partModelDirectory}/${resourceName}.jem`
    : `${base}/${resourceName}.jem`;

  return Object.freeze({
    profileId: PROFILE_ID,
    sourcePath,
    preserveSource: true,
    namespace,
    resourceName,
    compatibilityMode: input.compatibilityMode,
    directoryLayout: input.directoryLayout,
    animationDialect,
    jemPath,
    partModelDirectory,
    blockbenchCodecId: EMF_CEM_AUTHORITY.cemCodecId,
    requiresCemTemplateLoader: true,
    requiresEmfAnimationAddon: animationDialect === 'emf',
    resourcepackFileName: `${resourceName}_emf_cem_resourcepack.zip`,
    runtimeEvidence: 'UNPROVEN',
    runtimeValidated: false,
    f4I6Evidence: false,
  });
}

module.exports = {
  EMF_CEM_AUTHORITY,
  EmfCemContractError,
  createEmfCemExportPlan,
  normalizeBlockbenchEmfCemDocument,
  validateEmfCemJemDocument,
  validateEmfCemJpmDocument,
};
