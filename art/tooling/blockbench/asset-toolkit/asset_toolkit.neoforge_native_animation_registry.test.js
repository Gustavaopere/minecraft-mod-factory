'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const extensions = require('./core/extension-registry/extension_registry.js');
const providers = require('./core/provider-profile/provider_profiles.js');

test('PR8 records the upstream Animation to JSON plugin as audit-required interop, not runtime authority', () => {
  const definition = extensions.getExtensionDefinition('animation_to_json');
  assert.ok(definition, 'missing animation_to_json extension definition');
  assert.equal(definition.pluginVersion, '1.0.1');
  assert.equal(definition.classification, 'AUDIT_REQUIRED');
  assert.equal(definition.mcpPolicy, 'NEVER');
  assert.equal(definition.providerFamily, 'neoforge_native_animation');
});

test('PR8 exposes a native NeoForge entity-animation profile without inventing a physical provider dependency', () => {
  const profile = providers.getProviderProfile('neoforge_native_entity_animation');
  assert.ok(profile, 'missing neoforge_native_entity_animation profile');
  assert.equal(profile.family, 'neoforge_native_animation');
  assert.equal(profile.assetKind, 'entity_animation');
  assert.equal(profile.requiredProvider, null);
  assert.deepEqual(profile.requiredExtensions, []);
  assert.ok(profile.capabilities.includes('native_json_entity_animation'));
  assert.ok(profile.capabilities.includes('animation_definition_runtime'));
  assert.ok(profile.capabilities.includes('json_export_handoff'));
});

test('PR8 native profile resolves without external runtime mod or Blockbench plugin prerequisites', () => {
  const result = providers.resolveProviderProfile('neoforge_native_entity_animation', {
    blockbenchVersion: '5.1.6',
    physicalProviders: {},
    installedExtensions: [],
    mcpAuthorizedExtensionIds: [],
  });
  assert.equal(result.status, 'AVAILABLE', result.reasons.join(', '));
});

test('PR8 does not silently convert GeckoLib or AzureLib assets into NeoForge native animations', () => {
  assert.equal(providers.canConvertProfile('geckolib4_entity', 'neoforge_native_entity_animation'), false);
  assert.equal(providers.canConvertProfile('azurelib_entity', 'neoforge_native_entity_animation'), false);
  assert.equal(providers.canConvertProfile('neoforge_native_entity_animation', 'geckolib4_entity'), false);
});
