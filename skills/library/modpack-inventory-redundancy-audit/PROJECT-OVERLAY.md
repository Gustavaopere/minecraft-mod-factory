# Project overlay — modpack-inventory-redundancy-audit

## Active project target
Latest physical Minecraft **1.21.1 / NeoForge** modpack snapshot.

## Overrides
- Audit actual JAR metadata, mod IDs, versions, dependencies and functionality before classifying redundancy.
- Distinguish forks/ports/continued builds from compatibility addons and required libraries.
- Do not remove duplicates solely by filename/name similarity.
- Record evidence and downstream dependency impact before recommending deletion.

## Authority
Physical modlist/JAR metadata, dependency graph, current configs and `../../VERSION-AUTHORITY.md`.
