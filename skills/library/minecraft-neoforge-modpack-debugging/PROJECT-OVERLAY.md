# Project overlay — minecraft-neoforge-modpack-debugging

## Primary debugging target
Minecraft **1.21.1 / NeoForge 21.1.x / Java 21** with the latest physical modpack snapshot.

## Overrides
- Confirm actual loader/mod versions from metadata/JARs; do not diagnose from filenames alone when metadata is available.
- Classify dependency, mixin, registry, sidedness, config, world-data and provider failures separately.
- Use exact logs/crash reports and preserve minimal reproduction evidence.
- Do not recommend Fabric/Forge/Paper fixes unless the failing component actually belongs to that environment.

## Authority
`../../VERSION-AUTHORITY.md`, physical modlist/JARs, current configs/logs and exact upstream evidence.
