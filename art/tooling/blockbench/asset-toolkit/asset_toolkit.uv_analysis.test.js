'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const toolkit = require('./core/index.js');

function requireAnalyzer() {
  assert.equal(typeof toolkit.analyzeUvLayout, 'function', 'analyzeUvLayout must be exported by the core');
  return toolkit.analyzeUvLayout;
}

function texture(uuid = 'tex-main', name = 'main.png', width = 64, height = 64) {
  return {uuid, name, width, height};
}

function cube({uuid, name, from, to, faces}) {
  return {uuid, name, from, to, faces};
}

test('UV analysis reports normalized per-face inspection data and texel density', () => {
  const analyzeUvLayout = requireAnalyzer();
  const result = analyzeUvLayout({
    textures: [texture()],
    elements: [cube({
      uuid: 'cube-a',
      name: 'body',
      from: [0, 0, 0],
      to: [4, 4, 4],
      faces: {north: {enabled: true, texture: 'tex-main', uv: [8, 8, 0, 0]}},
    })],
  });

  assert.equal(result.faces.length, 1);
  assert.deepEqual(result.faces[0], {
    cubeId: 'cube-a',
    cubeName: 'body',
    face: 'north',
    textureRef: 'tex-main',
    uv: [0, 0, 8, 8],
    uvArea: 64,
    modelArea: 16,
    texelDensity: 2,
  });
  assert.deepEqual(result.density, {count: 1, min: 2, max: 2, mean: 2});
  assert.equal(result.issues.length, 0);
});

test('UV analysis reports positive-area overlaps per texture and ignores edge-only contact', () => {
  const analyzeUvLayout = requireAnalyzer();
  const result = analyzeUvLayout({
    textures: [texture()],
    elements: [
      cube({uuid: 'cube-a', name: 'a', from: [0,0,0], to: [4,8,2], faces: {north: {enabled: true, texture: '#tex-main', uv: [0,0,4,8]}}}),
      cube({uuid: 'cube-b', name: 'b', from: [0,0,0], to: [4,8,2], faces: {north: {enabled: true, texture: 'tex-main', uv: [2,0,6,8]}}}),
      cube({uuid: 'cube-c', name: 'c', from: [0,0,0], to: [4,8,2], faces: {north: {enabled: true, texture: 'tex-main', uv: [6,0,10,8]}}}),
    ],
  });

  assert.equal(result.overlaps.length, 1);
  assert.deepEqual(result.overlaps[0], {
    textureRef: 'tex-main',
    area: 16,
    a: {cubeId: 'cube-a', face: 'north'},
    b: {cubeId: 'cube-b', face: 'north'},
  });
});

test('UV analysis fails closed on malformed UV, unresolved texture refs, and zero model area', () => {
  const analyzeUvLayout = requireAnalyzer();
  const result = analyzeUvLayout({
    textures: [texture()],
    elements: [
      cube({uuid: 'bad-uv', name: 'bad_uv', from: [0,0,0], to: [4,4,4], faces: {north: {enabled: true, texture: 'tex-main', uv: [0,0,Number.NaN,4]}}}),
      cube({uuid: 'missing-texture', name: 'missing_texture', from: [0,0,0], to: [4,4,4], faces: {north: {enabled: true, texture: 'ghost', uv: [0,0,4,4]}}}),
      cube({uuid: 'zero-area', name: 'zero_area', from: [0,0,0], to: [0,4,4], faces: {north: {enabled: true, texture: 'tex-main', uv: [0,0,4,4]}}}),
    ],
  });

  assert.deepEqual(result.faces, []);
  assert.deepEqual(result.overlaps, []);
  assert.deepEqual(result.density, {count: 0, min: null, max: null, mean: null});
  assert.deepEqual(result.issues.map((item) => item.code), [
    'INVALID_FACE_UV',
    'UNRESOLVED_FACE_TEXTURE',
    'ZERO_FACE_MODEL_AREA',
  ]);
});
