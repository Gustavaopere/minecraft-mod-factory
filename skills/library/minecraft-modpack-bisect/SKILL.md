---
name: minecraft-modpack-bisect
description: Use when a Minecraft crash or incompatibility is reproducible but logs and research cannot isolate the exact interacting mod or minimal failing combination in a large modpack.
---

# Minecraft Modpack Bisect

## Core Rule
Change controlled subsets, preserve mandatory dependencies, and record every run.

## Preparation
1. Define reproducible failure.
2. Preserve:
   - NeoForge;
   - required libraries;
   - world/data needed for reproduction.
3. Freeze Java/config/runtime where possible.
4. Identify candidate optional mods.

## Bisect
1. Split suspects into two balanced groups.
2. Test group A with required dependencies.
3. Record PASS/FAIL.
4. Continue with the failing half.
5. Re-resolve dependencies after every split.
6. Repeat until minimal suspect set remains.
7. Test pairwise/interacting combinations if a single mod does not reproduce.
8. Confirm by re-adding/removing the final suspect.

## Run Ledger
`Run → Mods changed → Dependency adjustments → Result → Error signature`

## Hard Constraints
- Do not remove mandatory dependency chains blindly.
- Do not use a different world/config between runs unless required and recorded.
- Do not treat disappearance of one symptom as proof if a different fatal error replaced it.
