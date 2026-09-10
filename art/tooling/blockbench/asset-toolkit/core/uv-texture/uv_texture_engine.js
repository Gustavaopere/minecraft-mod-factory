'use strict';

const MAX_UV_TEXTURE_OPERATIONS = 128;
const MAX_TEXTURE_PIXELS_PER_BATCH = 262144;
const MAX_PALETTE_REPLACEMENTS = 256;
const MAX_UV_ISLAND_FACES = 128;
const MAX_IDENTIFIER_LENGTH = 128;
const MAX_LABEL_LENGTH = 160;
const FACES = new Set(['north', 'south', 'east', 'west', 'up', 'down']);
const BATCH_FIELDS = new Set(['expectedRevision', 'label', 'operations', 'dryRun']);
const OPERATION_FIELDS = Object.freeze({
  set_face_uv: new Set(['type', 'cubeId', 'face', 'uv']),
  set_face_texture: new Set(['type', 'cubeId', 'face', 'textureId']),
  set_box_uv: new Set(['type', 'cubeId', 'enabled', 'offset']),
  texture_fill_rect: new Set(['type', 'textureId', 'x', 'y', 'width', 'height', 'color']),
  texture_replace_palette: new Set(['type', 'textureId', 'region', 'replacements']),
  texture_paint_region: new Set(['type', 'textureId', 'region', 'pixels']),
  texture_paint_uv_island: new Set(['type', 'textureId', 'faces', 'region', 'pixels']),
  texture_create: new Set(['type', 'name', 'width', 'height']),
  texture_import_approved: new Set(['type', 'approvalId']),
});

class UvTextureContractError extends Error {
  constructor(code, message) {
    super(`${code}: ${message}`);
    this.name = 'UvTextureContractError';
    this.code = code;
  }
}

function fail(code, message) {
  throw new UvTextureContractError(code, message);
}

function isPlainObject(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return false;
  const prototype = Object.getPrototypeOf(value);
  return prototype === Object.prototype || prototype === null;
}

function rejectUnknownFields(value, allowed, code, context) {
  for (const key of Object.keys(value)) {
    if (!allowed.has(key)) fail(code, `${context} contains unsupported field "${key}".`);
  }
}

function boundedString(value, field, {max = MAX_IDENTIFIER_LENGTH} = {}) {
  if (typeof value !== 'string') fail('INVALID_STRING', `${field} must be a string.`);
  const output = value.trim();
  if (!output || output.length > max) fail('INVALID_STRING', `${field} must contain 1-${max} non-whitespace characters.`);
  return output;
}

function faceName(value, field) {
  const output = boundedString(value, field, {max: 5}).toLowerCase();
  if (!FACES.has(output)) fail('INVALID_FACE', `${field} must be a cardinal cube face.`);
  return output;
}

function finiteVector(value, length, code, field) {
  if (!Array.isArray(value) || value.length !== length || !value.every(Number.isFinite)) {
    fail(code, `${field} must contain exactly ${length} finite numbers.`);
  }
  return Object.freeze(value.slice());
}

function rgba(value, field) {
  if (!Array.isArray(value) || value.length !== 4 || !value.every((entry) => Number.isInteger(entry) && entry >= 0 && entry <= 255)) {
    fail('INVALID_RGBA', `${field} must be [r,g,b,a] integers in the 0-255 range.`);
  }
  return Object.freeze(value.slice());
}

function nonNegativeInteger(value, field) {
  if (!Number.isSafeInteger(value) || value < 0) fail('INVALID_PIXEL_REGION', `${field} must be a non-negative safe integer.`);
  return value;
}

function positiveInteger(value, field) {
  if (!Number.isSafeInteger(value) || value < 1) fail('INVALID_PIXEL_REGION', `${field} must be a positive safe integer.`);
  return value;
}

function pixelRegion(value, field) {
  if (!isPlainObject(value)) fail('INVALID_PIXEL_REGION', `${field} must be an object.`);
  rejectUnknownFields(value, new Set(['x', 'y', 'width', 'height']), 'INVALID_PIXEL_REGION', field);
  return Object.freeze({
    x: nonNegativeInteger(value.x, `${field}.x`),
    y: nonNegativeInteger(value.y, `${field}.y`),
    width: positiveInteger(value.width, `${field}.width`),
    height: positiveInteger(value.height, `${field}.height`),
  });
}

function pixelArea(region, field) {
  const area = region.width * region.height;
  if (!Number.isSafeInteger(area)) fail('INVALID_PIXEL_REGION', `${field} pixel area exceeds the safe integer range.`);
  return area;
}

function paletteReplacements(value, field) {
  if (!Array.isArray(value) || value.length < 1 || value.length > MAX_PALETTE_REPLACEMENTS) {
    fail('INVALID_PALETTE_REPLACEMENTS', `${field} must contain 1-${MAX_PALETTE_REPLACEMENTS} entries.`);
  }
  const seen = new Set();
  return Object.freeze(value.map((entry, index) => {
    if (!isPlainObject(entry)) fail('INVALID_PALETTE_REPLACEMENTS', `${field}[${index}] must be an object.`);
    rejectUnknownFields(entry, new Set(['from', 'to']), 'INVALID_PALETTE_REPLACEMENTS', `${field}[${index}]`);
    const from = rgba(entry.from, `${field}[${index}].from`);
    const to = rgba(entry.to, `${field}[${index}].to`);
    const key = from.join(',');
    if (seen.has(key)) fail('DUPLICATE_PALETTE_SOURCE', `${field} contains duplicate source color ${key}.`);
    seen.add(key);
    return Object.freeze({from, to});
  }));
}

function uvIslandFaces(value, field) {
  if (!Array.isArray(value) || value.length < 1 || value.length > MAX_UV_ISLAND_FACES) {
    fail('INVALID_UV_ISLAND_FACES', `${field} must contain 1-${MAX_UV_ISLAND_FACES} explicit cube-face selectors.`);
  }
  const seen = new Set();
  return Object.freeze(value.map((entry, index) => {
    if (!isPlainObject(entry)) fail('INVALID_UV_ISLAND_FACES', `${field}[${index}] must be an object.`);
    rejectUnknownFields(entry, new Set(['cubeId', 'face']), 'INVALID_UV_ISLAND_FACES', `${field}[${index}]`);
    const cubeId = boundedString(entry.cubeId, `${field}[${index}].cubeId`);
    const face = faceName(entry.face, `${field}[${index}].face`);
    const key = `${cubeId}\u0000${face}`;
    if (seen.has(key)) fail('DUPLICATE_UV_ISLAND_FACE', `${field} repeats cube face ${cubeId}/${face}.`);
    seen.add(key);
    return Object.freeze({cubeId, face});
  }));
}

function validateOperation(value, index) {
  if (!isPlainObject(value)) fail('INVALID_UV_TEXTURE_MUTATION', `operations[${index}] must be an object.`);
  const type = typeof value.type === 'string' ? value.type : '';
  const allowedFields = OPERATION_FIELDS[type];
  if (!allowedFields) fail('UNSUPPORTED_UV_TEXTURE_MUTATION', `operations[${index}] type "${type || '<missing>'}" is not allowlisted.`);
  rejectUnknownFields(value, allowedFields, 'UNKNOWN_UV_TEXTURE_FIELD', `operations[${index}]`);

  switch (type) {
    case 'set_face_uv':
      return Object.freeze({
        type,
        cubeId: boundedString(value.cubeId, `operations[${index}].cubeId`),
        face: faceName(value.face, `operations[${index}].face`),
        uv: finiteVector(value.uv, 4, 'INVALID_UV_RECT', `operations[${index}].uv`),
      });
    case 'set_face_texture':
      return Object.freeze({
        type,
        cubeId: boundedString(value.cubeId, `operations[${index}].cubeId`),
        face: faceName(value.face, `operations[${index}].face`),
        textureId: boundedString(value.textureId, `operations[${index}].textureId`),
      });
    case 'set_box_uv': {
      if (typeof value.enabled !== 'boolean') fail('INVALID_BOX_UV_MODE', `operations[${index}].enabled must be boolean.`);
      return Object.freeze({
        type,
        cubeId: boundedString(value.cubeId, `operations[${index}].cubeId`),
        enabled: value.enabled,
        offset: finiteVector(value.offset, 2, 'INVALID_UV_OFFSET', `operations[${index}].offset`),
      });
    }
    case 'texture_fill_rect': {
      const region = Object.freeze({
        x: nonNegativeInteger(value.x, `operations[${index}].x`),
        y: nonNegativeInteger(value.y, `operations[${index}].y`),
        width: positiveInteger(value.width, `operations[${index}].width`),
        height: positiveInteger(value.height, `operations[${index}].height`),
      });
      return Object.freeze({
        type,
        textureId: boundedString(value.textureId, `operations[${index}].textureId`),
        ...region,
        color: rgba(value.color, `operations[${index}].color`),
      });
    }
    case 'texture_replace_palette':
      return Object.freeze({
        type,
        textureId: boundedString(value.textureId, `operations[${index}].textureId`),
        region: pixelRegion(value.region, `operations[${index}].region`),
        replacements: paletteReplacements(value.replacements, `operations[${index}].replacements`),
      });
    case 'texture_paint_region': {
      const region = pixelRegion(value.region, `operations[${index}].region`);
      const area = pixelArea(region, `operations[${index}].region`);
      if (!Array.isArray(value.pixels) || value.pixels.length !== area) {
        fail('PAINT_PIXEL_COUNT_MISMATCH', `operations[${index}].pixels must contain exactly ${area} row-major RGBA pixels.`);
      }
      const pixels = Object.freeze(value.pixels.map((pixel, pixelIndex) =>
        rgba(pixel, `operations[${index}].pixels[${pixelIndex}]`)));
      return Object.freeze({
        type,
        textureId: boundedString(value.textureId, `operations[${index}].textureId`),
        region,
        pixels,
      });
    }
    case 'texture_paint_uv_island': {
    const faces = uvIslandFaces(value.faces, `operations[${index}].faces`);
    const region = pixelRegion(value.region, `operations[${index}].region`);
    const area = pixelArea(region, `operations[${index}].region`);
    if (!Array.isArray(value.pixels) || value.pixels.length !== area) {
      fail('PAINT_PIXEL_COUNT_MISMATCH', `operations[${index}].pixels must contain exactly ${area} row-major RGBA pixels.`);
    }
    const pixels = Object.freeze(value.pixels.map((pixel, pixelIndex) =>
      rgba(pixel, `operations[${index}].pixels[${pixelIndex}]`)));
    return Object.freeze({
      type,
      textureId: boundedString(value.textureId, `operations[${index}].textureId`),
      faces,
      region,
      pixels,
    });
  }
    case 'texture_create':
      return Object.freeze({
        type,
        name: boundedString(value.name, `operations[${index}].name`),
        width: positiveInteger(value.width, `operations[${index}].width`),
        height: positiveInteger(value.height, `operations[${index}].height`),
      });
    case 'texture_import_approved':
      return Object.freeze({
        type,
        approvalId: boundedString(value.approvalId, `operations[${index}].approvalId`),
      });
    default:
      fail('UNSUPPORTED_UV_TEXTURE_MUTATION', `operations[${index}] is not allowlisted.`);
  }
}

function operationPixelWrites(operation, index) {
  if (operation.type === 'texture_fill_rect') return pixelArea(operation, `operations[${index}]`);
  if (operation.type === 'texture_replace_palette') return pixelArea(operation.region, `operations[${index}].region`);
  if (operation.type === 'texture_paint_region') return pixelArea(operation.region, `operations[${index}].region`);
  if (operation.type === 'texture_paint_uv_island') return pixelArea(operation.region, `operations[${index}].region`);
  if (operation.type === 'texture_create') return pixelArea(operation, `operations[${index}]`);
  return 0;
}

function validateUvTextureBatch(value) {
  if (!isPlainObject(value)) fail('INVALID_UV_TEXTURE_BATCH', 'UV/texture batch must be an object.');
  rejectUnknownFields(value, BATCH_FIELDS, 'UNKNOWN_BATCH_FIELD', 'UV/texture batch');
  const expectedRevision = boundedString(value.expectedRevision, 'expectedRevision');
  if (!Array.isArray(value.operations) || value.operations.length < 1) {
    fail('EMPTY_UV_TEXTURE_BATCH', 'operations must contain at least one mutation.');
  }
  if (value.operations.length > MAX_UV_TEXTURE_OPERATIONS) {
    fail('UV_TEXTURE_BATCH_TOO_LARGE', `operations exceeds the maximum of ${MAX_UV_TEXTURE_OPERATIONS}.`);
  }
  if (value.dryRun !== undefined && typeof value.dryRun !== 'boolean') fail('INVALID_DRY_RUN', 'dryRun must be boolean when provided.');

  const operations = value.operations.map(validateOperation);
  let pixelWrites = 0;
  operations.forEach((operation, index) => {
    pixelWrites += operationPixelWrites(operation, index);
    if (!Number.isSafeInteger(pixelWrites) || pixelWrites > MAX_TEXTURE_PIXELS_PER_BATCH) {
      fail('TEXTURE_PIXEL_BUDGET_EXCEEDED', `Batch may write ${pixelWrites} pixels; maximum is ${MAX_TEXTURE_PIXELS_PER_BATCH}.`);
    }
  });

  return Object.freeze({
    expectedRevision,
    label: value.label === undefined
      ? 'Minecraft Mod Factory Asset Toolkit UV/Texture Batch'
      : boundedString(value.label, 'label', {max: MAX_LABEL_LENGTH}),
    operations: Object.freeze(operations),
    dryRun: value.dryRun === true,
    pixelWrites,
  });
}

function validateAdapter(adapter) {
  const methods = ['getRevision', 'preflight', 'beginTransaction', 'applyOperation', 'finishTransaction', 'cancelTransaction'];
  if (!adapter || typeof adapter !== 'object') fail('INVALID_UV_TEXTURE_ADAPTER', 'UV/texture adapter is required.');
  for (const method of methods) {
    if (typeof adapter[method] !== 'function') fail('INVALID_UV_TEXTURE_ADAPTER', `UV/texture adapter is missing ${method}().`);
  }
}

function collectChangedIds(target, changed) {
  const values = Array.isArray(changed) ? changed : [changed];
  for (const value of values) {
    if (typeof value === 'string' && value && !target.includes(value)) target.push(value);
  }
}

function applyUvTextureBatch(adapter, input) {
  validateAdapter(adapter);
  const batch = validateUvTextureBatch(input);
  const beforeRevision = adapter.getRevision();
  if (beforeRevision !== batch.expectedRevision) {
    fail('STALE_PROJECT_REVISION', `Expected ${batch.expectedRevision} but active project is ${beforeRevision}.`);
  }

  adapter.preflight(batch.operations);
  if (batch.dryRun) {
    return Object.freeze({
      ok: true,
      dryRun: true,
      beforeRevision,
      afterRevision: beforeRevision,
      applied: 0,
      changedIds: Object.freeze([]),
      pixelWrites: batch.pixelWrites,
    });
  }

  const changedIds = [];
  let begun = false;
  try {
    adapter.beginTransaction(batch.label);
    begun = true;
    batch.operations.forEach((operation, index) => {
      collectChangedIds(changedIds, adapter.applyOperation(operation, index));
    });
    adapter.finishTransaction(batch.label);
    begun = false;
    const afterRevision = adapter.getRevision();
    return Object.freeze({
      ok: true,
      dryRun: false,
      beforeRevision,
      afterRevision,
      applied: batch.operations.length,
      changedIds: Object.freeze(changedIds.slice()),
      pixelWrites: batch.pixelWrites,
    });
  } catch (error) {
    if (begun) {
      try { adapter.cancelTransaction(true); } catch (_) { /* preserve original mutation failure */ }
    }
    if (error && typeof error.code === 'string' && !String(error.message || '').includes(error.code)) {
      const wrapped = new Error(`${error.code}: ${error.message || error.code}`, {cause: error});
      wrapped.code = error.code;
      throw wrapped;
    }
    throw error;
  }
}

module.exports = {
  MAX_UV_TEXTURE_OPERATIONS,
  MAX_TEXTURE_PIXELS_PER_BATCH,
  MAX_PALETTE_REPLACEMENTS,
  UvTextureContractError,
  validateUvTextureBatch,
  applyUvTextureBatch,
};
