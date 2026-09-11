'use strict';

const epicFight = require('../core/provider-adapter/epicfight_blender_adapter.js');

function fail(code, message) {
  throw new epicFight.EpicFightBlenderContractError(code, message);
}

function createBlockbenchEpicFightHandoffAdapter(bb, options = {}) {
  if (!bb || typeof bb !== 'object') {
    fail('EPIC_FIGHT_BLOCKBENCH_UNAVAILABLE', 'Blockbench API object is required.');
  }
  if (bb.Blockbench?.isWeb === true || bb.Blockbench?.isMobile === true) {
    fail('EPIC_FIGHT_BLOCKBENCH_DESKTOP_REQUIRED', 'Epic Fight external-DCC handoff requires Blockbench Desktop.');
  }

  const project = bb.Project ?? bb.Blockbench?.Project;
  if (!project || typeof project !== 'object') {
    fail('EPIC_FIGHT_BLOCKBENCH_UNAVAILABLE', 'No active Blockbench project is available.');
  }

  function previewHandoff() {
    return epicFight.createEpicFightBlenderHandoff({
      blockbenchReferencePath: project.save_path,
      blenderSourcePath: options.blenderSourcePath,
      targetMinecraftVersion: options.targetMinecraftVersion,
    });
  }

  return Object.freeze({previewHandoff});
}

module.exports = {
  createBlockbenchEpicFightHandoffAdapter,
};
