'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const {applyUvTextureBatch} = require('./core/uv-texture/uv_texture_engine.js');
const {createBlockbenchUvTextureAdapter} = require('./blockbench-plugin/uv_texture_adapter.js');

function mockBlockbench({layersEnabled = false} = {}) {
  const events = [];
  const project = {name: 'uv_asset', format: {id: 'free'}, groups: [], elements: [], textures: [], animations: [], selected_elements: []};

  class Face {
    constructor() {
      this.enabled = true;
      this.texture = 'tex-1';
      this.uv = [0, 0, 1, 1];
    }
    extend(data) {
      if (data.uv) this.uv = data.uv.slice();
      if (Object.hasOwn(data, 'texture')) this.texture = data.texture;
      return this;
    }
  }

  class Cube {
    static all = [];
    constructor() {
      this.uuid = 'cube-1';
      this.name = 'cube';
      this.from = [0, 0, 0];
      this.to = [1, 1, 1];
      this.origin = [0, 0, 0];
      this.parent = null;
      this.box_uv = false;
      this.uv_offset = [0, 0];
      this.faces = {
        north: new Face(), south: new Face(), east: new Face(), west: new Face(), up: new Face(), down: new Face(),
      };
    }
    setUVMode(value) { this.box_uv = !!value; return this; }
    extend(data) { if (data.uv_offset) this.uv_offset = data.uv_offset.slice(); return this; }
  }

  function makeContext(width, height) {
    const pixels = new Uint8ClampedArray(width * height * 4);
    for (let index = 0; index < pixels.length; index += 4) pixels.set([1, 2, 3, 255], index);
    return {
      pixels,
      getImageData(x, y, regionWidth, regionHeight) {
        const data = new Uint8ClampedArray(regionWidth * regionHeight * 4);
        for (let row = 0; row < regionHeight; row++) {
          for (let column = 0; column < regionWidth; column++) {
            const source = ((y + row) * width + (x + column)) * 4;
            const target = (row * regionWidth + column) * 4;
            data.set(pixels.slice(source, source + 4), target);
          }
        }
        return {data, width: regionWidth, height: regionHeight};
      },
      putImageData(image, x, y) {
        for (let row = 0; row < image.height; row++) {
          for (let column = 0; column < image.width; column++) {
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
      this.name = 'texture.png';
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
      this.updateCalls++;
      this.internal = true;
      this.source = `data:image/mock;base64,${Buffer.from(this.ctx.pixels).toString('base64')}`;
    }
  }

  const cube = new Cube();
  Cube.all = [cube];
  project.elements = [cube];
  const texture = new Texture();
  Texture.all = [texture];
  project.textures = [texture];

  const Undo = {
    initEdit(aspects) { events.push(['undo.begin', aspects]); },
    finishEdit(label, aspects) { events.push(['undo.finish', label, aspects]); },
    cancelEdit(revert) { events.push(['undo.cancel', revert]); },
  };
  return {Blockbench: {Project: project, isWeb: false}, Cube, Texture, Undo, project, cube, texture, events};
}

function batch(expectedRevision) {
  return {
    expectedRevision,
    label: 'UV Texture',
    operations: [
      {type: 'set_face_uv', cubeId: 'cube-1', face: 'north', uv: [0, 0, 8, 8]},
      {type: 'set_face_texture', cubeId: 'cube-1', face: 'north', textureId: 'tex-1'},
      {type: 'set_box_uv', cubeId: 'cube-1', enabled: true, offset: [4, 8]},
      {type: 'texture_fill_rect', textureId: 'tex-1', x: 1, y: 2, width: 4, height: 3, color: [10, 20, 30, 255]},
      {
        type: 'texture_replace_palette', textureId: 'tex-1', region: {x: 0, y: 0, width: 8, height: 8},
        replacements: [{from: [1, 2, 3, 255], to: [4, 5, 6, 255]}],
      },
    ],
  };
}

function pixel(texture, x, y) {
  const index = (y * texture.width + x) * 4;
  return Array.from(texture.ctx.pixels.slice(index, index + 4));
}

test('Blockbench adapter applies UV and exact bounded pixels in one bitmap-aware Undo transaction', () => {
  const bb = mockBlockbench();
  const adapter = createBlockbenchUvTextureAdapter(bb);
  const before = adapter.getRevision();
  const result = applyUvTextureBatch(adapter, batch(before));

  assert.deepEqual(bb.cube.faces.north.uv, [0, 0, 8, 8]);
  assert.equal(bb.cube.faces.north.texture, 'tex-1');
  assert.equal(bb.cube.box_uv, true);
  assert.deepEqual(bb.cube.uv_offset, [4, 8]);
  assert.deepEqual(pixel(bb.texture, 0, 0), [4, 5, 6, 255]);
  assert.deepEqual(pixel(bb.texture, 1, 2), [10, 20, 30, 255]);
  assert.equal(bb.texture.updateCalls, 1);
  assert.deepEqual(result.changedIds, ['cube-1', 'tex-1']);
  assert.notEqual(result.afterRevision, before);

  const begin = bb.events.find(([kind]) => kind === 'undo.begin');
  assert.equal(begin[1].bitmap, true);
  assert.deepEqual(begin[1].elements, [bb.cube]);
  assert.deepEqual(begin[1].textures, [bb.texture]);
  assert.equal(bb.events.filter(([kind]) => kind === 'undo.begin').length, 1);
  assert.equal(bb.events.filter(([kind]) => kind === 'undo.finish').length, 1);
});

test('Blockbench adapter preflight rejects out-of-bounds pixels and layered textures', () => {
  const bb = mockBlockbench();
  const adapter = createBlockbenchUvTextureAdapter(bb);
  assert.throws(
    () => adapter.preflight([{type: 'texture_fill_rect', textureId: 'tex-1', x: 7, y: 7, width: 2, height: 2, color: [0, 0, 0, 255]}]),
    /PIXEL_REGION_OUT_OF_BOUNDS/,
  );

  const layered = mockBlockbench({layersEnabled: true});
  const layeredAdapter = createBlockbenchUvTextureAdapter(layered);
  assert.throws(
    () => layeredAdapter.preflight([{type: 'texture_fill_rect', textureId: 'tex-1', x: 0, y: 0, width: 1, height: 1, color: [0, 0, 0, 255]}]),
    /LAYERED_TEXTURE_UNSUPPORTED/,
  );
});
