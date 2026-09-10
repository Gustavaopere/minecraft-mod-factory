const test = require('node:test');
const assert = require('node:assert/strict');
const toolkit = require('./asset_toolkit.js');

function project(overrides = {}) {
  return {
    name: 'golden_asset', save_path: '/tmp/golden_asset.bbmodel',
    groups: [
      {name: 'root', uuid: 'bone-root', origin: [0, 0, 0], parent: null, children: []},
      {name: 'vfx_anchor', uuid: 'bone-vfx', origin: [0, 8, 0], parent: null, children: []},
    ],
    elements: [{name: 'body', uuid: 'cube-body', from: [-2, 0, -2], to: [2, 8, 2], origin: [0, 4, 0], parent: {uuid: 'bone-root', name: 'root'}, faces: {north: {enabled: true, texture: 'tex-main', uv: [0,0,4,8]}}}],
    textures: [{name: 'golden_asset.png', uuid: 'tex-main', width: 64, height: 64}],
    animations: [{name: 'animation.golden_asset.idle', uuid: 'anim-idle', length: 1, loop: 'loop', animators: {'bone-root': {}}}],
    ...overrides,
  };
}

test('clean project passes structural validation', () => { assert.equal(toolkit.validateProject(project(), {}).errors.length, 0); });
test('duplicate bone names are errors', () => { const p = project(); p.groups.push({name: 'ROOT', uuid: 'bone-dup', origin: [0,0,0], parent: null, children: []}); assert.ok(toolkit.validateProject(p, {}).errors.some((i) => i.code === 'DUPLICATE_BONE_NAME')); });
test('bone parent cycles are errors', () => { const a = {name: 'a', uuid: 'a', origin: [0,0,0], children: []}; const b = {name: 'b', uuid: 'b', origin: [0,0,0], children: []}; a.parent = b; b.parent = a; assert.ok(toolkit.validateProject(project({groups: [a,b]}), {}).errors.some((i) => i.code === 'BONE_PARENT_CYCLE')); });
test('enabled face referencing missing texture is an error', () => { const p = project(); p.elements[0].faces.north.texture = 'missing-texture'; assert.ok(toolkit.validateProject(p, {}).errors.some((i) => i.code === 'MISSING_FACE_TEXTURE')); });
test('contract profile enforces required bones and animations', () => { const result = toolkit.validateProject(project(), {requiredBones: ['root', 'weapon_socket'], requiredAnimations: ['animation.golden_asset.idle', 'animation.golden_asset.attack']}); assert.ok(result.errors.some((i) => i.code === 'MISSING_REQUIRED_BONE')); assert.ok(result.errors.some((i) => i.code === 'MISSING_REQUIRED_ANIMATION')); });
test('contract profile enforces maximum span without a universal hardcoded budget', () => { assert.ok(toolkit.validateProject(project(), {maxSpan: [3, 16, 16]}).errors.some((i) => i.code === 'MODEL_SPAN_EXCEEDED')); });
test('known animation target uuids are accepted and unknown targets warn', () => { const p = project(); p.animations[0].animators['ghost-bone'] = {}; assert.ok(toolkit.validateProject(p, {}).warnings.some((i) => i.code === 'UNKNOWN_ANIMATOR_TARGET')); });
test('locator-only projects do not receive cube bounds or texture errors', () => {
  const locator = {name: 'vfx_locator', uuid: 'locator-vfx', from: [0, 8, 0], parent: {uuid: 'bone-vfx', name: 'vfx_anchor'}};
  const result = toolkit.validateProject(project({elements: [locator], textures: []}), {});
  for (const code of ['INVALID_ELEMENT_BOUNDS', 'NO_TEXTURES', 'MISSING_FACE_TEXTURE']) {
    assert.equal(result.errors.some((item) => item.code === code), false, `unexpected ${code}`);
  }
});
test('malformed locator positions are reported separately from cube bounds', () => {
  const locator = {name: 'bad_locator', uuid: 'locator-bad', from: [0, Number.NaN, 0], parent: {uuid: 'bone-vfx', name: 'vfx_anchor'}};
  const result = toolkit.validateProject(project({elements: [locator], textures: []}), {});
  assert.ok(result.errors.some((item) => item.code === 'INVALID_LOCATOR_POSITION'));
  assert.equal(result.errors.some((item) => item.code === 'INVALID_ELEMENT_BOUNDS'), false);
});

require('./asset_toolkit.registry.test.js');
require('./asset_toolkit.modular.test.js');
require('./asset_toolkit.provider_expansion.test.js');
require('./asset_toolkit.live_bridge.test.js');
require('./asset_toolkit.mcp_sidecar.test.js');
require('./asset_toolkit.bundle_live_bridge.test.js');
require('./asset_toolkit.blockbench_adapter.test.js');
require('./asset_toolkit.mutations.test.js');
require('./asset_toolkit.locator_native.test.js');
require('./asset_toolkit.uv_texture_revision.test.js');
require('./asset_toolkit.uv_texture_adapter.test.js');
require('./asset_toolkit.uv_texture.test.js');
require('./asset_toolkit.uv_analysis.test.js');
require('./asset_toolkit.texture_path.test.js');
require('./asset_toolkit.uv_pack.test.js');
require('./asset_toolkit.texture_create_import.test.js');
require('./asset_toolkit.texture_create_import_adapter.test.js');
require('./asset_toolkit.texture_paint_region.test.js');
require('./asset_toolkit.uv_island_masks.test.js');
require('./asset_toolkit.palette_sampling.test.js');
