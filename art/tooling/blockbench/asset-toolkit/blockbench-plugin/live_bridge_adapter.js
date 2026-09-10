'use strict';

const {bridgeError, PROTOCOL_VERSION} = require('../live-bridge/protocol.js');
const {createProjectSnapshot} = require('../live-bridge/project_snapshot.js');
const {buildSessionFingerprint} = require('../live-bridge/fingerprint.js');
const {createReadOnlyRouter} = require('../live-bridge/read_only_router.js');
const {createBridgeConnection} = require('../live-bridge/blockbench_bridge_client.js');

const TOOLKIT_VERSION = '0.3.0';
const DESCRIPTOR_KEYS = new Set([
  'host', 'port', 'sessionId', 'token', 'protocolVersion',
  'minecraftVersion', 'loader', 'javaVersion', 'physicalProviders',
  'activeProviderProfile', 'mcpAuthorizedExtensionIds', 'heartbeatIntervalMs',
]);

function requiredString(value, field, maxLength = 256) {
  if (typeof value !== 'string' || !value.trim() || value.length > maxLength) throw bridgeError('INVALID_CONNECTION_DESCRIPTOR', field);
  return value.trim();
}

function parseConnectionDescriptor(input) {
  let value = input;
  if (typeof input === 'string') {
    try { value = JSON.parse(input); }
    catch (_) { throw bridgeError('INVALID_CONNECTION_DESCRIPTOR', 'invalid JSON'); }
  }
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw bridgeError('INVALID_CONNECTION_DESCRIPTOR');
  for (const key of Object.keys(value)) {
    if (!DESCRIPTOR_KEYS.has(key)) throw bridgeError('INVALID_CONNECTION_DESCRIPTOR', `unknown field: ${key}`);
  }

  const descriptor = {
    host: requiredString(value.host, 'host'),
    port: value.port,
    sessionId: requiredString(value.sessionId, 'sessionId'),
    token: requiredString(value.token, 'token'),
    protocolVersion: requiredString(value.protocolVersion, 'protocolVersion'),
    minecraftVersion: requiredString(value.minecraftVersion, 'minecraftVersion'),
    loader: requiredString(value.loader, 'loader'),
    javaVersion: requiredString(value.javaVersion, 'javaVersion'),
    activeProviderProfile: requiredString(value.activeProviderProfile, 'activeProviderProfile'),
    physicalProviders: Array.isArray(value.physicalProviders) ? value.physicalProviders.map((entry) => ({...entry})) : [],
    mcpAuthorizedExtensionIds: Array.isArray(value.mcpAuthorizedExtensionIds) ? [...value.mcpAuthorizedExtensionIds] : [],
    heartbeatIntervalMs: value.heartbeatIntervalMs,
  };

  if (!Number.isInteger(descriptor.port) || descriptor.port < 1 || descriptor.port > 65535) throw bridgeError('INVALID_CONNECTION_DESCRIPTOR', 'port');
  if (!/^[0-9a-f]{32}$/i.test(descriptor.sessionId)) throw bridgeError('INVALID_CONNECTION_DESCRIPTOR', 'sessionId');
  if (!/^[0-9a-f]{64}$/i.test(descriptor.token)) throw bridgeError('INVALID_CONNECTION_DESCRIPTOR', 'token');
  if (descriptor.protocolVersion !== PROTOCOL_VERSION) throw bridgeError('PROTOCOL_MISMATCH');
  if (descriptor.physicalProviders.length > 256 || descriptor.mcpAuthorizedExtensionIds.length > 256) throw bridgeError('INVALID_CONNECTION_DESCRIPTOR', 'entry limit');

  for (const entry of descriptor.physicalProviders) {
    if (!entry || typeof entry !== 'object' || Array.isArray(entry)) throw bridgeError('INVALID_CONNECTION_DESCRIPTOR', 'physicalProviders');
    entry.modId = requiredString(entry.modId, 'physicalProviders.modId');
    entry.version = requiredString(entry.version, 'physicalProviders.version');
    if (typeof entry.presence !== 'string') entry.presence = 'PRESENT';
    if (typeof entry.health !== 'string') entry.health = 'UNPROVEN';
  }
  descriptor.mcpAuthorizedExtensionIds = descriptor.mcpAuthorizedExtensionIds.map((id) => requiredString(id, 'mcpAuthorizedExtensionIds'));
  if (descriptor.heartbeatIntervalMs !== undefined && (!Number.isFinite(descriptor.heartbeatIntervalMs) || descriptor.heartbeatIntervalMs <= 0)) {
    throw bridgeError('INVALID_CONNECTION_DESCRIPTOR', 'heartbeatIntervalMs');
  }
  return Object.freeze(descriptor);
}

function installedExtensions(bb) {
  const installations = Array.isArray(bb?.Plugins?.installed) ? bb.Plugins.installed : [];
  return installations
    .filter((entry) => entry && entry.disabled !== true && typeof entry.id === 'string' && typeof entry.version === 'string')
    .map((entry) => ({pluginId: entry.id, pluginVersion: entry.version}));
}

function physicalProviderFingerprint(entries) {
  return entries.map((entry) => ({modId: entry.modId, modVersion: entry.version}));
}

function createBlockbenchLiveBridgeRuntime(bb, descriptorInput, options = {}) {
  if (!bb || !bb.Blockbench || bb.Blockbench.isWeb === true) throw bridgeError('DESKTOP_REQUIRED');
  const descriptor = parseConnectionDescriptor(descriptorInput);
  const getProject = () => bb.Blockbench.Project || null;
  const getInstalledExtensions = () => installedExtensions(bb);
  const router = createReadOnlyRouter({
    getProject,
    getBlockbenchVersion: () => String(bb.Blockbench.version || ''),
    getInstalledExtensions,
    getMcpAuthorizedExtensionIds: () => descriptor.mcpAuthorizedExtensionIds,
    physicalProviders: descriptor.physicalProviders,
    activeProviderProfile: () => descriptor.activeProviderProfile,
  });

  const snapshot = createProjectSnapshot(getProject());
  const fingerprint = buildSessionFingerprint({
    minecraftVersion: descriptor.minecraftVersion,
    loader: descriptor.loader,
    javaVersion: descriptor.javaVersion,
    blockbenchVersion: String(bb.Blockbench.version || ''),
    toolkitVersion: TOOLKIT_VERSION,
    protocolVersion: descriptor.protocolVersion,
    installedExtensions: getInstalledExtensions(),
    physicalProviders: physicalProviderFingerprint(descriptor.physicalProviders),
    activeProviderProfile: descriptor.activeProviderProfile,
    projectFormat: snapshot.projectFormat || 'unknown',
    projectRevision: snapshot.projectRevision,
  });

  const session = Object.freeze({
    sessionId: descriptor.sessionId,
    token: descriptor.token,
    protocolVersion: descriptor.protocolVersion,
  });
  const connection = createBridgeConnection({
    WebSocketClass: options.WebSocketClass,
    host: descriptor.host,
    port: descriptor.port,
    session,
    fingerprint,
    router,
    heartbeatIntervalMs: descriptor.heartbeatIntervalMs,
  });

  return Object.freeze({descriptor, fingerprint, router, connection});
}

module.exports = {
  TOOLKIT_VERSION,
  parseConnectionDescriptor,
  installedExtensions,
  createBlockbenchLiveBridgeRuntime,
};
