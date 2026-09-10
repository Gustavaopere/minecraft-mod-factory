'use strict';

const {bridgeError} = require('./protocol.js');

function requiredString(value, field) {
  if (typeof value !== 'string' || !value.trim() || value.length > 256) throw bridgeError('INVALID_FINGERPRINT', field);
  return value.trim();
}

function boundedEntries(entries, idKey, versionKey) {
  if (!Array.isArray(entries) || entries.length > 256) throw bridgeError('INVALID_FINGERPRINT', `${idKey} entries`);
  return entries.map((entry) => ({
    [idKey]: requiredString(entry && entry[idKey], idKey),
    [versionKey]: requiredString(entry && entry[versionKey], versionKey),
  }));
}

function buildSessionFingerprint(input = {}) {
  return Object.freeze({
    minecraft_version: requiredString(input.minecraftVersion, 'minecraft_version'),
    loader: requiredString(input.loader, 'loader'),
    java_version: requiredString(input.javaVersion, 'java_version'),
    blockbench_version: requiredString(input.blockbenchVersion, 'blockbench_version'),
    toolkit_version: requiredString(input.toolkitVersion, 'toolkit_version'),
    protocol_version: requiredString(input.protocolVersion, 'protocol_version'),
    installed_extensions: boundedEntries(input.installedExtensions || [], 'pluginId', 'pluginVersion'),
    physical_providers: boundedEntries(input.physicalProviders || [], 'modId', 'modVersion'),
    active_provider_profile: requiredString(input.activeProviderProfile, 'active_provider_profile'),
    project_format: requiredString(input.projectFormat, 'project_format'),
    project_revision: requiredString(input.projectRevision, 'project_revision'),
  });
}

module.exports = {buildSessionFingerprint};
