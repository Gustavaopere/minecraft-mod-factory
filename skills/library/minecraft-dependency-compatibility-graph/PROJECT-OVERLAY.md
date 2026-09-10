# Project overlay — minecraft-dependency-compatibility-graph

## Active project target
Large Minecraft **1.21.1 / NeoForge 21.1.x / Java 21** modpack.

## Overrides
- The current physical modlist/JAR set is mandatory evidence for presence and version.
- Architectury/Fabric-named libraries may be dependencies used by NeoForge mods; their presence does not change the loader target to Fabric.
- Distinguish required dependency, embedded library, compatibility addon, optional bridge, duplicate/fork and unrelated similarly named mod.
- Never infer compatibility solely from names or latest-version documentation.

## Authority
`../../VERSION-AUTHORITY.md`, physical modlist/JAR metadata, build files and exact provider documentation.
