'use strict';

function finiteVector3(value) {
  return Array.isArray(value) && value.length >= 3 && value.slice(0, 3).every(Number.isFinite);
}

function isPowerOfTwo(value) {
  return Number.isInteger(value) && value > 0 && (value & (value - 1)) === 0;
}

function normalizedName(value) {
  return typeof value === 'string' ? value.trim() : '';
}

function normalizeTextureRef(value) {
  if (typeof value !== 'string') return null;
  const trimmed = value.trim();
  if (!trimmed) return null;
  return trimmed.startsWith('#') ? trimmed.slice(1) : trimmed;
}

function parentObject(value) {
  return value && typeof value === 'object' ? value : null;
}

function hasOwn(value, key) {
  return !!value && typeof value === 'object' && Object.prototype.hasOwnProperty.call(value, key);
}

function isCubeLike(element) {
  return !!element && typeof element === 'object' && (
    hasOwn(element, 'to') || hasOwn(element, 'faces') || hasOwn(element, 'box_uv')
    || hasOwn(element, 'inflate') || hasOwn(element, 'autouv')
  );
}

function locatorPosition(element) {
  if (!element || typeof element !== 'object') return undefined;
  return hasOwn(element, 'position') ? element.position : element.from;
}

function isLocatorLike(element) {
  return !!element && typeof element === 'object'
    && (hasOwn(element, 'position') || hasOwn(element, 'from'))
    && !isCubeLike(element)
    && !hasOwn(element, 'vertices');
}

function computeBounds(elements) {
  const valid = (elements || []).filter((element) => isCubeLike(element) && finiteVector3(element?.from) && finiteVector3(element?.to));
  if (!valid.length) return null;
  const min = [Infinity, Infinity, Infinity];
  const max = [-Infinity, -Infinity, -Infinity];
  for (const element of valid) {
    for (let axis = 0; axis < 3; axis += 1) {
      min[axis] = Math.min(min[axis], element.from[axis], element.to[axis]);
      max[axis] = Math.max(max[axis], element.from[axis], element.to[axis]);
    }
  }
  return {min, max, span: max.map((value, axis) => value - min[axis])};
}

module.exports = {
  finiteVector3,
  isPowerOfTwo,
  normalizedName,
  normalizeTextureRef,
  parentObject,
  hasOwn,
  isCubeLike,
  locatorPosition,
  isLocatorLike,
  computeBounds,
};
