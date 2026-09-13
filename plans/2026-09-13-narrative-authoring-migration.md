# Narrative Authoring Migration Plan

Goal: move reusable story-authoring capability from `neoforge-rpg-skilltree` to Minecraft Mod Factory while story content remains in the RPG repository.

Boundary:
- Factory owns reusable narrative skill, tooling, generic templates, profile contract and tests.
- Consumer repos own project profiles, canon/lore, NPCs, quests, factions, locations, evidence, dialogues and runtime-specific authority rules.
- No paid dependency.

Execution:
1. Build profile-driven validators/inventory in `narrative/tooling/` with TDD.
2. Add generic templates and `minecraft-narrative-authoring` skill; route it from `skills/ROUTER.md`.
3. Add Factory CI and migration provenance.
4. Merge Factory PR to `main` after checks.
5. In the RPG, add a project profile and change History Authoring CI to consume a pinned Factory revision.
6. Remove duplicated RPG tooling/templates and close PRs whose scope moved to Factory.
7. Merge surviving RPG content/config changes in dependency order after validation.
