'use strict';

const playerProfiles = require('../core/provider-adapter/player_profiles_adapter.js');

function fail(code, message) {
  throw new playerProfiles.PlayerProfileContractError(code, message);
}

function createBlockbenchCpmPlayerProfileAdapter(bb) {
  if (!bb || typeof bb !== 'object') {
    fail('CPM_BLOCKBENCH_UNAVAILABLE', 'Blockbench API object is required.');
  }

  const project = bb.Project ?? bb.Blockbench?.Project;
  if (!project || typeof project !== 'object') {
    fail('CPM_BLOCKBENCH_UNAVAILABLE', 'No active Blockbench project is available.');
  }
  if (project.format?.id !== playerProfiles.PLAYER_PROFILE_AUTHORITIES.cpm.formatId) {
    fail(
      'CPM_PROJECT_FORMAT_REQUIRED',
      `Active Blockbench project format must be ${playerProfiles.PLAYER_PROFILE_AUTHORITIES.cpm.formatId}.`,
    );
  }

  function previewRoundTrip() {
    return playerProfiles.createCpmProjectRoundTripPlan({
      sourcePath: project.save_path,
      targetMinecraftVersion: playerProfiles.PLAYER_PROFILE_AUTHORITIES.minecraftVersion,
    });
  }

  return Object.freeze({previewRoundTrip});
}

module.exports = {
  createBlockbenchCpmPlayerProfileAdapter,
};
