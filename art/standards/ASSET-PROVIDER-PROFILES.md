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
- `geckolib4_entity`, `geckolib4_item`, `geckolib4_block`, `geckolib4_armor` — GeckoLib 4.9.2 with `geckolib` 4.2.5.
- `azurelib_entity`, `azurelib_item`, `azurelib_block`, `azurelib_armor` — AzureLib 3.1.11 with `azurelib_utils` 2.1.5.
- `emf_cem_entity` — Entity Model Features 3.3.5 with CEM Template Loader 9.2.0. EMF Animation Addon 1.0.5 is preferred, not a hard requirement.
- `animated_java_display_entities` — Animated Java 1.10.2 authoring/export pipeline. It deliberately has no invented physical runtime-mod requirement.

## Physical snapshot boundary

The current 2026-09-08 physical snapshot contains GeckoLib 4.9.2, AzureLib 3.1.11 and Entity Model Features 3.3.5. Photon 2.2.6.a remains a known runtime-risk VFX candidate; Lodestone 1.8.2 is present but runtime health is unproven; Particle Effects is presentation-only; AAA Particles and AAA Particles World are absent. Presence does not prove API compatibility or runtime health.

## Fidelity and conversion

No cross-profile conversion is implicit. `GeckoLib -> AzureLib`, `GeckoLib -> EMF/CEM`, `EMF/CEM -> Animated Java`, or any other provider change remains denied until a dedicated adapter defines source preservation, dry-run behavior, semantic/loss report, target constraints and round-trip validation. The source project is never destructively replaced by an inferred conversion.

## Scope boundary

These profiles expose capability resolution only. PR1 does not implement provider-specific mutation, exporters, Live Bridge transport, MCP mutation tools, arbitrary extension action invocation or automatic plugin installation. Those belong to later gated deliveries.
