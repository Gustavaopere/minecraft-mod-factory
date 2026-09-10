const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const toolkit = require('./asset_toolkit.js');
const projectModel = require('./core/project-model/project_model.js');
const validator = require('./core/validator/validator.js');
const contractProfile = require('./core/contract-profile/contract_profile.js');
const bundleBuilder = require('./build_toolkit_bundle.js');

const ROOT = __dirname;

function fixture() {
  return {
    name: 'modular_fixture',
    save_path: '/tmp/modular_fixture.bbmodel',
    groups: [{name: 'root', uuid: 'root-uuid', origin: [0, 0, 0], parent: null, children: []}],
    elements: [{
      name: 'body', uuid: 'body-uuid', from: [-1, 0, -1], to: [1, 4, 1], origin: [0, 2, 0],
      parent: {name: 'root', uuid: 'root-uuid'},
      faces: {north: {enabled: true, texture: 'main-texture', uv: [0, 0, 2, 4]}},
    }],
    textures: [{name: 'main.png', uuid: 'main-texture', width: 16, height: 16}],
    animations: [{name: 'animation.modular_fixture.idle', uuid: 'idle', length: 1, loop: 'loop', animators: {'root-uuid': {}}}],
  };
}

test('modular project-model predicates and bounds preserve the compatibility entrypoint behavior', () => {
  const cube = fixture().elements[0];
  assert.equal(projectModel.isCubeLike(cube), toolkit.isCubeLike(cube));
  assert.equal(projectModel.isLocatorLike(cube), toolkit.isLocatorLike(cube));
  assert.deepEqual(projectModel.computeBounds([cube]), toolkit.computeBounds([cube]));
});

test('modular validator is behaviorally identical to the compatibility entrypoint for structural QA', () => {
  const clean = fixture();
  assert.deepEqual(validator.validateProject(clean, {}), toolkit.validateProject(clean, {}));

  const broken = fixture();
  broken.elements[0].faces.north.texture = 'missing';
  assert.deepEqual(validator.validateProject(broken, {}), toolkit.validateProject(broken, {}));
});

test('contract-profile parser preserves the existing public parsing contract', () => {
  const source = '{"requiredBones":["root"],"maxSpan":[16,32,16]}';
  assert.deepEqual(contractProfile.parseProfileJson(source), toolkit.parseProfileJson(source));
  assert.throws(() => contractProfile.parseProfileJson('[]'), /Profile must be a JSON object/);
});

test('provider and extension schemas are strict machine-readable contracts', () => {
  const providerSchema = JSON.parse(fs.readFileSync(path.join(ROOT, 'core/provider-profile/provider-profile.schema.json'), 'utf8'));
  const extensionSchema = JSON.parse(fs.readFileSync(path.join(ROOT, 'core/extension-registry/extension.schema.json'), 'utf8'));

  assert.equal(providerSchema.additionalProperties, false);
  assert.equal(extensionSchema.additionalProperties, false);
  for (const key of ['id', 'family', 'authority', 'capabilities', 'requiredExtensions']) assert.ok(providerSchema.required.includes(key), `provider schema missing ${key}`);
  for (const key of ['pluginId', 'pluginVersion', 'classification', 'mcpPolicy']) assert.ok(extensionSchema.required.includes(key), `extension schema missing ${key}`);
});

test('standalone compatibility bundle keeps every old export and adds registry read APIs only', () => {
  for (const key of ['validateProject', 'formatReport', 'parseProfileJson', 'registerBlockbenchPlugin', 'computeBounds', 'isCubeLike', 'isLocatorLike']) {
    assert.equal(typeof toolkit[key], 'function', `missing legacy export ${key}`);
  }
  for (const key of ['getExtensionDefinition', 'evaluateExtension', 'listProviderProfiles', 'getProviderProfile', 'resolveProviderProfile', 'canConvertProfile']) {
    assert.equal(typeof toolkit[key], 'function', `missing registry export ${key}`);
  }
  assert.equal(typeof toolkit.CURRENT_PHYSICAL_PROVIDER_SNAPSHOT, 'object');
  assert.ok(Array.isArray(toolkit.EXTENSION_STATES));

  for (const forbidden of ['executeScript', 'installArbitraryExtension', 'loadExtensionUrl', 'executeExtensionActionByName']) {
    assert.equal(Object.prototype.hasOwnProperty.call(toolkit, forbidden), false, `forbidden mutation surface exposed: ${forbidden}`);
  }
});

test('committed standalone Blockbench plugin is generated exactly from modular sources', () => {
  const committed = fs.readFileSync(path.join(ROOT, 'asset_toolkit.js'), 'utf8');
  assert.equal(bundleBuilder.buildBundle(), committed);
});
