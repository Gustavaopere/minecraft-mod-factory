'use strict';

const contractUtils = require('../common/contract_utils.js');
const {isPlainObject, applyOperationsTransaction} = contractUtils;

const MAX_MUTATION_OPERATIONS = 128;
const MAX_IDENTIFIER_LENGTH = 128;
const MAX_LABEL_LENGTH = 160;

const BATCH_FIELDS = new Set(['expectedRevision', 'label', 'operations', 'dryRun']);
const OPERATION_FIELDS = Object.freeze({
  add_bone: new Set(['type', 'id', 'name', 'pivot', 'parentId']),
  add_cube: new Set(['type', 'id', 'name', 'from', 'to', 'pivot', 'parentId']),
  add_locator: new Set(['type', 'id', 'name', 'position', 'parentId']),
  set_pivot: new Set(['type', 'targetId', 'pivot']),
  rename: new Set(['type', 'targetId', 'name']),
  reparent: new Set(['type', 'targetId', 'parentId']),
  mirror: new Set(['type', 'targetId', 'axis', 'center']),
});

class MutationContractError extends Error {
  constructor(code, message) {
    super(`${code}: ${message}`);
    this.name = 'MutationContractError';
    this.code = code;
  }
}

function fail(code, message) {
  throw new MutationContractError(code, message);
}

function boundedString(value, field, {allowNull = false, max = MAX_IDENTIFIER_LENGTH} = {}) {
  return contractUtils.boundedString(value, field, fail, {allowNull, max, code: 'INVALID_STRING'});
}

function nullableIdentifier(value, field) {
  return value === null || value === undefined ? null : boundedString(value, field);
}

function vector3(value, field) {
  return contractUtils.vector3(value, field, fail, 'INVALID_VECTOR3');
}

function finiteNumber(value, field) {
  return contractUtils.finiteNumber(value, field, fail, 'INVALID_NUMBER');
}

function rejectUnknownFields(value, allowed, code, context) {
  contractUtils.rejectUnknownFields(value, allowed, fail, code, context);
}

function validateOperation(value, index) {
  if (!isPlainObject(value)) fail('INVALID_MUTATION', `operations[${index}] must be an object.`);
  const type = typeof value.type === 'string' ? value.type : '';
  const fields = OPERATION_FIELDS[type];
  if (!fields) fail('UNSUPPORTED_MUTATION', `operations[${index}] type "${type || '<missing>'}" is not allowlisted.`);
  rejectUnknownFields(value, fields, 'UNKNOWN_OPERATION_FIELD', `operations[${index}]`);

  let output;
  switch (type) {
    case 'add_bone':
      output = {
        type,
        id: boundedString(value.id, `operations[${index}].id`),
        name: boundedString(value.name, `operations[${index}].name`),
        pivot: vector3(value.pivot, `operations[${index}].pivot`),
        parentId: nullableIdentifier(value.parentId, `operations[${index}].parentId`),
      };
      break;
    case 'add_cube':
      output = {
        type,
        id: boundedString(value.id, `operations[${index}].id`),
        name: boundedString(value.name, `operations[${index}].name`),
        from: vector3(value.from, `operations[${index}].from`),
        to: vector3(value.to, `operations[${index}].to`),
        pivot: vector3(value.pivot, `operations[${index}].pivot`),
        parentId: nullableIdentifier(value.parentId, `operations[${index}].parentId`),
      };
      break;
    case 'add_locator':
      output = {
        type,
        id: boundedString(value.id, `operations[${index}].id`),
        name: boundedString(value.name, `operations[${index}].name`),
        position: vector3(value.position, `operations[${index}].position`),
        parentId: nullableIdentifier(value.parentId, `operations[${index}].parentId`),
      };
      break;
    case 'set_pivot':
      output = {
        type,
        targetId: boundedString(value.targetId, `operations[${index}].targetId`),
        pivot: vector3(value.pivot, `operations[${index}].pivot`),
      };
      break;
    case 'rename':
      output = {
        type,
        targetId: boundedString(value.targetId, `operations[${index}].targetId`),
        name: boundedString(value.name, `operations[${index}].name`),
      };
      break;
    case 'reparent':
      output = {
        type,
        targetId: boundedString(value.targetId, `operations[${index}].targetId`),
        parentId: nullableIdentifier(value.parentId, `operations[${index}].parentId`),
      };
      break;
    case 'mirror': {
      const axis = boundedString(value.axis, `operations[${index}].axis`, {max: 1}).toLowerCase();
      if (!['x', 'y', 'z'].includes(axis)) fail('INVALID_MIRROR_AXIS', `operations[${index}].axis must be x, y, or z.`);
      output = {
        type,
        targetId: boundedString(value.targetId, `operations[${index}].targetId`),
        axis,
        center: finiteNumber(value.center, `operations[${index}].center`),
      };
      break;
    }
    default:
      fail('UNSUPPORTED_MUTATION', `operations[${index}] is not allowlisted.`);
  }
  return Object.freeze(output);
}

function validateMutationBatch(value) {
  if (!isPlainObject(value)) fail('INVALID_MUTATION_BATCH', 'Mutation batch must be an object.');
  rejectUnknownFields(value, BATCH_FIELDS, 'UNKNOWN_BATCH_FIELD', 'Mutation batch');

  const expectedRevision = boundedString(value.expectedRevision, 'expectedRevision', {max: MAX_IDENTIFIER_LENGTH});
  if (!Array.isArray(value.operations) || value.operations.length < 1) {
    fail('EMPTY_MUTATION_BATCH', 'operations must contain at least one mutation.');
  }
  if (value.operations.length > MAX_MUTATION_OPERATIONS) {
    fail('MUTATION_BATCH_TOO_LARGE', `operations exceeds the maximum of ${MAX_MUTATION_OPERATIONS}.`);
  }
  if (value.dryRun !== undefined && typeof value.dryRun !== 'boolean') {
    fail('INVALID_DRY_RUN', 'dryRun must be boolean when provided.');
  }

  const operations = value.operations.map(validateOperation);
  const addedIds = new Set();
  for (const operation of operations) {
    if (!operation.type.startsWith('add_')) continue;
    if (addedIds.has(operation.id)) fail('DUPLICATE_DECLARED_ID', `Mutation batch declares id "${operation.id}" more than once.`);
    addedIds.add(operation.id);
  }

  return Object.freeze({
    expectedRevision,
    label: value.label === undefined
      ? 'Minecraft Mod Factory Asset Toolkit Modeling/Rig Batch'
      : boundedString(value.label, 'label', {max: MAX_LABEL_LENGTH}),
    operations: Object.freeze(operations),
    dryRun: value.dryRun === true,
  });
}

function validateAdapter(adapter) {
  contractUtils.validateAdapterMethods(
    adapter,
    ['getRevision', 'preflight', 'beginTransaction', 'applyOperation', 'finishTransaction', 'cancelTransaction'],
    fail,
    'INVALID_MUTATION_ADAPTER',
    'Mutation adapter',
  );
}

function applyMutationBatch(adapter, input) {
  validateAdapter(adapter);
  const batch = validateMutationBatch(input);
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
    });
  }

  return applyOperationsTransaction(adapter, batch, beforeRevision);
}

module.exports = {
  MAX_MUTATION_OPERATIONS,
  MutationContractError,
  validateMutationBatch,
  applyMutationBatch,
};
