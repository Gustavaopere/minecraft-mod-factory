'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const {
  MAX_TEXTURE_PIXELS_PER_BATCH,
  applyUvTextureBatch,
} = require('./core/uv-texture/uv_texture_engine.js');
const {
  createBlockbenchUvTextureAdapter,
} = require('./blockbench-plugin/uv_texture_adapter.js');

function mockBlockbench() {
  const events = [];
  const project = {
    name: 'texture_create_import',
    format: {id: 'free'},
    groups: [],
    elements: [],
    textures: [],
    animations: [],
    selected_elements: [],
    texture_width: 16,
    texture_height: 16,
  };
  let nextTextureId = 0;

  class Cube {
    static all = [];
  }

  class Texture {
    static all = project.textures;

    constructor(data = {}) {
      nextTextureId += 1;
      this.uuid = `tex-${nextTextureId}`;
      this.id = String(nextTextureId - 1);
      this.name = data.name || '';
      this.width = 0;
      this.height = 0;
      this.internal = data.internal !== false;
      this.layers_enabled = false;
      this.source = '';
      this.saved = false;
      this.canvas = {
        width: 16,
        height: 16,
        toDataURL() {
          return `data:image/png;base64,blank-${this.width}x${this.height}`;
        },
      };
      this.ctx = {
        clearRect(x, y, width, height) { events.push(['clearRect', x, y, width, height]); },
        getImageData() { return {data: new Uint8ClampedArray(4), width: 1, height: 1}; },
        putImageData() {},
      };
    }

    fromDataURL(dataUrl) {
      events.push(['fromDataURL', this.uuid, dataUrl]);
      this.source = dataUrl;
      this.internal = true;
      this.width = this.canvas.width;
      this.height = this.canvas.height;
      return this;
    }

    fromFile(file) {
      events.push(['fromFile', this.uuid, file]);
      this.name = file.name;
      this.source = typeof file.content === 'string' ? file.content : '';
      this.internal = true;
      return this;
    }

    add(undo, uvSizeFromResolution) {
      events.push(['texture.add', this.uuid, undo, uvSizeFromResolution]);
      if (!Texture.all.includes(this)) Texture.all.push(this);
      return this;
    }

    updateChangesAfterEdit() {
      events.push(['texture.update', this.uuid]);
    }
  }

  const Undo = {
    initEdit(aspects) { events.push(['undo.begin', aspects]); },
    finishEdit(label, aspects) { events.push(['undo.finish', label, aspects]); },
    cancelEdit(revert) { events.push(['undo.cancel', revert]); },
  };

  return {
    Blockbench: {Project: project, isWeb: false},
    Cube,
    Texture,
    Undo,
    project,
    events,
  };
}

function batch(expectedRevision, operations, dryRun = false) {
  return {
    expectedRevision,
    label: 'Texture Create/Import Adapter',
    dryRun,
    operations,
  };
}

test('Blockbench adapter registers approved local texture files behind opaque ids', () => {
  const bb = mockBlockbench();
  const adapter = createBlockbenchUvTextureAdapter(bb);
  assert.equal(typeof adapter.approveTextureImport, 'function');

  const file = {
    name: 'approved.png',
    path: '/private/user/approved.png',
    content: 'data:image/png;base64,approved',
  };
  const approvalId = adapter.approveTextureImport(file, {width: 8, height: 8});

  assert.equal(typeof approvalId, 'string');
  assert.ok(approvalId.length > 0);
  assert.equal(approvalId.includes(file.path), false);
  assert.equal(approvalId.includes(file.name), false);

  assert.throws(
    () => adapter.preflight([{type: 'texture_import_approved', approvalId: 'missing-approval'}]),
    /TEXTURE_IMPORT_APPROVAL_NOT_FOUND/,
  );
});

test('dry-run preserves approval and real apply creates/imports textures in one Undo transaction', () => {
  const bb = mockBlockbench();
  const adapter = createBlockbenchUvTextureAdapter(bb);
  const file = {
    name: 'approved.png',
    path: '/private/user/approved.png',
    content: 'data:image/png;base64,approved',
  };
  const approvalId = adapter.approveTextureImport(file, {width: 8, height: 8});
  const operations = [
    {type: 'texture_create', name: 'created.png', width: 16, height: 16},
    {type: 'texture_import_approved', approvalId},
  ];

  const before = adapter.getRevision();
  const preview = applyUvTextureBatch(adapter, batch(before, operations, true));
  assert.equal(preview.dryRun, true);
  assert.equal(bb.project.textures.length, 0);
  assert.equal(bb.events.some(([kind]) => kind === 'undo.begin'), false);

  const result = applyUvTextureBatch(adapter, batch(before, operations));
  assert.equal(result.ok, true);
  assert.equal(result.applied, 2);
  assert.equal(bb.project.textures.length, 2);
  assert.deepEqual(bb.project.textures.map((texture) => texture.name), ['created.png', 'approved.png']);
  assert.deepEqual([bb.project.textures[0].width, bb.project.textures[0].height], [16, 16]);
  assert.equal(bb.project.textures[0].internal, true);
  assert.match(bb.project.textures[0].source, /^data:image\/png;base64,blank-16x16$/);
  assert.equal(bb.events.filter(([kind]) => kind === 'fromFile').length, 1);
  assert.equal(bb.events.filter(([kind]) => kind === 'texture.add').length, 2);
  assert.equal(bb.events.filter(([kind]) => kind === 'undo.begin').length, 1);
  assert.equal(bb.events.filter(([kind]) => kind === 'undo.finish').length, 1);
  assert.notEqual(result.afterRevision, before);

  const finish = bb.events.find(([kind]) => kind === 'undo.finish');
  assert.deepEqual(finish[2].textures, bb.project.textures);

  assert.throws(
    () => adapter.preflight([{type: 'texture_import_approved', approvalId}]),
    /TEXTURE_IMPORT_APPROVAL_NOT_FOUND/,
  );
});

test('create/import preflight rejects texture-name collisions and oversized approved imports', () => {
  const bb = mockBlockbench();
  const existing = new bb.Texture({name: 'Existing.PNG'}).fromDataURL('data:image/png;base64,existing').add(false, true);
  existing.width = 16;
  existing.height = 16;
  const adapter = createBlockbenchUvTextureAdapter(bb);

  assert.throws(
    () => adapter.preflight([{type: 'texture_create', name: 'existing.png', width: 16, height: 16}]),
    /TEXTURE_NAME_COLLISION/,
  );

  assert.throws(
    () => adapter.approveTextureImport(
      {name: 'huge.png', path: '/private/user/huge.png'},
      {width: MAX_TEXTURE_PIXELS_PER_BATCH + 1, height: 1},
    ),
    /TEXTURE_PIXEL_BUDGET_EXCEEDED/,
  );
});
