---
name: minecraft-narrative-authoring
description: Use when creating, reviewing, structuring or validating Minecraft campaign lore, NPCs, quests, factions, locations, events, evidence, dialogues, relationships, progression arcs or epilogues while preserving project-specific canon and runtime authorities.
source: project-authored-2026-09-13
project_status: preferred
---
# Minecraft Narrative Authoring

## Core principle

The Factory owns reusable authoring capability. The consumer repository owns its campaign content and runtime-specific truth.

Never move a project's canon into the Factory and never infer mechanics from lore.

## Authority protocol

Before writing:

1. read the consumer project's narrative profile and project instructions;
2. identify the authority for structured lore/Campaign Bible, if any;
3. inspect the consumer repository's accepted story content and relevant open proposals;
4. inspect runtime/provider contracts when a narrative consequence depends on executable mechanics;
5. fail closed when a required authority is unavailable rather than filling canon by assumption.

Project-specific authority order is configuration, not a Factory global.

## Authoring workflow

1. Inventory existing story records before allocating a new ID.
2. Reconcile existing canon/knowledge/provenance before writing new facts.
3. Choose the generic template that matches the record type.
4. Keep objective world state separate from what a character/player knows.
5. Keep relationships multidimensional when the consumer runtime supports that distinction.
6. Treat discovery, offer/engagement and resolution as separate axes when the consumer project defines them separately.
7. Store generated campaign content only in the consumer repository.
8. Run story and dialogue validators.
9. Use spoiler-safe output by default; use `--reveal` only during deliberate editorial debugging.
10. Review diffs and project-specific authorities before promotion to canon.

## Hard gates

- Do not allocate IDs without checking the current inventory.
- Do not create duplicate declarations in auxiliary notes/asset briefs.
- Do not invent provider capabilities, biomes, APIs or runtime transitions from narrative prose.
- Do not give NPCs knowledge without provenance.
- Do not collapse rumor, evidence, memory, belief and objective truth into one field.
- Do not use a transient workflow phrase such as "proposed until merge" as a stable editorial state when the project defines stable categories.
- Do not expose spoilers in status/validation output by default.
- Do not make paid APIs or temporary trials a required authoring dependency unless the consumer project explicitly opts in.

## Visual handoff

For NPC concepts/skins/models, hand off to the Factory art domain:

- `../../../art/skills/minecraft-asset-art-direction/SKILL.md`
- `../../../art/skills/minecraft-blockbench-geckolib/SKILL.md`
- `../../../art/skills/minecraft-visual-qa/SKILL.md`

Concept art is not a final Minecraft asset.
