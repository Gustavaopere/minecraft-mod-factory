'use strict';

const {
  isPlainObject,
  validateMinecraftNamespace,
  validateSafeResourceName,
  normalizeBbmodelSourcePath,
} = require('../common/contract_utils.js');

const EASY_MODEL_ENTITIES_AUTHORITY = Object.freeze({
  providerFamily: 'easy_model_entities',
  minecraftVersion: '1.21.1',
  targetNeoForgeVersion: '21.1.248',
  providerVersion: '2.3.0',
  providerNeoForgeBuildVersion: '21.1.92',
  providerNeoForgeMinimumVersion: '21.1.0',
  runtimeSource: 'MarkusBordihn/BOs-Easy-Model-Entities',
  runtimeRef: '8c912371838c2a26bbb383008ad3999280f075d1',
  blockbenchPluginId: 'easy_model_entities',
  blockbenchPluginVersion: '1.0.0',
  blockbenchPluginSource: 'MarkusBordihn/BOs-Easy-Model-Entities-Blockbench-Plugin',
  blockbenchPluginRef: '99c0bb118d1ef70fac7016c423b528c317e282dc',
  schemaVersion: '0.2.0',
  apiVersion: '2.3.0',
  serverProfileRoot: 'easy_model_entities/profiles',
  renderProfileRoot: 'easy_model_entities/render_profiles',
  modelRoot: 'easy_model_entities/models',
});

const PROFILE_MODEL_TYPES = Object.freeze({
  easy_model_entities_entity: 'entity',
  easy_model_entities_block_entity: 'block_entity',
});

const SERVER_ROOT_FIELDS = new Set([
  'schema_version', 'model_type', 'preset_type', 'version', 'entity', 'block_entity',
  'dimensions', 'movement', 'behavior', 'attributes',
]);
const ENTITY_FIELDS = new Set(['type', 'movement_type', 'body_type']);
const BLOCK_ENTITY_FIELDS = new Set(['type', 'body_type']);
const DIMENSIONS_FIELDS = new Set(['width', 'height', 'eye_height']);
const MOVEMENT_FIELDS = new Set(['speed', 'step_height', 'gravity']);
const BEHAVIOR_FIELDS = new Set(['mode', 'look_at_players', 'random_stroll']);
const ATTRIBUTES_FIELDS = new Set(['max_health', 'movement_speed', 'follow_range']);

const RENDER_ROOT_FIELDS = new Set([
  'schema_version', 'preset_type', 'version', 'asset_fingerprint', 'body_type', 'model',
  'texture', 'textures', 'rendering', 'animation',
]);
const RENDERING_FIELDS = new Set([
  'scale', 'shadow_radius', 'visible_bounds_width', 'visible_bounds_height',
  'visible_bounds_offset', 'opacity',
]);
const ANIMATION_FIELDS = new Set([
  'mode', 'swing_speed', 'walk_speed_multiplier', 'idle_strength', 'gait', 'variant_mode',
]);

const ENTITY_PRESETS = new Set([
  'custom', 'static', 'statue', 'aquatic_still', 'aquatic_swimming',
  'amphibious_still', 'amphibious_wandering', 'arthropod_still',
  'arthropod_wandering', 'cuboid_hopping', 'cuboid_still', 'floating_still',
  'humanoid_still', 'humanoid_wandering', 'quadruped_still',
  'quadruped_wandering', 'winged_humanoid_still', 'winged_humanoid_wandering',
  'winged_still', 'winged_wandering',
]);
const BLOCK_ENTITY_PRESETS = new Set(['static', 'ticking', 'animated', 'animated_randomly']);
const BODY_TYPES = new Set([
  'static', 'biped', 'quadruped', 'aquatic', 'amphibious', 'winged',
  'winged_humanoid', 'arthropod', 'cuboid', 'floating',
]);
const MOVEMENT_TYPES = new Set(['ground', 'water', 'amphibious', 'static']);
const BEHAVIOR_MODES = new Set(['idle_only', 'ambient', 'static', 'external_owner']);
const ANIMATION_MODES = new Set(['automatic', 'random_idle', 'none']);
const GAIT_TYPES = new Set(['natural', 'feline', 'ungulate']);
const VARIANT_MODES = new Set(['random', 'sequential', 'none']);

class EasyModelEntitiesContractError extends Error {
  constructor(code, message) {
    super(`${code}: ${message}`);
    this.name = 'EasyModelEntitiesContractError';
    this.code = code;
  }
}

function fail(code, message) {
  throw new EasyModelEntitiesContractError(code, message);
}

function rejectUnknownFields(value, allowed, code, field) {
  for (const key of Object.keys(value)) {
    if (!allowed.has(key)) fail(code, `${field}.${key} is outside the audited Easy Model Entities 2.3.0 contract.`);
  }
}

function requireObject(value, field, code = 'INVALID_EASY_MODEL_ENTITIES_PROFILE') {
  if (!isPlainObject(value)) fail(code, `${field} must be an object.`);
  return value;
}

function optionalObject(value, field, allowed, code) {
  if (value === undefined) return null;
  const object = requireObject(value, field, code);
  rejectUnknownFields(object, allowed, code, field);
  return object;
}

function finiteNumber(value, field, options = {}) {
  if (!Number.isFinite(value)) fail('INVALID_EASY_MODEL_ENTITIES_NUMBER', `${field} must be finite.`);
  if (options.positive && value <= 0) fail('INVALID_EASY_MODEL_ENTITIES_NUMBER', `${field} must be positive.`);
  if (options.nonNegative && value < 0) fail('INVALID_EASY_MODEL_ENTITIES_NUMBER', `${field} must not be negative.`);
  if (options.max !== undefined && value > options.max) fail('INVALID_EASY_MODEL_ENTITIES_NUMBER', `${field} exceeds the audited maximum.`);
  return value;
}

function optionalFinite(object, key, field, options) {
  if (object && object[key] !== undefined) finiteNumber(object[key], `${field}.${key}`, options);
}

function enumValue(value, allowed, field, code = 'INVALID_EASY_MODEL_ENTITIES_ENUM') {
  if (typeof value !== 'string' || !allowed.has(value)) fail(code, `${field} is not part of the audited Easy Model Entities contract.`);
  return value;
}

function optionalEnum(object, key, allowed, field) {
  if (object && object[key] !== undefined) enumValue(object[key], allowed, `${field}.${key}`);
}

function optionalBoolean(object, key, field) {
  if (object && object[key] !== undefined && typeof object[key] !== 'boolean') {
    fail('INVALID_EASY_MODEL_ENTITIES_BOOLEAN', `${field}.${key} must be boolean.`);
  }
}

function optionalString(object, key, field) {
  if (object[key] !== undefined && typeof object[key] !== 'string') {
    fail('INVALID_EASY_MODEL_ENTITIES_STRING', `${field}.${key} must be a string.`);
  }
}

function resourceLocation(value, field) {
  if (typeof value !== 'string' || !/^[a-z0-9_.-]+:[a-z0-9_./-]+$/.test(value)) {
    fail('INVALID_EASY_MODEL_ENTITIES_RESOURCE_LOCATION', `${field} must be a lowercase Minecraft resource location.`);
  }
  return value;
}

function optionalResourceLocation(object, key, field) {
  if (object && object[key] !== undefined) resourceLocation(object[key], `${field}.${key}`);
}

function expectedModelType(profileId) {
  const modelType = PROFILE_MODEL_TYPES[profileId];
  if (!modelType) fail('EASY_MODEL_ENTITIES_PROFILE_REQUIRED', 'profileId must identify an audited Easy Model Entities entity or block-entity profile.');
  return modelType;
}

function createEasyModelEntitiesExportPlan(input) {
  requireObject(input, 'exportPlan', 'INVALID_EASY_MODEL_ENTITIES_EXPORT_PLAN');
  const modelType = expectedModelType(input.profileId);
  const sourcePath = normalizeBbmodelSourcePath(
    input.sourcePath,
    fail,
    'EASY_MODEL_ENTITIES_SOURCE_NOT_SAVED',
    'Source project must be saved as a .bbmodel before Easy Model Entities handoff.',
    'Easy Model Entities source authority must remain a saved .bbmodel file.',
  );
  const namespace = validateMinecraftNamespace(
    input.namespace,
    fail,
    'INVALID_EASY_MODEL_ENTITIES_NAMESPACE',
    'namespace must match the Minecraft lowercase namespace grammar.',
  );
  const resourceName = validateSafeResourceName(
    input.resourceName,
    fail,
    'INVALID_EASY_MODEL_ENTITIES_RESOURCE_NAME',
    'resourceName must be a safe lowercase profile/model id without path traversal.',
  );
  return Object.freeze({
    profileId: input.profileId,
    modelType,
    sourcePath,
    preserveSource: true,
    namespace,
    resourceName,
    serverProfilePath: `data/${namespace}/${EASY_MODEL_ENTITIES_AUTHORITY.serverProfileRoot}/${modelType}/${resourceName}.json`,
    renderProfilePath: `assets/${namespace}/${EASY_MODEL_ENTITIES_AUTHORITY.renderProfileRoot}/${modelType}/${resourceName}.json`,
    modelPath: `assets/${namespace}/${EASY_MODEL_ENTITIES_AUTHORITY.modelRoot}/${resourceName}.bbmodel`,
    datapackFileName: `${resourceName}_datapack.zip`,
    resourcepackFileName: `${resourceName}_resourcepack.zip`,
    runtimeEvidence: 'UNPROVEN',
  });
}

function validateSchema(value, field) {
  if (value !== EASY_MODEL_ENTITIES_AUTHORITY.schemaVersion) {
    fail('EASY_MODEL_ENTITIES_SCHEMA_UNSUPPORTED', `${field} must be exactly ${EASY_MODEL_ENTITIES_AUTHORITY.schemaVersion} for the audited exporter contract.`);
  }
}

function validateEasyModelEntitiesServerProfile(value, options = {}) {
  const document = requireObject(value, 'serverProfile');
  rejectUnknownFields(document, SERVER_ROOT_FIELDS, 'UNPROVEN_EASY_MODEL_ENTITIES_PROFILE_FIELD', 'serverProfile');
  validateSchema(document.schema_version, 'serverProfile.schema_version');

  if (options.modelType !== 'entity' && options.modelType !== 'block_entity') {
    fail('INVALID_EASY_MODEL_ENTITIES_MODEL_TYPE', 'options.modelType must be entity or block_entity.');
  }
  if (document.model_type !== options.modelType) {
    fail('EASY_MODEL_ENTITIES_MODEL_TYPE_MISMATCH', `serverProfile.model_type must be ${options.modelType}.`);
  }
  const presets = options.modelType === 'block_entity' ? BLOCK_ENTITY_PRESETS : ENTITY_PRESETS;
  enumValue(document.preset_type, presets, 'serverProfile.preset_type');
  optionalString(document, 'version', 'serverProfile');

  const entity = optionalObject(document.entity, 'serverProfile.entity', ENTITY_FIELDS, 'UNPROVEN_EASY_MODEL_ENTITIES_PROFILE_FIELD');
  const blockEntity = optionalObject(document.block_entity, 'serverProfile.block_entity', BLOCK_ENTITY_FIELDS, 'UNPROVEN_EASY_MODEL_ENTITIES_PROFILE_FIELD');
  const dimensions = optionalObject(document.dimensions, 'serverProfile.dimensions', DIMENSIONS_FIELDS, 'UNPROVEN_EASY_MODEL_ENTITIES_PROFILE_FIELD');
  const movement = optionalObject(document.movement, 'serverProfile.movement', MOVEMENT_FIELDS, 'UNPROVEN_EASY_MODEL_ENTITIES_PROFILE_FIELD');
  const behavior = optionalObject(document.behavior, 'serverProfile.behavior', BEHAVIOR_FIELDS, 'UNPROVEN_EASY_MODEL_ENTITIES_PROFILE_FIELD');
  const attributes = optionalObject(document.attributes, 'serverProfile.attributes', ATTRIBUTES_FIELDS, 'UNPROVEN_EASY_MODEL_ENTITIES_PROFILE_FIELD');

  if (options.modelType === 'entity' && blockEntity) fail('EASY_MODEL_ENTITIES_MODEL_TYPE_MISMATCH', 'entity profiles must not carry block_entity settings.');
  if (options.modelType === 'block_entity' && (entity || movement || behavior || attributes)) {
    fail('EASY_MODEL_ENTITIES_MODEL_TYPE_MISMATCH', 'block_entity profiles must not carry entity-only settings.');
  }

  optionalResourceLocation(entity, 'type', 'serverProfile.entity');
  optionalEnum(entity, 'movement_type', MOVEMENT_TYPES, 'serverProfile.entity');
  optionalEnum(entity, 'body_type', BODY_TYPES, 'serverProfile.entity');
  optionalResourceLocation(blockEntity, 'type', 'serverProfile.block_entity');
  optionalEnum(blockEntity, 'body_type', BODY_TYPES, 'serverProfile.block_entity');

  optionalFinite(dimensions, 'width', 'serverProfile.dimensions', {positive: true});
  optionalFinite(dimensions, 'height', 'serverProfile.dimensions', {positive: true});
  optionalFinite(dimensions, 'eye_height', 'serverProfile.dimensions', {nonNegative: true});
  optionalFinite(movement, 'speed', 'serverProfile.movement', {nonNegative: true});
  optionalFinite(movement, 'step_height', 'serverProfile.movement', {nonNegative: true});
  optionalBoolean(movement, 'gravity', 'serverProfile.movement');
  optionalEnum(behavior, 'mode', BEHAVIOR_MODES, 'serverProfile.behavior');
  optionalBoolean(behavior, 'look_at_players', 'serverProfile.behavior');
  optionalBoolean(behavior, 'random_stroll', 'serverProfile.behavior');
  optionalFinite(attributes, 'max_health', 'serverProfile.attributes', {positive: true});
  optionalFinite(attributes, 'movement_speed', 'serverProfile.attributes', {nonNegative: true});
  optionalFinite(attributes, 'follow_range', 'serverProfile.attributes', {nonNegative: true});

  return Object.freeze({ok: true, schemaVersion: document.schema_version, modelType: document.model_type, presetType: document.preset_type});
}

function validateTextures(value, field) {
  if (value === undefined) return;
  const object = requireObject(value, field, 'INVALID_EASY_MODEL_ENTITIES_TEXTURES');
  for (const [key, location] of Object.entries(object)) {
    if (!/^\d+$/.test(key)) fail('INVALID_EASY_MODEL_ENTITIES_TEXTURES', `${field} keys must be non-negative integer texture indices.`);
    resourceLocation(location, `${field}.${key}`);
  }
}

function validateEasyModelEntitiesRenderProfile(value, options = {}) {
  const document = requireObject(value, 'renderProfile', 'INVALID_EASY_MODEL_ENTITIES_RENDER_PROFILE');
  rejectUnknownFields(document, RENDER_ROOT_FIELDS, 'UNPROVEN_EASY_MODEL_ENTITIES_RENDER_FIELD', 'renderProfile');
  validateSchema(document.schema_version, 'renderProfile.schema_version');
  enumValue(document.preset_type, ENTITY_PRESETS, 'renderProfile.preset_type');
  optionalString(document, 'version', 'renderProfile');
  optionalString(document, 'asset_fingerprint', 'renderProfile');
  if (document.body_type !== undefined) enumValue(document.body_type, BODY_TYPES, 'renderProfile.body_type');

  const namespace = validateMinecraftNamespace(
    options.namespace,
    fail,
    'INVALID_EASY_MODEL_ENTITIES_NAMESPACE',
    'namespace must match the Minecraft lowercase namespace grammar.',
  );
  const resourceName = validateSafeResourceName(
    options.resourceName,
    fail,
    'INVALID_EASY_MODEL_ENTITIES_RESOURCE_NAME',
    'resourceName must be a safe lowercase profile/model id without path traversal.',
  );
  const expectedModel = `${namespace}:${EASY_MODEL_ENTITIES_AUTHORITY.modelRoot}/${resourceName}`;
  if (document.model !== expectedModel) {
    fail('EASY_MODEL_ENTITIES_MODEL_PATH_MISMATCH', `renderProfile.model must reference the preserved model ${expectedModel}.`);
  }
  optionalResourceLocation(document, 'texture', 'renderProfile');
  validateTextures(document.textures, 'renderProfile.textures');

  const rendering = optionalObject(document.rendering, 'renderProfile.rendering', RENDERING_FIELDS, 'UNPROVEN_EASY_MODEL_ENTITIES_RENDER_FIELD');
  optionalFinite(rendering, 'scale', 'renderProfile.rendering', {positive: true});
  optionalFinite(rendering, 'shadow_radius', 'renderProfile.rendering', {nonNegative: true});
  optionalFinite(rendering, 'visible_bounds_width', 'renderProfile.rendering', {nonNegative: true});
  optionalFinite(rendering, 'visible_bounds_height', 'renderProfile.rendering', {nonNegative: true});
  if (rendering?.visible_bounds_offset !== undefined) {
    const offset = rendering.visible_bounds_offset;
    if (!Array.isArray(offset) || offset.length !== 3 || !offset.every(Number.isFinite)) {
      fail('INVALID_EASY_MODEL_ENTITIES_VECTOR', 'renderProfile.rendering.visible_bounds_offset must contain exactly three finite numbers.');
    }
  }
  optionalFinite(rendering, 'opacity', 'renderProfile.rendering', {nonNegative: true, max: 1});

  const animation = optionalObject(document.animation, 'renderProfile.animation', ANIMATION_FIELDS, 'UNPROVEN_EASY_MODEL_ENTITIES_RENDER_FIELD');
  optionalEnum(animation, 'mode', ANIMATION_MODES, 'renderProfile.animation');
  optionalFinite(animation, 'swing_speed', 'renderProfile.animation', {nonNegative: true});
  optionalFinite(animation, 'walk_speed_multiplier', 'renderProfile.animation', {nonNegative: true});
  optionalFinite(animation, 'idle_strength', 'renderProfile.animation', {nonNegative: true});
  optionalEnum(animation, 'gait', GAIT_TYPES, 'renderProfile.animation');
  optionalEnum(animation, 'variant_mode', VARIANT_MODES, 'renderProfile.animation');

  return Object.freeze({ok: true, schemaVersion: document.schema_version, model: document.model, presetType: document.preset_type});
}

module.exports = {
  EASY_MODEL_ENTITIES_AUTHORITY,
  EasyModelEntitiesContractError,
  createEasyModelEntitiesExportPlan,
  validateEasyModelEntitiesServerProfile,
  validateEasyModelEntitiesRenderProfile,
};
