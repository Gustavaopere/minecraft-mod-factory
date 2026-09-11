'use strict';

const {isPlainObject} = require('../common/contract_utils.js');

const NEOFORGE_NATIVE_ANIMATION_AUTHORITY = Object.freeze({
  providerFamily: 'neoforge_native_animation',
  minecraftVersion: '1.21.1',
  neoforgeVersion: '21.1.248',
  runtimeSource: 'neoforged/NeoForge',
  runtimeRef: 'd8d64b44bb46323d44520fe27feda0a9a08c1c82',
  animationRoot: 'neoforge/animations/entity',
  blockbenchPluginId: 'animation_to_json',
  blockbenchPluginVersion: '1.0.1',
  blockbenchPluginSource: 'JannisX11/blockbench-plugins',
  blockbenchPluginRef: '91ba2b80c895960fe93de87fd0c30f9b840f28f2',
});

const ROOT_FIELDS = new Set(['length', 'loop', 'animations']);
const CHANNEL_FIELDS = new Set(['bone', 'target', 'keyframes']);
const KEYFRAME_FIELDS = new Set(['timestamp', 'target', 'interpolation']);
const SERIALIZER_FIELDS = new Set(['length', 'loop', 'channels', 'effectMarkers']);
const SERIALIZER_CHANNEL_FIELDS = new Set(['bone', 'channel', 'keyframes']);
const SERIALIZER_KEYFRAME_FIELDS = new Set(['time', 'value', 'easing']);
const TARGETS = new Set(['minecraft:position', 'minecraft:rotation', 'minecraft:scale']);
const INTERPOLATIONS = new Set(['minecraft:linear', 'minecraft:catmullrom']);

class NeoForgeNativeAnimationContractError extends Error {
  constructor(code, message) {
    super(`${code}: ${message}`);
    this.name = 'NeoForgeNativeAnimationContractError';
    this.code = code;
  }
}

function fail(code, message) {
  throw new NeoForgeNativeAnimationContractError(code, message);
}

function rejectUnknownFields(value, allowed, field) {
  for (const key of Object.keys(value)) {
    if (!allowed.has(key)) {
      fail('UNPROVEN_NEOFORGE_NATIVE_ANIMATION_FIELD', `${field}.${key} is not part of the audited NeoForge 21.1.248 animation contract.`);
    }
  }
}

function finiteNumber(value, field) {
  if (!Number.isFinite(value)) fail('INVALID_NEOFORGE_NATIVE_ANIMATION_NUMBER', `${field} must be finite.`);
  return value;
}

function nonEmptyString(value, field) {
  if (typeof value !== 'string' || value.length === 0) {
    fail('INVALID_NEOFORGE_NATIVE_ANIMATION_STRING', `${field} must be a non-empty string.`);
  }
  return value;
}

function vector3(value, field) {
  if (!Array.isArray(value) || value.length !== 3 || !value.every(Number.isFinite)) {
    fail('INVALID_NEOFORGE_NATIVE_ANIMATION_VECTOR', `${field} must contain exactly three finite numbers.`);
  }
  return Object.freeze([...value]);
}

function resourceLocation(value, field) {
  const raw = nonEmptyString(value, field).toLowerCase();
  return raw.includes(':') ? raw : `minecraft:${raw}`;
}

function canonicalResourceLocation(value, field, allowed) {
  const canonical = resourceLocation(value, field);
  if (!allowed.has(canonical)) {
    fail('UNPROVEN_NEOFORGE_NATIVE_ANIMATION_TYPE', `${field} ${JSON.stringify(value)} is not a built-in type audited for NeoForge 21.1.248.`);
  }
  return canonical;
}

function serializerInterpolation(value, field) {
  const canonical = resourceLocation(value, field);
  if (!INTERPOLATIONS.has(canonical)) {
    fail('UNSUPPORTED_NEOFORGE_NATIVE_ANIMATION_INTERPOLATION', `${field} ${JSON.stringify(value)} has no audited NeoForge native representation.`);
  }
  return canonical;
}

function validateNeoForgeNativeAnimationDocument(value) {
  if (!isPlainObject(value)) {
    fail('INVALID_NEOFORGE_NATIVE_ANIMATION_DOCUMENT', 'Animation document must be an object.');
  }
  rejectUnknownFields(value, ROOT_FIELDS, 'document');

  const length = finiteNumber(value.length, 'document.length');
  if (value.loop !== undefined && typeof value.loop !== 'boolean') {
    fail('INVALID_NEOFORGE_NATIVE_ANIMATION_LOOP', 'document.loop must be boolean when present.');
  }
  if (!Array.isArray(value.animations)) {
    fail('INVALID_NEOFORGE_NATIVE_ANIMATION_DOCUMENT', 'document.animations must be an array.');
  }

  let keyframeCount = 0;
  value.animations.forEach((channel, channelIndex) => {
    const field = `document.animations[${channelIndex}]`;
    if (!isPlainObject(channel)) fail('INVALID_NEOFORGE_NATIVE_ANIMATION_CHANNEL', `${field} must be an object.`);
    rejectUnknownFields(channel, CHANNEL_FIELDS, field);
    nonEmptyString(channel.bone, `${field}.bone`);
    canonicalResourceLocation(channel.target, `${field}.target`, TARGETS);
    if (!Array.isArray(channel.keyframes)) {
      fail('INVALID_NEOFORGE_NATIVE_ANIMATION_CHANNEL', `${field}.keyframes must be an array.`);
    }
    channel.keyframes.forEach((keyframe, keyframeIndex) => {
      const keyframeField = `${field}.keyframes[${keyframeIndex}]`;
      if (!isPlainObject(keyframe)) fail('INVALID_NEOFORGE_NATIVE_ANIMATION_KEYFRAME', `${keyframeField} must be an object.`);
      rejectUnknownFields(keyframe, KEYFRAME_FIELDS, keyframeField);
      finiteNumber(keyframe.timestamp, `${keyframeField}.timestamp`);
      vector3(keyframe.target, `${keyframeField}.target`);
      canonicalResourceLocation(keyframe.interpolation, `${keyframeField}.interpolation`, INTERPOLATIONS);
      keyframeCount += 1;
    });
  });

  return Object.freeze({
    ok: true,
    length,
    loop: value.loop === true,
    channelCount: value.animations.length,
    keyframeCount,
  });
}

function serializeNeoForgeNativeAnimation(input) {
  if (!isPlainObject(input)) {
    fail('INVALID_NEOFORGE_NATIVE_ANIMATION_SERIALIZER_INPUT', 'Animation serializer input must be an object.');
  }
  rejectUnknownFields(input, SERIALIZER_FIELDS, 'animation');

  const length = finiteNumber(input.length, 'animation.length');
  if (length <= 0) fail('INVALID_NEOFORGE_NATIVE_ANIMATION_NUMBER', 'animation.length must be greater than zero.');

  let loop;
  if (input.loop === 'loop') loop = true;
  else if (input.loop === 'once') loop = false;
  else fail('UNSUPPORTED_NEOFORGE_NATIVE_ANIMATION_LOOP_MODE', `animation.loop ${JSON.stringify(input.loop)} has no audited NeoForge native representation.`);

  if (input.effectMarkers !== undefined) {
    if (!Array.isArray(input.effectMarkers)) {
      fail('UNSUPPORTED_NEOFORGE_NATIVE_ANIMATION_EFFECT_MARKERS', 'animation.effectMarkers must be absent or an empty array for NeoForge native export.');
    }
    if (input.effectMarkers.length > 0) {
      fail('UNSUPPORTED_NEOFORGE_NATIVE_ANIMATION_EFFECT_MARKERS', 'NeoForge 21.1.248 JSON entity animations have no audited effect-marker representation.');
    }
  }
  if (!Array.isArray(input.channels)) {
    fail('INVALID_NEOFORGE_NATIVE_ANIMATION_SERIALIZER_INPUT', 'animation.channels must be an array.');
  }

  const animations = input.channels.map((channel, channelIndex) => {
    const field = `animation.channels[${channelIndex}]`;
    if (!isPlainObject(channel)) fail('INVALID_NEOFORGE_NATIVE_ANIMATION_CHANNEL', `${field} must be an object.`);
    rejectUnknownFields(channel, SERIALIZER_CHANNEL_FIELDS, field);
    const bone = nonEmptyString(channel.bone, `${field}.bone`);
    const target = canonicalResourceLocation(channel.channel, `${field}.channel`, TARGETS);
    if (!Array.isArray(channel.keyframes)) {
      fail('INVALID_NEOFORGE_NATIVE_ANIMATION_CHANNEL', `${field}.keyframes must be an array.`);
    }

    const keyframes = channel.keyframes.map((keyframe, keyframeIndex) => {
      const keyframeField = `${field}.keyframes[${keyframeIndex}]`;
      if (!isPlainObject(keyframe)) fail('INVALID_NEOFORGE_NATIVE_ANIMATION_KEYFRAME', `${keyframeField} must be an object.`);
      rejectUnknownFields(keyframe, SERIALIZER_KEYFRAME_FIELDS, keyframeField);
      const timestamp = finiteNumber(keyframe.time, `${keyframeField}.time`);
      if (timestamp < 0 || timestamp > length) {
        fail('INVALID_NEOFORGE_NATIVE_ANIMATION_TIMESTAMP', `${keyframeField}.time must be between 0 and animation.length.`);
      }
      const interpolation = serializerInterpolation(keyframe.easing, `${keyframeField}.easing`);
      return Object.freeze({
        timestamp,
        target: vector3(keyframe.value, `${keyframeField}.value`),
        interpolation,
      });
    }).sort((left, right) => left.timestamp - right.timestamp);

    return Object.freeze({bone, target, keyframes: Object.freeze(keyframes)});
  });

  const document = {
    length,
    loop,
    animations: Object.freeze(animations),
  };
  validateNeoForgeNativeAnimationDocument(document);
  return Object.freeze(document);
}

module.exports = {
  NEOFORGE_NATIVE_ANIMATION_AUTHORITY,
  NeoForgeNativeAnimationContractError,
  validateNeoForgeNativeAnimationDocument,
  serializeNeoForgeNativeAnimation,
};
