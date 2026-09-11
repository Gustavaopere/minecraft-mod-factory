'use strict';

const {isPlainObject} = require('../common/contract_utils.js');

const AZURELIB3_AUTHORITY = Object.freeze({
  providerFamily: 'azurelib',
  runtimeVersion: '3.1.11',
  runtimeSource: 'AzureDoom/AzureLib',
  runtimeRef: '74ca485d43089c6953492ae7a10fc896eda30385',
  blockbenchPluginId: 'azurelib_utils',
  blockbenchPluginVersion: '2.1.5',
  blockbenchPluginSource: 'AzureDoom/AzureLib',
  blockbenchPluginRef: '4aac02dcefff5440874b3ec64871a1cd0feffadf',
  blockbenchFormatId: 'azure_model',
  animationFormatVersion: '1.8.0',
});

const AZURELIB3_PROFILE_IDS = new Set([
  'azurelib_entity',
  'azurelib_item',
  'azurelib_block',
  'azurelib_armor',
]);

const GEO_FORMAT_VERSIONS = new Set(['1.12.0', '1.14.0', '1.21.0']);

const LOOP_VALUES = new Set([
  'false',
  'true',
  'play_once',
  'hold_on_last_frame',
  'loop',
]);

const EASING_NAMES = new Set([
  'none',
  'linear',
  'step',
  'easeinsine',
  'easeoutsine',
  'easeinoutsine',
  'easeinquad',
  'easeoutquad',
  'easeinoutquad',
  'easeincubic',
  'easeoutcubic',
  'easeinoutcubic',
  'easeinquart',
  'easeoutquart',
  'easeinoutquart',
  'easeinquint',
  'easeoutquint',
  'easeinoutquint',
  'easeinexpo',
  'easeoutexpo',
  'easeinoutexpo',
  'easeincirc',
  'easeoutcirc',
  'easeinoutcirc',
  'easeinback',
  'easeoutback',
  'easeinoutback',
  'easeinelastic',
  'easeoutelastic',
  'easeinoutelastic',
  'easeinbounce',
  'easeoutbounce',
  'easeinoutbounce',
  'bezier',
  'bezier_after',
  'catmullrom',
]);

const ROOT_FIELDS = new Set(['format_version', 'includes', 'animations']);
const ANIMATION_FIELDS = new Set([
  'animation_length',
  'loop',
  'bones',
  'sound_effects',
  'particle_effects',
  'timeline',
]);
const BONE_FIELDS = new Set(['position', 'rotation', 'scale']);
const KEYFRAME_FIELDS = new Set(['vector', 'easing', 'easingArgs', 'pre', 'post', 'lerp_mode']);
const SOUND_FIELDS = new Set(['effect']);
const PARTICLE_FIELDS = new Set(['effect', 'locator', 'pre_effect_script']);
const INCLUDE_FIELDS = new Set(['file_id', 'animations']);

class AzureLib3ContractError extends Error {
  constructor(code, message) {
    super(`${code}: ${message}`);
    this.name = 'AzureLib3ContractError';
    this.code = code;
  }
}

function fail(code, message) {
  throw new AzureLib3ContractError(code, message);
}

function nonEmptyString(value, field) {
  if (typeof value !== 'string' || value.length === 0) {
    fail('INVALID_AZURELIB3_STRING', `${field} must be a non-empty string.`);
  }
  return value;
}

function finiteNonNegative(value, field) {
  if (!Number.isFinite(value) || value < 0) {
    fail('INVALID_AZURELIB3_NUMBER', `${field} must be a finite non-negative number.`);
  }
  return value;
}

function rejectUnknownFields(value, allowedFields, field) {
  for (const key of Object.keys(value)) {
    if (!allowedFields.has(key)) {
      fail('UNPROVEN_AZURELIB3_RUNTIME_FIELD', `${field}.${key} is not part of the audited AzureLib 3.1.11 runtime contract.`);
    }
  }
}

function validateAzureLib3GeoDocument(value) {
  if (!isPlainObject(value)) {
    fail('INVALID_AZURELIB3_GEO_DOCUMENT', 'Geo document must be an object.');
  }
  if (Object.prototype.hasOwnProperty.call(value, 'azureIKChains')) {
    fail('UNPROVEN_AZURELIB3_RUNTIME_FIELD', 'azureIKChains is Blockbench authoring metadata and must not be serialized into AzureLib runtime geometry.');
  }

  const formatVersion = value.format_version;
  if (!GEO_FORMAT_VERSIONS.has(formatVersion)) {
    fail('UNSUPPORTED_AZURELIB3_GEO_FORMAT', `format_version ${JSON.stringify(formatVersion)} is not supported by AzureLib 3.1.11.`);
  }

  const geometries = value['minecraft:geometry'];
  if (!Array.isArray(geometries) || geometries.length === 0) {
    fail('INVALID_AZURELIB3_GEO_DOCUMENT', 'minecraft:geometry must contain at least one geometry entry.');
  }

  let boneCount = 0;
  geometries.forEach((geometry, geometryIndex) => {
    if (!isPlainObject(geometry)) {
      fail('INVALID_AZURELIB3_GEO_DOCUMENT', `minecraft:geometry[${geometryIndex}] must be an object.`);
    }
    const bones = geometry.bones === undefined ? [] : geometry.bones;
    if (!Array.isArray(bones)) {
      fail('INVALID_AZURELIB3_GEO_DOCUMENT', `minecraft:geometry[${geometryIndex}].bones must be an array.`);
    }
    bones.forEach((bone, boneIndex) => {
      if (!isPlainObject(bone)) {
        fail('INVALID_AZURELIB3_GEO_DOCUMENT', `minecraft:geometry[${geometryIndex}].bones[${boneIndex}] must be an object.`);
      }
      boneCount += 1;
    });
  });

  return Object.freeze({
    ok: true,
    formatVersion,
    geometryCount: geometries.length,
    boneCount,
  });
}

function validateMathScalar(value, field) {
  if (Number.isFinite(value)) return;
  if (typeof value === 'string' && value.length > 0) return;
  fail('INVALID_AZURELIB3_KEYFRAME', `${field} must be a finite number or Molang string.`);
}

function validateVectorExpression(value, field) {
  if (!Array.isArray(value) || value.length !== 3) {
    fail('INVALID_AZURELIB3_KEYFRAME', `${field} must contain exactly three values.`);
  }
  value.forEach((entry, index) => validateMathScalar(entry, `${field}[${index}]`));
}

function validateEasing(value, field) {
  if (typeof value !== 'string' || !EASING_NAMES.has(value.toLowerCase())) {
    fail('UNSUPPORTED_AZURELIB3_EASING', `${field} ${JSON.stringify(value)} is not registered by AzureLib 3.1.11.`);
  }
}

function validateEasingArgs(value, field) {
  if (!Array.isArray(value) || !value.every(Number.isFinite)) {
    fail('INVALID_AZURELIB3_KEYFRAME', `${field} must contain finite numbers.`);
  }
}

function validateKeyframeLeaf(value, field) {
  if (Number.isFinite(value) || (typeof value === 'string' && value.length > 0)) return;

  if (Array.isArray(value)) {
    validateVectorExpression(value, field);
    return;
  }

  if (!isPlainObject(value)) {
    fail('INVALID_AZURELIB3_KEYFRAME', `${field} has an unsupported keyframe shape.`);
  }

  rejectUnknownFields(value, KEYFRAME_FIELDS, field);

  if (value.vector !== undefined) {
    if (value.pre !== undefined || value.post !== undefined || value.lerp_mode !== undefined) {
      fail('INVALID_AZURELIB3_KEYFRAME', `${field} cannot mix vector/easing and Bedrock pre/post keyframe forms.`);
    }
    validateVectorExpression(value.vector, `${field}.vector`);
    if (value.easing !== undefined) validateEasing(value.easing, `${field}.easing`);
    if (value.easingArgs !== undefined) validateEasingArgs(value.easingArgs, `${field}.easingArgs`);
    return;
  }

  if (value.pre !== undefined) validateVectorExpression(value.pre, `${field}.pre`);
  if (value.post !== undefined) validateVectorExpression(value.post, `${field}.post`);
  if (value.pre === undefined && value.post === undefined) {
    fail('INVALID_AZURELIB3_KEYFRAME', `${field} must define vector, pre, or post.`);
  }
  if (value.easing !== undefined || value.easingArgs !== undefined) {
    fail('UNPROVEN_AZURELIB3_RUNTIME_FIELD', `${field} Bedrock pre/post form cannot carry AzureLib easing metadata in the audited runtime contract.`);
  }
  if (value.lerp_mode !== undefined) {
    if (typeof value.lerp_mode !== 'string' || !new Set(['linear', 'catmullrom']).has(value.lerp_mode.toLowerCase())) {
      fail('UNSUPPORTED_AZURELIB3_EASING', `${field}.lerp_mode ${JSON.stringify(value.lerp_mode)} is not an audited Bedrock interpolation mode.`);
    }
  }
}

function validateChannel(value, field) {
  if (value === undefined) return;
  if (Number.isFinite(value) || (typeof value === 'string' && value.length > 0) || Array.isArray(value)) {
    validateKeyframeLeaf(value, field);
    return;
  }
  if (!isPlainObject(value)) {
    fail('INVALID_AZURELIB3_KEYFRAME', `${field} must be a keyframe value or timestamp map.`);
  }
  if (value.vector !== undefined || value.pre !== undefined || value.post !== undefined) {
    validateKeyframeLeaf(value, field);
    return;
  }
  for (const [timestamp, frame] of Object.entries(value)) {
    const time = Number(timestamp);
    if (!Number.isFinite(time) || time < 0) {
      fail('INVALID_AZURELIB3_TIMESTAMP', `${field}.${timestamp} is not a valid non-negative timestamp.`);
    }
    validateKeyframeLeaf(frame, `${field}.${timestamp}`);
  }
}

function validateEffectTimestamp(timestamp, field) {
  const time = Number(timestamp);
  if (!Number.isFinite(time) || time < 0) {
    fail('INVALID_AZURELIB3_TIMESTAMP', `${field}.${timestamp} is not a valid non-negative timestamp.`);
  }
}

function validateIncludes(value) {
  if (value === undefined) return 0;
  if (!Array.isArray(value)) {
    fail('INVALID_AZURELIB3_INCLUDES', 'includes must be an array when present.');
  }

  value.forEach((entry, index) => {
    if (!isPlainObject(entry)) {
      fail('INVALID_AZURELIB3_INCLUDES', `includes[${index}] must be an object.`);
    }
    rejectUnknownFields(entry, INCLUDE_FIELDS, `includes[${index}]`);
    nonEmptyString(entry.file_id, `includes[${index}].file_id`);
    if (!Array.isArray(entry.animations) || entry.animations.length === 0) {
      fail('INVALID_AZURELIB3_INCLUDES', `includes[${index}].animations must be a non-empty string array.`);
    }
    entry.animations.forEach((name, animationIndex) => {
      nonEmptyString(name, `includes[${index}].animations[${animationIndex}]`);
    });
  });

  return value.length;
}

function validateLoop(value, field) {
  if (typeof value === 'boolean') return;
  if (typeof value !== 'string' || !LOOP_VALUES.has(value)) {
    fail('INVALID_AZURELIB3_LOOP', `${field} is not a registered AzureLib 3.1.11 loop type.`);
  }
}

function validateSoundEffects(value, animationName, effectCounts) {
  const sounds = value === undefined ? {} : value;
  if (!isPlainObject(sounds)) {
    fail('INVALID_AZURELIB3_EFFECTS', `${animationName}.sound_effects must be an object.`);
  }

  for (const [timestamp, sound] of Object.entries(sounds)) {
    validateEffectTimestamp(timestamp, `${animationName}.sound_effects`);
    if (Array.isArray(sound)) {
      fail('UNSUPPORTED_AZURELIB3_MULTI_EFFECT_PAYLOAD', `${animationName}.sound_effects.${timestamp} must contain one object because AzureLib 3.1.11 calls getAsJsonObject().`);
    }
    if (!isPlainObject(sound)) {
      fail('INVALID_AZURELIB3_EFFECTS', `${animationName}.sound_effects.${timestamp} must be an object.`);
    }
    rejectUnknownFields(sound, SOUND_FIELDS, `${animationName}.sound_effects.${timestamp}`);
    nonEmptyString(sound.effect, `${animationName}.sound_effects.${timestamp}.effect`);
    effectCounts.sound += 1;
  }
}

function validateParticleEffects(value, animationName, effectCounts) {
  const particles = value === undefined ? {} : value;
  if (!isPlainObject(particles)) {
    fail('INVALID_AZURELIB3_EFFECTS', `${animationName}.particle_effects must be an object.`);
  }

  for (const [timestamp, particle] of Object.entries(particles)) {
    validateEffectTimestamp(timestamp, `${animationName}.particle_effects`);
    if (Array.isArray(particle)) {
      fail('UNSUPPORTED_AZURELIB3_MULTI_EFFECT_PAYLOAD', `${animationName}.particle_effects.${timestamp} must contain one object because AzureLib 3.1.11 calls getAsJsonObject().`);
    }
    if (!isPlainObject(particle)) {
      fail('INVALID_AZURELIB3_EFFECTS', `${animationName}.particle_effects.${timestamp} must be an object.`);
    }
    rejectUnknownFields(particle, PARTICLE_FIELDS, `${animationName}.particle_effects.${timestamp}`);
    for (const field of PARTICLE_FIELDS) {
      if (particle[field] !== undefined && typeof particle[field] !== 'string') {
        fail('INVALID_AZURELIB3_EFFECTS', `${animationName}.particle_effects.${timestamp}.${field} must be a string.`);
      }
    }
    effectCounts.particle += 1;
  }
}

function validateTimeline(value, animationName, effectCounts) {
  const timeline = value === undefined ? {} : value;
  if (!isPlainObject(timeline)) {
    fail('INVALID_AZURELIB3_EFFECTS', `${animationName}.timeline must be an object.`);
  }

  for (const [timestamp, instruction] of Object.entries(timeline)) {
    validateEffectTimestamp(timestamp, `${animationName}.timeline`);
    const validInstruction = typeof instruction === 'string'
      || (Array.isArray(instruction) && instruction.every((entry) => typeof entry === 'string'));
    if (!validInstruction) {
      fail('INVALID_AZURELIB3_EFFECTS', `${animationName}.timeline.${timestamp} must be a string or string array.`);
    }
    effectCounts.timeline += 1;
  }
}

function validateAzureLib3AnimationDocument(value) {
  if (!isPlainObject(value)) {
    fail('INVALID_AZURELIB3_ANIMATION_DOCUMENT', 'Animation document must be an object.');
  }
  rejectUnknownFields(value, ROOT_FIELDS, 'document');

  if (value.format_version !== AZURELIB3_AUTHORITY.animationFormatVersion) {
    fail('UNSUPPORTED_AZURELIB3_ANIMATION_FORMAT', `format_version must be ${AZURELIB3_AUTHORITY.animationFormatVersion}.`);
  }

  const includeCount = validateIncludes(value.includes);

  if (!isPlainObject(value.animations) || Object.keys(value.animations).length === 0) {
    fail('INVALID_AZURELIB3_ANIMATION_DOCUMENT', 'animations must be a non-empty object.');
  }

  const effectCounts = {sound: 0, particle: 0, timeline: 0};

  for (const [animationName, animation] of Object.entries(value.animations)) {
    nonEmptyString(animationName, 'animation name');
    if (!isPlainObject(animation)) {
      fail('INVALID_AZURELIB3_ANIMATION_DOCUMENT', `Animation ${animationName} must be an object.`);
    }
    rejectUnknownFields(animation, ANIMATION_FIELDS, `animations.${animationName}`);

    if (animation.animation_length !== undefined) {
      finiteNonNegative(animation.animation_length, `${animationName}.animation_length`);
    }
    if (animation.loop !== undefined) validateLoop(animation.loop, `${animationName}.loop`);

    const bones = animation.bones === undefined ? {} : animation.bones;
    if (!isPlainObject(bones)) {
      fail('INVALID_AZURELIB3_ANIMATION_DOCUMENT', `${animationName}.bones must be an object.`);
    }

    for (const [boneName, channels] of Object.entries(bones)) {
      nonEmptyString(boneName, `${animationName} bone name`);
      if (!isPlainObject(channels)) {
        fail('INVALID_AZURELIB3_ANIMATION_DOCUMENT', `${animationName}.bones.${boneName} must be an object.`);
      }
      rejectUnknownFields(channels, BONE_FIELDS, `${animationName}.bones.${boneName}`);
      validateChannel(channels.position, `${animationName}.bones.${boneName}.position`);
      validateChannel(channels.rotation, `${animationName}.bones.${boneName}.rotation`);
      validateChannel(channels.scale, `${animationName}.bones.${boneName}.scale`);
    }

    validateSoundEffects(animation.sound_effects, animationName, effectCounts);
    validateParticleEffects(animation.particle_effects, animationName, effectCounts);
    validateTimeline(animation.timeline, animationName, effectCounts);
  }

  return Object.freeze({
    ok: true,
    animationCount: Object.keys(value.animations).length,
    includeCount,
    effectCounts: Object.freeze(effectCounts),
  });
}

function effectTimeKey(value) {
  return String(finiteNonNegative(value, 'effect marker time'));
}

function serializeAzureLib3EffectMarker(marker, providerData) {
  if (!isPlainObject(marker) || !isPlainObject(providerData)) {
    fail('INVALID_AZURELIB3_EFFECT_MARKER', 'Effect marker and provider data must be objects.');
  }

  const time = effectTimeKey(marker.time);

  switch (marker.markerType) {
    case 'sound': {
      rejectUnknownFields(providerData, new Set(['effect']), 'sound providerData');
      return Object.freeze({
        channel: 'sound_effects',
        time,
        value: Object.freeze({effect: nonEmptyString(providerData.effect, 'sound effect')}),
      });
    }
    case 'particle': {
      rejectUnknownFields(providerData, new Set(['effect', 'locator', 'preEffectScript']), 'particle providerData');
      const output = {};
      for (const [sourceField, targetField] of [
        ['effect', 'effect'],
        ['locator', 'locator'],
        ['preEffectScript', 'pre_effect_script'],
      ]) {
        if (providerData[sourceField] !== undefined) {
          output[targetField] = nonEmptyString(providerData[sourceField], `particle ${sourceField}`);
        }
      }
      return Object.freeze({channel: 'particle_effects', time, value: Object.freeze(output)});
    }
    case 'timeline': {
      rejectUnknownFields(providerData, new Set(['instruction']), 'timeline providerData');
      const instruction = providerData.instruction;
      const validInstruction = typeof instruction === 'string'
        || (Array.isArray(instruction) && instruction.every((entry) => typeof entry === 'string'));
      if (!validInstruction) {
        fail('INVALID_AZURELIB3_EFFECT_MARKER', 'timeline instruction must be a string or string array.');
      }
      return Object.freeze({channel: 'timeline', time, value: instruction});
    }
    default:
      fail('UNSUPPORTED_AZURELIB3_EFFECT_MARKER', `Marker type ${JSON.stringify(marker.markerType)} has no audited AzureLib 3.1.11 mapping.`);
  }
}

function normalizedSourceAuthorityPath(value) {
  const output = nonEmptyString(value, 'sourcePath').replace(/\\/g, '/').replace(/\/$/, '');
  if (output.split('/').includes('..')) {
    fail('INVALID_AZURELIB3_SOURCE_PATH', 'sourcePath must not contain traversal segments.');
  }
  return output;
}

function normalizedRelativePath(value, field) {
  const output = nonEmptyString(value, field).replace(/\\/g, '/').replace(/\/$/, '');
  if (output.startsWith('/') || /^[A-Za-z]:/.test(output) || output.split('/').includes('..')) {
    fail('INVALID_AZURELIB3_PATH', `${field} must be a safe relative path.`);
  }
  return output;
}

function createAzureLib3ExportPlan(input) {
  if (!isPlainObject(input)) {
    fail('INVALID_AZURELIB3_EXPORT_PLAN', 'Export plan request must be an object.');
  }
  if (!AZURELIB3_PROFILE_IDS.has(input.profileId)) {
    fail('INVALID_AZURELIB3_PROFILE', `Profile ${JSON.stringify(input.profileId)} is not an AzureLib 3 profile.`);
  }

  const sourcePath = normalizedSourceAuthorityPath(input.sourcePath);
  if (!sourcePath.toLowerCase().endsWith('.bbmodel')) {
    fail('AZURELIB3_SOURCE_MUST_BE_BBMODEL', 'Source authority must remain a .bbmodel file.');
  }

  const outputDirectory = normalizedRelativePath(input.outputDirectory, 'outputDirectory');
  const resourceName = nonEmptyString(input.resourceName, 'resourceName');
  if (!/^[a-z0-9_.-]+$/.test(resourceName)) {
    fail('INVALID_AZURELIB3_RESOURCE_NAME', 'resourceName must be filesystem/resource-safe lowercase text.');
  }
  if (input.includeAnimations !== undefined && typeof input.includeAnimations !== 'boolean') {
    fail('INVALID_AZURELIB3_EXPORT_PLAN', 'includeAnimations must be boolean.');
  }

  const artifacts = [
    Object.freeze({kind: 'model', path: `${outputDirectory}/${resourceName}.geo.json`}),
  ];
  if (input.includeAnimations) {
    artifacts.push(Object.freeze({kind: 'animation', path: `${outputDirectory}/${resourceName}.animation.json`}));
  }

  return Object.freeze({
    providerFamily: 'azurelib',
    profileId: input.profileId,
    sourcePath,
    preserveSource: true,
    artifacts: Object.freeze(artifacts),
    runtimeEvidence: 'UNPROVEN',
  });
}

module.exports = {
  AZURELIB3_AUTHORITY,
  AZURELIB3_PROFILE_IDS,
  AzureLib3ContractError,
  validateAzureLib3GeoDocument,
  validateAzureLib3AnimationDocument,
  serializeAzureLib3EffectMarker,
  createAzureLib3ExportPlan,
};
