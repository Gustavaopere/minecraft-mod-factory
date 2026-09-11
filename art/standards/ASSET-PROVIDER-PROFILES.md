# Asset Provider Profiles

Status: canonical profile contract for the modular Minecraft Mod Factory Asset Toolkit.

A provider profile describes an authoring/runtime path that has concrete capabilities and an explicit authority. Profiles are not placeholders and are not created to satisfy a target count.

## Resolution contract

A profile may declare:

- `id` and `family`;
- `authority` — the system that owns the exported/runtime semantics;
- `assetKind` when the profile is kind-specific;
- `requiredProvider` with exact physical mod ID/version when a Minecraft runtime provider is required;
- `requiredExtensions` with exact Blockbench plugin IDs;
- non-empty `capabilities`.

Resolution is fail-closed. Unknown profile, absent physical provider, unsupported provider version, known runtime-risk provider, missing extension, wrong extension version, incompatible Blockbench version, or missing MCP allowlist authorization makes a required path `UNAVAILABLE`.

## Current capability-backed profiles

- `java_block_item` — vanilla/NeoForge Java block/item model path.
- `neoforge_native_entity_animation` — Minecraft 1.21.1 / NeoForge 21.1.248 JSON entity-animation runtime through `AnimationParser.CODEC`. It has no invented external runtime-provider dependency and no required Blockbench extension. The `.bbmodel` remains source authority; the audited Factory handoff stages runtime JSON under `assets/<namespace>/neoforge/animations/entity/*.json`. The Blockbench catalog plugin `animation_to_json` 1.0.1 is recorded only as `AUDIT_REQUIRED` authoring interoperability reference: it is not runtime authority, it is not MCP-allowed, and exact live compatibility with Blockbench 5.1.6 is not claimed. Target-exact codec/compile evidence is `PASS` against Minecraft 1.21.1 / NeoForge 21.1.248 / Java 21; this is not a claim that a staged animation has been exercised in a live Minecraft client or server.
- `geckolib4_entity`, `geckolib4_item`, `geckolib4_block`, `geckolib4_armor` — GeckoLib 4.9.2 with `geckolib` 4.2.5.
- `azurelib_entity`, `azurelib_item`, `azurelib_block`, `azurelib_armor` — AzureLib 3.1.11 with `azurelib_utils` 2.1.5.
- `easy_model_entities_entity`, `easy_model_entities_block_entity` — Easy Model Entities 2.3.0 with the official `easy_model_entities` Blockbench exporter 1.0.0. The exporter declares Blockbench `min_version=4.9.0`; the Factory does not invent an exact-editor restriction above that minimum. `.bbmodel` remains the source authority. The audited handoff maps server profiles to `data/<namespace>/easy_model_entities/profiles/entity|block_entity/<id>.json`, render profiles to `assets/<namespace>/easy_model_entities/render_profiles/entity|block_entity/<id>.json`, and the preserved model to `assets/<namespace>/easy_model_entities/models/<id>.bbmodel`. Runtime schema authority is `0.2.0` and the Easy Model Entities 2.3.0 runtime API authority is `2.3.0`.
- `emf_cem_entity` — Entity Model Features 3.3.5 with CEM Template Loader 9.2.0. EMF Animation Addon 1.0.5 is preferred, not a hard requirement.
- `animated_java_display_entities` — Animated Java 1.10.2 authoring/export pipeline. It deliberately has no invented physical runtime-mod requirement.

## Easy Model Entities runtime evidence boundary

PR9 target-exact source runtime validation uses the pinned Easy Model Entities 2.3.0 source revision `8c912371838c2a26bbb383008ad3999280f075d1`, Java 21, Minecraft 1.21.1 and NeoForge 21.1.248. The source registers the entity spawn-item and block spawn/place GameTests, and the NeoForge GameTest server executed all 15 required Easy Model Entities tests successfully in Factory run `34621675116`.

The upstream 2.3.0 build was originally pinned to NeoForge 21.1.92 and forced ASM 9.7. NeoForge 21.1.248 bootstraps ASM 9.10.1, so the Factory smoke aligns only those ASM build-tool pins to 9.10.1 inside the ephemeral CI checkout before launching `:NeoForge:runGameTestServer`. No upstream source/runtime file is committed back or silently rewritten as a production artifact.

This evidence is `TARGET_EXACT_SOURCE_GAMETEST_PASS`. It proves the pinned 2.3.0 source GameTest suite can compile, launch and pass on NeoForge 21.1.248 under the documented ephemeral build-harness adaptation. It does **not** prove the physical modpack JAR or full-modpack runtime health, does not change the physical provider snapshot health from `UNPROVEN`, and does not constitute F4 real I6 handoff evidence.

## Physical snapshot boundary

The current 2026-09-10 physical snapshot contains GeckoLib 4.9.2, AzureLib 3.1.11, Easy Model Entities 2.3.0 and Entity Model Features 3.3.5. Photon 2.2.6.a remains a known runtime-risk VFX candidate; Lodestone 1.8.2 is present but runtime health is unproven; Particle Effects is presentation-only; AAA Particles and AAA Particles World are absent. Presence does not prove API compatibility or runtime health.

The NeoForge native animation profile is different from those provider-mod profiles: its runtime authority is the exact NeoForge 21.1.248 loader itself, not a separate mod discovered in the physical mod snapshot. This does not turn NeoForge presence into proof that a particular exported animation has executed successfully.

## Fidelity and conversion

No cross-profile conversion is implicit. `GeckoLib -> AzureLib`, `GeckoLib -> NeoForge native animation`, `AzureLib -> NeoForge native animation`, `GeckoLib -> Easy Model Entities`, `Easy Model Entities entity -> Easy Model Entities block entity`, `GeckoLib -> EMF/CEM`, `EMF/CEM -> Animated Java`, or any other provider change remains denied until a dedicated adapter defines source preservation, dry-run behavior, semantic/loss report, target constraints and round-trip validation. The source project is never destructively replaced by an inferred conversion.

## Scope boundary

These profiles expose capability resolution only. Later gated deliveries may add audited provider-specific mutation or export handoff while preserving the same profile authority and conversion boundaries. Live Bridge transport, MCP mutation tools, arbitrary extension action invocation and automatic plugin installation remain separately gated capabilities.
