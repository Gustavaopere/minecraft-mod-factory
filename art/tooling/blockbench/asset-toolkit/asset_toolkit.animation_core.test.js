'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const {
  MAX_ANIMATION_OPERATIONS,
  validateAnimationBatch,
  applyAnimationBatch,
  validateLoopSeam,
  diagnoseFootSlide,
  playPreview,
  stopPreview,
  inspectPose,
  capturePose,
} = require('./core/animation/animation_engine.js');

function completeBatch(overrides = {}) {
  return {
    expectedRevision: 'rev:1',
    label: 'Generic animation batch',
    operations: [
      {type: 'animation_create', id: 'anim-cast', name: 'cast', length: 1.25, loop: 'once'},
      {type: 'animation_update_settings', animationId: 'anim-cast', name: 'cast_primary', length: 1.5, loop: 'hold'},
      {
        type: 'animation_add_keyframe', animationId: 'anim-cast', keyframeId: 'kf-start', targetId: 'root',
        channel: 'rotation', time: 0, value: [0, 0, 0], easing: 'linear',
      },
      {
        type: 'animation_update_keyframe', animationId: 'anim-cast', keyframeId: 'kf-start', targetId: 'root',
        channel: 'rotation', time: 0.1, value: [5, 0, 0], easing: 'bezier',
      },
      {
        type: 'animation_add_effect_marker', animationId: 'anim-cast', markerId: 'marker-cast',
        time: 0.75, markerType: 'particle', label: 'cast_release',
      },
      {type: 'animation_delete_effect_marker', animationId: 'anim-cast', markerId: 'marker-cast'},
      {type: 'animation_delete_keyframe', animationId: 'anim-cast', keyframeId: 'kf-start'},
      {type: 'animation_delete', animationId: 'anim-cast'},
    ],
    ...overrides,
  };
}

function fakeAdapter(overrides = {}) {
  let revision = 'rev:1';
  const events = [];
  return {
    events,
    getRevision() { return revision; },
    preflight(operations) { events.push(['preflight', operations.map((operation) => operation.type)]); },
    beginTransaction(label) { events.push(['begin', label]); },
    applyOperation(operation) { events.push(['apply', operation.type]); return operation.id || operation.animationId || operation.keyframeId || operation.markerId; },
    finishTransaction(label) { events.push(['finish', label]); revision = 'rev:2'; },
    cancelTransaction(revert) { events.push(['cancel', revert]); },
    playPreview(request) { events.push(['preview.play', request]); return {playing: true, ...request}; },
    stopPreview() { events.push(['preview.stop']); return {playing: false}; },
    inspectPose(request) { events.push(['pose.inspect', request]); return {animationId: request.animationId, time: request.time, targets: {root: {rotation: [0, 15, 0]}}}; },
    capturePose(request) { events.push(['pose.capture', request]); return {captureId: 'capture-1', ...request}; },
    ...overrides,
  };
}

function confirmedBatch(adapter, overrides = {}) {
  const preview = applyAnimationBatch(adapter, completeBatch({...overrides, dryRun: true}));
  assert.equal(typeof preview.confirmationToken, 'string');
  assert.match(preview.confirmationToken, /^animation:v1:[0-9a-f]{64}$/);
  assert.ok(Array.isArray(preview.diff));
  return completeBatch({...overrides, dryRun: false, confirmationToken: preview.confirmationToken});
}

test('PR5 contract accepts provider-agnostic animation CRUD, keyframes and abstract effect markers', () => {
  const batch = validateAnimationBatch(completeBatch());
  assert.equal(batch.operations.length, 8);
  assert.deepEqual(batch.operations.map((operation) => operation.type), [
    'animation_create',
    'animation_update_settings',
    'animation_add_keyframe',
    'animation_update_keyframe',
    'animation_add_effect_marker',
    'animation_delete_effect_marker',
    'animation_delete_keyframe',
    'animation_delete',
  ]);
  assert.equal(Object.isFrozen(batch), true);
  assert.equal(Object.isFrozen(batch.operations), true);
});

test('PR5 contract rejects provider serialization, unsupported channels/easing and unsafe bounds', () => {
  assert.throws(
    () => validateAnimationBatch({...completeBatch(), provider: 'geckolib'}),
    /UNKNOWN_ANIMATION_BATCH_FIELD/,
  );
  assert.throws(
    () => validateAnimationBatch(completeBatch({operations: [{
      type: 'animation_add_keyframe', animationId: 'a', keyframeId: 'k', targetId: 'root',
      channel: 'provider_event', time: 0, value: [0, 0, 0], easing: 'linear',
    }]})),
    /INVALID_ANIMATION_CHANNEL/,
  );
  assert.throws(
    () => validateAnimationBatch(completeBatch({operations: [{
      type: 'animation_add_keyframe', animationId: 'a', keyframeId: 'k', targetId: 'root',
      channel: 'rotation', time: 0, value: [0, 0, 0], easing: 'geckolib_only_curve',
    }]})),
    /INVALID_ANIMATION_EASING/,
  );
  assert.throws(
    () => validateAnimationBatch(completeBatch({operations: [{type: 'animation_create', id: 'a', name: 'a', length: 0, loop: 'once'}]})),
    /INVALID_ANIMATION_LENGTH/,
  );
  const oversized = Array.from({length: MAX_ANIMATION_OPERATIONS + 1}, (_, index) => ({
    type: 'animation_create', id: `a-${index}`, name: `a_${index}`, length: 1, loop: 'once',
  }));
  assert.throws(() => validateAnimationBatch(completeBatch({operations: oversized})), /ANIMATION_BATCH_TOO_LARGE/);
});

test('stale revision fails before preflight or Undo and dry-run remains mutation-free', () => {
  const stale = fakeAdapter();
  assert.throws(
    () => applyAnimationBatch(stale, completeBatch({expectedRevision: 'rev:stale'})),
    /STALE_PROJECT_REVISION/,
  );
  assert.deepEqual(stale.events, []);

  const dry = fakeAdapter();
  const result = applyAnimationBatch(dry, completeBatch({dryRun: true}));
  assert.equal(result.ok, true);
  assert.equal(result.dryRun, true);
  assert.equal(result.beforeRevision, 'rev:1');
  assert.equal(result.afterRevision, 'rev:1');
  assert.equal(dry.events.filter(([kind]) => kind === 'preflight').length, 1);
  assert.equal(dry.events.some(([kind]) => ['begin', 'apply', 'finish', 'cancel'].includes(kind)), false);
});

test('Class C animation deletes require revision-bound dry-run diff and confirmation token', () => {
  const deleteOperations = [
    {type: 'animation_delete', animationId: 'anim-cast'},
    {type: 'animation_delete_keyframe', animationId: 'anim-cast', keyframeId: 'kf-start'},
    {type: 'animation_delete_effect_marker', animationId: 'anim-cast', markerId: 'marker-cast'},
  ];

  for (const operation of deleteOperations) {
    const previewAdapter = fakeAdapter();
    const preview = applyAnimationBatch(previewAdapter, completeBatch({operations: [operation], dryRun: true}));
    assert.equal(preview.dryRun, true);
    assert.deepEqual(preview.diff, [operation]);
    assert.match(preview.confirmationToken, /^animation:v1:[0-9a-f]{64}$/);

    const unconfirmed = fakeAdapter();
    assert.throws(
      () => applyAnimationBatch(unconfirmed, completeBatch({operations: [operation], dryRun: false})),
      /ANIMATION_CONFIRMATION_REQUIRED/,
    );
    assert.equal(unconfirmed.events.some(([kind]) => ['begin', 'apply', 'finish', 'cancel'].includes(kind)), false);

    const confirmed = fakeAdapter();
    const result = applyAnimationBatch(confirmed, completeBatch({
      operations: [operation],
      confirmationToken: preview.confirmationToken,
    }));
    assert.equal(result.ok, true);
    assert.equal(result.applied, 1);
  }
});

test('animation mutation batch commits atomically and rolls back adapter failures', () => {
  const adapter = fakeAdapter();
  const result = applyAnimationBatch(adapter, confirmedBatch(adapter));
  assert.equal(result.ok, true);
  assert.equal(result.applied, 8);
  assert.equal(result.beforeRevision, 'rev:1');
  assert.equal(result.afterRevision, 'rev:2');
  assert.equal(adapter.events.filter(([kind]) => kind === 'begin').length, 1);
  assert.equal(adapter.events.filter(([kind]) => kind === 'finish').length, 1);

  const failing = fakeAdapter({
    applyOperation(operation) {
      failing.events.push(['apply', operation.type]);
      if (operation.type === 'animation_add_effect_marker') throw new Error('synthetic animation failure');
      return operation.id || operation.animationId;
    },
  });
  assert.throws(() => applyAnimationBatch(failing, confirmedBatch(failing)), /synthetic animation failure/);
  assert.deepEqual(failing.events.at(-1), ['cancel', true]);
  assert.equal(failing.events.some(([kind]) => kind === 'finish'), false);
});

test('loop seam validation compares provider-neutral sampled poses deterministically', () => {
  const pass = validateLoopSeam({
    startPose: {root: {rotation: [0, 0, 0], position: [0, 0, 0], scale: [1, 1, 1]}},
    endPose: {root: {rotation: [0.001, 0, 0], position: [0, 0, 0], scale: [1, 1, 1]}},
    tolerance: 0.01,
  });
  assert.equal(pass.pass, true);
  assert.equal(pass.maxDelta, 0.001);

  const fail = validateLoopSeam({
    startPose: {root: {rotation: [0, 0, 0]}},
    endPose: {root: {rotation: [2, 0, 0]}},
    tolerance: 0.01,
  });
  assert.equal(fail.pass, false);
  assert.equal(fail.maxDelta, 2);
});

test('loop seam rotation uses shortest angular delta across full turns', () => {
  const wrapped = validateLoopSeam({
    startPose: {root: {rotation: [179, 0, 0]}},
    endPose: {root: {rotation: [-179, 360, 0]}},
    tolerance: 2,
  });
  assert.equal(wrapped.pass, true);
  assert.equal(wrapped.maxDelta, 2);

  const fullTurn = validateLoopSeam({
    startPose: {root: {rotation: [0, 0, 0]}},
    endPose: {root: {rotation: [360, -360, 720]}},
    tolerance: 0,
  });
  assert.equal(fullTurn.pass, true);
  assert.equal(fullTurn.maxDelta, 0);
});

test('foot-slide diagnostics fail closed when contact data is not measurable', () => {
  assert.deepEqual(diagnoseFootSlide({samples: []}), {
    measurable: false,
    reason: 'INSUFFICIENT_CONTACT_SAMPLES',
    plantedSamples: 0,
    distance: null,
  });

  const result = diagnoseFootSlide({samples: [
    {time: 0, position: [0, 0, 0], planted: true},
    {time: 0.1, position: [0.03, 0, 0], planted: true},
    {time: 0.2, position: [5, 0, 0], planted: false},
  ]});
  assert.equal(result.measurable, true);
  assert.equal(result.plantedSamples, 2);
  assert.equal(result.distance, 0.03);
});

test('foot-slide diagnostics do not bridge separate planted contact intervals', () => {
  const result = diagnoseFootSlide({samples: [
    {time: 0, position: [0, 0, 0], planted: true},
    {time: 0.1, position: [4, 0, 0], planted: false},
    {time: 0.2, position: [10, 0, 0], planted: true},
    {time: 0.3, position: [10.02, 0, 0], planted: true},
  ]});
  assert.equal(result.measurable, true);
  assert.equal(result.plantedSamples, 3);
  assert.equal(result.distance, 0.02);
});

test('preview, pose inspection and capture stay adapter-bound and read-only', () => {
  const adapter = fakeAdapter();
  assert.deepEqual(playPreview(adapter, {animationId: 'anim-cast', time: 0.5}), {playing: true, animationId: 'anim-cast', time: 0.5});
  assert.deepEqual(inspectPose(adapter, {animationId: 'anim-cast', time: 0.5}), {
    animationId: 'anim-cast', time: 0.5, targets: {root: {rotation: [0, 15, 0]}},
  });
  assert.deepEqual(capturePose(adapter, {
    animationId: 'anim-cast', time: 0.5, cameraPreset: 'three_quarter', resolution: [512, 512],
  }), {
    captureId: 'capture-1', animationId: 'anim-cast', time: 0.5, cameraPreset: 'three_quarter', resolution: [512, 512],
  });
  assert.deepEqual(stopPreview(adapter), {playing: false});
  assert.equal(adapter.events.some(([kind]) => ['begin', 'apply', 'finish', 'cancel'].includes(kind)), false);
});
