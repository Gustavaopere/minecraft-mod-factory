# Project overlay — minecraft-neoforge-engineering

## Primary engineering skill
This is the preferred implementation skill for Minecraft **1.21.1 / NeoForge 21.1.x / Java 21**.

## Project boundaries
- Read the latest physical modlist, repository state, active branches/PRs, canonical plans and STATUS before implementation.
- Individual mod repositories are the source of truth for their runtime code; `Gustavaopere/minecraft-mod-factory` is the canonical common infrastructure/control-plane repository.
- The Factory `art/` domain is the artistic source of truth for common visual/asset infrastructure; runtime repositories consume validated downstream assets/contracts.
- Preserve dedicated-server, multiplayer, persistence, networking, GameTest/CI and compatibility boundaries.
- Never invent APIs, versions, providers, paths or state.

## Authority
`../../VERSION-AUTHORITY.md` plus canonical engineering plans and exact repository/JAR evidence.
