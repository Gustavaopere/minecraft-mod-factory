---
name: minecraft-spell-vfx-engineering
description: Use when designing, implementing, reviewing, or debugging the presentation layer of Minecraft spells and magical abilities: cast animation, particles, beams, trails, projectiles, impact effects, lingering effects, camera feedback, synchronization, and VFX performance.
source: project-authored-2026-09-07
project_status: preferred
---
# Minecraft Spell VFX Engineering

## Core principle

A spell is not visually complete because its gameplay code works or because particles appear. Preserve gameplay authority, then build one causal presentation lifecycle around that authoritative action.

Canonical presentation phases:

`ANTICIPATION -> RELEASE -> TRAVEL/ACTIVE -> IMPACT/RESOLVE -> DECAY`

Not every spell needs every phase, but omitted phases must be deliberate.

## Authority order

1. exact provider/runtime code and physical JAR for gameplay semantics;
2. provider-native animation/VFX/sound facilities when they can express the required result;
3. project-owned presentation standards and established visual language;
4. confirmed optional VFX backends present in the physical modlist;
5. generic vanilla particles/sounds as an explicit fallback only.

Never replace a real provider integration with a generic particle bonus merely to make an effect visible.

## Current project backends

The physical modlist is authority for presence/version. At the 2026-09-07 snapshot it contains Photon 2.2.6.a, AAA Particles 2.2.3, AAA Particles: World 2.0.0, GeckoLib 4.9.2, and Iron's Spells 'n Spellbooks 3.16.3.

Backend selection:

- **provider-native first** when the provider already owns the cast/projectile/entity/effect and exposes suitable visual hooks;
- **Photon** for project-owned advanced authored effects that benefit from timelines, particles, trails, beams, shader/material graphs, post-processing or packaged FX resources;
- **AAA Particles / Effekseer** when an Effekseer-authored effect is the chosen implementation and the exact AAA API/version has been verified;
- **vanilla/NeoForge rendering primitives** for simple effects that do not justify an external VFX runtime.

The presence of Photon or AAA does not authorize invented Java API calls. Inspect the exact installed JAR/source/documentation before implementation.

## Required spell presentation contract

Before implementing polished VFX, record the fields in `standards/SPELL-PRESENTATION-CONTRACT.md`:

- spell/ability identity and gameplay owner;
- school/theme and approved palette/material language;
- authoritative cast/resolve/cancel boundaries;
- first-person and third-person readability goals;
- anticipation, release, travel/active, impact/resolve and decay behaviors;
- projectile/beam/area/construct model requirements, if any;
- cast/player animation and required attachment points;
- audio event map;
- camera/feedback/accessibility behavior;
- multiplayer synchronization and deduplication strategy;
- dedicated-server/client separation;
- cleanup behavior on cancel, death, logout, dimension change, entity removal, chunk unload and server stop when relevant;
- performance class and expected simultaneous-instance scenario;
- QA scenes and acceptance evidence.

## Causality and synchronization

- Gameplay remains server-authoritative unless the provider explicitly defines otherwise.
- Presentation may predict or preview only when the provider contract supports it; never let a visual prediction apply gameplay state.
- One authoritative action should produce one presentation sequence. Guard against server/client double-spawn, replay and duplicate packet handling.
- Persistent/looping effects must have an explicit owner and stop condition.
- Entity-bound effects must define what happens when the entity despawns, changes dimension, dies or is replaced.
- Seed/random variation should be deterministic across clients when visual agreement matters; do not synchronize every decorative particle if a compact deterministic parameter can reproduce the effect.

## Visual composition

Prefer layered readability over particle count:

- **anticipation:** communicates source, direction and commitment;
- **release:** clear timing accent when gameplay commits;
- **travel/active:** readable trajectory/area with restrained noise;
- **impact/resolve:** communicates contact, affected area and outcome category without obscuring gameplay;
- **decay:** removes energy cleanly instead of popping or lingering indefinitely.

Use `minecraft-asset-art-direction` for palette/material language and `minecraft-blockbench-geckolib` when a spell construct/projectile/entity needs a model or rig.

## Performance and safety

Do not invent universal particle-count or shader budgets. Classify the effect relative to expected concurrency and validate on the real client/modpack.

Required considerations:

- spawn rate, lifetime and overdraw;
- transparent layers and full-screen/post effects;
- trail/beam length and segmentation behavior;
- dynamic lights/shader cost when present;
- simultaneous casts, mobs and multiplayer viewers;
- cleanup after interrupted casts or unloaded owners;
- reduced-particles/accessibility path when the backend/provider exposes one.

## Hard gates

- No invented class, method, event, packet or resource path.
- No client-only class reachable from dedicated-server classloading.
- No visual event may become a second gameplay authority.
- No duplicate cast/impact effect from both prediction and authoritative handling.
- No silent substitution of a provider-native integration with unrelated generic VFX.
- No final approval from editor preview alone; validate in the actual modpack using `standards/VFX-QA.md`.
- No copyrighted/ripped third-party effects or textures without proven redistribution rights.

If the user must operate Photon, Effekseer, Blockbench or another GUI, follow `../../USER-GUIDED-WORKFLOW.md`: one manual action, verify the visible result, then continue.
