'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const {
  MAX_TEXTURE_PIXELS_PER_BATCH,
  validateUvTextureBatch,
} = require('./core/uv-texture/uv_texture_engine.js');

function batch(operation) {
  return {
    expectedRevision: 'sha256:before',
    label: 'Texture Create/Import Contract',
    operations: [operation],
  };
}

test('texture_create is allowlisted as a bounded deterministic internal texture allocation', () => {
  const validated = validateUvTextureBatch(batch({
    type: 'texture_create',
    name: 'created.png',
    width: 16,
    height: 16,
  }));

  assert.deepEqual(validated.operations[0], {
    type: 'texture_create',
    name: 'created.png',
    width: 16,
    height: 16,
  });
  assert.equal(validated.pixelWrites, 256);

  assert.throws(
    () => validateUvTextureBatch(batch({
      type: 'texture_create',
      name: 'too-large.png',
      width: MAX_TEXTURE_PIXELS_PER_BATCH + 1,
      height: 1,
    })),
    /TEXTURE_PIXEL_BUDGET_EXCEEDED/,
  );
});

test('texture_import_approved accepts only an opaque local approval id and no filesystem path', () => {
  const validated = validateUvTextureBatch(batch({
    type: 'texture_import_approved',
    approvalId: 'approved-texture-1',
  }));

  assert.deepEqual(validated.operations[0], {
    type: 'texture_import_approved',
    approvalId: 'approved-texture-1',
  });
  assert.equal(Object.hasOwn(validated.operations[0], 'path'), false);

  assert.throws(
    () => validateUvTextureBatch(batch({
      type: 'texture_import_approved',
      approvalId: 'approved-texture-1',
      path: '/tmp/unapproved.png',
    })),
    /UNKNOWN_UV_TEXTURE_FIELD/,
  );
});
