'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const {
  MAX_MUTATION_OPERATIONS,
  validateMutationBatch,
  applyMutationBatch,
} = require('./core/mutations/mutation_engine.js');
const {createBlockbenchModelingAdapter} = require('./blockbench-plugin/modeling_adapter.js');

function fakeAdapter(overrides = {}) {
  let revision = 'rev:1';
  const events = [];
  return {
    events,
    getRevision() { return revision; },
    preflight(operations) { events.push(['preflight', operations.map((item) => item.type)]); },
    beginTransaction(label) { events.push(['begin', label]); },
    applyOperation(operation) {
      events.push(['apply', operation.type, operation.id || operation.targetId]);
      return operation.id || operation.targetId;
    },
    finishTransaction(label) { events.push(['finish', label]); revision = 'rev:2'; },
    cancelTransaction(revert) { events.push(['cancel', revert]); },
    ...overrides,
  };
}

function completeBatch(overrides = {}) {
  return {
    expectedRevision: 'rev:1',
    label: 'Build rig scaffold',
    operations: [
      {type: 'add_bone', id: 'bone-hand', name: 'hand', pivot: [0, 8, 0], parentId: 'root'},
      {type: 'add_cube', id: 'cube-focus', name: 'focus', from: [-1, 7, -1], to: [1, 9, 1], pivot: [0, 8, 0], parentId: 'bone-hand'},
      {type: 'add_locator', id: 'locator-vfx', name: 'spell_muzzle', position: [0, 9, 0], parentId: 'bone-hand'},
      {type: 'set_pivot', targetId: 'cube-focus', pivot: [0, 8.5, 0]},
      {type: 'rename', targetId: 'locator-vfx', name: 'spell_origin'},
      {type: 'reparent', targetId: 'locator-vfx', parentId: 'root'},
      {type: 'mirror', targetId: 'cube-focus', axis: 'x', center: 0},
    ],
    ...overrides,
  };
}

test('mutation contract accepts the bounded modeling and rig allowlist', () => {
  const parsed = validateMutationBatch(completeBatch());
  assert.equal(parsed.operations.length, 7);
  assert.deepEqual(parsed.operations.map((item) => item.type), [
    'add_bone', 'add_cube', 'add_locator', 'set_pivot', 'rename', 'reparent', 'mirror',
  ]);
  assert.equal(Object.isFrozen(parsed), true);
});

test('mutation contract rejects unknown operations, malformed vectors, extra fields and oversized batches', () => {
  assert.throws(() => validateMutationBatch(completeBatch({operations: [{type: 'delete_everything'}]})), /UNSUPPORTED_MUTATION/);
  assert.throws(() => validateMutationBatch(completeBatch({operations: [{type: 'add_bone', id: 'a', name: 'a', pivot: [0, NaN, 0], parentId: null}]})), /INVALID_VECTOR3/);
  assert.throws(() => validateMutationBatch({...completeBatch(), arbitraryScript: 'alert(1)'}), /UNKNOWN_BATCH_FIELD/);
  const operations = Array.from({length: MAX_MUTATION_OPERATIONS + 1}, (_, index) => ({
    type: 'add_bone', id: `b${index}`, name: `bone_${index}`, pivot: [0, 0, 0], parentId: null,
  }));
  assert.throws(() => validateMutationBatch(completeBatch({operations})), /MUTATION_BATCH_TOO_LARGE/);
});

test('stale expected revision fails before preflight or Undo transaction', () => {
  const adapter = fakeAdapter();
  assert.throws(
    () => applyMutationBatch(adapter, completeBatch({expectedRevision: 'rev:stale'})),
    /STALE_PROJECT_REVISION/,
  );
  assert.deepEqual(adapter.events, []);
});

test('a declarative batch preflights once and commits as one transaction', () => {
  const adapter = fakeAdapter();
  const result = applyMutationBatch(adapter, completeBatch());
  assert.equal(result.ok, true);
  assert.equal(result.beforeRevision, 'rev:1');
  assert.equal(result.afterRevision, 'rev:2');
  assert.equal(result.applied, 7);
  assert.deepEqual(result.changedIds, ['bone-hand', 'cube-focus', 'locator-vfx']);
  assert.equal(adapter.events.filter(([kind]) => kind === 'begin').length, 1);
  assert.equal(adapter.events.filter(([kind]) => kind === 'finish').length, 1);
  assert.equal(adapter.events.filter(([kind]) => kind === 'apply').length, 7);
  assert.equal(adapter.events.some(([kind]) => kind === 'cancel'), false);
});

test('adapter failure cancels and reverts the whole transaction', () => {
  const adapter = fakeAdapter({
    applyOperation(operation) {
      adapter.events.push(['apply', operation.type]);
      if (operation.type === 'add_locator') throw new Error('synthetic adapter failure');
      return operation.id || operation.targetId;
    },
  });
  assert.throws(() => applyMutationBatch(adapter, completeBatch()), /synthetic adapter failure/);
  assert.deepEqual(adapter.events.at(-1), ['cancel', true]);
  assert.equal(adapter.events.some(([kind]) => kind === 'finish'), false);
});

test('dry-run validates and preflights without opening an Undo transaction', () => {
  const adapter = fakeAdapter();
  const result = applyMutationBatch(adapter, completeBatch({dryRun: true}));
  assert.equal(result.ok, true);
  assert.equal(result.dryRun, true);
  assert.equal(result.beforeRevision, 'rev:1');
  assert.equal(result.afterRevision, 'rev:1');
  assert.equal(adapter.events.filter(([kind]) => kind === 'preflight').length, 1);
  assert.equal(adapter.events.some(([kind]) => ['begin', 'apply', 'finish', 'cancel'].includes(kind)), false);
});

function mockBlockbench() {
  let serial = 0;
  const rootChildren = [];
  const events = [];
  const project = {
    name: 'mutation_asset', save_path: '/tmp/mutation_asset.bbmodel', format: {id: 'free'},
    groups: [], elements: [], textures: [], animations: [], selected_elements: [],
  };

  function addToParent(node, parent) {
    if (node.parent && Array.isArray(node.parent.children)) node.parent.children = node.parent.children.filter((child) => child !== node);
    node.parent = parent || null;
    const list = parent && Array.isArray(parent.children) ? parent.children : rootChildren;
    if (!list.includes(node)) list.push(node);
    return node;
  }

  class Group {
    static all = project.groups;
    constructor(data = {}, uuid) {
      this.uuid = uuid || `group-${++serial}`;
      this.name = data.name || 'group';
      this.origin = Array.isArray(data.origin) ? data.origin.slice() : [0, 0, 0];
      this.rotation = [0, 0, 0];
      this.children = [];
      this.parent = null;
    }
    addTo(parent) { return addToParent(this, parent); }
    init() { if (!Group.all.includes(this)) Group.all.push(this); return this; }
    extend(data) { if (data.origin) this.origin = data.origin.slice(); return this; }
  }

  class Cube {
    static all = [];
    constructor(data = {}, uuid) {
      this.uuid = uuid || `cube-${++serial}`;
      this.name = data.name || 'cube';
      this.from = (data.from || [0, 0, 0]).slice();
      this.to = (data.to || [1, 1, 1]).slice();
      this.origin = (data.origin || [0, 0, 0]).slice();
      this.parent = null;
      this.flipCalls = [];
    }
    addTo(parent) { return addToParent(this, parent); }
    init() { if (!project.elements.includes(this)) project.elements.push(this); if (!Cube.all.includes(this)) Cube.all.push(this); return this; }
    extend(data) { if (data.origin) this.origin = data.origin.slice(); return this; }
    flip(axis, center, update) { this.flipCalls.push([axis, center, update]); return this; }
  }

  class Locator {
    static all = [];
    constructor(data = {}, uuid) {
      this.uuid = uuid || `locator-${++serial}`;
      this.name = data.name || 'locator';
      this.position = (data.position || [0, 0, 0]).slice();
      this.from = this.position;
      this.parent = null;
      this.flipCalls = [];
    }
    addTo(parent) { return addToParent(this, parent); }
    init() { if (!project.elements.includes(this)) project.elements.push(this); if (!Locator.all.includes(this)) Locator.all.push(this); return this; }
    flip(axis, center, update) { this.flipCalls.push([axis, center, update]); return this; }
  }

  const root = new Group({name: 'root', origin: [0, 0, 0]}, 'root').init();
  rootChildren.push(root);

  return {
    events,
    root,
    project,
    Blockbench: {Project: project, isWeb: false, version: '5.1.6'},
    Group,
    Cube,
    Locator,
    Outliner: {elements: project.elements, root: rootChildren},
    Undo: {
      initEdit(aspects) { events.push(['undo.begin', aspects]); },
      finishEdit(label) { events.push(['undo.finish', label]); },
      cancelEdit(revert) { events.push(['undo.cancel', revert]); },
    },
  };
}

test('Blockbench adapter creates bones, cubes and locators using one Undo-aware allowlisted surface', () => {
  const bb = mockBlockbench();
  const adapter = createBlockbenchModelingAdapter(bb);
  const before = adapter.getRevision();
  const batch = {
    expectedRevision: before,
    label: 'Create scaffold',
    operations: [
      {type: 'add_bone', id: 'hand', name: 'hand', pivot: [0, 8, 0], parentId: 'root'},
      {type: 'add_cube', id: 'focus', name: 'focus', from: [-1, 7, -1], to: [1, 9, 1], pivot: [0, 8, 0], parentId: 'hand'},
      {type: 'add_locator', id: 'muzzle', name: 'spell_muzzle', position: [0, 9, 0], parentId: 'hand'},
      {type: 'set_pivot', targetId: 'focus', pivot: [0, 8.5, 0]},
      {type: 'rename', targetId: 'muzzle', name: 'spell_origin'},
      {type: 'reparent', targetId: 'muzzle', parentId: 'root'},
      {type: 'mirror', targetId: 'focus', axis: 'x', center: 0},
    ],
  };
  const result = applyMutationBatch(adapter, batch);
  assert.equal(result.ok, true);
  assert.equal(bb.project.groups.some((group) => group.uuid === 'hand' && group.parent === bb.root), true);
  const cube = bb.project.elements.find((element) => element.uuid === 'focus');
  const locator = bb.project.elements.find((element) => element.uuid === 'muzzle');
  assert.deepEqual(cube.origin, [0, 8.5, 0]);
  assert.deepEqual(cube.flipCalls, [[0, 0, false]]);
  assert.equal(locator.name, 'spell_origin');
  assert.equal(locator.parent, bb.root);
  assert.equal(bb.events.filter(([kind]) => kind === 'undo.begin').length, 1);
  assert.equal(bb.events.filter(([kind]) => kind === 'undo.finish').length, 1);
  assert.notEqual(result.afterRevision, before);
});

test('Blockbench adapter preflight rejects duplicate ids, missing parents, self-parenting and group cycles', () => {
  const bb = mockBlockbench();
  const adapter = createBlockbenchModelingAdapter(bb);
  assert.throws(() => adapter.preflight([{type: 'add_bone', id: 'root', name: 'duplicate', pivot: [0,0,0], parentId: null}]), /DUPLICATE_NODE_ID/);
  assert.throws(() => adapter.preflight([{type: 'add_cube', id: 'x', name: 'x', from: [0,0,0], to: [1,1,1], pivot: [0,0,0], parentId: 'missing'}]), /PARENT_NOT_FOUND/);
  assert.throws(() => adapter.preflight([{type: 'reparent', targetId: 'root', parentId: 'root'}]), /INVALID_PARENT_CYCLE/);

  const child = new bb.Group({name: 'child'}, 'child').addTo(bb.root).init();
  const grandchild = new bb.Group({name: 'grandchild'}, 'grandchild').addTo(child).init();
  assert.throws(() => adapter.preflight([{type: 'reparent', targetId: 'root', parentId: grandchild.uuid}]), /INVALID_PARENT_CYCLE/);
});
