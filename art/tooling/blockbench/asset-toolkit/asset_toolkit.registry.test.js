const test = require('node:test');
const assert = require('node:assert/strict');

const extensions = require('./core/extension-registry/extension_registry.js');
const providers = require('./core/provider-profile/provider_profiles.js');
const physical = require('./core/provider-profile/physical_provider_snapshot.js');

const EXPECTED_EXTENSION_STATES = [
  'REQUIRED_PROFILE',
  'PREFERRED',
  'OPTIONAL',
  'EXPERIMENTAL',
  'DEV_ONLY',
  'HUMAN_ONLY',
  'AUDIT_REQUIRED',
  'BLOCKED_LEGACY',
  'INCOMPATIBLE_EDITOR',
  'LOADER_MISMATCH',
  'PROVIDER_ABSENT',
  'NOT_RUNTIME_AUTHORITY',
  'DISABLED_BY_DEFAULT',
];

test('extension registry exposes the explicit fail-closed classifications from the master plan', () => {
  assert.deepEqual([...extensions.EXTENSION_STATES].sort(), [...EXPECTED_EXTENSION_STATES].sort());
});

test('installed extension is not MCP-authorized unless the session allowlist explicitly authorizes it', () => {
  const definition = extensions.getExtensionDefinition('geckolib');
  assert.equal(definition.pluginVersion, '4.2.5');
  assert.equal(definition.classification, 'REQUIRED_PROFILE');

  const denied = extensions.evaluateExtension(definition, {
    blockbenchVersion: '5.1.6',
    installedExtensions: [{pluginId: 'geckolib', pluginVersion: '4.2.5'}],
    mcpAuthorizedExtensionIds: [],
  });
  assert.equal(denied.installed, true);
  assert.equal(denied.compatible, true);
  assert.equal(denied.mcpAllowed, false);
  assert.ok(denied.reasons.includes('NOT_MCP_AUTHORIZED'));

  const allowed = extensions.evaluateExtension(definition, {
    blockbenchVersion: '5.1.6',
    installedExtensions: [{pluginId: 'geckolib', pluginVersion: '4.2.5'}],
    mcpAuthorizedExtensionIds: ['geckolib'],
  });
  assert.equal(allowed.mcpAllowed, true);
});

test('blocked legacy and human-only extensions remain unavailable to MCP even when installed and allowlisted', () => {
  const legacy = extensions.getExtensionDefinition('animation_utils');
  const legacyResult = extensions.evaluateExtension(legacy, {
    blockbenchVersion: '5.1.6',
    installedExtensions: [{pluginId: 'animation_utils', pluginVersion: '4.1.3'}],
    mcpAuthorizedExtensionIds: ['animation_utils'],
  });
  assert.equal(legacy.classification, 'BLOCKED_LEGACY');
  assert.equal(legacyResult.mcpAllowed, false);
  assert.ok(legacyResult.reasons.includes('CLASSIFICATION_BLOCKS_MCP'));

  const humanOnly = extensions.evaluateExtension({
    pluginId: 'test_human_only',
    pluginVersion: '1.0.0',
    classification: 'HUMAN_ONLY',
    mcpPolicy: 'NEVER',
  }, {
    blockbenchVersion: '5.1.6',
    installedExtensions: [{pluginId: 'test_human_only', pluginVersion: '1.0.0'}],
    mcpAuthorizedExtensionIds: ['test_human_only'],
  });
  assert.equal(humanOnly.mcpAllowed, false);
  assert.ok(humanOnly.reasons.includes('CLASSIFICATION_BLOCKS_MCP'));
});

test('current physical provider snapshot records current VFX replacement state without treating presence as health proof', () => {
  assert.deepEqual(physical.CURRENT_PHYSICAL_PROVIDER_SNAPSHOT.geckolib, {
    modId: 'geckolib', version: '4.9.2', presence: 'PRESENT', health: 'UNPROVEN',
  });
  assert.deepEqual(physical.CURRENT_PHYSICAL_PROVIDER_SNAPSHOT.azurelib, {
    modId: 'azurelib', version: '3.1.11', presence: 'PRESENT', health: 'UNPROVEN',
  });
  assert.deepEqual(physical.CURRENT_PHYSICAL_PROVIDER_SNAPSHOT.photon, {
    modId: 'photon', version: '2.2.6.a', presence: 'PRESENT', health: 'KNOWN_RUNTIME_RISK',
  });
  assert.deepEqual(physical.CURRENT_PHYSICAL_PROVIDER_SNAPSHOT.lodestone, {
    modId: 'lodestone', version: '1.8.2', presence: 'PRESENT', health: 'UNPROVEN',
  });
  assert.deepEqual(physical.CURRENT_PHYSICAL_PROVIDER_SNAPSHOT.particle_effects, {
    modId: 'particle_effects', version: '1.5.0+1.21.1+neoforge', presence: 'PRESENT', health: 'PRESENTATION_ONLY',
  });
  assert.equal(physical.CURRENT_PHYSICAL_PROVIDER_SNAPSHOT.aaa_particles.presence, 'ABSENT');
  assert.equal(physical.CURRENT_PHYSICAL_PROVIDER_SNAPSHOT.aaa_particles_world.presence, 'ABSENT');
});

test('provider profiles are real capability-bearing profiles rather than empty count-padding stubs', () => {
  const profileIds = providers.listProviderProfiles().map((profile) => profile.id);
  for (const required of [
    'java_block_item',
    'geckolib4_entity', 'geckolib4_item', 'geckolib4_block', 'geckolib4_armor',
    'azurelib_entity', 'azurelib_item', 'azurelib_block', 'azurelib_armor',
  ]) {
    assert.ok(profileIds.includes(required), `missing capability-backed profile ${required}`);
  }
  for (const profile of providers.listProviderProfiles()) {
    assert.ok(Array.isArray(profile.capabilities) && profile.capabilities.length > 0, `${profile.id} has no capabilities`);
    assert.ok(typeof profile.authority === 'string' && profile.authority.length > 0, `${profile.id} has no authority declaration`);
  }
});

test('profile resolver fails closed for unknown, absent, wrong-version, or missing-extension providers', () => {
  assert.equal(providers.resolveProviderProfile('does_not_exist', {}).status, 'UNAVAILABLE');

  const missingProvider = providers.resolveProviderProfile('geckolib4_entity', {
    blockbenchVersion: '5.1.6',
    physicalProviders: {},
    installedExtensions: [{pluginId: 'geckolib', pluginVersion: '4.2.5'}],
    mcpAuthorizedExtensionIds: ['geckolib'],
  });
  assert.equal(missingProvider.status, 'UNAVAILABLE');
  assert.ok(missingProvider.reasons.includes('PROVIDER_ABSENT'));

  const wrongVersion = providers.resolveProviderProfile('geckolib4_entity', {
    blockbenchVersion: '5.1.6',
    physicalProviders: {geckolib: {modId: 'geckolib', version: '4.9.1', presence: 'PRESENT', health: 'UNPROVEN'}},
    installedExtensions: [{pluginId: 'geckolib', pluginVersion: '4.2.5'}],
    mcpAuthorizedExtensionIds: ['geckolib'],
  });
  assert.equal(wrongVersion.status, 'UNAVAILABLE');
  assert.ok(wrongVersion.reasons.includes('PROVIDER_VERSION_UNSUPPORTED'));

  const missingExtension = providers.resolveProviderProfile('azurelib_entity', {
    blockbenchVersion: '5.1.6',
    physicalProviders: {azurelib: {modId: 'azurelib', version: '3.1.11', presence: 'PRESENT', health: 'UNPROVEN'}},
    installedExtensions: [],
    mcpAuthorizedExtensionIds: [],
  });
  assert.equal(missingExtension.status, 'UNAVAILABLE');
  assert.ok(missingExtension.reasons.includes('REQUIRED_EXTENSION_UNAVAILABLE'));
});

test('provider resolver accepts the audited GeckoLib and AzureLib paths only with exact provider and extension evidence', () => {
  for (const [profileId, providerId, providerVersion, pluginId, pluginVersion] of [
    ['geckolib4_entity', 'geckolib', '4.9.2', 'geckolib', '4.2.5'],
    ['azurelib_entity', 'azurelib', '3.1.11', 'azurelib_utils', '2.1.5'],
  ]) {
    const result = providers.resolveProviderProfile(profileId, {
      blockbenchVersion: '5.1.6',
      physicalProviders: {[providerId]: {modId: providerId, version: providerVersion, presence: 'PRESENT', health: 'UNPROVEN'}},
      installedExtensions: [{pluginId, pluginVersion}],
      mcpAuthorizedExtensionIds: [pluginId],
    });
    assert.equal(result.status, 'AVAILABLE', `${profileId}: ${result.reasons.join(', ')}`);
  }
});

test('cross-profile conversion is denied until an explicit audited adapter exists', () => {
  assert.equal(providers.canConvertProfile('geckolib4_entity', 'azurelib_entity'), false);
  assert.equal(providers.canConvertProfile('azurelib_entity', 'geckolib4_entity'), false);
  assert.equal(providers.canConvertProfile('geckolib4_entity', 'geckolib4_item'), false);
});
