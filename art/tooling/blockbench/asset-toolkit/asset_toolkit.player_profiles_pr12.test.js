'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');

const core = require('./core/index.js');
const blockbenchPlugin = require('./blockbench-plugin/plugin_adapter.js');
const standalone = require('./asset_toolkit.js');

const CPM_PROFILE = 'cpm_player_model';
const PAL_PROFILE = 'player_animation_library_player';
const PLAYER_ANIMATOR_PROFILE = 'player_animator_player';

test('PR12 physical snapshot pins the three player-profile runtime authorities exactly', () => {
  const snapshot = core.CURRENT_PHYSICAL_PROVIDER_SNAPSHOT;
  assert.deepEqual(snapshot.cpm, {
    modId: 'cpm', version: '0.6.27a', presence: 'PRESENT', health: 'UNPROVEN',
  });
  assert.deepEqual(snapshot.player_animation_library, {
    modId: 'player_animation_library', version: '1.1.6+mc.1.21.1', presence: 'PRESENT', health: 'UNPROVEN',
  });
  assert.deepEqual(snapshot.playeranimator, {
    modId: 'playeranimator', version: '2.0.4+1.21.1', presence: 'PRESENT', health: 'UNPROVEN',
  });
});

test('PR12 registers three separate provider profiles with no implicit PAL to Player Animator conversion', () => {
  const cpm = core.getProviderProfile(CPM_PROFILE);
  const pal = core.getProviderProfile(PAL_PROFILE);
  const playerAnimator = core.getProviderProfile(PLAYER_ANIMATOR_PROFILE);

  assert.equal(cpm?.family, 'cpm');
  assert.equal(cpm?.requiredProvider?.modId, 'cpm');
  assert.deepEqual(cpm?.requiredProvider?.exactVersions, ['0.6.27a']);
  assert.deepEqual(cpm?.requiredExtensions, ['cpm_plugin']);
  for (const capability of ['model', 'rig', 'animation', 'cpmproject_source', 'cpmproject_import_export', 'human_confirm_round_trip']) {
    assert.ok(cpm?.capabilities.includes(capability), `missing CPM capability ${capability}`);
  }

  assert.equal(pal?.family, 'player_animation_library');
  assert.equal(pal?.requiredProvider?.modId, 'player_animation_library');
  assert.deepEqual(pal?.requiredProvider?.exactVersions, ['1.1.6+mc.1.21.1']);
  assert.deepEqual(pal?.requiredExtensions, []);
  for (const capability of ['player_animation', 'json_animation_handoff', 'resource_pack_handoff', 'runtime_consumer']) {
    assert.ok(pal?.capabilities.includes(capability), `missing PAL capability ${capability}`);
  }

  assert.equal(playerAnimator?.family, 'player_animator');
  assert.equal(playerAnimator?.requiredProvider?.modId, 'playeranimator');
  assert.deepEqual(playerAnimator?.requiredProvider?.exactVersions, ['2.0.4+1.21.1']);
  assert.deepEqual(playerAnimator?.requiredExtensions, []);
  for (const capability of ['player_animation', 'api_integration', 'animation_stack', 'factory_registration', 'registry_lookup']) {
    assert.ok(playerAnimator?.capabilities.includes(capability), `missing Player Animator capability ${capability}`);
  }

  assert.equal(core.canConvertProfile(PAL_PROFILE, PLAYER_ANIMATOR_PROFILE), false);
  assert.equal(core.canConvertProfile(PLAYER_ANIMATOR_PROFILE, PAL_PROFILE), false);
});

test('PR12 classifies the CPM Blockbench plugin as beta human-confirm only', () => {
  const extension = core.getExtensionDefinition('cpm_plugin');
  assert.equal(extension?.pluginId, 'cpm_plugin');
  assert.equal(extension?.title, 'Customizable Player Models Plugin');
  assert.equal(extension?.pluginVersion, '0.6.27a');
  assert.equal(extension?.classification, 'HUMAN_ONLY');
  assert.equal(extension?.blockbenchCompatibility?.minInclusive, '5.0.0');
  assert.equal(extension?.mcpPolicy, 'NEVER');
  assert.equal(extension?.providerFamily, 'cpm');

  const evaluation = core.evaluateExtension(extension, {
    blockbenchVersion: '5.1.6',
    installedExtensions: [{pluginId: 'cpm_plugin', pluginVersion: '0.6.27a'}],
    mcpAuthorizedExtensionIds: ['cpm_plugin'],
  });
  assert.equal(evaluation.mcpAllowed, false);
  assert.ok(evaluation.reasons.includes('CLASSIFICATION_BLOCKS_MCP'));
});

test('PR12 exposes audited CPM, PAL, and Player Animator authorities', () => {
  const authority = core.PLAYER_PROFILE_AUTHORITIES;
  assert.equal(authority?.minecraftVersion, '1.21.1');

  assert.equal(authority?.cpm?.runtimeVersion, '0.6.27a');
  assert.equal(authority?.cpm?.sourceRepository, 'tom5454/CustomPlayerModels');
  assert.equal(authority?.cpm?.releaseMarkerRef, '9dcde8fb511ed0b8be5558defb1a577ce013600b');
  assert.equal(authority?.cpm?.blockbenchAuditRef, '9272f4f9c36a2bbd6986e6da65bf7091369cb12b');
  assert.equal(authority?.cpm?.pluginId, 'cpm_plugin');
  assert.equal(authority?.cpm?.sourceExtension, '.cpmproject');
  assert.equal(authority?.cpm?.pluginBeta, true);
  assert.equal(authority?.cpm?.humanConfirmationRequired, true);
  assert.equal(authority?.cpm?.automatedLosslessRoundTripProven, false);

  assert.equal(authority?.pal?.runtimeVersion, '1.1.6+mc.1.21.1');
  assert.equal(authority?.pal?.sourceRepository, 'PlayerAnimationLibrary/PlayerAnimationLibrary');
  assert.equal(authority?.pal?.sourceRef, '10e019f89fa25d0cd6f50fb8768586a969106911');
  assert.equal(authority?.pal?.resourceDirectory, 'player_animations');
  assert.equal(authority?.pal?.sourceExtension, '.json');
  assert.equal(authority?.pal?.runtimeSourceNeoForgeVersion, '21.1.230');

  assert.equal(authority?.playerAnimator?.runtimeVersion, '2.0.4+1.21.1');
  assert.equal(authority?.playerAnimator?.sourceRepository, 'KosmX/minecraftPlayerAnimator');
  assert.equal(authority?.playerAnimator?.sourceRef, 'cb3227efc19ec46065597332ae265076d0f2b495');
  assert.equal(authority?.playerAnimator?.resourceDirectory, 'player_animations');
  assert.equal(authority?.playerAnimator?.legacyResourceDirectory, 'player_animation');
  assert.deepEqual(authority?.playerAnimator?.defaultCodecs, ['emotecraft', 'gecko_legacy']);
  assert.equal(authority?.playerAnimator?.runtimeSourceNeoForgeVersion, '21.1.89');
  assert.equal(authority?.playerAnimator?.runtimeSide, 'BOTH');
  assert.equal(authority?.playerAnimator?.resourceRegistrySide, 'CLIENT');
  assert.equal(authority?.playerAnimator?.clientOnly, undefined);
});

test('PR12 CPM handoff preserves .cpmproject and never claims automated lossless round-trip', () => {
  assert.equal(typeof core.createCpmProjectRoundTripPlan, 'function');
  const plan = core.createCpmProjectRoundTripPlan({
    sourcePath: '/workspace/player.cpmproject',
    targetMinecraftVersion: '1.21.1',
  });
  assert.equal(plan.sourcePath, '/workspace/player.cpmproject');
  assert.equal(plan.preserveSource, true);
  assert.equal(plan.humanConfirmationRequired, true);
  assert.equal(plan.automatedLosslessRoundTripProven, false);
  assert.equal(plan.implicitProviderConversion, false);
  assert.equal(plan.runtimeEvidence, 'UNPROVEN');
  assert.equal(plan.runtimeValidated, false);
  assert.equal(plan.f4I6Evidence, false);

  assert.throws(
    () => core.createCpmProjectRoundTripPlan({sourcePath: '/workspace/player.bbmodel', targetMinecraftVersion: '1.21.1'}),
    error => error?.code === 'CPM_SOURCE_MUST_BE_CPMPROJECT',
  );
});

test('PR12 PAL handoff stages JSON only under the proven resource-pack root', () => {
  assert.equal(typeof core.createPlayerAnimationLibraryHandoff, 'function');
  const handoff = core.createPlayerAnimationLibraryHandoff({
    namespace: 'factory',
    sourcePath: '/workspace/player.animation.json',
  });
  assert.equal(handoff.sourcePath, '/workspace/player.animation.json');
  assert.equal(handoff.targetPath, 'assets/factory/player_animations/player.animation.json');
  assert.equal(handoff.resourceDirectory, 'player_animations');
  assert.equal(handoff.runtimeKeySource, 'internal_animation_id');
  assert.equal(handoff.preserveSource, true);
  assert.equal(handoff.implicitProviderConversion, false);
  assert.equal(handoff.runtimeEvidence, 'UNPROVEN');
  assert.equal(handoff.runtimeValidated, false);
  assert.equal(handoff.f4I6Evidence, false);
});

test('PR12 Player Animator profile records provider side and client registry scope without pretending PAL equivalence', () => {
  assert.equal(typeof core.getPlayerAnimatorApiAudit, 'function');
  const audit = core.getPlayerAnimatorApiAudit();
  assert.equal(audit.clientOnly, undefined);
  assert.equal(audit.runtimeSide, 'BOTH');
  assert.equal(audit.resourceRegistrySide, 'CLIENT');
  assert.deepEqual(audit.primaryApiClasses, [
    'PlayerAnimationAccess',
    'PlayerAnimationFactory',
    'PlayerAnimationRegistry',
  ]);
  assert.ok(audit.layeredApiClasses.includes('AnimationStack'));
  assert.ok(audit.layeredApiClasses.includes('ModifierLayer'));
  assert.deepEqual(audit.defaultCodecs, ['emotecraft', 'gecko_legacy']);
  assert.equal(audit.resourceDirectory, 'player_animations');
  assert.equal(audit.legacyResourceDirectory, 'player_animation');
  assert.equal(audit.palEquivalent, false);
  assert.equal(audit.automaticPalConversion, false);
  assert.equal(audit.runtimeEvidence, 'UNPROVEN');
  assert.equal(audit.runtimeValidated, false);
  assert.equal(audit.f4I6Evidence, false);
});

test('PR12 exposes the player-profile contract through core, Blockbench, and standalone without auto-installing CPM', () => {
  assert.equal(typeof blockbenchPlugin.createBlockbenchCpmPlayerProfileAdapter, 'function');
  assert.equal(typeof standalone.createBlockbenchCpmPlayerProfileAdapter, 'function');
  assert.equal(standalone.PLAYER_PROFILE_AUTHORITIES?.cpm?.pluginId, 'cpm_plugin');

  const adapter = blockbenchPlugin.createBlockbenchCpmPlayerProfileAdapter({
    Blockbench: {isWeb: false, isMobile: false},
    Project: {
      save_path: '/workspace/player.cpmproject',
      format: {id: 'cpm'},
    },
  });
  const preview = adapter.previewRoundTrip();
  assert.equal(preview.sourcePath, '/workspace/player.cpmproject');
  assert.equal(preview.humanConfirmationRequired, true);
  assert.equal(preview.automatedLosslessRoundTripProven, false);
  assert.equal(preview.runtimeEvidence, 'UNPROVEN');
  assert.equal(adapter.installExtension, undefined);

  assert.throws(
    () => blockbenchPlugin.createBlockbenchCpmPlayerProfileAdapter({
      Blockbench: {isWeb: false, isMobile: false},
      Project: {save_path: '/workspace/player.bbmodel', format: {id: 'free'}},
    }),
    error => error?.code === 'CPM_PROJECT_FORMAT_REQUIRED',
  );
});
