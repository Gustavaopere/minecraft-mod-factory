'use strict';

const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');
const {
  GECKOLIB4_AUTHORITY,
  validateGeckoLib4GeoDocument,
  validateGeckoLib4AnimationDocument,
  createGeckoLib4ExportPlan,
} = require('../../tooling/blockbench/asset-toolkit/core/provider-adapter/geckolib4_adapter.js');
const {getExtensionDefinition} = require('../../tooling/blockbench/asset-toolkit/core/extension-registry/extension_registry.js');

class GoldenSampleValidationError extends Error {
  constructor(code, message) { super(`${code}: ${message}`); this.name = 'GoldenSampleValidationError'; this.code = code; }
}
const fail = (code, message) => { throw new GoldenSampleValidationError(code, message); };
const readJson = (file) => JSON.parse(fs.readFileSync(file, 'utf8'));
const sha256 = (value) => crypto.createHash('sha256').update(value).digest('hex');

function pngDimensions(buffer) {
  const sig = Buffer.from([0x89,0x50,0x4e,0x47,0x0d,0x0a,0x1a,0x0a]);
  if (!Buffer.isBuffer(buffer) || buffer.length < 24 || !buffer.subarray(0, 8).equals(sig) || buffer.toString('ascii', 12, 16) !== 'IHDR') {
    fail('INVALID_TEXTURE_PNG', 'canonical texture must be a non-truncated PNG');
  }
  return {width: buffer.readUInt32BE(16), height: buffer.readUInt32BE(20)};
}

function outlinerRefs(entries, refs = new Set()) {
  if (!Array.isArray(entries)) fail('INVALID_BBMODEL_OUTLINER', 'outliner must be an array');
  for (const entry of entries) {
    if (typeof entry === 'string') { refs.add(entry); continue; }
    if (!entry || typeof entry.uuid !== 'string') fail('INVALID_BBMODEL_OUTLINER', 'group entries need uuid');
    refs.add(entry.uuid); outlinerRefs(entry.children || [], refs);
  }
  return refs;
}

function validateNativeBbmodel(bb, textureBuffer) {
  if (!bb || bb.meta?.format_version !== '5.0' || bb.meta?.model_format !== 'geckolib_model') fail('INVALID_BBMODEL_MODEL_FORMAT', 'requires Blockbench 5.0 project + geckolib_model');
  if (bb.name !== 'golden-sample-mob' || bb.model_identifier !== 'golden_sample_mob') fail('INVALID_BBMODEL_IDENTITY', 'project identity drifted');
  if (bb.geckolib_modid !== 'minecraft_mod_factory' || bb.geckolib_model_type !== 'Entity') fail('INVALID_GECKOLIB_PROJECT', 'GeckoLib project properties drifted');
  if (bb.resolution?.width !== 32 || bb.resolution?.height !== 32) fail('INVALID_BBMODEL_RESOLUTION', 'resolution must be 32x32');

  const elements = Array.isArray(bb.elements) ? bb.elements : [];
  const cubes = elements.filter((x) => x?.type === 'cube');
  const locators = elements.filter((x) => x?.type === 'locator');
  if (cubes.length !== 4) fail('INVALID_BBMODEL_GEOMETRY', `expected 4 cubes, got ${cubes.length}`);
  if (locators.length !== 1 || locators[0].name !== 'focus') fail('INVALID_BBMODEL_LOCATOR', 'requires one focus locator');
  const elementIds = new Set(elements.map((x) => x?.uuid));
  if (elementIds.has(undefined) || elementIds.size !== elements.length) fail('INVALID_BBMODEL_UUID', 'element UUIDs must be unique');

  const groups = Array.isArray(bb.groups) ? bb.groups : [];
  const expectedGroups = ['root','body','head','left_leg','right_leg'];
  if (groups.length !== expectedGroups.length || expectedGroups.some((name) => !groups.some((x) => x?.name === name))) fail('INVALID_BBMODEL_GROUPS', 'rig hierarchy drifted');
  const groupIds = new Set(groups.map((x) => x?.uuid));
  if (groupIds.has(undefined) || groupIds.size !== groups.length) fail('INVALID_BBMODEL_UUID', 'group UUIDs must be unique');
  const refs = outlinerRefs(bb.outliner);
  for (const id of [...elementIds, ...groupIds]) if (!refs.has(id)) fail('INVALID_BBMODEL_OUTLINER', `missing ${id}`);

  const textures = Array.isArray(bb.textures) ? bb.textures : [];
  if (textures.length !== 1) fail('INVALID_BBMODEL_TEXTURES', 'requires one canonical texture');
  const tex = textures[0];
  if (tex.name !== 'golden-sample-mob.png' || tex.relative_path !== 'golden-sample-mob.png' || !tex.source?.startsWith('data:image/png;base64,')) fail('INVALID_BBMODEL_TEXTURE_SOURCE', 'texture authority drifted');
  const embedded = Buffer.from(tex.source.slice('data:image/png;base64,'.length), 'base64');
  if (!embedded.equals(textureBuffer)) fail('BBMODEL_TEXTURE_DIVERGENCE', 'embedded texture differs from canonical PNG');
  for (const cube of cubes) {
    if (![...(cube.from || []), ...(cube.to || [])].every(Number.isFinite) || cube.from?.length !== 3 || cube.to?.length !== 3) fail('INVALID_BBMODEL_CUBE', `${cube.name} geometry invalid`);
    for (const side of ['north','east','south','west','up','down']) if (cube.faces?.[side]?.texture !== 0) fail('INVALID_BBMODEL_FACE_TEXTURE', `${cube.name}.${side} must use texture 0`);
  }

  const animations = Array.isArray(bb.animations) ? bb.animations : [];
  const names = animations.map((x) => x?.name).sort();
  if (JSON.stringify(names) !== JSON.stringify(['animation.golden_sample_mob.idle','animation.golden_sample_mob.walk'])) fail('INVALID_BBMODEL_ANIMATIONS', 'idle/walk required');
  for (const animation of animations) {
    if (!(animation.length > 0)) fail('INVALID_BBMODEL_ANIMATION', `${animation.name} length invalid`);
    for (const [id, animator] of Object.entries(animation.animators || {})) {
      if (!groupIds.has(id) || animator?.type !== 'bone') fail('INVALID_BBMODEL_ANIMATOR', `${animation.name} animator invalid`);
      for (const frame of animator.keyframes || []) {
        if (!(frame.time >= 0) || frame.channel !== 'rotation' || frame.data_points?.length !== 1) fail('INVALID_BBMODEL_KEYFRAME', `${animation.name} keyframe invalid`);
      }
    }
  }
  return {cubeCount: cubes.length, locatorCount: locators.length, animationCount: animations.length};
}

function validateManifest(manifest, textureBuffer, geo, animation, actualGeo, actualAnimation) {
  if (manifest?.sampleId !== 'golden_sample_mob_geckolib4' || !['PREPARED_FOR_REAL_HANDOFF','REAL_HANDOFF_VALIDATED'].includes(manifest.state)) fail('INVALID_MANIFEST', 'sample/state invalid');
  const source = manifest.sourceAuthority || {};
  if (source.path !== 'golden-sample-mob.bbmodel' || source.format !== 'bbmodel' || source.native !== true || source.blockbenchProjectFormatVersion !== '5.0' || source.blockbenchEditorBaseline !== '5.1.6' || source.modelFormat !== 'geckolib_model') fail('INVALID_SOURCE_AUTHORITY', 'native source pins drifted');

  const dim = pngDimensions(textureBuffer); const texture = manifest.textureSource || {};
  if (texture.path !== 'golden-sample-mob.png' || texture.sha256 !== sha256(textureBuffer) || texture.width !== 32 || texture.height !== 32 || dim.width !== 32 || dim.height !== 32) fail('INVALID_TEXTURE_AUTHORITY', 'texture pin drifted');

  const provider = manifest.provider || {}; const ext = getExtensionDefinition('geckolib');
  if (!ext || provider.profileId !== 'geckolib4_entity' || provider.providerFamily !== GECKOLIB4_AUTHORITY.providerFamily || provider.runtimeVersion !== GECKOLIB4_AUTHORITY.runtimeVersion || provider.blockbenchPluginId !== GECKOLIB4_AUTHORITY.blockbenchPluginId || provider.blockbenchPluginVersion !== GECKOLIB4_AUTHORITY.blockbenchPluginVersion || ext.pluginVersion !== provider.blockbenchPluginVersion || ext.classification !== 'REQUIRED_PROFILE' || ext.providerFamily !== 'geckolib4') fail('PROVIDER_AUTHORITY_DRIFT', 'provider/plugin pins drifted');

  validateGeckoLib4GeoDocument(geo); validateGeckoLib4AnimationDocument(animation);
  const expected = manifest.expectedExports || [];
  if (expected.length !== 2 || expected.some((x) => x.classification !== 'EXPECTED_CONTRACT_NOT_EXPORTER_EVIDENCE')) fail('EXPECTED_EXPORT_CLASSIFICATION_DRIFT', 'expected fixtures are not exporter evidence');

  const plan = createGeckoLib4ExportPlan({profileId:'geckolib4_entity', sourcePath:'art/golden-samples/geckolib4-simple-mob/golden-sample-mob.bbmodel', outputDirectory:'art/golden-samples/geckolib4-simple-mob/actual', resourceName:'golden-sample-mob', includeAnimations:true});
  const paths = plan.artifacts.map((x) => x.path);
  const wanted = ['art/golden-samples/geckolib4-simple-mob/actual/golden-sample-mob.geo.json','art/golden-samples/geckolib4-simple-mob/actual/golden-sample-mob.animation.json'];
  if (!plan.preserveSource || JSON.stringify(paths) !== JSON.stringify(wanted)) fail('EXPORT_PLAN_DRIFT', 'adapter handoff plan drifted');

  const h = manifest.realHandoff || {}; const gates = ['editorOpened','sourceRoundTripValidated','exporterProduced','reopenValidated','runtimeValidated'];
  if ([...gates,'f4I6Evidence'].some((key) => typeof h[key] !== 'boolean')) fail('INVALID_HANDOFF_STATE', 'handoff evidence must be boolean');
  if (h.f4I6Evidence && !gates.every((key) => h[key])) fail('PREMATURE_I6_EVIDENCE', 'I6 requires all real handoff gates');
  if (h.exporterProduced) {
    if (!actualGeo || !actualAnimation) fail('MISSING_EXPORTER_EVIDENCE', 'actual exporter artifacts required');
    validateGeckoLib4GeoDocument(actualGeo); validateGeckoLib4AnimationDocument(actualAnimation);
  } else if (actualGeo || actualAnimation) fail('UNCLASSIFIED_ACTUAL_OUTPUT', 'actual outputs require exporterProduced=true');
  if (manifest.state === 'REAL_HANDOFF_VALIDATED' && !h.f4I6Evidence) fail('INVALID_MANIFEST_STATE', 'validated state requires I6 evidence');
  if (manifest.state === 'PREPARED_FOR_REAL_HANDOFF' && h.f4I6Evidence) fail('INVALID_MANIFEST_STATE', 'prepared state cannot claim I6');
  return {plan, dimensions: dim};
}

function loadSample(root = __dirname) {
  const actual = path.join(root, 'actual');
  const geoPath = path.join(actual, 'golden-sample-mob.geo.json');
  const animPath = path.join(actual, 'golden-sample-mob.animation.json');
  return {
    bbmodel: readJson(path.join(root, 'golden-sample-mob.bbmodel')),
    manifest: readJson(path.join(root, 'MANIFEST.json')),
    textureBuffer: fs.readFileSync(path.join(root, 'golden-sample-mob.png')),
    geo: readJson(path.join(root, 'expected', 'golden-sample-mob.geo.json')),
    animation: readJson(path.join(root, 'expected', 'golden-sample-mob.animation.json')),
    actualGeo: fs.existsSync(geoPath) ? readJson(geoPath) : null,
    actualAnimation: fs.existsSync(animPath) ? readJson(animPath) : null,
  };
}

function validateSample(input = loadSample()) {
  const native = validateNativeBbmodel(input.bbmodel, input.textureBuffer);
  const manifest = validateManifest(input.manifest, input.textureBuffer, input.geo, input.animation, input.actualGeo, input.actualAnimation);
  return {ok:true, native, exportPlan:manifest.plan, texture:manifest.dimensions};
}
if (require.main === module) process.stdout.write(`${JSON.stringify(validateSample(), null, 2)}\n`);
module.exports = {GoldenSampleValidationError, loadSample, validateNativeBbmodel, validateManifest, validateSample};
