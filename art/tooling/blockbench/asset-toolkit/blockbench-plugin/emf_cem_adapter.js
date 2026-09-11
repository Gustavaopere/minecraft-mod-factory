'use strict';

const emfCem = require('../core/provider-adapter/emf_cem_adapter.js');

function fail(code, message) {
  throw new emfCem.EmfCemContractError(code, message);
}

function normalizedSourcePath(value) {
  if (typeof value !== 'string' || value.length === 0) {
    fail('EMF_CEM_SOURCE_NOT_SAVED', 'Active Blockbench project must be saved as a .bbmodel before EMF/CEM handoff.');
  }
  const normalized = value.replace(/\\/g, '/');
  if (!normalized.toLowerCase().endsWith('.bbmodel')) {
    fail('EMF_CEM_SOURCE_NOT_SAVED', 'Active Blockbench project source must remain a .bbmodel file.');
  }
  return normalized;
}

function createBlockbenchEmfCemAdapter(bb) {
  if (!bb || typeof bb !== 'object') {
    fail('EMF_CEM_BLOCKBENCH_UNAVAILABLE', 'Blockbench API object is required.');
  }
  const project = bb.Blockbench?.Project;
  if (!project || typeof project !== 'object') {
    fail('EMF_CEM_BLOCKBENCH_UNAVAILABLE', 'No active Blockbench project is available.');
  }
  const savedSourcePath = normalizedSourcePath(project.save_path);
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
