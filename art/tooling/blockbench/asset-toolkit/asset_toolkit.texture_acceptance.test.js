'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const toolkit = require('./core/index.js');
const {applyUvTextureBatch} = require('./core/uv-texture/uv_texture_engine.js');
const {createBlockbenchUvTextureAdapter} = require('./blockbench-plugin/uv_texture_adapter.js');

function makeContext(width, height, initial = [9, 9, 9, 255], events = []) {
  const pixels = new Uint8ClampedArray(width * height * 4);
  for (let offset = 0; offset < pixels.length; offset += 4) pixels.set(initial, offset);
  return {
    pixels,
    getImageData(x, y, regionWidth, regionHeight) {
      events.push(['getImageData', x, y, regionWidth, regionHeight]);
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

function mockBlockbench() {
  const events = [];
  const project = {
    name: 'factory_pr4_texture_acceptance',
    format: {id: 'free'},
    save_path: '/tmp/factory_pr4_texture_acceptance.bbmodel',
    texture_width: 4,
    texture_height: 4,
    groups: [],
    elements: [],
    textures: [],
    animations: [],
    selected_elements: [],
  };
  let nextTextureId = 0;
  let pendingUndo = null;

  class Cube {
    static all = [];
  }

  class Texture {
    static all = project.textures;

    constructor(data = {}) {
      nextTextureId += 1;
      this.uuid = data.uuid || `tex-${nextTextureId}`;
      this.id = data.id || String(nextTextureId - 1);
      this.name = data.name || `${this.uuid}.png`;
      this.width = data.width || 4;
      this.height = data.height || 4;
      this.internal = true;
      this.layers_enabled = false;
      this.saved = false;
      this.canvas = {};
      this.ctx = makeContext(this.width, this.height, data.initial || [9, 9, 9, 255], events);
      this.source = this.getDataURL();
      this.updateCalls = 0;
    }

    getDataURL() {
      return `data:image/mock;base64,${Buffer.from(this.ctx.pixels).toString('base64')}`;
    }

    fromDataURL(dataUrl) {
      const encoded = String(dataUrl).split(',').pop();
      const decoded = Buffer.from(encoded, 'base64');
      if (decoded.length !== this.ctx.pixels.length) throw new Error('mock texture dimensions do not match staged bitmap');
      this.ctx.pixels.set(decoded);
      this.source = this.getDataURL();
      this.internal = true;
      this.saved = false;
      return this;
    }

    getUndoCopy(bitmap) {
      return {
        uuid: this.uuid,
        source: this.source,
        image_data: bitmap === true ? this.getDataURL() : undefined,
      };
    }

    add() {
      if (!Texture.all.includes(this)) Texture.all.push(this);
      return this;
    }

    updateChangesAfterEdit() {
      this.updateCalls += 1;
      this.source = this.getDataURL();
    }
  }

  const Undo = {
    initEdit(aspects) {
      events.push(['undo.begin', aspects]);
      pendingUndo = (aspects.textures || []).map((texture) => ({
        texture,
        copy: texture.getUndoCopy(aspects.bitmap === true),
      }));
    },
    finishEdit(label, aspects) {
      events.push(['undo.finish', label, aspects]);
    },
    cancelEdit(revert) {
      events.push(['undo.cancel', revert]);
      if (revert === true && pendingUndo) this.undo();
    },
    undo() {
      events.push(['undo.apply']);
      for (const entry of pendingUndo || []) {
        if (entry.copy.image_data) entry.texture.fromDataURL(entry.copy.image_data);
      }
    },
  };

  const bb = {Blockbench: {Project: project, isWeb: false}, Cube, Texture, Undo};
  const left = new Texture({uuid: 'tex-left', name: 'left.png'}).add();
  const right = new Texture({uuid: 'tex-right', name: 'right.png'}).add();
  const adapter = createBlockbenchUvTextureAdapter(bb);
  return {bb, project, adapter, left, right, events};
}

function pixel(texture, x, y) {
  const offset = (y * texture.width + x) * 4;
  return Array.from(texture.ctx.pixels.slice(offset, offset + 4));
}

function setPixel(texture, x, y, rgba) {
  const offset = (y * texture.width + x) * 4;
  texture.ctx.pixels.set(rgba, offset);
  texture.source = texture.getDataURL();
}

test('PR4 texture validation acceptance covers size, external path, and unresolved face texture', () => {
  const result = toolkit.validateProject({
    name: 'texture_validation_acceptance',
    save_path: '/tmp/texture_validation_acceptance.bbmodel',
    groups: [],
    elements: [{
      name: 'body',
      uuid: 'cube-body',
      from: [0, 0, 0],
      to: [1, 1, 1],
      origin: [0, 0, 0],
      parent: null,
      faces: {north: {enabled: true, texture: 'missing-texture', uv: [0, 0, 1, 1]}},
    }],
    textures: [{
      name: 'external.png',
      uuid: 'tex-external',
      width: 0,
      height: 16,
      internal: false,
      path: '',
    }],
    animations: [],
  }, {});

  const codes = new Set(result.errors.map((entry) => entry.code));
  assert.equal(codes.has('INVALID_TEXTURE_SIZE'), true);
  assert.equal(codes.has('MISSING_EXTERNAL_TEXTURE_PATH'), true);
  assert.equal(codes.has('MISSING_FACE_TEXTURE'), true);
});

test('texture compare reports an exact deterministic alpha-aware visual diff without mutation', () => {
  const env = mockBlockbench();
  setPixel(env.right, 2, 1, [9, 9, 9, 128]);
  env.events.length = 0;
  const beforeRevision = env.adapter.getRevision();

  assert.equal(typeof env.adapter.compareTextures, 'function');
  const result = env.adapter.compareTextures({leftTextureId: 'tex-left', rightTextureId: 'tex-right'});

  assert.deepEqual(result, {
    ok: true,
    projectRevision: beforeRevision,
    leftTextureId: 'tex-left',
    rightTextureId: 'tex-right',
    leftDimensions: {width: 4, height: 4},
    rightDimensions: {width: 4, height: 4},
    dimensionsEqual: true,
    equal: false,
    comparedPixels: 16,
    changedPixels: 1,
    changedBounds: {x: 2, y: 1, width: 1, height: 1},
  });
  assert.equal(env.adapter.getRevision(), beforeRevision);
  assert.equal(env.events.filter(([kind]) => kind === 'getImageData').length, 2);
  assert.equal(env.events.some(([kind]) => kind === 'putImageData'), false);
  assert.equal(env.events.some(([kind]) => kind.startsWith('undo.')), false);
});

test('edited texture survives staging and re-import with semantic pixel equality', () => {
  const env = mockBlockbench();
  const beforeRevision = env.adapter.getRevision();
  const operation = {
    type: 'texture_paint_region',
    textureId: 'tex-left',
    region: {x: 1, y: 1, width: 1, height: 1},
    pixels: [[20, 40, 60, 128]],
  };
  applyUvTextureBatch(env.adapter, {
    expectedRevision: beforeRevision,
    label: 'PR4 round-trip edit',
    operations: [operation],
  });
  assert.deepEqual(pixel(env.left, 1, 1), [20, 40, 60, 128]);

  const staged = env.left.getDataURL();
  const reimported = new env.bb.Texture({uuid: 'tex-reimported', name: 'reimported.png', width: 4, height: 4})
    .fromDataURL(staged)
    .add(false, true);
  assert.equal(reimported.internal, true);

  assert.equal(typeof env.adapter.compareTextures, 'function');
  const comparison = env.adapter.compareTextures({leftTextureId: 'tex-left', rightTextureId: 'tex-reimported'});
  assert.equal(comparison.equal, true);
  assert.equal(comparison.dimensionsEqual, true);
  assert.equal(comparison.comparedPixels, 16);
  assert.equal(comparison.changedPixels, 0);
  assert.equal(comparison.changedBounds, null);
});

test('bitmap-aware PR4 transaction is sufficient for audited Blockbench Undo bitmap restoration', () => {
  const env = mockBlockbench();
  const before = pixel(env.left, 0, 0);
  const beforeRevision = env.adapter.getRevision();

  applyUvTextureBatch(env.adapter, {
    expectedRevision: beforeRevision,
    label: 'PR4 Undo acceptance',
    operations: [{
      type: 'texture_paint_region',
      textureId: 'tex-left',
      region: {x: 0, y: 0, width: 1, height: 1},
      pixels: [[200, 100, 50, 64]],
    }],
  });
  assert.deepEqual(pixel(env.left, 0, 0), [200, 100, 50, 64]);

  const begin = env.events.find(([kind]) => kind === 'undo.begin');
  const finish = env.events.find(([kind]) => kind === 'undo.finish');
  assert.equal(begin[1].bitmap, true);
  assert.deepEqual(begin[1].textures, [env.left]);
  assert.equal(finish[2].bitmap, true);

  env.bb.Undo.undo();
  assert.deepEqual(pixel(env.left, 0, 0), before);
});
