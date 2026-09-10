---
name: minecraft-spell-production
description: Use when a Minecraft spell or magical ability needs end-to-end production or review across mechanics, casting, animation, models, VFX, audio, feedback, accessibility, synchronization, lifecycle, and performance.
source: project-authored-2026-09-08
project_status: preferred
---
# Minecraft Spell Production

## Core principle

A spell is complete only when its authoritative mechanics and all applicable presentation layers agree on the same causal lifecycle. Do not treat “damage works” or “particles appear” as finished spell production.

## Start with authority

Before presentation work, confirm from exact provider/runtime evidence:

- spell/ability owner;
- targeting semantics;
- resource/mana/cost owner;
- cooldown owner;
- cast/channel timing;
- cancel/interruption semantics;
- damage/effect/world-mutation owner;
- authoritative release/resolve boundaries.

If the provider/hook cannot be confirmed, fail closed and record the implementation component as pending.

## Production stack

Use `../../templates/SPELL-BRIEF.md`. Applicable layers are:

1. mechanical design and authority;
2. cast pose/player animation;
3. model/construct/projectile asset when needed;
4. cast/release/travel/impact/linger VFX;
5. audio event map;
6. camera/hit feedback;
7. accessibility/readability;
8. multiplayer causality/deduplication;
9. lifecycle cleanup;
10. performance/concurrency validation.

## Skill routing

- art/model: `minecraft-asset-art-direction` + `minecraft-blockbench-geckolib`;
- general VFX: `minecraft-vfx-engineering`;
- spell presentation specifics: `minecraft-spell-vfx-engineering`;
- sound: `minecraft-audio-design`;
- final acceptance: `minecraft-visual-qa` + specialized standards.

## Server/client boundary

Gameplay/cost/damage/state stays with the real provider/server authority. Client animation/VFX/audio consumes confirmed lifecycle information or supported prediction. Cosmetic prediction must not mutate gameplay and must reconcile without double playback/spawn.

## Completion gates

A spell cannot be marked complete when an applicable item is missing without an explicit design reason:

- [ ] owner/API/event exact-version proof
- [ ] cost/cooldown/cast semantics
- [ ] cast/resolve/cancel boundaries
- [ ] animation/pose
- [ ] model/attachment contract when needed
- [ ] VFX lifecycle
- [ ] audio cue sheet
- [ ] first-/third-person readability
- [ ] multiplayer dedup/causality
- [ ] cleanup/lifecycle
- [ ] dedicated-server separation
- [ ] concurrency/performance evidence
- [ ] in-game QA

## Hard gates

- No generic particle substitute for a missing provider integration.
- No copied Iron's/third-party code/assets by analogy.
- No visual timing used to infer authoritative hit/damage unless provider contract explicitly says so.
- No final approval solely from editor or singleplayer preview.
