# Epic Fight / Blender External DCC Handoff

Status: canonical PR13 contract for the Minecraft Mod Factory Asset Toolkit.

## Authority split

PR13 deliberately separates four authorities that must not be conflated:

- physical runtime provider: `epicfight` `21.17.3.1`, artifact `epic-fight-21.17.3.1-mc1.21.1-neoforge.jar`, physical-modlist hash `c21b394dc6a51f43089f068a5a5bda6eac4c1ce4`;
- upstream Epic Fight source audit: `Antikythera-Studios/epicfight@a78aa24b72e90a9d09f5fd61925e4369d117abaf`, source version family `21.17.3`, Minecraft `1.21.1`, NeoForge `21.1.219`, Java `21`;
- Blender exporter audit: `Antikythera-Studios/blender-json-addon@b9c6844193074f8c21b35513052d61c82cc2c207`, addon version `1.0.0`, JSON output;
- Factory target: Minecraft `1.21.1`, NeoForge `21.1.248`, Java `21`.

The source audit baseline and the Factory target are intentionally recorded separately. Source NeoForge `21.1.219` is not relabeled as target-exact `21.1.248` evidence.

## Authoring boundary

The profile ID is `epicfight_blender_handoff`. Blender is authoritative for the final animation authoring source. The Factory preserves both the Blockbench `.bbmodel` reference project and the Blender `.blend` source.

Blockbench is reference-only in this lane. The public bridge can create a handoff manifest from a saved `.bbmodel`, but exposes no direct Epic Fight animation export, no automatic plugin installation, no MCP mutation lane, and no hidden provider conversion.

The handoff manifest records explicit bone mappings and texture references supplied by the caller. It stages the expected runtime destination as:

`assets/<namespace>/animmodels/animations/<animation-id>.json`

No Blockbench, GeckoLib, AzureLib, Animated Java, PAL, Player Animator, or other profile is automatically converted into Epic Fight.

## Proven JSON boundary

The audited Epic Fight runtime loader resolves animation resources from `animmodels/animations` and expects a JSON root containing an `animation` array. The `format` root field is optional in the audited loader and defaults to `MATRIX` when omitted.

The Factory validator intentionally checks only this proven root contract. It does not invent unverified per-keyframe, transform, rig, or exporter semantics.

## Runtime evidence boundary

PR13 is an audited external-DCC handoff contract, not a provider-real runtime proof. It does not prove that the physical Epic Fight `21.17.3.1` JAR loaded on NeoForge `21.1.248`, that the audited Blender exporter generated the staged JSON in a real production session, that a staged animation played correctly in a live Minecraft client, or that the complete physical modpack consumed the artifact successfully.

Therefore PR13 APIs retain:

- `runtimeEvidence=UNPROVEN`;
- `runtimeValidated=false`;
- `f4I6Evidence=false`.

`I6_REAL_HANDOFF=NOT_COMPLETE` remains unchanged and `I7_STATE=BLOCKED_BY_F4_REAL_I6_HANDOFF` remains blocked until separate real handoff evidence exists.
