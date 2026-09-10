'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const {createProjectSnapshot} = require('./live-bridge/project_snapshot.js');

function project({boxUv = false, uvOffset = [0, 0], source = 'data:image/png;base64,AAAA'} = {}) {
  return {
    name: 'uv_revision_asset',
    format: {id: 'free'},
    groups: [],
    animations: [],
    selected_elements: [],
    elements: [{
      name: 'cube',
      uuid: 'cube-1',
      from: [0, 0, 0],
      to: [1, 1, 1],
      origin: [0, 0, 0],
      parent: null,
      box_uv: boxUv,
      uv_offset: uvOffset,
      faces: {north: {enabled: true, texture: 'tex-1', uv: [0, 0, 1, 1]}},
    }],
    textures: [{
      name: 'texture.png',
      uuid: 'tex-1',
      width: 16,
      height: 16,
      internal: true,
      source,
    }],
  };
}

test('project revision changes when cube Box UV mode or offset changes', () => {
  const before = createProjectSnapshot(project()).projectRevision;
  const after = createProjectSnapshot(project({boxUv: true, uvOffset: [4, 8]})).projectRevision;
  assert.notEqual(before, after);
});

test('project revision changes with internal texture content without exposing source bytes', () => {
  const before = createProjectSnapshot(project());
  const after = createProjectSnapshot(project({source: 'data:image/png;base64,BBBB'}));
  assert.notEqual(before.projectRevision, after.projectRevision);
  assert.equal(JSON.stringify(before).includes('AAAA'), false);
});
