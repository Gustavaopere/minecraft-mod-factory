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
const playerProfiles = require('./provider-adapter/player_profiles_adapter.js');
const epicFightBlender = require('./provider-adapter/epicfight_blender_adapter.js');

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
  playerProfiles,
  epicFightBlender,
);