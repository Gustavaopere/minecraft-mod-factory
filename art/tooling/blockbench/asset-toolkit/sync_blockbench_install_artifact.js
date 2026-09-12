'use strict';

const fs = require('node:fs');
const path = require('node:path');

const ROOT = __dirname;
const CANONICAL_BUNDLE_FILENAME = 'asset_toolkit.js';
const PLUGIN_ADAPTER_FILENAME = path.join('blockbench-plugin', 'plugin_adapter.js');

function pluginIdFromSource(source) {
  const match = String(source).match(/Plugin\.register\(['"]([^'"]+)['"]/);
  if (!match) throw new Error('Minecraft Mod Factory Asset Toolkit Plugin.register id is not statically discoverable.');
  return match[1];
}

function installArtifactFilename() {
  const pluginSource = fs.readFileSync(path.join(ROOT, PLUGIN_ADAPTER_FILENAME), 'utf8');
  return `${pluginIdFromSource(pluginSource)}.js`;
}

function canonicalPath() {
  return path.join(ROOT, CANONICAL_BUNDLE_FILENAME);
}

function installPath() {
  return path.join(ROOT, installArtifactFilename());
}

function checkInstallArtifact() {
  const canonical = canonicalPath();
  const install = installPath();
  if (!fs.existsSync(install)) {
    process.stderr.write(`${path.basename(install)} is missing; run node sync_blockbench_install_artifact.js --write\n`);
    return false;
  }
  if (!fs.readFileSync(canonical).equals(fs.readFileSync(install))) {
    process.stderr.write(`${path.basename(install)} is stale; run node sync_blockbench_install_artifact.js --write\n`);
    return false;
  }
  return true;
}

function writeInstallArtifact() {
  fs.copyFileSync(canonicalPath(), installPath());
}

if (require.main === module) {
  const mode = process.argv[2] || '--check';
  if (mode === '--write') {
    writeInstallArtifact();
  } else if (mode === '--check') {
    if (!checkInstallArtifact()) process.exitCode = 1;
  } else {
    process.stderr.write(`unknown mode: ${mode}\n`);
    process.exitCode = 2;
  }
}

module.exports = {
  CANONICAL_BUNDLE_FILENAME,
  PLUGIN_ADAPTER_FILENAME,
  pluginIdFromSource,
  installArtifactFilename,
  canonicalPath,
  installPath,
  checkInstallArtifact,
  writeInstallArtifact,
};
