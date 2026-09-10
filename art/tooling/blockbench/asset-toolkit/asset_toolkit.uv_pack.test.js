'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const toolkit = require('./core/index.js');
const {createBlockbenchUvTextureAdapter} = require('./blockbench-plugin/uv_texture_adapter.js');

function targetState() {
  return {
    textureId: 'tex-main',
    pixelWidth: 16,
    pixelHeight: 16,
    uvWidth: 16,
    uvHeight: 16,
    faces: [
      {cubeId: 'cube-a', face: 'north', uv: [8, 0, 12, 4], boxUv: false},
      {cubeId: 'cube-b', face: 'south', uv: [0, 8, 4, 12], boxUv: false},
    ],
  };
}

function makeAdapter() {
  let revision = 'rev-1';
  const mutations = [];
  return {
    mutations,
    getRevision() {
      return revision;
    },
    inspectPackTarget(textureId) {
      assert.equal(textureId, 'tex-main');
      return targetState();
    },
    preflightPack(preview) {
      mutations.push(['preflight', preview.confirmationToken]);
      return true;
    },
    beginTransaction(label) {
      mutations.push(['begin', label]);
    },
    applyPack(preview) {
      mutations.push(['apply', preview.moves.length]);
      revision = 'rev-2';
      return ['tex-main', 'cube-a', 'cube-b'];
    },
    finishTransaction(label) {
      mutations.push(['finish', label]);
    },
    cancelTransaction(revert) {
      mutations.push(['cancel', revert]);
    },
  };
}

function pixelOffset(width, x, y) {
  return ((y * width) + x) * 4;
}

function paintRegion(pixels, width, x, y, regionWidth, regionHeight, rgba) {
  for (let py = y; py < y + regionHeight; py += 1) {
    for (let px = x; px < x + regionWidth; px += 1) {
      const offset = pixelOffset(width, px, py);
      pixels.set(rgba, offset);
    }
  }
}

function readPixel(pixels, width, x, y) {
  const offset = pixelOffset(width, x, y);
  return Array.from(pixels.slice(offset, offset + 4));
}

function blockbenchPackFixture() {
  class FakeCube {}
  class FakeTexture {}

  function face(textureId, uv) {
    return {
      enabled: true,
      texture: textureId,
      uv: uv.slice(),
      extend(patch) {
        if (patch.uv) this.uv = patch.uv.slice();
        if (patch.texture !== undefined) this.texture = patch.texture;
        return this;
      },
    };
  }

  const width = 16;
  const height = 16;
  const pixels = new Uint8ClampedArray(width * height * 4);
  paintRegion(pixels, width, 8, 0, 4, 4, [200, 0, 0, 255]);
  paintRegion(pixels, width, 0, 0, 4, 4, [0, 200, 0, 255]);

  const texture = new FakeTexture();
  Object.assign(texture, {
    uuid: 'tex-main',
    id: 'tex-main',
    name: 'main.png',
    width,
    height,
    layers_enabled: false,
    internal: false,
    canvas: {},
    changed: 0,
    updateChangesAfterEdit() { this.changed += 1; },
  });
  texture.ctx = {
    getImageData(x, y, regionWidth, regionHeight) {
      const data = new Uint8ClampedArray(regionWidth * regionHeight * 4);
      for (let py = 0; py < regionHeight; py += 1) {
        for (let px = 0; px < regionWidth; px += 1) {
          const source = pixelOffset(width, x + px, y + py);
          const target = ((py * regionWidth) + px) * 4;
          data.set(pixels.slice(source, source + 4), target);
        }
      }
      return {data, width: regionWidth, height: regionHeight};
    },
    putImageData(image, x, y) {
      for (let py = 0; py < image.height; py += 1) {
        for (let px = 0; px < image.width; px += 1) {
          const source = ((py * image.width) + px) * 4;
          const target = pixelOffset(width, x + px, y + py);
          pixels.set(image.data.slice(source, source + 4), target);
        }
      }
    },
  };

  const cubeA = new FakeCube();
  Object.assign(cubeA, {
    uuid: 'cube-a',
    name: 'Cube A',
    from: [0, 0, 0],
    to: [4, 4, 4],
    origin: [0, 0, 0],
    box_uv: false,
    faces: {north: face('tex-main', [8, 0, 12, 4])},
  });
  const cubeB = new FakeCube();
  Object.assign(cubeB, {
    uuid: 'cube-b',
    name: 'Cube B',
    from: [4, 0, 0],
    to: [8, 4, 4],
    origin: [0, 0, 0],
    box_uv: false,
    faces: {south: face('tex-main', [0, 0, 4, 4])},
  });

  FakeCube.all = [cubeA, cubeB];
  FakeTexture.all = [texture];
  const undoEvents = [];
  const project = {
    name: 'UV Pack Fixture',
    format: {id: 'java_block'},
    save_path: '/tmp/fixture.bbmodel',
    texture_width: width,
    texture_height: height,
    groups: [],
    elements: [cubeA, cubeB],
    textures: [texture],
    animations: [],
    selected_elements: [],
  };
  const bb = {
    Blockbench: {Project: project, isWeb: false},
    Cube: FakeCube,
    Texture: FakeTexture,
    Undo: {
      initEdit(aspects) { undoEvents.push(['begin', aspects]); },
      finishEdit(label, aspects) { undoEvents.push(['finish', label, aspects]); },
      cancelEdit(revert) { undoEvents.push(['cancel', revert]); },
    },
  };
  return {bb, pixels, cubeA, cubeB, texture, undoEvents, width};
}

test('UV pack preview is deterministic and apply requires its exact revision-bound confirmation token', () => {
  assert.equal(typeof toolkit.previewUvPack, 'function', 'previewUvPack must be exported by the core');
  assert.equal(typeof toolkit.applyUvPack, 'function', 'applyUvPack must be exported by the core');

  const adapter = makeAdapter();
  const request = {
    expectedRevision: 'rev-1',
    textureId: 'tex-main',
    scope: 'texture',
    padding: 1,
    label: 'Pack UV texture',
  };

  const preview = toolkit.previewUvPack(adapter, request);
  assert.deepEqual(toolkit.previewUvPack(adapter, request), preview, 'same state and request must produce the same preview');
  assert.equal(preview.ok, true);
  assert.equal(preview.dryRun, true);
  assert.equal(preview.beforeRevision, 'rev-1');
  assert.equal(preview.textureId, 'tex-main');
  assert.equal(preview.scope, 'texture');
  assert.deepEqual(preview.atlas, {width: 16, height: 16, padding: 1});
  assert.equal(preview.moves.length, 2);
  assert.ok(preview.moves.some((move) => !move.oldUv.every((value, index) => value === move.newUv[index])), 'preview must describe at least one UV change');
  for (const move of preview.moves) {
    assert.equal(move.sourcePixels.width, move.destinationPixels.width);
    assert.equal(move.sourcePixels.height, move.destinationPixels.height);
  }
  assert.equal(preview.copiedPixels, 32);
  assert.match(preview.confirmationToken, /^uvpack:v1:/);
  assert.deepEqual(adapter.mutations, [], 'preview must not mutate or open Undo');

  assert.throws(
    () => toolkit.applyUvPack(adapter, {...request, confirmationToken: 'uvpack:v1:wrong'}),
    (error) => error && error.code === 'UV_PACK_CONFIRMATION_MISMATCH',
  );
  assert.deepEqual(adapter.mutations, [], 'bad confirmation must fail before preflight or Undo');

  const applied = toolkit.applyUvPack(adapter, {...request, confirmationToken: preview.confirmationToken});
  assert.equal(applied.ok, true);
  assert.equal(applied.dryRun, false);
  assert.equal(applied.beforeRevision, 'rev-1');
  assert.equal(applied.afterRevision, 'rev-2');
  assert.equal(applied.applied, 2);
  assert.deepEqual(applied.changedIds, ['tex-main', 'cube-a', 'cube-b']);
  assert.deepEqual(adapter.mutations.map((entry) => entry[0]), ['preflight', 'begin', 'apply', 'finish']);
});

test('Blockbench UV pack adapter previews without mutation and buffers all source pixels before overlapping destinations are written', () => {
  const fixture = blockbenchPackFixture();
  const adapter = createBlockbenchUvTextureAdapter(fixture.bb);
  assert.equal(typeof adapter.inspectPackTarget, 'function', 'Blockbench adapter must expose inspectPackTarget');
  assert.equal(typeof adapter.preflightPack, 'function', 'Blockbench adapter must expose preflightPack');
  assert.equal(typeof adapter.applyPack, 'function', 'Blockbench adapter must expose applyPack');

  const beforeRevision = adapter.getRevision();
  const beforePixels = fixture.pixels.slice();
  const request = {
    expectedRevision: beforeRevision,
    textureId: 'tex-main',
    scope: 'texture',
    padding: 1,
    label: 'Pack UV texture',
  };
  const preview = toolkit.previewUvPack(adapter, request);

  assert.deepEqual(Array.from(fixture.pixels), Array.from(beforePixels), 'preview must not touch bitmap pixels');
  assert.deepEqual(fixture.cubeA.faces.north.uv, [8, 0, 12, 4], 'preview must not touch cube UVs');
  assert.deepEqual(fixture.cubeB.faces.south.uv, [0, 0, 4, 4], 'preview must not touch cube UVs');
  assert.equal(fixture.undoEvents.length, 0, 'preview must not open Undo');

  const result = toolkit.applyUvPack(adapter, {...request, confirmationToken: preview.confirmationToken});
  assert.equal(result.ok, true);
  assert.equal(result.dryRun, false);
  assert.notEqual(result.afterRevision, beforeRevision, 'UV changes must advance the project revision');
  assert.deepEqual(result.changedIds, ['tex-main', 'cube-a', 'cube-b']);
  assert.deepEqual(fixture.cubeA.faces.north.uv, [0, 0, 4, 4]);
  assert.deepEqual(fixture.cubeB.faces.south.uv, [5, 0, 9, 4]);
  assert.deepEqual(readPixel(fixture.pixels, fixture.width, 0, 0), [200, 0, 0, 255], 'first destination must receive cube A original pixels');
  assert.deepEqual(readPixel(fixture.pixels, fixture.width, 5, 0), [0, 200, 0, 255], 'second destination must receive cube B original pixels even though its source was overwritten earlier');
  assert.equal(fixture.texture.changed, 1, 'bitmap change publication must happen once');
  assert.deepEqual(fixture.undoEvents.map((entry) => entry[0]), ['begin', 'finish']);
});
