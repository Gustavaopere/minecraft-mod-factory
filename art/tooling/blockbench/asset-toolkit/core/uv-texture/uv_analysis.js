'use strict';

const {normalizeTextureRef, normalizedName} = require('../project-model/project_model.js');

const FACE_AXES = Object.freeze({
  north: [0, 1],
  south: [0, 1],
  east: [2, 1],
  west: [2, 1],
  up: [0, 2],
  down: [0, 2],
});

function compareText(left, right) { return String(left).localeCompare(String(right), 'en', {sensitivity: 'variant', numeric: false}); }

function issue(code, message, context) {
  return Object.freeze({severity: 'error', code, message, context: context || null});
}

function finiteVec3(value) {
  return Array.isArray(value) && value.length >= 3 && value.slice(0, 3).every(Number.isFinite);
}

function normalizeUv(value) {
  if (!Array.isArray(value) || value.length < 4 || !value.slice(0, 4).every(Number.isFinite)) return null;
  const [u1, v1, u2, v2] = value;
  return Object.freeze([Math.min(u1, u2), Math.min(v1, v2), Math.max(u1, u2), Math.max(v1, v2)]);
}

function uvArea(uv) {
  return (uv[2] - uv[0]) * (uv[3] - uv[1]);
}

function modelFaceArea(element, face) {
  const axes = FACE_AXES[face];
  if (!axes || !finiteVec3(element?.from) || !finiteVec3(element?.to)) return null;
  const size = [0, 1, 2].map((axis) => Math.abs(element.to[axis] - element.from[axis]));
  return size[axes[0]] * size[axes[1]];
}

function textureRefs(textures) {
  const refs = new Set();
  for (const texture of textures) {
    const uuid = normalizedName(texture?.uuid);
    const name = normalizedName(texture?.name);
    if (uuid) refs.add(uuid);
    if (name) refs.add(name);
  }
  return refs;
}

function faceKey(face) {
  return `${face.textureRef}\u0000${face.cubeId}\u0000${face.face}`;
}

function overlapArea(a, b) {
  const width = Math.min(a.uv[2], b.uv[2]) - Math.max(a.uv[0], b.uv[0]);
  const height = Math.min(a.uv[3], b.uv[3]) - Math.max(a.uv[1], b.uv[1]);
  return width > 0 && height > 0 ? width * height : 0;
}

function densitySummary(faces) {
  const values = faces.map((face) => face.texelDensity);
  if (!values.length) return Object.freeze({count: 0, min: null, max: null, mean: null});
  const sum = values.reduce((total, value) => total + value, 0);
  return Object.freeze({count: values.length, min: Math.min(...values), max: Math.max(...values), mean: sum / values.length});
}

function analyzeUvLayout(project) {
  const input = project && typeof project === 'object' ? project : {};
  const textures = Array.isArray(input.textures) ? input.textures : [];
  const elements = Array.isArray(input.elements) ? input.elements : [];
  const knownTextures = textureRefs(textures);
  const faces = [];
  const issues = [];

  for (const element of elements) {
    const elementFaces = element?.faces && typeof element.faces === 'object' ? element.faces : {};
    const cubeId = normalizedName(element?.uuid) || normalizedName(element?.name) || '<unnamed>';
    const cubeName = normalizedName(element?.name) || '<unnamed>';

    for (const faceName of Object.keys(elementFaces).sort(compareText)) {
      const face = elementFaces[faceName];
      if (!face || face.enabled === false) continue;
      const context = Object.freeze({cubeId, face: faceName});
      const uv = normalizeUv(face.uv);
      if (!uv) {
        issues.push(issue('INVALID_FACE_UV', `Cube "${cubeName}" face "${faceName}" has malformed UV coordinates.`, context));
        continue;
      }

      const textureRef = normalizeTextureRef(face.texture);
      if (!textureRef || !knownTextures.has(textureRef)) {
        issues.push(issue('UNRESOLVED_FACE_TEXTURE', `Cube "${cubeName}" face "${faceName}" has an unresolved texture reference.`, context));
        continue;
      }

      const modelArea = modelFaceArea(element, faceName);
      if (modelArea === null) {
        issues.push(issue('INVALID_CUBE_BOUNDS', `Cube "${cubeName}" face "${faceName}" cannot be measured from malformed bounds.`, context));
        continue;
      }
      if (modelArea <= 0) {
        issues.push(issue('ZERO_FACE_MODEL_AREA', `Cube "${cubeName}" face "${faceName}" has zero model-space area.`, context));
        continue;
      }

      const area = uvArea(uv);
      if (area <= 0) {
        issues.push(issue('ZERO_FACE_UV_AREA', `Cube "${cubeName}" face "${faceName}" has zero UV area.`, context));
        continue;
      }

      faces.push(Object.freeze({
        cubeId,
        cubeName,
        face: faceName,
        textureRef,
        uv,
        uvArea: area,
        modelArea,
        texelDensity: Math.sqrt(area / modelArea),
      }));
    }
  }

  faces.sort((a, b) => faceKey(a).localeCompare(faceKey(b), 'en', {sensitivity: 'variant', numeric: false}));
  const overlaps = [];
  for (let left = 0; left < faces.length; left += 1) {
    for (let right = left + 1; right < faces.length; right += 1) {
      const a = faces[left];
      const b = faces[right];
      if (a.textureRef !== b.textureRef) continue;
      const area = overlapArea(a, b);
      if (area <= 0) continue;
      overlaps.push(Object.freeze({
        textureRef: a.textureRef,
        area,
        a: Object.freeze({cubeId: a.cubeId, face: a.face}),
        b: Object.freeze({cubeId: b.cubeId, face: b.face}),
      }));
    }
  }

  return Object.freeze({
    faces: Object.freeze(faces.slice()),
    overlaps: Object.freeze(overlaps),
    density: densitySummary(faces),
    issues: Object.freeze(issues),
  });
}

module.exports = {analyzeUvLayout};
