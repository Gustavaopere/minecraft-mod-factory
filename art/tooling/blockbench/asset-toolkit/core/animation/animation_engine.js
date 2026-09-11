'use strict';

const contractUtils = require('../common/contract_utils.js');
const {isPlainObject, applyOperationsTransaction} = contractUtils;

const MAX_ANIMATION_OPERATIONS = 128;
const MAX_IDENTIFIER_LENGTH = 128;
const MAX_LABEL_LENGTH = 160;
const MAX_ANIMATION_LENGTH = 3600;
const MAX_KEYFRAME_TIME = 3600;
const MAX_CAPTURE_DIMENSION = 8192;

const LOOP_MODES = new Set(['once', 'loop', 'hold']);
const ANIMATION_CHANNELS = new Set(['position', 'rotation', 'scale']);
const ANIMATION_EASINGS = new Set(['linear', 'bezier', 'catmullrom', 'step']);
const EFFECT_MARKER_TYPES = new Set(['particle', 'sound', 'timeline', 'custom']);
const DESTRUCTIVE_OPERATION_TYPES = new Set([
  'animation_delete',
  'animation_delete_keyframe',
  'animation_delete_effect_marker',
]);

const BATCH_FIELDS = new Set(['expectedRevision', 'label', 'operations', 'dryRun', 'confirmationToken']);
const OPERATION_FIELDS = Object.freeze({
  animation_create: new Set(['type', 'id', 'name', 'length', 'loop']),
  animation_update_settings: new Set(['type', 'animationId', 'name', 'length', 'loop']),
  animation_delete: new Set(['type', 'animationId']),
  animation_add_keyframe: new Set(['type', 'animationId', 'keyframeId', 'targetId', 'channel', 'time', 'value', 'easing']),
  animation_update_keyframe: new Set(['type', 'animationId', 'keyframeId', 'targetId', 'channel', 'time', 'value', 'easing']),
  animation_delete_keyframe: new Set(['type', 'animationId', 'keyframeId']),
  animation_add_effect_marker: new Set(['type', 'animationId', 'markerId', 'time', 'markerType', 'label']),
  animation_delete_effect_marker: new Set(['type', 'animationId', 'markerId']),
});

class AnimationContractError extends Error {
  constructor(code, message) {
    super(`${code}: ${message}`);
    this.name = 'AnimationContractError';
    this.code = code;
  }
}

function fail(code, message) {
  throw new AnimationContractError(code, message);
}

function rejectUnknownFields(value, allowed, code, context) {
  contractUtils.rejectUnknownFields(value, allowed, fail, code, context);
}

function boundedString(value, field, {max = MAX_IDENTIFIER_LENGTH} = {}) {
  return contractUtils.boundedString(value, field, fail, {max, code: 'INVALID_ANIMATION_STRING'});
}

function optionalBoundedString(value, field, options) {
  return value === undefined ? undefined : boundedString(value, field, options);
}

function finiteNumber(value, field) {
  return contractUtils.finiteNumber(value, field, fail, 'INVALID_ANIMATION_NUMBER');
}

function positiveLength(value, field) {
  const output = finiteNumber(value, field);
  if (output <= 0 || output > MAX_ANIMATION_LENGTH) {
    fail('INVALID_ANIMATION_LENGTH', `${field} must be greater than 0 and at most ${MAX_ANIMATION_LENGTH}.`);
  }
  return output;
}

function nonNegativeTime(value, field) {
  const output = finiteNumber(value, field);
  if (output < 0 || output > MAX_KEYFRAME_TIME) {
    fail('INVALID_ANIMATION_TIME', `${field} must be between 0 and ${MAX_KEYFRAME_TIME}.`);
  }
  return output;
}

function vector3(value, field) {
  return contractUtils.vector3(value, field, fail, 'INVALID_ANIMATION_VECTOR3');
}

function loopMode(value, field) {
  const output = boundedString(value, field, {max: 16}).toLowerCase();
  if (!LOOP_MODES.has(output)) fail('INVALID_ANIMATION_LOOP_MODE', `${field} is not provider-neutral.`);
  return output;
}

function channel(value, field) {
  const output = boundedString(value, field, {max: 32}).toLowerCase();
  if (!ANIMATION_CHANNELS.has(output)) fail('INVALID_ANIMATION_CHANNEL', `${field} is not allowlisted.`);
  return output;
}

function easing(value, field) {
  const output = boundedString(value, field, {max: 32}).toLowerCase();
  if (!ANIMATION_EASINGS.has(output)) fail('INVALID_ANIMATION_EASING', `${field} is not provider-neutral.`);
  return output;
}

function markerType(value, field) {
  const output = boundedString(value, field, {max: 32}).toLowerCase();
  if (!EFFECT_MARKER_TYPES.has(output)) fail('INVALID_EFFECT_MARKER_TYPE', `${field} is not allowlisted.`);
  return output;
}

function validateOperation(value, index) {
  if (!isPlainObject(value)) fail('INVALID_ANIMATION_OPERATION', `operations[${index}] must be an object.`);
  const type = typeof value.type === 'string' ? value.type : '';
  const fields = OPERATION_FIELDS[type];
  if (!fields) {
    fail('UNSUPPORTED_ANIMATION_OPERATION', `operations[${index}] type "${type || '<missing>'}" is not allowlisted.`);
  }
  rejectUnknownFields(value, fields, 'UNKNOWN_ANIMATION_OPERATION_FIELD', `operations[${index}]`);

  let output;
  switch (type) {
    case 'animation_create':
      output = {
        type,
        id: boundedString(value.id, `operations[${index}].id`),
        name: boundedString(value.name, `operations[${index}].name`),
        length: positiveLength(value.length, `operations[${index}].length`),
        loop: loopMode(value.loop, `operations[${index}].loop`),
      };
      break;
    case 'animation_update_settings': {
      const name = optionalBoundedString(value.name, `operations[${index}].name`);
      const length = value.length === undefined ? undefined : positiveLength(value.length, `operations[${index}].length`);
      const loop = value.loop === undefined ? undefined : loopMode(value.loop, `operations[${index}].loop`);
      if (name === undefined && length === undefined && loop === undefined) {
        fail('EMPTY_ANIMATION_UPDATE', `operations[${index}] must update name, length, or loop.`);
      }
      output = {
        type,
        animationId: boundedString(value.animationId, `operations[${index}].animationId`),
        ...(name === undefined ? {} : {name}),
        ...(length === undefined ? {} : {length}),
        ...(loop === undefined ? {} : {loop}),
      };
      break;
    }
    case 'animation_delete':
      output = {
        type,
        animationId: boundedString(value.animationId, `operations[${index}].animationId`),
      };
      break;
    case 'animation_add_keyframe':
    case 'animation_update_keyframe':
      output = {
        type,
        animationId: boundedString(value.animationId, `operations[${index}].animationId`),
        keyframeId: boundedString(value.keyframeId, `operations[${index}].keyframeId`),
        targetId: boundedString(value.targetId, `operations[${index}].targetId`),
        channel: channel(value.channel, `operations[${index}].channel`),
        time: nonNegativeTime(value.time, `operations[${index}].time`),
        value: vector3(value.value, `operations[${index}].value`),
        easing: easing(value.easing, `operations[${index}].easing`),
      };
      break;
    case 'animation_delete_keyframe':
      output = {
        type,
        animationId: boundedString(value.animationId, `operations[${index}].animationId`),
        keyframeId: boundedString(value.keyframeId, `operations[${index}].keyframeId`),
      };
      break;
    case 'animation_add_effect_marker':
      output = {
        type,
        animationId: boundedString(value.animationId, `operations[${index}].animationId`),
        markerId: boundedString(value.markerId, `operations[${index}].markerId`),
        time: nonNegativeTime(value.time, `operations[${index}].time`),
        markerType: markerType(value.markerType, `operations[${index}].markerType`),
        label: boundedString(value.label, `operations[${index}].label`, {max: MAX_LABEL_LENGTH}),
      };
      break;
    case 'animation_delete_effect_marker':
      output = {
        type,
        animationId: boundedString(value.animationId, `operations[${index}].animationId`),
        markerId: boundedString(value.markerId, `operations[${index}].markerId`),
      };
      break;
    default:
      fail('UNSUPPORTED_ANIMATION_OPERATION', `operations[${index}] is not allowlisted.`);
  }
  return Object.freeze(output);
}

function validateAnimationBatch(value) {
  if (!isPlainObject(value)) fail('INVALID_ANIMATION_BATCH', 'Animation batch must be an object.');
  rejectUnknownFields(value, BATCH_FIELDS, 'UNKNOWN_ANIMATION_BATCH_FIELD', 'Animation batch');

  const expectedRevision = boundedString(value.expectedRevision, 'expectedRevision');
  if (!Array.isArray(value.operations) || value.operations.length < 1) {
    fail('EMPTY_ANIMATION_BATCH', 'operations must contain at least one animation operation.');
  }
  if (value.operations.length > MAX_ANIMATION_OPERATIONS) {
    fail('ANIMATION_BATCH_TOO_LARGE', `operations exceeds the maximum of ${MAX_ANIMATION_OPERATIONS}.`);
  }
  if (value.dryRun !== undefined && typeof value.dryRun !== 'boolean') {
    fail('INVALID_ANIMATION_DRY_RUN', 'dryRun must be boolean when provided.');
  }

  const operations = value.operations.map(validateOperation);
  const declaredAnimations = new Set();
  const declaredKeyframes = new Set();
  const declaredMarkers = new Set();
  for (const operation of operations) {
    if (operation.type === 'animation_create') {
      if (declaredAnimations.has(operation.id)) {
        fail('DUPLICATE_ANIMATION_ID', `Animation id "${operation.id}" is declared more than once.`);
      }
      declaredAnimations.add(operation.id);
    } else if (operation.type === 'animation_add_keyframe') {
      const key = `${operation.animationId}\u0000${operation.keyframeId}`;
      if (declaredKeyframes.has(key)) fail('DUPLICATE_KEYFRAME_ID', `Keyframe "${operation.keyframeId}" is declared more than once.`);
      declaredKeyframes.add(key);
    } else if (operation.type === 'animation_add_effect_marker') {
      const key = `${operation.animationId}\u0000${operation.markerId}`;
      if (declaredMarkers.has(key)) fail('DUPLICATE_EFFECT_MARKER_ID', `Effect marker "${operation.markerId}" is declared more than once.`);
      declaredMarkers.add(key);
    }
  }

  return Object.freeze({
    expectedRevision,
    label: value.label === undefined
      ? 'Minecraft Mod Factory Asset Toolkit Generic Animation Batch'
      : boundedString(value.label, 'label', {max: MAX_LABEL_LENGTH}),
    operations: Object.freeze(operations),
    dryRun: value.dryRun === true,
    confirmationToken: value.confirmationToken === undefined
      ? undefined
      : boundedString(value.confirmationToken, 'confirmationToken', {max: 256}),
  });
}

function validateMutationAdapter(adapter) {
  contractUtils.validateAdapterMethods(
    adapter,
    ['getRevision', 'preflight', 'beginTransaction', 'applyOperation', 'finishTransaction', 'cancelTransaction'],
    fail,
    'INVALID_ANIMATION_ADAPTER',
    'Animation adapter',
  );
}

function destructiveDiff(operations) {
  return Object.freeze(operations.filter((operation) => DESTRUCTIVE_OPERATION_TYPES.has(operation.type)));
}

function confirmationTokenFor(beforeRevision, operations, diff) {
  const crypto = require('node:crypto');
  const payload = {beforeRevision, operations, diff};
  return `animation:v1:${crypto.createHash('sha256').update(JSON.stringify(payload)).digest('hex')}`;
}

function applyAnimationBatch(adapter, input) {
  validateMutationAdapter(adapter);
  const batch = validateAnimationBatch(input);
  const beforeRevision = adapter.getRevision();
  if (beforeRevision !== batch.expectedRevision) {
    fail('STALE_PROJECT_REVISION', `Expected ${batch.expectedRevision} but active project is ${beforeRevision}.`);
  }

  adapter.preflight(batch.operations);
  const diff = destructiveDiff(batch.operations);
  const confirmationToken = diff.length > 0 ? confirmationTokenFor(beforeRevision, batch.operations, diff) : null;
  if (batch.dryRun) {
    return Object.freeze({
      ok: true,
      dryRun: true,
      beforeRevision,
      afterRevision: beforeRevision,
      applied: 0,
      changedIds: Object.freeze([]),
      diff,
      confirmationToken,
    });
  }
  if (diff.length > 0) {
    if (!batch.confirmationToken) {
      fail('ANIMATION_CONFIRMATION_REQUIRED', 'Destructive animation operations require a revision-bound dry-run confirmation token.');
    }
    if (batch.confirmationToken !== confirmationToken) {
      fail('ANIMATION_CONFIRMATION_MISMATCH', 'Animation confirmation token does not match the current revision-bound diff.');
    }
  }

  return applyOperationsTransaction(adapter, batch, beforeRevision);
}

function poseChannel(value, field) {
  if (!Array.isArray(value) || value.length !== 3 || !value.every(Number.isFinite)) {
    fail('INVALID_LOOP_SEAM_POSE', `${field} must contain exactly three finite numbers.`);
  }
  return value;
}

function normalizePose(value, field) {
  if (!isPlainObject(value)) fail('INVALID_LOOP_SEAM_POSE', `${field} must be an object keyed by target id.`);
  const output = new Map();
  for (const targetId of Object.keys(value).sort((left, right) => left.localeCompare(right, 'en'))) {
    const target = value[targetId];
    if (!isPlainObject(target)) fail('INVALID_LOOP_SEAM_POSE', `${field}.${targetId} must be an object.`);
    const channels = new Map();
    for (const channelName of Object.keys(target).sort((left, right) => left.localeCompare(right, 'en'))) {
      if (!ANIMATION_CHANNELS.has(channelName)) {
        fail('INVALID_LOOP_SEAM_POSE', `${field}.${targetId}.${channelName} is not a provider-neutral transform channel.`);
      }
      channels.set(channelName, poseChannel(target[channelName], `${field}.${targetId}.${channelName}`));
    }
    output.set(targetId, channels);
  }
  return output;
}

function channelValueDelta(channelName, left, right) {
  const absolute = Math.abs(left - right);
  if (channelName !== 'rotation') return absolute;
  const wrapped = absolute % 360;
  return Math.min(wrapped, 360 - wrapped);
}

function validateLoopSeam(input) {
  if (!isPlainObject(input)) fail('INVALID_LOOP_SEAM_REQUEST', 'Loop seam request must be an object.');
  rejectUnknownFields(input, new Set(['startPose', 'endPose', 'tolerance']), 'UNKNOWN_LOOP_SEAM_FIELD', 'Loop seam request');
  const tolerance = finiteNumber(input.tolerance, 'tolerance');
  if (tolerance < 0) fail('INVALID_LOOP_SEAM_TOLERANCE', 'tolerance must be non-negative.');
  const start = normalizePose(input.startPose, 'startPose');
  const end = normalizePose(input.endPose, 'endPose');

  const targetIds = [...new Set([...start.keys(), ...end.keys()])].sort((left, right) => left.localeCompare(right, 'en'));
  let maxDelta = 0;
  const mismatches = [];
  for (const targetId of targetIds) {
    const left = start.get(targetId);
    const right = end.get(targetId);
    if (!left || !right) {
      mismatches.push(Object.freeze({targetId, channel: null, delta: null, reason: 'MISSING_TARGET'}));
      continue;
    }
    const channels = [...new Set([...left.keys(), ...right.keys()])].sort((left, right) => left.localeCompare(right, 'en'));
    for (const channelName of channels) {
      const leftValue = left.get(channelName);
      const rightValue = right.get(channelName);
      if (!leftValue || !rightValue) {
        mismatches.push(Object.freeze({targetId, channel: channelName, delta: null, reason: 'MISSING_CHANNEL'}));
        continue;
      }
      let channelDelta = 0;
      for (let index = 0; index < 3; index += 1) {
        channelDelta = Math.max(channelDelta, channelValueDelta(channelName, leftValue[index], rightValue[index]));
      }
      maxDelta = Math.max(maxDelta, channelDelta);
      if (channelDelta > tolerance) {
        mismatches.push(Object.freeze({targetId, channel: channelName, delta: channelDelta, reason: 'TOLERANCE_EXCEEDED'}));
      }
    }
  }
  const roundedMaxDelta = Number(maxDelta.toFixed(12));
  return Object.freeze({
    pass: mismatches.length === 0,
    tolerance,
    maxDelta: roundedMaxDelta,
    mismatches: Object.freeze(mismatches),
  });
}

function distance3(left, right) {
  const dx = left[0] - right[0];
  const dy = left[1] - right[1];
  const dz = left[2] - right[2];
  return Math.sqrt((dx * dx) + (dy * dy) + (dz * dz));
}

function diagnoseFootSlide(input) {
  if (!isPlainObject(input)) fail('INVALID_FOOT_SLIDE_REQUEST', 'Foot-slide request must be an object.');
  rejectUnknownFields(input, new Set(['samples']), 'UNKNOWN_FOOT_SLIDE_FIELD', 'Foot-slide request');
  if (!Array.isArray(input.samples)) fail('INVALID_FOOT_SLIDE_SAMPLES', 'samples must be an array.');

  let plantedSamples = 0;
  let previousPlanted = null;
  let distance = 0;
  for (let index = 0; index < input.samples.length; index += 1) {
    const sample = input.samples[index];
    if (!isPlainObject(sample)) fail('INVALID_FOOT_SLIDE_SAMPLE', `samples[${index}] must be an object.`);
    rejectUnknownFields(sample, new Set(['time', 'position', 'planted']), 'UNKNOWN_FOOT_SLIDE_SAMPLE_FIELD', `samples[${index}]`);
    nonNegativeTime(sample.time, `samples[${index}].time`);
    const position = vector3(sample.position, `samples[${index}].position`);
    if (typeof sample.planted !== 'boolean') fail('INVALID_FOOT_SLIDE_SAMPLE', `samples[${index}].planted must be boolean.`);
    if (!sample.planted) {
      previousPlanted = null;
      continue;
    }
    plantedSamples += 1;
    if (previousPlanted) distance += distance3(previousPlanted, position);
    previousPlanted = position;
  }

  if (plantedSamples < 2) {
    return Object.freeze({
      measurable: false,
      reason: 'INSUFFICIENT_CONTACT_SAMPLES',
      plantedSamples,
      distance: null,
    });
  }

  return Object.freeze({
    measurable: true,
    reason: null,
    plantedSamples,
    distance: Number(distance.toFixed(12)),
  });
}

function validateReadOnlyAdapter(adapter, method) {
  if (!adapter || typeof adapter !== 'object' || typeof adapter[method] !== 'function') {
    fail('INVALID_ANIMATION_ADAPTER', `Animation adapter is missing ${method}().`);
  }
}

function previewRequest(input) {
  if (!isPlainObject(input)) fail('INVALID_ANIMATION_PREVIEW_REQUEST', 'Preview request must be an object.');
  rejectUnknownFields(input, new Set(['animationId', 'time']), 'UNKNOWN_ANIMATION_PREVIEW_FIELD', 'Preview request');
  return Object.freeze({
    animationId: boundedString(input.animationId, 'animationId'),
    time: nonNegativeTime(input.time, 'time'),
  });
}

function playPreview(adapter, input) {
  validateReadOnlyAdapter(adapter, 'playPreview');
  return adapter.playPreview(previewRequest(input));
}

function stopPreview(adapter) {
  validateReadOnlyAdapter(adapter, 'stopPreview');
  return adapter.stopPreview();
}

function inspectPose(adapter, input) {
  validateReadOnlyAdapter(adapter, 'inspectPose');
  return adapter.inspectPose(previewRequest(input));
}

function capturePose(adapter, input) {
  validateReadOnlyAdapter(adapter, 'capturePose');
  if (!isPlainObject(input)) fail('INVALID_POSE_CAPTURE_REQUEST', 'Pose capture request must be an object.');
  rejectUnknownFields(input, new Set(['animationId', 'time', 'cameraPreset', 'resolution']), 'UNKNOWN_POSE_CAPTURE_FIELD', 'Pose capture request');
  const resolution = input.resolution;
  if (!Array.isArray(resolution) || resolution.length !== 2 || !resolution.every(Number.isInteger)
      || resolution.some((entry) => entry < 1 || entry > MAX_CAPTURE_DIMENSION)) {
    fail('INVALID_CAPTURE_RESOLUTION', `resolution must contain two integers in 1-${MAX_CAPTURE_DIMENSION}.`);
  }
  const request = Object.freeze({
    animationId: boundedString(input.animationId, 'animationId'),
    time: nonNegativeTime(input.time, 'time'),
    cameraPreset: boundedString(input.cameraPreset, 'cameraPreset', {max: 64}),
    resolution: Object.freeze(resolution.slice()),
  });
  return adapter.capturePose(request);
}

module.exports = {
  MAX_ANIMATION_OPERATIONS,
  AnimationContractError,
  validateAnimationBatch,
  applyAnimationBatch,
  validateLoopSeam,
  diagnoseFootSlide,
  playPreview,
  stopPreview,
  inspectPose,
  capturePose,
};
