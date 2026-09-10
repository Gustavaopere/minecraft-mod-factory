---
name: modpack-inventory-redundancy-audit
description: Use when auditing a large Minecraft modlist for duplicate mods, forks, ports, continued versions, overlapping functionality, obsolete libraries, compatibility addons, or modpack inventory state.
---

# Modpack Inventory and Redundancy Audit

## Platform Constraint
Default only to the platform explicitly supplied by the user. For Gustavo's current pack, preserve Minecraft 1.21.1 + NeoForge when that context applies.

## Workflow
1. Normalize filenames.
2. Extract likely mod names, IDs, and versions.
3. Separate:
   - content mods;
   - libraries/APIs;
   - compatibility addons;
   - resource/data packs;
   - client-only utilities.
4. Detect lineage signals:
   - fork;
   - port;
   - unofficial;
   - continued;
   - redux;
   - reborn;
   - maintained fork;
   - compatibility fork.
5. Distinguish:
   - true duplicate;
   - successor/replacement;
   - complementary overlap;
   - same category but different mechanics.
6. Check current maintained status and exact loader/version.
7. Map required and optional dependencies.
8. Identify compatibility addons that are relevant to the installed set.
9. Flag obsolete/unsupported items.
10. Produce keep/remove/replace/investigate recommendations with evidence.

## Hard Constraints
- Same category does not equal redundancy.
- Multiple complementary mods are acceptable.
- Do not remove a library simply because it has no visible gameplay.
- Do not recommend a replacement without checking current version/loader support.
