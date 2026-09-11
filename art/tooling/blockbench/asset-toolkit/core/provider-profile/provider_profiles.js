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
  frozenProfile({
    id: 'cpm_player_model', family: 'cpm', authority: 'Customizable Player Models 0.6.27a player model runtime', assetKind: 'player_model',
    requiredProvider: {modId: 'cpm', exactVersions: ['0.6.27a']}, requiredExtensions: ['cpm_plugin'],
    capabilities: ['model', 'rig', 'animation', 'cpmproject_source', 'cpmproject_import_export', 'human_confirm_round_trip'],
  }),
  frozenProfile({
    id: 'player_animation_library_player', family: 'player_animation_library', authority: 'Player Animation Library 1.1.6+mc.1.21.1 runtime consumer', assetKind: 'player_animation',
    requiredProvider: {modId: 'player_animation_library', exactVersions: ['1.1.6+mc.1.21.1']}, requiredExtensions: [],
    capabilities: ['player_animation', 'json_animation_handoff', 'resource_pack_handoff', 'runtime_consumer'],
  }),
  frozenProfile({
    id: 'player_animator_player', family: 'player_animator', authority: 'Player Animator 2.0.4+1.21.1 client animation API', assetKind: 'player_animation',
    requiredProvider: {modId: 'playeranimator', exactVersions: ['2.0.4+1.21.1']}, requiredExtensions: [],
    capabilities: ['player_animation', 'api_integration', 'animation_stack', 'factory_registration', 'registry_lookup'],
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
