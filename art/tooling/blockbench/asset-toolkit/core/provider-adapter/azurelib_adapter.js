'use strict';

const {isPlainObject, rejectUnknownFields} = require('../common/contract_utils.js');

const AZURELIB_AUTHORITY = Object.freeze({
  providerFamily: 'azurelib',
  runtimeVersion: '3.1.11',
  runtimeSource: 'AzureDoom/AzureLib',
  runtimeRef: '4aac02dcefff5440874b3ec64871a1cd0feffadf',
  blockbenchPluginId: 'azurelib_utils',
  blockbenchPluginVersion: '2.1.5',
  blockbenchPluginSource: 'JannisX11/blockbench-plugins',
  blockbenchPluginRef: '38862eb66b219995b09926488f7d1084a0fb6b3a',
  blockbenchFormatId: 'azure_model',
  animationCodecId: 'azure_animation',
  animationFormatVersion: '1.8.0',
});

const AZURELIB_PROFILE_IDS = new Set([
  'azurelib_entity',
  'azurelib_item',
  'azurelib_block',
  'azurelib_armor',
]);
const GEO_FORMAT_VERSIONS = new Set(['1.12.0', '1.14.0', '1.21.0']);
const LOOP_VALUES = new Set(['false', 'true', 'play_once', 'loop', 'hold_on_last_frame']);
const BEDROCK_LERP_MODES = new Set(['linear', 'catmullrom']);
const LOCATOR_OBJECT_FIELDS = new Set(['ignore_inherited_scale', 'offset', 'rotation']);
const AZURE_KEYFRAME_FIELDS = new Set(['vector', 'easing', 'easingArgs']);
const BEDROCK_KEYFRAME_FIELDS = new Set(['pre', 'post', 'lerp_mode']);
const RESOURCE_LOCATION = /^[a-z0-9_.-]+:[a-z0-9/._-]+$/;

class AzureLibContractError extends Error {
  constructor(code, message) {
    super(`${code}: ${message}`);
    this.name = 'AzureLibContractError';
    this.code = code;
  }
}

function fail(code, message) {
  throw new AzureLibContractError(code, message);
}

function nonEmptyString(value, field, code = 'INVALID_AZURELIB_STRING') {
  if (typeof value !== 'string' || !value.trim()) fail(code, `${field} must be a non-empty string.`);
  return value;
}

function finiteNonNegative(value, field) {
  if (!Number.isFinite(value) || value < 0) fail('INVALID_AZURELIB_NUMBER', `${field} must be a finite non-negative number.`);
  return value;
}

function vector3Numbers(value, field, code = 'INVALID_AZURELIB_VECTOR3') {
  if (!Array.isArray(value) || value.length !== 3 || !value.every(Number.isFinite)) {
    fail(code, `${field} must contain exactly three finite numbers.`);
  }
  return value;
}

function rejectAuthoringMetadata(value, artifact) {
  if (Object.prototype.hasOwnProperty.call(value, 'azureIKChains')) {
    fail(
      'AZURELIB_AUTHORING_METADATA_IN_RUNTIME_ARTIFACT',
      `azureIKChains is Blockbench authoring metadata and must not be serialized into AzureLib ${artifact} runtime artifacts.`,
    );
  }
}

function validateLocatorValue(value, field) {
  if (Array.isArray(value)) {
    vector3Numbers(value, field, 'INVALID_AZURELIB_LOCATOR');
    return;
  }
  if (!isPlainObject(value)) fail('INVALID_AZURELIB_LOCATOR', `${field} must be a vector or locator object.`);
  rejectUnknownFields(value, LOCATOR_OBJECT_FIELDS, fail, 'INVALID_AZURELIB_LOCATOR', field);
  if (value.ignore_inherited_scale !== undefined && typeof value.ignore_inherited_scale !== 'boolean') {
    fail('INVALID_AZURELIB_LOCATOR', `${field}.ignore_inherited_scale must be boolean.`);
  }
  if (value.offset !== undefined) vector3Numbers(value.offset, `${field}.offset`, 'INVALID_AZURELIB_LOCATOR');
  if (value.rotation !== undefined) vector3Numbers(value.rotation, `${field}.rotation`, 'INVALID_AZURELIB_LOCATOR');
  if (value.offset === undefined && value.rotation === undefined) {
    fail('INVALID_AZURELIB_LOCATOR', `${field} must define offset or rotation.`);
  }
}

function validateAzureLibGeoDocument(value) {
  if (!isPlainObject(value)) fail('INVALID_AZURELIB_GEO_DOCUMENT', 'Geo document must be an object.');
  rejectAuthoringMetadata(value, 'geometry');
  const formatVersion = value.format_version;
  if (!GEO_FORMAT_VERSIONS.has(formatVersion)) {
    fail('UNSUPPORTED_AZURELIB_GEO_FORMAT', `format_version ${JSON.stringify(formatVersion)} is not supported by AzureLib 3.1.11.`);
  }
  const geometries = value['minecraft:geometry'];
  if (!Array.isArray(geometries) || geometries.length === 0) {
    fail('INVALID_AZURELIB_GEO_DOCUMENT', 'minecraft:geometry must contain at least one geometry entry.');
  }

  let locatorCount = 0;
  geometries.forEach((geometry, geometryIndex) => {
    if (!isPlainObject(geometry)) fail('INVALID_AZURELIB_GEO_DOCUMENT', `minecraft:geometry[${geometryIndex}] must be an object.`);
    const bones = geometry.bones === undefined ? [] : geometry.bones;
    if (!Array.isArray(bones)) fail('INVALID_AZURELIB_GEO_DOCUMENT', `minecraft:geometry[${geometryIndex}].bones must be an array.`);
    bones.forEach((bone, boneIndex) => {
      if (!isPlainObject(bone)) fail('INVALID_AZURELIB_GEO_DOCUMENT', `bone ${boneIndex} must be an object.`);
      if (bone.locators === undefined) return;
      if (!isPlainObject(bone.locators)) fail('INVALID_AZURELIB_LOCATOR', `bone ${boneIndex}.locators must be an object.`);
      for (const [locatorName, locatorValue] of Object.entries(bone.locators)) {
        nonEmptyString(locatorName, `bone ${boneIndex} locator name`, 'INVALID_AZURELIB_LOCATOR');
        validateLocatorValue(locatorValue, `bone ${boneIndex}.locators.${locatorName}`);
        locatorCount++;
      }
    });
  });

  return Object.freeze({ok: true, formatVersion, geometryCount: geometries.length, locatorCount});
}

function validateMathScalar(value, field) {
  if (Number.isFinite(value)) return;
  if (typeof value === 'string' && value.trim()) return;
  fail('INVALID_AZURELIB_KEYFRAME', `${field} must be a finite number or Molang string.`);
}

function validateVectorExpression(value, field) {
  if (!Array.isArray(value) || value.length !== 3) {
    fail('INVALID_AZURELIB_KEYFRAME', `${field} must contain exactly three values.`);
  }
  value.forEach((entry, index) => validateMathScalar(entry, `${field}[${index}]`));
}

function validateBedrockVector(value, field) {
  if (Array.isArray(value)) {
    validateVectorExpression(value, field);
    return;
  }
  if (isPlainObject(value) && Array.isArray(value.vector)) {
    rejectUnknownFields(value, new Set(['vector']), fail, 'INVALID_AZURELIB_KEYFRAME', field);
    validateVectorExpression(value.vector, `${field}.vector`);
    return;
  }
  fail('INVALID_AZURELIB_KEYFRAME', `${field} must be a vector or an object containing vector.`);
}

function validateKeyframeLeaf(value, field) {
  if (Number.isFinite(value) || (typeof value === 'string' && value.trim())) return;
  if (Array.isArray(value)) {
    validateVectorExpression(value, field);
    return;
  }
  if (!isPlainObject(value)) fail('INVALID_AZURELIB_KEYFRAME', `${field} has an unsupported keyframe shape.`);

  const hasAzureShape = value.vector !== undefined || value.easing !== undefined || value.easingArgs !== undefined;
  const hasBedrockShape = value.pre !== undefined || value.post !== undefined || value.lerp_mode !== undefined;
  if (hasAzureShape && hasBedrockShape) {
    fail('INVALID_AZURELIB_KEYFRAME', `${field} must not mix AzureLib vector/easing fields with Bedrock pre/post/lerp_mode fields in one keyframe.`);
  }

  if (hasAzureShape) {
    rejectUnknownFields(value, AZURE_KEYFRAME_FIELDS, fail, 'INVALID_AZURELIB_KEYFRAME', field);
    if (value.vector === undefined) fail('INVALID_AZURELIB_KEYFRAME', `${field}.vector is required for AzureLib easing keyframes.`);
    validateVectorExpression(value.vector, `${field}.vector`);
    if (value.easing !== undefined) nonEmptyString(value.easing, `${field}.easing`, 'INVALID_AZURELIB_KEYFRAME');
    if (value.easingArgs !== undefined && (!Array.isArray(value.easingArgs) || !value.easingArgs.every(Number.isFinite))) {
      fail('INVALID_AZURELIB_KEYFRAME', `${field}.easingArgs must contain finite numbers.`);
    }
    return;
  }

  if (hasBedrockShape) {
    rejectUnknownFields(value, BEDROCK_KEYFRAME_FIELDS, fail, 'INVALID_AZURELIB_KEYFRAME', field);
    if (value.pre !== undefined) validateBedrockVector(value.pre, `${field}.pre`);
    if (value.post !== undefined) validateBedrockVector(value.post, `${field}.post`);
    if (value.pre === undefined && value.post === undefined) {
      fail('INVALID_AZURELIB_KEYFRAME', `${field} must define pre or post when using Bedrock keyframe fields.`);
    }
    if (value.lerp_mode !== undefined && !BEDROCK_LERP_MODES.has(value.lerp_mode)) {
      fail('UNSUPPORTED_AZURELIB_LERP_MODE', `${field}.lerp_mode ${JSON.stringify(value.lerp_mode)} is not audited for AzureLib 3.1.11.`);
    }
    return;
  }

  fail('INVALID_AZURELIB_KEYFRAME', `${field} has an unsupported keyframe object.`);
}

function validateChannel(value, field) {
  if (value === undefined) return;
  if (Number.isFinite(value) || (typeof value === 'string' && value.trim()) || Array.isArray(value)) {
    validateKeyframeLeaf(value, field);
    return;
  }
  if (!isPlainObject(value)) fail('INVALID_AZURELIB_KEYFRAME', `${field} must be a keyframe value or timestamp map.`);
  if (
    value.vector !== undefined || value.easing !== undefined || value.easingArgs !== undefined
    || value.pre !== undefined || value.post !== undefined || value.lerp_mode !== undefined
  ) {
    validateKeyframeLeaf(value, field);
    return;
  }
  for (const [timestamp, frame] of Object.entries(value)) {
    const time = Number(timestamp);
    if (!Number.isFinite(time) || time < 0) fail('INVALID_AZURELIB_TIMESTAMP', `${field}.${timestamp} is not a valid non-negative timestamp.`);
    validateKeyframeLeaf(frame, `${field}.${timestamp}`);
  }
}

function validateEffectTimestamp(timestamp, field) {
  const time = Number(timestamp);
  if (!Number.isFinite(time) || time < 0) fail('INVALID_AZURELIB_TIMESTAMP', `${field}.${timestamp} is not a valid non-negative timestamp.`);
}

function validateIncludes(value) {
  if (value === undefined) return 0;
  if (!Array.isArray(value)) fail('INVALID_AZURELIB_INCLUDES', 'includes must be an array.');
  const claimedAnimations = new Set();
  value.forEach((entry, index) => {
    if (!isPlainObject(entry)) fail('INVALID_AZURELIB_INCLUDES', `includes[${index}] must be an object.`);
    rejectUnknownFields(entry, new Set(['file_id', 'animations']), fail, 'INVALID_AZURELIB_INCLUDES', `includes[${index}]`);
    const fileId = nonEmptyString(entry.file_id, `includes[${index}].file_id`, 'INVALID_AZURELIB_INCLUDES');
    if (!RESOURCE_LOCATION.test(fileId)) fail('INVALID_AZURELIB_INCLUDES', `includes[${index}].file_id must be a Minecraft resource location.`);
    if (!Array.isArray(entry.animations) || entry.animations.length === 0) {
      fail('INVALID_AZURELIB_INCLUDES', `includes[${index}].animations must be a non-empty string array.`);
    }
    for (const animationName of entry.animations) {
      const name = nonEmptyString(animationName, `includes[${index}] animation name`, 'INVALID_AZURELIB_INCLUDES');
      if (claimedAnimations.has(name)) {
        fail('DUPLICATE_AZURELIB_INCLUDE_ANIMATION', `Animation ${JSON.stringify(name)} is claimed by more than one include entry.`);
      }
      claimedAnimations.add(name);
    }
  });
  return value.length;
}

function validateAzureLibAnimationDocument(value) {
  if (!isPlainObject(value)) fail('INVALID_AZURELIB_ANIMATION_DOCUMENT', 'Animation document must be an object.');
  rejectAuthoringMetadata(value, 'animation');
  if (value.format_version !== AZURELIB_AUTHORITY.animationFormatVersion) {
    fail(
      'UNSUPPORTED_AZURELIB_ANIMATION_FORMAT',
      `format_version ${JSON.stringify(value.format_version)} does not match AzureLib Animator ${AZURELIB_AUTHORITY.blockbenchPluginVersion} output ${AZURELIB_AUTHORITY.animationFormatVersion}.`,
    );
  }
  const includeCount = validateIncludes(value.includes);
  if (!isPlainObject(value.animations) || Object.keys(value.animations).length === 0) {
    fail('INVALID_AZURELIB_ANIMATION_DOCUMENT', 'animations must be a non-empty object.');
  }

  const effectCounts = {sound: 0, particle: 0, timeline: 0};
  for (const [animationName, animation] of Object.entries(value.animations)) {
    nonEmptyString(animationName, 'animation name');
    if (!isPlainObject(animation)) fail('INVALID_AZURELIB_ANIMATION_DOCUMENT', `Animation ${animationName} must be an object.`);
    if (animation.animation_length !== undefined) finiteNonNegative(animation.animation_length, `${animationName}.animation_length`);
    if (animation.loop !== undefined) {
      const loop = typeof animation.loop === 'boolean' ? String(animation.loop) : animation.loop;
      if (typeof loop !== 'string' || !LOOP_VALUES.has(loop)) {
        fail('UNSUPPORTED_AZURELIB_LOOP', `${animationName}.loop ${JSON.stringify(animation.loop)} is not a built-in audited AzureLib 3.1.11 loop mode.`);
      }
    }

    const bones = animation.bones === undefined ? {} : animation.bones;
    if (!isPlainObject(bones)) fail('INVALID_AZURELIB_ANIMATION_DOCUMENT', `${animationName}.bones must be an object.`);
    for (const [boneName, channels] of Object.entries(bones)) {
      nonEmptyString(boneName, `${animationName} bone name`);
      if (!isPlainObject(channels)) fail('INVALID_AZURELIB_ANIMATION_DOCUMENT', `${animationName}.bones.${boneName} must be an object.`);
      validateChannel(channels.position, `${animationName}.bones.${boneName}.position`);
      validateChannel(channels.rotation, `${animationName}.bones.${boneName}.rotation`);
      validateChannel(channels.scale, `${animationName}.bones.${boneName}.scale`);
    }

    const sounds = animation.sound_effects === undefined ? {} : animation.sound_effects;
    if (!isPlainObject(sounds)) fail('INVALID_AZURELIB_EFFECTS', `${animationName}.sound_effects must be an object.`);
    for (const [timestamp, sound] of Object.entries(sounds)) {
      validateEffectTimestamp(timestamp, `${animationName}.sound_effects`);
      if (!isPlainObject(sound)) fail('INVALID_AZURELIB_EFFECTS', `${animationName}.sound_effects.${timestamp} must be an object.`);
      nonEmptyString(sound.effect, `${animationName}.sound_effects.${timestamp}.effect`, 'INVALID_AZURELIB_EFFECTS');
      effectCounts.sound++;
    }

    const particles = animation.particle_effects === undefined ? {} : animation.particle_effects;
    if (!isPlainObject(particles)) fail('INVALID_AZURELIB_EFFECTS', `${animationName}.particle_effects must be an object.`);
    for (const [timestamp, particle] of Object.entries(particles)) {
      validateEffectTimestamp(timestamp, `${animationName}.particle_effects`);
      if (!isPlainObject(particle)) fail('INVALID_AZURELIB_EFFECTS', `${animationName}.particle_effects.${timestamp} must be an object.`);
      nonEmptyString(particle.effect, `${animationName}.particle_effects.${timestamp}.effect`, 'INVALID_AZURELIB_EFFECTS');
      for (const field of ['locator', 'pre_effect_script']) {
        if (particle[field] !== undefined && typeof particle[field] !== 'string') {
          fail('INVALID_AZURELIB_EFFECTS', `${animationName}.particle_effects.${timestamp}.${field} must be a string.`);
        }
      }
      effectCounts.particle++;
    }

    const timeline = animation.timeline === undefined ? {} : animation.timeline;
    if (!isPlainObject(timeline)) fail('INVALID_AZURELIB_EFFECTS', `${animationName}.timeline must be an object.`);
    for (const [timestamp, instruction] of Object.entries(timeline)) {
      validateEffectTimestamp(timestamp, `${animationName}.timeline`);
      const validInstruction = typeof instruction === 'string'
        ? instruction.length > 0
        : Array.isArray(instruction) && instruction.length > 0 && instruction.every((entry) => typeof entry === 'string' && entry.length > 0);
      if (!validInstruction) fail('INVALID_AZURELIB_EFFECTS', `${animationName}.timeline.${timestamp} must be a non-empty string or non-empty string array.`);
      effectCounts.timeline++;
    }
  }

  return Object.freeze({
    ok: true,
    formatVersion: value.format_version,
    animationCount: Object.keys(value.animations).length,
    includeCount,
    effectCounts: Object.freeze(effectCounts),
  });
}

function effectTimeKey(value) {
  return String(finiteNonNegative(value, 'effect marker time'));
}

function serializeAzureLibEffectMarker(marker, providerData) {
  if (!isPlainObject(marker) || !isPlainObject(providerData)) {
    fail('INVALID_AZURELIB_EFFECT_MARKER', 'Effect marker and provider data must be objects.');
  }
  const time = effectTimeKey(marker.time);
  switch (marker.markerType) {
    case 'sound':
      return Object.freeze({
        channel: 'sound_effects',
        time,
        value: Object.freeze({effect: nonEmptyString(providerData.effect, 'sound effect', 'INVALID_AZURELIB_EFFECT_MARKER')}),
      });
    case 'particle': {
      const value = {
        effect: nonEmptyString(providerData.effect, 'particle effect', 'INVALID_AZURELIB_EFFECT_MARKER'),
      };
      if (providerData.locator !== undefined) value.locator = nonEmptyString(providerData.locator, 'particle locator', 'INVALID_AZURELIB_EFFECT_MARKER');
      if (providerData.preEffectScript !== undefined) {
        value.pre_effect_script = nonEmptyString(providerData.preEffectScript, 'particle preEffectScript', 'INVALID_AZURELIB_EFFECT_MARKER');
      }
      return Object.freeze({channel: 'particle_effects', time, value: Object.freeze(value)});
    }
    case 'timeline': {
      const instruction = providerData.instruction;
      const valid = typeof instruction === 'string'
        ? instruction.length > 0
        : Array.isArray(instruction) && instruction.length > 0 && instruction.every((entry) => typeof entry === 'string' && entry.length > 0);
      if (!valid) fail('INVALID_AZURELIB_EFFECT_MARKER', 'timeline instruction must be a non-empty string or non-empty string array.');
      return Object.freeze({channel: 'timeline', time, value: Array.isArray(instruction) ? Object.freeze([...instruction]) : instruction});
    }
    default:
      fail('UNSUPPORTED_AZURELIB_EFFECT_MARKER', `Marker type ${JSON.stringify(marker.markerType)} has no audited AzureLib mapping.`);
  }
}

function normalizedSourceAuthorityPath(value) {
  const output = nonEmptyString(value, 'sourcePath', 'INVALID_AZURELIB_SOURCE_PATH').replace(/\\/g, '/').replace(/\/$/, '');
  if (output.split('/').includes('..')) fail('INVALID_AZURELIB_SOURCE_PATH', 'sourcePath must not contain traversal segments.');
  return output;
}

function normalizedRelativePath(value, field) {
  const output = nonEmptyString(value, field, 'INVALID_AZURELIB_PATH').replace(/\\/g, '/').replace(/\/$/, '');
  if (output.startsWith('/') || /^[A-Za-z]:/.test(output) || output.split('/').includes('..')) {
    fail('INVALID_AZURELIB_PATH', `${field} must be a safe relative path.`);
  }
  return output;
}

function createAzureLibExportPlan(input) {
  if (!isPlainObject(input)) fail('INVALID_AZURELIB_EXPORT_PLAN', 'Export plan request must be an object.');
  if (!AZURELIB_PROFILE_IDS.has(input.profileId)) fail('INVALID_AZURELIB_PROFILE', `Profile ${JSON.stringify(input.profileId)} is not an AzureLib profile.`);
  const sourcePath = normalizedSourceAuthorityPath(input.sourcePath);
  if (!sourcePath.toLowerCase().endsWith('.bbmodel')) fail('AZURELIB_SOURCE_MUST_BE_BBMODEL', 'Source authority must remain a .bbmodel file.');
  const outputDirectory = normalizedRelativePath(input.outputDirectory, 'outputDirectory');
  const resourceName = nonEmptyString(input.resourceName, 'resourceName', 'INVALID_AZURELIB_RESOURCE_NAME');
  if (!/^[a-z0-9_.-]+$/.test(resourceName)) fail('INVALID_AZURELIB_RESOURCE_NAME', 'resourceName must be filesystem/resource-safe lowercase text.');
  if (input.includeAnimations !== undefined && typeof input.includeAnimations !== 'boolean') {
    fail('INVALID_AZURELIB_EXPORT_PLAN', 'includeAnimations must be boolean.');
  }

  const artifacts = [{kind: 'model', path: `${outputDirectory}/${resourceName}.geo.json`}];
  if (input.includeAnimations === true) artifacts.push({kind: 'animation', path: `${outputDirectory}/${resourceName}.animation.json`});
  return Object.freeze({
    providerFamily: 'azurelib',
    profileId: input.profileId,
    sourcePath,
    preserveSource: true,
    artifacts: Object.freeze(artifacts.map((artifact) => Object.freeze(artifact))),
    runtimeEvidence: 'UNPROVEN',
  });
}

module.exports = {
  AZURELIB_AUTHORITY,
  AzureLibContractError,
  validateAzureLibGeoDocument,
  validateAzureLibAnimationDocument,
  serializeAzureLibEffectMarker,
  createAzureLibExportPlan,
};
