# Project overlay — minecraft-world-generation

## Active project target
Minecraft **1.21.1 / NeoForge 21.1.x** worldgen and compatible data-driven resources.

## Overrides
- Worldgen JSON/registry/biome-modifier APIs must be verified for 1.21.1; 1.21.10/1.21.11 examples are not authority.
- Prefer data-driven formats where they satisfy the requirement; use NeoForge runtime code only where necessary.
- Validate deterministic placement, reloadability where applicable, dedicated-server behavior, dimensions/biomes/structures and compatibility with installed worldgen mods.

## Authority
Current mod repository, exact NeoForge/vanilla 1.21.1 behavior, installed provider/mod JARs and `../../VERSION-AUTHORITY.md`.
