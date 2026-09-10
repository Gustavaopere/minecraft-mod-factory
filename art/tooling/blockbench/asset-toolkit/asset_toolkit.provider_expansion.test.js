const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const extensions = require('./core/extension-registry/extension_registry.js');
const providers = require('./core/provider-profile/provider_profiles.js');
const physical = require('./core/provider-profile/physical_provider_snapshot.js');

test('current official Blockbench catalog pins audited provider extensions', () => {
  assert.equal(extensions.getExtensionDefinition('azurelib_utils')?.pluginVersion, '2.1.5');

  const cem = extensions.getExtensionDefinition('cem_template_loader');
  assert.equal(cem?.pluginVersion, '9.2.0');
  assert.equal(cem?.classification, 'REQUIRED_PROFILE');

  const emf = extensions.getExtensionDefinition('emf_animation_addon');
  assert.equal(emf?.pluginVersion, '1.0.5');
  assert.equal(emf?.classification, 'PREFERRED');

  const animatedJava = extensions.getExtensionDefinition('animated_java');
  assert.equal(animatedJava?.pluginVersion, '1.10.2');
  assert.equal(animatedJava?.classification, 'OPTIONAL');
});

test('physical provider snapshot includes current Entity Model Features authority', () => {
  assert.deepEqual(physical.CURRENT_PHYSICAL_PROVIDER_SNAPSHOT.entity_model_features, {
    modId: 'entity_model_features', version: '3.3.5', presence: 'PRESENT', health: 'UNPROVEN',
  });
});

test('EMF/CEM and Animated Java profiles are capability-bearing and not placeholder stubs', () => {
  for (const profileId of ['emf_cem_entity', 'animated_java_display_entities']) {
    const profile = providers.getProviderProfile(profileId);
    assert.ok(profile, `missing ${profileId}`);
    assert.ok(profile.capabilities.length > 0, `${profileId} has no capabilities`);
    assert.ok(profile.authority.length > 0, `${profileId} has no authority`);
  }
});

test('EMF/CEM requires physical EMF 3.3.5 plus the current CEM Template Loader but not the preferred addon', () => {
  const base = {
    blockbenchVersion: '5.1.6',
    physicalProviders: {
      entity_model_features: {modId: 'entity_model_features', version: '3.3.5', presence: 'PRESENT', health: 'UNPROVEN'},
    },
    installedExtensions: [{pluginId: 'cem_template_loader', pluginVersion: '9.2.0'}],
    mcpAuthorizedExtensionIds: ['cem_template_loader'],
  };

  assert.equal(providers.resolveProviderProfile('emf_cem_entity', base).status, 'AVAILABLE');

  const absentProvider = providers.resolveProviderProfile('emf_cem_entity', {
    ...base,
    physicalProviders: {},
  });
  assert.equal(absentProvider.status, 'UNAVAILABLE');
  assert.ok(absentProvider.reasons.includes('PROVIDER_ABSENT'));

  const missingCem = providers.resolveProviderProfile('emf_cem_entity', {
    ...base,
    installedExtensions: [],
    mcpAuthorizedExtensionIds: [],
  });
  assert.equal(missingCem.status, 'UNAVAILABLE');
  assert.ok(missingCem.reasons.includes('REQUIRED_EXTENSION_UNAVAILABLE'));
});

test('Animated Java profile is editor-extension-authoritative and does not invent a physical runtime mod', () => {
  const profile = providers.getProviderProfile('animated_java_display_entities');
  assert.equal(profile.requiredProvider, null);

  const available = providers.resolveProviderProfile('animated_java_display_entities', {
    blockbenchVersion: '5.1.6',
    physicalProviders: {},
    installedExtensions: [{pluginId: 'animated_java', pluginVersion: '1.10.2'}],
    mcpAuthorizedExtensionIds: ['animated_java'],
  });
  assert.equal(available.status, 'AVAILABLE', available.reasons.join(', '));
});

test('new provider families remain non-convertible without an explicit audited adapter', () => {
  for (const [source, target] of [
    ['geckolib4_entity', 'emf_cem_entity'],
    ['emf_cem_entity', 'animated_java_display_entities'],
    ['animated_java_display_entities', 'azurelib_entity'],
  ]) {
    assert.equal(providers.canConvertProfile(source, target), false, `${source} -> ${target}`);
  }
});

test('canonical extension and provider policy documents are present', () => {
  const standards = path.resolve(__dirname, '../../../standards');
  for (const name of ['BLOCKBENCH-EXTENSION-POLICY.md', 'ASSET-PROVIDER-PROFILES.md']) {
    assert.equal(fs.existsSync(path.join(standards, name)), true, `missing standards/${name}`);
  }
});
