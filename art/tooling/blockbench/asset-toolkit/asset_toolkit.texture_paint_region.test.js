'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const {
  MAX_TEXTURE_PIXELS_PER_BATCH,
  validateUvTextureBatch,
  applyUvTextureBatch,
} = require('./core/uv-texture/uv_texture_engine.js');
const {createBlockbenchUvTextureAdapter} = require('./blockbench-plugin/uv_texture_adapter.js');

function paintOperation(overrides = {}) {
  return {
    type: 'texture_paint_region',
    textureId: 'tex-1',
    region: {x: 1, y: 2, width: 2, height: 2},
    pixels: [
      [255, 0, 0, 255],
      [0, 255, 0, 128],
      [0, 0, 255, 255],
      [255, 255, 255, 0],
    ],
    ...overrides,
  };
}

function batch(operation, dryRun = false, expectedRevision = 'sha256:before') {
  return {
    expectedRevision,
    label: 'Bounded Paint Region',
    dryRun,
    operations: [operation],
  };
}

function mockBlockbench() {
  const events = [];
  const project = {
    name: 'paint_region_asset',
    format: {id: 'free'},
    groups: [],
    elements: [],
    textures: [],
    animations: [],
    selected_elements: [],
  };

  class Cube {
    static all = [];
  }

  function makeContext(width, height) {
    const pixels = new Uint8ClampedArray(width * height * 4);
    for (let offset = 0; offset < pixels.length; offset += 4) pixels.set([9, 9, 9, 255], offset);
    return {
      pixels,
      getImageData(x, y, regionWidth, regionHeight) {
        const data = new Uint8ClampedArray(regionWidth * regionHeight * 4);
        for (let row = 0; row < regionHeight; row += 1) {
          for (let column = 0; column < regionWidth; column += 1) {
            const source = ((y + row) * width + (x + column)) * 4;
            const target = (row * regionWidth + column) * 4;
            data.set(pixels.slice(source, source + 4), target);
          }
        }
        return {data, width: regionWidth, height: regionHeight};
      },
      putImageData(image, x, y) {
        events.push(['putImageData', x, y, image.width, image.height]);
        for (let row = 0; row < image.height; row += 1) {
          for (let column = 0; column < image.width; column += 1) {
            const source = (row * image.width + column) * 4;
            const target = ((y + row) * width + (x + column)) * 4;
            pixels.set(image.data.slice(source, source + 4), target);
          }
        }
      },
    };
  }

  class Texture {
    static all = [];
    constructor() {
      this.uuid = 'tex-1';
      this.id = '0';
      this.name = 'paint.png';
      this.width = 8;
      this.height = 8;
      this.internal = true;
      this.layers_enabled = false;
      this.ctx = makeContext(8, 8);
      this.canvas = {};
      this.source = 'data:image/mock;base64,before';
      this.updateCalls = 0;
    }
    updateChangesAfterEdit() {
      this.updateCalls += 1;
      this.source = `data:image/mock;base64,${Buffer.from(this.ctx.pixels).toString('base64')}`;
    }
  }

  const texture = new Texture();
  Texture.all = [texture];
  project.textures = [texture];

  const Undo = {
    initEdit(aspects) { events.push(['undo.begin', aspects]); },
    finishEdit(label, aspects) { events.push(['undo.finish', label, aspects]); },
    cancelEdit(revert) { events.push(['undo.cancel', revert]); },
  };

  const bb = {Blockbench: {Project: project, isWeb: false}, Cube, Texture, Undo};
  const adapter = createBlockbenchUvTextureAdapter(bb);
  return {bb, adapter, texture, events};
}

function pixel(texture, x, y) {
  const offset = (y * texture.width + x) * 4;
  return Array.from(texture.ctx.pixels.slice(offset, offset + 4));
}

test('bounded paint region validates an exact row-major RGBA payload and charges the region area', () => {
  const validated = validateUvTextureBatch(batch(paintOperation()));
  assert.equal(validated.operations.length, 1);
  assert.equal(validated.pixelWrites, 4);
  assert.deepEqual(validated.operations[0].region, {x: 1, y: 2, width: 2, height: 2});
  assert.deepEqual(validated.operations[0].pixels, paintOperation().pixels);
  assert.equal(Object.isFrozen(validated.operations[0].pixels), true);
});

test('bounded paint region rejects pixel-count mismatch, invalid RGBA, and batch budget overflow', () => {
  assert.throws(
    () => validateUvTextureBatch(batch(paintOperation({pixels: [[255, 0, 0, 255]]}))),
    /PAINT_PIXEL_COUNT_MISMATCH/,
  );
  assert.throws(
    () => validateUvTextureBatch(batch(paintOperation({
      region: {x: 0, y: 0, width: 1, height: 1},
      pixels: [[0, 0, 0, 256]],
    }))),
    /INVALID_RGBA/,
  );
  assert.throws(
    () => validateUvTextureBatch(batch(paintOperation({
      region: {x: 0, y: 0, width: MAX_TEXTURE_PIXELS_PER_BATCH + 1, height: 1},
      pixels: [],
    }))),
    /TEXTURE_PIXEL_BUDGET_EXCEEDED|PAINT_PIXEL_COUNT_MISMATCH/,
  );
});

test('bounded paint region dry-run is mutation-free and committed apply writes exact non-uniform RGBA in one Undo transaction', () => {
  const env = mockBlockbench();
  const operation = paintOperation();
  const beforeRevision = env.adapter.getRevision();

  const preview = applyUvTextureBatch(env.adapter, batch(operation, true, beforeRevision));
  assert.equal(preview.dryRun, true);
  assert.deepEqual(pixel(env.texture, 1, 2), [9, 9, 9, 255]);
  assert.equal(env.events.some(([kind]) => kind === 'undo.begin'), false);

  const result = applyUvTextureBatch(env.adapter, batch(operation, false, beforeRevision));
  assert.equal(result.ok, true);
  assert.equal(result.pixelWrites, 4);
  assert.deepEqual(pixel(env.texture, 1, 2), [255, 0, 0, 255]);
  assert.deepEqual(pixel(env.texture, 2, 2), [0, 255, 0, 128]);
  assert.deepEqual(pixel(env.texture, 1, 3), [0, 0, 255, 255]);
  assert.deepEqual(pixel(env.texture, 2, 3), [255, 255, 255, 0]);
  assert.deepEqual(pixel(env.texture, 0, 0), [9, 9, 9, 255]);
  assert.equal(env.texture.updateCalls, 1);
  assert.equal(env.events.filter(([kind]) => kind === 'putImageData').length, 1);
  assert.equal(env.events.filter(([kind]) => kind === 'undo.begin').length, 1);
  assert.equal(env.events.filter(([kind]) => kind === 'undo.finish').length, 1);
  assert.notEqual(result.afterRevision, beforeRevision);
});

test('bounded paint region adapter rejects out-of-bounds and layered targets before Undo', () => {
  const env = mockBlockbench();
  assert.throws(
    () => env.adapter.preflight([paintOperation({region: {x: 7, y: 7, width: 2, height: 2}})]),
    /PIXEL_REGION_OUT_OF_BOUNDS/,
  );

  env.texture.layers_enabled = true;
  assert.throws(
    () => env.adapter.preflight([paintOperation({region: {x: 0, y: 0, width: 1, height: 1}, pixels: [[1, 2, 3, 4]]})]),
    /LAYERED_TEXTURE_UNSUPPORTED/,
  );
  assert.equal(env.events.some(([kind]) => kind === 'undo.begin'), false);
});
