# Project overlay — minecraft-modpack-bisect

## Active project target
The current large Minecraft **1.21.1 / NeoForge** modpack.

## Overrides
- Start from the latest physical modlist, logs and reproduction evidence.
- Preserve dependencies and known required library/compatibility clusters while bisecting; do not remove a required dependency and misclassify the resulting failure.
- Back up world/config before destructive tests.
- Separate client-only, server-only and both-sides failures.

## Authority
Physical modlist/JARs, current configs/logs and `../../VERSION-AUTHORITY.md`.
