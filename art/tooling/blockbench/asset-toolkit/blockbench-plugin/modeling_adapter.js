'use strict';

function fail(code, message) {
  const error = new Error(`${code}: ${message}`);
  error.code = code;
  throw error;
}

function array(value) {
  return Array.isArray(value) ? value : [];
}

function idOf(value) {
  if (typeof value === 'string') return value || null;
  return value && typeof value === 'object' && typeof value.uuid === 'string' && value.uuid ? value.uuid : null;
}

function parentIdOf(value) {
  if (!value) return null;
  return idOf(value);
}

function createBlockbenchModelingAdapter(bb) {
  const project = bb?.Blockbench?.Project;
  if (!project || typeof project !== 'object') fail('NO_PROJECT', 'No Blockbench project is open.');
  if (bb.Blockbench.isWeb !== false) fail('DESKTOP_REQUIRED', 'Modeling/rig mutations require desktop Blockbench.');
  for (const [name, value] of [['Group', bb.Group], ['Cube', bb.Cube], ['Locator', bb.Locator]]) {
    if (typeof value !== 'function') fail('BLOCKBENCH_API_UNAVAILABLE', `${name} constructor is unavailable.`);
  }
  if (!bb.Outliner || !Array.isArray(bb.Outliner.elements)) fail('BLOCKBENCH_API_UNAVAILABLE', 'Outliner.elements is unavailable.');
  if (!bb.Undo || ['initEdit', 'finishEdit', 'cancelEdit'].some((name) => typeof bb.Undo[name] !== 'function')) {
    fail('BLOCKBENCH_API_UNAVAILABLE', 'Blockbench Undo API is incomplete.');
  }

  let transactionOpen = false;

  function groups() {
    return Array.isArray(bb.Group.all) ? bb.Group.all : array(project.groups);
  }

  function elements() {
    return Array.isArray(bb.Outliner.elements) ? bb.Outliner.elements : array(project.elements);
  }

  function nodes() {
    const output = [];
    for (const node of groups().concat(elements())) {
      if (node && !output.includes(node)) output.push(node);
    }
    return output;
  }

  function kindOf(node) {
    if (!node) return null;
    if (groups().includes(node) || node instanceof bb.Group) return 'group';
    if (node instanceof bb.Cube) return 'cube';
    if (node instanceof bb.Locator) return 'locator';
    return 'element';
  }

  function findNode(nodeId) {
    return nodes().find((node) => idOf(node) === nodeId) || null;
  }

  function requireNode(nodeId) {
    const node = findNode(nodeId);
    if (!node) fail('NODE_NOT_FOUND', `Node "${nodeId}" does not exist.`);
    return node;
  }

  function requireParent(parentId) {
    if (parentId === null) return null;
    const parent = findNode(parentId);
    if (!parent) fail('PARENT_NOT_FOUND', `Parent "${parentId}" does not exist.`);
    if (kindOf(parent) !== 'group') fail('PARENT_NOT_GROUP', `Parent "${parentId}" is not a group/bone.`);
    return parent;
  }

  function getRevision() {
    const {createProjectSnapshot} = require('../live-bridge/project_snapshot.js');
    return createProjectSnapshot(project).projectRevision;
  }

  function preflight(operations) {
    const simulated = new Map();
    for (const node of nodes()) {
      const id = idOf(node);
      if (!id) continue;
      simulated.set(id, {
        id,
        kind: kindOf(node),
        name: typeof node.name === 'string' ? node.name : '',
        parentId: parentIdOf(node.parent),
      });
    }

    function simulatedParent(parentId) {
      if (parentId === null) return null;
      const parent = simulated.get(parentId);
      if (!parent) fail('PARENT_NOT_FOUND', `Parent "${parentId}" does not exist.`);
      if (parent.kind !== 'group') fail('PARENT_NOT_GROUP', `Parent "${parentId}" is not a group/bone.`);
      return parent;
    }

    function groupNameExists(name, excludeId = null) {
      const wanted = name.toLowerCase();
      return [...simulated.values()].some((node) => node.kind === 'group' && node.id !== excludeId && node.name.toLowerCase() === wanted);
    }

    function checkCycle(targetId, parentId) {
      if (parentId === null) return;
      if (targetId === parentId) fail('INVALID_PARENT_CYCLE', `Node "${targetId}" cannot parent itself.`);
      let cursor = parentId;
      const seen = new Set();
      while (cursor !== null) {
        if (cursor === targetId) fail('INVALID_PARENT_CYCLE', `Reparenting "${targetId}" below "${parentId}" would create a cycle.`);
        if (seen.has(cursor)) fail('INVALID_PARENT_CYCLE', `Existing simulated hierarchy contains a cycle at "${cursor}".`);
        seen.add(cursor);
        const node = simulated.get(cursor);
        if (!node) break;
        cursor = node.parentId;
      }
    }

    for (const operation of operations) {
      switch (operation.type) {
        case 'add_bone': {
          if (simulated.has(operation.id)) fail('DUPLICATE_NODE_ID', `Node id "${operation.id}" already exists.`);
          simulatedParent(operation.parentId);
          if (groupNameExists(operation.name)) fail('DUPLICATE_BONE_NAME', `Bone name "${operation.name}" already exists.`);
          simulated.set(operation.id, {id: operation.id, kind: 'group', name: operation.name, parentId: operation.parentId});
          break;
        }
        case 'add_cube':
        case 'add_locator': {
          if (simulated.has(operation.id)) fail('DUPLICATE_NODE_ID', `Node id "${operation.id}" already exists.`);
          simulatedParent(operation.parentId);
          simulated.set(operation.id, {
            id: operation.id,
            kind: operation.type === 'add_cube' ? 'cube' : 'locator',
            name: operation.name,
            parentId: operation.parentId,
          });
          break;
        }
        case 'set_pivot': {
          const target = simulated.get(operation.targetId);
          if (!target) fail('NODE_NOT_FOUND', `Node "${operation.targetId}" does not exist.`);
          if (!['group', 'cube'].includes(target.kind)) fail('PIVOT_UNSUPPORTED', `Node "${operation.targetId}" does not expose a modeling pivot.`);
          break;
        }
        case 'rename': {
          const target = simulated.get(operation.targetId);
          if (!target) fail('NODE_NOT_FOUND', `Node "${operation.targetId}" does not exist.`);
          if (target.kind === 'group' && groupNameExists(operation.name, target.id)) {
            fail('DUPLICATE_BONE_NAME', `Bone name "${operation.name}" already exists.`);
          }
          target.name = operation.name;
          break;
        }
        case 'reparent': {
          const target = simulated.get(operation.targetId);
          if (!target) fail('NODE_NOT_FOUND', `Node "${operation.targetId}" does not exist.`);
          simulatedParent(operation.parentId);
          checkCycle(target.id, operation.parentId);
          target.parentId = operation.parentId;
          break;
        }
        case 'mirror': {
          const target = simulated.get(operation.targetId);
          if (!target) fail('NODE_NOT_FOUND', `Node "${operation.targetId}" does not exist.`);
          if (target.kind !== 'cube') fail('MIRROR_UNSUPPORTED', 'PR3 mirror is restricted to cube elements.');
          break;
        }
        default:
          fail('UNSUPPORTED_MUTATION', `Mutation "${operation.type}" is not supported by the Blockbench adapter.`);
      }
    }
    return true;
  }

  function beginTransaction() {
    if (transactionOpen) fail('TRANSACTION_ALREADY_OPEN', 'A Blockbench Undo transaction is already open.');
    bb.Undo.initEdit({
      outliner: true,
      elements: elements().slice(),
      groups: groups().slice(),
    });
    transactionOpen = true;
  }

  function finishTransaction(label) {
    if (!transactionOpen) fail('NO_ACTIVE_TRANSACTION', 'No Blockbench Undo transaction is open.');
    bb.Undo.finishEdit(label, {
      outliner: true,
      elements: elements().slice(),
      groups: groups().slice(),
    });
    transactionOpen = false;
  }

  function cancelTransaction(revert) {
    if (!transactionOpen) return;
    try {
      bb.Undo.cancelEdit(revert === true);
    } finally {
      transactionOpen = false;
    }
  }

  function applyOperation(operation) {
    switch (operation.type) {
      case 'add_bone': {
        const parent = requireParent(operation.parentId);
        const node = new bb.Group({name: operation.name, origin: operation.pivot.slice()}, operation.id).init();
        node.addTo(parent || undefined);
        return node.uuid || operation.id;
      }
      case 'add_cube': {
        const parent = requireParent(operation.parentId);
        const node = new bb.Cube({
          name: operation.name,
          from: operation.from.slice(),
          to: operation.to.slice(),
          origin: operation.pivot.slice(),
        }, operation.id).init();
        node.addTo(parent || undefined);
        return node.uuid || operation.id;
      }
      case 'add_locator': {
        const parent = requireParent(operation.parentId);
        const node = new bb.Locator({name: operation.name, position: operation.position.slice()}, operation.id)
          .addTo(parent || undefined)
          .init();
        return node.uuid || operation.id;
      }
      case 'set_pivot': {
        const node = requireNode(operation.targetId);
        if (typeof node.extend !== 'function') fail('PIVOT_UNSUPPORTED', `Node "${operation.targetId}" cannot update its pivot.`);
        node.extend({origin: operation.pivot.slice()});
        return node.uuid || operation.targetId;
      }
      case 'rename': {
        const node = requireNode(operation.targetId);
        node.name = operation.name;
        return node.uuid || operation.targetId;
      }
      case 'reparent': {
        const node = requireNode(operation.targetId);
        const parent = requireParent(operation.parentId);
        if (typeof node.addTo !== 'function') fail('REPARENT_UNSUPPORTED', `Node "${operation.targetId}" cannot be reparented.`);
        node.addTo(parent || undefined);
        return node.uuid || operation.targetId;
      }
      case 'mirror': {
        const node = requireNode(operation.targetId);
        if (!(node instanceof bb.Cube) || typeof node.flip !== 'function') fail('MIRROR_UNSUPPORTED', `Node "${operation.targetId}" is not a mirrorable cube.`);
        node.flip({x: 0, y: 1, z: 2}[operation.axis], operation.center, false);
        return node.uuid || operation.targetId;
      }
      default:
        fail('UNSUPPORTED_MUTATION', `Mutation "${operation.type}" is not supported by the Blockbench adapter.`);
    }
  }

  return Object.freeze({
    getRevision,
    preflight,
    beginTransaction,
    applyOperation,
    finishTransaction,
    cancelTransaction,
  });
}

module.exports = {createBlockbenchModelingAdapter};
