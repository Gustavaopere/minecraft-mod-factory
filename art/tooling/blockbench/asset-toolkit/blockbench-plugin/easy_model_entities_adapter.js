'use strict';

const easyModelEntities = require('../core/provider-adapter/easy_model_entities_adapter.js');

function fail(code, message) {
  throw new easyModelEntities.EasyModelEntitiesContractError(code, message);
}

function normalizedSourcePath(value) {
  if (typeof value !== 'string' || value.length === 0) {
    fail('EASY_MODEL_ENTITIES_SOURCE_NOT_SAVED', 'Active Blockbench project must be saved as a .bbmodel before Easy Model Entities handoff.');
  }
  const normalized = value.replace(/\\/g, '/');
  if (!normalized.toLowerCase().endsWith('.bbmodel')) {
    fail('EASY_MODEL_ENTITIES_SOURCE_NOT_SAVED', 'Active Blockbench project source must remain a .bbmodel file.');
  }
  return normalized;
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
  const savedSourcePath = normalizedSourcePath(project.save_path);

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
