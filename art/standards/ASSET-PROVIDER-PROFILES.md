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
- `emf_cem_entity` — Entity Model Features 3.3.5 with CEM Template Loader 9.2.0. The runtime authority is `Traben-0/Entity_Model_Features@02034eb0f102040b16900be7c900eff88da89e9e`; its `1.21-neoforge` subproject is built upstream against NeoForge 21.0.167 while the Factory target remains NeoForge 21.1.248. The physical dependency Entity Texture Features 7.2.1 satisfies EMF's declared ETF minimum 7.2.0. Authoring authority is Blockbench 5.1.6 at `JannisX11/blockbench@794e964e966b6783b4e9b98ecbdda5152c0620cc`, using the built-in `optifine_entity` JEM and `optifine_part` JPM codecs. `.bbmodel` remains source authority. Export mode is explicit: OptiFine-compatible output stages under `assets/<namespace>/optifine/cem`, while EMF-only output stages under `assets/<namespace>/emf/cem`; flat versus per-entity subfolder layout is also explicit. EMF Animation Addon 1.0.5 is preferred rather than globally required, and is required by the handoff only when the selected animation dialect is EMF-only. No GeckoLib/AzureLib conversion is implied.
- `animated_java_display_entities` — Animated Java 1.10.2 at `Animated-Java/animated-java@a5fc548d2a53cc0887fa070db33ccfcef1cd3541`, with official release asset `animated_java.js` SHA-256 `81aadc4def796d97dab6642ad05b564b470ecadcaf455c8cc5826c9e24759672`. The official Blockbench catalog marks it desktop-only with `min_version=5.1.4`; the Factory audit baseline is Blockbench 5.1.6 at `JannisX11/blockbench@794e964e966b6783b4e9b98ecbdda5152c0620cc`. `.ajblueprint` is the source authority and the audited format/codec IDs are `animated-java:format/blueprint` and `animated_java:codec/blueprint`. PR11 is pinned to Minecraft 1.21.1, which falls in the upstream compiler bucket `>=1.21.0` and `<1.21.2`. The Factory inspects variants, locators, cameras and function/variant keyframe channels without mutating source. Datapack/resource-pack export modes are explicitly `folder`, `zip` or `none`; plugin JSON mode is not part of the PR11 contract and fails closed. The audited model/texture roots are `assets/<namespace>/models/blueprint/<path>` and `assets/<namespace>/textures/blueprint/<path>`. The profile deliberately has no invented physical runtime-mod requirement and no implicit provider conversion.
- `cpm_player_model` — Customizable Player Models 0.6.27a player-model runtime with the audited Blockbench `cpm_plugin` path. `.cpmproject` remains source authority. The Blockbench plugin is beta/experimental and classified `HUMAN_ONLY`; Factory automation may preview the preserved-source handoff but does not install the plugin, does not MCP-authorize it, and does not claim an automated lossless import/export round-trip. Human confirmation remains mandatory.
- `player_animation_library_player` — Player Animation Library `1.1.6+mc.1.21.1` runtime-consumer profile. The proven Factory handoff accepts JSON and stages it only under `assets/<namespace>/player_animations/<file>.json`, preserving source and treating the animation identifier as runtime-owned internal data. No Blockbench plugin is invented for PAL.
- `player_animator_player` — Player Animator `2.0.4+1.21.1` runtime/API profile. The audited public surface is `PlayerAnimationAccess`, `PlayerAnimationFactory` and `PlayerAnimationRegistry`, with layered APIs including `AnimationStack` and `ModifierLayer`. The NeoForge mod metadata declares the Minecraft dependency with `side=BOTH`; separately, `PlayerAnimationRegistry` is client-environment code and reloads `assets/<namespace>/player_animations/*`, retaining legacy `player_animation` loading with warning. Its default JSON codecs are `emotecraft` followed by `gecko_legacy`. This profile is distinct from PAL and does not imply PAL equivalence or automatic PAL conversion.

## Easy Model Entities runtime evidence boundary

PR9 target-exact source runtime validation uses the pinned Easy Model Entities 2.3.0 source revision `8c912371838c2a26bbb383008ad3999280f075d1`, Java 21, Minecraft 1.21.1 and NeoForge 21.1.248. The source registers the entity spawn-item and block spawn/place GameTests, and the NeoForge GameTest server executed all 15 required Easy Model Entities tests successfully in Factory run `34621675116`.

The upstream 2.3.0 build was originally pinned to NeoForge 21.1.92 and forced ASM 9.7. NeoForge 21.1.248 bootstraps ASM 9.10.1, so the Factory smoke aligns only those ASM build-tool pins to 9.10.1 inside the ephemeral CI checkout before launching `:NeoForge:runGameTestServer`. No upstream source/runtime file is committed back or silently rewritten as a production artifact.

This evidence is `TARGET_EXACT_SOURCE_GAMETEST_PASS`. It proves the pinned 2.3.0 source GameTest suite can compile, launch and pass on NeoForge 21.1.248 under the documented ephemeral build-harness adaptation. It does **not** prove the physical modpack JAR or full-modpack runtime health, does not change the physical provider snapshot health from `UNPROVEN`, and does not constitute F4 real I6 handoff evidence.

## EMF/CEM evidence boundary

PR10 pins the physical EMF 3.3.5 provider and ETF 7.2.1 dependency, the exact EMF 3.3.5 source revision, Blockbench 5.1.6 codecs, CEM Template Loader 9.2.0 source revision `ewanhowell5195/blockbenchPlugins@bdea1d6c5e8f9fca3dbbeb446e568adb025b5ef2`, and the official catalog EMF Animation Addon 1.0.5 reference `JannisX11/blockbench-plugins@38862eb66b219995b09926488f7d1084a0fb6b3a`.

The physical artifact is `entity_model_features-3.3.5-1.21-neoforge.jar`. The pinned source exposes a `1.21-neoforge` subproject rather than a dedicated `1.21.1-neoforge` subproject and pins that source build to NeoForge 21.0.167. Factory diagnostic run `34629620625`, job `103362965564`, built that exact source/subproject successfully on Java 25 with `:1.21-neoforge:build --configure-on-demand`. This evidence is `UPSTREAM_SOURCE_BUILD_PASS`; it proves the audited source authority builds in its own declared Minecraft 1.21 / NeoForge 21.0.167 configuration.

The same diagnostic attempted an ephemeral NeoForge override from 21.0.167 to the Factory loader 21.1.248. Loom rejected configuration before EMF compilation because NeoForge 21.1.248 is for Minecraft 1.21.1 while the audited source subproject is Minecraft 1.21. This result is `TARGET_OVERRIDE_SOURCE_BUILD=BLOCKED_BY_PLATFORM_VERSION_MISMATCH`, not an EMF code-compilation failure and not target-exact evidence. The Factory does not suppress that mismatch with `loom.allowMismatchedPlatformVersion` and does not relabel a mismatched build as target-exact.

The Factory adapter validates an audited conservative JEM/JPM subset, preserves native Blockbench `shadowSize` output rather than silently rewriting provider semantics, requires the compatibility root/layout/animation dialect to be selected explicitly, and keeps EMF-only fields behind the EMF dialect. The standalone bundle and adapter tests prove this handoff contract. Neither the upstream source build nor the blocked override proves that the physical JAR loads correctly in the Minecraft 1.21.1 / NeoForge 21.1.248 full pack, nor that a staged CEM model or animation renders in a live client. `runtimeEvidence=UNPROVEN`, `runtimeValidated=false`, physical-provider health remains `UNPROVEN`, and no F4 real I6 handoff evidence is claimed.

## Animated Java evidence boundary

PR11 pins Animated Java 1.10.2 source and release provenance, its desktop-only Blockbench catalog contract, the `.ajblueprint` authoring format, exact Minecraft 1.21.1 target, the datapack/resource-pack staging contract, and the source-preserving Blockbench/standalone Factory adapters. The contract tests also prove read-only awareness of variants, locators, cameras and function/variant keyframe channels. Plugin installation remains human-controlled, and plugin JSON mode is deliberately excluded until a separate audited contract exists.

Factory run `34638984175`, job `103393743390`, generated the canonical Java 21 / NeoForge 21.1.248 smoke project and executed one required GameTest on Minecraft 1.21.1. The server loaded namespace `i3_golden_mod`, ran `function factorypr11:smoke/summon`, verified the summoned `minecraft:item_display`, and reported `All 1 required tests passed`. This evidence is `TARGET_EXACT_DATAPACK_DISPLAY_ENTITY_GAMETEST_PASS`.

That smoke proves the target-exact vanilla datapack/display-entity runtime primitive used by the audited PR11 handoff. It does **not** prove that Animated Java 1.10.2 itself generated the exercised datapack/resource pack, that a real `.ajblueprint` export rendered correctly in a client, or that the complete physical modpack loaded the staged output. Therefore the handoff remains `runtimeEvidence=UNPROVEN`, `runtimeValidated=false`, `f4I6Evidence=false`, and no F4 real I6 handoff evidence is claimed.

## Player profile evidence boundary

PR12 pins the physical player-profile providers exactly to CPM `0.6.27a`, Player Animation Library `1.1.6+mc.1.21.1`, and Player Animator `2.0.4+1.21.1`. CPM release provenance is `tom5454/CustomPlayerModels@9dcde8fb511ed0b8be5558defb1a577ce013600b`, with the Blockbench integration audited at `9272f4f9c36a2bbd6986e6da65bf7091369cb12b`; PAL is audited at `PlayerAnimationLibrary/PlayerAnimationLibrary@10e019f89fa25d0cd6f50fb8768586a969106911`; Player Animator is audited at `KosmX/minecraftPlayerAnimator@cb3227efc19ec46065597332ae265076d0f2b495`.

The CPM contract preserves a saved `.cpmproject`, pins Minecraft 1.21.1, requires human confirmation, and explicitly records `automatedLosslessRoundTripProven=false`. The Factory Blockbench bridge only previews this handoff and never installs the CPM plugin. The PAL contract stages JSON only below `assets/<namespace>/player_animations/` and records the runtime key source as the animation internal identifier. For Player Animator, the audited NeoForge metadata declares runtime side `BOTH`, while `PlayerAnimationRegistry` is client-environment code responsible for resource reload under `player_animations`, with `player_animation` retained only as a legacy fallback. The Factory records those two scopes separately as `runtimeSide=BOTH` and `resourceRegistrySide=CLIENT`, and records default codec order `emotecraft`, then `gecko_legacy`, without treating PAL as an equivalent runtime.

These are contract and handoff proofs, not provider-real runtime proofs. PR12 does not claim that the CPM plugin completed a lossless real project round-trip, that PAL consumed a staged animation in a live target client, that Player Animator played a staged animation, or that the complete physical modpack loaded these paths together. The canonical PR12 APIs therefore retain `runtimeEvidence=UNPROVEN`, `runtimeValidated=false`, `f4I6Evidence=false`; F4 real I6 handoff remains incomplete and I7 remains blocked.

## Physical snapshot boundary

The current 2026-09-11 physical snapshot contains GeckoLib 4.9.2, AzureLib 3.1.11, Easy Model Entities 2.3.0, Entity Model Features 3.3.5, Customizable Player Models 0.6.27a, Player Animation Library 1.1.6+mc.1.21.1 and Player Animator 2.0.4+1.21.1. Photon 2.2.6.a remains a known runtime-risk VFX candidate; Lodestone 1.8.2 is present but runtime health is unproven; Particle Effects is presentation-only; AAA Particles and AAA Particles World are absent. Presence does not prove API compatibility or runtime health.

The NeoForge native animation profile is different from those provider-mod profiles: its runtime authority is the exact NeoForge 21.1.248 loader itself, not a separate mod discovered in the physical mod snapshot. This does not turn NeoForge presence into proof that a particular exported animation has executed successfully.

## Fidelity and conversion

No cross-profile conversion is implicit. `GeckoLib -> AzureLib`, `GeckoLib -> NeoForge native animation`, `AzureLib -> NeoForge native animation`, `GeckoLib -> Easy Model Entities`, `Easy Model Entities entity -> Easy Model Entities block entity`, `GeckoLib -> EMF/CEM`, `EMF/CEM -> Animated Java`, or any other provider change remains denied until a dedicated adapter defines source preservation, dry-run behavior, semantic/loss report, target constraints and round-trip validation. The source project is never destructively replaced by an inferred conversion. PAL -> Player Animator, Player Animator -> PAL, CPM -> PAL, CPM -> Player Animator, and the reverse player-profile paths are likewise denied unless a dedicated audited adapter explicitly defines the conversion.

## Scope boundary

These profiles expose capability resolution only. Later gated deliveries may add audited provider-specific mutation or export handoff while preserving the same profile authority and conversion boundaries. Live Bridge transport, MCP mutation tools, arbitrary extension action invocation and automatic plugin installation remain separately gated capabilities.
