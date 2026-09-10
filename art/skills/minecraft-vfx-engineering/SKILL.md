---
name: minecraft-vfx-engineering
description: Use when designing, implementing, reviewing, or debugging Minecraft VFX for spells, mobs, bosses, explosions, environments, corruption, hazards, technology, weapons, impacts, trails, beams, particles, or screen feedback.
source: project-authored-2026-09-08
project_status: preferred
---
# Minecraft VFX Engineering

## Core principle

VFX is a causal presentation layer around a real event, not a second gameplay engine. Begin with the owner/event, then make timing, hierarchy, cleanup, synchronization and performance explicit.

## Canonical lifecycle

`ANTICIPATION -> CHARGE -> RELEASE -> TRAVEL/ACTIVE -> IMPACT -> LINGER -> DECAY`

Not every effect needs every phase. Omissions are deliberate and documented.

## Backend order

1. provider-native effect facilities when they already own the event;
2. vanilla/NeoForge primitives for small/simple presentation;
3. Photon for project-owned authored effects when timelines/trails/beams/materials/post processing justify it;
4. AAA Particles/Effekseer when an Effekseer-authored effect is deliberately selected and the exact installed version/API/assets are verified.

Do not run Photon and AAA as two independent pipelines for the same causal event without a documented reason.

## Required design fields

Use `../../templates/VFX-BRIEF.md` and define:

- owner/event and authoritative boundary;
- visual language/palette/material;
- lifecycle phases;
- source/target/attachment points;
- backend + exact-version proof;
- sync/dedup policy;
- owner and cleanup lifecycle;
- accessibility/reduced-effects behavior where supported;
- expected concurrency and profiling scenario;
- provenance/licence;
- QA scenes.

## Causality and multiplayer

- One authoritative event produces one intended presentation sequence per viewer.
- Prediction may preview presentation only when compatible with the provider contract; prediction never applies gameplay state.
- Avoid server broadcast + independent client replay duplication.
- Persistent effects require one owner, refresh policy and termination condition.
- Define cleanup for relevant cancel, death, logout, dimension change, entity removal, chunk unload/reload and server stop paths.
- Dedicated server must not classload client-only renderer/VFX classes.

## Composition

Quality comes from readable layering, not particle count. Prefer primary shape/motion, secondary accents and controlled detail. Preserve target/HUD/world readability. Emissive, distortion, screenshake and post effects are accents with a purpose, not default polish buttons.

## Performance

Do not invent universal particle or GPU budgets. Validate the expected real concurrency on the actual modpack. Review lifetime, spawn rate, transparency/overdraw, trail/beam segmentation, dynamic lights/shaders, post effects, simultaneous viewers/casters and cleanup.

## Hard gates

- No invented provider/Photon/AAA class or signature.
- No VFX event as gameplay authority.
- No duplicate predicted + authoritative spawn.
- No unowned persistent effect.
- No final approval from editor preview alone.
- No third-party VFX asset without compatible provenance.

Use `minecraft-visual-qa` plus `standards/VFX-QA.md` for acceptance. For spell-specific production, combine with `minecraft-spell-production`.
