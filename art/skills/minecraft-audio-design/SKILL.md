---
name: minecraft-audio-design
description: Use when designing, implementing, reviewing, or debugging sound for Minecraft spells, abilities, entities, items, machines, ambience, impacts, loops, and other project-owned audio that must remain causally aligned with gameplay and readable in the modpack mix.
source: project-authored-2026-09-07
project_status: preferred
---
# Minecraft Audio Design

## Core principle

Sound is part of the gameplay feedback contract. Map each sound to a real event, give loops an owner and stop condition, preserve server/client authority, and validate the result in the actual modpack mix.

## Authority order

1. exact gameplay/provider event that owns the action;
2. provider-native sound behavior and established sound language when integrating with that provider;
3. project-owned audio direction and neighboring canonical assets;
4. original or properly licensed source assets with recorded provenance;
5. generic vanilla sounds only as an explicit fallback.

Do not rip audio from games, mods, films, music or asset packs whose license does not permit the intended redistribution.

## Required audio event map

For each sound-bearing ability/system, define which of these events actually exist:

- anticipation/start;
- cast/commit/release;
- travel or active loop;
- contact/impact;
- success/resolve;
- fail/cancel/interrupted state;
- decay/tail;
- persistent environmental/idle loop.

A single sound may cover more than one role, but every role must be intentional rather than duplicated by several listeners.

## Spell sound layering

For polished spell presentation, consider these layers without requiring all of them:

- transient attack for timing/readability;
- tonal/body layer that carries school/material identity;
- movement/air/energy layer for travel;
- impact transient and optional debris/resonance layer;
- tail/reverb/decay that matches environment and scale.

Layer count is not a quality metric. Prefer a small number of distinct, readable layers over loud stacking.

## Variation and repetition

- Use pitch/variant randomization only when it preserves identity and does not make timing ambiguous.
- Repeated rapid events should avoid obvious machine-gun repetition when the provider/backend supports variants safely.
- Loops require start, ownership, refresh policy and stop/fade behavior.
- Do not start a new loop every tick.
- Do not assume vanilla attenuation, category, distance or volume values are appropriate; verify the exact API/provider behavior and test in-game.

## Multiplayer causality

- Decide whether the provider already broadcasts/plays the sound before adding networking.
- One authoritative gameplay action should yield one audible event per intended listener.
- Avoid server broadcast plus independent client replay of the same cue.
- Cosmetic local-only sounds are permitted only when they do not misrepresent gameplay state to the player.
- Persistent sounds tied to entities/blocks must stop on removal, unload, death, logout, dimension transition or other owner termination when applicable.

## Accessibility and mix

Review:

- whether critical gameplay information is also available visually and not encoded only in sound;
- category/routing so users can control the sound through appropriate volume settings;
- relative loudness against combat, ambience, UI and provider-native spell sounds;
- fatigue from frequent casts/repetitive loops;
- stereo/spatial readability in first and third person;
- whether low-frequency/high-frequency content masks other important cues.

Do not normalize or amplify assets blindly. Perceived loudness must be evaluated in the real game mix.

## Source and asset provenance

For every project-owned audio asset, record:

- creator/source;
- license or original-production status;
- modification/processing performed;
- intended redistribution scope;
- filename/resource identity;
- whether attribution is required.

Generated audio is not automatically rights-clear. Record the generator/provider terms applicable at creation time when generated assets are used.

## Hard gates

- No invented sound event/resource/API path.
- No client-only audio class reachable on dedicated server.
- No sound event used as gameplay authority.
- No duplicate playback caused by multiple listeners or prediction + authoritative replay.
- No unowned infinite loop.
- No final approval in isolation from the modpack mix.
- No third-party audio without compatible redistribution rights.

Use `standards/AUDIO-QA.md` for acceptance. For spells, combine this skill with `minecraft-spell-vfx-engineering` and `standards/SPELL-PRESENTATION-CONTRACT.md`.

If the user must operate an audio editor or another GUI, follow `../../USER-GUIDED-WORKFLOW.md`: one manual action, verify the result, then continue.
