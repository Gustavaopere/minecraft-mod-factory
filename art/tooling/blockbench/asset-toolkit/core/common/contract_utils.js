'use strict';

function isPlainObject(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return false;
  const prototype = Object.getPrototypeOf(value);
  return prototype === Object.prototype || prototype === null;
}

function rejectUnknownFields(value, allowed, fail, code, context) {
  for (const key of Object.keys(value)) {
    if (!allowed.has(key)) fail(code, `${context} contains unsupported field "${key}".`);
  }
}

function boundedString(value, field, fail, {allowNull = false, max = 128, code = 'INVALID_STRING'} = {}) {
  if (allowNull && value === null) return null;
  if (typeof value !== 'string') fail(code, `${field} must be a string.`);
  const output = value.trim();
  if (!output || output.length > max) {
    fail(code, `${field} must contain 1-${max} non-whitespace characters.`);
  }
  return output;
}

function finiteNumber(value, field, fail, code = 'INVALID_NUMBER') {
  if (!Number.isFinite(value)) fail(code, `${field} must be finite.`);
  return value;
}

function vector3(value, field, fail, code = 'INVALID_VECTOR3') {
  if (!Array.isArray(value) || value.length !== 3 || !value.every(Number.isFinite)) {
    fail(code, `${field} must be an array of exactly three finite numbers.`);
  }
  return Object.freeze(value.slice());
}

function validateAdapterMethods(adapter, methods, fail, code, label) {
  if (!adapter || typeof adapter !== 'object') fail(code, `${label} is required.`);
  for (const method of methods) {
    if (typeof adapter[method] !== 'function') fail(code, `${label} is missing ${method}().`);
  }
}

function collectChangedIds(target, changed) {
  const values = Array.isArray(changed) ? changed : [changed];
  for (const value of values) {
    if (typeof value === 'string' && value && !target.includes(value)) target.push(value);
  }
}

function applyOperationsTransaction(adapter, batch, beforeRevision) {
  const changedIds = [];
  let begun = false;
  try {
    adapter.beginTransaction(batch.label);
    begun = true;
    for (const operation of batch.operations) {
      collectChangedIds(changedIds, adapter.applyOperation(operation));
    }
    adapter.finishTransaction(batch.label);
    begun = false;
    return Object.freeze({
      ok: true,
      dryRun: false,
      beforeRevision,
      afterRevision: adapter.getRevision(),
      applied: batch.operations.length,
      changedIds: Object.freeze(changedIds.slice()),
    });
  } catch (error) {
    if (begun) {
      try {
        adapter.cancelTransaction(true);
      } catch (rollbackError) {
        if (error && typeof error === 'object' && error.rollbackError === undefined) {
          Object.defineProperty(error, 'rollbackError', {value: rollbackError, enumerable: false});
        }
      }
    }
    throw error;
  }
}

module.exports = {
  isPlainObject,
  rejectUnknownFields,
  boundedString,
  finiteNumber,
  vector3,
  validateAdapterMethods,
  collectChangedIds,
  applyOperationsTransaction,
};
