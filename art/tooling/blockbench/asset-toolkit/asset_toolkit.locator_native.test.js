'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const projectModel = require('./core/project-model/project_model.js');
const {validateProject} = require('./core/validator/validator.js');
const {createProjectSnapshot} = require('./live-bridge/project_snapshot.js');

function nativeLocatorProject(position = [0, 8, 0]) {
  const root = {name: 'root', uuid: 'root', origin: [0, 0, 0], parent: null, children: []};
  const locator = {name: 'spell_muzzle', uuid: 'locator-vfx', position: position.slice(), rotation: [0, 0, 0], parent: root};
  root.children.push(locator);
  return {
    name: 'native_locator_fixture',
    save_path: '/tmp/native_locator_fixture.bbmodel',
    format: {id: 'free'},
    groups: [root],
    elements: [locator],
    textures: [],
    animations: [],
    selected_elements: [],
  };
}

test('native Blockbench Locator.position is recognized as a locator while legacy from remains supported', () => {
  assert.equal(projectModel.isLocatorLike(nativeLocatorProject().elements[0]), true);
  assert.equal(projectModel.isLocatorLike({name: 'legacy', uuid: 'legacy', from: [1, 2, 3], parent: {uuid: 'root'}}), true);
});

test('native Locator.position takes precedence over legacy from when both fields exist', () => {
  const hybrid = {name: 'hybrid', uuid: 'hybrid', position: [0, Number.NaN, 0], from: [1, 2, 3], parent: {uuid: 'root'}};
  assert.deepEqual(projectModel.locatorPosition(hybrid), hybrid.position);
  const project = nativeLocatorProject();
  project.elements = [hybrid];
  const result = validateProject(project, {});
  assert.equal(result.counts.locatorCount, 1);
  assert.equal(result.errors.some((item) => item.code === 'INVALID_LOCATOR_POSITION'), true);
});

test('validator counts native position locators and validates their actual position', () => {
  const valid = validateProject(nativeLocatorProject(), {});
  assert.equal(valid.counts.locatorCount, 1);
  assert.equal(valid.errors.some((item) => item.code === 'INVALID_LOCATOR_POSITION'), false);

  const invalid = validateProject(nativeLocatorProject([0, Number.NaN, 0]), {});
  assert.equal(invalid.counts.locatorCount, 1);
  assert.equal(invalid.errors.some((item) => item.code === 'INVALID_LOCATOR_POSITION'), true);
});

test('project snapshot records native locator position and revision changes when it moves', () => {
  const before = createProjectSnapshot(nativeLocatorProject([0, 8, 0]));
  const after = createProjectSnapshot(nativeLocatorProject([0, 9, 0]));
  assert.deepEqual(before.elements[0].position, [0, 8, 0]);
  assert.notEqual(after.projectRevision, before.projectRevision);
});
