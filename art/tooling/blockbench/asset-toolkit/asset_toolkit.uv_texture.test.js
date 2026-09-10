'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const {
  MAX_TEXTURE_PIXELS_PER_BATCH,
  validateUvTextureBatch,
  applyUvTextureBatch,
} = require('./core/uv-texture/uv_texture_engine.js');
const {
  createBlockbenchUvTextureAdapter,
} = require('./blockbench-plugin/uv_texture_adapter.js');

function batch(overrides = {}) {
  return {
    expectedRevision: 'sha256:before',
    label: 'UV/Texture Batch',
    dryRun: false,
    operations: [
      {type: 'set_face_uv', cubeId: 'cube-1', face: 'north', uv: [0, 0, 8, 8]},
      {type: 'set_face_texture', cubeId: 'cube-1', face: 'north', textureId: 'tex-1'},
      {type: 'set_box_uv', cubeId: 'cube-1', enabled: true, offset: [4, 8]},
      {type: 'texture_fill_rect', textureId: 'tex-1', x: 1, y: 2, width: 4, height: 3, color: [10, 20, 30, 255]},
      {
        type: 'texture_replace_palette',
        textureId: 'tex-1',
        region: {x: 0, y: 0, width: 8, height: 8},
        replacements: [{from: [1, 2, 3, 255], to: [4, 5, 6, 255]}],
      },
    ],
    ...overrides,
  };
}

function fakeAdapter({revision = 'sha256:before', failAt = -1} = {}) {
  const events = [];
  let currentRevision = revision;
  return {
    events,
    getRevision() { events.push('getRevision'); return currentRevision; },
    preflight(operations) { events.push(['preflight', operations.length]); },
    beginTransaction(label) { events.push(['begin', label]); },
    applyOperation(operation, index) {
      events.push(['apply', operation.type]);
      if (index === failAt) throw Object.assign(new Error('boom'), {code: 'FAKE_FAILURE'});
      currentRevision = 'sha256:after';
      return operation.cubeId || operation.textureId;
    },
    finishTransaction(label) { events.push(['finish', label]); },
    cancelTransaction(revert) { events.push(['cancel', revert]); },
  };
}

test('UV/texture batch accepts only the bounded declarative surface', () => {
  const validated = validateUvTextureBatch(batch());
  assert.equal(validated.operations.length, 5);
  assert.equal(validated.pixelWrites, 76);
  assert.equal(Object.isFrozen(validated), true);
  assert.equal(Object.isFrozen(validated.operations), true);
});

test('UV/texture contract rejects unknown operations, malformed UV, colors, and regions', () => {
  assert.throws(
    () => validateUvTextureBatch(batch({operations: [{type: 'execute_script'}]})),
    /UNSUPPORTED_UV_TEXTURE_MUTATION/,
  );
  assert.throws(
    () => validateUvTextureBatch(batch({operations: [{type: 'set_face_uv', cubeId: 'c', face: 'north', uv: [0, 1, 2]}]})),
    /INVALID_UV_RECT/,
  );
  assert.throws(
    () => validateUvTextureBatch(batch({operations: [{type: 'texture_fill_rect', textureId: 't', x: 0, y: 0, width: 1, height: 1, color: [0, 0, 0, 999]}]})),
    /INVALID_RGBA/,
  );
  assert.throws(
    () => validateUvTextureBatch(batch({operations: [{type: 'texture_replace_palette', textureId: 't', region: {x: -1, y: 0, width: 2, height: 2}, replacements: [{from: [0,0,0,255], to: [1,1,1,255]}]}]})),
    /INVALID_PIXEL_REGION/,
  );
});

test('UV/texture contract rejects pixel-write budgets above the bounded batch limit', () => {
  assert.throws(
    () => validateUvTextureBatch(batch({
      operations: [{
        type: 'texture_fill_rect',
        textureId: 'tex-1',
        x: 0,
        y: 0,
        width: MAX_TEXTURE_PIXELS_PER_BATCH + 1,
        height: 1,
        color: [0, 0, 0, 255],
      }],
    })),
    /TEXTURE_PIXEL_BUDGET_EXCEEDED/,
  );
});

test('stale revision fails before preflight or Undo', () => {
  const adapter = fakeAdapter({revision: 'sha256:current'});
  assert.throws(() => applyUvTextureBatch(adapter, batch()), /STALE_PROJECT_REVISION/);
  assert.deepEqual(adapter.events, ['getRevision']);
});

test('dry-run performs preflight without opening an Undo transaction', () => {
  const adapter = fakeAdapter();
  const result = applyUvTextureBatch(adapter, batch({dryRun: true}));
  assert.equal(result.dryRun, true);
  assert.equal(result.applied, 0);
  assert.deepEqual(adapter.events, ['getRevision', ['preflight', 5]]);
});

test('committed UV/texture batch uses one transaction and returns changed ids', () => {
  const adapter = fakeAdapter();
  const result = applyUvTextureBatch(adapter, batch());
  assert.equal(result.ok, true);
  assert.equal(result.applied, 5);
  assert.deepEqual(result.changedIds, ['cube-1', 'tex-1']);
  assert.equal(result.afterRevision, 'sha256:after');
  assert.equal(adapter.events.filter((entry) => Array.isArray(entry) && entry[0] === 'begin').length, 1);
  assert.equal(adapter.events.filter((entry) => Array.isArray(entry) && entry[0] === 'finish').length, 1);
});

test('adapter failure rolls back the entire UV/texture transaction', () => {
  const adapter = fakeAdapter({failAt: 3});
  assert.throws(() => applyUvTextureBatch(adapter, batch()), /FAKE_FAILURE/);
  assert.deepEqual(adapter.events.at(-1), ['cancel', true]);
});

test('Blockbench UV/texture adapter is desktop-only and requires concrete APIs', () => {
  assert.throws(
    () => createBlockbenchUvTextureAdapter({Blockbench: {Project: {}, isWeb: true}}),
    /DESKTOP_REQUIRED/,
  );
});

test('remote MCP protocol remains read-only after PR4 contracts are loaded', () => {
  const {READ_ONLY_METHODS} = require('./live-bridge/protocol.js');
  assert.equal(READ_ONLY_METHODS.some((method) => /uv|texture.*(?:set|fill|replace|paint)/i.test(method)), false);
});
