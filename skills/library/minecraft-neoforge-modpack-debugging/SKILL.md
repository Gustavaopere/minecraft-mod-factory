---
name: minecraft-neoforge-modpack-debugging
description: Use when investigating Minecraft Java 1.21.1 NeoForge crashes, incompatibilities, dependencies, modlists, logs, crash reports, JARs, mixins, registries, configuration issues, or choosing the least destructive modpack fix.
---

# Minecraft NeoForge Modpack Debugging

## Overview

Investigate the causal chain of a heavily modded Minecraft 1.21.1 NeoForge installation before recommending removals, downgrades, patches, or replacements.

Hard platform constraint:

**Minecraft Java 1.21.1 + NeoForge.**

Do not silently substitute Forge, Fabric, or 1.20.1 guidance.

## Core Rule

**No mod removal or downgrade recommendation before root-cause investigation and current-version compatibility research.**

The mod named last in a crash report may be a victim, caller, compatibility layer, or downstream failure rather than the origin.

## Intake

Inventory all supplied evidence before diagnosis:

- `latest.log`;
- `debug.log`;
- crash reports;
- stdout;
- Crash Assistant reports;
- modlist;
- screenshots;
- configs;
- JAR files;
- launcher/runtime information;
- recent mod additions/removals/updates.

State explicitly if an expected file is missing.

## Crash Workflow

### 1. Establish chronology

Find:

- startup phase;
- first relevant ERROR/FATAL;
- first exception in the causal chain;
- later cascading errors;
- final crash wrapper.

Do not begin from the final `Caused by` line alone if earlier evidence exists.

### 2. Classify the failure

Classify into one or more:

- missing dependency;
- wrong dependency version;
- loader/version mismatch;
- API incompatibility;
- binary incompatibility;
- Mixin failure;
- registry error;
- datapack/resource loading error;
- client/server side mismatch;
- rendering/graphics incompatibility;
- JEI/REI/EMI integration;
- worldgen conflict;
- config error;
- duplicate/fork/port collision;
- classloading issue;
- upstream mod bug;
- compatibility addon bug;
- unknown.

### 3. Build the causal chain

Record:

`trigger → calling mod → API/library → failing symbol/class/mixin/registry → crash`

Identify:

- primary suspect;
- secondary participants;
- likely victims;
- unrelated warnings.

### 4. Check recent changes

Correlate with:

- newly added mods;
- removed mods;
- version updates;
- changed configs;
- changed Java/runtime;
- changed resource/data packs.

### 5. Research current compatibility

For every material suspect, verify current information from appropriate sources:

1. official project page;
2. releases/changelog;
3. GitHub source/issues/PRs;
4. Modrinth/CurseForge metadata;
5. user comments/discussions only as secondary evidence.

Confirm:

- exact Minecraft version;
- exact loader;
- exact mod version;
- dependency ranges;
- known incompatibilities;
- current upstream fix;
- maintained fork/port;
- whether a downgrade is actually necessary.

Do not invent a port, fork, release, or compatibility claim.

### 6. Form a single hypothesis

Write:

`Hypothesis: X causes the failure because Y evidence links X to Z.`

Then identify what evidence would falsify it.

### 7. Choose the least destructive fix

Preference order:

1. configuration correction;
2. missing compatibility addon/dependency;
3. update to fixed current release;
4. replace obsolete fork/port with maintained equivalent;
5. minimal local patch;
6. temporary removal of the smallest offending component;
7. downgrade only when current-version options have been exhausted and evidence supports it.

Preserve the user's chosen mod ecosystem whenever reasonably possible.

### 8. Validate

After a change, compare a fresh run against the original failure.

A successful launch alone does not prove a compatibility issue is solved if the failure was runtime-specific. Reproduce the original trigger when possible.

## Compatibility Questions

For "can A and B coexist?" investigate:

- declared compatibility;
- overlapping hooks/mixins;
- worldgen or registry ownership;
- shared libraries/APIs;
- known issues;
- current version pair;
- compatibility addons;
- configuration burden.

Return one of:

- COMPATIBLE;
- COMPATIBLE WITH CONDITIONS;
- UNVERIFIED;
- KNOWN CONFLICT;
- REDUNDANT/SUBSTITUTIVE;
- COMPLEMENTARY.

Do not call two mods redundant merely because they share a category.

## Mod Comparison

Compare at minimum:

- maintained status;
- Minecraft/NeoForge compatibility;
- content depth;
- configuration burden;
- integration with installed pack;
- overlap vs complementarity;
- known regressions;
- visual/UX quality when relevant;
- required addons.

A more feature-rich mod can still be the worse choice if it destabilizes the pack.

## Modpack Audit

For large modlists:

1. Normalize JAR names.
2. Extract mod IDs and versions where possible.
3. Group libraries/APIs separately.
4. Detect forks/ports/continued/redux/reborn variants.
5. Detect obvious duplicates.
6. Map mandatory dependencies.
7. Map optional integrations.
8. Flag unsupported Minecraft/loader versions.
9. Flag abandoned components with maintained successors.
10. Separate functional overlap from true substitution.

## JAR Investigation

When a JAR is supplied and analysis is justified:

1. calculate hash;
2. inspect metadata;
3. identify mod id/version;
4. inspect dependency declarations;
5. inspect mixin configs;
6. inspect packages/classes relevant to the failure;
7. compare against upstream source when available;
8. identify the smallest viable change;
9. rebuild only when source/build tooling supports it;
10. validate the rebuilt artifact.

Prefer source code over decompilation when source is available.

## Bisect Workflow

Use when evidence implicates an interaction but not a specific pair.

- Keep core loader/API dependencies fixed.
- Split optional suspects into groups.
- Test one controlled subset at a time.
- Record every run.
- Do not randomly remove unrelated mods.
- Narrow until the minimal failing combination is identified.

## Required Diagnostic Output

### Root cause
State only what evidence supports.

### Evidence
List key log lines/files, versions, issues, or source findings.

### Causal chain
Explain which mod is origin, participant, and victim.

### Fix
Give the least destructive supported correction.

### Alternatives
Include fallback options and their tradeoffs.

### Validation
State exactly what should be retested.

### Confidence
Use high / medium / low and explain material uncertainty.

## Hard Constraints

- Minecraft 1.21.1.
- NeoForge.
- Verify exact mod versions.
- Do not present Forge/1.20.1 solutions as equivalent.
- Preserve mods when a reasonable compatibility fix exists.
- Research before recommending downgrade.
- Do not invent compatibility.
- Distinguish warning from fatal error.
- Distinguish cause from downstream symptom.
- Consider all supplied files when they matter.
- Consult more than one source when reliable sources disagree.
- Do not recommend mods already installed as if they were new.
- Configuration burden matters.
- Multiple complementary mods are acceptable.
