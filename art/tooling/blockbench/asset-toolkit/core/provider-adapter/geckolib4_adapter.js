'use strict';

const {isPlainObject} = require('../common/contract_utils.js');

const GECKOLIB4_AUTHORITY = Object.freeze({
  providerFamily: 'geckolib4',
  runtimeVersion: '4.9.2',
  runtimeSource: 'bernie-g/geckolib',
  runtimeRef: 'd57fc640de083ae67ec0051a02b2b4fb22f4d02b',
  blockbenchPluginId: 'geckolib',
  blockbenchPluginVersion: '4.2.5',
  blockbenchPluginSource: 'JannisX11/blockbench-plugins',
  blockbenchPluginRef: '96d3b694de7d44077de68181711816153c442a6f',
});

const GECKOLIB4_PROFILE_IDS = new Set([
  'geckolib4_entity',
  'geckolib4_block_entity',
  'geckolib4_item',
  'geckolib4_armor',
]);
const GEO_FORMAT_VERSIONS = new Set(['1.12.0', '1.14.0', '1.21.0']);
const LOOP_VALUES = new Set(['false', 'play_once', 'true', 'loop', 'hold_on_last_frame']);
const LOCATOR_OBJECT_FIELDS = new Set(['ignore_inherited_scale', 'offset', 'rotation']);

class GeckoLib4ContractError extends Error {
  constructor(code, message) {
    super(`${code}: ${message}`);
    this.name = 'GeckoLib4ContractError';
    this.code = code;
  }
}

function fail(code, message) {
  throw new GeckoLib4ContractError(code, message);
}

function nonEmptyString(value, field) {
  if (typeof value !== 'string' || value.length === 0) fail('INVALID_GECKOLIB4_STRING', `${field} must be a non-empty string.`);
  return value;
}

function finiteNonNegative(value, field) {
  if (!Number.isFinite(value) || value < 0) fail('INVALID_GECKOLIB4_NUMBER', `${field} must be a finite non-negative number.`);
  return value;
}

function vector3(value, field, code = 'INVALID_GECKOLIB4_VECTOR3') {
  if (!Array.isArray(value) || value.length !== 3 || !value.every(Number.isFinite)) {
    fail(code, `${field} must contain exactly three finite numbers.`);
  }
  return value;
}

function validateLocatorValue(value, field) {
  if (Array.isArray(value)) {
    vector3(value, field, 'INVALID_GECKOLIB4_LOCATOR');
    return;
  }
  if (!isPlainObject(value)) fail('INVALID_GECKOLIB4_LOCATOR', `${field} must be a vector or locator object.`);
  for (const key of Object.keys(value)) {
    if (!LOCATOR_OBJECT_FIELDS.has(key)) fail('INVALID_GECKOLIB4_LOCATOR', `${field}.${key} is not supported by GeckoLib 4.9.2.`);
  }
  if (value.ignore_inherited_scale !== undefined && typeof value.ignore_inherited_scale !== 'boolean') {
    fail('INVALID_GECKOLIB4_LOCATOR', `${field}.ignore_inherited_scale must be boolean.`);
  }
  if (value.offset !== undefined) vector3(value.offset, `${field}.offset`, 'INVALID_GECKOLIB4_LOCATOR');
  if (value.rotation !== undefined) vector3(value.rotation, `${field}.rotation`, 'INVALID_GECKOLIB4_LOCATOR');
  if (value.offset === undefined && value.rotation === undefined) {
    fail('INVALID_GECKOLIB4_LOCATOR', `${field} must define offset or rotation.`);
  }
}

function validateGeckoLib4GeoDocument(value) {
  if (!isPlainObject(value)) fail('INVALID_GECKOLIB4_GEO_DOCUMENT', 'Geo document must be an object.');
  const formatVersion = value.format_version;
  if (!GEO_FORMAT_VERSIONS.has(formatVersion)) {
    fail('UNSUPPORTED_GECKOLIB4_GEO_FORMAT', `format_version ${JSON.stringify(formatVersion)} is not supported by GeckoLib 4.9.2.`);
  }
  const geometries = value['minecraft:geometry'];
  if (!Array.isArray(geometries) || geometries.length === 0) {
    fail('INVALID_GECKOLIB4_GEO_DOCUMENT', 'minecraft:geometry must contain at least one geometry entry.');
  }

  let locatorCount = 0;
  geometries.forEach((geometry, geometryIndex) => {
    if (!isPlainObject(geometry)) fail('INVALID_GECKOLIB4_GEO_DOCUMENT', `minecraft:geometry[${geometryIndex}] must be an object.`);
    const bones = geometry.bones === undefined ? [] : geometry.bones;
    if (!Array.isArray(bones)) fail('INVALID_GECKOLIB4_GEO_DOCUMENT', `minecraft:geometry[${geometryIndex}].bones must be an array.`);
    bones.forEach((bone, boneIndex) => {
      if (!isPlainObject(bone)) fail('INVALID_GECKOLIB4_GEO_DOCUMENT', `bone ${boneIndex} must be an object.`);
      if (bone.locators === undefined) return;
      if (!isPlainObject(bone.locators)) fail('INVALID_GECKOLIB4_LOCATOR', `bone ${boneIndex}.locators must be an object.`);
      for (const [locatorName, locatorValue] of Object.entries(bone.locators)) {
        nonEmptyString(locatorName, `bone ${boneIndex} locator name`);
        validateLocatorValue(locatorValue, `bone ${boneIndex}.locators.${locatorName}`);
        locatorCount++;
      }
    });
  });

  return Object.freeze({ok: true, formatVersion, geometryCount: geometries.length, locatorCount});
}

function validateMathScalar(value, field) {
  if (Number.isFinite(value)) return;
  if (typeof value === 'string' && value.length > 0) return;
  fail('INVALID_GECKOLIB4_KEYFRAME', `${field} must be a finite number or Molang string.`);
}

function validateVectorExpression(value, field) {
  if (!Array.isArray(value) || value.length !== 3) fail('INVALID_GECKOLIB4_KEYFRAME', `${field} must contain exactly three values.`);
  value.forEach((entry, index) => validateMathScalar(entry, `${field}[${index}]`));
}

function validateKeyframeLeaf(value, field) {
  if (Number.isFinite(value) || (typeof value === 'string' && value.length > 0)) return;
  if (Array.isArray(value)) {
    validateVectorExpression(value, field);
    return;
  }
  if (!isPlainObject(value)) fail('INVALID_GECKOLIB4_KEYFRAME', `${field} has an unsupported keyframe shape.`);
  if (value.vector !== undefined) {
    validateVectorExpression(value.vector, `${field}.vector`);
    if (value.easing !== undefined && typeof value.easing !== 'string') fail('INVALID_GECKOLIB4_KEYFRAME', `${field}.easing must be a string.`);
    if (value.easingArgs !== undefined && (!Array.isArray(value.easingArgs) || !value.easingArgs.every(Number.isFinite))) {
      fail('INVALID_GECKOLIB4_KEYFRAME', `${field}.easingArgs must contain finite numbers.`);
    }
    return;
  }
  if (value.pre !== undefined) validateVectorExpression(value.pre, `${field}.pre`);
  if (value.post !== undefined) validateVectorExpression(value.post, `${field}.post`);
  if (value.pre === undefined && value.post === undefined) fail('INVALID_GECKOLIB4_KEYFRAME', `${field} must define vector, pre, or post.`);
  if (value.lerp_mode !== undefined && typeof value.lerp_mode !== 'string') fail('INVALID_GECKOLIB4_KEYFRAME', `${field}.lerp_mode must be a string.`);
}

function validateChannel(value, field) {
  if (value === undefined) return;
  if (Number.isFinite(value) || (typeof value === 'string' && value.length > 0) || Array.isArray(value)) {
    validateKeyframeLeaf(value, field);
    return;
  }
  if (!isPlainObject(value)) fail('INVALID_GECKOLIB4_KEYFRAME', `${field} must be a keyframe value or timestamp map.`);
  if (value.vector !== undefined || value.pre !== undefined || value.post !== undefined) {
    validateKeyframeLeaf(value, field);
    return;
  }
  for (const [timestamp, frame] of Object.entries(value)) {
    const time = Number(timestamp);
    if (!Number.isFinite(time) || time < 0) fail('INVALID_GECKOLIB4_TIMESTAMP', `${field}.${timestamp} is not a valid non-negative timestamp.`);
    validateKeyframeLeaf(frame, `${field}.${timestamp}`);
  }
}

function validateEffectTimestamp(timestamp, field) {
  const time = Number(timestamp);
  if (!Number.isFinite(time) || time < 0) fail('INVALID_GECKOLIB4_TIMESTAMP', `${field}.${timestamp} is not a valid non-negative timestamp.`);
}

function validateGeckoLib4AnimationDocument(value) {
  if (!isPlainObject(value)) fail('INVALID_GECKOLIB4_ANIMATION_DOCUMENT', 'Animation document must be an object.');
  if (!isPlainObject(value.animations) || Object.keys(value.animations).length === 0) {
    fail('INVALID_GECKOLIB4_ANIMATION_DOCUMENT', 'animations must be a non-empty object.');
  }

  const effectCounts = {sound: 0, particle: 0, timeline: 0};
  for (const [animationName, animation] of Object.entries(value.animations)) {
    nonEmptyString(animationName, 'animation name');
    if (!isPlainObject(animation)) fail('INVALID_GECKOLIB4_ANIMATION_DOCUMENT', `Animation ${animationName} must be an object.`);
    if (animation.animation_length !== undefined) finiteNonNegative(animation.animation_length, `${animationName}.animation_length`);
    if (animation.loop !== undefined) {
      const loop = typeof animation.loop === 'boolean' ? String(animation.loop) : animation.loop;
      if (typeof loop !== 'string' || !LOOP_VALUES.has(loop)) fail('INVALID_GECKOLIB4_LOOP', `${animationName}.loop is not a supported GeckoLib 4 loop mode.`);
    }
    const bones = animation.bones === undefined ? {} : animation.bones;
    if (!isPlainObject(bones)) fail('INVALID_GECKOLIB4_ANIMATION_DOCUMENT', `${animationName}.bones must be an object.`);
    for (const [boneName, channels] of Object.entries(bones)) {
      nonEmptyString(boneName, `${animationName} bone name`);
      if (!isPlainObject(channels)) fail('INVALID_GECKOLIB4_ANIMATION_DOCUMENT', `${animationName}.bones.${boneName} must be an object.`);
      validateChannel(channels.position, `${animationName}.bones.${boneName}.position`);
      validateChannel(channels.rotation, `${animationName}.bones.${boneName}.rotation`);
      validateChannel(channels.scale, `${animationName}.bones.${boneName}.scale`);
    }

    const sounds = animation.sound_effects === undefined ? {} : animation.sound_effects;
    if (!isPlainObject(sounds)) fail('INVALID_GECKOLIB4_EFFECTS', `${animationName}.sound_effects must be an object.`);
    for (const [timestamp, sound] of Object.entries(sounds)) {
      validateEffectTimestamp(timestamp, `${animationName}.sound_effects`);
      if (!isPlainObject(sound)) fail('INVALID_GECKOLIB4_EFFECTS', `${animationName}.sound_effects.${timestamp} must be an object.`);
      nonEmptyString(sound.effect, `${animationName}.sound_effects.${timestamp}.effect`);
      effectCounts.sound++;
    }

    const particles = animation.particle_effects === undefined ? {} : animation.particle_effects;
    if (!isPlainObject(particles)) fail('INVALID_GECKOLIB4_EFFECTS', `${animationName}.particle_effects must be an object.`);
    for (const [timestamp, particle] of Object.entries(particles)) {
      validateEffectTimestamp(timestamp, `${animationName}.particle_effects`);
      if (!isPlainObject(particle)) fail('INVALID_GECKOLIB4_EFFECTS', `${animationName}.particle_effects.${timestamp} must be an object.`);
      for (const field of ['effect', 'locator', 'pre_effect_script']) {
        if (particle[field] !== undefined && typeof particle[field] !== 'string') {
          fail('INVALID_GECKOLIB4_EFFECTS', `${animationName}.particle_effects.${timestamp}.${field} must be a string.`);
        }
      }
      effectCounts.particle++;
    }

    const timeline = animation.timeline === undefined ? {} : animation.timeline;
    if (!isPlainObject(timeline)) fail('INVALID_GECKOLIB4_EFFECTS', `${animationName}.timeline must be an object.`);
    for (const [timestamp, instruction] of Object.entries(timeline)) {
      validateEffectTimestamp(timestamp, `${animationName}.timeline`);
      const validInstruction = typeof instruction === 'string' || (Array.isArray(instruction) && instruction.every((entry) => typeof entry === 'string'));
      if (!validInstruction) fail('INVALID_GECKOLIB4_EFFECTS', `${animationName}.timeline.${timestamp} must be a string or string array.`);
      effectCounts.timeline++;
    }
  }

  return Object.freeze({
    ok: true,
    animationCount: Object.keys(value.animations).length,
    effectCounts: Object.freeze(effectCounts),
  });
}

function effectTimeKey(value) {
  return String(finiteNonNegative(value, 'effect marker time'));
}

function serializeGeckoLib4EffectMarker(marker, providerData) {
  if (!isPlainObject(marker) || !isPlainObject(providerData)) fail('INVALID_GECKOLIB4_EFFECT_MARKER', 'Effect marker and provider data must be objects.');
  const time = effectTimeKey(marker.time);
  switch (marker.markerType) {
    case 'sound':
      return Object.freeze({
        channel: 'sound_effects',
        time,
        value: Object.freeze({effect: nonEmptyString(providerData.effect, 'sound effect')}),
      });
    case 'particle': {
      const value = {};
      for (const [sourceField, targetField] of [['effect', 'effect'], ['locator', 'locator'], ['preEffectScript', 'pre_effect_script']]) {
        if (providerData[sourceField] !== undefined) value[targetField] = nonEmptyString(providerData[sourceField], `particle ${sourceField}`);
      }
      return Object.freeze({channel: 'particle_effects', time, value: Object.freeze(value)});
    }
    case 'timeline':
      if (typeof providerData.instruction !== 'string' && !(Array.isArray(providerData.instruction) && providerData.instruction.every((entry) => typeof entry === 'string'))) {
        fail('INVALID_GECKOLIB4_EFFECT_MARKER', 'timeline instruction must be a string or string array.');
      }
      return Object.freeze({channel: 'timeline', time, value: providerData.instruction});
    default:
      fail('UNSUPPORTED_GECKOLIB4_EFFECT_MARKER', `Marker type ${JSON.stringify(marker.markerType)} has no audited GeckoLib 4 mapping.`);
  }
}

function normalizedSourceAuthorityPath(value) {
  const output = nonEmptyString(value, 'sourcePath').replace(/\\/g, '/').replace(/\/$/, '');
  if (output.split('/').includes('..')) fail('INVALID_GECKOLIB4_SOURCE_PATH', 'sourcePath must not contain traversal segments.');
  return output;
}

function normalizedRelativePath(value, field) {
  const output = nonEmptyString(value, field).replace(/\\/g, '/').replace(/\/$/, '');
  if (output.startsWith('/') || /^[A-Za-z]:/.test(output) || output.split('/').includes('..')) fail('INVALID_GECKOLIB4_PATH', `${field} must be a safe relative path.`);
  return output;
}

function createGeckoLib4ExportPlan(input) {
  if (!isPlainObject(input)) fail('INVALID_GECKOLIB4_EXPORT_PLAN', 'Export plan request must be an object.');
  if (!GECKOLIB4_PROFILE_IDS.has(input.profileId)) fail('INVALID_GECKOLIB4_PROFILE', `Profile ${JSON.stringify(input.profileId)} is not a GeckoLib 4 profile.`);
  const sourcePath = normalizedSourceAuthorityPath(input.sourcePath);
  if (!sourcePath.toLowerCase().endsWith('.bbmodel')) fail('GECKOLIB4_SOURCE_MUST_BE_BBMODEL', 'Source authority must remain a .bbmodel file.');
  const outputDirectory = normalizedRelativePath(input.outputDirectory, 'outputDirectory');
  const resourceName = nonEmptyString(input.resourceName, 'resourceName');
  if (!/^[a-z0-9_.-]+$/.test(resourceName)) fail('INVALID_GECKOLIB4_RESOURCE_NAME', 'resourceName must be filesystem/resource-safe lowercase text.');
  if (input.includeAnimations !== undefined && typeof input.includeAnimations !== 'boolean') fail('INVALID_GECKOLIB4_EXPORT_PLAN', 'includeAnimations must be boolean.');

  const artifacts = [{kind: 'model', path: `${outputDirectory}/${resourceName}.geo.json`}];
  if (input.includeAnimations === true) artifacts.push({kind: 'animation', path: `${outputDirectory}/${resourceName}.animation.json`});

  return Object.freeze({
    providerFamily: 'geckolib4',
    profileId: input.profileId,
    sourcePath,
    preserveSource: true,
    artifacts: Object.freeze(artifacts.map((artifact) => Object.freeze(artifact))),
    runtimeEvidence: 'UNPROVEN',
  });
}

module.exports = {
  GECKOLIB4_AUTHORITY,
  GeckoLib4ContractError,
  validateGeckoLib4GeoDocument,
  validateGeckoLib4AnimationDocument,
  serializeGeckoLib4EffectMarker,
  createGeckoLib4ExportPlan,
};
