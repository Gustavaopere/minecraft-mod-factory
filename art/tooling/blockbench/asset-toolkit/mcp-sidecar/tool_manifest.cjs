'use strict';

const TOOL_NAMES = Object.freeze([
  'blockbench.get_status',
  'blockbench.get_capabilities',
  'blockbench.get_project',
  'blockbench.get_scene_graph',
  'blockbench.get_selection',
  'blockbench.get_bones',
  'blockbench.get_elements',
  'blockbench.get_textures',
  'blockbench.get_animations',
  'blockbench.get_animation',
  'blockbench.compute_bounds',
  'blockbench.validate',
  'blockbench.validate_contract',
  'blockbench.extensions.list',
  'blockbench.extensions.get',
  'blockbench.extensions.get_fingerprint',
  'blockbench.extensions.check_compatibility',
  'blockbench.profiles.list',
  'blockbench.profiles.get',
  'blockbench.profiles.resolve_for_asset',
]);

const TOOL_DESCRIPTIONS = Object.freeze(Object.fromEntries(TOOL_NAMES.map((name) => [name, `Read-only Minecraft Mod Factory Asset Toolkit bridge operation: ${name}`])));

module.exports = {TOOL_NAMES, TOOL_DESCRIPTIONS};
