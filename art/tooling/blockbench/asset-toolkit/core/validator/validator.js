'use strict';

const {
  finiteVector3,
  isPowerOfTwo,
  normalizedName,
  normalizeTextureRef,
  parentObject,
  isCubeLike,
  locatorPosition,
  isLocatorLike,
  computeBounds,
} = require('../project-model/project_model.js');

function issue(severity, code, message, context) {
  return {severity, code, message, context: context || null};
}

function summarize(issues, bounds, counts = {}) {
  const errors = issues.filter((item) => item.severity === 'error');
  const warnings = issues.filter((item) => item.severity !== 'error');
  return {issues, errors, warnings, bounds, counts};
}

function validateProject(project, profile = {}) {
  const issues = [];
  if (!project || typeof project !== 'object') {
    issues.push(issue('error', 'NO_PROJECT', 'No Blockbench model project is open.'));
    return summarize(issues, null);
  }

  const groups = Array.isArray(project.groups) ? project.groups : [];
  const elements = Array.isArray(project.elements) ? project.elements : [];
  const textures = Array.isArray(project.textures) ? project.textures : [];
  const animations = Array.isArray(project.animations) ? project.animations : [];
  const cubeElements = elements.filter(isCubeLike);
  const locatorElements = elements.filter(isLocatorLike);

  if (!normalizedName(project.save_path)) {
    issues.push(issue('warning', 'UNSAVED_SOURCE', 'Project has no save_path. Preserve a project-owned .bbmodel source before final approval.'));
  } else if (!project.save_path.toLowerCase().endsWith('.bbmodel')) {
    issues.push(issue('warning', 'SOURCE_NOT_BBMODEL', `Project source path does not end in .bbmodel: ${project.save_path}`));
  }
  if (cubeElements.length > 0 && groups.length === 0) {
    issues.push(issue('warning', 'NO_GROUPS', 'Model has renderable cube elements but no groups/bones. Animated GeckoLib assets require intentional hierarchy.'));
  }

  const groupsByUuid = new Map();
  const groupsByName = new Map();
  for (const group of groups) {
    const name = normalizedName(group?.name);
    const uuid = normalizedName(group?.uuid);
    if (uuid) groupsByUuid.set(uuid, group);
    if (!name) {
      issues.push(issue('error', 'EMPTY_BONE_NAME', 'A group/bone has no name.'));
    } else {
      const canonical = name.toLowerCase();
      if (groupsByName.has(canonical)) issues.push(issue('error', 'DUPLICATE_BONE_NAME', `Duplicate group/bone name: "${name}".`));
      else groupsByName.set(canonical, group);
      if (!/^[a-z0-9_]+$/.test(name)) issues.push(issue('warning', 'BONE_NAME_STYLE', `Bone "${name}" is not lower_snake_case.`));
    }
    if (!finiteVector3(group?.origin)) issues.push(issue('error', 'INVALID_BONE_PIVOT', `Bone "${name || '<unnamed>'}" has a malformed/non-finite origin.`));
  }

  for (const group of groups) {
    const seen = new Set();
    let cursor = group;
    while (cursor && typeof cursor === 'object') {
      const key = normalizedName(cursor.uuid) || cursor;
      if (seen.has(key)) {
        issues.push(issue('error', 'BONE_PARENT_CYCLE', `Bone "${normalizedName(group.name) || '<unnamed>'}" participates in a parent cycle.`));
        break;
      }
      seen.add(key);
      cursor = parentObject(cursor.parent);
    }
  }

  const textureRefs = new Set();
  const textureNames = new Map();
  for (const texture of textures) {
    const name = normalizedName(texture?.name) || '<unnamed>';
    const uuid = normalizedName(texture?.uuid);
    if (uuid) textureRefs.add(uuid);
    textureRefs.add(name);
    const canonical = name.toLowerCase();
    if (textureNames.has(canonical)) issues.push(issue('warning', 'DUPLICATE_TEXTURE_NAME', `Duplicate texture name: "${name}".`));
    else textureNames.set(canonical, texture);
    if (texture?.internal === false && !normalizedName(texture?.path)) {
      issues.push(issue('error', 'MISSING_EXTERNAL_TEXTURE_PATH', `External texture "${name}" has no path.`));
    }
    const width = texture?.width;
    const height = texture?.height;
    if (!Number.isFinite(width) || !Number.isFinite(height) || width <= 0 || height <= 0) {
      issues.push(issue('error', 'INVALID_TEXTURE_SIZE', `Texture "${name}" has invalid dimensions.`));
    } else if (!isPowerOfTwo(width) || !isPowerOfTwo(height)) {
      issues.push(issue('warning', 'NON_POWER_OF_TWO_TEXTURE', `Texture "${name}" is ${width}x${height}; review provider/project requirements.`));
    }
  }

  const elementNames = new Map();
  for (const element of elements) {
    const name = normalizedName(element?.name) || '<unnamed>';
    if (name !== '<unnamed>') {
      const canonical = name.toLowerCase();
      if (elementNames.has(canonical)) issues.push(issue('warning', 'DUPLICATE_ELEMENT_NAME', `Duplicate element name: "${name}".`));
      else elementNames.set(canonical, element);
    }

    if (isLocatorLike(element)) {
      if (!finiteVector3(locatorPosition(element))) issues.push(issue('error', 'INVALID_LOCATOR_POSITION', `Locator "${name}" has a malformed/non-finite position.`));
      if (!parentObject(element.parent)) issues.push(issue('warning', 'UNGROUPED_LOCATOR', `Locator "${name}" is not attached to an object-backed group/bone.`));
      continue;
    }

    if (!isCubeLike(element)) continue;

    if (!finiteVector3(element?.from) || !finiteVector3(element?.to)) {
      issues.push(issue('error', 'INVALID_ELEMENT_BOUNDS', `Cube element "${name}" has malformed/non-finite from/to bounds.`));
      continue;
    }
    if (element.origin !== undefined && !finiteVector3(element.origin)) issues.push(issue('error', 'INVALID_ELEMENT_PIVOT', `Cube element "${name}" has malformed/non-finite origin.`));
    const size = [0, 1, 2].map((axis) => element.to[axis] - element.from[axis]);
    if (size.some((value) => value < 0)) issues.push(issue('error', 'NEGATIVE_ELEMENT_SIZE', `Cube element "${name}" has negative size on at least one axis.`));
    else if (size.some((value) => value === 0)) issues.push(issue('warning', 'ZERO_ELEMENT_SIZE', `Cube element "${name}" has zero thickness on at least one axis.`));
    if (!parentObject(element.parent)) issues.push(issue('warning', 'UNGROUPED_ELEMENT', `Cube element "${name}" is not attached to an object-backed group/bone.`));

    const faces = element?.faces && typeof element.faces === 'object' ? Object.values(element.faces) : [];
    for (const face of faces) {
      if (!face || face.enabled === false) continue;
      const ref = normalizeTextureRef(face.texture);
      if (!ref || !textureRefs.has(ref)) issues.push(issue('error', 'MISSING_FACE_TEXTURE', `Cube element "${name}" has an enabled face with an unresolved texture reference.`));
      if (face.uv !== undefined && (!Array.isArray(face.uv) || face.uv.length < 4 || !face.uv.slice(0, 4).every(Number.isFinite))) issues.push(issue('error', 'INVALID_FACE_UV', `Cube element "${name}" has an enabled face with malformed UV coordinates.`));
    }
  }
  if (cubeElements.length > 0 && textures.length === 0) issues.push(issue('error', 'NO_TEXTURES', 'Model has renderable cube elements but no project texture.'));

  const animationNames = new Map();
  for (const animation of animations) {
    const name = normalizedName(animation?.name);
    if (!name) issues.push(issue('error', 'EMPTY_ANIMATION_NAME', 'An animation has no name.'));
    else {
      const canonical = name.toLowerCase();
      if (animationNames.has(canonical)) issues.push(issue('error', 'DUPLICATE_ANIMATION_NAME', `Duplicate animation name: "${name}".`));
      else animationNames.set(canonical, animation);
    }
    if (!Number.isFinite(animation?.length) || animation.length <= 0) issues.push(issue('warning', 'INVALID_ANIMATION_LENGTH', `Animation "${name || '<unnamed>'}" has zero, negative, or non-finite length.`));
    if (!['once', 'hold', 'loop'].includes(animation?.loop)) issues.push(issue('warning', 'UNKNOWN_LOOP_MODE', `Animation "${name || '<unnamed>'}" has unexpected loop mode "${animation?.loop}".`));
    const animators = animation?.animators && typeof animation.animators === 'object' ? animation.animators : {};
    for (const target of Object.keys(animators)) {
      if (!groupsByUuid.has(target)) issues.push(issue('warning', 'UNKNOWN_ANIMATOR_TARGET', `Animation "${name || '<unnamed>'}" targets unknown bone UUID "${target}".`));
    }
  }

  for (const required of Array.isArray(profile.requiredBones) ? profile.requiredBones : []) {
    const canonical = normalizedName(required).toLowerCase();
    if (canonical && !groupsByName.has(canonical)) issues.push(issue('error', 'MISSING_REQUIRED_BONE', `Required contract bone "${required}" is missing.`));
  }
  for (const required of Array.isArray(profile.requiredAnimations) ? profile.requiredAnimations : []) {
    const canonical = normalizedName(required).toLowerCase();
    if (canonical && !animationNames.has(canonical)) issues.push(issue('error', 'MISSING_REQUIRED_ANIMATION', `Required contract animation "${required}" is missing.`));
  }

  const bounds = computeBounds(cubeElements);
  if (bounds && Array.isArray(profile.maxSpan) && profile.maxSpan.length >= 3) {
    for (let axis = 0; axis < 3; axis += 1) {
      const limit = profile.maxSpan[axis];
      if (Number.isFinite(limit) && limit >= 0 && bounds.span[axis] > limit) {
        issues.push(issue('error', 'MODEL_SPAN_EXCEEDED', `Model span ${bounds.span.join(' x ')} exceeds contract maxSpan ${profile.maxSpan.slice(0, 3).join(' x ')}.`));
        break;
      }
    }
  }

  return summarize(issues, bounds, {
    groupCount: groups.length,
    elementCount: elements.length,
    cubeCount: cubeElements.length,
    locatorCount: locatorElements.length,
    textureCount: textures.length,
    animationCount: animations.length,
  });
}

module.exports = {validateProject, issue, summarize};
