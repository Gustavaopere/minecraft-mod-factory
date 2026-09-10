# Project overlay — minecraft-testing

## Active project target
Testing Java **21** code/resources for Minecraft **1.21.1 / NeoForge 21.1.x**.

## Overrides
- Prefer the repository's JUnit and NeoForge GameTest setup.
- MockBukkit/Fabric GameTest examples are reference-only unless a separate target explicitly requires them.
- For changes that touch runtime initialization, networking, persistence, worldgen or sided code, include the applicable dedicated-server/multiplayer boundary test.
- Test success does not replace visual QA for artistic assets.

## Authority
Current Gradle test configuration, canonical engineering test contracts and `../../VERSION-AUTHORITY.md`.
