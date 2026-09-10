'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const {createBlockbenchUvTextureAdapter} = require('./blockbench-plugin/uv_texture_adapter.js');

function mockBlockbench({width = 4, height = 3, layersEnabled = false, pixels = null} = {}) {
  const events = [];
  const project = {
    name: 'palette_sampling_asset',
    format: {id: 'free'},
    groups: [],
    elements: [],
    textures: [],
    animations: [],
    selected_elements: [],
    texture_width: width,
    texture_height: height,
  };

  class Cube {
    static all = [];
  }

  function makeContext() {
    const source = pixels
      ? new Uint8ClampedArray(pixels.flat())
      : new Uint8ClampedArray(width * height * 4);
    if (source.length !== width * height * 4) throw new Error('fixture pixel count mismatch');
    return {
      pixels: source,
      getImageData(x, y, regionWidth, regionHeight) {
        events.push(['getImageData', x, y, regionWidth, regionHeight]);
        const data = new Uint8ClampedArray(regionWidth * regionHeight * 4);
        for (let row = 0; row < regionHeight; row += 1) {
          for (let column = 0; column < regionWidth; column += 1) {
            const sourceOffset = ((y + row) * width + (x + column)) * 4;
            const targetOffset = (row * regionWidth + column) * 4;
            data.set(source.slice(sourceOffset, sourceOffset + 4), targetOffset);
          }
        }
        return {data, width: regionWidth, height: regionHeight};
      },
      putImageData() { events.push(['putImageData']); },
    };
  }

  class Texture {
    static all = [];
    constructor() {
      this.uuid = 'tex-1';
      this.id = '0';
      this.name = 'palette.png';
      this.width = width;
      this.height = height;
      this.internal = true;
      this.layers_enabled = layersEnabled;
      this.ctx = makeContext();
      this.canvas = {};
      this.source = 'data:image/mock;base64,palette-source';
      this.updateCalls = 0;
    }
    updateChangesAfterEdit() {
      this.updateCalls += 1;
      events.push(['updateChangesAfterEdit']);
    }
  }

  const texture = new Texture();
  Texture.all = [texture];
  project.textures = [texture];

  const Undo = {
    initEdit() { events.push(['undo.begin']); },
    finishEdit() { events.push(['undo.finish']); },
    cancelEdit() { events.push(['undo.cancel']); },
  };

  const bb = {Blockbench: {Project: project, isWeb: false}, Cube, Texture, Undo};
  return {adapter: createBlockbenchUvTextureAdapter(bb), texture, events};
}

function samplePixels() {
  const red = [10, 20, 30, 255];
  const transparentBlack = [0, 0, 0, 0];
  const opaqueBlack = [0, 0, 0, 255];
  const halfRed = [10, 20, 30, 128];
  return [
    red, red, red, halfRed,
    red, transparentBlack, transparentBlack, halfRed,
    opaqueBlack, opaqueBlack, opaqueBlack, transparentBlack,
  ];
}

test('palette sampling exposes a read-only adapter capability with deterministic exact RGBA histogram output', () => {
  const env = mockBlockbench({pixels: samplePixels()});
  assert.equal(typeof env.adapter.samplePalette, 'function');
  const beforeRevision = env.adapter.getRevision();
  const result = env.adapter.samplePalette({
    textureId: 'tex-1',
    region: {x: 0, y: 0, width: 4, height: 3},
  });

  assert.deepEqual(result, {
    projectRevision: beforeRevision,
    textureId: 'tex-1',
    region: {x: 0, y: 0, width: 4, height: 3},
    sampledPixels: 12,
    uniqueColorCount: 4,
    truncated: false,
    colors: [
      {rgba: [10, 20, 30, 255], count: 4},
      {rgba: [0, 0, 0, 0], count: 3},
      {rgba: [0, 0, 0, 255], count: 3},
      {rgba: [10, 20, 30, 128], count: 2},
    ],
  });
  assert.equal(env.adapter.getRevision(), beforeRevision);
  assert.equal(env.events.filter(([kind]) => kind === 'getImageData').length, 1);
  assert.equal(env.events.some(([kind]) => kind === 'putImageData'), false);
  assert.equal(env.events.some(([kind]) => kind.startsWith('undo.')), false);
  assert.equal(env.texture.updateCalls, 0);
});

test('palette sampling respects the explicit region and keeps alpha-distinct colors separate', () => {
  const env = mockBlockbench({pixels: samplePixels()});
  const result = env.adapter.samplePalette({
    textureId: 'tex-1',
    region: {x: 1, y: 0, width: 2, height: 2},
  });

  assert.equal(result.sampledPixels, 4);
  assert.equal(result.uniqueColorCount, 2);
  assert.deepEqual(result.colors, [
    {rgba: [0, 0, 0, 0], count: 2},
    {rgba: [10, 20, 30, 255], count: 2},
  ]);
});

test('palette sampling reports the full unique-color count while truncating deterministic output to 256 colors', () => {
  const width = 17;
  const height = 17;
  const pixels = Array.from({length: width * height}, (_, index) => [
    index % 256,
    Math.floor(index / 256),
    0,
    255,
  ]);
  const env = mockBlockbench({width, height, pixels});
  const result = env.adapter.samplePalette({
    textureId: 'tex-1',
    region: {x: 0, y: 0, width, height},
  });

  assert.equal(result.sampledPixels, 289);
  assert.equal(result.uniqueColorCount, 289);
  assert.equal(result.truncated, true);
  assert.equal(result.colors.length, 256);
  assert.deepEqual(result.colors[0], {rgba: [0, 0, 0, 255], count: 1});
  assert.deepEqual(result.colors[1], {rgba: [0, 1, 0, 255], count: 1});
  assert.deepEqual(result.colors[2], {rgba: [1, 0, 0, 255], count: 1});
});

test('palette sampling fails closed for out-of-bounds regions and layered textures without Undo', () => {
  const outOfBounds = mockBlockbench();
  assert.throws(
    () => outOfBounds.adapter.samplePalette({textureId: 'tex-1', region: {x: 3, y: 2, width: 2, height: 2}}),
    /PIXEL_REGION_OUT_OF_BOUNDS/,
  );
  assert.equal(outOfBounds.events.some(([kind]) => kind.startsWith('undo.')), false);

  const layered = mockBlockbench({layersEnabled: true});
  assert.throws(
    () => layered.adapter.samplePalette({textureId: 'tex-1', region: {x: 0, y: 0, width: 1, height: 1}}),
    /LAYERED_TEXTURE_UNSUPPORTED/,
  );
  assert.equal(layered.events.some(([kind]) => kind.startsWith('undo.')), false);
});

test('palette sampling rejects reads above the existing texture pixel budget before touching the canvas', () => {
  const width = 513;
  const height = 512;
  const env = mockBlockbench({width, height});
  assert.throws(
    () => env.adapter.samplePalette({textureId: 'tex-1', region: {x: 0, y: 0, width, height}}),
    /TEXTURE_PIXEL_BUDGET_EXCEEDED/,
  );
  assert.equal(env.events.some(([kind]) => kind === 'getImageData'), false);
  assert.equal(env.events.some(([kind]) => kind.startsWith('undo.')), false);
});
