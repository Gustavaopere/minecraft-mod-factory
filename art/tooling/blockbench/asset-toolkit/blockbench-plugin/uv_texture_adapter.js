'use strict';

const {MAX_TEXTURE_PIXELS_PER_BATCH, MAX_PALETTE_REPLACEMENTS} = require('../core/uv-texture/uv_texture_engine.js');

function fail(code, message) {
  const error = new Error(`${code}: ${message}`);
  error.code = code;
  throw error;
}

function array(value) {
  return Array.isArray(value) ? value : [];
}

function createBlockbenchUvTextureAdapter(bb) {
  const project = bb?.Blockbench?.Project;
  if (!project || typeof project !== 'object') fail('NO_PROJECT', 'No Blockbench project is open.');
  if (bb.Blockbench.isWeb !== false) fail('DESKTOP_REQUIRED', 'UV/texture mutations require desktop Blockbench.');
  if (typeof bb.Cube !== 'function' || typeof bb.Texture !== 'function') {
    fail('BLOCKBENCH_API_UNAVAILABLE', 'Cube and Texture constructors are required.');
  }
  if (!bb.Undo || ['initEdit', 'finishEdit', 'cancelEdit'].some((name) => typeof bb.Undo[name] !== 'function')) {
    fail('BLOCKBENCH_API_UNAVAILABLE', 'Blockbench Undo API is incomplete.');
  }

  let transactionOpen = false;
  let prepared = null;
  const dirtyTextures = new Set();
  let approvalSequence = 0;
  const approvedTextureImports = new Map();
  const transactionConsumedApprovals = [];

  function cubes() {
    return Array.isArray(bb.Cube.all) ? bb.Cube.all : array(project.elements).filter((entry) => entry instanceof bb.Cube);
  }

  function textures() {
    return Array.isArray(bb.Texture.all) ? bb.Texture.all : array(project.textures);
  }

  function normalizedTextureName(value) {
    return typeof value === 'string' ? value.trim().toLowerCase() : '';
  }

  function requireTextureDimensions(width, height, context) {
    if (!Number.isSafeInteger(width) || width < 1 || !Number.isSafeInteger(height) || height < 1) {
      fail('INVALID_TEXTURE_DIMENSIONS', `${context} must use positive safe integer dimensions.`);
    }
    return Object.freeze({width, height});
  }

  function texturePixelArea(width, height, context) {
    const area = width * height;
    if (!Number.isSafeInteger(area) || area > MAX_TEXTURE_PIXELS_PER_BATCH) {
      fail('TEXTURE_PIXEL_BUDGET_EXCEEDED', `${context} may write ${area} pixels; maximum is ${MAX_TEXTURE_PIXELS_PER_BATCH}.`);
    }
    return area;
  }

  function requireTextureNameAvailable(name, reservedNames) {
    const normalized = normalizedTextureName(name);
    if (!normalized) fail('INVALID_TEXTURE_NAME', 'Texture name must contain non-whitespace characters.');
    const occupied = reservedNames || new Set(textures().map((texture) => normalizedTextureName(texture?.name)).filter(Boolean));
    if (occupied.has(normalized)) fail('TEXTURE_NAME_COLLISION', `Texture name "${name}" already exists in the active project or batch.`);
    return normalized;
  }

  function requireApprovedTextureImport(approvalId) {
    const approval = approvedTextureImports.get(approvalId);
    if (!approval) fail('TEXTURE_IMPORT_APPROVAL_NOT_FOUND', `Approved local texture import "${approvalId}" is unavailable or already consumed.`);
    return approval;
  }

  function approveTextureImport(file, dimensions) {
    if (!file || typeof file !== 'object') fail('INVALID_TEXTURE_IMPORT_FILE', 'Approved texture import must originate from a Blockbench file result.');
    const name = typeof file.name === 'string' ? file.name.trim() : '';
    if (!name) fail('INVALID_TEXTURE_IMPORT_FILE', 'Approved texture import requires a file name.');
    const {width, height} = requireTextureDimensions(dimensions?.width, dimensions?.height, 'Approved texture import');
    texturePixelArea(width, height, `Approved texture import "${name}"`);
    requireTextureNameAvailable(name);

    const approvedFile = {name};
    for (const field of ['path', 'content', 'browser_file']) {
      if (Object.prototype.hasOwnProperty.call(file, field)) approvedFile[field] = file[field];
    }

    approvalSequence += 1;
    const approvalId = `texture-import-approval-${approvalSequence}`;
    approvedTextureImports.set(approvalId, Object.freeze({
      approvalId,
      name,
      width,
      height,
      file: Object.freeze(approvedFile),
    }));
    return approvalId;
  }

  function requireCube(cubeId) {
    const cube = cubes().find((entry) => entry && entry.uuid === cubeId);
    if (!cube) fail('CUBE_NOT_FOUND', `Cube "${cubeId}" does not exist.`);
    return cube;
  }

  function requireTexture(textureId) {
    const texture = textures().find((entry) => entry && (entry.uuid === textureId || entry.id === textureId));
    if (!texture) fail('TEXTURE_NOT_FOUND', `Texture "${textureId}" does not exist.`);
    return texture;
  }

  function requireFace(cube, faceName) {
    const face = cube && cube.faces && cube.faces[faceName];
    if (!face || typeof face.extend !== 'function') fail('FACE_NOT_FOUND', `Cube "${cube?.uuid || '<unknown>'}" does not expose face "${faceName}".`);
    return face;
  }

  function requireCubeUvApi(cube) {
    if (typeof cube.setUVMode !== 'function' || typeof cube.extend !== 'function') {
      fail('BLOCKBENCH_API_UNAVAILABLE', `Cube "${cube.uuid}" does not expose the Blockbench 5.1.6 UV API.`);
    }
  }

  function requireComparableTexture(texture) {
    if (texture.layers_enabled === true) {
      fail('LAYERED_TEXTURE_UNSUPPORTED', `Texture "${texture.uuid || texture.id}" uses layers; PR4 requires an explicit future layer target.`);
    }
    const ctx = texture.ctx;
    if (!texture.canvas || !ctx || typeof ctx.getImageData !== 'function') {
      fail('BLOCKBENCH_API_UNAVAILABLE', `Texture "${texture.uuid || texture.id}" does not expose a readable 2D canvas.`);
    }
    if (!Number.isSafeInteger(texture.width) || texture.width < 1 || !Number.isSafeInteger(texture.height) || texture.height < 1) {
      fail('INVALID_TEXTURE_DIMENSIONS', `Texture "${texture.uuid || texture.id}" has invalid dimensions.`);
    }
    return texture;
  }

  function requireEditableTexture(texture) {
    if (texture.layers_enabled === true) {
      fail('LAYERED_TEXTURE_UNSUPPORTED', `Texture "${texture.uuid || texture.id}" uses layers; PR4 requires an explicit future layer target.`);
    }
    const ctx = texture.ctx;
    if (!texture.canvas || !ctx || typeof ctx.getImageData !== 'function' || typeof ctx.putImageData !== 'function') {
      fail('BLOCKBENCH_API_UNAVAILABLE', `Texture "${texture.uuid || texture.id}" does not expose a mutable 2D canvas.`);
    }
    if (typeof texture.updateChangesAfterEdit !== 'function') {
      fail('BLOCKBENCH_API_UNAVAILABLE', `Texture "${texture.uuid || texture.id}" cannot publish canvas edits.`);
    }
    if (!Number.isSafeInteger(texture.width) || texture.width < 1 || !Number.isSafeInteger(texture.height) || texture.height < 1) {
      fail('INVALID_TEXTURE_DIMENSIONS', `Texture "${texture.uuid || texture.id}" has invalid dimensions.`);
    }
    return texture;
  }

  function regionFor(operation) {
    if (operation.type === 'texture_replace_palette' || operation.type === 'texture_paint_region' || operation.type === 'texture_paint_uv_island') return operation.region;
    return operation;
  }

  function requireRegionInBounds(texture, operation) {
    const region = regionFor(operation);
    if (!region || !Number.isSafeInteger(region.x) || !Number.isSafeInteger(region.y)
      || !Number.isSafeInteger(region.width) || !Number.isSafeInteger(region.height)
      || region.x < 0 || region.y < 0 || region.width < 1 || region.height < 1
      || region.x > texture.width - region.width || region.y > texture.height - region.height) {
      fail('PIXEL_REGION_OUT_OF_BOUNDS', `Pixel region is outside texture "${texture.uuid || texture.id}" bounds ${texture.width}x${texture.height}.`);
    }
  }

  function requirePackRegionInBounds(texture, region, context) {
    if (!region || !Number.isSafeInteger(region.x) || !Number.isSafeInteger(region.y)
      || !Number.isSafeInteger(region.width) || !Number.isSafeInteger(region.height)
      || region.x < 0 || region.y < 0 || region.width < 1 || region.height < 1
      || region.x > texture.width - region.width || region.y > texture.height - region.height) {
      fail('UV_PACK_PIXEL_REGION_OUT_OF_BOUNDS', `${context} is outside texture "${texture.uuid || texture.id}" bounds ${texture.width}x${texture.height}.`);
    }
    return region;
  }

  function requireUvIslandRegionInBounds(texture, region, context) {
  if (!region || !Number.isSafeInteger(region.x) || !Number.isSafeInteger(region.y)
    || !Number.isSafeInteger(region.width) || !Number.isSafeInteger(region.height)
    || region.x < 0 || region.y < 0 || region.width < 1 || region.height < 1
    || region.x > texture.width - region.width || region.y > texture.height - region.height) {
    fail('UV_ISLAND_PIXEL_REGION_OUT_OF_BOUNDS', `${context} is outside texture "${texture.uuid || texture.id}" bounds ${texture.width}x${texture.height}.`);
  }
  return region;
}

function exactUvIslandPixelRect(texture, uv, scaleX, scaleY, context) {
  if (!Array.isArray(uv) || uv.length < 4 || !uv.slice(0, 4).every(Number.isFinite)) {
    fail('INVALID_UV_ISLAND_UV', `${context} must expose four finite UV coordinates.`);
  }
  const minX = Math.min(uv[0], uv[2]);
  const minY = Math.min(uv[1], uv[3]);
  const width = Math.abs(uv[2] - uv[0]);
  const height = Math.abs(uv[3] - uv[1]);
  if (!(width > 0) || !(height > 0)) fail('INVALID_UV_ISLAND_UV', `${context} must have positive UV area.`);
  const values = [minX * scaleX, minY * scaleY, width * scaleX, height * scaleY];
  if (!values.every(Number.isSafeInteger)) {
    fail('UV_ISLAND_NON_PIXEL_ALIGNED', `${context} does not map exactly to texture pixels.`);
  }
  return requireUvIslandRegionInBounds(texture, {
    x: values[0], y: values[1], width: values[2], height: values[3],
  }, context);
}

function uvIslandRectsConnected(a, b) {
  const xOverlap = Math.min(a.x + a.width, b.x + b.width) - Math.max(a.x, b.x);
  const yOverlap = Math.min(a.y + a.height, b.y + b.height) - Math.max(a.y, b.y);
  if (xOverlap > 0 && yOverlap > 0) return true;
  if (xOverlap > 0 && (a.y + a.height === b.y || b.y + b.height === a.y)) return true;
  if (yOverlap > 0 && (a.x + a.width === b.x || b.x + b.width === a.x)) return true;
  return false;
}

function prepareUvIslandPaint(operation) {
  const texture = requireEditableTexture(requireTexture(operation.textureId));
  if (!Array.isArray(operation.faces) || operation.faces.length < 1) {
    fail('INVALID_UV_ISLAND_FACES', 'texture_paint_uv_island requires explicit cube-face selectors.');
  }
  const uvWidth = requireProjectUvDimension(project.texture_width, 'Project.texture_width');
  const uvHeight = requireProjectUvDimension(project.texture_height, 'Project.texture_height');
  const scaleX = texture.width / uvWidth;
  const scaleY = texture.height / uvHeight;
  if (!Number.isFinite(scaleX) || scaleX <= 0 || !Number.isFinite(scaleY) || scaleY <= 0) {
    fail('INVALID_PROJECT_UV_DIMENSIONS', 'Texture pixel/UV scale is invalid for UV island painting.');
  }

  const rectangles = operation.faces.map((selector) => {
    const cube = requireCube(selector.cubeId);
    const face = requireFace(cube, selector.face);
    if (cube.box_uv === true) fail('BOX_UV_ISLAND_UNSUPPORTED', `Cube "${cube.uuid}" must use per-face UV for bounded UV island painting.`);
    if (face.enabled === false) fail('UV_ISLAND_FACE_DISABLED', `Cube "${cube.uuid}" face "${selector.face}" is disabled.`);
    if (!faceUsesTexture(face, texture)) {
      fail('UV_ISLAND_TEXTURE_MISMATCH', `Cube "${cube.uuid}" face "${selector.face}" does not reference texture "${operation.textureId}".`);
    }
    return exactUvIslandPixelRect(texture, face.uv, scaleX, scaleY, `Cube face ${cube.uuid}/${selector.face}`);
  });

  const visited = new Set([0]);
  const queue = [0];
  while (queue.length) {
    const current = queue.shift();
    for (let candidate = 0; candidate < rectangles.length; candidate += 1) {
      if (visited.has(candidate) || !uvIslandRectsConnected(rectangles[current], rectangles[candidate])) continue;
      visited.add(candidate);
      queue.push(candidate);
    }
  }
  if (visited.size !== rectangles.length) {
    fail('UV_ISLAND_DISCONNECTED', 'Selected cube faces do not form one UV island by shared area or edge segment.');
  }

  const left = Math.min(...rectangles.map((rect) => rect.x));
  const top = Math.min(...rectangles.map((rect) => rect.y));
  const right = Math.max(...rectangles.map((rect) => rect.x + rect.width));
  const bottom = Math.max(...rectangles.map((rect) => rect.y + rect.height));
  const derivedRegion = {x: left, y: top, width: right - left, height: bottom - top};
  const region = operation.region;
  if (!region || region.x !== derivedRegion.x || region.y !== derivedRegion.y
    || region.width !== derivedRegion.width || region.height !== derivedRegion.height) {
    fail('UV_ISLAND_REGION_MISMATCH', `Declared paint region must exactly match the derived UV island bounds ${left},${top} ${derivedRegion.width}x${derivedRegion.height}.`);
  }
  requireUvIslandRegionInBounds(texture, region, 'Derived UV island bounds');

  const mask = new Array(region.width * region.height).fill(false);
  for (const rect of rectangles) {
    for (let y = rect.y; y < rect.y + rect.height; y += 1) {
      for (let x = rect.x; x < rect.x + rect.width; x += 1) {
        mask[(y - region.y) * region.width + (x - region.x)] = true;
      }
    }
  }
  return Object.freeze({operation, texture, mask: Object.freeze(mask)});
}

  function samplePalette(input) {
    if (!input || typeof input !== 'object' || Array.isArray(input)) {
      fail('INVALID_PALETTE_SAMPLE', 'Palette sample request must be an object.');
    }
    for (const key of Object.keys(input)) {
      if (key !== 'textureId' && key !== 'region') {
        fail('INVALID_PALETTE_SAMPLE', `Palette sample request contains unsupported field "${key}".`);
      }
    }
    if (typeof input.textureId !== 'string' || !input.textureId.trim()) {
      fail('INVALID_TEXTURE_ID', 'Palette sample textureId must be a non-empty string.');
    }
    const region = input.region;
    if (!region || typeof region !== 'object' || Array.isArray(region)) {
      fail('INVALID_PIXEL_REGION', 'Palette sample region must be an object.');
    }
    for (const key of Object.keys(region)) {
      if (!['x', 'y', 'width', 'height'].includes(key)) {
        fail('INVALID_PIXEL_REGION', `Palette sample region contains unsupported field "${key}".`);
      }
    }
    const normalizedRegion = {
      x: region.x,
      y: region.y,
      width: region.width,
      height: region.height,
    };
    if (!Number.isSafeInteger(normalizedRegion.x) || normalizedRegion.x < 0
      || !Number.isSafeInteger(normalizedRegion.y) || normalizedRegion.y < 0
      || !Number.isSafeInteger(normalizedRegion.width) || normalizedRegion.width < 1
      || !Number.isSafeInteger(normalizedRegion.height) || normalizedRegion.height < 1) {
      fail('INVALID_PIXEL_REGION', 'Palette sample region must use non-negative integer x/y and positive integer width/height.');
    }

    const textureId = input.textureId.trim();
    const texture = requireEditableTexture(requireTexture(textureId));
    requireRegionInBounds(texture, {type: 'texture_replace_palette', region: normalizedRegion});
    const sampledPixels = normalizedRegion.width * normalizedRegion.height;
    if (!Number.isSafeInteger(sampledPixels) || sampledPixels > MAX_TEXTURE_PIXELS_PER_BATCH) {
      fail('TEXTURE_PIXEL_BUDGET_EXCEEDED', `Palette sample may read ${sampledPixels} pixels; maximum is ${MAX_TEXTURE_PIXELS_PER_BATCH}.`);
    }

    const image = texture.ctx.getImageData(
      normalizedRegion.x,
      normalizedRegion.y,
      normalizedRegion.width,
      normalizedRegion.height,
    );
    if (!image || !image.data || image.data.length !== sampledPixels * 4) {
      fail('BLOCKBENCH_API_UNAVAILABLE', 'Palette sample did not receive the expected RGBA bitmap data.');
    }

    const histogram = new Map();
    for (let offset = 0; offset < image.data.length; offset += 4) {
      const rgba = [image.data[offset], image.data[offset + 1], image.data[offset + 2], image.data[offset + 3]];
      const key = rgba.join(',');
      const current = histogram.get(key);
      if (current) current.count += 1;
      else histogram.set(key, {rgba, count: 1});
    }

    const colors = Array.from(histogram.values()).sort((left, right) => {
      if (left.count !== right.count) return right.count - left.count;
      for (let channel = 0; channel < 4; channel += 1) {
        if (left.rgba[channel] !== right.rgba[channel]) return left.rgba[channel] - right.rgba[channel];
      }
      return 0;
    });
    const uniqueColorCount = colors.length;
    const outputColors = colors.slice(0, MAX_PALETTE_REPLACEMENTS).map((entry) => Object.freeze({
      rgba: Object.freeze(entry.rgba.slice()),
      count: entry.count,
    }));

    return Object.freeze({
      projectRevision: getRevision(),
      textureId,
      region: Object.freeze({...normalizedRegion}),
      sampledPixels,
      uniqueColorCount,
      truncated: uniqueColorCount > MAX_PALETTE_REPLACEMENTS,
      colors: Object.freeze(outputColors),
    });
  }

  function compareTextures(input) {
    if (!input || typeof input !== 'object' || Array.isArray(input)) {
      fail('INVALID_TEXTURE_COMPARE', 'Texture compare request must be an object.');
    }
    for (const key of Object.keys(input)) {
      if (key !== 'leftTextureId' && key !== 'rightTextureId') {
        fail('INVALID_TEXTURE_COMPARE', `Texture compare request contains unsupported field "${key}".`);
      }
    }
    const leftTextureId = typeof input.leftTextureId === 'string' ? input.leftTextureId.trim() : '';
    const rightTextureId = typeof input.rightTextureId === 'string' ? input.rightTextureId.trim() : '';
    if (!leftTextureId || !rightTextureId) {
      fail('INVALID_TEXTURE_ID', 'Texture compare requires non-empty leftTextureId and rightTextureId.');
    }

    const left = requireComparableTexture(requireTexture(leftTextureId));
    const right = requireComparableTexture(requireTexture(rightTextureId));
    const leftDimensions = Object.freeze({width: left.width, height: left.height});
    const rightDimensions = Object.freeze({width: right.width, height: right.height});
    const dimensionsEqual = left.width === right.width && left.height === right.height;
    const projectRevision = getRevision();

    if (!dimensionsEqual) {
      return Object.freeze({
        ok: true,
        projectRevision,
        leftTextureId,
        rightTextureId,
        leftDimensions,
        rightDimensions,
        dimensionsEqual: false,
        equal: false,
        comparedPixels: 0,
        changedPixels: null,
        changedBounds: null,
      });
    }

    const comparedPixels = left.width * left.height;
    if (!Number.isSafeInteger(comparedPixels) || comparedPixels > MAX_TEXTURE_PIXELS_PER_BATCH) {
      fail('TEXTURE_PIXEL_BUDGET_EXCEEDED', `Texture compare may read ${comparedPixels} pixels; maximum is ${MAX_TEXTURE_PIXELS_PER_BATCH}.`);
    }
    const leftImage = left.ctx.getImageData(0, 0, left.width, left.height);
    const rightImage = right.ctx.getImageData(0, 0, right.width, right.height);
    const expectedBytes = comparedPixels * 4;
    if (!leftImage?.data || leftImage.data.length !== expectedBytes || !rightImage?.data || rightImage.data.length !== expectedBytes) {
      fail('BLOCKBENCH_API_UNAVAILABLE', 'Texture compare did not receive the expected RGBA bitmap data.');
    }

    let changedPixels = 0;
    let minX = left.width;
    let minY = left.height;
    let maxX = -1;
    let maxY = -1;
    for (let pixelIndex = 0; pixelIndex < comparedPixels; pixelIndex += 1) {
      const offset = pixelIndex * 4;
      let changed = false;
      for (let channel = 0; channel < 4; channel += 1) {
        if (leftImage.data[offset + channel] !== rightImage.data[offset + channel]) {
          changed = true;
          break;
        }
      }
      if (!changed) continue;
      changedPixels += 1;
      const x = pixelIndex % left.width;
      const y = Math.floor(pixelIndex / left.width);
      if (x < minX) minX = x;
      if (y < minY) minY = y;
      if (x > maxX) maxX = x;
      if (y > maxY) maxY = y;
    }
    const changedBounds = changedPixels === 0 ? null : Object.freeze({
      x: minX,
      y: minY,
      width: maxX - minX + 1,
      height: maxY - minY + 1,
    });

    return Object.freeze({
      ok: true,
      projectRevision,
      leftTextureId,
      rightTextureId,
      leftDimensions,
      rightDimensions,
      dimensionsEqual: true,
      equal: changedPixels === 0,
      comparedPixels,
      changedPixels,
      changedBounds,
    });
  }

  function normalizedTextureRef(value) {
    if (typeof value !== 'string') return null;
    const output = value.trim();
    if (!output) return null;
    return output.startsWith('#') ? output.slice(1) : output;
  }

  function textureRefs(texture) {
    const refs = new Set();
    for (const value of [texture.uuid, texture.id, texture.name]) {
      const normalized = normalizedTextureRef(value);
      if (normalized) refs.add(normalized);
    }
    return refs;
  }

  function faceUsesTexture(face, texture) {
    const ref = normalizedTextureRef(face?.texture);
    return !!ref && textureRefs(texture).has(ref);
  }

  function requireProjectUvDimension(value, field) {
    if (!Number.isSafeInteger(value) || value < 1) {
      fail('INVALID_PROJECT_UV_DIMENSIONS', `${field} must be a positive safe integer for bounded UV packing.`);
    }
    return value;
  }

  function sameUv(left, right) {
    return Array.isArray(left) && Array.isArray(right) && left.length >= 4 && right.length >= 4
      && left.slice(0, 4).every((value, index) => value === right[index]);
  }

  function addUnique(target, value) {
    if (!target.includes(value)) target.push(value);
  }

  function getRevision() {
    const {createProjectSnapshot} = require('../live-bridge/project_snapshot.js');
    return createProjectSnapshot(project).projectRevision;
  }

  function inspectPackTarget(textureId) {
    const texture = requireEditableTexture(requireTexture(textureId));
    const uvWidth = requireProjectUvDimension(project.texture_width, 'Project.texture_width');
    const uvHeight = requireProjectUvDimension(project.texture_height, 'Project.texture_height');
    const faces = [];

    for (const cube of cubes()) {
      const cubeFaces = cube?.faces && typeof cube.faces === 'object' ? cube.faces : {};
      for (const faceName of Object.keys(cubeFaces).sort()) {
        const face = cubeFaces[faceName];
        if (!face || face.enabled === false || !faceUsesTexture(face, texture)) continue;
        faces.push(Object.freeze({
          cubeId: cube.uuid,
          face: faceName,
          uv: Array.isArray(face.uv) ? face.uv.slice(0, 4) : face.uv,
          boxUv: cube.box_uv === true,
        }));
      }
    }

    return Object.freeze({
      textureId,
      pixelWidth: texture.width,
      pixelHeight: texture.height,
      uvWidth,
      uvHeight,
      faces: Object.freeze(faces),
    });
  }

  function preflight(operations) {
    if (!Array.isArray(operations)) fail('INVALID_UV_TEXTURE_MUTATIONS', 'operations must be an array.');
    const touchedCubes = [];
    const touchedTextures = [];
    const createdTextures = [];
    const approvedImportIds = [];
    const uvIslandPaintPlans = [];
    const reservedTextureNames = new Set(textures().map((texture) => normalizedTextureName(texture?.name)).filter(Boolean));
    let pixelWrites = 0;
    let expectsNewTextures = false;

    function chargePixels(count, context) {
      pixelWrites += count;
      if (!Number.isSafeInteger(pixelWrites) || pixelWrites > MAX_TEXTURE_PIXELS_PER_BATCH) {
        fail('TEXTURE_PIXEL_BUDGET_EXCEEDED', `${context} raises the batch pixel budget to ${pixelWrites}; maximum is ${MAX_TEXTURE_PIXELS_PER_BATCH}.`);
      }
    }

    for (const operation of operations) {
      switch (operation.type) {
        case 'set_face_uv': {
          const cube = requireCube(operation.cubeId);
          requireFace(cube, operation.face);
          addUnique(touchedCubes, cube);
          break;
        }
        case 'set_face_texture': {
          const cube = requireCube(operation.cubeId);
          requireFace(cube, operation.face);
          requireTexture(operation.textureId);
          addUnique(touchedCubes, cube);
          break;
        }
        case 'set_box_uv': {
          const cube = requireCube(operation.cubeId);
          requireCubeUvApi(cube);
          addUnique(touchedCubes, cube);
          break;
        }
        case 'texture_fill_rect':
        case 'texture_replace_palette':
        case 'texture_paint_region': {
          const texture = requireEditableTexture(requireTexture(operation.textureId));
          requireRegionInBounds(texture, operation);
          const region = regionFor(operation);
          chargePixels(region.width * region.height, `Mutation "${operation.type}"`);
          addUnique(touchedTextures, texture);
          break;
        }
        case 'texture_paint_uv_island': {
    const plan = prepareUvIslandPaint(operation);
    chargePixels(operation.region.width * operation.region.height, 'Mutation "texture_paint_uv_island"');
    addUnique(touchedTextures, plan.texture);
    uvIslandPaintPlans.push(plan);
    break;
  }
        case 'texture_create': {
          const {width, height} = requireTextureDimensions(operation.width, operation.height, 'texture_create');
          const normalized = requireTextureNameAvailable(operation.name, reservedTextureNames);
          reservedTextureNames.add(normalized);
          chargePixels(texturePixelArea(width, height, `texture_create "${operation.name}"`), `texture_create "${operation.name}"`);
          expectsNewTextures = true;
          break;
        }
        case 'texture_import_approved': {
          const approval = requireApprovedTextureImport(operation.approvalId);
          if (approvedImportIds.includes(operation.approvalId)) {
            fail('TEXTURE_IMPORT_APPROVAL_REUSED', `Approval "${operation.approvalId}" may appear only once in a batch.`);
          }
          const normalized = requireTextureNameAvailable(approval.name, reservedTextureNames);
          reservedTextureNames.add(normalized);
          chargePixels(texturePixelArea(approval.width, approval.height, `Approved texture import "${approval.name}"`), `Approved texture import "${approval.name}"`);
          approvedImportIds.push(operation.approvalId);
          expectsNewTextures = true;
          break;
        }
        default:
          fail('UNSUPPORTED_UV_TEXTURE_MUTATION', `Mutation "${operation.type}" is not supported by the Blockbench adapter.`);
      }
    }

    prepared = Object.freeze({
      cubes: Object.freeze(touchedCubes.slice()),
      textures: Object.freeze(touchedTextures.slice()),
      createdTextures,
      approvedImportIds: Object.freeze(approvedImportIds.slice()),
      uvIslandPaintPlans: Object.freeze(uvIslandPaintPlans.slice()),
      expectsNewTextures,
    });
    return true;
  }

  function preflightPack(preview) {
    if (!preview || typeof preview !== 'object' || !Array.isArray(preview.moves)) {
      fail('INVALID_UV_PACK_PREVIEW', 'UV pack preview must contain a moves array.');
    }
    if (getRevision() !== preview.beforeRevision) {
      fail('STALE_PROJECT_REVISION', `UV pack preview revision ${preview.beforeRevision} is no longer current.`);
    }
    const texture = requireEditableTexture(requireTexture(preview.textureId));
    const touchedCubes = [];

    for (const move of preview.moves) {
      if (!move || typeof move !== 'object') fail('INVALID_UV_PACK_PREVIEW', 'UV pack move must be an object.');
      const cube = requireCube(move.cubeId);
      const face = requireFace(cube, move.face);
      if (cube.box_uv === true) fail('BOX_UV_PACK_UNSUPPORTED', `Cube "${cube.uuid}" must use per-face UV for bounded packing.`);
      if (!faceUsesTexture(face, texture)) {
        fail('UV_PACK_TARGET_MISMATCH', `Cube "${cube.uuid}" face "${move.face}" no longer references texture "${preview.textureId}".`);
      }
      if (!sameUv(face.uv, move.oldUv)) {
        fail('STALE_PROJECT_REVISION', `Cube "${cube.uuid}" face "${move.face}" no longer matches the previewed UV state.`);
      }
      const source = requirePackRegionInBounds(texture, move.sourcePixels, `Source pixels for ${cube.uuid}/${move.face}`);
      const destination = requirePackRegionInBounds(texture, move.destinationPixels, `Destination pixels for ${cube.uuid}/${move.face}`);
      if (source.width !== destination.width || source.height !== destination.height) {
        fail('INVALID_UV_PACK_PREVIEW', `Pixel copy for ${cube.uuid}/${move.face} must preserve region dimensions.`);
      }
      if (!Array.isArray(move.newUv) || move.newUv.length !== 4 || !move.newUv.every(Number.isFinite)) {
        fail('INVALID_UV_PACK_PREVIEW', `New UV for ${cube.uuid}/${move.face} must contain four finite coordinates.`);
      }
      addUnique(touchedCubes, cube);
    }

    prepared = Object.freeze({
      cubes: Object.freeze(touchedCubes.slice()),
      textures: Object.freeze([texture]),
      pack: Object.freeze({texture, confirmationToken: preview.confirmationToken}),
    });
    return true;
  }

  function undoAspects() {
    if (!prepared) fail('PREFLIGHT_REQUIRED', 'UV/texture batch must preflight before opening an Undo transaction.');
    const aspects = {};
    if (prepared.cubes.length) aspects.elements = prepared.cubes.slice();

    const transactionTextures = prepared.textures.slice();
    for (const texture of prepared.createdTextures || []) addUnique(transactionTextures, texture);
    if (transactionTextures.length || prepared.expectsNewTextures) aspects.textures = transactionTextures;
    if (prepared.textures.length) aspects.bitmap = true;
    return aspects;
  }

  function beginTransaction() {
    if (transactionOpen) fail('TRANSACTION_ALREADY_OPEN', 'A Blockbench Undo transaction is already open.');
    bb.Undo.initEdit(undoAspects());
    dirtyTextures.clear();
    transactionConsumedApprovals.length = 0;
    transactionOpen = true;
  }

  function applyFill(texture, operation) {
    const image = texture.ctx.getImageData(operation.x, operation.y, operation.width, operation.height);
    for (let index = 0; index < image.data.length; index += 4) {
      image.data[index] = operation.color[0];
      image.data[index + 1] = operation.color[1];
      image.data[index + 2] = operation.color[2];
      image.data[index + 3] = operation.color[3];
    }
    texture.ctx.putImageData(image, operation.x, operation.y);
  }

  function applyPaintRegion(texture, operation) {
    const {x, y, width, height} = operation.region;
    const image = texture.ctx.getImageData(x, y, width, height);
    operation.pixels.forEach((pixel, index) => {
      const offset = index * 4;
      image.data[offset] = pixel[0];
      image.data[offset + 1] = pixel[1];
      image.data[offset + 2] = pixel[2];
      image.data[offset + 3] = pixel[3];
    });
    texture.ctx.putImageData(image, x, y);
  }

  function applyUvIslandPaint(plan) {
  const {operation, texture, mask} = plan;
  const {x, y, width, height} = operation.region;
  const image = texture.ctx.getImageData(x, y, width, height);
  operation.pixels.forEach((pixel, index) => {
    if (!mask[index]) return;
    const offset = index * 4;
    image.data[offset] = pixel[0];
    image.data[offset + 1] = pixel[1];
    image.data[offset + 2] = pixel[2];
    image.data[offset + 3] = pixel[3];
  });
  texture.ctx.putImageData(image, x, y);
}

  function colorKey(color) {
    return (((color[0] * 256 + color[1]) * 256 + color[2]) * 256 + color[3]);
  }

  function applyPalette(texture, operation) {
    const {x, y, width, height} = operation.region;
    const image = texture.ctx.getImageData(x, y, width, height);
    const replacements = new Map(operation.replacements.map((entry) => [colorKey(entry.from), entry.to]));
    for (let index = 0; index < image.data.length; index += 4) {
      const replacement = replacements.get(colorKey(image.data.subarray(index, index + 4)));
      if (!replacement) continue;
      image.data[index] = replacement[0];
      image.data[index + 1] = replacement[1];
      image.data[index + 2] = replacement[2];
      image.data[index + 3] = replacement[3];
    }
    texture.ctx.putImageData(image, x, y);
  }

  function applyOperation(operation) {
    if (!transactionOpen) fail('NO_ACTIVE_TRANSACTION', 'No Blockbench Undo transaction is open.');
    switch (operation.type) {
      case 'set_face_uv': {
        const cube = requireCube(operation.cubeId);
        requireFace(cube, operation.face).extend({uv: operation.uv.slice()});
        return cube.uuid;
      }
      case 'set_face_texture': {
        const cube = requireCube(operation.cubeId);
        const texture = requireTexture(operation.textureId);
        requireFace(cube, operation.face).extend({texture: texture.uuid});
        return cube.uuid;
      }
      case 'set_box_uv': {
        const cube = requireCube(operation.cubeId);
        requireCubeUvApi(cube);
        cube.setUVMode(operation.enabled);
        cube.extend({uv_offset: operation.offset.slice()});
        return cube.uuid;
      }
      case 'texture_fill_rect': {
        const texture = requireEditableTexture(requireTexture(operation.textureId));
        applyFill(texture, operation);
        dirtyTextures.add(texture);
        return texture.uuid || texture.id;
      }
      case 'texture_replace_palette': {
        const texture = requireEditableTexture(requireTexture(operation.textureId));
        applyPalette(texture, operation);
        dirtyTextures.add(texture);
        return texture.uuid || texture.id;
      }
      case 'texture_paint_region': {
        const texture = requireEditableTexture(requireTexture(operation.textureId));
        applyPaintRegion(texture, operation);
        dirtyTextures.add(texture);
        return texture.uuid || texture.id;
      }
      case 'texture_paint_uv_island': {
    const plan = prepared?.uvIslandPaintPlans?.find((entry) => entry.operation === operation);
    if (!plan) fail('PREFLIGHT_REQUIRED', 'texture_paint_uv_island requires the exact preflighted operation.');
    applyUvIslandPaint(plan);
    dirtyTextures.add(plan.texture);
    return plan.texture.uuid || plan.texture.id;
  }
      case 'texture_create': {
        if (!prepared?.expectsNewTextures) fail('PREFLIGHT_REQUIRED', 'texture_create requires the exact preflighted batch.');
        const texture = new bb.Texture({name: operation.name, internal: true});
        if (!texture.canvas || typeof texture.canvas.toDataURL !== 'function'
          || typeof texture.fromDataURL !== 'function' || typeof texture.add !== 'function') {
          fail('BLOCKBENCH_API_UNAVAILABLE', 'Texture creation requires canvas.toDataURL(), Texture.fromDataURL(), and Texture.add().');
        }
        texture.width = operation.width;
        texture.height = operation.height;
        texture.uv_width = operation.width;
        texture.uv_height = operation.height;
        texture.canvas.width = operation.width;
        texture.canvas.height = operation.height;
        if (texture.ctx && typeof texture.ctx.clearRect === 'function') {
          texture.ctx.clearRect(0, 0, operation.width, operation.height);
        }
        const dataUrl = texture.canvas.toDataURL();
        texture.fromDataURL(dataUrl);
        texture.add(false, true);
        prepared.createdTextures.push(texture);
        return texture.uuid || texture.id;
      }
      case 'texture_import_approved': {
        if (!prepared?.approvedImportIds?.includes(operation.approvalId)) {
          fail('PREFLIGHT_REQUIRED', `Texture import approval "${operation.approvalId}" was not part of the preflighted batch.`);
        }
        const approval = requireApprovedTextureImport(operation.approvalId);
        const texture = new bb.Texture({name: approval.name});
        if (typeof texture.fromFile !== 'function' || typeof texture.add !== 'function') {
          fail('BLOCKBENCH_API_UNAVAILABLE', 'Approved texture import requires Texture.fromFile() and Texture.add().');
        }
        texture.fromFile(approval.file);
        texture.add(false, true);
        prepared.createdTextures.push(texture);
        approvedTextureImports.delete(operation.approvalId);
        transactionConsumedApprovals.push([operation.approvalId, approval]);
        return texture.uuid || texture.id;
      }
      default:
        fail('UNSUPPORTED_UV_TEXTURE_MUTATION', `Mutation "${operation.type}" is not supported by the Blockbench adapter.`);
    }
  }

  function applyPack(preview) {
    if (!transactionOpen) fail('NO_ACTIVE_TRANSACTION', 'No Blockbench Undo transaction is open.');
    if (!prepared?.pack || prepared.pack.confirmationToken !== preview?.confirmationToken) {
      fail('PREFLIGHT_REQUIRED', 'UV pack apply requires the exact preview that passed preflight.');
    }
    const texture = prepared.pack.texture;
    const buffered = preview.moves.map((move) => Object.freeze({
      move,
      image: texture.ctx.getImageData(move.sourcePixels.x, move.sourcePixels.y, move.sourcePixels.width, move.sourcePixels.height),
    }));

    for (const entry of buffered) {
      texture.ctx.putImageData(entry.image, entry.move.destinationPixels.x, entry.move.destinationPixels.y);
    }
    dirtyTextures.add(texture);

    const changedIds = [];
    addUnique(changedIds, texture.uuid || texture.id);
    for (const entry of buffered) {
      const cube = requireCube(entry.move.cubeId);
      requireFace(cube, entry.move.face).extend({uv: entry.move.newUv.slice()});
      addUnique(changedIds, cube.uuid);
    }
    return changedIds;
  }

  function finishTransaction(label) {
    if (!transactionOpen) fail('NO_ACTIVE_TRANSACTION', 'No Blockbench Undo transaction is open.');
    for (const texture of dirtyTextures) texture.updateChangesAfterEdit();
    bb.Undo.finishEdit(label, undoAspects());
    transactionOpen = false;
    prepared = null;
    dirtyTextures.clear();
    transactionConsumedApprovals.length = 0;
  }

  function cancelTransaction(revert) {
    function restoreConsumedApprovals() {
      for (const [approvalId, approval] of transactionConsumedApprovals) {
        if (!approvedTextureImports.has(approvalId)) approvedTextureImports.set(approvalId, approval);
      }
      transactionConsumedApprovals.length = 0;
    }

    if (!transactionOpen) {
      restoreConsumedApprovals();
      prepared = null;
      dirtyTextures.clear();
      return;
    }
    try {
      bb.Undo.cancelEdit(revert === true);
    } finally {
      restoreConsumedApprovals();
      transactionOpen = false;
      prepared = null;
      dirtyTextures.clear();
    }
  }

  return Object.freeze({
    getRevision,
    compareTextures,
    samplePalette,
    approveTextureImport,
    inspectPackTarget,
    preflight,
    preflightPack,
    beginTransaction,
    applyOperation,
    applyPack,
    finishTransaction,
    cancelTransaction,
  });
}

module.exports = {createBlockbenchUvTextureAdapter};
