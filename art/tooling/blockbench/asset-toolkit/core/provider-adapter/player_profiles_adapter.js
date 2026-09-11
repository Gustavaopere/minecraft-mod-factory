'use strict';

class PlayerProfileContractError extends Error {
  constructor(code, message) {
    super(message);
    this.name = 'PlayerProfileContractError';
    this.code = code;
  }
}

function fail(code, message) {
  throw new PlayerProfileContractError(code, message);
}

const PLAYER_PROFILE_AUTHORITIES = Object.freeze({
  minecraftVersion: '1.21.1',
  cpm: Object.freeze({
    runtimeVersion: '0.6.27a',
    sourceRepository: 'tom5454/CustomPlayerModels',
    releaseMarkerRef: '9dcde8fb511ed0b8be5558defb1a577ce013600b',
    blockbenchAuditRef: '9272f4f9c36a2bbd6986e6da65bf7091369cb12b',
    pluginId: 'cpm_plugin',
    sourceExtension: '.cpmproject',
    formatId: 'cpm',
    codecId: 'cpmproject',
    pluginBeta: true,
    pluginVariant: 'both',
    blockbenchMinimumVersion: '5.0.0',
    humanConfirmationRequired: true,
    automatedLosslessRoundTripProven: false,
  }),
  pal: Object.freeze({
    runtimeVersion: '1.1.6+mc.1.21.1',
    sourceRepository: 'PlayerAnimationLibrary/PlayerAnimationLibrary',
    sourceRef: '10e019f89fa25d0cd6f50fb8768586a969106911',
    resourceDirectory: 'player_animations',
    sourceExtension: '.json',
    runtimeSourceNeoForgeVersion: '21.1.230',
  }),
  playerAnimator: Object.freeze({
    runtimeVersion: '2.0.4+1.21.1',
    sourceRepository: 'KosmX/minecraftPlayerAnimator',
    sourceRef: 'cb3227efc19ec46065597332ae265076d0f2b495',
    resourceDirectory: 'player_animations',
    legacyResourceDirectory: 'player_animation',
    defaultCodecs: Object.freeze(['emotecraft', 'gecko_legacy']),
    runtimeSourceNeoForgeVersion: '21.1.89',
    runtimeSide: 'BOTH',
    resourceRegistrySide: 'CLIENT',
  }),
});

function requireExactMinecraftVersion(value, code) {
  if (value !== PLAYER_PROFILE_AUTHORITIES.minecraftVersion) {
    fail(code, `Player profile contract is audited only for Minecraft ${PLAYER_PROFILE_AUTHORITIES.minecraftVersion}.`);
  }
}

function requireNonEmptyString(value, code, label) {
  if (typeof value !== 'string' || !value.trim()) fail(code, `${label} is required.`);
  return value.trim();
}

function basename(value) {
  const normalized = value.replace(/\\/g, '/');
  return normalized.slice(normalized.lastIndexOf('/') + 1);
}

function createCpmProjectRoundTripPlan(input = {}) {
  const sourcePath = requireNonEmptyString(input.sourcePath, 'CPM_SOURCE_REQUIRED', 'CPM source path');
  if (!sourcePath.toLowerCase().endsWith(PLAYER_PROFILE_AUTHORITIES.cpm.sourceExtension)) {
    fail('CPM_SOURCE_MUST_BE_CPMPROJECT', 'CPM Blockbench handoff must preserve a saved .cpmproject source.');
  }
  requireExactMinecraftVersion(input.targetMinecraftVersion, 'CPM_TARGET_MINECRAFT_VERSION_UNSUPPORTED');

  return Object.freeze({
    sourcePath,
    sourceExtension: PLAYER_PROFILE_AUTHORITIES.cpm.sourceExtension,
    sourceFormatId: PLAYER_PROFILE_AUTHORITIES.cpm.formatId,
    sourceCodecId: PLAYER_PROFILE_AUTHORITIES.cpm.codecId,
    targetMinecraftVersion: input.targetMinecraftVersion,
    preserveSource: true,
    humanConfirmationRequired: true,
    automatedLosslessRoundTripProven: false,
    implicitProviderConversion: false,
    runtimeEvidence: 'UNPROVEN',
    runtimeValidated: false,
    f4I6Evidence: false,
  });
}

function createPlayerAnimationLibraryHandoff(input = {}) {
  const namespace = requireNonEmptyString(input.namespace, 'PAL_NAMESPACE_REQUIRED', 'PAL resource namespace');
  if (!/^[a-z0-9_.-]+$/.test(namespace)) {
    fail('PAL_NAMESPACE_INVALID', 'PAL resource namespace must satisfy Minecraft resource namespace grammar.');
  }
  const sourcePath = requireNonEmptyString(input.sourcePath, 'PAL_SOURCE_REQUIRED', 'PAL source path');
  if (!sourcePath.toLowerCase().endsWith('.json')) {
    fail('PAL_SOURCE_MUST_BE_JSON', 'PAL handoff accepts only the audited JSON resource format.');
  }
  const fileName = basename(sourcePath);
  if (!fileName || fileName === '.json') fail('PAL_SOURCE_INVALID', 'PAL source path must include a JSON filename.');

  return Object.freeze({
    sourcePath,
    targetPath: `assets/${namespace}/${PLAYER_PROFILE_AUTHORITIES.pal.resourceDirectory}/${fileName}`,
    resourceDirectory: PLAYER_PROFILE_AUTHORITIES.pal.resourceDirectory,
    runtimeKeySource: 'internal_animation_id',
    preserveSource: true,
    implicitProviderConversion: false,
    runtimeEvidence: 'UNPROVEN',
    runtimeValidated: false,
    f4I6Evidence: false,
  });
}

const PLAYER_ANIMATOR_API_AUDIT = Object.freeze({
  runtimeSide: PLAYER_PROFILE_AUTHORITIES.playerAnimator.runtimeSide,
  resourceRegistrySide: PLAYER_PROFILE_AUTHORITIES.playerAnimator.resourceRegistrySide,
  primaryApiClasses: Object.freeze([
    'PlayerAnimationAccess',
    'PlayerAnimationFactory',
    'PlayerAnimationRegistry',
  ]),
  layeredApiClasses: Object.freeze([
    'AnimationStack',
    'ModifierLayer',
    'IAnimation',
    'IActualAnimation',
    'KeyframeAnimationPlayer',
  ]),
  defaultCodecs: PLAYER_PROFILE_AUTHORITIES.playerAnimator.defaultCodecs,
  resourceDirectory: PLAYER_PROFILE_AUTHORITIES.playerAnimator.resourceDirectory,
  legacyResourceDirectory: PLAYER_PROFILE_AUTHORITIES.playerAnimator.legacyResourceDirectory,
  runtimeKeySource: 'internal_animation_name',
  palEquivalent: false,
  automaticPalConversion: false,
  runtimeEvidence: 'UNPROVEN',
  runtimeValidated: false,
  f4I6Evidence: false,
});

function getPlayerAnimatorApiAudit() {
  return PLAYER_ANIMATOR_API_AUDIT;
}

module.exports = {
  PlayerProfileContractError,
  PLAYER_PROFILE_AUTHORITIES,
  createCpmProjectRoundTripPlan,
  createPlayerAnimationLibraryHandoff,
  getPlayerAnimatorApiAudit,
};
