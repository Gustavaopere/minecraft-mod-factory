'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const {
  validateUvTextureBatch,
  applyUvTextureBatch,
} = require('./core/uv-texture/uv_texture_engine.js');
const {createBlockbenchUvTextureAdapter} = require('./blockbench-plugin/uv_texture_adapter.js');

function islandOperation(overrides = {}) {
  return {
    type: 'texture_paint_uv_island',
    textureId: 'tex-1',
    faces: [
      {cubeId: 'cube-a', face: 'north'},
      {cubeId: 'cube-b', face: 'north'},
    ],
    region: {x: 0, y: 0, width: 2, height: 3},
    pixels: [
      [255, 0, 0, 255],
      [0, 255, 0, 255],
      [0, 0, 255, 255],
      [255, 255, 0, 255],
      [255, 0, 255, 128],
      [0, 255, 255, 64],
    ],
    ...overrides,
  };
}

function batch(operation, expectedRevision = 'sha256:before', dryRun = false) {
  return {
    expectedRevision,
    label: 'Bounded UV Island Paint',
    dryRun,
    operations: [operation],
  };
}

function mockBlockbench({layersEnabled = false} = {}) {
  const events = [];
  const project = {
    name: 'uv_island_asset',
    format: {id: 'free'},
    groups: [],
    elements: [],
    textures: [],
    animations: [],
    selected_elements: [],
    texture_width: 8,
    texture_height: 8,
  };

  class Face {
    constructor(texture, uv) {
      this.enabled = true;
      this.texture = texture;
      this.uv = uv.slice();
    }
    extend(data) {
      if (data.uv) this.uv = data.uv.slice();
      if (Object.hasOwn(data, 'texture')) this.texture = data.texture;
      return this;
    }
  }

  class Cube {
    static all = [];
    constructor(uuid, uv) {
      this.uuid = uuid;
      this.name = uuid;
      this.from = [0, 0, 0];
      this.to = [1, 1, 1];
      this.origin = [0, 0, 0];
      this.parent = null;
      this.box_uv = false;
      this.uv_offset = [0, 0];
      this.faces = {north: new Face('tex-1', uv)};
    }
    setUVMode(value) { this.box_uv = !!value; return this; }
    extend(data) { if (data.uv_offset) this.uv_offset = data.uv_offset.slice(); return this; }
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
      this.name = 'island.png';
      this.width = 8;
      this.height = 8;
      this.internal = true;
      this.layers_enabled = layersEnabled;
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

  const cubeA = new Cube('cube-a', [0, 0, 2, 1]);
  const cubeB = new Cube('cube-b', [0, 1, 1, 3]);
  Cube.all = [cubeA, cubeB];
  project.elements = [cubeA, cubeB];

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
  return {bb, adapter, project, cubeA, cubeB, texture, events};
}

function pixel(texture, x, y) {
  const offset = (y * texture.width + x) * 4;
  return Array.from(texture.ctx.pixels.slice(offset, offset + 4));
}

test('UV island paint validates explicit face selectors and charges the declared bounding region', () => {
  const validated = validateUvTextureBatch(batch(islandOperation()));
  assert.equal(validated.operations.length, 1);
  assert.equal(validated.pixelWrites, 6);
  assert.deepEqual(validated.operations[0].faces, [
    {cubeId: 'cube-a', face: 'north'},
    {cubeId: 'cube-b', face: 'north'},
  ]);
  assert.deepEqual(validated.operations[0].region, {x: 0, y: 0, width: 2, height: 3});
  assert.equal(Object.isFrozen(validated.operations[0].faces), true);
  assert.equal(Object.isFrozen(validated.operations[0].pixels), true);
});

test('UV island paint rejects empty or duplicate face selectors and malformed region pixels', () => {
  assert.throws(
    () => validateUvTextureBatch(batch(islandOperation({faces: []}))),
    /INVALID_UV_ISLAND_FACES/,
  );
  assert.throws(
    () => validateUvTextureBatch(batch(islandOperation({
      faces: [{cubeId: 'cube-a', face: 'north'}, {cubeId: 'cube-a', face: 'north'}],
    }))),
    /DUPLICATE_UV_ISLAND_FACE/,
  );
  assert.throws(
    () => validateUvTextureBatch(batch(islandOperation({pixels: [[1, 2, 3, 4]]}))),
    /PAINT_PIXEL_COUNT_MISMATCH/,
  );
  assert.throws(
    () => validateUvTextureBatch(batch(islandOperation({
      region: {x: 0, y: 0, width: 1, height: 1},
      pixels: [[0, 0, 0, 256]],
    }))),
    /INVALID_RGBA/,
  );
});

test('UV island dry-run is mutation-free and committed apply paints only mask pixels in one Undo transaction', () => {
  const env = mockBlockbench();
  const beforeRevision = env.adapter.getRevision();
  const operation = islandOperation();

  const preview = applyUvTextureBatch(env.adapter, batch(operation, beforeRevision, true));
  assert.equal(preview.dryRun, true);
  assert.deepEqual(pixel(env.texture, 0, 0), [9, 9, 9, 255]);
  assert.equal(env.events.some(([kind]) => kind === 'undo.begin'), false);

  const result = applyUvTextureBatch(env.adapter, batch(operation, beforeRevision, false));
  assert.equal(result.ok, true);
  assert.equal(result.pixelWrites, 6);
  assert.deepEqual(pixel(env.texture, 0, 0), [255, 0, 0, 255]);
  assert.deepEqual(pixel(env.texture, 1, 0), [0, 255, 0, 255]);
  assert.deepEqual(pixel(env.texture, 0, 1), [0, 0, 255, 255]);
  assert.deepEqual(pixel(env.texture, 0, 2), [255, 0, 255, 128]);
  assert.deepEqual(pixel(env.texture, 1, 1), [9, 9, 9, 255]);
  assert.deepEqual(pixel(env.texture, 1, 2), [9, 9, 9, 255]);
  assert.deepEqual(pixel(env.texture, 7, 7), [9, 9, 9, 255]);
  assert.equal(env.texture.updateCalls, 1);
  assert.equal(env.events.filter(([kind]) => kind === 'putImageData').length, 1);
  assert.equal(env.events.filter(([kind]) => kind === 'undo.begin').length, 1);
  assert.equal(env.events.filter(([kind]) => kind === 'undo.finish').length, 1);
  assert.notEqual(result.afterRevision, beforeRevision);
});

test('UV island preflight rejects disconnected and corner-only selections before Undo', () => {
  const disconnected = mockBlockbench();
  disconnected.cubeB.faces.north.uv = [4, 4, 5, 5];
  assert.throws(
    () => applyUvTextureBatch(disconnected.adapter, batch(
      islandOperation({region: {x: 0, y: 0, width: 5, height: 5}, pixels: Array.from({length: 25}, () => [1, 2, 3, 4])}),
      disconnected.adapter.getRevision(),
    )),
    /UV_ISLAND_DISCONNECTED/,
  );
  assert.equal(disconnected.events.some(([kind]) => kind === 'undo.begin'), false);

  const cornerOnly = mockBlockbench();
  cornerOnly.cubeB.faces.north.uv = [2, 1, 3, 2];
  assert.throws(
    () => applyUvTextureBatch(cornerOnly.adapter, batch(
      islandOperation({region: {x: 0, y: 0, width: 3, height: 2}, pixels: Array.from({length: 6}, () => [1, 2, 3, 4])}),
      cornerOnly.adapter.getRevision(),
    )),
    /UV_ISLAND_DISCONNECTED/,
  );
  assert.equal(cornerOnly.events.some(([kind]) => kind === 'undo.begin'), false);
});

test('UV island preflight fails closed on texture mismatch, Box UV, non-pixel alignment, region mismatch, layers, and bounds', () => {
  const mismatch = mockBlockbench();
  mismatch.cubeB.faces.north.texture = 'other-texture';
  assert.throws(
    () => applyUvTextureBatch(mismatch.adapter, batch(islandOperation(), mismatch.adapter.getRevision())),
    /UV_ISLAND_TEXTURE_MISMATCH/,
  );

  const boxUv = mockBlockbench();
  boxUv.cubeB.box_uv = true;
  assert.throws(
    () => applyUvTextureBatch(boxUv.adapter, batch(islandOperation(), boxUv.adapter.getRevision())),
    /BOX_UV_ISLAND_UNSUPPORTED/,
  );

  const fractional = mockBlockbench();
  fractional.cubeA.faces.north.uv = [0.5, 0, 2, 1];
  assert.throws(
    () => applyUvTextureBatch(fractional.adapter, batch(islandOperation(), fractional.adapter.getRevision())),
    /UV_ISLAND_NON_PIXEL_ALIGNED/,
  );

  const wrongRegion = mockBlockbench();
  assert.throws(
    () => applyUvTextureBatch(wrongRegion.adapter, batch(
      islandOperation({region: {x: 0, y: 0, width: 3, height: 3}, pixels: Array.from({length: 9}, () => [1, 2, 3, 4])}),
      wrongRegion.adapter.getRevision(),
    )),
    /UV_ISLAND_REGION_MISMATCH/,
  );

  const layered = mockBlockbench({layersEnabled: true});
  assert.throws(
    () => applyUvTextureBatch(layered.adapter, batch(islandOperation(), layered.adapter.getRevision())),
    /LAYERED_TEXTURE_UNSUPPORTED/,
  );

  const outOfBounds = mockBlockbench();
  outOfBounds.cubeB.faces.north.uv = [7, 7, 9, 8];
  assert.throws(
    () => applyUvTextureBatch(outOfBounds.adapter, batch(
      islandOperation({region: {x: 0, y: 0, width: 9, height: 8}, pixels: Array.from({length: 72}, () => [1, 2, 3, 4])}),
      outOfBounds.adapter.getRevision(),
    )),
    /UV_ISLAND_PIXEL_REGION_OUT_OF_BOUNDS/,
  );
});
