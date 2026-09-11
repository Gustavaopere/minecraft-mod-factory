'use strict';

// Physical modlist authority snapshot checked 2026-09-10 (595 top-level mods).
// Presence is not API proof, runtime-health proof, or MCP authorization.
const CURRENT_PHYSICAL_PROVIDER_SNAPSHOT = Object.freeze({
  geckolib: Object.freeze({modId: 'geckolib', version: '4.9.2', presence: 'PRESENT', health: 'UNPROVEN'}),
  azurelib: Object.freeze({modId: 'azurelib', version: '3.1.11', presence: 'PRESENT', health: 'UNPROVEN'}),
  easy_model_entities: Object.freeze({modId: 'easy_model_entities', version: '2.3.0', presence: 'PRESENT', health: 'UNPROVEN'}),
  entity_model_features: Object.freeze({modId: 'entity_model_features', version: '3.3.5', presence: 'PRESENT', health: 'UNPROVEN'}),
  photon: Object.freeze({modId: 'photon', version: '2.2.6.a', presence: 'PRESENT', health: 'KNOWN_RUNTIME_RISK'}),
  lodestone: Object.freeze({modId: 'lodestone', version: '1.8.2', presence: 'PRESENT', health: 'UNPROVEN'}),
  particle_effects: Object.freeze({modId: 'particle_effects', version: '1.5.0+1.21.1+neoforge', presence: 'PRESENT', health: 'PRESENTATION_ONLY'}),
  aaa_particles: Object.freeze({modId: null, version: null, presence: 'ABSENT', health: 'UNAVAILABLE'}),
  aaa_particles_world: Object.freeze({modId: null, version: null, presence: 'ABSENT', health: 'UNAVAILABLE'}),
});

const SNAPSHOT_METADATA = Object.freeze({
  checkedDate: '2026-09-10',
  topLevelModCount: 595,
  authority: 'physical-modlist',
});

module.exports = {CURRENT_PHYSICAL_PROVIDER_SNAPSHOT, SNAPSHOT_METADATA};
