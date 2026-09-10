'use strict';

const core = require('../core/index.js');
const {PROTOCOL_VERSION, READ_ONLY_METHODS, bridgeError} = require('./protocol.js');
const {createProjectSnapshot} = require('./project_snapshot.js');

function clone(value) { return value == null ? value : JSON.parse(JSON.stringify(value)); }

function createReadOnlyRouter(options = {}) {
  const getProject = typeof options.getProject === 'function' ? options.getProject : () => ({});
  const getBlockbenchVersion = typeof options.getBlockbenchVersion === 'function' ? options.getBlockbenchVersion : () => 'UNKNOWN';
  const getInstalledExtensions = typeof options.getInstalledExtensions === 'function' ? options.getInstalledExtensions : () => [];
  const getAuthorizedExtensionIds = typeof options.getMcpAuthorizedExtensionIds === 'function' ? options.getMcpAuthorizedExtensionIds : () => [];
  const activeProviderProfile = typeof options.activeProviderProfile === 'function' ? options.activeProviderProfile : () => null;
  const physicalProviders = options.physicalProviders || {};

  function context() {
    return {
      blockbenchVersion: getBlockbenchVersion(),
      installedExtensions: getInstalledExtensions(),
      mcpAuthorizedExtensionIds: getAuthorizedExtensionIds(),
      physicalProviders,
    };
  }

  async function call(method, params = {}) {
    if (!READ_ONLY_METHODS.includes(method)) throw bridgeError('METHOD_NOT_ALLOWED', method);
    const project = getProject() || {};
    const snapshot = createProjectSnapshot(project);
    const ctx = context();
    switch (method) {
      case 'blockbench.get_status': return {connected: true, readOnly: true, protocolVersion: PROTOCOL_VERSION, blockbenchVersion: ctx.blockbenchVersion, projectRevision: snapshot.projectRevision, activeProviderProfile: activeProviderProfile()};
      case 'blockbench.get_capabilities': return {readOnly: true, methods: [...READ_ONLY_METHODS], protocolVersion: PROTOCOL_VERSION};
      case 'blockbench.get_project': return snapshot;
      case 'blockbench.get_scene_graph': return {groups: snapshot.groups, elements: snapshot.elements, projectRevision: snapshot.projectRevision};
      case 'blockbench.get_selection': return {selection: snapshot.selection, projectRevision: snapshot.projectRevision};
      case 'blockbench.get_bones': return snapshot.groups;
      case 'blockbench.get_elements': return snapshot.elements;
      case 'blockbench.get_textures': return snapshot.textures;
      case 'blockbench.get_animations': return snapshot.animations;
      case 'blockbench.get_animation': {
        const target = typeof params.animationId === 'string' ? params.animationId : (typeof params.name === 'string' ? params.name : '');
        return snapshot.animations.find((entry) => entry.uuid === target || entry.name === target) || null;
      }
      case 'blockbench.compute_bounds': return core.computeBounds(Array.isArray(project.elements) ? project.elements : []);
      case 'blockbench.validate': return core.validateProject(project, {});
      case 'blockbench.validate_contract': return core.validateProject(project, params.profile && typeof params.profile === 'object' ? params.profile : {});
      case 'blockbench.extensions.list': return Object.values(core.EXTENSION_CATALOG).map(clone);
      case 'blockbench.extensions.get': {
        const definition = core.getExtensionDefinition(params.pluginId);
        return definition ? {...clone(definition), evaluation: core.evaluateExtension(definition, ctx)} : null;
      }
      case 'blockbench.extensions.get_fingerprint': return {blockbenchVersion: ctx.blockbenchVersion, installedExtensions: clone(ctx.installedExtensions)};
      case 'blockbench.extensions.check_compatibility': {
        const definition = core.getExtensionDefinition(params.pluginId);
        return definition ? core.evaluateExtension(definition, ctx) : {installed: false, compatible: false, versionMatch: false, mcpAllowed: false, reasons: ['UNKNOWN_EXTENSION']};
      }
      case 'blockbench.profiles.list': return core.listProviderProfiles().map(clone);
      case 'blockbench.profiles.get': return clone(core.getProviderProfile(params.profileId));
      case 'blockbench.profiles.resolve_for_asset': return core.resolveProviderProfile(params.profileId, ctx);
      default: throw bridgeError('METHOD_NOT_ALLOWED', method);
    }
  }

  return Object.freeze({call, methods: () => [...READ_ONLY_METHODS]});
}

module.exports = {createReadOnlyRouter};
