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
);
