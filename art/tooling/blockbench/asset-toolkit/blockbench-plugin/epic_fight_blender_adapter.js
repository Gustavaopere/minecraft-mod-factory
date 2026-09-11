'use strict';

const epicFight = require('../core/provider-adapter/epic_fight_blender_adapter.js');

function fail(code, message) {
  throw new epicFight.EpicFightDccContractError(code, message);
}

function createBlockbenchEpicFightReferenceHandoffAdapter(bb) {
  if (!bb || typeof bb !== 'object') fail('EPIC_FIGHT_BLOCKBENCH_UNAVAILABLE', 'Blockbench bridge object is required.');
  const project = bb.Project || (bb.Blockbench && bb.Blockbench.Project);
  if (!project || typeof project !== 'object') fail('EPIC_FIGHT_BLOCKBENCH_PROJECT_REQUIRED', 'Active Blockbench project is required.');
  if (typeof project.save_path !== 'string' || project.save_path.length === 0) {
    fail('EPIC_FIGHT_SOURCE_REFERENCE_REQUIRED', 'Save the Blockbench reference project before creating the Epic Fight handoff.');
  }
  if (!project.save_path.toLowerCase().endsWith(epicFight.EPIC_FIGHT_DCC_AUTHORITY.blockbenchReferenceExtension)) {
    fail('EPIC_FIGHT_SOURCE_REFERENCE_REQUIRED', 'Epic Fight Blockbench reference project must remain a .bbmodel file.');
  }

  function createHandoff(input = {}) {
    return epicFight.createEpicFightBlenderHandoffManifest({
      ...input,
      sourceReferencePath: project.save_path,
    });
  }

  return Object.freeze({createHandoff});
}

module.exports = {createBlockbenchEpicFightReferenceHandoffAdapter};
