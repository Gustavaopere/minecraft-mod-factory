# Project overlay — minecraft-datapack

## Active project target
Vanilla data formats compatible with Minecraft **1.21.1**, consumed by NeoForge **21.1.x** mods/datapacks.

## Overrides
- Never copy pack formats, component schemas, paths, recipe/loot/advancement syntax or registry behavior from later 1.21.x releases without proof for 1.21.1.
- Runtime data owned by an individual mod stays authoritative in that mod repository; the integration repository may host reusable contracts/tooling only when intended.
- Validate namespace, resource location, reload behavior and server/client boundary against the actual target.

## Authority
Use `../../VERSION-AUTHORITY.md`; repository/JAR/runtime evidence outranks generic source examples.
