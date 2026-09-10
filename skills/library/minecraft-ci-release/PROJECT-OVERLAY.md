# Project overlay — minecraft-ci-release

## Active project target
- Minecraft **1.21.1**
- NeoForge **21.1.x**
- Java **21**
- Prefer the repository's existing Gradle/CI conventions over generic examples.

## Overrides
- Treat Fabric/Paper matrices and Minecraft 1.21.2+ / 1.21.11 examples in `SKILL.md` as reference only.
- Do not publish or change release channels without explicit repository evidence and user intent.
- CI must validate the actual NeoForge build, tests, dedicated-server boundary when applicable, and artifact/release contracts already defined by the repository.
- Exact dependency/action versions come from current workflows and repository policy; do not invent upgrades.

## Authority
Read `../../VERSION-AUTHORITY.md` first. Repository build/workflows, physical modlist, exact provider/JAR documentation and project instructions override generic source-skill examples.
