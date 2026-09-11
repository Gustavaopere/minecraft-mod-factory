(function (root, nativeRequire, factory) {
  'use strict';
  const api = factory(nativeRequire);
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (root && root.Plugin && root.Action && root.MenuBar && root.Blockbench) api.registerBlockbenchPlugin(root);
})(
  typeof globalThis !== 'undefined' ? globalThis : this,
  typeof require === 'function' ? require : null,
  function (nativeRequire) {
  'use strict';

  const nativeModuleAllowlist = new Set(["node:crypto"]);
  const modules = {
    "core/project-model/project_model.js": function(module, exports, require) {
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
    },
    "core/common/contract_utils.js": function(module, exports, require) {
      'use strict';

      function isPlainObject(value) {
        if (!value || typeof value !== 'object' || Array.isArray(value)) return false;
        const prototype = Object.getPrototypeOf(value);
        return prototype === Object.prototype || prototype === null;
      }

      function validateMinecraftNamespace(value, fail, code, message) {
        if (typeof value !== 'string' || !/^[a-z0-9_.-]+$/.test(value)) fail(code, message);
        return value;
      }

      function validateSafeResourceName(value, fail, code, message) {
        if (typeof value !== 'string' || !/^[a-z0-9_-]+$/.test(value)) fail(code, message);
        return value;
      }

      function normalizeBbmodelSourcePath(value, fail, code, missingMessage, invalidMessage) {
        if (typeof value !== 'string' || value.length === 0) fail(code, missingMessage);
        const normalized = value.replace(/\\/g, '/');
        if (!normalized.toLowerCase().endsWith('.bbmodel')) fail(code, invalidMessage);
        return normalized;
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
        validateMinecraftNamespace,
        validateSafeResourceName,
        normalizeBbmodelSourcePath,
        rejectUnknownFields,
        boundedString,
        finiteNumber,
        vector3,
        validateAdapterMethods,
        collectChangedIds,
        applyOperationsTransaction,
      };
    },
    "core/mutations/mutation_engine.js": function(module, exports, require) {
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
    },
    "core/animation/animation_engine.js": function(module, exports, require) {
      'use strict';

      const contractUtils = require('../common/contract_utils.js');
      const {isPlainObject, applyOperationsTransaction} = contractUtils;

      const MAX_ANIMATION_OPERATIONS = 128;
      const MAX_IDENTIFIER_LENGTH = 128;
      const MAX_LABEL_LENGTH = 160;
      const MAX_ANIMATION_LENGTH = 3600;
      const MAX_KEYFRAME_TIME = 3600;
      const MAX_CAPTURE_DIMENSION = 8192;

      const LOOP_MODES = new Set(['once', 'loop', 'hold']);
      const ANIMATION_CHANNELS = new Set(['position', 'rotation', 'scale']);
      const ANIMATION_EASINGS = new Set(['linear', 'bezier', 'catmullrom', 'step']);
      const EFFECT_MARKER_TYPES = new Set(['particle', 'sound', 'timeline', 'custom']);
      const DESTRUCTIVE_OPERATION_TYPES = new Set([
        'animation_delete',
        'animation_delete_keyframe',
        'animation_delete_effect_marker',
      ]);

      const BATCH_FIELDS = new Set(['expectedRevision', 'label', 'operations', 'dryRun', 'confirmationToken']);
      const OPERATION_FIELDS = Object.freeze({
        animation_create: new Set(['type', 'id', 'name', 'length', 'loop']),
        animation_update_settings: new Set(['type', 'animationId', 'name', 'length', 'loop']),
        animation_delete: new Set(['type', 'animationId']),
        animation_add_keyframe: new Set(['type', 'animationId', 'keyframeId', 'targetId', 'channel', 'time', 'value', 'easing']),
        animation_update_keyframe: new Set(['type', 'animationId', 'keyframeId', 'targetId', 'channel', 'time', 'value', 'easing']),
        animation_delete_keyframe: new Set(['type', 'animationId', 'keyframeId']),
        animation_add_effect_marker: new Set(['type', 'animationId', 'markerId', 'time', 'markerType', 'label']),
        animation_delete_effect_marker: new Set(['type', 'animationId', 'markerId']),
      });

      class AnimationContractError extends Error {
        constructor(code, message) {
          super(`${code}: ${message}`);
          this.name = 'AnimationContractError';
          this.code = code;
        }
      }

      function fail(code, message) {
        throw new AnimationContractError(code, message);
      }

      function rejectUnknownFields(value, allowed, code, context) {
        contractUtils.rejectUnknownFields(value, allowed, fail, code, context);
      }

      function boundedString(value, field, {max = MAX_IDENTIFIER_LENGTH} = {}) {
        return contractUtils.boundedString(value, field, fail, {max, code: 'INVALID_ANIMATION_STRING'});
      }

      function optionalBoundedString(value, field, options) {
        return value === undefined ? undefined : boundedString(value, field, options);
      }

      function finiteNumber(value, field) {
        return contractUtils.finiteNumber(value, field, fail, 'INVALID_ANIMATION_NUMBER');
      }

      function positiveLength(value, field) {
        const output = finiteNumber(value, field);
        if (output <= 0 || output > MAX_ANIMATION_LENGTH) {
          fail('INVALID_ANIMATION_LENGTH', `${field} must be greater than 0 and at most ${MAX_ANIMATION_LENGTH}.`);
        }
        return output;
      }

      function nonNegativeTime(value, field) {
        const output = finiteNumber(value, field);
        if (output < 0 || output > MAX_KEYFRAME_TIME) {
          fail('INVALID_ANIMATION_TIME', `${field} must be between 0 and ${MAX_KEYFRAME_TIME}.`);
        }
        return output;
      }

      function vector3(value, field) {
        return contractUtils.vector3(value, field, fail, 'INVALID_ANIMATION_VECTOR3');
      }

      function loopMode(value, field) {
        const output = boundedString(value, field, {max: 16}).toLowerCase();
        if (!LOOP_MODES.has(output)) fail('INVALID_ANIMATION_LOOP_MODE', `${field} is not provider-neutral.`);
        return output;
      }

      function channel(value, field) {
        const output = boundedString(value, field, {max: 32}).toLowerCase();
        if (!ANIMATION_CHANNELS.has(output)) fail('INVALID_ANIMATION_CHANNEL', `${field} is not allowlisted.`);
        return output;
      }

      function easing(value, field) {
        const output = boundedString(value, field, {max: 32}).toLowerCase();
        if (!ANIMATION_EASINGS.has(output)) fail('INVALID_ANIMATION_EASING', `${field} is not provider-neutral.`);
        return output;
      }

      function markerType(value, field) {
        const output = boundedString(value, field, {max: 32}).toLowerCase();
        if (!EFFECT_MARKER_TYPES.has(output)) fail('INVALID_EFFECT_MARKER_TYPE', `${field} is not allowlisted.`);
        return output;
      }

      function validateOperation(value, index) {
        if (!isPlainObject(value)) fail('INVALID_ANIMATION_OPERATION', `operations[${index}] must be an object.`);
        const type = typeof value.type === 'string' ? value.type : '';
        const fields = OPERATION_FIELDS[type];
        if (!fields) {
          fail('UNSUPPORTED_ANIMATION_OPERATION', `operations[${index}] type "${type || '<missing>'}" is not allowlisted.`);
        }
        rejectUnknownFields(value, fields, 'UNKNOWN_ANIMATION_OPERATION_FIELD', `operations[${index}]`);

        let output;
        switch (type) {
          case 'animation_create':
            output = {
              type,
              id: boundedString(value.id, `operations[${index}].id`),
              name: boundedString(value.name, `operations[${index}].name`),
              length: positiveLength(value.length, `operations[${index}].length`),
              loop: loopMode(value.loop, `operations[${index}].loop`),
            };
            break;
          case 'animation_update_settings': {
            const name = optionalBoundedString(value.name, `operations[${index}].name`);
            const length = value.length === undefined ? undefined : positiveLength(value.length, `operations[${index}].length`);
            const loop = value.loop === undefined ? undefined : loopMode(value.loop, `operations[${index}].loop`);
            if (name === undefined && length === undefined && loop === undefined) {
              fail('EMPTY_ANIMATION_UPDATE', `operations[${index}] must update name, length, or loop.`);
            }
            output = {
              type,
              animationId: boundedString(value.animationId, `operations[${index}].animationId`),
              ...(name === undefined ? {} : {name}),
              ...(length === undefined ? {} : {length}),
              ...(loop === undefined ? {} : {loop}),
            };
            break;
          }
          case 'animation_delete':
            output = {
              type,
              animationId: boundedString(value.animationId, `operations[${index}].animationId`),
            };
            break;
          case 'animation_add_keyframe':
          case 'animation_update_keyframe':
            output = {
              type,
              animationId: boundedString(value.animationId, `operations[${index}].animationId`),
              keyframeId: boundedString(value.keyframeId, `operations[${index}].keyframeId`),
              targetId: boundedString(value.targetId, `operations[${index}].targetId`),
              channel: channel(value.channel, `operations[${index}].channel`),
              time: nonNegativeTime(value.time, `operations[${index}].time`),
              value: vector3(value.value, `operations[${index}].value`),
              easing: easing(value.easing, `operations[${index}].easing`),
            };
            break;
          case 'animation_delete_keyframe':
            output = {
              type,
              animationId: boundedString(value.animationId, `operations[${index}].animationId`),
              keyframeId: boundedString(value.keyframeId, `operations[${index}].keyframeId`),
            };
            break;
          case 'animation_add_effect_marker':
            output = {
              type,
              animationId: boundedString(value.animationId, `operations[${index}].animationId`),
              markerId: boundedString(value.markerId, `operations[${index}].markerId`),
              time: nonNegativeTime(value.time, `operations[${index}].time`),
              markerType: markerType(value.markerType, `operations[${index}].markerType`),
              label: boundedString(value.label, `operations[${index}].label`, {max: MAX_LABEL_LENGTH}),
            };
            break;
          case 'animation_delete_effect_marker':
            output = {
              type,
              animationId: boundedString(value.animationId, `operations[${index}].animationId`),
              markerId: boundedString(value.markerId, `operations[${index}].markerId`),
            };
            break;
          default:
            fail('UNSUPPORTED_ANIMATION_OPERATION', `operations[${index}] is not allowlisted.`);
        }
        return Object.freeze(output);
      }

      function validateAnimationBatch(value) {
        if (!isPlainObject(value)) fail('INVALID_ANIMATION_BATCH', 'Animation batch must be an object.');
        rejectUnknownFields(value, BATCH_FIELDS, 'UNKNOWN_ANIMATION_BATCH_FIELD', 'Animation batch');

        const expectedRevision = boundedString(value.expectedRevision, 'expectedRevision');
        if (!Array.isArray(value.operations) || value.operations.length < 1) {
          fail('EMPTY_ANIMATION_BATCH', 'operations must contain at least one animation operation.');
        }
        if (value.operations.length > MAX_ANIMATION_OPERATIONS) {
          fail('ANIMATION_BATCH_TOO_LARGE', `operations exceeds the maximum of ${MAX_ANIMATION_OPERATIONS}.`);
        }
        if (value.dryRun !== undefined && typeof value.dryRun !== 'boolean') {
          fail('INVALID_ANIMATION_DRY_RUN', 'dryRun must be boolean when provided.');
        }

        const operations = value.operations.map(validateOperation);
        const declaredAnimations = new Set();
        const declaredKeyframes = new Set();
        const declaredMarkers = new Set();
        for (const operation of operations) {
          if (operation.type === 'animation_create') {
            if (declaredAnimations.has(operation.id)) {
              fail('DUPLICATE_ANIMATION_ID', `Animation id "${operation.id}" is declared more than once.`);
            }
            declaredAnimations.add(operation.id);
          } else if (operation.type === 'animation_add_keyframe') {
            const key = `${operation.animationId}\u0000${operation.keyframeId}`;
            if (declaredKeyframes.has(key)) fail('DUPLICATE_KEYFRAME_ID', `Keyframe "${operation.keyframeId}" is declared more than once.`);
            declaredKeyframes.add(key);
          } else if (operation.type === 'animation_add_effect_marker') {
            const key = `${operation.animationId}\u0000${operation.markerId}`;
            if (declaredMarkers.has(key)) fail('DUPLICATE_EFFECT_MARKER_ID', `Effect marker "${operation.markerId}" is declared more than once.`);
            declaredMarkers.add(key);
          }
        }

        return Object.freeze({
          expectedRevision,
          label: value.label === undefined
            ? 'Minecraft Mod Factory Asset Toolkit Generic Animation Batch'
            : boundedString(value.label, 'label', {max: MAX_LABEL_LENGTH}),
          operations: Object.freeze(operations),
          dryRun: value.dryRun === true,
          confirmationToken: value.confirmationToken === undefined
            ? undefined
            : boundedString(value.confirmationToken, 'confirmationToken', {max: 256}),
        });
      }

      function validateMutationAdapter(adapter) {
        contractUtils.validateAdapterMethods(
          adapter,
          ['getRevision', 'preflight', 'beginTransaction', 'applyOperation', 'finishTransaction', 'cancelTransaction'],
          fail,
          'INVALID_ANIMATION_ADAPTER',
          'Animation adapter',
        );
      }

      function destructiveDiff(operations) {
        return Object.freeze(operations.filter((operation) => DESTRUCTIVE_OPERATION_TYPES.has(operation.type)));
      }

      function confirmationTokenFor(beforeRevision, operations, diff) {
        const crypto = require('node:crypto');
        const payload = {beforeRevision, operations, diff};
        return `animation:v1:${crypto.createHash('sha256').update(JSON.stringify(payload)).digest('hex')}`;
      }

      function applyAnimationBatch(adapter, input) {
        validateMutationAdapter(adapter);
        const batch = validateAnimationBatch(input);
        const beforeRevision = adapter.getRevision();
        if (beforeRevision !== batch.expectedRevision) {
          fail('STALE_PROJECT_REVISION', `Expected ${batch.expectedRevision} but active project is ${beforeRevision}.`);
        }

        adapter.preflight(batch.operations);
        const diff = destructiveDiff(batch.operations);
        const confirmationToken = diff.length > 0 ? confirmationTokenFor(beforeRevision, batch.operations, diff) : null;
        if (batch.dryRun) {
          return Object.freeze({
            ok: true,
            dryRun: true,
            beforeRevision,
            afterRevision: beforeRevision,
            applied: 0,
            changedIds: Object.freeze([]),
            diff,
            confirmationToken,
          });
        }
        if (diff.length > 0) {
          if (!batch.confirmationToken) {
            fail('ANIMATION_CONFIRMATION_REQUIRED', 'Destructive animation operations require a revision-bound dry-run confirmation token.');
          }
          if (batch.confirmationToken !== confirmationToken) {
            fail('ANIMATION_CONFIRMATION_MISMATCH', 'Animation confirmation token does not match the current revision-bound diff.');
          }
        }

        return applyOperationsTransaction(adapter, batch, beforeRevision);
      }

      function poseChannel(value, field) {
        if (!Array.isArray(value) || value.length !== 3 || !value.every(Number.isFinite)) {
          fail('INVALID_LOOP_SEAM_POSE', `${field} must contain exactly three finite numbers.`);
        }
        return value;
      }

      function normalizePose(value, field) {
        if (!isPlainObject(value)) fail('INVALID_LOOP_SEAM_POSE', `${field} must be an object keyed by target id.`);
        const output = new Map();
        for (const targetId of Object.keys(value).sort((left, right) => left.localeCompare(right, 'en'))) {
          const target = value[targetId];
          if (!isPlainObject(target)) fail('INVALID_LOOP_SEAM_POSE', `${field}.${targetId} must be an object.`);
          const channels = new Map();
          for (const channelName of Object.keys(target).sort((left, right) => left.localeCompare(right, 'en'))) {
            if (!ANIMATION_CHANNELS.has(channelName)) {
              fail('INVALID_LOOP_SEAM_POSE', `${field}.${targetId}.${channelName} is not a provider-neutral transform channel.`);
            }
            channels.set(channelName, poseChannel(target[channelName], `${field}.${targetId}.${channelName}`));
          }
          output.set(targetId, channels);
        }
        return output;
      }

      function channelValueDelta(channelName, left, right) {
        const absolute = Math.abs(left - right);
        if (channelName !== 'rotation') return absolute;
        const wrapped = absolute % 360;
        return Math.min(wrapped, 360 - wrapped);
      }

      function validateLoopSeam(input) {
        if (!isPlainObject(input)) fail('INVALID_LOOP_SEAM_REQUEST', 'Loop seam request must be an object.');
        rejectUnknownFields(input, new Set(['startPose', 'endPose', 'tolerance']), 'UNKNOWN_LOOP_SEAM_FIELD', 'Loop seam request');
        const tolerance = finiteNumber(input.tolerance, 'tolerance');
        if (tolerance < 0) fail('INVALID_LOOP_SEAM_TOLERANCE', 'tolerance must be non-negative.');
        const start = normalizePose(input.startPose, 'startPose');
        const end = normalizePose(input.endPose, 'endPose');

        const targetIds = [...new Set([...start.keys(), ...end.keys()])].sort((left, right) => left.localeCompare(right, 'en'));
        let maxDelta = 0;
        const mismatches = [];
        for (const targetId of targetIds) {
          const left = start.get(targetId);
          const right = end.get(targetId);
          if (!left || !right) {
            mismatches.push(Object.freeze({targetId, channel: null, delta: null, reason: 'MISSING_TARGET'}));
            continue;
          }
          const channels = [...new Set([...left.keys(), ...right.keys()])].sort((left, right) => left.localeCompare(right, 'en'));
          for (const channelName of channels) {
            const leftValue = left.get(channelName);
            const rightValue = right.get(channelName);
            if (!leftValue || !rightValue) {
              mismatches.push(Object.freeze({targetId, channel: channelName, delta: null, reason: 'MISSING_CHANNEL'}));
              continue;
            }
            let channelDelta = 0;
            for (let index = 0; index < 3; index += 1) {
              channelDelta = Math.max(channelDelta, channelValueDelta(channelName, leftValue[index], rightValue[index]));
            }
            maxDelta = Math.max(maxDelta, channelDelta);
            if (channelDelta > tolerance) {
              mismatches.push(Object.freeze({targetId, channel: channelName, delta: channelDelta, reason: 'TOLERANCE_EXCEEDED'}));
            }
          }
        }
        const roundedMaxDelta = Number(maxDelta.toFixed(12));
        return Object.freeze({
          pass: mismatches.length === 0,
          tolerance,
          maxDelta: roundedMaxDelta,
          mismatches: Object.freeze(mismatches),
        });
      }

      function distance3(left, right) {
        const dx = left[0] - right[0];
        const dy = left[1] - right[1];
        const dz = left[2] - right[2];
        return Math.sqrt((dx * dx) + (dy * dy) + (dz * dz));
      }

      function diagnoseFootSlide(input) {
        if (!isPlainObject(input)) fail('INVALID_FOOT_SLIDE_REQUEST', 'Foot-slide request must be an object.');
        rejectUnknownFields(input, new Set(['samples']), 'UNKNOWN_FOOT_SLIDE_FIELD', 'Foot-slide request');
        if (!Array.isArray(input.samples)) fail('INVALID_FOOT_SLIDE_SAMPLES', 'samples must be an array.');

        let plantedSamples = 0;
        let previousPlanted = null;
        let distance = 0;
        for (let index = 0; index < input.samples.length; index += 1) {
          const sample = input.samples[index];
          if (!isPlainObject(sample)) fail('INVALID_FOOT_SLIDE_SAMPLE', `samples[${index}] must be an object.`);
          rejectUnknownFields(sample, new Set(['time', 'position', 'planted']), 'UNKNOWN_FOOT_SLIDE_SAMPLE_FIELD', `samples[${index}]`);
          nonNegativeTime(sample.time, `samples[${index}].time`);
          const position = vector3(sample.position, `samples[${index}].position`);
          if (typeof sample.planted !== 'boolean') fail('INVALID_FOOT_SLIDE_SAMPLE', `samples[${index}].planted must be boolean.`);
          if (!sample.planted) {
            previousPlanted = null;
            continue;
          }
          plantedSamples += 1;
          if (previousPlanted) distance += distance3(previousPlanted, position);
          previousPlanted = position;
        }

        if (plantedSamples < 2) {
          return Object.freeze({
            measurable: false,
            reason: 'INSUFFICIENT_CONTACT_SAMPLES',
            plantedSamples,
            distance: null,
          });
        }

        return Object.freeze({
          measurable: true,
          reason: null,
          plantedSamples,
          distance: Number(distance.toFixed(12)),
        });
      }

      function validateReadOnlyAdapter(adapter, method) {
        if (!adapter || typeof adapter !== 'object' || typeof adapter[method] !== 'function') {
          fail('INVALID_ANIMATION_ADAPTER', `Animation adapter is missing ${method}().`);
        }
      }

      function previewRequest(input) {
        if (!isPlainObject(input)) fail('INVALID_ANIMATION_PREVIEW_REQUEST', 'Preview request must be an object.');
        rejectUnknownFields(input, new Set(['animationId', 'time']), 'UNKNOWN_ANIMATION_PREVIEW_FIELD', 'Preview request');
        return Object.freeze({
          animationId: boundedString(input.animationId, 'animationId'),
          time: nonNegativeTime(input.time, 'time'),
        });
      }

      function playPreview(adapter, input) {
        validateReadOnlyAdapter(adapter, 'playPreview');
        return adapter.playPreview(previewRequest(input));
      }

      function stopPreview(adapter) {
        validateReadOnlyAdapter(adapter, 'stopPreview');
        return adapter.stopPreview();
      }

      function inspectPose(adapter, input) {
        validateReadOnlyAdapter(adapter, 'inspectPose');
        return adapter.inspectPose(previewRequest(input));
      }

      function capturePose(adapter, input) {
        validateReadOnlyAdapter(adapter, 'capturePose');
        if (!isPlainObject(input)) fail('INVALID_POSE_CAPTURE_REQUEST', 'Pose capture request must be an object.');
        rejectUnknownFields(input, new Set(['animationId', 'time', 'cameraPreset', 'resolution']), 'UNKNOWN_POSE_CAPTURE_FIELD', 'Pose capture request');
        const resolution = input.resolution;
        if (!Array.isArray(resolution) || resolution.length !== 2 || !resolution.every(Number.isInteger)
            || resolution.some((entry) => entry < 1 || entry > MAX_CAPTURE_DIMENSION)) {
          fail('INVALID_CAPTURE_RESOLUTION', `resolution must contain two integers in 1-${MAX_CAPTURE_DIMENSION}.`);
        }
        const request = Object.freeze({
          animationId: boundedString(input.animationId, 'animationId'),
          time: nonNegativeTime(input.time, 'time'),
          cameraPreset: boundedString(input.cameraPreset, 'cameraPreset', {max: 64}),
          resolution: Object.freeze(resolution.slice()),
        });
        return adapter.capturePose(request);
      }

      module.exports = {
        MAX_ANIMATION_OPERATIONS,
        AnimationContractError,
        validateAnimationBatch,
        applyAnimationBatch,
        validateLoopSeam,
        diagnoseFootSlide,
        playPreview,
        stopPreview,
        inspectPose,
        capturePose,
      };
    },
    "core/uv-texture/uv_texture_engine.js": function(module, exports, require) {
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
    },
    "core/uv-texture/uv_analysis.js": function(module, exports, require) {
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
    },
    "core/uv-texture/uv_pack.js": function(module, exports, require) {
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
    },
    "core/validator/validator.js": function(module, exports, require) {
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
    },
    "core/contract-profile/contract_profile.js": function(module, exports, require) {
      'use strict';

      function parseProfileJson(text) {
        const value = typeof text === 'string' ? text.trim() : '';
        if (!value) return {};
        const parsed = JSON.parse(value);
        if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) throw new Error('Profile must be a JSON object.');
        return parsed;
      }

      module.exports = {parseProfileJson};
    },
    "core/report/report.js": function(module, exports, require) {
      'use strict';

      function formatReport(result) {
        const lines = [`Structural QA: ${result.errors.length} error(s), ${result.warnings.length} warning(s).`];
        if (result.bounds) lines.push(`Bounds span: ${result.bounds.span.join(' x ')}.`);
        if (result.counts) lines.push(`Bones: ${result.counts.groupCount || 0}; elements: ${result.counts.elementCount || 0} (cubes: ${result.counts.cubeCount || 0}, locators: ${result.counts.locatorCount || 0}); textures: ${result.counts.textureCount || 0}; animations: ${result.counts.animationCount || 0}.`);
        const limited = result.issues.slice(0, 50);
        for (const item of limited) lines.push(`[${item.severity.toUpperCase()}] ${item.code}: ${item.message}`);
        if (result.issues.length > limited.length) lines.push(`... ${result.issues.length - limited.length} additional issue(s) omitted.`);
        lines.push('Texel-density/aesthetic approval still requires the asset contract and in-game visual QA.');
        return lines.join('\n');
      }

      module.exports = {formatReport};
    },
    "core/extension-registry/extension_registry.js": function(module, exports, require) {
      'use strict';

      const EXTENSION_STATES = Object.freeze([
        'REQUIRED_PROFILE', 'PREFERRED', 'OPTIONAL', 'EXPERIMENTAL', 'DEV_ONLY',
        'HUMAN_ONLY', 'AUDIT_REQUIRED', 'BLOCKED_LEGACY', 'INCOMPATIBLE_EDITOR',
        'LOADER_MISMATCH', 'PROVIDER_ABSENT', 'NOT_RUNTIME_AUTHORITY', 'DISABLED_BY_DEFAULT',
      ]);

      const BLOCKING_CLASSIFICATIONS = new Set([
        'HUMAN_ONLY', 'AUDIT_REQUIRED', 'BLOCKED_LEGACY', 'INCOMPATIBLE_EDITOR',
        'LOADER_MISMATCH', 'PROVIDER_ABSENT',
      ]);

      const EXTENSION_CATALOG = Object.freeze({
        geckolib: Object.freeze({
          pluginId: 'geckolib',
          title: 'GeckoLib Models & Animations',
          pluginVersion: '4.2.5',
          classification: 'REQUIRED_PROFILE',
          blockbenchCompatibility: Object.freeze({minInclusive: '5.0.0', maxExclusive: '6.0.0'}),
          mcpPolicy: 'ALLOWLIST',
          providerFamily: 'geckolib4',
        }),
        animation_utils: Object.freeze({
          pluginId: 'animation_utils',
          title: 'GeckoLib Animation Utils',
          pluginVersion: '4.1.3',
          classification: 'BLOCKED_LEGACY',
          mcpPolicy: 'NEVER',
          providerFamily: 'geckolib4',
        }),
        azurelib_utils: Object.freeze({
          pluginId: 'azurelib_utils',
          title: 'AzureLib Animator',
          pluginVersion: '2.1.5',
          classification: 'REQUIRED_PROFILE',
          blockbenchCompatibility: Object.freeze({auditedExact: Object.freeze(['5.1.6'])}),
          mcpPolicy: 'ALLOWLIST',
          providerFamily: 'azurelib',
        }),
        animation_to_json: Object.freeze({
          pluginId: 'animation_to_json',
          title: 'Animation to JSON Converter',
          pluginVersion: '1.0.1',
          classification: 'AUDIT_REQUIRED',
          mcpPolicy: 'NEVER',
          providerFamily: 'neoforge_native_animation',
        }),
        easy_model_entities: Object.freeze({
          pluginId: 'easy_model_entities',
          title: 'Easy Model Entities',
          pluginVersion: '1.0.0',
          classification: 'REQUIRED_PROFILE',
          blockbenchCompatibility: Object.freeze({minInclusive: '4.9.0'}),
          mcpPolicy: 'ALLOWLIST',
          providerFamily: 'easy_model_entities',
        }),
        cem_template_loader: Object.freeze({
          pluginId: 'cem_template_loader',
          title: 'CEM Template Loader',
          pluginVersion: '9.2.0',
          classification: 'REQUIRED_PROFILE',
          blockbenchCompatibility: Object.freeze({minInclusive: '5.0.0'}),
          mcpPolicy: 'ALLOWLIST',
          providerFamily: 'emf_cem',
        }),
        emf_animation_addon: Object.freeze({
          pluginId: 'emf_animation_addon',
          title: 'EMF Animation Addon',
          pluginVersion: '1.0.5',
          classification: 'PREFERRED',
          blockbenchCompatibility: Object.freeze({minInclusive: '4.9.0'}),
          mcpPolicy: 'ALLOWLIST',
          providerFamily: 'emf_cem',
        }),
        animated_java: Object.freeze({
          pluginId: 'animated_java',
          title: 'Animated Java',
          pluginVersion: '1.10.2',
          classification: 'OPTIONAL',
          blockbenchCompatibility: Object.freeze({minInclusive: '5.1.4'}),
          mcpPolicy: 'ALLOWLIST',
          providerFamily: 'animated_java',
        }),
      });

      function numericVersion(value) {
        if (typeof value !== 'string' || !/^\d+(?:\.\d+)*$/.test(value.trim())) return null;
        return value.trim().split('.').map((part) => Number.parseInt(part, 10));
      }

      function compareNumericVersions(a, b) {
        const left = numericVersion(a);
        const right = numericVersion(b);
        if (!left || !right) return null;
        const length = Math.max(left.length, right.length);
        for (let index = 0; index < length; index += 1) {
          const delta = (left[index] || 0) - (right[index] || 0);
          if (delta !== 0) return delta < 0 ? -1 : 1;
        }
        return 0;
      }

      function blockbenchCompatible(definition, blockbenchVersion) {
        const compatibility = definition && definition.blockbenchCompatibility;
        if (!compatibility) return true;
        if (typeof blockbenchVersion !== 'string' || !blockbenchVersion.trim()) return false;
        if (Array.isArray(compatibility.auditedExact)) return compatibility.auditedExact.includes(blockbenchVersion.trim());
        if (compatibility.minInclusive) {
          const comparison = compareNumericVersions(blockbenchVersion.trim(), compatibility.minInclusive);
          if (comparison === null || comparison < 0) return false;
        }
        if (compatibility.maxExclusive) {
          const comparison = compareNumericVersions(blockbenchVersion.trim(), compatibility.maxExclusive);
          if (comparison === null || comparison >= 0) return false;
        }
        return true;
      }

      function getExtensionDefinition(pluginId) {
        return typeof pluginId === 'string' ? EXTENSION_CATALOG[pluginId] || null : null;
      }

      function evaluateExtension(definition, session = {}) {
        if (!definition || typeof definition !== 'object' || typeof definition.pluginId !== 'string') {
          return {installed: false, compatible: false, versionMatch: false, mcpAllowed: false, reasons: ['INVALID_EXTENSION_DEFINITION']};
        }

        const reasons = [];
        const installedExtensions = Array.isArray(session.installedExtensions) ? session.installedExtensions : [];
        const installed = installedExtensions.find((entry) => entry && entry.pluginId === definition.pluginId) || null;
        const isInstalled = !!installed;
        if (!isInstalled) reasons.push('NOT_INSTALLED');

        const versionMatch = !!installed && typeof installed.pluginVersion === 'string'
          && installed.pluginVersion === definition.pluginVersion;
        if (isInstalled && !versionMatch) reasons.push('EXTENSION_VERSION_MISMATCH');

        const compatible = blockbenchCompatible(definition, session.blockbenchVersion);
        if (!compatible) reasons.push('BLOCKBENCH_VERSION_INCOMPATIBLE');

        const classificationBlocksMcp = BLOCKING_CLASSIFICATIONS.has(definition.classification) || definition.mcpPolicy === 'NEVER';
        if (classificationBlocksMcp) reasons.push('CLASSIFICATION_BLOCKS_MCP');

        const authorizedIds = Array.isArray(session.mcpAuthorizedExtensionIds) ? session.mcpAuthorizedExtensionIds : [];
        const authorized = authorizedIds.includes(definition.pluginId);
        if (!authorized) reasons.push('NOT_MCP_AUTHORIZED');

        const mcpAllowed = isInstalled && versionMatch && compatible && authorized
          && definition.mcpPolicy === 'ALLOWLIST' && !classificationBlocksMcp;

        return {installed: isInstalled, compatible, versionMatch, mcpAllowed, reasons: [...new Set(reasons)]};
      }

      module.exports = {
        EXTENSION_STATES,
        EXTENSION_CATALOG,
        getExtensionDefinition,
        evaluateExtension,
        compareNumericVersions,
      };
    },
    "core/provider-profile/physical_provider_snapshot.js": function(module, exports, require) {
      'use strict';

      // Physical modlist authority snapshot checked 2026-09-11 (595 top-level mods).
      // Presence is not API proof, runtime-health proof, or MCP authorization.
      const CURRENT_PHYSICAL_PROVIDER_SNAPSHOT = Object.freeze({
        geckolib: Object.freeze({modId: 'geckolib', version: '4.9.2', presence: 'PRESENT', health: 'UNPROVEN'}),
        azurelib: Object.freeze({modId: 'azurelib', version: '3.1.11', presence: 'PRESENT', health: 'UNPROVEN'}),
        easy_model_entities: Object.freeze({modId: 'easy_model_entities', version: '2.3.0', presence: 'PRESENT', health: 'UNPROVEN'}),
        entity_model_features: Object.freeze({modId: 'entity_model_features', version: '3.3.5', presence: 'PRESENT', health: 'UNPROVEN'}),
        photon: Object.freeze({modId: 'photon', version: '2.2.6.a', presence: 'PRESENT', health: 'KNOWN_RUNTIME_RISK'}),
        lodestone: Object.freeze({modId: 'lodestone', version: '1.8.2', presence: 'PRESENT', health: 'UNPROVEN'}),
        particle_effects: Object.freeze({modId: 'particle_effects', version: '1.5.0+1.21.1+neoforge', presence: 'PRESENT', health: 'PRESENTATION_ONLY'}),
        aaa_particles: Object.freeze({modId: null, version: null, presence: 'ABSENT', health: 'UNAVAILABLE'}),
        aaa_particles_world: Object.freeze({modId: null, version: null, presence: 'ABSENT', health: 'UNAVAILABLE'}),
      });

      const SNAPSHOT_METADATA = Object.freeze({
        checkedDate: '2026-09-11',
        topLevelModCount: 595,
        authority: 'physical-modlist',
      });

      module.exports = {CURRENT_PHYSICAL_PROVIDER_SNAPSHOT, SNAPSHOT_METADATA};
    },
    "core/provider-profile/provider_profiles.js": function(module, exports, require) {
      'use strict';

      const {getExtensionDefinition, evaluateExtension} = require('../extension-registry/extension_registry.js');

      function frozenProfile(value) {
        const result = {...value};
        result.capabilities = Object.freeze([...(value.capabilities || [])]);
        result.requiredExtensions = Object.freeze([...(value.requiredExtensions || [])]);
        if (value.requiredProvider) result.requiredProvider = Object.freeze({...value.requiredProvider, exactVersions: Object.freeze([...(value.requiredProvider.exactVersions || [])])});
        return Object.freeze(result);
      }

      const PROVIDER_PROFILES = Object.freeze([
        frozenProfile({
          id: 'java_block_item', family: 'java_block_item', authority: 'Minecraft Java block/item model runtime',
          requiredProvider: null, requiredExtensions: [], capabilities: ['model', 'uv', 'texture', 'display_transforms'],
        }),
        frozenProfile({
          id: 'neoforge_native_entity_animation', family: 'neoforge_native_animation', authority: 'NeoForge 21.1.248 JSON entity animation runtime', assetKind: 'entity_animation',
          requiredProvider: null, requiredExtensions: [],
          capabilities: ['animation', 'native_json_entity_animation', 'animation_definition_runtime', 'json_export_handoff'],
        }),
        frozenProfile({
          id: 'easy_model_entities_entity', family: 'easy_model_entities', authority: 'Easy Model Entities 2.3.0 runtime', assetKind: 'entity',
          requiredProvider: {modId: 'easy_model_entities', exactVersions: ['2.3.0']}, requiredExtensions: ['easy_model_entities'],
          capabilities: ['model', 'bbmodel_source', 'server_profile', 'render_profile', 'datapack_resourcepack_handoff', 'spawn_runtime'],
        }),
        frozenProfile({
          id: 'easy_model_entities_block_entity', family: 'easy_model_entities', authority: 'Easy Model Entities 2.3.0 runtime', assetKind: 'block_entity',
          requiredProvider: {modId: 'easy_model_entities', exactVersions: ['2.3.0']}, requiredExtensions: ['easy_model_entities'],
          capabilities: ['model', 'bbmodel_source', 'server_profile', 'render_profile', 'datapack_resourcepack_handoff', 'place_runtime'],
        }),
        ...['entity', 'item', 'block', 'armor'].map((kind) => frozenProfile({
          id: `geckolib4_${kind}`, family: 'geckolib4', authority: 'GeckoLib 4 runtime', assetKind: kind,
          requiredProvider: {modId: 'geckolib', exactVersions: ['4.9.2']}, requiredExtensions: ['geckolib'],
          capabilities: ['model', 'rig', 'animation', 'effect_keyframe_timing', 'provider_export_handoff'],
        })),
        ...['entity', 'item', 'block', 'armor'].map((kind) => frozenProfile({
          id: `azurelib_${kind}`, family: 'azurelib', authority: 'AzureLib runtime', assetKind: kind,
          requiredProvider: {modId: 'azurelib', exactVersions: ['3.1.11']}, requiredExtensions: ['azurelib_utils'],
          capabilities: ['model', 'rig', 'animation', 'custom_easing_authoring', 'provider_export_handoff'],
        })),
        frozenProfile({
          id: 'emf_cem_entity', family: 'emf_cem', authority: 'Entity Model Features resource-pack/CEM runtime', assetKind: 'entity',
          requiredProvider: {modId: 'entity_model_features', exactVersions: ['3.3.5']}, requiredExtensions: ['cem_template_loader'],
          capabilities: ['model', 'resource_pack_cem', 'animation_authoring', 'provider_export_handoff'],
        }),
        frozenProfile({
          id: 'animated_java_display_entities', family: 'animated_java', authority: 'Animated Java display-entity datapack/resource-pack export pipeline', assetKind: 'display_entities',
          requiredProvider: null, requiredExtensions: ['animated_java'],
          capabilities: ['model', 'rig', 'animation', 'locator', 'variant', 'display_entity_export_handoff'],
        }),
      ]);

      const PROFILE_BY_ID = new Map(PROVIDER_PROFILES.map((profile) => [profile.id, profile]));

      function listProviderProfiles() {
        return [...PROVIDER_PROFILES];
      }

      function getProviderProfile(profileId) {
        return typeof profileId === 'string' ? PROFILE_BY_ID.get(profileId) || null : null;
      }

      function physicalProviderEntry(physicalProviders, modId) {
        if (!physicalProviders || typeof physicalProviders !== 'object') return null;
        if (Array.isArray(physicalProviders)) return physicalProviders.find((entry) => entry && entry.modId === modId) || null;
        return physicalProviders[modId] || null;
      }

      function resolveProviderProfile(profileId, context = {}) {
        const profile = getProviderProfile(profileId);
        if (!profile) return {status: 'UNAVAILABLE', profile: null, reasons: ['UNKNOWN_PROFILE']};

        const reasons = [];
        if (profile.requiredProvider) {
          const actual = physicalProviderEntry(context.physicalProviders, profile.requiredProvider.modId);
          if (!actual || actual.presence !== 'PRESENT') {
            reasons.push('PROVIDER_ABSENT');
          } else {
            if (!profile.requiredProvider.exactVersions.includes(actual.version)) reasons.push('PROVIDER_VERSION_UNSUPPORTED');
            if (actual.health === 'KNOWN_RUNTIME_RISK') reasons.push('PROVIDER_RUNTIME_RISK');
          }
        }

        for (const extensionId of profile.requiredExtensions) {
          const definition = getExtensionDefinition(extensionId);
          if (!definition) {
            reasons.push('REQUIRED_EXTENSION_UNAVAILABLE');
            continue;
          }
          const result = evaluateExtension(definition, context);
          if (!result.mcpAllowed) reasons.push('REQUIRED_EXTENSION_UNAVAILABLE');
        }

        return {status: reasons.length ? 'UNAVAILABLE' : 'AVAILABLE', profile, reasons: [...new Set(reasons)]};
      }

      function canConvertProfile(sourceProfileId, targetProfileId) {
        const source = getProviderProfile(sourceProfileId);
        const target = getProviderProfile(targetProfileId);
        if (!source || !target) return false;
        return source.id === target.id;
      }

      module.exports = {
        PROVIDER_PROFILES,
        listProviderProfiles,
        getProviderProfile,
        resolveProviderProfile,
        canConvertProfile,
      };
    },
    "core/provider-adapter/geckolib4_adapter.js": function(module, exports, require) {
      'use strict';

      const {isPlainObject} = require('../common/contract_utils.js');

      const GECKOLIB4_AUTHORITY = Object.freeze({
        providerFamily: 'geckolib4',
        runtimeVersion: '4.9.2',
        runtimeSource: 'bernie-g/geckolib',
        runtimeRef: 'd57fc640de083ae67ec0051a02b2b4fb22f4d02b',
        blockbenchPluginId: 'geckolib',
        blockbenchPluginVersion: '4.2.5',
        blockbenchPluginSource: 'JannisX11/blockbench-plugins',
        blockbenchPluginRef: '96d3b694de7d44077de68181711816153c442a6f',
      });

      const GECKOLIB4_PROFILE_IDS = new Set([
        'geckolib4_entity',
        'geckolib4_block_entity',
        'geckolib4_item',
        'geckolib4_armor',
      ]);
      const GEO_FORMAT_VERSIONS = new Set(['1.12.0', '1.14.0', '1.21.0']);
      const LOOP_VALUES = new Set(['false', 'play_once', 'true', 'loop', 'hold_on_last_frame']);
      const LOCATOR_OBJECT_FIELDS = new Set(['ignore_inherited_scale', 'offset', 'rotation']);

      class GeckoLib4ContractError extends Error {
        constructor(code, message) {
          super(`${code}: ${message}`);
          this.name = 'GeckoLib4ContractError';
          this.code = code;
        }
      }

      function fail(code, message) {
        throw new GeckoLib4ContractError(code, message);
      }

      function nonEmptyString(value, field) {
        if (typeof value !== 'string' || value.length === 0) fail('INVALID_GECKOLIB4_STRING', `${field} must be a non-empty string.`);
        return value;
      }

      function finiteNonNegative(value, field) {
        if (!Number.isFinite(value) || value < 0) fail('INVALID_GECKOLIB4_NUMBER', `${field} must be a finite non-negative number.`);
        return value;
      }

      function vector3(value, field, code = 'INVALID_GECKOLIB4_VECTOR3') {
        if (!Array.isArray(value) || value.length !== 3 || !value.every(Number.isFinite)) {
          fail(code, `${field} must contain exactly three finite numbers.`);
        }
        return value;
      }

      function validateLocatorValue(value, field) {
        if (Array.isArray(value)) {
          vector3(value, field, 'INVALID_GECKOLIB4_LOCATOR');
          return;
        }
        if (!isPlainObject(value)) fail('INVALID_GECKOLIB4_LOCATOR', `${field} must be a vector or locator object.`);
        for (const key of Object.keys(value)) {
          if (!LOCATOR_OBJECT_FIELDS.has(key)) fail('INVALID_GECKOLIB4_LOCATOR', `${field}.${key} is not supported by GeckoLib 4.9.2.`);
        }
        if (value.ignore_inherited_scale !== undefined && typeof value.ignore_inherited_scale !== 'boolean') {
          fail('INVALID_GECKOLIB4_LOCATOR', `${field}.ignore_inherited_scale must be boolean.`);
        }
        if (value.offset !== undefined) vector3(value.offset, `${field}.offset`, 'INVALID_GECKOLIB4_LOCATOR');
        if (value.rotation !== undefined) vector3(value.rotation, `${field}.rotation`, 'INVALID_GECKOLIB4_LOCATOR');
        if (value.offset === undefined && value.rotation === undefined) {
          fail('INVALID_GECKOLIB4_LOCATOR', `${field} must define offset or rotation.`);
        }
      }

      function validateGeckoLib4GeoDocument(value) {
        if (!isPlainObject(value)) fail('INVALID_GECKOLIB4_GEO_DOCUMENT', 'Geo document must be an object.');
        const formatVersion = value.format_version;
        if (!GEO_FORMAT_VERSIONS.has(formatVersion)) {
          fail('UNSUPPORTED_GECKOLIB4_GEO_FORMAT', `format_version ${JSON.stringify(formatVersion)} is not supported by GeckoLib 4.9.2.`);
        }
        const geometries = value['minecraft:geometry'];
        if (!Array.isArray(geometries) || geometries.length === 0) {
          fail('INVALID_GECKOLIB4_GEO_DOCUMENT', 'minecraft:geometry must contain at least one geometry entry.');
        }

        let locatorCount = 0;
        geometries.forEach((geometry, geometryIndex) => {
          if (!isPlainObject(geometry)) fail('INVALID_GECKOLIB4_GEO_DOCUMENT', `minecraft:geometry[${geometryIndex}] must be an object.`);
          const bones = geometry.bones === undefined ? [] : geometry.bones;
          if (!Array.isArray(bones)) fail('INVALID_GECKOLIB4_GEO_DOCUMENT', `minecraft:geometry[${geometryIndex}].bones must be an array.`);
          bones.forEach((bone, boneIndex) => {
            if (!isPlainObject(bone)) fail('INVALID_GECKOLIB4_GEO_DOCUMENT', `bone ${boneIndex} must be an object.`);
            if (bone.locators === undefined) return;
            if (!isPlainObject(bone.locators)) fail('INVALID_GECKOLIB4_LOCATOR', `bone ${boneIndex}.locators must be an object.`);
            for (const [locatorName, locatorValue] of Object.entries(bone.locators)) {
              nonEmptyString(locatorName, `bone ${boneIndex} locator name`);
              validateLocatorValue(locatorValue, `bone ${boneIndex}.locators.${locatorName}`);
              locatorCount++;
            }
          });
        });

        return Object.freeze({ok: true, formatVersion, geometryCount: geometries.length, locatorCount});
      }

      function validateMathScalar(value, field) {
        if (Number.isFinite(value)) return;
        if (typeof value === 'string' && value.length > 0) return;
        fail('INVALID_GECKOLIB4_KEYFRAME', `${field} must be a finite number or Molang string.`);
      }

      function validateVectorExpression(value, field) {
        if (!Array.isArray(value) || value.length !== 3) fail('INVALID_GECKOLIB4_KEYFRAME', `${field} must contain exactly three values.`);
        value.forEach((entry, index) => validateMathScalar(entry, `${field}[${index}]`));
      }

      function validateKeyframeLeaf(value, field) {
        if (Number.isFinite(value) || (typeof value === 'string' && value.length > 0)) return;
        if (Array.isArray(value)) {
          validateVectorExpression(value, field);
          return;
        }
        if (!isPlainObject(value)) fail('INVALID_GECKOLIB4_KEYFRAME', `${field} has an unsupported keyframe shape.`);
        if (value.vector !== undefined) {
          validateVectorExpression(value.vector, `${field}.vector`);
          if (value.easing !== undefined && typeof value.easing !== 'string') fail('INVALID_GECKOLIB4_KEYFRAME', `${field}.easing must be a string.`);
          if (value.easingArgs !== undefined && (!Array.isArray(value.easingArgs) || !value.easingArgs.every(Number.isFinite))) {
            fail('INVALID_GECKOLIB4_KEYFRAME', `${field}.easingArgs must contain finite numbers.`);
          }
          return;
        }
        if (value.pre !== undefined) validateVectorExpression(value.pre, `${field}.pre`);
        if (value.post !== undefined) validateVectorExpression(value.post, `${field}.post`);
        if (value.pre === undefined && value.post === undefined) fail('INVALID_GECKOLIB4_KEYFRAME', `${field} must define vector, pre, or post.`);
        if (value.lerp_mode !== undefined && typeof value.lerp_mode !== 'string') fail('INVALID_GECKOLIB4_KEYFRAME', `${field}.lerp_mode must be a string.`);
      }

      function validateChannel(value, field) {
        if (value === undefined) return;
        if (Number.isFinite(value) || (typeof value === 'string' && value.length > 0) || Array.isArray(value)) {
          validateKeyframeLeaf(value, field);
          return;
        }
        if (!isPlainObject(value)) fail('INVALID_GECKOLIB4_KEYFRAME', `${field} must be a keyframe value or timestamp map.`);
        if (value.vector !== undefined || value.pre !== undefined || value.post !== undefined) {
          validateKeyframeLeaf(value, field);
          return;
        }
        for (const [timestamp, frame] of Object.entries(value)) {
          const time = Number(timestamp);
          if (!Number.isFinite(time) || time < 0) fail('INVALID_GECKOLIB4_TIMESTAMP', `${field}.${timestamp} is not a valid non-negative timestamp.`);
          validateKeyframeLeaf(frame, `${field}.${timestamp}`);
        }
      }

      function validateEffectTimestamp(timestamp, field) {
        const time = Number(timestamp);
        if (!Number.isFinite(time) || time < 0) fail('INVALID_GECKOLIB4_TIMESTAMP', `${field}.${timestamp} is not a valid non-negative timestamp.`);
      }

      function validateGeckoLib4AnimationDocument(value) {
        if (!isPlainObject(value)) fail('INVALID_GECKOLIB4_ANIMATION_DOCUMENT', 'Animation document must be an object.');
        if (!isPlainObject(value.animations) || Object.keys(value.animations).length === 0) {
          fail('INVALID_GECKOLIB4_ANIMATION_DOCUMENT', 'animations must be a non-empty object.');
        }

        const effectCounts = {sound: 0, particle: 0, timeline: 0};
        for (const [animationName, animation] of Object.entries(value.animations)) {
          nonEmptyString(animationName, 'animation name');
          if (!isPlainObject(animation)) fail('INVALID_GECKOLIB4_ANIMATION_DOCUMENT', `Animation ${animationName} must be an object.`);
          if (animation.animation_length !== undefined) finiteNonNegative(animation.animation_length, `${animationName}.animation_length`);
          if (animation.loop !== undefined) {
            const loop = typeof animation.loop === 'boolean' ? String(animation.loop) : animation.loop;
            if (typeof loop !== 'string' || !LOOP_VALUES.has(loop)) fail('INVALID_GECKOLIB4_LOOP', `${animationName}.loop is not a supported GeckoLib 4 loop mode.`);
          }
          const bones = animation.bones === undefined ? {} : animation.bones;
          if (!isPlainObject(bones)) fail('INVALID_GECKOLIB4_ANIMATION_DOCUMENT', `${animationName}.bones must be an object.`);
          for (const [boneName, channels] of Object.entries(bones)) {
            nonEmptyString(boneName, `${animationName} bone name`);
            if (!isPlainObject(channels)) fail('INVALID_GECKOLIB4_ANIMATION_DOCUMENT', `${animationName}.bones.${boneName} must be an object.`);
            validateChannel(channels.position, `${animationName}.bones.${boneName}.position`);
            validateChannel(channels.rotation, `${animationName}.bones.${boneName}.rotation`);
            validateChannel(channels.scale, `${animationName}.bones.${boneName}.scale`);
          }

          const sounds = animation.sound_effects === undefined ? {} : animation.sound_effects;
          if (!isPlainObject(sounds)) fail('INVALID_GECKOLIB4_EFFECTS', `${animationName}.sound_effects must be an object.`);
          for (const [timestamp, sound] of Object.entries(sounds)) {
            validateEffectTimestamp(timestamp, `${animationName}.sound_effects`);
            if (!isPlainObject(sound)) fail('INVALID_GECKOLIB4_EFFECTS', `${animationName}.sound_effects.${timestamp} must be an object.`);
            nonEmptyString(sound.effect, `${animationName}.sound_effects.${timestamp}.effect`);
            effectCounts.sound++;
          }

          const particles = animation.particle_effects === undefined ? {} : animation.particle_effects;
          if (!isPlainObject(particles)) fail('INVALID_GECKOLIB4_EFFECTS', `${animationName}.particle_effects must be an object.`);
          for (const [timestamp, particle] of Object.entries(particles)) {
            validateEffectTimestamp(timestamp, `${animationName}.particle_effects`);
            if (!isPlainObject(particle)) fail('INVALID_GECKOLIB4_EFFECTS', `${animationName}.particle_effects.${timestamp} must be an object.`);
            for (const field of ['effect', 'locator', 'pre_effect_script']) {
              if (particle[field] !== undefined && typeof particle[field] !== 'string') {
                fail('INVALID_GECKOLIB4_EFFECTS', `${animationName}.particle_effects.${timestamp}.${field} must be a string.`);
              }
            }
            effectCounts.particle++;
          }

          const timeline = animation.timeline === undefined ? {} : animation.timeline;
          if (!isPlainObject(timeline)) fail('INVALID_GECKOLIB4_EFFECTS', `${animationName}.timeline must be an object.`);
          for (const [timestamp, instruction] of Object.entries(timeline)) {
            validateEffectTimestamp(timestamp, `${animationName}.timeline`);
            const validInstruction = typeof instruction === 'string' || (Array.isArray(instruction) && instruction.every((entry) => typeof entry === 'string'));
            if (!validInstruction) fail('INVALID_GECKOLIB4_EFFECTS', `${animationName}.timeline.${timestamp} must be a string or string array.`);
            effectCounts.timeline++;
          }
        }

        return Object.freeze({
          ok: true,
          animationCount: Object.keys(value.animations).length,
          effectCounts: Object.freeze(effectCounts),
        });
      }

      function effectTimeKey(value) {
        return String(finiteNonNegative(value, 'effect marker time'));
      }

      function serializeGeckoLib4EffectMarker(marker, providerData) {
        if (!isPlainObject(marker) || !isPlainObject(providerData)) fail('INVALID_GECKOLIB4_EFFECT_MARKER', 'Effect marker and provider data must be objects.');
        const time = effectTimeKey(marker.time);
        switch (marker.markerType) {
          case 'sound':
            return Object.freeze({
              channel: 'sound_effects',
              time,
              value: Object.freeze({effect: nonEmptyString(providerData.effect, 'sound effect')}),
            });
          case 'particle': {
            const value = {};
            for (const [sourceField, targetField] of [['effect', 'effect'], ['locator', 'locator'], ['preEffectScript', 'pre_effect_script']]) {
              if (providerData[sourceField] !== undefined) value[targetField] = nonEmptyString(providerData[sourceField], `particle ${sourceField}`);
            }
            return Object.freeze({channel: 'particle_effects', time, value: Object.freeze(value)});
          }
          case 'timeline':
            if (typeof providerData.instruction !== 'string' && !(Array.isArray(providerData.instruction) && providerData.instruction.every((entry) => typeof entry === 'string'))) {
              fail('INVALID_GECKOLIB4_EFFECT_MARKER', 'timeline instruction must be a string or string array.');
            }
            return Object.freeze({channel: 'timeline', time, value: providerData.instruction});
          default:
            fail('UNSUPPORTED_GECKOLIB4_EFFECT_MARKER', `Marker type ${JSON.stringify(marker.markerType)} has no audited GeckoLib 4 mapping.`);
        }
      }

      function normalizedSourceAuthorityPath(value) {
        const output = nonEmptyString(value, 'sourcePath').replace(/\\/g, '/').replace(/\/$/, '');
        if (output.split('/').includes('..')) fail('INVALID_GECKOLIB4_SOURCE_PATH', 'sourcePath must not contain traversal segments.');
        return output;
      }

      function normalizedRelativePath(value, field) {
        const output = nonEmptyString(value, field).replace(/\\/g, '/').replace(/\/$/, '');
        if (output.startsWith('/') || /^[A-Za-z]:/.test(output) || output.split('/').includes('..')) fail('INVALID_GECKOLIB4_PATH', `${field} must be a safe relative path.`);
        return output;
      }

      function createGeckoLib4ExportPlan(input) {
        if (!isPlainObject(input)) fail('INVALID_GECKOLIB4_EXPORT_PLAN', 'Export plan request must be an object.');
        if (!GECKOLIB4_PROFILE_IDS.has(input.profileId)) fail('INVALID_GECKOLIB4_PROFILE', `Profile ${JSON.stringify(input.profileId)} is not a GeckoLib 4 profile.`);
        const sourcePath = normalizedSourceAuthorityPath(input.sourcePath);
        if (!sourcePath.toLowerCase().endsWith('.bbmodel')) fail('GECKOLIB4_SOURCE_MUST_BE_BBMODEL', 'Source authority must remain a .bbmodel file.');
        const outputDirectory = normalizedRelativePath(input.outputDirectory, 'outputDirectory');
        const resourceName = nonEmptyString(input.resourceName, 'resourceName');
        if (!/^[a-z0-9_.-]+$/.test(resourceName)) fail('INVALID_GECKOLIB4_RESOURCE_NAME', 'resourceName must be filesystem/resource-safe lowercase text.');
        if (input.includeAnimations !== undefined && typeof input.includeAnimations !== 'boolean') fail('INVALID_GECKOLIB4_EXPORT_PLAN', 'includeAnimations must be boolean.');

        const artifacts = [{kind: 'model', path: `${outputDirectory}/${resourceName}.geo.json`}];
        if (input.includeAnimations === true) artifacts.push({kind: 'animation', path: `${outputDirectory}/${resourceName}.animation.json`});

        return Object.freeze({
          providerFamily: 'geckolib4',
          profileId: input.profileId,
          sourcePath,
          preserveSource: true,
          artifacts: Object.freeze(artifacts.map((artifact) => Object.freeze(artifact))),
          runtimeEvidence: 'UNPROVEN',
        });
      }

      module.exports = {
        GECKOLIB4_AUTHORITY,
        GeckoLib4ContractError,
        validateGeckoLib4GeoDocument,
        validateGeckoLib4AnimationDocument,
        serializeGeckoLib4EffectMarker,
        createGeckoLib4ExportPlan,
      };
    },
    "core/provider-adapter/azurelib3_adapter.js": function(module, exports, require) {
      'use strict';

      const {isPlainObject} = require('../common/contract_utils.js');

      const AZURELIB3_AUTHORITY = Object.freeze({
        providerFamily: 'azurelib',
        runtimeVersion: '3.1.11',
        runtimeSource: 'AzureDoom/AzureLib',
        runtimeRef: '74ca485d43089c6953492ae7a10fc896eda30385',
        blockbenchPluginId: 'azurelib_utils',
        blockbenchPluginVersion: '2.1.5',
        blockbenchPluginSource: 'AzureDoom/AzureLib',
        blockbenchPluginRef: '4aac02dcefff5440874b3ec64871a1cd0feffadf',
        blockbenchFormatId: 'azure_model',
        animationFormatVersion: '1.8.0',
      });

      const AZURELIB3_PROFILE_IDS = new Set([
        'azurelib_entity',
        'azurelib_item',
        'azurelib_block',
        'azurelib_armor',
      ]);

      const GEO_FORMAT_VERSIONS = new Set(['1.12.0', '1.14.0', '1.21.0']);

      const LOOP_VALUES = new Set([
        'false',
        'true',
        'play_once',
        'hold_on_last_frame',
        'loop',
      ]);

      const EASING_NAMES = new Set([
        'none',
        'linear',
        'step',
        'easeinsine',
        'easeoutsine',
        'easeinoutsine',
        'easeinquad',
        'easeoutquad',
        'easeinoutquad',
        'easeincubic',
        'easeoutcubic',
        'easeinoutcubic',
        'easeinquart',
        'easeoutquart',
        'easeinoutquart',
        'easeinquint',
        'easeoutquint',
        'easeinoutquint',
        'easeinexpo',
        'easeoutexpo',
        'easeinoutexpo',
        'easeincirc',
        'easeoutcirc',
        'easeinoutcirc',
        'easeinback',
        'easeoutback',
        'easeinoutback',
        'easeinelastic',
        'easeoutelastic',
        'easeinoutelastic',
        'easeinbounce',
        'easeoutbounce',
        'easeinoutbounce',
        'bezier',
        'bezier_after',
        'catmullrom',
      ]);

      const ROOT_FIELDS = new Set(['format_version', 'includes', 'animations']);
      const ANIMATION_FIELDS = new Set([
        'animation_length',
        'loop',
        'bones',
        'sound_effects',
        'particle_effects',
        'timeline',
      ]);
      const BONE_FIELDS = new Set(['position', 'rotation', 'scale']);
      const KEYFRAME_FIELDS = new Set(['vector', 'easing', 'easingArgs', 'pre', 'post', 'lerp_mode']);
      const SOUND_FIELDS = new Set(['effect']);
      const PARTICLE_FIELDS = new Set(['effect', 'locator', 'pre_effect_script']);
      const INCLUDE_FIELDS = new Set(['file_id', 'animations']);

      class AzureLib3ContractError extends Error {
        constructor(code, message) {
          super(`${code}: ${message}`);
          this.name = 'AzureLib3ContractError';
          this.code = code;
        }
      }

      function fail(code, message) {
        throw new AzureLib3ContractError(code, message);
      }

      function nonEmptyString(value, field) {
        if (typeof value !== 'string' || value.length === 0) {
          fail('INVALID_AZURELIB3_STRING', `${field} must be a non-empty string.`);
        }
        return value;
      }

      function finiteNonNegative(value, field) {
        if (!Number.isFinite(value) || value < 0) {
          fail('INVALID_AZURELIB3_NUMBER', `${field} must be a finite non-negative number.`);
        }
        return value;
      }

      function rejectUnknownFields(value, allowedFields, field) {
        for (const key of Object.keys(value)) {
          if (!allowedFields.has(key)) {
            fail('UNPROVEN_AZURELIB3_RUNTIME_FIELD', `${field}.${key} is not part of the audited AzureLib 3.1.11 runtime contract.`);
          }
        }
      }

      function validateAzureLib3GeoDocument(value) {
        if (!isPlainObject(value)) {
          fail('INVALID_AZURELIB3_GEO_DOCUMENT', 'Geo document must be an object.');
        }
        if (Object.prototype.hasOwnProperty.call(value, 'azureIKChains')) {
          fail('UNPROVEN_AZURELIB3_RUNTIME_FIELD', 'azureIKChains is Blockbench authoring metadata and must not be serialized into AzureLib runtime geometry.');
        }

        const formatVersion = value.format_version;
        if (!GEO_FORMAT_VERSIONS.has(formatVersion)) {
          fail('UNSUPPORTED_AZURELIB3_GEO_FORMAT', `format_version ${JSON.stringify(formatVersion)} is not supported by AzureLib 3.1.11.`);
        }

        const geometries = value['minecraft:geometry'];
        if (!Array.isArray(geometries) || geometries.length === 0) {
          fail('INVALID_AZURELIB3_GEO_DOCUMENT', 'minecraft:geometry must contain at least one geometry entry.');
        }

        let boneCount = 0;
        geometries.forEach((geometry, geometryIndex) => {
          if (!isPlainObject(geometry)) {
            fail('INVALID_AZURELIB3_GEO_DOCUMENT', `minecraft:geometry[${geometryIndex}] must be an object.`);
          }
          const bones = geometry.bones === undefined ? [] : geometry.bones;
          if (!Array.isArray(bones)) {
            fail('INVALID_AZURELIB3_GEO_DOCUMENT', `minecraft:geometry[${geometryIndex}].bones must be an array.`);
          }
          bones.forEach((bone, boneIndex) => {
            if (!isPlainObject(bone)) {
              fail('INVALID_AZURELIB3_GEO_DOCUMENT', `minecraft:geometry[${geometryIndex}].bones[${boneIndex}] must be an object.`);
            }
            boneCount += 1;
          });
        });

        return Object.freeze({
          ok: true,
          formatVersion,
          geometryCount: geometries.length,
          boneCount,
        });
      }

      function validateMathScalar(value, field) {
        if (Number.isFinite(value)) return;
        if (typeof value === 'string' && value.length > 0) return;
        fail('INVALID_AZURELIB3_KEYFRAME', `${field} must be a finite number or Molang string.`);
      }

      function validateVectorExpression(value, field) {
        if (!Array.isArray(value) || value.length !== 3) {
          fail('INVALID_AZURELIB3_KEYFRAME', `${field} must contain exactly three values.`);
        }
        value.forEach((entry, index) => validateMathScalar(entry, `${field}[${index}]`));
      }

      function validateEasing(value, field) {
        if (typeof value !== 'string' || !EASING_NAMES.has(value.toLowerCase())) {
          fail('UNSUPPORTED_AZURELIB3_EASING', `${field} ${JSON.stringify(value)} is not registered by AzureLib 3.1.11.`);
        }
      }

      function validateEasingArgs(value, field) {
        if (!Array.isArray(value) || !value.every(Number.isFinite)) {
          fail('INVALID_AZURELIB3_KEYFRAME', `${field} must contain finite numbers.`);
        }
      }

      function validateKeyframeLeaf(value, field) {
        if (Number.isFinite(value) || (typeof value === 'string' && value.length > 0)) return;

        if (Array.isArray(value)) {
          validateVectorExpression(value, field);
          return;
        }

        if (!isPlainObject(value)) {
          fail('INVALID_AZURELIB3_KEYFRAME', `${field} has an unsupported keyframe shape.`);
        }

        rejectUnknownFields(value, KEYFRAME_FIELDS, field);

        if (value.vector !== undefined) {
          if (value.pre !== undefined || value.post !== undefined || value.lerp_mode !== undefined) {
            fail('INVALID_AZURELIB3_KEYFRAME', `${field} cannot mix vector/easing and Bedrock pre/post keyframe forms.`);
          }
          validateVectorExpression(value.vector, `${field}.vector`);
          if (value.easing !== undefined) validateEasing(value.easing, `${field}.easing`);
          if (value.easingArgs !== undefined) validateEasingArgs(value.easingArgs, `${field}.easingArgs`);
          return;
        }

        if (value.pre !== undefined) validateVectorExpression(value.pre, `${field}.pre`);
        if (value.post !== undefined) validateVectorExpression(value.post, `${field}.post`);
        if (value.pre === undefined && value.post === undefined) {
          fail('INVALID_AZURELIB3_KEYFRAME', `${field} must define vector, pre, or post.`);
        }
        if (value.easing !== undefined || value.easingArgs !== undefined) {
          fail('UNPROVEN_AZURELIB3_RUNTIME_FIELD', `${field} Bedrock pre/post form cannot carry AzureLib easing metadata in the audited runtime contract.`);
        }
        if (value.lerp_mode !== undefined) {
          if (typeof value.lerp_mode !== 'string' || !new Set(['linear', 'catmullrom']).has(value.lerp_mode.toLowerCase())) {
            fail('UNSUPPORTED_AZURELIB3_EASING', `${field}.lerp_mode ${JSON.stringify(value.lerp_mode)} is not an audited Bedrock interpolation mode.`);
          }
        }
      }

      function validateChannel(value, field) {
        if (value === undefined) return;
        if (Number.isFinite(value) || (typeof value === 'string' && value.length > 0) || Array.isArray(value)) {
          validateKeyframeLeaf(value, field);
          return;
        }
        if (!isPlainObject(value)) {
          fail('INVALID_AZURELIB3_KEYFRAME', `${field} must be a keyframe value or timestamp map.`);
        }
        if (value.vector !== undefined || value.pre !== undefined || value.post !== undefined) {
          validateKeyframeLeaf(value, field);
          return;
        }
        for (const [timestamp, frame] of Object.entries(value)) {
          const time = Number(timestamp);
          if (!Number.isFinite(time) || time < 0) {
            fail('INVALID_AZURELIB3_TIMESTAMP', `${field}.${timestamp} is not a valid non-negative timestamp.`);
          }
          validateKeyframeLeaf(frame, `${field}.${timestamp}`);
        }
      }

      function validateEffectTimestamp(timestamp, field) {
        const time = Number(timestamp);
        if (!Number.isFinite(time) || time < 0) {
          fail('INVALID_AZURELIB3_TIMESTAMP', `${field}.${timestamp} is not a valid non-negative timestamp.`);
        }
      }

      function validateIncludes(value) {
        if (value === undefined) return 0;
        if (!Array.isArray(value)) {
          fail('INVALID_AZURELIB3_INCLUDES', 'includes must be an array when present.');
        }

        value.forEach((entry, index) => {
          if (!isPlainObject(entry)) {
            fail('INVALID_AZURELIB3_INCLUDES', `includes[${index}] must be an object.`);
          }
          rejectUnknownFields(entry, INCLUDE_FIELDS, `includes[${index}]`);
          nonEmptyString(entry.file_id, `includes[${index}].file_id`);
          if (!Array.isArray(entry.animations) || entry.animations.length === 0) {
            fail('INVALID_AZURELIB3_INCLUDES', `includes[${index}].animations must be a non-empty string array.`);
          }
          entry.animations.forEach((name, animationIndex) => {
            nonEmptyString(name, `includes[${index}].animations[${animationIndex}]`);
          });
        });

        return value.length;
      }

      function validateLoop(value, field) {
        if (typeof value === 'boolean') return;
        if (typeof value !== 'string' || !LOOP_VALUES.has(value)) {
          fail('INVALID_AZURELIB3_LOOP', `${field} is not a registered AzureLib 3.1.11 loop type.`);
        }
      }

      function validateSoundEffects(value, animationName, effectCounts) {
        const sounds = value === undefined ? {} : value;
        if (!isPlainObject(sounds)) {
          fail('INVALID_AZURELIB3_EFFECTS', `${animationName}.sound_effects must be an object.`);
        }

        for (const [timestamp, sound] of Object.entries(sounds)) {
          validateEffectTimestamp(timestamp, `${animationName}.sound_effects`);
          if (Array.isArray(sound)) {
            fail('UNSUPPORTED_AZURELIB3_MULTI_EFFECT_PAYLOAD', `${animationName}.sound_effects.${timestamp} must contain one object because AzureLib 3.1.11 calls getAsJsonObject().`);
          }
          if (!isPlainObject(sound)) {
            fail('INVALID_AZURELIB3_EFFECTS', `${animationName}.sound_effects.${timestamp} must be an object.`);
          }
          rejectUnknownFields(sound, SOUND_FIELDS, `${animationName}.sound_effects.${timestamp}`);
          nonEmptyString(sound.effect, `${animationName}.sound_effects.${timestamp}.effect`);
          effectCounts.sound += 1;
        }
      }

      function validateParticleEffects(value, animationName, effectCounts) {
        const particles = value === undefined ? {} : value;
        if (!isPlainObject(particles)) {
          fail('INVALID_AZURELIB3_EFFECTS', `${animationName}.particle_effects must be an object.`);
        }

        for (const [timestamp, particle] of Object.entries(particles)) {
          validateEffectTimestamp(timestamp, `${animationName}.particle_effects`);
          if (Array.isArray(particle)) {
            fail('UNSUPPORTED_AZURELIB3_MULTI_EFFECT_PAYLOAD', `${animationName}.particle_effects.${timestamp} must contain one object because AzureLib 3.1.11 calls getAsJsonObject().`);
          }
          if (!isPlainObject(particle)) {
            fail('INVALID_AZURELIB3_EFFECTS', `${animationName}.particle_effects.${timestamp} must be an object.`);
          }
          rejectUnknownFields(particle, PARTICLE_FIELDS, `${animationName}.particle_effects.${timestamp}`);
          for (const field of PARTICLE_FIELDS) {
            if (particle[field] !== undefined && typeof particle[field] !== 'string') {
              fail('INVALID_AZURELIB3_EFFECTS', `${animationName}.particle_effects.${timestamp}.${field} must be a string.`);
            }
          }
          effectCounts.particle += 1;
        }
      }

      function validateTimeline(value, animationName, effectCounts) {
        const timeline = value === undefined ? {} : value;
        if (!isPlainObject(timeline)) {
          fail('INVALID_AZURELIB3_EFFECTS', `${animationName}.timeline must be an object.`);
        }

        for (const [timestamp, instruction] of Object.entries(timeline)) {
          validateEffectTimestamp(timestamp, `${animationName}.timeline`);
          const validInstruction = typeof instruction === 'string'
            || (Array.isArray(instruction) && instruction.every((entry) => typeof entry === 'string'));
          if (!validInstruction) {
            fail('INVALID_AZURELIB3_EFFECTS', `${animationName}.timeline.${timestamp} must be a string or string array.`);
          }
          effectCounts.timeline += 1;
        }
      }

      function validateAzureLib3AnimationDocument(value) {
        if (!isPlainObject(value)) {
          fail('INVALID_AZURELIB3_ANIMATION_DOCUMENT', 'Animation document must be an object.');
        }
        rejectUnknownFields(value, ROOT_FIELDS, 'document');

        if (value.format_version !== AZURELIB3_AUTHORITY.animationFormatVersion) {
          fail('UNSUPPORTED_AZURELIB3_ANIMATION_FORMAT', `format_version must be ${AZURELIB3_AUTHORITY.animationFormatVersion}.`);
        }

        const includeCount = validateIncludes(value.includes);

        if (!isPlainObject(value.animations) || Object.keys(value.animations).length === 0) {
          fail('INVALID_AZURELIB3_ANIMATION_DOCUMENT', 'animations must be a non-empty object.');
        }

        const effectCounts = {sound: 0, particle: 0, timeline: 0};

        for (const [animationName, animation] of Object.entries(value.animations)) {
          nonEmptyString(animationName, 'animation name');
          if (!isPlainObject(animation)) {
            fail('INVALID_AZURELIB3_ANIMATION_DOCUMENT', `Animation ${animationName} must be an object.`);
          }
          rejectUnknownFields(animation, ANIMATION_FIELDS, `animations.${animationName}`);

          if (animation.animation_length !== undefined) {
            finiteNonNegative(animation.animation_length, `${animationName}.animation_length`);
          }
          if (animation.loop !== undefined) validateLoop(animation.loop, `${animationName}.loop`);

          const bones = animation.bones === undefined ? {} : animation.bones;
          if (!isPlainObject(bones)) {
            fail('INVALID_AZURELIB3_ANIMATION_DOCUMENT', `${animationName}.bones must be an object.`);
          }

          for (const [boneName, channels] of Object.entries(bones)) {
            nonEmptyString(boneName, `${animationName} bone name`);
            if (!isPlainObject(channels)) {
              fail('INVALID_AZURELIB3_ANIMATION_DOCUMENT', `${animationName}.bones.${boneName} must be an object.`);
            }
            rejectUnknownFields(channels, BONE_FIELDS, `${animationName}.bones.${boneName}`);
            validateChannel(channels.position, `${animationName}.bones.${boneName}.position`);
            validateChannel(channels.rotation, `${animationName}.bones.${boneName}.rotation`);
            validateChannel(channels.scale, `${animationName}.bones.${boneName}.scale`);
          }

          validateSoundEffects(animation.sound_effects, animationName, effectCounts);
          validateParticleEffects(animation.particle_effects, animationName, effectCounts);
          validateTimeline(animation.timeline, animationName, effectCounts);
        }

        return Object.freeze({
          ok: true,
          animationCount: Object.keys(value.animations).length,
          includeCount,
          effectCounts: Object.freeze(effectCounts),
        });
      }

      function effectTimeKey(value) {
        return String(finiteNonNegative(value, 'effect marker time'));
      }

      function serializeAzureLib3EffectMarker(marker, providerData) {
        if (!isPlainObject(marker) || !isPlainObject(providerData)) {
          fail('INVALID_AZURELIB3_EFFECT_MARKER', 'Effect marker and provider data must be objects.');
        }

        const time = effectTimeKey(marker.time);

        switch (marker.markerType) {
          case 'sound': {
            rejectUnknownFields(providerData, new Set(['effect']), 'sound providerData');
            return Object.freeze({
              channel: 'sound_effects',
              time,
              value: Object.freeze({effect: nonEmptyString(providerData.effect, 'sound effect')}),
            });
          }
          case 'particle': {
            rejectUnknownFields(providerData, new Set(['effect', 'locator', 'preEffectScript']), 'particle providerData');
            const output = {};
            for (const [sourceField, targetField] of [
              ['effect', 'effect'],
              ['locator', 'locator'],
              ['preEffectScript', 'pre_effect_script'],
            ]) {
              if (providerData[sourceField] !== undefined) {
                output[targetField] = nonEmptyString(providerData[sourceField], `particle ${sourceField}`);
              }
            }
            return Object.freeze({channel: 'particle_effects', time, value: Object.freeze(output)});
          }
          case 'timeline': {
            rejectUnknownFields(providerData, new Set(['instruction']), 'timeline providerData');
            const instruction = providerData.instruction;
            const validInstruction = typeof instruction === 'string'
              || (Array.isArray(instruction) && instruction.every((entry) => typeof entry === 'string'));
            if (!validInstruction) {
              fail('INVALID_AZURELIB3_EFFECT_MARKER', 'timeline instruction must be a string or string array.');
            }
            return Object.freeze({channel: 'timeline', time, value: instruction});
          }
          default:
            fail('UNSUPPORTED_AZURELIB3_EFFECT_MARKER', `Marker type ${JSON.stringify(marker.markerType)} has no audited AzureLib 3.1.11 mapping.`);
        }
      }

      function normalizedSourceAuthorityPath(value) {
        const output = nonEmptyString(value, 'sourcePath').replace(/\\/g, '/').replace(/\/$/, '');
        if (output.split('/').includes('..')) {
          fail('INVALID_AZURELIB3_SOURCE_PATH', 'sourcePath must not contain traversal segments.');
        }
        return output;
      }

      function normalizedRelativePath(value, field) {
        const output = nonEmptyString(value, field).replace(/\\/g, '/').replace(/\/$/, '');
        if (output.startsWith('/') || /^[A-Za-z]:/.test(output) || output.split('/').includes('..')) {
          fail('INVALID_AZURELIB3_PATH', `${field} must be a safe relative path.`);
        }
        return output;
      }

      function createAzureLib3ExportPlan(input) {
        if (!isPlainObject(input)) {
          fail('INVALID_AZURELIB3_EXPORT_PLAN', 'Export plan request must be an object.');
        }
        if (!AZURELIB3_PROFILE_IDS.has(input.profileId)) {
          fail('INVALID_AZURELIB3_PROFILE', `Profile ${JSON.stringify(input.profileId)} is not an AzureLib 3 profile.`);
        }

        const sourcePath = normalizedSourceAuthorityPath(input.sourcePath);
        if (!sourcePath.toLowerCase().endsWith('.bbmodel')) {
          fail('AZURELIB3_SOURCE_MUST_BE_BBMODEL', 'Source authority must remain a .bbmodel file.');
        }

        const outputDirectory = normalizedRelativePath(input.outputDirectory, 'outputDirectory');
        const resourceName = nonEmptyString(input.resourceName, 'resourceName');
        if (!/^[a-z0-9_.-]+$/.test(resourceName)) {
          fail('INVALID_AZURELIB3_RESOURCE_NAME', 'resourceName must be filesystem/resource-safe lowercase text.');
        }
        if (input.includeAnimations !== undefined && typeof input.includeAnimations !== 'boolean') {
          fail('INVALID_AZURELIB3_EXPORT_PLAN', 'includeAnimations must be boolean.');
        }

        const artifacts = [
          Object.freeze({kind: 'model', path: `${outputDirectory}/${resourceName}.geo.json`}),
        ];
        if (input.includeAnimations) {
          artifacts.push(Object.freeze({kind: 'animation', path: `${outputDirectory}/${resourceName}.animation.json`}));
        }

        return Object.freeze({
          providerFamily: 'azurelib',
          profileId: input.profileId,
          sourcePath,
          preserveSource: true,
          artifacts: Object.freeze(artifacts),
          runtimeEvidence: 'UNPROVEN',
        });
      }

      module.exports = {
        AZURELIB3_AUTHORITY,
        AZURELIB3_PROFILE_IDS,
        AzureLib3ContractError,
        validateAzureLib3GeoDocument,
        validateAzureLib3AnimationDocument,
        serializeAzureLib3EffectMarker,
        createAzureLib3ExportPlan,
      };
    },
    "core/provider-adapter/neoforge_native_animation_adapter.js": function(module, exports, require) {
      'use strict';

      const {isPlainObject} = require('../common/contract_utils.js');

      const NEOFORGE_NATIVE_ANIMATION_AUTHORITY = Object.freeze({
        providerFamily: 'neoforge_native_animation',
        minecraftVersion: '1.21.1',
        neoforgeVersion: '21.1.248',
        runtimeSource: 'neoforged/NeoForge',
        runtimeRef: 'd8d64b44bb46323d44520fe27feda0a9a08c1c82',
        animationRoot: 'neoforge/animations/entity',
        blockbenchPluginId: 'animation_to_json',
        blockbenchPluginVersion: '1.0.1',
        blockbenchPluginSource: 'JannisX11/blockbench-plugins',
        blockbenchPluginRef: '91ba2b80c895960fe93de87fd0c30f9b840f28f2',
      });

      const ROOT_FIELDS = new Set(['length', 'loop', 'animations']);
      const CHANNEL_FIELDS = new Set(['bone', 'target', 'keyframes']);
      const KEYFRAME_FIELDS = new Set(['timestamp', 'target', 'interpolation']);
      const SERIALIZER_FIELDS = new Set(['length', 'loop', 'channels', 'effectMarkers']);
      const SERIALIZER_CHANNEL_FIELDS = new Set(['bone', 'channel', 'keyframes']);
      const SERIALIZER_KEYFRAME_FIELDS = new Set(['time', 'value', 'easing']);
      const TARGETS = new Set(['minecraft:position', 'minecraft:rotation', 'minecraft:scale']);
      const INTERPOLATIONS = new Set(['minecraft:linear', 'minecraft:catmullrom']);
      const PROFILE_ID = 'neoforge_native_entity_animation';

      class NeoForgeNativeAnimationContractError extends Error {
        constructor(code, message) {
          super(`${code}: ${message}`);
          this.name = 'NeoForgeNativeAnimationContractError';
          this.code = code;
        }
      }

      function fail(code, message) {
        throw new NeoForgeNativeAnimationContractError(code, message);
      }

      function rejectUnknownFields(value, allowed, field) {
        for (const key of Object.keys(value)) {
          if (!allowed.has(key)) {
            fail('UNPROVEN_NEOFORGE_NATIVE_ANIMATION_FIELD', `${field}.${key} is not part of the audited NeoForge 21.1.248 animation contract.`);
          }
        }
      }

      function finiteNumber(value, field) {
        if (!Number.isFinite(value)) fail('INVALID_NEOFORGE_NATIVE_ANIMATION_NUMBER', `${field} must be finite.`);
        return value;
      }

      function nonEmptyString(value, field) {
        if (typeof value !== 'string' || value.length === 0) {
          fail('INVALID_NEOFORGE_NATIVE_ANIMATION_STRING', `${field} must be a non-empty string.`);
        }
        return value;
      }

      function vector3(value, field) {
        if (!Array.isArray(value) || value.length !== 3 || !value.every(Number.isFinite)) {
          fail('INVALID_NEOFORGE_NATIVE_ANIMATION_VECTOR', `${field} must contain exactly three finite numbers.`);
        }
        return Object.freeze([...value]);
      }

      function resourceLocation(value, field) {
        const raw = nonEmptyString(value, field).toLowerCase();
        return raw.includes(':') ? raw : `minecraft:${raw}`;
      }

      function canonicalResourceLocation(value, field, allowed) {
        const canonical = resourceLocation(value, field);
        if (!allowed.has(canonical)) {
          fail('UNPROVEN_NEOFORGE_NATIVE_ANIMATION_TYPE', `${field} ${JSON.stringify(value)} is not a built-in type audited for NeoForge 21.1.248.`);
        }
        return canonical;
      }

      function serializerInterpolation(value, field) {
        const canonical = resourceLocation(value, field);
        if (!INTERPOLATIONS.has(canonical)) {
          fail('UNSUPPORTED_NEOFORGE_NATIVE_ANIMATION_INTERPOLATION', `${field} ${JSON.stringify(value)} has no audited NeoForge native representation.`);
        }
        return canonical;
      }

      function normalizedSourcePath(value) {
        if (typeof value !== 'string' || value.length === 0) {
          fail('NEOFORGE_NATIVE_ANIMATION_SOURCE_NOT_SAVED', 'Source project must be saved as a .bbmodel before NeoForge native export.');
        }
        const normalized = value.replace(/\\/g, '/');
        if (!normalized.toLowerCase().endsWith('.bbmodel')) {
          fail('NEOFORGE_NATIVE_ANIMATION_SOURCE_NOT_SAVED', 'Source authority must remain a saved .bbmodel file.');
        }
        return normalized;
      }

      function validateNamespace(value) {
        if (typeof value !== 'string' || !/^[a-z0-9_.-]+$/.test(value)) {
          fail('INVALID_NEOFORGE_NATIVE_ANIMATION_NAMESPACE', 'namespace must match the Minecraft lowercase namespace grammar.');
        }
        return value;
      }

      function validateResourceName(value) {
        if (typeof value !== 'string' || !/^[a-z0-9_-]+(?:\/[a-z0-9_-]+)*$/.test(value)) {
          fail('INVALID_NEOFORGE_NATIVE_ANIMATION_PATH', 'resourceName must be a safe lowercase relative resource path without an extension.');
        }
        return value;
      }

      function createNeoForgeNativeAnimationExportPlan(input) {
        if (!isPlainObject(input)) fail('INVALID_NEOFORGE_NATIVE_ANIMATION_EXPORT_PLAN', 'Export plan input must be an object.');
        if (input.profileId !== PROFILE_ID) {
          fail('NEOFORGE_NATIVE_ANIMATION_PROFILE_REQUIRED', `profileId must be ${PROFILE_ID}.`);
        }
        const sourcePath = normalizedSourcePath(input.sourcePath);
        const namespace = validateNamespace(input.namespace);
        const resourceName = validateResourceName(input.resourceName);
        return Object.freeze({
          profileId: PROFILE_ID,
          sourcePath,
          preserveSource: true,
          namespace,
          resourceName,
          outputPath: `assets/${namespace}/${NEOFORGE_NATIVE_ANIMATION_AUTHORITY.animationRoot}/${resourceName}.json`,
          runtimeEvidence: 'UNPROVEN',
        });
      }

      function validateNeoForgeNativeAnimationDocument(value) {
        if (!isPlainObject(value)) {
          fail('INVALID_NEOFORGE_NATIVE_ANIMATION_DOCUMENT', 'Animation document must be an object.');
        }
        rejectUnknownFields(value, ROOT_FIELDS, 'document');

        const length = finiteNumber(value.length, 'document.length');
        if (value.loop !== undefined && typeof value.loop !== 'boolean') {
          fail('INVALID_NEOFORGE_NATIVE_ANIMATION_LOOP', 'document.loop must be boolean when present.');
        }
        if (!Array.isArray(value.animations)) {
          fail('INVALID_NEOFORGE_NATIVE_ANIMATION_DOCUMENT', 'document.animations must be an array.');
        }

        let keyframeCount = 0;
        value.animations.forEach((channel, channelIndex) => {
          const field = `document.animations[${channelIndex}]`;
          if (!isPlainObject(channel)) fail('INVALID_NEOFORGE_NATIVE_ANIMATION_CHANNEL', `${field} must be an object.`);
          rejectUnknownFields(channel, CHANNEL_FIELDS, field);
          nonEmptyString(channel.bone, `${field}.bone`);
          canonicalResourceLocation(channel.target, `${field}.target`, TARGETS);
          if (!Array.isArray(channel.keyframes)) {
            fail('INVALID_NEOFORGE_NATIVE_ANIMATION_CHANNEL', `${field}.keyframes must be an array.`);
          }
          channel.keyframes.forEach((keyframe, keyframeIndex) => {
            const keyframeField = `${field}.keyframes[${keyframeIndex}]`;
            if (!isPlainObject(keyframe)) fail('INVALID_NEOFORGE_NATIVE_ANIMATION_KEYFRAME', `${keyframeField} must be an object.`);
            rejectUnknownFields(keyframe, KEYFRAME_FIELDS, keyframeField);
            finiteNumber(keyframe.timestamp, `${keyframeField}.timestamp`);
            vector3(keyframe.target, `${keyframeField}.target`);
            canonicalResourceLocation(keyframe.interpolation, `${keyframeField}.interpolation`, INTERPOLATIONS);
            keyframeCount += 1;
          });
        });

        return Object.freeze({
          ok: true,
          length,
          loop: value.loop === true,
          channelCount: value.animations.length,
          keyframeCount,
        });
      }

      function serializeNeoForgeNativeAnimation(input) {
        if (!isPlainObject(input)) {
          fail('INVALID_NEOFORGE_NATIVE_ANIMATION_SERIALIZER_INPUT', 'Animation serializer input must be an object.');
        }
        rejectUnknownFields(input, SERIALIZER_FIELDS, 'animation');

        const length = finiteNumber(input.length, 'animation.length');
        if (length <= 0) fail('INVALID_NEOFORGE_NATIVE_ANIMATION_NUMBER', 'animation.length must be greater than zero.');

        let loop;
        if (input.loop === 'loop') loop = true;
        else if (input.loop === 'once') loop = false;
        else fail('UNSUPPORTED_NEOFORGE_NATIVE_ANIMATION_LOOP_MODE', `animation.loop ${JSON.stringify(input.loop)} has no audited NeoForge native representation.`);

        if (input.effectMarkers !== undefined) {
          if (!Array.isArray(input.effectMarkers) || input.effectMarkers.length > 0) {
            fail('UNSUPPORTED_NEOFORGE_NATIVE_ANIMATION_EFFECT_MARKERS', 'NeoForge 21.1.248 JSON entity animations have no audited effect-marker representation.');
          }
        }
        if (!Array.isArray(input.channels)) {
          fail('INVALID_NEOFORGE_NATIVE_ANIMATION_SERIALIZER_INPUT', 'animation.channels must be an array.');
        }

        const animations = input.channels.map((channel, channelIndex) => {
          const field = `animation.channels[${channelIndex}]`;
          if (!isPlainObject(channel)) fail('INVALID_NEOFORGE_NATIVE_ANIMATION_CHANNEL', `${field} must be an object.`);
          rejectUnknownFields(channel, SERIALIZER_CHANNEL_FIELDS, field);
          const bone = nonEmptyString(channel.bone, `${field}.bone`);
          const target = canonicalResourceLocation(channel.channel, `${field}.channel`, TARGETS);
          if (!Array.isArray(channel.keyframes)) {
            fail('INVALID_NEOFORGE_NATIVE_ANIMATION_CHANNEL', `${field}.keyframes must be an array.`);
          }

          const keyframes = channel.keyframes.map((keyframe, keyframeIndex) => {
            const keyframeField = `${field}.keyframes[${keyframeIndex}]`;
            if (!isPlainObject(keyframe)) fail('INVALID_NEOFORGE_NATIVE_ANIMATION_KEYFRAME', `${keyframeField} must be an object.`);
            rejectUnknownFields(keyframe, SERIALIZER_KEYFRAME_FIELDS, keyframeField);
            const timestamp = finiteNumber(keyframe.time, `${keyframeField}.time`);
            if (timestamp < 0 || timestamp > length) {
              fail('INVALID_NEOFORGE_NATIVE_ANIMATION_TIMESTAMP', `${keyframeField}.time must be between 0 and animation.length.`);
            }
            const interpolation = serializerInterpolation(keyframe.easing, `${keyframeField}.easing`);
            return Object.freeze({
              timestamp,
              target: vector3(keyframe.value, `${keyframeField}.value`),
              interpolation,
            });
          }).sort((left, right) => left.timestamp - right.timestamp);

          return Object.freeze({bone, target, keyframes: Object.freeze(keyframes)});
        });

        const document = {
          length,
          loop,
          animations: Object.freeze(animations),
        };
        validateNeoForgeNativeAnimationDocument(document);
        return Object.freeze(document);
      }

      module.exports = {
        NEOFORGE_NATIVE_ANIMATION_AUTHORITY,
        NeoForgeNativeAnimationContractError,
        createNeoForgeNativeAnimationExportPlan,
        validateNeoForgeNativeAnimationDocument,
        serializeNeoForgeNativeAnimation,
      };
    },
    "core/provider-adapter/easy_model_entities_adapter.js": function(module, exports, require) {
      'use strict';

      const {
        isPlainObject,
        validateMinecraftNamespace,
        validateSafeResourceName,
        normalizeBbmodelSourcePath,
      } = require('../common/contract_utils.js');

      const EASY_MODEL_ENTITIES_AUTHORITY = Object.freeze({
        providerFamily: 'easy_model_entities',
        minecraftVersion: '1.21.1',
        targetNeoForgeVersion: '21.1.248',
        providerVersion: '2.3.0',
        providerNeoForgeBuildVersion: '21.1.92',
        providerNeoForgeMinimumVersion: '21.1.0',
        runtimeSource: 'MarkusBordihn/BOs-Easy-Model-Entities',
        runtimeRef: '8c912371838c2a26bbb383008ad3999280f075d1',
        blockbenchPluginId: 'easy_model_entities',
        blockbenchPluginVersion: '1.0.0',
        blockbenchPluginSource: 'MarkusBordihn/BOs-Easy-Model-Entities-Blockbench-Plugin',
        blockbenchPluginRef: '99c0bb118d1ef70fac7016c423b528c317e282dc',
        schemaVersion: '0.2.0',
        apiVersion: '2.3.0',
        serverProfileRoot: 'easy_model_entities/profiles',
        renderProfileRoot: 'easy_model_entities/render_profiles',
        modelRoot: 'easy_model_entities/models',
      });

      const PROFILE_MODEL_TYPES = Object.freeze({
        easy_model_entities_entity: 'entity',
        easy_model_entities_block_entity: 'block_entity',
      });

      const SERVER_ROOT_FIELDS = new Set([
        'schema_version', 'model_type', 'preset_type', 'version', 'entity', 'block_entity',
        'dimensions', 'movement', 'behavior', 'attributes',
      ]);
      const ENTITY_FIELDS = new Set(['type', 'movement_type', 'body_type']);
      const BLOCK_ENTITY_FIELDS = new Set(['type', 'body_type']);
      const DIMENSIONS_FIELDS = new Set(['width', 'height', 'eye_height']);
      const MOVEMENT_FIELDS = new Set(['speed', 'step_height', 'gravity']);
      const BEHAVIOR_FIELDS = new Set(['mode', 'look_at_players', 'random_stroll']);
      const ATTRIBUTES_FIELDS = new Set(['max_health', 'movement_speed', 'follow_range']);

      const RENDER_ROOT_FIELDS = new Set([
        'schema_version', 'preset_type', 'version', 'asset_fingerprint', 'body_type', 'model',
        'texture', 'textures', 'rendering', 'animation',
      ]);
      const RENDERING_FIELDS = new Set([
        'scale', 'shadow_radius', 'visible_bounds_width', 'visible_bounds_height',
        'visible_bounds_offset', 'opacity',
      ]);
      const ANIMATION_FIELDS = new Set([
        'mode', 'swing_speed', 'walk_speed_multiplier', 'idle_strength', 'gait', 'variant_mode',
      ]);

      const ENTITY_PRESETS = new Set([
        'custom', 'static', 'statue', 'aquatic_still', 'aquatic_swimming',
        'amphibious_still', 'amphibious_wandering', 'arthropod_still',
        'arthropod_wandering', 'cuboid_hopping', 'cuboid_still', 'floating_still',
        'humanoid_still', 'humanoid_wandering', 'quadruped_still',
        'quadruped_wandering', 'winged_humanoid_still', 'winged_humanoid_wandering',
        'winged_still', 'winged_wandering',
      ]);
      const BLOCK_ENTITY_PRESETS = new Set(['static', 'ticking', 'animated', 'animated_randomly']);
      const BODY_TYPES = new Set([
        'static', 'biped', 'quadruped', 'aquatic', 'amphibious', 'winged',
        'winged_humanoid', 'arthropod', 'cuboid', 'floating',
      ]);
      const MOVEMENT_TYPES = new Set(['ground', 'water', 'amphibious', 'static']);
      const BEHAVIOR_MODES = new Set(['idle_only', 'ambient', 'static', 'external_owner']);
      const ANIMATION_MODES = new Set(['automatic', 'random_idle', 'none']);
      const GAIT_TYPES = new Set(['natural', 'feline', 'ungulate']);
      const VARIANT_MODES = new Set(['random', 'sequential', 'none']);

      class EasyModelEntitiesContractError extends Error {
        constructor(code, message) {
          super(`${code}: ${message}`);
          this.name = 'EasyModelEntitiesContractError';
          this.code = code;
        }
      }

      function fail(code, message) {
        throw new EasyModelEntitiesContractError(code, message);
      }

      function rejectUnknownFields(value, allowed, code, field) {
        for (const key of Object.keys(value)) {
          if (!allowed.has(key)) fail(code, `${field}.${key} is outside the audited Easy Model Entities 2.3.0 contract.`);
        }
      }

      function requireObject(value, field, code = 'INVALID_EASY_MODEL_ENTITIES_PROFILE') {
        if (!isPlainObject(value)) fail(code, `${field} must be an object.`);
        return value;
      }

      function optionalObject(value, field, allowed, code) {
        if (value === undefined) return null;
        const object = requireObject(value, field, code);
        rejectUnknownFields(object, allowed, code, field);
        return object;
      }

      function finiteNumber(value, field, options = {}) {
        if (!Number.isFinite(value)) fail('INVALID_EASY_MODEL_ENTITIES_NUMBER', `${field} must be finite.`);
        if (options.positive && value <= 0) fail('INVALID_EASY_MODEL_ENTITIES_NUMBER', `${field} must be positive.`);
        if (options.nonNegative && value < 0) fail('INVALID_EASY_MODEL_ENTITIES_NUMBER', `${field} must not be negative.`);
        if (options.max !== undefined && value > options.max) fail('INVALID_EASY_MODEL_ENTITIES_NUMBER', `${field} exceeds the audited maximum.`);
        return value;
      }

      function optionalFinite(object, key, field, options) {
        if (object && object[key] !== undefined) finiteNumber(object[key], `${field}.${key}`, options);
      }

      function enumValue(value, allowed, field, code = 'INVALID_EASY_MODEL_ENTITIES_ENUM') {
        if (typeof value !== 'string' || !allowed.has(value)) fail(code, `${field} is not part of the audited Easy Model Entities contract.`);
        return value;
      }

      function optionalEnum(object, key, allowed, field) {
        if (object && object[key] !== undefined) enumValue(object[key], allowed, `${field}.${key}`);
      }

      function optionalBoolean(object, key, field) {
        if (object && object[key] !== undefined && typeof object[key] !== 'boolean') {
          fail('INVALID_EASY_MODEL_ENTITIES_BOOLEAN', `${field}.${key} must be boolean.`);
        }
      }

      function optionalString(object, key, field) {
        if (object[key] !== undefined && typeof object[key] !== 'string') {
          fail('INVALID_EASY_MODEL_ENTITIES_STRING', `${field}.${key} must be a string.`);
        }
      }

      function resourceLocation(value, field) {
        if (typeof value !== 'string' || !/^[a-z0-9_.-]+:[a-z0-9_./-]+$/.test(value)) {
          fail('INVALID_EASY_MODEL_ENTITIES_RESOURCE_LOCATION', `${field} must be a lowercase Minecraft resource location.`);
        }
        return value;
      }

      function optionalResourceLocation(object, key, field) {
        if (object && object[key] !== undefined) resourceLocation(object[key], `${field}.${key}`);
      }

      function expectedModelType(profileId) {
        const modelType = PROFILE_MODEL_TYPES[profileId];
        if (!modelType) fail('EASY_MODEL_ENTITIES_PROFILE_REQUIRED', 'profileId must identify an audited Easy Model Entities entity or block-entity profile.');
        return modelType;
      }

      function createEasyModelEntitiesExportPlan(input) {
        requireObject(input, 'exportPlan', 'INVALID_EASY_MODEL_ENTITIES_EXPORT_PLAN');
        const modelType = expectedModelType(input.profileId);
        const sourcePath = normalizeBbmodelSourcePath(
          input.sourcePath,
          fail,
          'EASY_MODEL_ENTITIES_SOURCE_NOT_SAVED',
          'Source project must be saved as a .bbmodel before Easy Model Entities handoff.',
          'Easy Model Entities source authority must remain a saved .bbmodel file.',
        );
        const namespace = validateMinecraftNamespace(
          input.namespace,
          fail,
          'INVALID_EASY_MODEL_ENTITIES_NAMESPACE',
          'namespace must match the Minecraft lowercase namespace grammar.',
        );
        const resourceName = validateSafeResourceName(
          input.resourceName,
          fail,
          'INVALID_EASY_MODEL_ENTITIES_RESOURCE_NAME',
          'resourceName must be a safe lowercase profile/model id without path traversal.',
        );
        return Object.freeze({
          profileId: input.profileId,
          modelType,
          sourcePath,
          preserveSource: true,
          namespace,
          resourceName,
          serverProfilePath: `data/${namespace}/${EASY_MODEL_ENTITIES_AUTHORITY.serverProfileRoot}/${modelType}/${resourceName}.json`,
          renderProfilePath: `assets/${namespace}/${EASY_MODEL_ENTITIES_AUTHORITY.renderProfileRoot}/${modelType}/${resourceName}.json`,
          modelPath: `assets/${namespace}/${EASY_MODEL_ENTITIES_AUTHORITY.modelRoot}/${resourceName}.bbmodel`,
          datapackFileName: `${resourceName}_datapack.zip`,
          resourcepackFileName: `${resourceName}_resourcepack.zip`,
          runtimeEvidence: 'UNPROVEN',
        });
      }

      function validateSchema(value, field) {
        if (value !== EASY_MODEL_ENTITIES_AUTHORITY.schemaVersion) {
          fail('EASY_MODEL_ENTITIES_SCHEMA_UNSUPPORTED', `${field} must be exactly ${EASY_MODEL_ENTITIES_AUTHORITY.schemaVersion} for the audited exporter contract.`);
        }
      }

      function validateEasyModelEntitiesServerProfile(value, options = {}) {
        const document = requireObject(value, 'serverProfile');
        rejectUnknownFields(document, SERVER_ROOT_FIELDS, 'UNPROVEN_EASY_MODEL_ENTITIES_PROFILE_FIELD', 'serverProfile');
        validateSchema(document.schema_version, 'serverProfile.schema_version');

        if (options.modelType !== 'entity' && options.modelType !== 'block_entity') {
          fail('INVALID_EASY_MODEL_ENTITIES_MODEL_TYPE', 'options.modelType must be entity or block_entity.');
        }
        if (document.model_type !== options.modelType) {
          fail('EASY_MODEL_ENTITIES_MODEL_TYPE_MISMATCH', `serverProfile.model_type must be ${options.modelType}.`);
        }
        const presets = options.modelType === 'block_entity' ? BLOCK_ENTITY_PRESETS : ENTITY_PRESETS;
        enumValue(document.preset_type, presets, 'serverProfile.preset_type');
        optionalString(document, 'version', 'serverProfile');

        const entity = optionalObject(document.entity, 'serverProfile.entity', ENTITY_FIELDS, 'UNPROVEN_EASY_MODEL_ENTITIES_PROFILE_FIELD');
        const blockEntity = optionalObject(document.block_entity, 'serverProfile.block_entity', BLOCK_ENTITY_FIELDS, 'UNPROVEN_EASY_MODEL_ENTITIES_PROFILE_FIELD');
        const dimensions = optionalObject(document.dimensions, 'serverProfile.dimensions', DIMENSIONS_FIELDS, 'UNPROVEN_EASY_MODEL_ENTITIES_PROFILE_FIELD');
        const movement = optionalObject(document.movement, 'serverProfile.movement', MOVEMENT_FIELDS, 'UNPROVEN_EASY_MODEL_ENTITIES_PROFILE_FIELD');
        const behavior = optionalObject(document.behavior, 'serverProfile.behavior', BEHAVIOR_FIELDS, 'UNPROVEN_EASY_MODEL_ENTITIES_PROFILE_FIELD');
        const attributes = optionalObject(document.attributes, 'serverProfile.attributes', ATTRIBUTES_FIELDS, 'UNPROVEN_EASY_MODEL_ENTITIES_PROFILE_FIELD');

        if (options.modelType === 'entity' && blockEntity) fail('EASY_MODEL_ENTITIES_MODEL_TYPE_MISMATCH', 'entity profiles must not carry block_entity settings.');
        if (options.modelType === 'block_entity' && (entity || movement || behavior || attributes)) {
          fail('EASY_MODEL_ENTITIES_MODEL_TYPE_MISMATCH', 'block_entity profiles must not carry entity-only settings.');
        }

        optionalResourceLocation(entity, 'type', 'serverProfile.entity');
        optionalEnum(entity, 'movement_type', MOVEMENT_TYPES, 'serverProfile.entity');
        optionalEnum(entity, 'body_type', BODY_TYPES, 'serverProfile.entity');
        optionalResourceLocation(blockEntity, 'type', 'serverProfile.block_entity');
        optionalEnum(blockEntity, 'body_type', BODY_TYPES, 'serverProfile.block_entity');

        optionalFinite(dimensions, 'width', 'serverProfile.dimensions', {positive: true});
        optionalFinite(dimensions, 'height', 'serverProfile.dimensions', {positive: true});
        optionalFinite(dimensions, 'eye_height', 'serverProfile.dimensions', {nonNegative: true});
        optionalFinite(movement, 'speed', 'serverProfile.movement', {nonNegative: true});
        optionalFinite(movement, 'step_height', 'serverProfile.movement', {nonNegative: true});
        optionalBoolean(movement, 'gravity', 'serverProfile.movement');
        optionalEnum(behavior, 'mode', BEHAVIOR_MODES, 'serverProfile.behavior');
        optionalBoolean(behavior, 'look_at_players', 'serverProfile.behavior');
        optionalBoolean(behavior, 'random_stroll', 'serverProfile.behavior');
        optionalFinite(attributes, 'max_health', 'serverProfile.attributes', {positive: true});
        optionalFinite(attributes, 'movement_speed', 'serverProfile.attributes', {nonNegative: true});
        optionalFinite(attributes, 'follow_range', 'serverProfile.attributes', {nonNegative: true});

        return Object.freeze({ok: true, schemaVersion: document.schema_version, modelType: document.model_type, presetType: document.preset_type});
      }

      function validateTextures(value, field) {
        if (value === undefined) return;
        const object = requireObject(value, field, 'INVALID_EASY_MODEL_ENTITIES_TEXTURES');
        for (const [key, location] of Object.entries(object)) {
          if (!/^\d+$/.test(key)) fail('INVALID_EASY_MODEL_ENTITIES_TEXTURES', `${field} keys must be non-negative integer texture indices.`);
          resourceLocation(location, `${field}.${key}`);
        }
      }

      function validateEasyModelEntitiesRenderProfile(value, options = {}) {
        const document = requireObject(value, 'renderProfile', 'INVALID_EASY_MODEL_ENTITIES_RENDER_PROFILE');
        rejectUnknownFields(document, RENDER_ROOT_FIELDS, 'UNPROVEN_EASY_MODEL_ENTITIES_RENDER_FIELD', 'renderProfile');
        validateSchema(document.schema_version, 'renderProfile.schema_version');
        enumValue(document.preset_type, ENTITY_PRESETS, 'renderProfile.preset_type');
        optionalString(document, 'version', 'renderProfile');
        optionalString(document, 'asset_fingerprint', 'renderProfile');
        if (document.body_type !== undefined) enumValue(document.body_type, BODY_TYPES, 'renderProfile.body_type');

        const namespace = validateMinecraftNamespace(
          options.namespace,
          fail,
          'INVALID_EASY_MODEL_ENTITIES_NAMESPACE',
          'namespace must match the Minecraft lowercase namespace grammar.',
        );
        const resourceName = validateSafeResourceName(
          options.resourceName,
          fail,
          'INVALID_EASY_MODEL_ENTITIES_RESOURCE_NAME',
          'resourceName must be a safe lowercase profile/model id without path traversal.',
        );
        const expectedModel = `${namespace}:${EASY_MODEL_ENTITIES_AUTHORITY.modelRoot}/${resourceName}`;
        if (document.model !== expectedModel) {
          fail('EASY_MODEL_ENTITIES_MODEL_PATH_MISMATCH', `renderProfile.model must reference the preserved model ${expectedModel}.`);
        }
        optionalResourceLocation(document, 'texture', 'renderProfile');
        validateTextures(document.textures, 'renderProfile.textures');

        const rendering = optionalObject(document.rendering, 'renderProfile.rendering', RENDERING_FIELDS, 'UNPROVEN_EASY_MODEL_ENTITIES_RENDER_FIELD');
        optionalFinite(rendering, 'scale', 'renderProfile.rendering', {positive: true});
        optionalFinite(rendering, 'shadow_radius', 'renderProfile.rendering', {nonNegative: true});
        optionalFinite(rendering, 'visible_bounds_width', 'renderProfile.rendering', {nonNegative: true});
        optionalFinite(rendering, 'visible_bounds_height', 'renderProfile.rendering', {nonNegative: true});
        if (rendering?.visible_bounds_offset !== undefined) {
          const offset = rendering.visible_bounds_offset;
          if (!Array.isArray(offset) || offset.length !== 3 || !offset.every(Number.isFinite)) {
            fail('INVALID_EASY_MODEL_ENTITIES_VECTOR', 'renderProfile.rendering.visible_bounds_offset must contain exactly three finite numbers.');
          }
        }
        optionalFinite(rendering, 'opacity', 'renderProfile.rendering', {nonNegative: true, max: 1});

        const animation = optionalObject(document.animation, 'renderProfile.animation', ANIMATION_FIELDS, 'UNPROVEN_EASY_MODEL_ENTITIES_RENDER_FIELD');
        optionalEnum(animation, 'mode', ANIMATION_MODES, 'renderProfile.animation');
        optionalFinite(animation, 'swing_speed', 'renderProfile.animation', {nonNegative: true});
        optionalFinite(animation, 'walk_speed_multiplier', 'renderProfile.animation', {nonNegative: true});
        optionalFinite(animation, 'idle_strength', 'renderProfile.animation', {nonNegative: true});
        optionalEnum(animation, 'gait', GAIT_TYPES, 'renderProfile.animation');
        optionalEnum(animation, 'variant_mode', VARIANT_MODES, 'renderProfile.animation');

        return Object.freeze({ok: true, schemaVersion: document.schema_version, model: document.model, presetType: document.preset_type});
      }

      module.exports = {
        EASY_MODEL_ENTITIES_AUTHORITY,
        EasyModelEntitiesContractError,
        createEasyModelEntitiesExportPlan,
        validateEasyModelEntitiesServerProfile,
        validateEasyModelEntitiesRenderProfile,
      };
    },
    "core/provider-adapter/emf_cem_adapter.js": function(module, exports, require) {
      'use strict';

      const {
        isPlainObject,
        validateMinecraftNamespace,
        validateSafeResourceName,
        normalizeBbmodelSourcePath,
      } = require('../common/contract_utils.js');

      const EMF_CEM_RUNTIME_ROOTS = Object.freeze({
        optifineCompatible: 'optifine/cem',
        emfOnly: 'emf/cem',
      });

      const EMF_CEM_AUTHORITY = Object.freeze({
        providerFamily: 'emf_cem',
        minecraftVersion: '1.21.1',
        targetNeoForgeVersion: '21.1.248',
        providerVersion: '3.3.5',
        providerNeoForgeBuildVersion: '21.0.167',
        runtimeSource: 'Traben-0/Entity_Model_Features',
        runtimeRef: '02034eb0f102040b16900be7c900eff88da89e9e',
        etfMinimumVersion: '7.2.0',
        physicalEtfVersion: '7.2.1',
        blockbenchVersion: '5.1.6',
        blockbenchSource: 'JannisX11/blockbench',
        blockbenchRef: '794e964e966b6783b4e9b98ecbdda5152c0620cc',
        cemCodecId: 'optifine_entity',
        jpmCodecId: 'optifine_part',
        cemTemplatePluginId: 'cem_template_loader',
        cemTemplatePluginVersion: '9.2.0',
        cemTemplatePluginSource: 'ewanhowell5195/blockbenchPlugins',
        cemTemplatePluginRef: 'bdea1d6c5e8f9fca3dbbeb446e568adb025b5ef2',
        emfAnimationAddonId: 'emf_animation_addon',
        emfAnimationAddonVersion: '1.0.5',
        pluginCatalogSource: 'JannisX11/blockbench-plugins',
        pluginCatalogRef: '38862eb66b219995b09926488f7d1084a0fb6b3a',
        runtimeRoots: EMF_CEM_RUNTIME_ROOTS,
      });

      const PROFILE_ID = 'emf_cem_entity';
      const JEM_FIELDS = new Set(['credit', 'texture', 'textureSize', 'shadowSize', 'models']);
      const PART_FIELDS = new Set([
        'credit', 'texture', 'textureSize', 'invertAxis', 'translate', 'rotate', 'mirrorTexture',
        'boxes', 'submodel', 'submodels', 'baseId', 'model', 'id', 'part', 'attach', 'scale',
        'attachments', 'animations',
      ]);
      const BOX_COMMON_FIELDS = new Set([
        'textureOffset', 'uvDown', 'uvUp', 'uvFront', 'uvBack', 'uvLeft', 'uvRight',
        'uvNorth', 'uvSouth', 'uvWest', 'uvEast', 'coordinates', 'sizeAdd',
      ]);
      const BOX_EMF_ONLY_FIELDS = new Set(['sizeAddX', 'sizeAddY', 'sizeAddZ', 'sizesAdd']);
      const BOX_FIELDS = new Set([...BOX_COMMON_FIELDS, ...BOX_EMF_ONLY_FIELDS]);
      const EMF_ONLY_PART_FIELDS = new Set(['attachments']);
      const UV_FIELDS = [
        'uvDown', 'uvUp', 'uvFront', 'uvBack', 'uvLeft', 'uvRight',
        'uvNorth', 'uvSouth', 'uvWest', 'uvEast',
      ];

      class EmfCemContractError extends Error {
        constructor(code, message) {
          super(`${code}: ${message}`);
          this.name = 'EmfCemContractError';
          this.code = code;
        }
      }

      function fail(code, message) {
        throw new EmfCemContractError(code, message);
      }

      function requireObject(value, field, code = 'INVALID_EMF_CEM_DOCUMENT') {
        if (!isPlainObject(value)) fail(code, `${field} must be a plain object.`);
        return value;
      }

      function rejectUnknownFields(value, allowed, code, field) {
        for (const key of Object.keys(value)) {
          if (!allowed.has(key)) fail(code, `${field}.${key} is outside the audited EMF/CEM contract.`);
        }
      }

      function cloneAndFreeze(value, field = 'document') {
        if (Array.isArray(value)) {
          return Object.freeze(value.map((item, index) => cloneAndFreeze(item, `${field}[${index}]`)));
        }
        if (isPlainObject(value)) {
          const output = {};
          for (const [key, item] of Object.entries(value)) output[key] = cloneAndFreeze(item, `${field}.${key}`);
          return Object.freeze(output);
        }
        if (value === null || ['string', 'number', 'boolean'].includes(typeof value)) return value;
        fail('INVALID_EMF_CEM_DOCUMENT_VALUE', `${field} contains a value that cannot be preserved in audited JSON output.`);
      }

      function normalizeBlockbenchEmfCemDocument(value) {
        requireObject(value, 'Blockbench CEM document');
        return cloneAndFreeze(value, 'Blockbench CEM document');
      }

      function finiteNumber(value, field) {
        if (!Number.isFinite(value)) fail('INVALID_EMF_CEM_NUMBER', `${field} must be finite.`);
        return value;
      }

      function numericArray(value, field, lengths, {positive = false} = {}) {
        if (!Array.isArray(value) || !lengths.includes(value.length) || !value.every(Number.isFinite)) {
          fail('INVALID_EMF_CEM_ARRAY', `${field} must contain ${lengths.join(' or ')} finite numeric values.`);
        }
        if (positive && value.some((entry) => entry <= 0)) {
          fail('INVALID_EMF_CEM_ARRAY', `${field} values must be positive.`);
        }
        return value;
      }

      function optionalString(object, key, field) {
        if (object[key] !== undefined && typeof object[key] !== 'string') {
          fail('INVALID_EMF_CEM_STRING', `${field}.${key} must be a string.`);
        }
      }

      function optionalBoolean(object, key, field) {
        if (object[key] !== undefined && typeof object[key] !== 'boolean') {
          fail('INVALID_EMF_CEM_BOOLEAN', `${field}.${key} must be boolean.`);
        }
      }

      function validateAnimationDialect(value) {
        if (value !== 'optifine' && value !== 'emf') {
          fail('INVALID_EMF_CEM_ANIMATION_DIALECT', 'animationDialect must be explicitly optifine or emf.');
        }
        return value;
      }

      function markEmfOnly(state, dialect, field) {
        if (dialect !== 'emf') {
          fail('EMF_ONLY_FIELD_REQUIRES_EMF_DIALECT', `${field} is EMF-only and requires animationDialect=emf.`);
        }
        state.emfOnly = true;
      }

      function validateAnimations(value, field, state) {
        if (value === undefined || value === null) return;
        if (!Array.isArray(value)) fail('INVALID_EMF_CEM_ANIMATIONS', `${field} must be an array.`);
        for (let index = 0; index < value.length; index += 1) {
          const expressionMap = requireObject(value[index], `${field}[${index}]`, 'INVALID_EMF_CEM_ANIMATIONS');
          for (const [key, expression] of Object.entries(expressionMap)) {
            if (!key.trim() || typeof expression !== 'string') {
              fail('INVALID_EMF_CEM_ANIMATION_EXPRESSION', `${field}[${index}] must map non-empty animation keys to string expressions.`);
            }
            state.animationExpressionCount += 1;
          }
        }
      }

      function validateTextureSize(value, field) {
        if (value !== undefined) numericArray(value, field, [2], {positive: true});
      }

      function validateOptionalVector3(value, field) {
        if (value !== undefined) numericArray(value, field, [3]);
      }

      function validateOptionalUv(value, field) {
        if (value !== undefined) numericArray(value, field, [0, 4]);
      }

      function validateBox(value, field, dialect, state) {
        const box = requireObject(value, field, 'INVALID_EMF_CEM_BOX');
        rejectUnknownFields(box, BOX_FIELDS, 'UNPROVEN_EMF_CEM_BOX_FIELD', field);
        if (box.coordinates !== undefined) numericArray(box.coordinates, `${field}.coordinates`, [6]);
        if (box.textureOffset !== undefined) numericArray(box.textureOffset, `${field}.textureOffset`, [0, 2]);
        for (const uvField of UV_FIELDS) validateOptionalUv(box[uvField], `${field}.${uvField}`);
        if (box.sizeAdd !== undefined) finiteNumber(box.sizeAdd, `${field}.sizeAdd`);
        for (const key of ['sizeAddX', 'sizeAddY', 'sizeAddZ']) {
          if (box[key] !== undefined) {
            markEmfOnly(state, dialect, `${field}.${key}`);
            finiteNumber(box[key], `${field}.${key}`);
          }
        }
        if (box.sizesAdd !== undefined) {
          markEmfOnly(state, dialect, `${field}.sizesAdd`);
          numericArray(box.sizesAdd, `${field}.sizesAdd`, [0, 3]);
        }
      }

      function validateAttachments(value, field, dialect, state) {
        if (value === undefined) return;
        markEmfOnly(state, dialect, field);
        const attachments = requireObject(value, field, 'INVALID_EMF_CEM_ATTACHMENTS');
        for (const [name, vector] of Object.entries(attachments)) {
          if (!name.trim()) fail('INVALID_EMF_CEM_ATTACHMENTS', `${field} attachment names must not be blank.`);
          numericArray(vector, `${field}.${name}`, [3]);
        }
      }

      function validatePart(value, field, dialect, state, {jpmRoot = false} = {}) {
        const part = requireObject(value, field, 'INVALID_EMF_CEM_PART');
        rejectUnknownFields(part, PART_FIELDS, 'UNPROVEN_EMF_CEM_PART_FIELD', field);

        if (!jpmRoot && part.credit !== undefined) {
          fail('UNPROVEN_EMF_CEM_PART_FIELD', `${field}.credit is only audited for a JPM root export.`);
        }
        optionalString(part, 'credit', field);
        optionalString(part, 'texture', field);
        optionalString(part, 'invertAxis', field);
        optionalString(part, 'mirrorTexture', field);
        optionalString(part, 'baseId', field);
        optionalString(part, 'model', field);
        optionalString(part, 'id', field);
        optionalString(part, 'part', field);
        optionalBoolean(part, 'attach', field);
        if (part.scale !== undefined) finiteNumber(part.scale, `${field}.scale`);
        validateTextureSize(part.textureSize, `${field}.textureSize`);
        validateOptionalVector3(part.translate, `${field}.translate`);
        validateOptionalVector3(part.rotate, `${field}.rotate`);

        if (typeof part.model === 'string' && (part.model.includes('..') || part.model.includes('\\'))) {
          fail('INVALID_EMF_CEM_MODEL_REFERENCE', `${field}.model must not contain traversal or backslash path segments.`);
        }

        if (part.boxes !== undefined) {
          if (!Array.isArray(part.boxes)) fail('INVALID_EMF_CEM_BOXES', `${field}.boxes must be an array.`);
          part.boxes.forEach((box, index) => validateBox(box, `${field}.boxes[${index}]`, dialect, state));
        }

        validateAttachments(part.attachments, `${field}.attachments`, dialect, state);
        validateAnimations(part.animations, `${field}.animations`, state);

        if (part.submodel !== undefined && part.submodel !== null) {
          validatePart(part.submodel, `${field}.submodel`, dialect, state);
        }
        if (part.submodels !== undefined) {
          if (!Array.isArray(part.submodels)) fail('INVALID_EMF_CEM_SUBMODELS', `${field}.submodels must be an array.`);
          part.submodels.forEach((submodel, index) => validatePart(submodel, `${field}.submodels[${index}]`, dialect, state));
        }
      }

      function validateEmfCemJemDocument(value, options = {}) {
        const dialect = validateAnimationDialect(options.animationDialect);
        const document = requireObject(value, 'JEM document');
        rejectUnknownFields(document, JEM_FIELDS, 'UNPROVEN_EMF_CEM_JEM_FIELD', 'JEM document');
        optionalString(document, 'credit', 'JEM document');
        optionalString(document, 'texture', 'JEM document');
        validateTextureSize(document.textureSize, 'JEM document.textureSize');
        if (document.shadowSize !== undefined) finiteNumber(document.shadowSize, 'JEM document.shadowSize');
        if (!Array.isArray(document.models)) fail('INVALID_EMF_CEM_MODELS', 'JEM document.models must be an array.');

        const state = {animationExpressionCount: 0, emfOnly: false};
        document.models.forEach((part, index) => validatePart(part, `JEM document.models[${index}]`, dialect, state));
        return Object.freeze({
          ok: true,
          modelCount: document.models.length,
          animationExpressionCount: state.animationExpressionCount,
          emfOnly: state.emfOnly,
        });
      }

      function validateEmfCemJpmDocument(value, options = {}) {
        const dialect = validateAnimationDialect(options.animationDialect);
        const state = {animationExpressionCount: 0, emfOnly: false};
        validatePart(value, 'JPM document', dialect, state, {jpmRoot: true});
        return Object.freeze({
          ok: true,
          animationExpressionCount: state.animationExpressionCount,
          emfOnly: state.emfOnly,
        });
      }

      function createEmfCemExportPlan(input) {
        requireObject(input, 'exportPlan', 'INVALID_EMF_CEM_EXPORT_PLAN');
        if (input.profileId !== PROFILE_ID) {
          fail('EMF_CEM_PROFILE_REQUIRED', `profileId must be exactly ${PROFILE_ID}.`);
        }
        const sourcePath = normalizeBbmodelSourcePath(
          input.sourcePath,
          fail,
          'EMF_CEM_SOURCE_NOT_SAVED',
          'Source project must be saved as a .bbmodel before EMF/CEM handoff.',
          'EMF/CEM source authority must remain a saved .bbmodel file.',
        );
        const namespace = validateMinecraftNamespace(
          input.namespace,
          fail,
          'INVALID_EMF_CEM_NAMESPACE',
          'namespace must match the lowercase Minecraft namespace grammar.',
        );
        const resourceName = validateSafeResourceName(
          input.resourceName,
          fail,
          'INVALID_EMF_CEM_RESOURCE_NAME',
          'resourceName must be a safe lowercase CEM id without path traversal.',
        );

        if (input.compatibilityMode !== 'optifine_compatible' && input.compatibilityMode !== 'emf_only') {
          fail('EMF_CEM_COMPATIBILITY_MODE_REQUIRED', 'compatibilityMode must be explicitly optifine_compatible or emf_only.');
        }
        if (input.directoryLayout !== 'flat' && input.directoryLayout !== 'subfolder') {
          fail('EMF_CEM_DIRECTORY_LAYOUT_REQUIRED', 'directoryLayout must be explicitly flat or subfolder.');
        }
        const animationDialect = validateAnimationDialect(input.animationDialect);
        if (input.compatibilityMode === 'optifine_compatible' && animationDialect === 'emf') {
          fail('EMF_ONLY_ANIMATION_REQUIRES_EMF_MODE', 'EMF-only animation semantics cannot be staged under the OptiFine-compatible root.');
        }

        const runtimeRoot = input.compatibilityMode === 'emf_only'
          ? EMF_CEM_AUTHORITY.runtimeRoots.emfOnly
          : EMF_CEM_AUTHORITY.runtimeRoots.optifineCompatible;
        const base = `assets/${namespace}/${runtimeRoot}`;
        const partModelDirectory = input.directoryLayout === 'subfolder' ? `${base}/${resourceName}` : base;
        const jemPath = input.directoryLayout === 'subfolder'
          ? `${partModelDirectory}/${resourceName}.jem`
          : `${base}/${resourceName}.jem`;

        return Object.freeze({
          profileId: PROFILE_ID,
          sourcePath,
          preserveSource: true,
          namespace,
          resourceName,
          compatibilityMode: input.compatibilityMode,
          directoryLayout: input.directoryLayout,
          animationDialect,
          jemPath,
          partModelDirectory,
          blockbenchCodecId: EMF_CEM_AUTHORITY.cemCodecId,
          requiresCemTemplateLoader: true,
          requiresEmfAnimationAddon: animationDialect === 'emf',
          resourcepackFileName: `${resourceName}_emf_cem_resourcepack.zip`,
          runtimeEvidence: 'UNPROVEN',
          runtimeValidated: false,
          f4I6Evidence: false,
        });
      }

      module.exports = {
        EMF_CEM_AUTHORITY,
        EmfCemContractError,
        createEmfCemExportPlan,
        normalizeBlockbenchEmfCemDocument,
        validateEmfCemJemDocument,
        validateEmfCemJpmDocument,
      };
    },
    "core/provider-adapter/animated_java_adapter.js": function(module, exports, require) {
      'use strict';

      const {isPlainObject} = require('../common/contract_utils.js');

      const PROFILE_ID = 'animated_java_display_entities';
      const EXPORT_MODES = Object.freeze(['folder', 'zip', 'none']);
      const EXPORT_MODE_SET = new Set(EXPORT_MODES);

      const ANIMATED_JAVA_AUTHORITY = Object.freeze({
        providerFamily: 'animated_java',
        minecraftVersion: '1.21.1',
        pluginId: 'animated_java',
        pluginVersion: '1.10.2',
        pluginSource: 'Animated-Java/animated-java',
        pluginRef: 'a5fc548d2a53cc0887fa070db33ccfcef1cd3541',
        releaseAsset: 'animated_java.js',
        releaseAssetSha256: '81aadc4def796d97dab6642ad05b564b470ecadcaf455c8cc5826c9e24759672',
        blockbenchVersion: '5.1.6',
        blockbenchSource: 'JannisX11/blockbench',
        blockbenchRef: '794e964e966b6783b4e9b98ecbdda5152c0620cc',
        blockbenchMinimumVersion: '5.1.4',
        blueprintFormatId: 'animated-java:format/blueprint',
        blueprintCodecId: 'animated_java:codec/blueprint',
        sourceExtension: '.ajblueprint',
        exportModes: EXPORT_MODES,
        compilerRange: Object.freeze({minInclusive: '1.21.0', maxExclusive: '1.21.2'}),
      });

      const BLUEPRINT_FIELDS = new Set([
        'meta', 'blueprint_settings', 'variants', 'resolution', 'elements', 'groups', 'outliner', 'textures',
        'animations', 'animation_controllers', 'animation_variable_placeholders', 'backgrounds',
        'collections',
      ]);
      const META_FIELDS = new Set([
        'format', 'format_version', 'uuid', 'last_used_blueprint_id', 'box_uv', 'backup', 'save_location',
      ]);
      const SETTINGS_FIELDS = new Set([
        'blueprint_id', 'show_render_box', 'auto_render_box', 'render_box', 'enable_plugin_mode',
        'resource_pack_export_mode', 'data_pack_export_mode', 'target_minecraft_version', 'display_item',
        'custom_model_data_offset', 'enable_advanced_resource_pack_settings', 'resource_pack',
        'enable_advanced_data_pack_settings', 'data_pack', 'on_summon_function', 'on_remove_function',
        'on_pre_tick_function', 'on_post_tick_function', 'interpolation_duration', 'teleportation_duration',
        'custom_rig_entity_tags', 'auto_update_rig_orientation', 'use_storage_for_animation',
        'use_entity_stacking', 'baked_animations', 'json_file',
      ]);

      class AnimatedJavaContractError extends Error {
        constructor(code, message) {
          super(`${code}: ${message}`);
          this.name = 'AnimatedJavaContractError';
          this.code = code;
        }
      }

      function fail(code, message) {
        throw new AnimatedJavaContractError(code, message);
      }

      function rejectUnknownFields(value, allowed, code, context) {
        for (const key of Object.keys(value)) {
          if (!allowed.has(key)) fail(code, `${context}.${key} is outside the audited Animated Java 1.10.2 contract.`);
        }
      }

      function cloneAndFreeze(value, field = 'blueprint') {
        if (Array.isArray(value)) return Object.freeze(value.map((item, index) => cloneAndFreeze(item, `${field}[${index}]`)));
        if (isPlainObject(value)) {
          const output = {};
          for (const [key, item] of Object.entries(value)) output[key] = cloneAndFreeze(item, `${field}.${key}`);
          return Object.freeze(output);
        }
        if (value === null || value === undefined || ['string', 'number', 'boolean'].includes(typeof value)) return value;
        fail('INVALID_ANIMATED_JAVA_BLUEPRINT_VALUE', `${field} contains a value that cannot be preserved in audited JSON output.`);
      }

      function validateExportMode(value, field) {
        if (!EXPORT_MODE_SET.has(value)) {
          fail('INVALID_ANIMATED_JAVA_EXPORT_MODE', `${field} must be one of ${EXPORT_MODES.join(', ')}.`);
        }
        return value;
      }

      function parseBlueprintId(value) {
        if (typeof value !== 'string') fail('INVALID_ANIMATED_JAVA_BLUEPRINT_ID', 'blueprintId must be a Minecraft resource location.');
        const separator = value.indexOf(':');
        if (separator <= 0 || separator === value.length - 1) {
          fail('INVALID_ANIMATED_JAVA_BLUEPRINT_ID', 'blueprintId must include namespace:path.');
        }
        const namespace = value.slice(0, separator);
        const resourcePath = value.slice(separator + 1);
        if (!/^[a-z0-9_]+$/.test(namespace) || !/^[a-z0-9_/]+$/.test(resourcePath)) {
          fail('INVALID_ANIMATED_JAVA_BLUEPRINT_ID', 'blueprintId must match the audited Animated Java lowercase resource-location grammar.');
        }
        if (namespace === 'minecraft') {
          fail('INVALID_ANIMATED_JAVA_BLUEPRINT_ID', 'Animated Java blueprintId cannot use the minecraft namespace.');
        }
        if (namespace === 'animated_java' && resourcePath === 'global') {
          fail('INVALID_ANIMATED_JAVA_BLUEPRINT_ID', 'animated_java:global is reserved by Animated Java.');
        }
        return Object.freeze({namespace, path: resourcePath});
      }

      function normalizeSourcePath(value) {
        if (typeof value !== 'string' || value.length === 0) {
          fail('ANIMATED_JAVA_SOURCE_NOT_SAVED', 'Animated Java source project must be saved as .ajblueprint before handoff.');
        }
        const normalized = value.replace(/\\/g, '/');
        if (!normalized.toLowerCase().endsWith(ANIMATED_JAVA_AUTHORITY.sourceExtension)) {
          fail('ANIMATED_JAVA_SOURCE_NOT_SAVED', 'Animated Java source authority must remain a saved .ajblueprint file.');
        }
        return normalized;
      }

      function validateAnimatedJavaBlueprint(value) {
        if (!isPlainObject(value)) fail('INVALID_ANIMATED_JAVA_BLUEPRINT', 'Blueprint must be a plain object.');
        rejectUnknownFields(value, BLUEPRINT_FIELDS, 'INVALID_ANIMATED_JAVA_BLUEPRINT_FIELD', 'blueprint');
        if (!isPlainObject(value.meta)) fail('INVALID_ANIMATED_JAVA_BLUEPRINT_META', 'Blueprint meta is required.');
        rejectUnknownFields(value.meta, META_FIELDS, 'INVALID_ANIMATED_JAVA_BLUEPRINT_META_FIELD', 'meta');
        if (value.meta.format !== ANIMATED_JAVA_AUTHORITY.blueprintFormatId) {
          fail('INVALID_ANIMATED_JAVA_BLUEPRINT_FORMAT', `meta.format must be ${ANIMATED_JAVA_AUTHORITY.blueprintFormatId}.`);
        }
        if (value.meta.format_version !== undefined && value.meta.format_version !== ANIMATED_JAVA_AUTHORITY.pluginVersion) {
          fail('INVALID_ANIMATED_JAVA_BLUEPRINT_VERSION', `meta.format_version must be ${ANIMATED_JAVA_AUTHORITY.pluginVersion} for the audited PR11 handoff.`);
        }
        if (!isPlainObject(value.blueprint_settings)) {
          fail('INVALID_ANIMATED_JAVA_BLUEPRINT_SETTINGS', 'blueprint_settings are required for audited export.');
        }
        rejectUnknownFields(
          value.blueprint_settings,
          SETTINGS_FIELDS,
          'INVALID_ANIMATED_JAVA_BLUEPRINT_SETTING',
          'blueprint_settings',
        );
        parseBlueprintId(value.blueprint_settings.blueprint_id);
        if (value.blueprint_settings.target_minecraft_version !== ANIMATED_JAVA_AUTHORITY.minecraftVersion) {
          fail(
            'UNSUPPORTED_ANIMATED_JAVA_MINECRAFT_VERSION',
            `Factory PR11 is pinned to Minecraft ${ANIMATED_JAVA_AUTHORITY.minecraftVersion}.`,
          );
        }
        validateExportMode(value.blueprint_settings.resource_pack_export_mode, 'resource_pack_export_mode');
        validateExportMode(value.blueprint_settings.data_pack_export_mode, 'data_pack_export_mode');
        return cloneAndFreeze(value);
      }

      function requireExportPath(mode, value, field) {
        if (mode === 'none') return value ?? '';
        if (typeof value !== 'string' || value.length === 0) {
          fail('INVALID_ANIMATED_JAVA_EXPORT_PATH', `${field} is required when export mode is ${mode}.`);
        }
        return value.replace(/\\/g, '/');
      }

      function createAnimatedJavaExportPlan(input) {
        if (!isPlainObject(input)) fail('INVALID_ANIMATED_JAVA_EXPORT_PLAN', 'Export plan input must be a plain object.');
        const sourcePath = normalizeSourcePath(input.sourcePath);
        const parsed = parseBlueprintId(input.blueprintId);
        if (input.targetMinecraftVersion !== ANIMATED_JAVA_AUTHORITY.minecraftVersion) {
          fail(
            'UNSUPPORTED_ANIMATED_JAVA_MINECRAFT_VERSION',
            `Factory PR11 is pinned to Minecraft ${ANIMATED_JAVA_AUTHORITY.minecraftVersion}.`,
          );
        }
        const resourcePackExportMode = validateExportMode(input.resourcePackExportMode, 'resourcePackExportMode');
        const dataPackExportMode = validateExportMode(input.dataPackExportMode, 'dataPackExportMode');
        const resourcePackPath = requireExportPath(resourcePackExportMode, input.resourcePackPath, 'resourcePackPath');
        const dataPackPath = requireExportPath(dataPackExportMode, input.dataPackPath, 'dataPackPath');
        const modelExportRoot = `assets/${parsed.namespace}/models/blueprint/${parsed.path}`;
        const textureExportRoot = `assets/${parsed.namespace}/textures/blueprint/${parsed.path}`;

        return Object.freeze({
          profileId: PROFILE_ID,
          sourcePath,
          preserveSource: true,
          blueprintId: input.blueprintId,
          targetMinecraftVersion: input.targetMinecraftVersion,
          resourcePackExportMode,
          dataPackExportMode,
          resourcePackPath,
          dataPackPath,
          enablePluginMode: input.enablePluginMode === true,
          modelExportRoot,
          textureExportRoot,
          blueprintFormatId: ANIMATED_JAVA_AUTHORITY.blueprintFormatId,
          blueprintCodecId: ANIMATED_JAVA_AUTHORITY.blueprintCodecId,
          requiresAnimatedJavaPlugin: true,
          implicitProviderConversion: false,
          runtimeEvidence: 'UNPROVEN',
          runtimeValidated: false,
          f4I6Evidence: false,
        });
      }

      module.exports = {
        ANIMATED_JAVA_AUTHORITY,
        AnimatedJavaContractError,
        validateAnimatedJavaBlueprint,
        createAnimatedJavaExportPlan,
      };
    },
    "core/index.js": function(module, exports, require) {
      'use strict';

      const projectModel = require('./project-model/project_model.js');
      const mutations = require('./mutations/mutation_engine.js');
      const animation = require('./animation/animation_engine.js');
      const uvTexture = require('./uv-texture/uv_texture_engine.js');
      const uvAnalysis = require('./uv-texture/uv_analysis.js');
      const uvPack = require('./uv-texture/uv_pack.js');
      const validator = require('./validator/validator.js');
      const contractProfile = require('./contract-profile/contract_profile.js');
      const report = require('./report/report.js');
      const extensions = require('./extension-registry/extension_registry.js');
      const providers = require('./provider-profile/provider_profiles.js');
      const physical = require('./provider-profile/physical_provider_snapshot.js');
      const geckolib4 = require('./provider-adapter/geckolib4_adapter.js');
      const azurelib3 = require('./provider-adapter/azurelib3_adapter.js');
      const neoforgeNativeAnimation = require('./provider-adapter/neoforge_native_animation_adapter.js');
      const easyModelEntities = require('./provider-adapter/easy_model_entities_adapter.js');
      const emfCem = require('./provider-adapter/emf_cem_adapter.js');
      const animatedJava = require('./provider-adapter/animated_java_adapter.js');

      module.exports = Object.assign(
        {},
        projectModel,
        mutations,
        animation,
        uvTexture,
        uvAnalysis,
        uvPack,
        validator,
        contractProfile,
        report,
        extensions,
        providers,
        physical,
        geckolib4,
        azurelib3,
        neoforgeNativeAnimation,
        easyModelEntities,
        emfCem,
        animatedJava,
      );
    },
    "live-bridge/protocol.js": function(module, exports, require) {
      'use strict';

      const PROTOCOL_VERSION = '1.0.0';
      const MAX_MESSAGE_BYTES = 64 * 1024;

      const READ_ONLY_METHODS = Object.freeze([
        'blockbench.get_status',
        'blockbench.get_capabilities',
        'blockbench.get_project',
        'blockbench.get_scene_graph',
        'blockbench.get_selection',
        'blockbench.get_bones',
        'blockbench.get_elements',
        'blockbench.get_textures',
        'blockbench.get_animations',
        'blockbench.get_animation',
        'blockbench.compute_bounds',
        'blockbench.validate',
        'blockbench.validate_contract',
        'blockbench.extensions.list',
        'blockbench.extensions.get',
        'blockbench.extensions.get_fingerprint',
        'blockbench.extensions.check_compatibility',
        'blockbench.profiles.list',
        'blockbench.profiles.get',
        'blockbench.profiles.resolve_for_asset',
      ]);

      const READ_ONLY_METHOD_SET = new Set(READ_ONLY_METHODS);

      function bridgeError(code, message = code) {
        const error = new Error(`${code}: ${message}`);
        error.code = code;
        return error;
      }

      function assertLoopbackHost(host) {
        if (host === '::1') return host;
        if (typeof host === 'string') {
          const parts = host.split('.');
          if (parts.length === 4 && parts[0] === '127' && parts.every((part) => /^\d{1,3}$/.test(part) && Number(part) >= 0 && Number(part) <= 255)) return host;
        }
        throw bridgeError('LOOPBACK_REQUIRED', 'bridge transport must bind to a numeric loopback address');
      }

      function validateEnvelope(value) {
        if (!value || typeof value !== 'object' || Array.isArray(value)) throw bridgeError('MALFORMED_MESSAGE');
        for (const key of ['protocolVersion', 'sessionId', 'token', 'requestId', 'method']) {
          if (typeof value[key] !== 'string' || !value[key]) throw bridgeError('MALFORMED_MESSAGE', `missing ${key}`);
        }
        if (!/^[0-9a-f]{32}$/i.test(value.sessionId)) throw bridgeError('MALFORMED_MESSAGE', 'invalid sessionId');
        if (!/^[0-9a-f]{64}$/i.test(value.token)) throw bridgeError('MALFORMED_MESSAGE', 'invalid token');
        if (value.requestId.length > 128) throw bridgeError('MALFORMED_MESSAGE', 'requestId too long');
        if (!READ_ONLY_METHOD_SET.has(value.method)) throw bridgeError('METHOD_NOT_ALLOWED', value.method);
        if (value.params === undefined) value.params = {};
        if (!value.params || typeof value.params !== 'object' || Array.isArray(value.params)) throw bridgeError('MALFORMED_MESSAGE', 'params must be an object');
        return value;
      }

      function parseEnvelope(raw) {
        const text = Buffer.isBuffer(raw) ? raw.toString('utf8') : String(raw);
        if (Buffer.byteLength(text, 'utf8') > MAX_MESSAGE_BYTES) throw bridgeError('MESSAGE_TOO_LARGE');
        let value;
        try { value = JSON.parse(text); }
        catch (_) { throw bridgeError('MALFORMED_MESSAGE', 'invalid JSON'); }
        return validateEnvelope(value);
      }

      module.exports = {
        PROTOCOL_VERSION,
        MAX_MESSAGE_BYTES,
        READ_ONLY_METHODS,
        bridgeError,
        assertLoopbackHost,
        validateEnvelope,
        parseEnvelope,
      };
    },
    "live-bridge/project_snapshot.js": function(module, exports, require) {
      'use strict';

      const crypto = require('node:crypto');
      const {isLocatorLike, locatorPosition} = require('../core/project-model/project_model.js');

      function vec(value) { return Array.isArray(value) ? value.slice(0, 3).map((entry) => Number.isFinite(entry) ? entry : null) : null; }
      function vec2(value) { return Array.isArray(value) && value.length >= 2 ? value.slice(0, 2).map((entry) => Number.isFinite(entry) ? entry : null) : null; }
      function parentRef(value) { return value && typeof value === 'object' ? (value.uuid || value.name || null) : (typeof value === 'string' ? value : null); }
      function compareText(left, right) { return String(left).localeCompare(String(right), 'en', {sensitivity: 'variant', numeric: false}); }
      function sourceFile(savePath) {
        if (typeof savePath !== 'string' || !savePath) return null;
        return savePath.replace(/\\/g, '/').split('/').filter(Boolean).pop() || null;
      }
      function canonical(value) {
        if (Array.isArray(value)) return value.map(canonical);
        if (value && typeof value === 'object') return Object.fromEntries(Object.keys(value).sort(compareText).map((key) => [key, canonical(value[key])]));
        return value;
      }
      function hashRevision(value) { return `sha256:${crypto.createHash('sha256').update(JSON.stringify(canonical(value))).digest('hex')}`; }

      function groupSnapshot(group) {
        return {name: group?.name || null, uuid: group?.uuid || null, origin: vec(group?.origin), parent: parentRef(group?.parent)};
      }
      function faceSnapshot(face) { return {enabled: face?.enabled !== false, texture: typeof face?.texture === 'string' ? face.texture : null, uv: Array.isArray(face?.uv) ? face.uv.slice(0, 4) : null}; }
      function elementSnapshot(element) {
        const faces = element?.faces && typeof element.faces === 'object' ? Object.fromEntries(Object.keys(element.faces).sort(compareText).map((key) => [key, faceSnapshot(element.faces[key])])) : {};
        const snapshot = {name: element?.name || null, uuid: element?.uuid || null, from: vec(element?.from), to: vec(element?.to), origin: vec(element?.origin), parent: parentRef(element?.parent), faces};
        if (typeof element?.box_uv === 'boolean') snapshot.boxUv = element.box_uv;
        if (Array.isArray(element?.uv_offset)) snapshot.uvOffset = vec2(element.uv_offset);
        if (isLocatorLike(element)) snapshot.position = vec(locatorPosition(element));
        return snapshot;
      }
      function textureSnapshot(texture) {
        const snapshot = {name: texture?.name || null, uuid: texture?.uuid || null, width: Number.isFinite(texture?.width) ? texture.width : null, height: Number.isFinite(texture?.height) ? texture.height : null};
        if (texture?.internal === true && typeof texture?.source === 'string' && texture.source) snapshot.contentHash = hashRevision(texture.source);
        return snapshot;
      }
      function animationSnapshot(animation) {
        return {name: animation?.name || null, uuid: animation?.uuid || null, length: Number.isFinite(animation?.length) ? animation.length : null, loop: animation?.loop || null, animatorTargets: animation?.animators && typeof animation.animators === 'object' ? Object.keys(animation.animators).sort(compareText) : []};
      }

      function createProjectSnapshot(project) {
        const input = project && typeof project === 'object' ? project : {};
        const body = {
          name: input.name || null,
          projectFormat: input.format && typeof input.format === 'object' ? input.format.id || null : input.format || null,
          sourceFile: sourceFile(input.save_path),
          saved: typeof input.save_path === 'string' && input.save_path.length > 0,
          groups: (Array.isArray(input.groups) ? input.groups : []).map(groupSnapshot),
          elements: (Array.isArray(input.elements) ? input.elements : []).map(elementSnapshot),
          textures: (Array.isArray(input.textures) ? input.textures : []).map(textureSnapshot),
          animations: (Array.isArray(input.animations) ? input.animations : []).map(animationSnapshot),
          selection: (Array.isArray(input.selected_elements) ? input.selected_elements : []).map((entry) => entry?.uuid || entry?.name || null).filter(Boolean),
        };
        return Object.freeze({...body, projectRevision: hashRevision(body)});
      }

      module.exports = {createProjectSnapshot, hashRevision};
    },
    "live-bridge/fingerprint.js": function(module, exports, require) {
      'use strict';

      const {bridgeError} = require('./protocol.js');

      function requiredString(value, field) {
        if (typeof value !== 'string' || !value.trim() || value.length > 256) throw bridgeError('INVALID_FINGERPRINT', field);
        return value.trim();
      }

      function boundedEntries(entries, idKey, versionKey) {
        if (!Array.isArray(entries) || entries.length > 256) throw bridgeError('INVALID_FINGERPRINT', `${idKey} entries`);
        return entries.map((entry) => ({
          [idKey]: requiredString(entry && entry[idKey], idKey),
          [versionKey]: requiredString(entry && entry[versionKey], versionKey),
        }));
      }

      function buildSessionFingerprint(input = {}) {
        return Object.freeze({
          minecraft_version: requiredString(input.minecraftVersion, 'minecraft_version'),
          loader: requiredString(input.loader, 'loader'),
          java_version: requiredString(input.javaVersion, 'java_version'),
          blockbench_version: requiredString(input.blockbenchVersion, 'blockbench_version'),
          toolkit_version: requiredString(input.toolkitVersion, 'toolkit_version'),
          protocol_version: requiredString(input.protocolVersion, 'protocol_version'),
          installed_extensions: boundedEntries(input.installedExtensions || [], 'pluginId', 'pluginVersion'),
          physical_providers: boundedEntries(input.physicalProviders || [], 'modId', 'modVersion'),
          active_provider_profile: requiredString(input.activeProviderProfile, 'active_provider_profile'),
          project_format: requiredString(input.projectFormat, 'project_format'),
          project_revision: requiredString(input.projectRevision, 'project_revision'),
        });
      }

      module.exports = {buildSessionFingerprint};
    },
    "live-bridge/read_only_router.js": function(module, exports, require) {
      'use strict';

      const core = require('../core/index.js');
      const {PROTOCOL_VERSION, READ_ONLY_METHODS, bridgeError} = require('./protocol.js');
      const {createProjectSnapshot} = require('./project_snapshot.js');

      function clone(value) { return value == null ? value : JSON.parse(JSON.stringify(value)); }

      function createReadOnlyRouter(options = {}) {
        const getProject = typeof options.getProject === 'function' ? options.getProject : () => ({});
        const getBlockbenchVersion = typeof options.getBlockbenchVersion === 'function' ? options.getBlockbenchVersion : () => 'UNKNOWN';
        const getInstalledExtensions = typeof options.getInstalledExtensions === 'function' ? options.getInstalledExtensions : () => [];
        const getAuthorizedExtensionIds = typeof options.getMcpAuthorizedExtensionIds === 'function' ? options.getMcpAuthorizedExtensionIds : () => [];
        const activeProviderProfile = typeof options.activeProviderProfile === 'function' ? options.activeProviderProfile : () => null;
        const physicalProviders = options.physicalProviders || {};

        function context() {
          return {
            blockbenchVersion: getBlockbenchVersion(),
            installedExtensions: getInstalledExtensions(),
            mcpAuthorizedExtensionIds: getAuthorizedExtensionIds(),
            physicalProviders,
          };
        }

        async function call(method, params = {}) {
          if (!READ_ONLY_METHODS.includes(method)) throw bridgeError('METHOD_NOT_ALLOWED', method);
          const project = getProject() || {};
          const snapshot = createProjectSnapshot(project);
          const ctx = context();
          switch (method) {
            case 'blockbench.get_status': return {connected: true, readOnly: true, protocolVersion: PROTOCOL_VERSION, blockbenchVersion: ctx.blockbenchVersion, projectRevision: snapshot.projectRevision, activeProviderProfile: activeProviderProfile()};
            case 'blockbench.get_capabilities': return {readOnly: true, methods: [...READ_ONLY_METHODS], protocolVersion: PROTOCOL_VERSION};
            case 'blockbench.get_project': return snapshot;
            case 'blockbench.get_scene_graph': return {groups: snapshot.groups, elements: snapshot.elements, projectRevision: snapshot.projectRevision};
            case 'blockbench.get_selection': return {selection: snapshot.selection, projectRevision: snapshot.projectRevision};
            case 'blockbench.get_bones': return snapshot.groups;
            case 'blockbench.get_elements': return snapshot.elements;
            case 'blockbench.get_textures': return snapshot.textures;
            case 'blockbench.get_animations': return snapshot.animations;
            case 'blockbench.get_animation': {
              const target = typeof params.animationId === 'string' ? params.animationId : (typeof params.name === 'string' ? params.name : '');
              return snapshot.animations.find((entry) => entry.uuid === target || entry.name === target) || null;
            }
            case 'blockbench.compute_bounds': return core.computeBounds(Array.isArray(project.elements) ? project.elements : []);
            case 'blockbench.validate': return core.validateProject(project, {});
            case 'blockbench.validate_contract': return core.validateProject(project, params.profile && typeof params.profile === 'object' ? params.profile : {});
            case 'blockbench.extensions.list': return Object.values(core.EXTENSION_CATALOG).map(clone);
            case 'blockbench.extensions.get': {
              const definition = core.getExtensionDefinition(params.pluginId);
              return definition ? {...clone(definition), evaluation: core.evaluateExtension(definition, ctx)} : null;
            }
            case 'blockbench.extensions.get_fingerprint': return {blockbenchVersion: ctx.blockbenchVersion, installedExtensions: clone(ctx.installedExtensions)};
            case 'blockbench.extensions.check_compatibility': {
              const definition = core.getExtensionDefinition(params.pluginId);
              return definition ? core.evaluateExtension(definition, ctx) : {installed: false, compatible: false, versionMatch: false, mcpAllowed: false, reasons: ['UNKNOWN_EXTENSION']};
            }
            case 'blockbench.profiles.list': return core.listProviderProfiles().map(clone);
            case 'blockbench.profiles.get': return clone(core.getProviderProfile(params.profileId));
            case 'blockbench.profiles.resolve_for_asset': return core.resolveProviderProfile(params.profileId, ctx);
            default: throw bridgeError('METHOD_NOT_ALLOWED', method);
          }
        }

        return Object.freeze({call, methods: () => [...READ_ONLY_METHODS]});
      }

      module.exports = {createReadOnlyRouter};
    },
    "live-bridge/blockbench_bridge_client.js": function(module, exports, require) {
      'use strict';

      const {assertLoopbackHost, READ_ONLY_METHODS, MAX_MESSAGE_BYTES, bridgeError} = require('./protocol.js');

      function assertPort(port) {
        if (!Number.isInteger(port) || port < 1 || port > 65535) throw bridgeError('INVALID_PORT');
        return port;
      }

      function buildBridgeUrl(options = {}) {
        const host = assertLoopbackHost(options.host);
        const port = assertPort(options.port);
        const authority = host.includes(':') ? `[${host}]` : host;
        return `ws://${authority}:${port}/bridge`;
      }

      function buildHandshake(options = {}) {
        const session = options.session || {};
        if (typeof session.protocolVersion !== 'string' || typeof session.sessionId !== 'string' || typeof session.token !== 'string') {
          throw bridgeError('INVALID_SESSION');
        }
        const capabilities = Array.isArray(options.capabilities) ? options.capabilities : [];
        if (capabilities.some((method) => !READ_ONLY_METHODS.includes(method))) throw bridgeError('METHOD_NOT_ALLOWED');
        const fingerprint = options.fingerprint && typeof options.fingerprint === 'object' && !Array.isArray(options.fingerprint)
          ? options.fingerprint : {};
        return {
          type: 'handshake',
          protocolVersion: session.protocolVersion,
          sessionId: session.sessionId,
          token: session.token,
          capabilities: [...capabilities],
          fingerprint,
        };
      }

      function addSocketListener(socket, event, handler) {
        if (socket && typeof socket.addEventListener === 'function') {
          socket.addEventListener(event, handler);
          return () => socket.removeEventListener?.(event, handler);
        }
        if (socket && typeof socket.on === 'function') {
          socket.on(event, handler);
          return () => socket.off?.(event, handler);
        }
        throw bridgeError('WEBSOCKET_API_UNAVAILABLE');
      }

      async function messageText(eventOrData) {
        let value = eventOrData && typeof eventOrData === 'object' && 'data' in eventOrData
          ? eventOrData.data
          : eventOrData;
        if (typeof value === 'string') return value;
        if (typeof Buffer !== 'undefined' && Buffer.isBuffer && Buffer.isBuffer(value)) return value.toString('utf8');
        if (typeof ArrayBuffer !== 'undefined' && value instanceof ArrayBuffer) return new TextDecoder().decode(new Uint8Array(value));
        if (typeof ArrayBuffer !== 'undefined' && ArrayBuffer.isView?.(value)) {
          return new TextDecoder().decode(new Uint8Array(value.buffer, value.byteOffset, value.byteLength));
        }
        if (value && typeof value.text === 'function') return value.text();
        return String(value);
      }

      function byteLength(text) {
        if (typeof Buffer !== 'undefined' && Buffer.byteLength) return Buffer.byteLength(text, 'utf8');
        if (typeof TextEncoder !== 'undefined') return new TextEncoder().encode(text).byteLength;
        return text.length * 4;
      }

      function parseBridgeMessage(text) {
        if (byteLength(text) > MAX_MESSAGE_BYTES) throw bridgeError('MESSAGE_TOO_LARGE');
        let value;
        try { value = JSON.parse(text); }
        catch (_) { throw bridgeError('MALFORMED_MESSAGE', 'invalid JSON'); }
        if (!value || typeof value !== 'object' || Array.isArray(value)) throw bridgeError('MALFORMED_MESSAGE');
        return value;
      }

      function socketOpenConstant(WebSocketClass) {
        return Number.isInteger(WebSocketClass?.OPEN) ? WebSocketClass.OPEN : 1;
      }

      function socketClosedConstant(WebSocketClass) {
        return Number.isInteger(WebSocketClass?.CLOSED) ? WebSocketClass.CLOSED : 3;
      }

      function createBridgeConnection(options = {}) {
        const WebSocketClass = options.WebSocketClass || (typeof globalThis !== 'undefined' ? globalThis.WebSocket : null);
        if (typeof WebSocketClass !== 'function') throw bridgeError('WEBSOCKET_API_UNAVAILABLE');
        const host = options.host;
        const port = options.port;
        const session = options.session || {};
        const fingerprint = options.fingerprint || {};
        const router = options.router;
        const heartbeatIntervalMs = Number.isFinite(options.heartbeatIntervalMs) ? options.heartbeatIntervalMs : 10_000;
        if (!router || typeof router.call !== 'function' || typeof router.methods !== 'function') throw bridgeError('INVALID_ROUTER');
        if (heartbeatIntervalMs <= 0) throw bridgeError('INVALID_HEARTBEAT_INTERVAL');

        const url = buildBridgeUrl({host, port});
        let socket = null;
        let connected = false;
        let connecting = null;
        let generation = 0;
        let capabilities = [];
        let heartbeatTimer = null;
        let intentionalClose = false;
        let listenerCleanup = [];

        function cleanupListeners() {
          for (const remove of listenerCleanup.splice(0)) {
            try { remove(); } catch (_) { /* best effort */ }
          }
        }

        function stopHeartbeat() {
          if (heartbeatTimer) clearInterval(heartbeatTimer);
          heartbeatTimer = null;
        }

        function sendJson(target, value) {
          if (!target || target.readyState !== socketOpenConstant(WebSocketClass)) throw bridgeError('BRIDGE_DISCONNECTED');
          const text = JSON.stringify(value);
          if (byteLength(text) > MAX_MESSAGE_BYTES) throw bridgeError('MESSAGE_TOO_LARGE');
          target.send(text);
        }

        function currentStatus() {
          return Object.freeze({
            connected,
            generation,
            capabilities: [...capabilities],
            url,
            protocolVersion: session.protocolVersion || null,
          });
        }

        function validateServerEnvelope(message) {
          if (message.protocolVersion !== session.protocolVersion) throw bridgeError('PROTOCOL_MISMATCH');
          if (message.sessionId !== session.sessionId) throw bridgeError('SESSION_MISMATCH');
        }

        function responseError(error) {
          const code = typeof error?.code === 'string' && error.code ? error.code : 'BLOCKBENCH_ROUTER_ERROR';
          const message = String(error?.message || code).slice(0, 512);
          return {code, message};
        }

        async function handleRequest(target, message) {
          validateServerEnvelope(message);
          if (typeof message.requestId !== 'string' || !message.requestId || message.requestId.length > 128) throw bridgeError('MALFORMED_MESSAGE');
          if (typeof message.method !== 'string' || !READ_ONLY_METHODS.includes(message.method) || !capabilities.includes(message.method)) {
            throw bridgeError('METHOD_NOT_ALLOWED', message.method || 'UNKNOWN');
          }
          const params = message.params === undefined ? {} : message.params;
          if (!params || typeof params !== 'object' || Array.isArray(params)) throw bridgeError('MALFORMED_MESSAGE');
          try {
            const result = await router.call(message.method, params);
            sendJson(target, {
              type: 'response',
              protocolVersion: session.protocolVersion,
              sessionId: session.sessionId,
              requestId: message.requestId,
              ok: true,
              result,
            });
          } catch (error) {
            sendJson(target, {
              type: 'response',
              protocolVersion: session.protocolVersion,
              sessionId: session.sessionId,
              requestId: message.requestId,
              ok: false,
              error: responseError(error),
            });
          }
        }

        function startHeartbeat(target) {
          stopHeartbeat();
          heartbeatTimer = setInterval(() => {
            if (!connected || target !== socket || target.readyState !== socketOpenConstant(WebSocketClass)) return;
            try {
              sendJson(target, {
                type: 'heartbeat',
                protocolVersion: session.protocolVersion,
                sessionId: session.sessionId,
              });
            } catch (_) {
              connected = false;
              stopHeartbeat();
            }
          }, heartbeatIntervalMs);
          heartbeatTimer.unref?.();
        }

        async function connect() {
          if (connected && socket) return currentStatus();
          if (connecting) return connecting;

          capabilities = router.methods();
          if (!Array.isArray(capabilities)) throw bridgeError('INVALID_ROUTER');
          const handshake = buildHandshake({session, capabilities, fingerprint});
          intentionalClose = false;

          connecting = new Promise((resolve, reject) => {
            const target = new WebSocketClass(url);
            socket = target;
            let settled = false;

            const fail = (error) => {
              if (settled) return;
              settled = true;
              connected = false;
              stopHeartbeat();
              connecting = null;
              reject(error instanceof Error ? error : bridgeError('BRIDGE_CONNECTION_FAILED'));
            };

            const onOpen = () => {
              try { sendJson(target, handshake); }
              catch (error) { fail(error); }
            };

            const onMessage = async (event) => {
              let message;
              try {
                message = parseBridgeMessage(await messageText(event));
                if (!connected) {
                  if (message.type !== 'handshake_ack') throw bridgeError('INVALID_HANDSHAKE_ACK');
                  validateServerEnvelope(message);
                  if (!Array.isArray(message.capabilities) || message.capabilities.some((method) => !capabilities.includes(method))) {
                    throw bridgeError('CAPABILITY_MISMATCH');
                  }
                  connected = true;
                  generation += 1;
                  startHeartbeat(target);
                  if (!settled) {
                    settled = true;
                    connecting = null;
                    resolve(currentStatus());
                  }
                  return;
                }

                if (target !== socket) return;
                if (message.type === 'request') await handleRequest(target, message);
                else if (message.type === 'heartbeat_ack') validateServerEnvelope(message);
                else throw bridgeError('MESSAGE_TYPE_NOT_ALLOWED');
              } catch (error) {
                if (!connected) fail(error);
                else {
                  connected = false;
                  stopHeartbeat();
                  try { target.close(4400, String(error?.code || 'PROTOCOL_ERROR').slice(0, 120)); } catch (_) { /* best effort */ }
                }
              }
            };

            const onClose = () => {
              if (target !== socket) return;
              connected = false;
              stopHeartbeat();
              if (!settled && !intentionalClose) fail(bridgeError('BRIDGE_CONNECTION_CLOSED'));
            };

            const onError = () => {
              if (!settled && !intentionalClose) fail(bridgeError('BRIDGE_CONNECTION_FAILED'));
            };

            listenerCleanup.push(
              addSocketListener(target, 'open', onOpen),
              addSocketListener(target, 'message', onMessage),
              addSocketListener(target, 'close', onClose),
              addSocketListener(target, 'error', onError),
            );
          });

          return connecting;
        }

        async function disconnect() {
          intentionalClose = true;
          connected = false;
          stopHeartbeat();
          const target = socket;
          socket = null;
          connecting = null;
          cleanupListeners();
          if (!target || target.readyState === socketClosedConstant(WebSocketClass)) return;
          try { target.close(1000, 'CLIENT_DISCONNECT'); }
          catch (_) { /* best effort */ }
        }

        async function reconnect() {
          await disconnect();
          return connect();
        }

        return Object.freeze({connect, reconnect, disconnect, status: currentStatus});
      }

      module.exports = {buildBridgeUrl, buildHandshake, assertPort, createBridgeConnection};
    },
    "blockbench-plugin/live_bridge_adapter.js": function(module, exports, require) {
      'use strict';

      const {bridgeError, PROTOCOL_VERSION} = require('../live-bridge/protocol.js');
      const {createProjectSnapshot} = require('../live-bridge/project_snapshot.js');
      const {buildSessionFingerprint} = require('../live-bridge/fingerprint.js');
      const {createReadOnlyRouter} = require('../live-bridge/read_only_router.js');
      const {createBridgeConnection} = require('../live-bridge/blockbench_bridge_client.js');

      const TOOLKIT_VERSION = '0.3.0';
      const DESCRIPTOR_KEYS = new Set([
        'host', 'port', 'sessionId', 'token', 'protocolVersion',
        'minecraftVersion', 'loader', 'javaVersion', 'physicalProviders',
        'activeProviderProfile', 'mcpAuthorizedExtensionIds', 'heartbeatIntervalMs',
      ]);

      function requiredString(value, field, maxLength = 256) {
        if (typeof value !== 'string' || !value.trim() || value.length > maxLength) throw bridgeError('INVALID_CONNECTION_DESCRIPTOR', field);
        return value.trim();
      }

      function parseConnectionDescriptor(input) {
        let value = input;
        if (typeof input === 'string') {
          try { value = JSON.parse(input); }
          catch (_) { throw bridgeError('INVALID_CONNECTION_DESCRIPTOR', 'invalid JSON'); }
        }
        if (!value || typeof value !== 'object' || Array.isArray(value)) throw bridgeError('INVALID_CONNECTION_DESCRIPTOR');
        for (const key of Object.keys(value)) {
          if (!DESCRIPTOR_KEYS.has(key)) throw bridgeError('INVALID_CONNECTION_DESCRIPTOR', `unknown field: ${key}`);
        }

        const descriptor = {
          host: requiredString(value.host, 'host'),
          port: value.port,
          sessionId: requiredString(value.sessionId, 'sessionId'),
          token: requiredString(value.token, 'token'),
          protocolVersion: requiredString(value.protocolVersion, 'protocolVersion'),
          minecraftVersion: requiredString(value.minecraftVersion, 'minecraftVersion'),
          loader: requiredString(value.loader, 'loader'),
          javaVersion: requiredString(value.javaVersion, 'javaVersion'),
          activeProviderProfile: requiredString(value.activeProviderProfile, 'activeProviderProfile'),
          physicalProviders: Array.isArray(value.physicalProviders) ? value.physicalProviders.map((entry) => ({...entry})) : [],
          mcpAuthorizedExtensionIds: Array.isArray(value.mcpAuthorizedExtensionIds) ? [...value.mcpAuthorizedExtensionIds] : [],
          heartbeatIntervalMs: value.heartbeatIntervalMs,
        };

        if (!Number.isInteger(descriptor.port) || descriptor.port < 1 || descriptor.port > 65535) throw bridgeError('INVALID_CONNECTION_DESCRIPTOR', 'port');
        if (!/^[0-9a-f]{32}$/i.test(descriptor.sessionId)) throw bridgeError('INVALID_CONNECTION_DESCRIPTOR', 'sessionId');
        if (!/^[0-9a-f]{64}$/i.test(descriptor.token)) throw bridgeError('INVALID_CONNECTION_DESCRIPTOR', 'token');
        if (descriptor.protocolVersion !== PROTOCOL_VERSION) throw bridgeError('PROTOCOL_MISMATCH');
        if (descriptor.physicalProviders.length > 256 || descriptor.mcpAuthorizedExtensionIds.length > 256) throw bridgeError('INVALID_CONNECTION_DESCRIPTOR', 'entry limit');

        for (const entry of descriptor.physicalProviders) {
          if (!entry || typeof entry !== 'object' || Array.isArray(entry)) throw bridgeError('INVALID_CONNECTION_DESCRIPTOR', 'physicalProviders');
          entry.modId = requiredString(entry.modId, 'physicalProviders.modId');
          entry.version = requiredString(entry.version, 'physicalProviders.version');
          if (typeof entry.presence !== 'string') entry.presence = 'PRESENT';
          if (typeof entry.health !== 'string') entry.health = 'UNPROVEN';
        }
        descriptor.mcpAuthorizedExtensionIds = descriptor.mcpAuthorizedExtensionIds.map((id) => requiredString(id, 'mcpAuthorizedExtensionIds'));
        if (descriptor.heartbeatIntervalMs !== undefined && (!Number.isFinite(descriptor.heartbeatIntervalMs) || descriptor.heartbeatIntervalMs <= 0)) {
          throw bridgeError('INVALID_CONNECTION_DESCRIPTOR', 'heartbeatIntervalMs');
        }
        return Object.freeze(descriptor);
      }

      function installedExtensions(bb) {
        const installations = Array.isArray(bb?.Plugins?.installed) ? bb.Plugins.installed : [];
        return installations
          .filter((entry) => entry && entry.disabled !== true && typeof entry.id === 'string' && typeof entry.version === 'string')
          .map((entry) => ({pluginId: entry.id, pluginVersion: entry.version}));
      }

      function physicalProviderFingerprint(entries) {
        return entries.map((entry) => ({modId: entry.modId, modVersion: entry.version}));
      }

      function createBlockbenchLiveBridgeRuntime(bb, descriptorInput, options = {}) {
        if (!bb || !bb.Blockbench || bb.Blockbench.isWeb === true) throw bridgeError('DESKTOP_REQUIRED');
        const descriptor = parseConnectionDescriptor(descriptorInput);
        const getProject = () => bb.Blockbench.Project || null;
        const getInstalledExtensions = () => installedExtensions(bb);
        const router = createReadOnlyRouter({
          getProject,
          getBlockbenchVersion: () => String(bb.Blockbench.version || ''),
          getInstalledExtensions,
          getMcpAuthorizedExtensionIds: () => descriptor.mcpAuthorizedExtensionIds,
          physicalProviders: descriptor.physicalProviders,
          activeProviderProfile: () => descriptor.activeProviderProfile,
        });

        const snapshot = createProjectSnapshot(getProject());
        const fingerprint = buildSessionFingerprint({
          minecraftVersion: descriptor.minecraftVersion,
          loader: descriptor.loader,
          javaVersion: descriptor.javaVersion,
          blockbenchVersion: String(bb.Blockbench.version || ''),
          toolkitVersion: TOOLKIT_VERSION,
          protocolVersion: descriptor.protocolVersion,
          installedExtensions: getInstalledExtensions(),
          physicalProviders: physicalProviderFingerprint(descriptor.physicalProviders),
          activeProviderProfile: descriptor.activeProviderProfile,
          projectFormat: snapshot.projectFormat || 'unknown',
          projectRevision: snapshot.projectRevision,
        });

        const session = Object.freeze({
          sessionId: descriptor.sessionId,
          token: descriptor.token,
          protocolVersion: descriptor.protocolVersion,
        });
        const connection = createBridgeConnection({
          WebSocketClass: options.WebSocketClass,
          host: descriptor.host,
          port: descriptor.port,
          session,
          fingerprint,
          router,
          heartbeatIntervalMs: descriptor.heartbeatIntervalMs,
        });

        return Object.freeze({descriptor, fingerprint, router, connection});
      }

      module.exports = {
        TOOLKIT_VERSION,
        parseConnectionDescriptor,
        installedExtensions,
        createBlockbenchLiveBridgeRuntime,
      };
    },
    "blockbench-plugin/modeling_adapter.js": function(module, exports, require) {
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
    },
    "blockbench-plugin/uv_texture_adapter.js": function(module, exports, require) {
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
            for (const faceName of Object.keys(cubeFaces).sort((left, right) => left.localeCompare(right, 'en', {sensitivity: 'variant', numeric: false}))) {
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
    },
    "blockbench-plugin/animation_adapter.js": function(module, exports, require) {
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
        return value && typeof value === 'object' && typeof value.uuid === 'string' && value.uuid ? value.uuid : null;
      }

      function vector3FromObject(value, fallback) {
        const source = value && typeof value === 'object' ? value : {};
        const output = ['x', 'y', 'z'].map((axis, index) => Number.isFinite(source[axis]) ? source[axis] : fallback[index]);
        return output;
      }

      function createBlockbenchAnimationAdapter(bb) {
        const project = bb?.Blockbench?.Project;
        if (!project || typeof project !== 'object') fail('NO_PROJECT', 'No Blockbench project is open.');
        if (bb.Blockbench.isWeb !== false) fail('DESKTOP_REQUIRED', 'Animation mutations require desktop Blockbench.');
        if (typeof bb.Animation !== 'function') fail('BLOCKBENCH_API_UNAVAILABLE', 'Animation constructor is unavailable.');
        if (!bb.Undo || ['initEdit', 'finishEdit', 'cancelEdit'].some((name) => typeof bb.Undo[name] !== 'function')) {
          fail('BLOCKBENCH_API_UNAVAILABLE', 'Blockbench Undo API is incomplete.');
        }
        if (!bb.Animator || typeof bb.Animator.preview !== 'function') {
          fail('BLOCKBENCH_API_UNAVAILABLE', 'Animator.preview() is unavailable.');
        }

        let transactionOpen = false;

        function animations() {
          return Array.isArray(bb.Animation.all) ? bb.Animation.all : array(project.animations);
        }

        function groups() {
          return bb.Group && Array.isArray(bb.Group.all) ? bb.Group.all : array(project.groups);
        }

        function findAnimation(animationId) {
          return animations().find((animation) => idOf(animation) === animationId) || null;
        }

        function requireAnimation(animationId) {
          const animation = findAnimation(animationId);
          if (!animation) fail('ANIMATION_NOT_FOUND', `Animation "${animationId}" does not exist.`);
          return animation;
        }

        function findTarget(targetId) {
          return groups().find((group) => idOf(group) === targetId) || null;
        }

        function requireTarget(targetId) {
          const target = findTarget(targetId);
          if (!target) fail('ANIMATION_TARGET_NOT_FOUND', `Animation target "${targetId}" does not exist.`);
          return target;
        }

        function animatorsOf(animation) {
          return animation?.animators && typeof animation.animators === 'object'
            ? Object.values(animation.animators).filter(Boolean)
            : [];
        }

        function keyframesOf(animation) {
          const output = [];
          for (const animator of animatorsOf(animation)) {
            for (const keyframe of array(animator.keyframes)) {
              if (keyframe && !output.includes(keyframe)) output.push(keyframe);
            }
          }
          return output;
        }

        function allKeyframes() {
          const output = [];
          for (const animation of animations()) {
            for (const keyframe of keyframesOf(animation)) {
              if (!output.includes(keyframe)) output.push(keyframe);
            }
          }
          return output;
        }

        function findKeyframe(animation, keyframeId) {
          for (const animator of animatorsOf(animation)) {
            const keyframe = array(animator.keyframes).find((entry) => idOf(entry) === keyframeId);
            if (keyframe) return {animator, keyframe};
          }
          return null;
        }

        function keyframeRevisionSnapshot() {
          return animations().map((animation) => ({
            animationId: idOf(animation),
            animators: Object.keys(animation?.animators || {}).sort((left, right) => left.localeCompare(right, 'en')).map((targetId) => ({
              targetId,
              keyframes: array(animation.animators[targetId]?.keyframes).map((keyframe) => ({
                keyframeId: idOf(keyframe),
                channel: typeof keyframe?.channel === 'string' ? keyframe.channel : null,
                time: Number.isFinite(keyframe?.time) ? keyframe.time : null,
                interpolation: typeof keyframe?.interpolation === 'string' ? keyframe.interpolation : null,
                dataPoints: array(keyframe?.data_points).map((point) => ({
                  x: point?.x ?? null,
                  y: point?.y ?? null,
                  z: point?.z ?? null,
                })),
              })),
            })),
          }));
        }

        function getRevision() {
          const {createProjectSnapshot, hashRevision} = require('../live-bridge/project_snapshot.js');
          const baseRevision = createProjectSnapshot(project).projectRevision;
          return hashRevision({baseRevision, animationKeyframes: keyframeRevisionSnapshot()});
        }

        function preflight(operations) {
          const simulated = new Map();
          for (const animation of animations()) {
            const id = idOf(animation);
            if (!id) continue;
            const keyframes = new Map();
            for (const animator of animatorsOf(animation)) {
              for (const keyframe of array(animator.keyframes)) {
                const keyframeId = idOf(keyframe);
                if (keyframeId) keyframes.set(keyframeId, {targetId: idOf(animator), channel: keyframe.channel});
              }
            }
            simulated.set(id, {
              id,
              name: typeof animation.name === 'string' ? animation.name : '',
              length: Number.isFinite(animation.length) ? animation.length : 0,
              keyframes,
            });
          }

          function animationNameExists(name, excludeId = null) {
            const wanted = String(name).toLowerCase();
            return [...simulated.values()].some((entry) => entry.id !== excludeId && entry.name.toLowerCase() === wanted);
          }

          for (const operation of operations) {
            switch (operation.type) {
              case 'animation_create':
                if (simulated.has(operation.id)) fail('DUPLICATE_ANIMATION_ID', `Animation id "${operation.id}" already exists.`);
                if (animationNameExists(operation.name)) fail('DUPLICATE_ANIMATION_NAME', `Animation name "${operation.name}" already exists.`);
                simulated.set(operation.id, {
                  id: operation.id,
                  name: operation.name,
                  length: operation.length,
                  keyframes: new Map(),
                });
                break;
              case 'animation_update_settings': {
                const animation = simulated.get(operation.animationId);
                if (!animation) fail('ANIMATION_NOT_FOUND', `Animation "${operation.animationId}" does not exist.`);
                if (operation.name !== undefined && animationNameExists(operation.name, operation.animationId)) {
                  fail('DUPLICATE_ANIMATION_NAME', `Animation name "${operation.name}" already exists.`);
                }
                if (operation.name !== undefined) animation.name = operation.name;
                if (operation.length !== undefined) animation.length = operation.length;
                break;
              }
              case 'animation_delete':
                if (!simulated.has(operation.animationId)) fail('ANIMATION_NOT_FOUND', `Animation "${operation.animationId}" does not exist.`);
                simulated.delete(operation.animationId);
                break;
              case 'animation_add_keyframe': {
                const animation = simulated.get(operation.animationId);
                if (!animation) fail('ANIMATION_NOT_FOUND', `Animation "${operation.animationId}" does not exist.`);
                requireTarget(operation.targetId);
                if (animation.keyframes.has(operation.keyframeId)) {
                  fail('DUPLICATE_KEYFRAME_ID', `Keyframe "${operation.keyframeId}" already exists in animation "${operation.animationId}".`);
                }
                if (operation.time > animation.length) {
                  fail('KEYFRAME_OUTSIDE_ANIMATION', `Keyframe time ${operation.time} exceeds animation length ${animation.length}.`);
                }
                animation.keyframes.set(operation.keyframeId, {targetId: operation.targetId, channel: operation.channel});
                break;
              }
              case 'animation_update_keyframe': {
                const animation = simulated.get(operation.animationId);
                if (!animation) fail('ANIMATION_NOT_FOUND', `Animation "${operation.animationId}" does not exist.`);
                requireTarget(operation.targetId);
                if (!animation.keyframes.has(operation.keyframeId)) {
                  fail('KEYFRAME_NOT_FOUND', `Keyframe "${operation.keyframeId}" does not exist in animation "${operation.animationId}".`);
                }
                if (operation.time > animation.length) {
                  fail('KEYFRAME_OUTSIDE_ANIMATION', `Keyframe time ${operation.time} exceeds animation length ${animation.length}.`);
                }
                animation.keyframes.set(operation.keyframeId, {targetId: operation.targetId, channel: operation.channel});
                break;
              }
              case 'animation_delete_keyframe': {
                const animation = simulated.get(operation.animationId);
                if (!animation) fail('ANIMATION_NOT_FOUND', `Animation "${operation.animationId}" does not exist.`);
                if (!animation.keyframes.has(operation.keyframeId)) {
                  fail('KEYFRAME_NOT_FOUND', `Keyframe "${operation.keyframeId}" does not exist in animation "${operation.animationId}".`);
                }
                animation.keyframes.delete(operation.keyframeId);
                break;
              }
              case 'animation_add_effect_marker':
              case 'animation_delete_effect_marker':
                fail('PROVIDER_ADAPTER_REQUIRED', 'Abstract PR5 effect markers require a provider adapter before Blockbench serialization.');
                break;
              default:
                fail('UNSUPPORTED_ANIMATION_OPERATION', `Animation operation "${operation.type}" is not supported by the Blockbench adapter.`);
            }
          }
          return true;
        }

        function undoAspects() {
          return {
            animations: animations().slice(),
            keyframes: allKeyframes().slice(),
          };
        }

        function beginTransaction() {
          if (transactionOpen) fail('TRANSACTION_ALREADY_OPEN', 'A Blockbench Undo transaction is already open.');
          bb.Undo.initEdit(undoAspects());
          transactionOpen = true;
        }

        function finishTransaction(label) {
          if (!transactionOpen) fail('NO_ACTIVE_TRANSACTION', 'No Blockbench Undo transaction is open.');
          bb.Undo.finishEdit(label, undoAspects());
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

        function addKeyframe(animation, operation) {
          const target = requireTarget(operation.targetId);
          if (typeof animation.getBoneAnimator !== 'function') {
            fail('BLOCKBENCH_API_UNAVAILABLE', 'Animation.getBoneAnimator() is unavailable.');
          }
          const animator = animation.getBoneAnimator(target);
          if (!animator || typeof animator.addKeyframe !== 'function') {
            fail('ANIMATION_TARGET_UNSUPPORTED', `Target "${operation.targetId}" does not expose a mutable animation channel.`);
          }
          const keyframe = animator.addKeyframe({
            channel: operation.channel,
            time: operation.time,
            interpolation: operation.easing,
            data_points: [{x: operation.value[0], y: operation.value[1], z: operation.value[2]}],
          }, operation.keyframeId);
          if (!keyframe) fail('KEYFRAME_CREATE_FAILED', `Blockbench did not create keyframe "${operation.keyframeId}".`);
          return idOf(keyframe) || operation.keyframeId;
        }

        function applyOperation(operation) {
          switch (operation.type) {
            case 'animation_create': {
              const animation = new bb.Animation({
                uuid: operation.id,
                name: operation.name,
                length: operation.length,
                loop: operation.loop,
              });
              if (typeof animation.add !== 'function') fail('BLOCKBENCH_API_UNAVAILABLE', 'Animation.add() is unavailable.');
              animation.add(false);
              return idOf(animation) || operation.id;
            }
            case 'animation_update_settings': {
              const animation = requireAnimation(operation.animationId);
              if (operation.name !== undefined) animation.name = operation.name;
              if (operation.length !== undefined) {
                if (typeof animation.setLength !== 'function') fail('BLOCKBENCH_API_UNAVAILABLE', 'Animation.setLength() is unavailable.');
                animation.setLength(operation.length);
              }
              if (operation.loop !== undefined) {
                if (typeof animation.setLoop !== 'function') fail('BLOCKBENCH_API_UNAVAILABLE', 'Animation.setLoop() is unavailable.');
                animation.setLoop(operation.loop, false);
              }
              return idOf(animation) || operation.animationId;
            }
            case 'animation_delete': {
              const animation = requireAnimation(operation.animationId);
              if (typeof animation.remove !== 'function') fail('BLOCKBENCH_API_UNAVAILABLE', 'Animation.remove() is unavailable.');
              animation.remove(false);
              return operation.animationId;
            }
            case 'animation_add_keyframe':
              return addKeyframe(requireAnimation(operation.animationId), operation);
            case 'animation_update_keyframe': {
              const animation = requireAnimation(operation.animationId);
              const found = findKeyframe(animation, operation.keyframeId);
              if (!found) fail('KEYFRAME_NOT_FOUND', `Keyframe "${operation.keyframeId}" does not exist.`);
              if (typeof found.keyframe.remove !== 'function') fail('BLOCKBENCH_API_UNAVAILABLE', 'Keyframe.remove() is unavailable.');
              found.keyframe.remove();
              return addKeyframe(animation, operation);
            }
            case 'animation_delete_keyframe': {
              const animation = requireAnimation(operation.animationId);
              const found = findKeyframe(animation, operation.keyframeId);
              if (!found) fail('KEYFRAME_NOT_FOUND', `Keyframe "${operation.keyframeId}" does not exist.`);
              if (typeof found.keyframe.remove !== 'function') fail('BLOCKBENCH_API_UNAVAILABLE', 'Keyframe.remove() is unavailable.');
              found.keyframe.remove();
              return operation.keyframeId;
            }
            case 'animation_add_effect_marker':
            case 'animation_delete_effect_marker':
              fail('PROVIDER_ADAPTER_REQUIRED', 'Abstract PR5 effect markers require a provider adapter before Blockbench serialization.');
              break;
            default:
              fail('UNSUPPORTED_ANIMATION_OPERATION', `Animation operation "${operation.type}" is not supported by the Blockbench adapter.`);
          }
          return null;
        }

        function selectPreviewAnimation(request) {
          const animation = requireAnimation(request.animationId);
          if (request.time > animation.length) {
            fail('PREVIEW_TIME_OUT_OF_RANGE', `Preview time ${request.time} exceeds animation length ${animation.length}.`);
          }
          if (typeof animation.select !== 'function') fail('BLOCKBENCH_API_UNAVAILABLE', 'Animation.select() is unavailable.');
          animation.select();
          animation.time = request.time;
          bb.Animator.preview(false);
          return animation;
        }

        function playPreview(request) {
          const animation = selectPreviewAnimation(request);
          if (typeof animation.togglePlayingState === 'function') animation.togglePlayingState(true);
          return Object.freeze({ok: true, animationId: request.animationId, time: request.time});
        }

        function stopPreview() {
          const animation = bb.Animation.selected || null;
          if (animation && typeof animation.togglePlayingState === 'function') animation.togglePlayingState(false);
          if (typeof bb.Animator.showDefaultPose === 'function') bb.Animator.showDefaultPose(false);
          return Object.freeze({ok: true, animationId: animation ? idOf(animation) : null});
        }

        function inspectPose(request) {
          selectPreviewAnimation(request);
          const targets = {};
          for (const group of groups()) {
            const targetId = idOf(group);
            if (!targetId || !group.mesh) continue;
            targets[targetId] = Object.freeze({
              position: Object.freeze(vector3FromObject(group.mesh.position, [0, 0, 0])),
              rotation: Object.freeze(vector3FromObject(group.mesh.rotation, [0, 0, 0])),
              scale: Object.freeze(vector3FromObject(group.mesh.scale, [1, 1, 1])),
            });
          }
          return Object.freeze({
            animationId: request.animationId,
            time: request.time,
            targets: Object.freeze(targets),
          });
        }

        function capturePose(request) {
          selectPreviewAnimation(request);
          const presets = array(bb.DefaultCameraPresets);
          const preset = presets.find((entry) => entry && entry.id === request.cameraPreset);
          if (!preset) fail('CAMERA_PRESET_NOT_FOUND', `Camera preset "${request.cameraPreset}" is not available.`);
          const preview = bb?.Preview?.selected;
          if (!preview || typeof preview.loadAnglePreset !== 'function') {
            fail('BLOCKBENCH_API_UNAVAILABLE', 'Preview.selected.loadAnglePreset() is unavailable.');
          }
          if (!bb.Screencam || typeof bb.Screencam.screenshotPreview !== 'function') {
            fail('BLOCKBENCH_API_UNAVAILABLE', 'Screencam.screenshotPreview() is unavailable.');
          }
          preview.loadAnglePreset(preset);
          return new Promise((resolve, reject) => {
            try {
              bb.Screencam.screenshotPreview(preview, {
                width: request.resolution[0],
                height: request.resolution[1],
              }, (dataUrl) => {
                resolve(Object.freeze({
                  ok: true,
                  animationId: request.animationId,
                  time: request.time,
                  cameraPreset: request.cameraPreset,
                  resolution: Object.freeze(request.resolution.slice()),
                  dataUrl,
                }));
              });
            } catch (error) {
              reject(error);
            }
          });
        }

        return Object.freeze({
          getRevision,
          preflight,
          beginTransaction,
          applyOperation,
          finishTransaction,
          cancelTransaction,
          playPreview,
          stopPreview,
          inspectPose,
          capturePose,
        });
      }

      module.exports = {createBlockbenchAnimationAdapter};
    },
    "blockbench-plugin/geckolib4_adapter.js": function(module, exports, require) {
      'use strict';

      const geckolib4 = require('../core/provider-adapter/geckolib4_adapter.js');

      function fail(code, message) {
        throw new geckolib4.GeckoLib4ContractError(code, message);
      }

      function normalizedSourcePath(value) {
        if (typeof value !== 'string' || value.length === 0) fail('GECKOLIB4_SOURCE_NOT_SAVED', 'Active GeckoLib project must be saved as a .bbmodel before provider export.');
        const normalized = value.replace(/\\/g, '/');
        if (!normalized.toLowerCase().endsWith('.bbmodel')) fail('GECKOLIB4_SOURCE_MUST_BE_BBMODEL', 'Active GeckoLib project source must remain a .bbmodel file.');
        return normalized;
      }

      function cloneJsonDocument(value, code, label) {
        if (typeof value === 'string') {
          try {
            return JSON.parse(value);
          } catch (error) {
            fail(code, `${label} compiler returned invalid JSON: ${error.message}`);
          }
        }
        if (!value || typeof value !== 'object') fail(code, `${label} compiler must return JSON text or an object.`);
        try {
          return JSON.parse(JSON.stringify(value));
        } catch (error) {
          fail(code, `${label} compiler returned a non-serializable object: ${error.message}`);
        }
      }

      function deepFreezeJsonDocument(value) {
        if (!value || typeof value !== 'object' || Object.isFrozen(value)) return value;
        for (const child of Object.values(value)) deepFreezeJsonDocument(child);
        return Object.freeze(value);
      }

      function createBlockbenchGeckoLib4Adapter(bb) {
        if (!bb || typeof bb !== 'object') fail('GECKOLIB4_BLOCKBENCH_UNAVAILABLE', 'Blockbench API object is required.');
        const project = bb.Blockbench?.Project;
        if (!project || project.format?.id !== 'geckolib_model') {
          fail('GECKOLIB4_PROJECT_FORMAT_REQUIRED', 'Active Blockbench project must use the GeckoLib plugin format geckolib_model.');
        }
        const savedSourcePath = normalizedSourcePath(project.save_path);
        if (typeof bb.Codecs?.bedrock?.compile !== 'function') {
          fail('GECKOLIB4_MODEL_CODEC_UNAVAILABLE', 'Blockbench Codecs.bedrock.compile is required by the audited GeckoLib 4.2.5 integration.');
        }

        const trustedPreviews = new WeakSet();

        function sourcePath() {
          return savedSourcePath;
        }

        function compileModelDocument() {
          const document = cloneJsonDocument(bb.Codecs.bedrock.compile(), 'INVALID_GECKOLIB4_COMPILED_MODEL', 'GeckoLib model');
          geckolib4.validateGeckoLib4GeoDocument(document);
          return deepFreezeJsonDocument(document);
        }

        function compileAnimationDocument() {
          if (typeof bb.Animator?.buildFile !== 'function') {
            fail('GECKOLIB4_ANIMATION_CODEC_UNAVAILABLE', 'Blockbench Animator.buildFile is required by the audited GeckoLib 4.2.5 integration.');
          }
          const document = cloneJsonDocument(bb.Animator.buildFile(), 'INVALID_GECKOLIB4_COMPILED_ANIMATION', 'GeckoLib animation');
          geckolib4.validateGeckoLib4AnimationDocument(document);
          return deepFreezeJsonDocument(document);
        }

        function previewExport(request) {
          if (!request || typeof request !== 'object' || Array.isArray(request)) fail('INVALID_GECKOLIB4_EXPORT_PLAN', 'Export request must be an object.');
          const plan = geckolib4.createGeckoLib4ExportPlan({...request, sourcePath: savedSourcePath});
          const modelDocument = compileModelDocument();
          const animationDocument = request.includeAnimations === true ? compileAnimationDocument() : null;
          const artifacts = plan.artifacts.map((artifact) => Object.freeze({
            kind: artifact.kind,
            path: artifact.path,
            document: artifact.kind === 'model' ? modelDocument : animationDocument,
          }));
          const preview = Object.freeze({
            plan,
            artifacts: Object.freeze(artifacts),
            runtimeEvidence: 'UNPROVEN',
          });
          trustedPreviews.add(preview);
          return preview;
        }

        function stageExport(preview, writer) {
          if (!preview || typeof preview !== 'object' || !trustedPreviews.has(preview)) {
            fail('INVALID_GECKOLIB4_EXPORT_PREVIEW', 'Only a validated preview produced by this adapter can be staged.');
          }
          if (!writer || typeof writer.writeText !== 'function') {
            fail('INVALID_GECKOLIB4_EXPORT_WRITER', 'Export writer must provide writeText(path, content).');
          }
          for (const artifact of preview.artifacts) {
            if (artifact.path === preview.plan.sourcePath || artifact.path.toLowerCase().endsWith('.bbmodel')) {
              fail('GECKOLIB4_SOURCE_OVERWRITE_FORBIDDEN', 'Provider staging must never overwrite the source .bbmodel.');
            }
            writer.writeText(artifact.path, `${JSON.stringify(artifact.document, null, 2)}\n`);
          }
          return Object.freeze({
            ok: true,
            staged: preview.artifacts.length,
            sourcePath: preview.plan.sourcePath,
            preserveSource: true,
            runtimeEvidence: 'UNPROVEN',
          });
        }

        return Object.freeze({
          sourcePath,
          compileModelDocument,
          compileAnimationDocument,
          previewExport,
          stageExport,
        });
      }

      module.exports = {
        createBlockbenchGeckoLib4Adapter,
      };
    },
    "blockbench-plugin/azurelib3_adapter.js": function(module, exports, require) {
      'use strict';

      const azurelib3 = require('../core/provider-adapter/azurelib3_adapter.js');

      function fail(code, message) {
        throw new azurelib3.AzureLib3ContractError(code, message);
      }

      function normalizedSourcePath(value) {
        if (typeof value !== 'string' || value.length === 0) {
          fail('AZURELIB3_SOURCE_NOT_SAVED', 'Active AzureLib project must be saved as a .bbmodel before provider export.');
        }
        const normalized = value.replace(/\\/g, '/');
        if (!normalized.toLowerCase().endsWith('.bbmodel')) {
          fail('AZURELIB3_SOURCE_MUST_BE_BBMODEL', 'Active AzureLib project source must remain a .bbmodel file.');
        }
        return normalized;
      }

      function cloneJsonDocument(value, code, label) {
        if (typeof value === 'string') {
          try {
            return JSON.parse(value);
          } catch (error) {
            fail(code, `${label} compiler returned invalid JSON: ${error.message}`);
          }
        }
        if (!value || typeof value !== 'object') {
          fail(code, `${label} compiler must return JSON text or an object.`);
        }
        try {
          return JSON.parse(JSON.stringify(value));
        } catch (error) {
          fail(code, `${label} compiler returned a non-serializable object: ${error.message}`);
        }
      }

      function deepFreezeJsonDocument(value) {
        if (!value || typeof value !== 'object' || Object.isFrozen(value)) return value;
        for (const child of Object.values(value)) deepFreezeJsonDocument(child);
        return Object.freeze(value);
      }

      function createBlockbenchAzureLib3Adapter(bb) {
        if (!bb || typeof bb !== 'object') {
          fail('AZURELIB3_BLOCKBENCH_UNAVAILABLE', 'Blockbench API object is required.');
        }
        if (bb.Blockbench?.isWeb !== false) {
          fail('AZURELIB3_DESKTOP_REQUIRED', 'AzureLib provider export requires desktop Blockbench.');
        }

        const project = bb.Blockbench?.Project;
        if (!project || project.format?.id !== azurelib3.AZURELIB3_AUTHORITY.blockbenchFormatId) {
          fail('AZURELIB3_PROJECT_FORMAT_REQUIRED', 'Active Blockbench project must use the AzureLib plugin format azure_model.');
        }
        const savedSourcePath = normalizedSourcePath(project.save_path);
        if (typeof bb.Codecs?.bedrock?.compile !== 'function') {
          fail('AZURELIB3_MODEL_CODEC_UNAVAILABLE', 'Blockbench Codecs.bedrock.compile is required by the audited AzureLib 2.1.5 integration.');
        }

        const trustedPreviews = new WeakSet();

        function sourcePath() {
          return savedSourcePath;
        }

        function animationCodec() {
          const codec = project.format?.animation_codec;
          if (!codec || typeof codec.compileFile !== 'function' || typeof codec.write !== 'function') {
            fail('AZURELIB3_ANIMATION_CODEC_UNAVAILABLE', 'The active azure_model format must expose animation_codec.compileFile and animation_codec.write from azurelib_utils 2.1.5.');
          }
          return codec;
        }

        function compileModelDocument() {
          const document = cloneJsonDocument(
            bb.Codecs.bedrock.compile(),
            'INVALID_AZURELIB3_COMPILED_MODEL',
            'AzureLib model',
          );
          azurelib3.validateAzureLib3GeoDocument(document);
          return deepFreezeJsonDocument(document);
        }

        function compileAnimationDocument() {
          const document = cloneJsonDocument(
            animationCodec().compileFile(),
            'INVALID_AZURELIB3_COMPILED_ANIMATION',
            'AzureLib animation',
          );
          azurelib3.validateAzureLib3AnimationDocument(document);
          return deepFreezeJsonDocument(document);
        }

        function previewExport(request) {
          if (!request || typeof request !== 'object' || Array.isArray(request)) {
            fail('INVALID_AZURELIB3_EXPORT_PLAN', 'Export request must be an object.');
          }
          const plan = azurelib3.createAzureLib3ExportPlan({...request, sourcePath: savedSourcePath});
          const modelDocument = compileModelDocument();
          const animationDocument = request.includeAnimations === true ? compileAnimationDocument() : null;
          const artifacts = plan.artifacts.map((artifact) => Object.freeze({
            kind: artifact.kind,
            path: artifact.path,
            document: artifact.kind === 'model' ? modelDocument : animationDocument,
          }));
          const preview = Object.freeze({
            plan,
            artifacts: Object.freeze(artifacts),
            runtimeEvidence: 'UNPROVEN',
          });
          trustedPreviews.add(preview);
          return preview;
        }

        function stageExport(preview, writer) {
          if (!preview || typeof preview !== 'object' || !trustedPreviews.has(preview)) {
            fail('INVALID_AZURELIB3_EXPORT_PREVIEW', 'Only a validated preview produced by this adapter can be staged.');
          }
          if (!writer || typeof writer.writeText !== 'function') {
            fail('INVALID_AZURELIB3_EXPORT_WRITER', 'Export writer must provide writeText(path, content).');
          }

          for (const artifact of preview.artifacts) {
            if (artifact.path === preview.plan.sourcePath || artifact.path.toLowerCase().endsWith('.bbmodel')) {
              fail('AZURELIB3_SOURCE_OVERWRITE_FORBIDDEN', 'Provider staging must never overwrite the source .bbmodel.');
            }

            if (artifact.kind === 'animation') {
              const serialized = animationCodec().write(artifact.document, artifact.path);
              if (typeof serialized !== 'string') {
                fail('INVALID_AZURELIB3_ANIMATION_SERIALIZATION', 'AzureLib animation_codec.write must return serialized JSON text.');
              }
              writer.writeText(artifact.path, serialized);
            } else {
              writer.writeText(artifact.path, `${JSON.stringify(artifact.document, null, 2)}\n`);
            }
          }

          return Object.freeze({
            ok: true,
            staged: preview.artifacts.length,
            sourcePath: preview.plan.sourcePath,
            preserveSource: true,
            runtimeEvidence: 'UNPROVEN',
          });
        }

        return Object.freeze({
          sourcePath,
          compileModelDocument,
          compileAnimationDocument,
          previewExport,
          stageExport,
        });
      }

      module.exports = {
        createBlockbenchAzureLib3Adapter,
      };
    },
    "blockbench-plugin/neoforge_native_animation_adapter.js": function(module, exports, require) {
      'use strict';

      const neoforgeNative = require('../core/provider-adapter/neoforge_native_animation_adapter.js');

      function fail(code, message) {
        throw new neoforgeNative.NeoForgeNativeAnimationContractError(code, message);
      }

      function normalizedSourcePath(value) {
        if (typeof value !== 'string' || value.length === 0) {
          fail('NEOFORGE_NATIVE_ANIMATION_SOURCE_NOT_SAVED', 'Active Blockbench project must be saved as a .bbmodel before native animation export.');
        }
        const normalized = value.replace(/\\/g, '/');
        if (!normalized.toLowerCase().endsWith('.bbmodel')) {
          fail('NEOFORGE_NATIVE_ANIMATION_SOURCE_NOT_SAVED', 'Active Blockbench project source must remain a .bbmodel file.');
        }
        return normalized;
      }

      function createBlockbenchNeoForgeNativeAnimationAdapter(bb) {
        if (!bb || typeof bb !== 'object') {
          fail('NEOFORGE_NATIVE_ANIMATION_BLOCKBENCH_UNAVAILABLE', 'Blockbench API object is required.');
        }
        if (bb.Blockbench?.isWeb !== false) {
          fail('NEOFORGE_NATIVE_ANIMATION_DESKTOP_REQUIRED', 'NeoForge native animation export requires desktop Blockbench.');
        }
        const project = bb.Blockbench?.Project;
        if (!project || typeof project !== 'object') {
          fail('NEOFORGE_NATIVE_ANIMATION_BLOCKBENCH_UNAVAILABLE', 'No active Blockbench project is available.');
        }
        const savedSourcePath = normalizedSourcePath(project.save_path);
        if (typeof bb.BoneAnimator !== 'function') {
          fail('NEOFORGE_NATIVE_ANIMATION_BLOCKBENCH_API_UNAVAILABLE', 'Blockbench BoneAnimator API is required.');
        }

        const trustedPreviews = new WeakSet();

        function sourcePath() {
          return savedSourcePath;
        }

        function animations() {
          if (Array.isArray(bb.Animation?.all)) return bb.Animation.all;
          return Array.isArray(project.animations) ? project.animations : [];
        }

        function requireAnimation(animationId) {
          if (typeof animationId !== 'string' || animationId.length === 0) {
            fail('NEOFORGE_NATIVE_ANIMATION_NOT_FOUND', 'animationId must identify an active Blockbench animation.');
          }
          const animation = animations().find((entry) => entry && entry.uuid === animationId) || null;
          if (!animation) fail('NEOFORGE_NATIVE_ANIMATION_NOT_FOUND', `Animation ${JSON.stringify(animationId)} does not exist.`);
          return animation;
        }

        function keyframeVector(keyframe, field) {
          if (!keyframe || typeof keyframe.get !== 'function') {
            fail('NEOFORGE_NATIVE_ANIMATION_KEYFRAME_UNAVAILABLE', `${field} does not expose Blockbench keyframe values.`);
          }
          return ['x', 'y', 'z'].map((axis) => keyframe.get(axis));
        }

        function providerNeutralAnimation(animation) {
          const channels = [];
          for (const animator of Object.values(animation.animators || {})) {
            if (!(animator instanceof bb.BoneAnimator)) {
              fail('UNPROVEN_NEOFORGE_NATIVE_ANIMATION_ANIMATOR', 'Only audited BoneAnimator transform channels can be exported to NeoForge native JSON.');
            }
            if (typeof animator.name !== 'string' || animator.name.length === 0) {
              fail('UNPROVEN_NEOFORGE_NATIVE_ANIMATION_ANIMATOR', 'Each exported BoneAnimator must expose its bone name.');
            }
            for (const channel of ['position', 'rotation', 'scale']) {
              const keyframes = Array.isArray(animator[channel]) ? animator[channel] : [];
              if (keyframes.length === 0) continue;
              channels.push({
                bone: animator.name,
                channel,
                keyframes: keyframes.map((keyframe, index) => ({
                  time: keyframe?.time,
                  value: keyframeVector(keyframe, `${animator.name}.${channel}[${index}]`),
                  easing: keyframe?.interpolation,
                })),
              });
            }
          }
          return {
            length: animation.length,
            loop: animation.loop,
            channels,
            effectMarkers: Array.isArray(animation.markers) ? animation.markers : [],
          };
        }

        function previewExport(request) {
          if (!request || typeof request !== 'object' || Array.isArray(request)) {
            fail('INVALID_NEOFORGE_NATIVE_ANIMATION_EXPORT_PLAN', 'Export request must be an object.');
          }
          const plan = neoforgeNative.createNeoForgeNativeAnimationExportPlan({...request, sourcePath: savedSourcePath});
          const animation = requireAnimation(request.animationId);
          const document = neoforgeNative.serializeNeoForgeNativeAnimation(providerNeutralAnimation(animation));
          const artifact = Object.freeze({kind: 'animation', path: plan.outputPath, document});
          const preview = Object.freeze({
            plan,
            artifacts: Object.freeze([artifact]),
            runtimeEvidence: 'UNPROVEN',
          });
          trustedPreviews.add(preview);
          return preview;
        }

        function stageExport(preview, writer) {
          if (!preview || typeof preview !== 'object' || !trustedPreviews.has(preview)) {
            fail('INVALID_NEOFORGE_NATIVE_ANIMATION_EXPORT_PREVIEW', 'Only a validated preview produced by this adapter can be staged.');
          }
          if (!writer || typeof writer.writeText !== 'function') {
            fail('INVALID_NEOFORGE_NATIVE_ANIMATION_EXPORT_WRITER', 'Export writer must provide writeText(path, content).');
          }
          for (const artifact of preview.artifacts) {
            if (artifact.path === preview.plan.sourcePath || artifact.path.toLowerCase().endsWith('.bbmodel')) {
              fail('NEOFORGE_NATIVE_ANIMATION_SOURCE_OVERWRITE_FORBIDDEN', 'Native animation staging must never overwrite the source .bbmodel.');
            }
            neoforgeNative.validateNeoForgeNativeAnimationDocument(artifact.document);
            writer.writeText(artifact.path, `${JSON.stringify(artifact.document, null, 2)}\n`);
          }
          return Object.freeze({
            ok: true,
            staged: preview.artifacts.length,
            sourcePath: preview.plan.sourcePath,
            preserveSource: true,
            runtimeEvidence: 'UNPROVEN',
          });
        }

        return Object.freeze({sourcePath, previewExport, stageExport});
      }

      module.exports = {
        createBlockbenchNeoForgeNativeAnimationAdapter,
      };
    },
    "blockbench-plugin/easy_model_entities_adapter.js": function(module, exports, require) {
      'use strict';

      const easyModelEntities = require('../core/provider-adapter/easy_model_entities_adapter.js');
      const {normalizeBbmodelSourcePath} = require('../core/common/contract_utils.js');

      function fail(code, message) {
        throw new easyModelEntities.EasyModelEntitiesContractError(code, message);
      }

      function createBlockbenchEasyModelEntitiesAdapter(bb) {
        if (!bb || typeof bb !== 'object') {
          fail('EASY_MODEL_ENTITIES_BLOCKBENCH_UNAVAILABLE', 'Blockbench API object is required.');
        }
        if (bb.Blockbench?.isWeb !== false) {
          fail('EASY_MODEL_ENTITIES_DESKTOP_REQUIRED', 'The audited Easy Model Entities exporter is a desktop Blockbench plugin.');
        }
        const project = bb.Blockbench?.Project;
        if (!project || typeof project !== 'object') {
          fail('EASY_MODEL_ENTITIES_BLOCKBENCH_UNAVAILABLE', 'No active Blockbench project is available.');
        }
        const savedSourcePath = normalizeBbmodelSourcePath(
          project.save_path,
          fail,
          'EASY_MODEL_ENTITIES_SOURCE_NOT_SAVED',
          'Active Blockbench project must be saved as a .bbmodel before Easy Model Entities handoff.',
          'Active Blockbench project source must remain a .bbmodel file.',
        );

        function sourcePath() {
          return savedSourcePath;
        }

        function previewHandoff(request) {
          if (!request || typeof request !== 'object' || Array.isArray(request)) {
            fail('INVALID_EASY_MODEL_ENTITIES_EXPORT_PLAN', 'Handoff request must be an object.');
          }
          const plan = easyModelEntities.createEasyModelEntitiesExportPlan({...request, sourcePath: savedSourcePath});
          return Object.freeze({
            plan,
            requiresOfficialExporter: true,
            exporterPluginId: easyModelEntities.EASY_MODEL_ENTITIES_AUTHORITY.blockbenchPluginId,
            exporterPluginVersion: easyModelEntities.EASY_MODEL_ENTITIES_AUTHORITY.blockbenchPluginVersion,
            runtimeEvidence: 'UNPROVEN',
          });
        }

        return Object.freeze({sourcePath, previewHandoff});
      }

      module.exports = {
        createBlockbenchEasyModelEntitiesAdapter,
      };
    },
    "blockbench-plugin/emf_cem_adapter.js": function(module, exports, require) {
      'use strict';

      const emfCem = require('../core/provider-adapter/emf_cem_adapter.js');
      const {normalizeBbmodelSourcePath} = require('../core/common/contract_utils.js');

      function fail(code, message) {
        throw new emfCem.EmfCemContractError(code, message);
      }

      function createBlockbenchEmfCemAdapter(bb) {
        if (!bb || typeof bb !== 'object') {
          fail('EMF_CEM_BLOCKBENCH_UNAVAILABLE', 'Blockbench API object is required.');
        }
        const project = bb.Blockbench?.Project;
        if (!project || typeof project !== 'object') {
          fail('EMF_CEM_BLOCKBENCH_UNAVAILABLE', 'No active Blockbench project is available.');
        }
        const savedSourcePath = normalizeBbmodelSourcePath(
          project.save_path,
          fail,
          'EMF_CEM_SOURCE_NOT_SAVED',
          'Active Blockbench project must be saved as a .bbmodel before EMF/CEM handoff.',
          'Active Blockbench project source must remain a saved .bbmodel file.',
        );
        if (bb.Format?.id !== emfCem.EMF_CEM_AUTHORITY.cemCodecId) {
          fail('EMF_CEM_FORMAT_REQUIRED', `Active Blockbench format must be ${emfCem.EMF_CEM_AUTHORITY.cemCodecId}.`);
        }
        const codec = bb.Codecs?.[emfCem.EMF_CEM_AUTHORITY.cemCodecId];
        if (!codec || typeof codec.compile !== 'function') {
          fail('EMF_CEM_CODEC_UNAVAILABLE', `Blockbench codec ${emfCem.EMF_CEM_AUTHORITY.cemCodecId} is required.`);
        }

        function sourcePath() {
          return savedSourcePath;
        }

        function previewHandoff(request) {
          if (!request || typeof request !== 'object' || Array.isArray(request)) {
            fail('INVALID_EMF_CEM_EXPORT_PLAN', 'Handoff request must be an object.');
          }
          const plan = emfCem.createEmfCemExportPlan({...request, profileId: 'emf_cem_entity', sourcePath: savedSourcePath});
          const document = emfCem.normalizeBlockbenchEmfCemDocument(codec.compile({raw: true}));
          emfCem.validateEmfCemJemDocument(document, {animationDialect: plan.animationDialect});
          return Object.freeze({
            plan,
            document,
            codecId: emfCem.EMF_CEM_AUTHORITY.cemCodecId,
            requiresCemTemplateLoader: true,
            requiresEmfAnimationAddon: plan.requiresEmfAnimationAddon,
            runtimeEvidence: 'UNPROVEN',
            runtimeValidated: false,
            f4I6Evidence: false,
          });
        }

        return Object.freeze({sourcePath, previewHandoff});
      }

      module.exports = {
        createBlockbenchEmfCemAdapter,
      };
    },
    "blockbench-plugin/animated_java_adapter.js": function(module, exports, require) {
      'use strict';

      const animatedJava = require('../core/provider-adapter/animated_java_adapter.js');

      function fail(code, message) {
        throw new animatedJava.AnimatedJavaContractError(code, message);
      }

      function createBlockbenchAnimatedJavaAdapter(bb) {
        if (!bb || typeof bb !== 'object') {
          fail('ANIMATED_JAVA_BLOCKBENCH_UNAVAILABLE', 'Blockbench API object is required.');
        }
        if (bb.Blockbench?.isMobile === true || bb.Blockbench?.isWeb === true) {
          fail('ANIMATED_JAVA_DESKTOP_REQUIRED', 'Animated Java 1.10.2 is audited as a desktop Blockbench extension.');
        }

        const project = bb.Project ?? bb.Blockbench?.Project;
        if (!project || typeof project !== 'object') {
          fail('ANIMATED_JAVA_BLOCKBENCH_UNAVAILABLE', 'No active Blockbench project is available.');
        }
        if (project.format?.id !== animatedJava.ANIMATED_JAVA_AUTHORITY.blueprintFormatId) {
          fail(
            'ANIMATED_JAVA_BLUEPRINT_FORMAT_REQUIRED',
            `Active Blockbench project format must be ${animatedJava.ANIMATED_JAVA_AUTHORITY.blueprintFormatId}.`,
          );
        }

        const settings = project.animated_java;
        if (!settings || typeof settings !== 'object' || Array.isArray(settings)) {
          fail('ANIMATED_JAVA_SETTINGS_UNAVAILABLE', 'Active Blueprint project does not expose Animated Java settings.');
        }

        function previewHandoff() {
          const plan = animatedJava.createAnimatedJavaExportPlan({
            sourcePath: project.save_path,
            blueprintId: settings.blueprint_id,
            targetMinecraftVersion: settings.target_minecraft_version,
            resourcePackExportMode: settings.resource_pack_export_mode,
            dataPackExportMode: settings.data_pack_export_mode,
            resourcePackPath: settings.resource_pack,
            dataPackPath: settings.data_pack,
            enablePluginMode: settings.enable_plugin_mode === true,
          });

          return Object.freeze({
            ...plan,
            sourceFormatId: animatedJava.ANIMATED_JAVA_AUTHORITY.blueprintFormatId,
            sourceCodecId: animatedJava.ANIMATED_JAVA_AUTHORITY.blueprintCodecId,
          });
        }

        return Object.freeze({previewHandoff});
      }

      module.exports = {
        createBlockbenchAnimatedJavaAdapter,
      };
    },
    "blockbench-plugin/plugin_adapter.js": function(module, exports, require) {
      'use strict';

      const core = require('../core/index.js');
      const modeling = require('./modeling_adapter.js');
      const uvTexture = require('./uv_texture_adapter.js');
      const animation = require('./animation_adapter.js');
      const geckolib4 = require('./geckolib4_adapter.js');
      const azurelib3 = require('./azurelib3_adapter.js');
      const neoforgeNativeAnimation = require('./neoforge_native_animation_adapter.js');
      const easyModelEntities = require('./easy_model_entities_adapter.js');
      const emfCem = require('./emf_cem_adapter.js');
      const animatedJava = require('./animated_java_adapter.js');

      function registerBlockbenchPlugin(bb) {
        let auditAction = null;
        let profileAction = null;
        let modelingMutationAction = null;
        let uvTextureMutationAction = null;
        let animationMutationAction = null;
        let bridgeConnectAction = null;
        let bridgeDisconnectAction = null;
        let bridgeStatusAction = null;
        let bridgeRuntime = null;

        function show(result) {
          bb.Blockbench.showMessageBox({
            title: 'Minecraft Mod Factory Asset Toolkit',
            icon: result.errors.length ? 'error' : 'check_circle',
            message: core.formatReport(result),
            buttons: ['OK'],
          });
        }

        function showError(title, error) {
          const code = error && typeof error.code === 'string' ? error.code : 'TOOLKIT_ERROR';
          const detail = error && typeof error.message === 'string' ? error.message : String(error);
          bb.Blockbench.showMessageBox({
            title,
            icon: 'error',
            message: `${code}: ${detail}`.slice(0, 2048),
            buttons: ['OK'],
          });
        }

        function showBridgeError(error) {
          showError('Minecraft Mod Factory Asset Toolkit — Live Bridge', error);
        }

        function addToolAction(action) {
          bb.MenuBar.menus.tools.addAction(action);
          return action;
        }

        bb.Plugin.register('rpg_asset_toolkit', {
          title: 'Minecraft Mod Factory Asset Toolkit',
          author: 'Gustavaopere',
          description: 'Structural/provider-aware asset QA with bounded local modeling/rig, UV/texture, and generic animation mutations plus an optional authenticated read-only desktop-local MCP Live Bridge.',
          icon: 'fact_check',
          version: '0.6.0',
          min_version: '5.1.6',
          variant: 'both',
          tags: ['Minecraft: Java Edition'],
          onload() {
            auditAction = addToolAction(new bb.Action('rpg_asset_toolkit_validate', {
              name: 'Validate RPG Asset',
              description: 'Run read-only structural checks on the active Blockbench project.',
              icon: 'fact_check',
              click() { show(core.validateProject(bb.Blockbench.Project, {})); },
            }));
            profileAction = addToolAction(new bb.Action('rpg_asset_toolkit_validate_profile', {
              name: 'Validate RPG Asset Against Contract Profile',
              description: 'Run the same checks plus optional required bones/animations/maxSpan from JSON.',
              icon: 'rule',
              click() {
                bb.Blockbench.textPrompt('RPG Asset Contract Profile (JSON)', '{}', (text) => {
                  try { show(core.validateProject(bb.Blockbench.Project, core.parseProfileJson(text))); }
                  catch (error) { showError('Minecraft Mod Factory Asset Toolkit — Invalid Profile', error); }
                });
              },
            }));

            if (bb.Blockbench.isWeb === false) {
              modelingMutationAction = addToolAction(new bb.Action('rpg_asset_toolkit_modeling_mutation_batch', {
                name: 'Apply RPG Modeling/Rig Batch',
                description: 'Apply a bounded declarative modeling/rig batch locally with expected-revision checks, preflight, Undo, and rollback. This does not expose remote MCP writes.',
                icon: 'architecture',
                click() {
                  try {
                    const adapter = modeling.createBlockbenchModelingAdapter(bb);
                    const template = JSON.stringify({
                      expectedRevision: adapter.getRevision(),
                      dryRun: true,
                      label: 'Minecraft Mod Factory Asset Toolkit Modeling/Rig Batch',
                      operations: [],
                    }, null, 2);
                    bb.Blockbench.textPrompt('RPG Modeling/Rig Mutation Batch (JSON)', template, (text) => {
                      try {
                        const result = core.applyMutationBatch(adapter, JSON.parse(text));
                        bb.Blockbench.showMessageBox({
                          title: 'Minecraft Mod Factory Asset Toolkit — Modeling/Rig Batch',
                          icon: 'check_circle',
                          message: JSON.stringify(result, null, 2).slice(0, 4096),
                          buttons: ['OK'],
                        });
                      } catch (error) {
                        showError('Minecraft Mod Factory Asset Toolkit — Modeling/Rig Batch Failed', error);
                      }
                    });
                  } catch (error) {
                    showError('Minecraft Mod Factory Asset Toolkit — Modeling/Rig Batch Unavailable', error);
                  }
                },
              }));

              uvTextureMutationAction = addToolAction(new bb.Action('rpg_asset_toolkit_uv_texture_batch', {
                name: 'Apply RPG UV/Texture Batch',
                description: 'Apply bounded declarative UV and deterministic texture-pixel mutations locally with expected-revision checks, dry-run preflight, bitmap-aware Undo, and rollback. This does not expose remote MCP writes.',
                icon: 'texture',
                click() {
                  try {
                    const adapter = uvTexture.createBlockbenchUvTextureAdapter(bb);
                    const template = JSON.stringify({
                      expectedRevision: adapter.getRevision(),
                      dryRun: true,
                      label: 'Minecraft Mod Factory Asset Toolkit UV/Texture Batch',
                      operations: [],
                    }, null, 2);
                    bb.Blockbench.textPrompt('RPG UV/Texture Mutation Batch (JSON)', template, (text) => {
                      try {
                        const result = core.applyUvTextureBatch(adapter, JSON.parse(text));
                        bb.Blockbench.showMessageBox({
                          title: 'Minecraft Mod Factory Asset Toolkit — UV/Texture Batch',
                          icon: 'check_circle',
                          message: JSON.stringify(result, null, 2).slice(0, 4096),
                          buttons: ['OK'],
                        });
                      } catch (error) {
                        showError('Minecraft Mod Factory Asset Toolkit — UV/Texture Batch Failed', error);
                      }
                    });
                  } catch (error) {
                    showError('Minecraft Mod Factory Asset Toolkit — UV/Texture Batch Unavailable', error);
                  }
                },
              }));

              animationMutationAction = addToolAction(new bb.Action('rpg_asset_toolkit_animation_batch', {
                name: 'Apply RPG Generic Animation Batch',
                description: 'Apply bounded provider-neutral animation/keyframe mutations locally with expected-revision checks, preflight, Undo, and rollback. Provider-specific effect-marker serialization remains unavailable here and remote MCP stays read-only.',
                icon: 'animation',
                click() {
                  try {
                    const adapter = animation.createBlockbenchAnimationAdapter(bb);
                    const template = JSON.stringify({
                      expectedRevision: adapter.getRevision(),
                      dryRun: true,
                      label: 'Minecraft Mod Factory Asset Toolkit Generic Animation Batch',
                      operations: [],
                    }, null, 2);
                    bb.Blockbench.textPrompt('RPG Generic Animation Mutation Batch (JSON)', template, (text) => {
                      try {
                        const result = core.applyAnimationBatch(adapter, JSON.parse(text));
                        bb.Blockbench.showMessageBox({
                          title: 'Minecraft Mod Factory Asset Toolkit — Generic Animation Batch',
                          icon: 'check_circle',
                          message: JSON.stringify(result, null, 2).slice(0, 4096),
                          buttons: ['OK'],
                        });
                      } catch (error) {
                        showError('Minecraft Mod Factory Asset Toolkit — Generic Animation Batch Failed', error);
                      }
                    });
                  } catch (error) {
                    showError('Minecraft Mod Factory Asset Toolkit — Generic Animation Batch Unavailable', error);
                  }
                },
              }));

              bridgeConnectAction = addToolAction(new bb.Action('rpg_asset_toolkit_live_bridge_connect', {
                name: 'Connect Minecraft Mod Factory Asset MCP (Read-only)',
                description: 'Connect this desktop Blockbench session to the authenticated numeric-loopback Minecraft Mod Factory Asset MCP sidecar.',
                icon: 'link',
                click() {
                  bb.Blockbench.textPrompt('Minecraft Mod Factory Asset MCP Connection Descriptor (JSON)', '{}', async (text) => {
                    try {
                      if (bridgeRuntime) await bridgeRuntime.connection.disconnect();
                      const liveBridge = require('./live_bridge_adapter.js');
                      const runtime = liveBridge.createBlockbenchLiveBridgeRuntime(bb, text);
                      await runtime.connection.connect();
                      bridgeRuntime = runtime;
                      bb.Blockbench.showQuickMessage?.('Minecraft Mod Factory Asset MCP read-only bridge connected', 2500);
                    } catch (error) {
                      bridgeRuntime = null;
                      showBridgeError(error);
                    }
                  });
                },
              }));

              bridgeDisconnectAction = addToolAction(new bb.Action('rpg_asset_toolkit_live_bridge_disconnect', {
                name: 'Disconnect Minecraft Mod Factory Asset MCP',
                description: 'Disconnect the current read-only local bridge session.',
                icon: 'link_off',
                async click() {
                  try {
                    if (bridgeRuntime) await bridgeRuntime.connection.disconnect();
                    bridgeRuntime = null;
                    bb.Blockbench.showQuickMessage?.('Minecraft Mod Factory Asset MCP bridge disconnected', 2000);
                  } catch (error) {
                    bridgeRuntime = null;
                    showBridgeError(error);
                  }
                },
              }));

              bridgeStatusAction = addToolAction(new bb.Action('rpg_asset_toolkit_live_bridge_status', {
                name: 'Minecraft Mod Factory Asset MCP Bridge Status',
                description: 'Show non-secret connection state for the local read-only bridge.',
                icon: 'info',
                click() {
                  const status = bridgeRuntime ? bridgeRuntime.connection.status() : {connected: false, generation: 0, capabilities: []};
                  bb.Blockbench.showMessageBox({
                    title: 'Minecraft Mod Factory Asset Toolkit — Live Bridge Status',
                    icon: status.connected ? 'check_circle' : 'info',
                    message: JSON.stringify(status, null, 2),
                    buttons: ['OK'],
                  });
                },
              }));
            }
          },
          onunload() {
            if (bridgeRuntime) {
              try { void bridgeRuntime.connection.disconnect(); } catch (_) { /* best effort during plugin unload */ }
            }
            bridgeRuntime = null;
            for (const action of [
              auditAction,
              profileAction,
              modelingMutationAction,
              uvTextureMutationAction,
              animationMutationAction,
              bridgeConnectAction,
              bridgeDisconnectAction,
              bridgeStatusAction,
            ]) {
              if (action) action.delete();
            }
            auditAction = null;
            profileAction = null;
            modelingMutationAction = null;
            uvTextureMutationAction = null;
            animationMutationAction = null;
            bridgeConnectAction = null;
            bridgeDisconnectAction = null;
            bridgeStatusAction = null;
          },
        });
      }

      module.exports = {
        registerBlockbenchPlugin,
        createBlockbenchModelingAdapter: modeling.createBlockbenchModelingAdapter,
        createBlockbenchUvTextureAdapter: uvTexture.createBlockbenchUvTextureAdapter,
        createBlockbenchAnimationAdapter: animation.createBlockbenchAnimationAdapter,
        createBlockbenchGeckoLib4Adapter: geckolib4.createBlockbenchGeckoLib4Adapter,
        createBlockbenchAzureLib3Adapter: azurelib3.createBlockbenchAzureLib3Adapter,
        createBlockbenchNeoForgeNativeAnimationAdapter: neoforgeNativeAnimation.createBlockbenchNeoForgeNativeAnimationAdapter,
        createBlockbenchEasyModelEntitiesAdapter: easyModelEntities.createBlockbenchEasyModelEntitiesAdapter,
        createBlockbenchEmfCemAdapter: emfCem.createBlockbenchEmfCemAdapter,
        createBlockbenchAnimatedJavaAdapter: animatedJava.createBlockbenchAnimatedJavaAdapter,
      };
    }
  };
  const cache = Object.create(null);

  function normalizeModuleId(value) {
    const output = [];
    for (const segment of value.split('/')) {
      if (!segment || segment === '.') continue;
      if (segment === '..') {
        if (!output.length) throw new Error('Minecraft Mod Factory Asset Toolkit module path escaped bundle root.');
        output.pop();
      } else output.push(segment);
    }
    return output.join('/');
  }

  function resolveModuleId(fromId, request) {
    const base = fromId.split('/');
    base.pop();
    const resolved = normalizeModuleId(base.concat(request.split('/')).join('/'));
    return resolved.endsWith('.js') ? resolved : resolved + '.js';
  }

  function moduleRequire(fromId, request) {
    if (typeof request !== 'string') throw new Error('Minecraft Mod Factory Asset Toolkit bundle requires a string module id.');
    if (request.startsWith('.')) return loadModule(resolveModuleId(fromId, request));
    if (!nativeModuleAllowlist.has(request)) throw new Error('Minecraft Mod Factory Asset Toolkit bundle forbids native module: ' + request);
    if (typeof nativeRequire !== 'function') throw new Error('Minecraft Mod Factory Asset Toolkit native module is unavailable in this Blockbench variant: ' + request);
    return nativeRequire(request);
  }

  function loadModule(id) {
    if (cache[id]) return cache[id].exports;
    const factory = modules[id];
    if (!factory) throw new Error('Minecraft Mod Factory Asset Toolkit bundle module not found: ' + id);
    const module = {exports: {}};
    cache[id] = module;
    factory(module, module.exports, (request) => moduleRequire(id, request));
    return module.exports;
  }

  const core = loadModule('core/index.js');
  const protocol = loadModule('live-bridge/protocol.js');
  const bridgeClient = loadModule('live-bridge/blockbench_bridge_client.js');
  const blockbenchPlugin = loadModule('blockbench-plugin/plugin_adapter.js');
  return Object.assign({}, core, protocol, bridgeClient, blockbenchPlugin);
});
