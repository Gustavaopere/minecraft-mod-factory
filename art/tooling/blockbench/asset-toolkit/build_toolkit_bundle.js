'use strict';

const fs = require('node:fs');
const path = require('node:path');

const ROOT = __dirname;
const NATIVE_MODULE_ALLOWLIST = Object.freeze(['node:crypto']);
const SOURCE_MODULES = Object.freeze([
  'core/project-model/project_model.js',
  'core/common/contract_utils.js',
  'core/mutations/mutation_engine.js',
  'core/animation/animation_engine.js',
  'core/uv-texture/uv_texture_engine.js',
  'core/uv-texture/uv_analysis.js',
  'core/uv-texture/uv_pack.js',
  'core/validator/validator.js',
  'core/contract-profile/contract_profile.js',
  'core/report/report.js',
  'core/extension-registry/extension_registry.js',
  'core/provider-profile/physical_provider_snapshot.js',
  'core/provider-profile/provider_profiles.js',
  'core/index.js',
  'live-bridge/protocol.js',
  'live-bridge/project_snapshot.js',
  'live-bridge/fingerprint.js',
  'live-bridge/read_only_router.js',
  'live-bridge/blockbench_bridge_client.js',
  'blockbench-plugin/live_bridge_adapter.js',
  'blockbench-plugin/modeling_adapter.js',
  'blockbench-plugin/uv_texture_adapter.js',
  'blockbench-plugin/animation_adapter.js',
  'blockbench-plugin/plugin_adapter.js',
]);

function isAllowedNativeModule(moduleId) {
  return typeof moduleId === 'string' && NATIVE_MODULE_ALLOWLIST.includes(moduleId);
}

function sourceExternalRequires(source) {
  const modules = [];
  const pattern = /\brequire\(\s*['"]([^'"]+)['"]\s*\)/g;
  let match;
  while ((match = pattern.exec(source))) {
    if (!match[1].startsWith('.')) modules.push(match[1]);
  }
  return modules;
}

function validateExternalRequires() {
  for (const id of SOURCE_MODULES) {
    const source = fs.readFileSync(path.join(ROOT, id), 'utf8');
    for (const moduleId of sourceExternalRequires(source)) {
      if (!isAllowedNativeModule(moduleId)) {
        throw new Error(`Minecraft Mod Factory Asset Toolkit bundle source ${id} requests forbidden native module: ${moduleId}`);
      }
    }
  }
  return true;
}

function indent(source, spaces) {
  const prefix = ' '.repeat(spaces);
  return source.replace(/\r\n/g, '\n').trimEnd().split('\n').map((line) => line.trim().length === 0 ? '' : `${prefix}${line}`).join('\n');
}

function buildBundle() {
  validateExternalRequires();
  const moduleEntries = SOURCE_MODULES.map((id) => {
    const source = fs.readFileSync(path.join(ROOT, id), 'utf8');
    return `    ${JSON.stringify(id)}: function(module, exports, require) {\n${indent(source, 6)}\n    }`;
  }).join(',\n');

  return `(function (root, nativeRequire, factory) {\n  'use strict';\n  const api = factory(nativeRequire);\n  if (typeof module === 'object' && module.exports) module.exports = api;\n  if (root && root.Plugin && root.Action && root.MenuBar && root.Blockbench) api.registerBlockbenchPlugin(root);\n})(\n  typeof globalThis !== 'undefined' ? globalThis : this,\n  typeof require === 'function' ? require : null,\n  function (nativeRequire) {\n  'use strict';\n\n  const nativeModuleAllowlist = new Set(${JSON.stringify([...NATIVE_MODULE_ALLOWLIST])});\n  const modules = {\n${moduleEntries}\n  };\n  const cache = Object.create(null);\n\n  function normalizeModuleId(value) {\n    const output = [];\n    for (const segment of value.split('/')) {\n      if (!segment || segment === '.') continue;\n      if (segment === '..') {\n        if (!output.length) throw new Error('Minecraft Mod Factory Asset Toolkit module path escaped bundle root.');\n        output.pop();\n      } else output.push(segment);\n    }\n    return output.join('/');\n  }\n\n  function resolveModuleId(fromId, request) {\n    const base = fromId.split('/');\n    base.pop();\n    const resolved = normalizeModuleId(base.concat(request.split('/')).join('/'));\n    return resolved.endsWith('.js') ? resolved : resolved + '.js';\n  }\n\n  function moduleRequire(fromId, request) {\n    if (typeof request !== 'string') throw new Error('Minecraft Mod Factory Asset Toolkit bundle requires a string module id.');\n    if (request.startsWith('.')) return loadModule(resolveModuleId(fromId, request));\n    if (!nativeModuleAllowlist.has(request)) throw new Error('Minecraft Mod Factory Asset Toolkit bundle forbids native module: ' + request);\n    if (typeof nativeRequire !== 'function') throw new Error('Minecraft Mod Factory Asset Toolkit native module is unavailable in this Blockbench variant: ' + request);\n    return nativeRequire(request);\n  }\n\n  function loadModule(id) {\n    if (cache[id]) return cache[id].exports;\n    const factory = modules[id];\n    if (!factory) throw new Error('Minecraft Mod Factory Asset Toolkit bundle module not found: ' + id);\n    const module = {exports: {}};\n    cache[id] = module;\n    factory(module, module.exports, (request) => moduleRequire(id, request));\n    return module.exports;\n  }\n\n  const core = loadModule('core/index.js');\n  const protocol = loadModule('live-bridge/protocol.js');\n  const bridgeClient = loadModule('live-bridge/blockbench_bridge_client.js');\n  const blockbenchPlugin = loadModule('blockbench-plugin/plugin_adapter.js');\n  return Object.assign({}, core, protocol, bridgeClient, blockbenchPlugin);\n});\n`;
}

function checkBundle() {
  const target = path.join(ROOT, 'asset_toolkit.js');
  const current = fs.existsSync(target) ? fs.readFileSync(target, 'utf8') : '';
  const expected = buildBundle();
  if (current !== expected) {
    process.stderr.write('asset_toolkit.js is stale; run node build_toolkit_bundle.js --write\n');
    return false;
  }
  return true;
}

if (require.main === module) {
  const mode = process.argv[2] || '--check';
  if (mode === '--write') {
    fs.writeFileSync(path.join(ROOT, 'asset_toolkit.js'), buildBundle(), 'utf8');
  } else if (mode === '--check') {
    if (!checkBundle()) process.exitCode = 1;
  } else {
    process.stderr.write(`unknown mode: ${mode}\n`);
    process.exitCode = 2;
  }
}

module.exports = {
  SOURCE_MODULES,
  NATIVE_MODULE_ALLOWLIST,
  isAllowedNativeModule,
  validateExternalRequires,
  buildBundle,
  checkBundle,
};
