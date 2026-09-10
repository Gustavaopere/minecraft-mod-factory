'use strict';

const fs = require('node:fs');
const path = require('node:path');
const toolkit = require('../art/tooling/blockbench/asset-toolkit/asset_toolkit.js');
require('./validate_reference_evidence.js');

const ROOT = __dirname;
const MODEL_ID = 'golden_reference_focus_relic';
const SPELL_ID = 'golden_reference_arcane_bolt';
const REFERENCE_MARKER = 'REFERENCE-ONLY';
const UNRESOLVED_MARKER = 'UNRESOLVED';

function fail(message) {
  throw new Error(`Golden Samples validation failed: ${message}`);
}

function readJson(relative) {
  return JSON.parse(fs.readFileSync(path.join(ROOT, relative), 'utf8'));
}

function readText(relative) {
  return fs.readFileSync(path.join(ROOT, relative), 'utf8');
}

function walk(dir) {
  const out = [];
  for (const entry of fs.readdirSync(dir, {withFileTypes: true})) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) out.push(...walk(full));
    else out.push(full);
  }
  return out;
}

function requireGuardedField(relative, linePrefix, token = UNRESOLVED_MARKER) {
  const line = readText(relative)
    .split(/\r?\n/)
    .find((candidate) => candidate.trim().startsWith(linePrefix));
  if (!line) fail(`${relative} missing guarded field ${linePrefix}`);
  if (!line.includes(token)) fail(`${relative} guarded field ${linePrefix} must remain ${token}`);
}

const fixture = readJson('model-asset/validator-project-fixture.json');
const profile = readJson('model-asset/TOOLKIT-PROFILE.json');

if (fixture.name !== MODEL_ID) fail(`fixture name must be ${MODEL_ID}`);
if (profile.assetId !== MODEL_ID || profile.referenceOnly !== true) fail('Toolkit profile must identify the reference-only model asset');

const result = toolkit.validateProject(fixture, profile);
if (result.errors.length) fail(toolkit.formatReport(result));
if (!result.counts || !Number.isInteger(result.counts.cubeCount) || result.counts.cubeCount < 1) fail('fixture must exercise at least one cube-like element');
if (!Number.isInteger(result.counts.locatorCount) || result.counts.locatorCount < 1) fail('fixture must exercise at least one Locator-like element');
if (!result.bounds || !result.bounds.span.every(Number.isFinite)) fail('fixture must produce finite cube bounds');

const warningCodes = result.warnings.map((item) => item.code).sort();
if (warningCodes.length !== 1 || warningCodes[0] !== 'UNSAVED_SOURCE') {
  fail(`fixture warnings must be exactly UNSAVED_SOURCE while native .bbmodel is intentionally absent; got ${warningCodes.join(', ') || '<none>'}`);
}

const focusCore = fixture.elements.find((element) => element && element.name === 'focus_core');
if (!focusCore || !Array.isArray(focusCore.from) || !Array.isArray(focusCore.to)) fail('fixture must keep focus_core as cube-like geometry');
if (!focusCore.parent || focusCore.parent.uuid !== 'bone-root') fail('focus_core must remain attached to root');

const spellMuzzle = fixture.elements.find((element) => element && element.name === 'spell_muzzle');
if (!spellMuzzle || !Array.isArray(spellMuzzle.from)) fail('fixture must contain the spell_muzzle Locator-like attachment');
if (Object.prototype.hasOwnProperty.call(spellMuzzle, 'to') || Object.prototype.hasOwnProperty.call(spellMuzzle, 'faces')) fail('spell_muzzle must remain Locator-like, not cube-like');
if (!spellMuzzle.parent || spellMuzzle.parent.uuid !== 'bone-vfx') fail('spell_muzzle must remain attached to vfx_anchor');

for (const bone of ['root', 'cast_hand', 'vfx_anchor']) {
  if (!Array.isArray(profile.requiredBones) || !profile.requiredBones.includes(bone)) fail(`profile missing required bone ${bone}`);
}
for (const animation of [
  'animation.golden_reference_focus_relic.idle',
  'animation.golden_reference_focus_relic.cast',
]) {
  if (!Array.isArray(profile.requiredAnimations) || !profile.requiredAnimations.includes(animation)) fail(`profile missing required animation ${animation}`);
}
const boundedMaxSpan = Array.isArray(profile.maxSpan) ? profile.maxSpan.slice(0, 3) : [];
if (boundedMaxSpan.length !== 3 || !boundedMaxSpan.every((value) => Number.isFinite(value) && value > 0)) {
  fail('profile must keep exactly three finite, positive asset-specific maxSpan limits');
}

const allFiles = walk(ROOT);
const markdownFiles = allFiles.filter((file) => file.endsWith('.md'));
if (markdownFiles.length < 10) fail('expected complete model/spell markdown corpus');
for (const file of markdownFiles) {
  const text = fs.readFileSync(file, 'utf8');
  const label = path.relative(ROOT, file);
  if (!text.includes(REFERENCE_MARKER)) fail(`${label} missing ${REFERENCE_MARKER} safety marker`);
  if (path.basename(file) !== 'README.md' && !text.includes(UNRESOLVED_MARKER)) fail(`${label} missing ${UNRESOLVED_MARKER} fail-closed marker`);
}

const guardedUnresolvedFields = {
  'model-asset/ASSET-BRIEF.md': [
    '- Gameplay owner:',
    '- Runtime consumer/class:',
    '- Registry/resource ID:',
    '- Multiplayer authority impact:',
    '- Production dimensions/scale:',
    '- Real texture file:',
    '- Texel density:',
    '- Exact exporter/plugin version:',
    '- Runtime renderer/controller:',
    '- Export destination:',
    '- VFX provider/API for `spell_muzzle`:',
  ],
  'model-asset/MODEL-CONTRACT.md': [
    '- Project-owned native `.bbmodel`:',
    '- Real texture source:',
    '- Exported GeckoLib geometry/animation resources:',
    '| `root` |',
    '| `cast_hand` |',
    '| `vfx_anchor` |',
    '- Exact provider consumer/API:',
    '- Production cube count/topology:',
    '- Production scale:',
    '- Actual PNG asset:',
    '- Final palette/material separation:',
    '- Final texel density:',
    '- Any future VFX attachment must consume',
    '- Blockbench GeckoLib plugin/exporter version:',
    '- Geometry export path:',
    '- Animation export path:',
    '- Renderer/model class:',
    '- Client registration:',
    '- Dedicated-server classloading boundary:',
  ],
  'model-asset/ANIMATION-BRIEF.md': [
    '- Production amplitude/easing/keyframes:',
    '- Player-hand synchronization:',
    '- Exact keyframes/easing:',
    '- Exact event marker/API linking release to gameplay:',
    '- Animation controller class/API:',
    '- Trigger/network synchronization:',
    '- Client prediction policy:',
  ],
  'spell/SPELL-BRIEF.md': [
    '- Gameplay owner/mod:',
    '- Runtime spell/ability registry ID:',
    '- Provider-native spell implementation:',
    '- Cast legality:',
    '- Resource/mana cost:',
    '- Cooldown:',
    '- Damage/effect:',
    '- Targeting/range/velocity:',
    '- Hit/miss/block resolution:',
    '- Anti-abuse/deduplication key:',
    '- Real model dependency:',
    '- Real animation dependency:',
    '- Real VFX assets/provider graphs:',
    '- Real audio assets/SoundEvents:',
    '- Selected provider and exact API/hook:',
  ],
  'spell/SPELL-PRESENTATION.md': [
    '- exact prediction policy is',
    '- exact event/network message/API is',
    '- authoritative projectile/active-state owner is',
    '- interpolation/snapshot policy is',
    '- hit/miss/block/resist/damage owner is',
    '- deduplication/causal event key is',
    '- lifecycle cleanup hooks are',
    '- anticipation cue asset/event:',
    '- release cue asset/event:',
    '- travel loop:',
    '- impact cue asset/event:',
    '- decay tail:',
    '- camera shake:',
    '- crosshair/target lock integration:',
    '- first-person obstruction budget:',
    '- provider selection/API:',
    '- particle count/lifetime/distance culling budgets:',
    '- multiplayer concurrency target:',
    '- fallback when optional provider is absent/incompatible:',
  ],
  'spell/VFX-BRIEF.md': [
    '| Photon 2.2.6.a |',
    '| AAA Particles 2.2.3 |',
    '| AAA Particles World 2.0.0 |',
    '- Release/travel authoritative start condition:',
    '- Impact must consume authoritative result evidence;',
    '- Deduplication token/event identity:',
    '- particle/emitter budgets:',
    '- max visible distance/culling:',
    '- simultaneous caster stress target:',
    '- fallback behavior:',
  ],
  'spell/AUDIO-CUE-SHEET.md': [
    '| Anticipation |',
    '| Release |',
    '| Travel |',
    '| Impact |',
    '| Decay |',
    '- Variant count:',
    '- Pitch randomization:',
    '- Volume:',
    '- Attenuation distance/model:',
    '- Mono/stereo choice:',
    '- Start/loop/end implementation for travel:',
    'A future implementation must prevent duplicate release/impact cues',
    'Actual audio source/author/license:',
  ],
  'spell/VISUAL-QA.md': [
    '| Model silhouette front/back/sides |',
    '| First-person held/cast obstruction |',
    '| Third-person held/cast readability |',
    '| Inventory/icon presentation |',
    '| Day/bright lighting |',
    '| Night/dark lighting |',
    '| Anticipation vs release phase readability |',
    '| Travel silhouette at near/mid/far distance |',
    '| Hit/miss/blocked outcome distinction |',
    '| Multiple simultaneous casters |',
    '| Multiplayer observer consistency |',
    '| Low-FPS/reduced-effects behavior |',
  ],
  'spell/VFX-QA.md': [
    '| Anticipation readability |',
    '| Release landmark readability |',
    '| Travel core/trail separation |',
    '| Impact/resolve causality |',
    '| Decay cleanup |',
    '| First-person visibility |',
    '| Near/mid/far readability |',
    '| Multiple-caster clutter |',
    '| Selected provider exact-version behavior |',
    '| Particle/emitter counts |',
    '| Lifetimes/culling |',
    '| Multiplayer deduplication |',
    '| Optional-provider fallback |',
    '| Performance budget |',
  ],
  'spell/AUDIO-QA.md': [
    '| SoundEvent/sounds.json correctness |',
    '| OGG format/readability |',
    '| Mono/stereo suitability |',
    '| Attenuation and distance falloff |',
    '| Release cue causal uniqueness |',
    '| Impact cue causal uniqueness |',
    '| Travel loop start/stop cleanup |',
    '| Variant/pitch repetition control |',
    '| Combat mix with concurrent casters |',
    '| Death/logout/dimension cleanup where applicable |',
    '| Source/license provenance |',
  ],
};

for (const [relative, fields] of Object.entries(guardedUnresolvedFields)) {
  for (const field of fields) requireGuardedField(relative, field);
}

for (const relative of [
  'model-asset/ASSET-BRIEF.md',
  'model-asset/MODEL-CONTRACT.md',
  'model-asset/ANIMATION-BRIEF.md',
]) {
  if (!readText(relative).includes(MODEL_ID)) fail(`${relative} missing model reference ID`);
}
for (const relative of [
  'spell/SPELL-BRIEF.md',
  'spell/SPELL-PRESENTATION.md',
  'spell/VFX-BRIEF.md',
  'spell/AUDIO-CUE-SHEET.md',
  'spell/VISUAL-QA.md',
  'spell/VFX-QA.md',
  'spell/AUDIO-QA.md',
]) {
  if (!readText(relative).includes(SPELL_ID)) fail(`${relative} missing spell reference ID`);
}

const spellPresentation = readText('spell/SPELL-PRESENTATION.md');
for (const phase of ['Anticipation', 'Release', 'Travel / Active', 'Impact / Resolve', 'Decay']) {
  if (!spellPresentation.includes(phase)) fail(`spell presentation missing lifecycle phase ${phase}`);
}
if (!spellPresentation.includes('server') || !spellPresentation.includes('authoritative')) fail('spell presentation must preserve server-authority language');

const vfxBrief = readText('spell/VFX-BRIEF.md');
for (const providerToken of ['Photon 2.2.6.a', 'AAA Particles 2.2.3', 'AAA Particles World 2.0.0']) {
  if (!vfxBrief.includes(providerToken)) fail(`VFX brief missing verified candidate token ${providerToken}`);
}

for (const qaRelative of ['spell/VISUAL-QA.md', 'spell/VFX-QA.md', 'spell/AUDIO-QA.md']) {
  const qa = readText(qaRelative);
  if (!qa.includes('PENDING')) fail(`${qaRelative} must demonstrate evidence-gated PENDING state`);
  if (/\|\s*PASS\s*\|/i.test(qa)) fail(`${qaRelative} must not claim PASS without real evidence`);
}

const forbiddenArtifacts = allFiles.filter((file) => /\.(bbmodel|png|ogg)$/i.test(file));
if (forbiddenArtifacts.length) fail(`native/binary art assets are out of scope until exact source evidence exists: ${forbiddenArtifacts.join(', ')}`);

if (!String(fixture.fixtureType || '').includes('NOT a Blockbench .bbmodel')) fail('fixture must explicitly deny native .bbmodel semantics');

console.log(`OK: Golden Samples validated; ${result.counts.cubeCount} cube(s), ${result.counts.locatorCount} locator(s), ${result.errors.length} Toolkit error(s), expected warning ${warningCodes[0]}`);
