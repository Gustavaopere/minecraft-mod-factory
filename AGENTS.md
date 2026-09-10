# AGENTS.md — Minecraft Mod Factory

This repository is the canonical control plane for reusable Minecraft mod engineering and artistic infrastructure.

Before changing it:

1. read `STATUS.md`;
2. read the canonical plans under `plans/` once materialized;
3. verify the current physical modlist source, GitHub HEAD, open branches/PRs and migration boundary;
4. do not reimplement work already proven in the historical source repository;
5. do not invent APIs, versions, providers, paths or repository state;
6. preserve source asset formats such as `.bbmodel`; conversions between pipelines must be explicit;
7. keep mod-specific runtime code and data in the corresponding mod repository;
8. keep RPG-specific runtime/modlist material in `Gustavaopere/neoforge-rpg-skilltree` unless an explicit migration matrix classifies an item as reusable;
9. migrate reusable infrastructure in reviewable waves with tests and provenance;
10. when a user must perform a manual action, request one step at a time and wait for its result.

The repository layout is intentionally established by the migration program rather than copied blindly from historical `PROJECT-INSTRUCTIONS/` paths.
