'use strict';

const {isPlainObject} = require('../common/contract_utils.js');

const LOCATOR_OBJECT_FIELDS = new Set(['ignore_inherited_scale', 'offset', 'rotation']);

function nonEmptyString(value, field, fail, code) {
  if (typeof value !== 'string' || value.length === 0) fail(code, `${field} must be a non-empty string.`);
  return value;
}

function finiteNonNegative(value, field, fail, code) {
  if (!Number.isFinite(value) || value < 0) fail(code, `${field} must be a finite non-negative number.`);
  return value;
}

function vector3Numbers(value, field, fail, code) {
  if (!Array.isArray(value) || value.length !== 3 || !value.every(Number.isFinite)) {
    fail(code, `${field} must contain exactly three finite numbers.`);
  }
  return value;
}

function validateLocatorValue(value, field, options) {
  const {fail, invalidLocatorCode, providerLabel} = options;
  if (Array.isArray(value)) {
    vector3Numbers(value, field, fail, invalidLocatorCode);
    return;
  }
  if (!isPlainObject(value)) fail(invalidLocatorCode, `${field} must be a vector or locator object.`);
  for (const key of Object.keys(value)) {
    if (!LOCATOR_OBJECT_FIELDS.has(key)) fail(invalidLocatorCode, `${field}.${key} is not supported by ${providerLabel}.`);
  }
  if (value.ignore_inherited_scale !== undefined && typeof value.ignore_inherited_scale !== 'boolean') {
    fail(invalidLocatorCode, `${field}.ignore_inherited_scale must be boolean.`);
  }
  if (value.offset !== undefined) vector3Numbers(value.offset, `${field}.offset`, fail, invalidLocatorCode);
  if (value.rotation !== undefined) vector3Numbers(value.rotation, `${field}.rotation`, fail, invalidLocatorCode);
  if (value.offset === undefined && value.rotation === undefined) {
    fail(invalidLocatorCode, `${field} must define offset or rotation.`);
  }
}

function validateGeoDocument(value, options) {
  const {
    fail,
    invalidDocumentCode,
    unsupportedFormatCode,
    invalidLocatorCode,
    invalidStringCode,
    providerLabel,
    formatVersions,
    rejectRootMetadata,
  } = options;
  if (!isPlainObject(value)) fail(invalidDocumentCode, 'Geo document must be an object.');
  if (rejectRootMetadata) rejectRootMetadata(value, 'geometry');
  const formatVersion = value.format_version;
  if (!formatVersions.has(formatVersion)) {
    fail(unsupportedFormatCode, `format_version ${JSON.stringify(formatVersion)} is not supported by ${providerLabel}.`);
  }
  const geometries = value['minecraft:geometry'];
  if (!Array.isArray(geometries) || geometries.length === 0) {
    fail(invalidDocumentCode, 'minecraft:geometry must contain at least one geometry entry.');
  }

  let locatorCount = 0;
  geometries.forEach((geometry, geometryIndex) => {
    if (!isPlainObject(geometry)) fail(invalidDocumentCode, `minecraft:geometry[${geometryIndex}] must be an object.`);
    const bones = geometry.bones === undefined ? [] : geometry.bones;
    if (!Array.isArray(bones)) fail(invalidDocumentCode, `minecraft:geometry[${geometryIndex}].bones must be an array.`);
    bones.forEach((bone, boneIndex) => {
      if (!isPlainObject(bone)) fail(invalidDocumentCode, `bone ${boneIndex} must be an object.`);
      if (bone.locators === undefined) return;
      if (!isPlainObject(bone.locators)) fail(invalidLocatorCode, `bone ${boneIndex}.locators must be an object.`);
      for (const [locatorName, locatorValue] of Object.entries(bone.locators)) {
        nonEmptyString(locatorName, `bone ${boneIndex} locator name`, fail, invalidStringCode);
        validateLocatorValue(locatorValue, `bone ${boneIndex}.locators.${locatorName}`, {
          fail,
          invalidLocatorCode,
          providerLabel,
        });
        locatorCount++;
      }
    });
  });

  return Object.freeze({ok: true, formatVersion, geometryCount: geometries.length, locatorCount});
}

function validateMathScalar(value, field, fail, invalidKeyframeCode) {
  if (Number.isFinite(value)) return;
  if (typeof value === 'string' && value.length > 0) return;
  fail(invalidKeyframeCode, `${field} must be a finite number or Molang string.`);
}

function validateVectorExpression(value, field, fail, invalidKeyframeCode) {
  if (!Array.isArray(value) || value.length !== 3) {
    fail(invalidKeyframeCode, `${field} must contain exactly three values.`);
  }
  value.forEach((entry, index) => validateMathScalar(entry, `${field}[${index}]`, fail, invalidKeyframeCode));
}

function validateTimestamp(timestamp, field, fail, invalidTimestampCode) {
  const time = Number(timestamp);
  if (!Number.isFinite(time) || time < 0) {
    fail(invalidTimestampCode, `${field}.${timestamp} is not a valid non-negative timestamp.`);
  }
}

function validateChannel(value, field, options) {
  const {fail, invalidKeyframeCode, invalidTimestampCode, validateKeyframeLeaf} = options;
  if (value === undefined) return;
  if (Number.isFinite(value) || (typeof value === 'string' && value.length > 0) || Array.isArray(value)) {
    validateKeyframeLeaf(value, field);
    return;
  }
  if (!isPlainObject(value)) fail(invalidKeyframeCode, `${field} must be a keyframe value or timestamp map.`);
  if (
    value.vector !== undefined || value.easing !== undefined || value.easingArgs !== undefined
    || value.pre !== undefined || value.post !== undefined || value.lerp_mode !== undefined
  ) {
    validateKeyframeLeaf(value, field);
    return;
  }
  for (const [timestamp, frame] of Object.entries(value)) {
    validateTimestamp(timestamp, field, fail, invalidTimestampCode);
    validateKeyframeLeaf(frame, `${field}.${timestamp}`);
  }
}

function validateEffectChannels(animationName, animation, options) {
  const {
    fail,
    invalidEffectsCode,
    invalidTimestampCode,
    invalidStringCode,
    requireParticleEffect = false,
    requireNonEmptyTimeline = false,
  } = options;
  const counts = {sound: 0, particle: 0, timeline: 0};

  const sounds = animation.sound_effects === undefined ? {} : animation.sound_effects;
  if (!isPlainObject(sounds)) fail(invalidEffectsCode, `${animationName}.sound_effects must be an object.`);
  for (const [timestamp, sound] of Object.entries(sounds)) {
    validateTimestamp(timestamp, `${animationName}.sound_effects`, fail, invalidTimestampCode);
    if (!isPlainObject(sound)) fail(invalidEffectsCode, `${animationName}.sound_effects.${timestamp} must be an object.`);
    nonEmptyString(sound.effect, `${animationName}.sound_effects.${timestamp}.effect`, fail, invalidStringCode || invalidEffectsCode);
    counts.sound++;
  }

  const particles = animation.particle_effects === undefined ? {} : animation.particle_effects;
  if (!isPlainObject(particles)) fail(invalidEffectsCode, `${animationName}.particle_effects must be an object.`);
  for (const [timestamp, particle] of Object.entries(particles)) {
    validateTimestamp(timestamp, `${animationName}.particle_effects`, fail, invalidTimestampCode);
    if (!isPlainObject(particle)) fail(invalidEffectsCode, `${animationName}.particle_effects.${timestamp} must be an object.`);
    if (requireParticleEffect) {
      nonEmptyString(particle.effect, `${animationName}.particle_effects.${timestamp}.effect`, fail, invalidEffectsCode);
    }
    for (const field of ['effect', 'locator', 'pre_effect_script']) {
      if (particle[field] !== undefined && typeof particle[field] !== 'string') {
        fail(invalidEffectsCode, `${animationName}.particle_effects.${timestamp}.${field} must be a string.`);
      }
    }
    counts.particle++;
  }

  const timeline = animation.timeline === undefined ? {} : animation.timeline;
  if (!isPlainObject(timeline)) fail(invalidEffectsCode, `${animationName}.timeline must be an object.`);
  for (const [timestamp, instruction] of Object.entries(timeline)) {
    validateTimestamp(timestamp, `${animationName}.timeline`, fail, invalidTimestampCode);
    const validString = typeof instruction === 'string' && (!requireNonEmptyTimeline || instruction.length > 0);
    const validArray = Array.isArray(instruction)
      && (!requireNonEmptyTimeline || instruction.length > 0)
      && instruction.every((entry) => typeof entry === 'string' && (!requireNonEmptyTimeline || entry.length > 0));
    if (!validString && !validArray) {
      fail(invalidEffectsCode, `${animationName}.timeline.${timestamp} must be a string or string array.`);
    }
    counts.timeline++;
  }

  return counts;
}

function validateAnimationDocument(value, options) {
  const {
    fail,
    invalidDocumentCode,
    invalidStringCode,
    invalidNumberCode,
    invalidLoopCode,
    invalidKeyframeCode,
    invalidTimestampCode,
    invalidEffectsCode,
    loopValues,
    validateKeyframeLeaf,
    expectedFormatVersion,
    unsupportedFormatCode,
    rejectRootMetadata,
    validateIncludes,
    requireParticleEffect,
    requireNonEmptyTimeline,
  } = options;
  if (!isPlainObject(value)) fail(invalidDocumentCode, 'Animation document must be an object.');
  if (rejectRootMetadata) rejectRootMetadata(value, 'animation');
  if (expectedFormatVersion !== undefined && value.format_version !== expectedFormatVersion) {
    fail(unsupportedFormatCode, `format_version ${JSON.stringify(value.format_version)} does not match audited output ${expectedFormatVersion}.`);
  }
  const includeCount = validateIncludes ? validateIncludes(value.includes) : 0;
  if (!isPlainObject(value.animations) || Object.keys(value.animations).length === 0) {
    fail(invalidDocumentCode, 'animations must be a non-empty object.');
  }

  const effectCounts = {sound: 0, particle: 0, timeline: 0};
  for (const [animationName, animation] of Object.entries(value.animations)) {
    nonEmptyString(animationName, 'animation name', fail, invalidStringCode);
    if (!isPlainObject(animation)) fail(invalidDocumentCode, `Animation ${animationName} must be an object.`);
    if (animation.animation_length !== undefined) {
      finiteNonNegative(animation.animation_length, `${animationName}.animation_length`, fail, invalidNumberCode);
    }
    if (animation.loop !== undefined) {
      const loop = typeof animation.loop === 'boolean' ? String(animation.loop) : animation.loop;
      if (typeof loop !== 'string' || !loopValues.has(loop)) {
        fail(invalidLoopCode, `${animationName}.loop ${JSON.stringify(animation.loop)} is not an audited loop mode.`);
      }
    }
    const bones = animation.bones === undefined ? {} : animation.bones;
    if (!isPlainObject(bones)) fail(invalidDocumentCode, `${animationName}.bones must be an object.`);
    for (const [boneName, channels] of Object.entries(bones)) {
      nonEmptyString(boneName, `${animationName} bone name`, fail, invalidStringCode);
      if (!isPlainObject(channels)) fail(invalidDocumentCode, `${animationName}.bones.${boneName} must be an object.`);
      const channelOptions = {fail, invalidKeyframeCode, invalidTimestampCode, validateKeyframeLeaf};
      validateChannel(channels.position, `${animationName}.bones.${boneName}.position`, channelOptions);
      validateChannel(channels.rotation, `${animationName}.bones.${boneName}.rotation`, channelOptions);
      validateChannel(channels.scale, `${animationName}.bones.${boneName}.scale`, channelOptions);
    }
    const counts = validateEffectChannels(animationName, animation, {
      fail,
      invalidEffectsCode,
      invalidTimestampCode,
      invalidStringCode,
      requireParticleEffect,
      requireNonEmptyTimeline,
    });
    effectCounts.sound += counts.sound;
    effectCounts.particle += counts.particle;
    effectCounts.timeline += counts.timeline;
  }

  const result = {
    ok: true,
    animationCount: Object.keys(value.animations).length,
    effectCounts: Object.freeze(effectCounts),
  };
  if (expectedFormatVersion !== undefined) result.formatVersion = value.format_version;
  if (validateIncludes) result.includeCount = includeCount;
  return Object.freeze(result);
}

function serializeEffectMarker(marker, providerData, options) {
  const {
    fail,
    invalidMarkerCode,
    unsupportedMarkerCode,
    invalidNumberCode,
    invalidStringCode,
    providerLabel,
    requireParticleEffect = false,
    requireNonEmptyTimeline = false,
  } = options;
  if (!isPlainObject(marker) || !isPlainObject(providerData)) {
    fail(invalidMarkerCode, 'Effect marker and provider data must be objects.');
  }
  const time = String(finiteNonNegative(marker.time, 'effect marker time', fail, invalidNumberCode));
  switch (marker.markerType) {
    case 'sound':
      return Object.freeze({
        channel: 'sound_effects',
        time,
        value: Object.freeze({effect: nonEmptyString(providerData.effect, 'sound effect', fail, invalidStringCode)}),
      });
    case 'particle': {
      const value = {};
      if (requireParticleEffect) {
        value.effect = nonEmptyString(providerData.effect, 'particle effect', fail, invalidStringCode);
      }
      for (const [sourceField, targetField] of [['effect', 'effect'], ['locator', 'locator'], ['preEffectScript', 'pre_effect_script']]) {
        if (providerData[sourceField] !== undefined && value[targetField] === undefined) {
          value[targetField] = nonEmptyString(providerData[sourceField], `particle ${sourceField}`, fail, invalidStringCode);
        }
      }
      return Object.freeze({channel: 'particle_effects', time, value: Object.freeze(value)});
    }
    case 'timeline': {
      const instruction = providerData.instruction;
      const validString = typeof instruction === 'string' && (!requireNonEmptyTimeline || instruction.length > 0);
      const validArray = Array.isArray(instruction)
        && (!requireNonEmptyTimeline || instruction.length > 0)
        && instruction.every((entry) => typeof entry === 'string' && (!requireNonEmptyTimeline || entry.length > 0));
      if (!validString && !validArray) fail(invalidMarkerCode, 'timeline instruction must be a string or string array.');
      return Object.freeze({
        channel: 'timeline',
        time,
        value: Array.isArray(instruction) ? Object.freeze([...instruction]) : instruction,
      });
    }
    default:
      fail(unsupportedMarkerCode, `Marker type ${JSON.stringify(marker.markerType)} has no audited ${providerLabel} mapping.`);
  }
}

function normalizeSourcePath(value, options) {
  const {fail, invalidSourcePathCode, invalidStringCode} = options;
  const output = nonEmptyString(value, 'sourcePath', fail, invalidStringCode).replace(/\\/g, '/').replace(/\/$/, '');
  if (output.split('/').includes('..')) fail(invalidSourcePathCode, 'sourcePath must not contain traversal segments.');
  return output;
}

function normalizeRelativePath(value, field, options) {
  const {fail, invalidPathCode, invalidStringCode} = options;
  const output = nonEmptyString(value, field, fail, invalidStringCode).replace(/\\/g, '/').replace(/\/$/, '');
  if (output.startsWith('/') || /^[A-Za-z]:/.test(output) || output.split('/').includes('..')) {
    fail(invalidPathCode, `${field} must be a safe relative path.`);
  }
  return output;
}

function createExportPlan(input, options) {
  const {
    fail,
    profileIds,
    providerFamily,
    providerLabel,
    invalidPlanCode,
    invalidProfileCode,
    invalidSourcePathCode,
    sourceMustBeBbmodelCode,
    invalidPathCode,
    invalidResourceNameCode,
    invalidStringCode,
  } = options;
  if (!isPlainObject(input)) fail(invalidPlanCode, 'Export plan request must be an object.');
  if (!profileIds.has(input.profileId)) fail(invalidProfileCode, `Profile ${JSON.stringify(input.profileId)} is not a ${providerLabel} profile.`);
  const sourcePath = normalizeSourcePath(input.sourcePath, {fail, invalidSourcePathCode, invalidStringCode});
  if (!sourcePath.toLowerCase().endsWith('.bbmodel')) fail(sourceMustBeBbmodelCode, 'Source authority must remain a .bbmodel file.');
  const outputDirectory = normalizeRelativePath(input.outputDirectory, 'outputDirectory', {fail, invalidPathCode, invalidStringCode});
  const resourceName = nonEmptyString(input.resourceName, 'resourceName', fail, invalidResourceNameCode);
  if (!/^[a-z0-9_.-]+$/.test(resourceName)) fail(invalidResourceNameCode, 'resourceName must be filesystem/resource-safe lowercase text.');
  if (input.includeAnimations !== undefined && typeof input.includeAnimations !== 'boolean') {
    fail(invalidPlanCode, 'includeAnimations must be boolean.');
  }
  const artifacts = [{kind: 'model', path: `${outputDirectory}/${resourceName}.geo.json`}];
  if (input.includeAnimations === true) artifacts.push({kind: 'animation', path: `${outputDirectory}/${resourceName}.animation.json`});
  return Object.freeze({
    providerFamily,
    profileId: input.profileId,
    sourcePath,
    preserveSource: true,
    artifacts: Object.freeze(artifacts.map((artifact) => Object.freeze(artifact))),
    runtimeEvidence: 'UNPROVEN',
  });
}

module.exports = {
  nonEmptyString,
  finiteNonNegative,
  vector3Numbers,
  validateVectorExpression,
  validateGeoDocument,
  validateAnimationDocument,
  serializeEffectMarker,
  createExportPlan,
};
