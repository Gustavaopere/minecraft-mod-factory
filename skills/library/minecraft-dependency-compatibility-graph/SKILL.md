---
name: minecraft-dependency-compatibility-graph
description: Use when mapping Minecraft mod dependencies, optional integrations, libraries, compatibility addons, missing requirements, version ranges, or relationships across a large NeoForge modpack.
---

# Minecraft Dependency and Compatibility Graph

## Workflow
1. Normalize installed mod IDs and versions.
2. Separate libraries/APIs from gameplay mods.
3. For each mod, map:
   - required dependencies;
   - optional dependencies;
   - incompatibilities;
   - loader/Minecraft constraints;
   - compatibility addons.
4. Resolve version ranges.
5. Detect:
   - missing required dependency;
   - duplicate provider;
   - incompatible range;
   - obsolete library;
   - unnecessary compat addon;
   - missing useful compat addon.
6. Build graph edges:
   - REQUIRES;
   - OPTIONAL;
   - INTEGRATES_WITH;
   - CONFLICTS_WITH;
   - REPLACES;
   - FORK_OF.
7. Prioritize issues that can actually break startup/runtime.

## Output
- dependency graph summary;
- critical missing/conflicting edges;
- recommended compatibility addons;
- safe removals;
- items needing research.

## Hard Constraints
Same category is not dependency.
Do not classify an optional integration as mandatory.
Verify exact Minecraft/loader versions.
