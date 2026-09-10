'use strict';

const MAX_UV_PACK_FACES = 128;
const MAX_UV_PACK_COPIED_PIXELS = 262144;
const FACES = new Set(['north', 'south', 'east', 'west', 'up', 'down']);

class UvPackContractError extends Error {
  constructor(code, message) {
    super(`${code}: ${message}`);
    this.name = 'UvPackContractError';
    this.code = code;
  }
}

function fail(code, message) {
  throw new UvPackContractError(code, message);
}

function isPlainObject(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return false;
  const prototype = Object.getPrototypeOf(value);
  return prototype === Object.prototype || prototype === null;
}

function boundedString(value, field, max = 160) {
  if (typeof value !== 'string') fail('INVALID_UV_PACK_REQUEST', `${field} must be a string.`);
  const output = value.trim();
  if (!output || output.length > max) fail('INVALID_UV_PACK_REQUEST', `${field} must contain 1-${max} non-whitespace characters.`);
  return output;
}

function positiveSafeInteger(value, field) {
  if (!Number.isSafeInteger(value) || value < 1) fail('INVALID_UV_PACK_TARGET', `${field} must be a positive safe integer.`);
  return value;
}

function nonNegativeSafeInteger(value, field) {
  if (!Number.isSafeInteger(value) || value < 0) fail('INVALID_UV_PACK_REQUEST', `${field} must be a non-negative safe integer.`);
  return value;
}

function finiteUv(value, field) {
  if (!Array.isArray(value) || value.length !== 4 || !value.every(Number.isFinite)) {
    fail('INVALID_UV_PACK_TARGET', `${field} must contain exactly four finite UV coordinates.`);
  }
  if (value[0] === value[2] || value[1] === value[3]) fail('INVALID_UV_PACK_TARGET', `${field} must have positive area.`);
  return value.slice();
}

function freezeRect(rect) {
  return Object.freeze({x: rect.x, y: rect.y, width: rect.width, height: rect.height});
}

function requirePixelRectInBounds(rect, width, height, context) {
  if (rect.x < 0 || rect.y < 0 || rect.width < 1 || rect.height < 1
    || rect.x > width - rect.width || rect.y > height - rect.height) {
    fail('UV_PACK_PIXEL_REGION_OUT_OF_BOUNDS', `${context} is outside the target texture bitmap.`);
  }
}

function rectFromUv(uv) {
  const x = Math.min(uv[0], uv[2]);
  const y = Math.min(uv[1], uv[3]);
  return {x, y, width: Math.abs(uv[2] - uv[0]), height: Math.abs(uv[3] - uv[1])};
}

function exactPixelRect(uvRect, scaleX, scaleY, context) {
  const values = [uvRect.x * scaleX, uvRect.y * scaleY, uvRect.width * scaleX, uvRect.height * scaleY];
  if (!values.every(Number.isSafeInteger)) {
    fail('UV_PACK_NON_PIXEL_ALIGNED', `${context} does not map to exact texture pixels.`);
  }
  return freezeRect({x: values[0], y: values[1], width: values[2], height: values[3]});
}

function orientedUv(oldUv, x, y, width, height) {
  const uForward = oldUv[2] > oldUv[0];
  const vForward = oldUv[3] > oldUv[1];
  return Object.freeze([
    uForward ? x : x + width,
    vForward ? y : y + height,
    uForward ? x + width : x,
    vForward ? y + height : y,
  ]);
}

function normalizeRequest(value, {apply = false} = {}) {
  if (!isPlainObject(value)) fail('INVALID_UV_PACK_REQUEST', 'UV pack request must be an object.');
  const allowed = new Set(['expectedRevision', 'textureId', 'scope', 'padding', 'label']);
  if (apply) {
    allowed.add('confirmationToken');
    allowed.add('dryRun');
  }
  for (const key of Object.keys(value)) {
    if (!allowed.has(key)) fail('INVALID_UV_PACK_REQUEST', `UV pack request contains unsupported field "${key}".`);
  }
  const scope = value.scope === undefined ? 'texture' : value.scope;
  if (scope !== 'texture') fail('UNSUPPORTED_UV_PACK_SCOPE', 'Initial bounded UV pack supports scope "texture" only.');
  const output = {
    expectedRevision: boundedString(value.expectedRevision, 'expectedRevision', 128),
    textureId: boundedString(value.textureId, 'textureId', 128),
    scope,
    padding: value.padding === undefined ? 0 : nonNegativeSafeInteger(value.padding, 'padding'),
    label: value.label === undefined ? 'Minecraft Mod Factory Asset Toolkit UV Pack' : boundedString(value.label, 'label'),
  };
  if (apply) {
    output.confirmationToken = boundedString(value.confirmationToken, 'confirmationToken', 256);
    if (value.dryRun !== undefined && typeof value.dryRun !== 'boolean') fail('INVALID_UV_PACK_REQUEST', 'dryRun must be boolean when provided.');
    output.dryRun = value.dryRun === true;
  }
  return output;
}

function validatePreviewAdapter(adapter) {
  if (!adapter || typeof adapter !== 'object' || typeof adapter.getRevision !== 'function' || typeof adapter.inspectPackTarget !== 'function') {
    fail('INVALID_UV_PACK_ADAPTER', 'UV pack adapter must expose getRevision() and inspectPackTarget().');
  }
}

function validateApplyAdapter(adapter) {
  validatePreviewAdapter(adapter);
  for (const name of ['preflightPack', 'beginTransaction', 'applyPack', 'finishTransaction', 'cancelTransaction']) {
    if (typeof adapter[name] !== 'function') fail('INVALID_UV_PACK_ADAPTER', `UV pack adapter is missing ${name}().`);
  }
}

function normalizeTarget(target, request) {
  if (!isPlainObject(target)) fail('INVALID_UV_PACK_TARGET', 'inspectPackTarget() must return an object.');
  const textureId = boundedString(target.textureId, 'target.textureId', 128);
  if (textureId !== request.textureId) fail('UV_PACK_TARGET_MISMATCH', `Requested texture "${request.textureId}" but adapter inspected "${textureId}".`);
  const pixelWidth = positiveSafeInteger(target.pixelWidth, 'target.pixelWidth');
  const pixelHeight = positiveSafeInteger(target.pixelHeight, 'target.pixelHeight');
  const uvWidth = positiveSafeInteger(target.uvWidth, 'target.uvWidth');
  const uvHeight = positiveSafeInteger(target.uvHeight, 'target.uvHeight');
  if (request.padding >= uvWidth || request.padding >= uvHeight) fail('UV_PACK_ATLAS_OVERFLOW', 'padding leaves no bounded atlas space.');
  if (!Array.isArray(target.faces) || target.faces.length < 1) fail('EMPTY_UV_PACK_TARGET', 'Target texture has no packable cube faces.');
  if (target.faces.length > MAX_UV_PACK_FACES) fail('UV_PACK_FACE_LIMIT_EXCEEDED', `Target contains ${target.faces.length} faces; maximum is ${MAX_UV_PACK_FACES}.`);

  const scaleX = pixelWidth / uvWidth;
  const scaleY = pixelHeight / uvHeight;
  if (!Number.isFinite(scaleX) || scaleX <= 0 || !Number.isFinite(scaleY) || scaleY <= 0) fail('INVALID_UV_PACK_TARGET', 'Texture pixel/UV scale is invalid.');
  const seen = new Set();
  let copiedPixels = 0;
  const faces = target.faces.map((entry, index) => {
    if (!isPlainObject(entry)) fail('INVALID_UV_PACK_TARGET', `target.faces[${index}] must be an object.`);
    const cubeId = boundedString(entry.cubeId, `target.faces[${index}].cubeId`, 128);
    const face = boundedString(entry.face, `target.faces[${index}].face`, 5).toLowerCase();
    if (!FACES.has(face)) fail('INVALID_UV_PACK_TARGET', `target.faces[${index}].face is not a cube face.`);
    if (entry.boxUv !== false) fail('BOX_UV_PACK_UNSUPPORTED', `Cube "${cubeId}" must use per-face UV for this bounded pack slice.`);
    const key = `${cubeId}\u0000${face}`;
    if (seen.has(key)) fail('DUPLICATE_UV_PACK_FACE', `Target repeats cube face ${cubeId}/${face}.`);
    seen.add(key);
    const oldUv = finiteUv(entry.uv, `target.faces[${index}].uv`);
    const rect = rectFromUv(oldUv);
    if (!Number.isSafeInteger(rect.width) || !Number.isSafeInteger(rect.height)) {
      fail('UV_PACK_NON_INTEGER_SIZE', `Cube face ${cubeId}/${face} has non-integer UV extent.`);
    }
    const sourcePixels = exactPixelRect(rect, scaleX, scaleY, `Cube face ${cubeId}/${face}`);
    requirePixelRectInBounds(sourcePixels, pixelWidth, pixelHeight, `Source pixels for ${cubeId}/${face}`);
    copiedPixels += sourcePixels.width * sourcePixels.height;
    if (!Number.isSafeInteger(copiedPixels) || copiedPixels > MAX_UV_PACK_COPIED_PIXELS) {
      fail('UV_PACK_PIXEL_BUDGET_EXCEEDED', `UV pack would copy ${copiedPixels} pixels; maximum is ${MAX_UV_PACK_COPIED_PIXELS}.`);
    }
    return {cubeId, face, oldUv: Object.freeze(oldUv), width: rect.width, height: rect.height, sourcePixels, key};
  });
  return {textureId, pixelWidth, pixelHeight, uvWidth, uvHeight, scaleX, scaleY, faces, copiedPixels};
}

function packFaces(target, padding) {
  const faces = target.faces.slice().sort((a, b) => {
    const areaDiff = (b.width * b.height) - (a.width * a.height);
    if (areaDiff) return areaDiff;
    if (b.height !== a.height) return b.height - a.height;
    if (b.width !== a.width) return b.width - a.width;
    return a.key < b.key ? -1 : a.key > b.key ? 1 : 0;
  });
  let x = 0;
  let y = 0;
  let rowHeight = 0;
  const moves = [];
  for (const face of faces) {
    if (face.width > target.uvWidth || face.height > target.uvHeight) fail('UV_PACK_ATLAS_OVERFLOW', `Cube face ${face.cubeId}/${face.face} exceeds the target atlas.`);
    if (x > 0 && x + face.width > target.uvWidth) {
      x = 0;
      y += rowHeight + padding;
      rowHeight = 0;
    }
    if (y + face.height > target.uvHeight) fail('UV_PACK_ATLAS_OVERFLOW', 'Target atlas cannot contain the deterministic bounded UV pack plan.');
    const newUv = orientedUv(face.oldUv, x, y, face.width, face.height);
    const destinationPixels = exactPixelRect({x, y, width: face.width, height: face.height}, target.scaleX, target.scaleY, `Destination for ${face.cubeId}/${face.face}`);
    requirePixelRectInBounds(destinationPixels, target.pixelWidth, target.pixelHeight, `Destination pixels for ${face.cubeId}/${face.face}`);
    moves.push(Object.freeze({
      cubeId: face.cubeId,
      face: face.face,
      oldUv: face.oldUv,
      newUv,
      sourcePixels: face.sourcePixels,
      destinationPixels,
    }));
    x += face.width + padding;
    rowHeight = Math.max(rowHeight, face.height);
  }
  return Object.freeze(moves);
}

function tokenFor(preview) {
  const payload = {
    beforeRevision: preview.beforeRevision,
    textureId: preview.textureId,
    scope: preview.scope,
    atlas: preview.atlas,
    moves: preview.moves,
    copiedPixels: preview.copiedPixels,
  };
  const crypto = require('node:crypto');
  return `uvpack:v1:${crypto.createHash('sha256').update(JSON.stringify(payload)).digest('hex')}`;
}

function previewUvPack(adapter, input) {
  validatePreviewAdapter(adapter);
  const request = normalizeRequest(input);
  const beforeRevision = adapter.getRevision();
  if (beforeRevision !== request.expectedRevision) fail('STALE_PROJECT_REVISION', `Expected ${request.expectedRevision} but active project is ${beforeRevision}.`);
  const target = normalizeTarget(adapter.inspectPackTarget(request.textureId), request);
  const moves = packFaces(target, request.padding);
  const base = {
    ok: true,
    dryRun: true,
    beforeRevision,
    expectedRevision: request.expectedRevision,
    textureId: request.textureId,
    scope: request.scope,
    atlas: Object.freeze({width: target.uvWidth, height: target.uvHeight, padding: request.padding}),
    moves,
    copiedPixels: target.copiedPixels,
    label: request.label,
  };
  return Object.freeze({...base, confirmationToken: tokenFor(base)});
}

function safeChangedIds(value) {
  const input = Array.isArray(value) ? value : [value];
  const output = [];
  for (const id of input) if (typeof id === 'string' && id && !output.includes(id)) output.push(id);
  return Object.freeze(output);
}

function applyUvPack(adapter, input) {
  validateApplyAdapter(adapter);
  const request = normalizeRequest(input, {apply: true});
  const preview = previewUvPack(adapter, {
    expectedRevision: request.expectedRevision,
    textureId: request.textureId,
    scope: request.scope,
    padding: request.padding,
    label: request.label,
  });
  if (request.confirmationToken !== preview.confirmationToken) {
    fail('UV_PACK_CONFIRMATION_MISMATCH', 'UV pack confirmation token does not match the current revision-bound preview.');
  }
  adapter.preflightPack(preview);
  if (request.dryRun) return preview;
  const beforeRevision = preview.beforeRevision;

  let opened = false;
  try {
    adapter.beginTransaction(request.label);
    opened = true;
    const changedIds = safeChangedIds(adapter.applyPack(preview));
    adapter.finishTransaction(request.label);
    opened = false;
    const afterRevision = adapter.getRevision();
    if (afterRevision === beforeRevision) fail('UV_PACK_REVISION_DID_NOT_ADVANCE', 'Committed UV pack did not advance the project revision.');
    return Object.freeze({
      ...preview,
      dryRun: false,
      applied: preview.moves.length,
      changedIds,
      afterRevision,
    });
  } catch (error) {
    if (opened) {
      try { adapter.cancelTransaction(true); } catch (_) { /* preserve original error */ }
    }
    throw error;
  }
}

module.exports = {
  MAX_UV_PACK_FACES,
  MAX_UV_PACK_COPIED_PIXELS,
  UvPackContractError,
  previewUvPack,
  applyUvPack,
};
