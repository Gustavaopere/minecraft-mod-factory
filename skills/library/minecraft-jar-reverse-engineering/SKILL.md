---
name: minecraft-jar-reverse-engineering
description: Use when a Minecraft mod JAR must be inspected, compared, patched, or understood because source is unavailable, metadata is unclear, dependencies or mixins are suspect, or binary compatibility must be investigated.
---

# Minecraft JAR Reverse Engineering

## Core Rule
Prefer upstream source when available. Reverse engineer only what is necessary for the specific question.

## Workflow
1. Hash the JAR.
2. Read manifest and mod metadata.
3. Extract:
   - mod ID;
   - version;
   - loader constraints;
   - Minecraft range;
   - dependencies.
4. Inspect mixin configs.
5. Map packages/classes relevant to the observed failure.
6. Decompile only targeted classes when needed.
7. Compare symbols/calls against dependency/API versions.
8. Search upstream source/release history for matching code.
9. Identify the smallest patchable incompatibility.
10. Rebuild only when toolchain and licensing/source conditions permit.
11. Re-test the original failure.

## Watch For
- removed methods/classes;
- descriptor/signature changes;
- mappings mismatch;
- mixin targets moved;
- dependency range too strict/loose;
- metadata-only incompatibility;
- client-only references on server path.

## Output
- JAR identity;
- relevant metadata;
- failing class/symbol;
- compatibility finding;
- patch feasibility;
- safest next step.
