'use strict';

const animatedJava = require('../core/provider-adapter/animated_java_adapter.js');

function fail(code, message) {
  throw new animatedJava.AnimatedJavaContractError(code, message);
}

function createBlockbenchAnimatedJavaAdapter(bb) {
  if (!bb || typeof bb !== 'object') {
    fail('ANIMATED_JAVA_BLOCKBENCH_UNAVAILABLE', 'Blockbench API object is required.');
  }
  if (bb.Blockbench?.isMobile === true || bb.Blockbench?.isWeb === true) {
    fail('ANIMATED_JAVA_DESKTOP_REQUIRED', 'Animated Java 1.10.2 is audited as a desktop Blockbench extension.');
  }

  const project = bb.Project ?? bb.Blockbench?.Project;
  if (!project || typeof project !== 'object') {
    fail('ANIMATED_JAVA_BLOCKBENCH_UNAVAILABLE', 'No active Blockbench project is available.');
  }
  if (project.format?.id !== animatedJava.ANIMATED_JAVA_AUTHORITY.blueprintFormatId) {
    fail(
      'ANIMATED_JAVA_BLUEPRINT_FORMAT_REQUIRED',
      `Active Blockbench project format must be ${animatedJava.ANIMATED_JAVA_AUTHORITY.blueprintFormatId}.`,
    );
  }

  const settings = project.animated_java;
  if (!settings || typeof settings !== 'object' || Array.isArray(settings)) {
    fail('ANIMATED_JAVA_SETTINGS_UNAVAILABLE', 'Active Blueprint project does not expose Animated Java settings.');
  }

  function previewHandoff() {
    const plan = animatedJava.createAnimatedJavaExportPlan({
      sourcePath: project.save_path,
      blueprintId: settings.blueprint_id,
      targetMinecraftVersion: settings.target_minecraft_version,
      resourcePackExportMode: settings.resource_pack_export_mode,
      dataPackExportMode: settings.data_pack_export_mode,
      resourcePackPath: settings.resource_pack,
      dataPackPath: settings.data_pack,
      enablePluginMode: settings.enable_plugin_mode === true,
    });

    return Object.freeze({
      ...plan,
      sourceFormatId: animatedJava.ANIMATED_JAVA_AUTHORITY.blueprintFormatId,
      sourceCodecId: animatedJava.ANIMATED_JAVA_AUTHORITY.blueprintCodecId,
    });
  }

  return Object.freeze({previewHandoff});
}

module.exports = {
  createBlockbenchAnimatedJavaAdapter,
};
