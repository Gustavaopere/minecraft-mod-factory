# Project overlay — minecraft-mod-dev

## Routing status
Secondary/general reference. Prefer `minecraft-neoforge-engineering` for this project.

## Overrides
- Target Minecraft **1.21.1**, NeoForge **21.1.x**, Java **21** only unless the user explicitly opens another target.
- Fabric and legacy Forge examples are reference-only.
- Individual mod repositories are runtime-code authorities; the integration repository owns shared contracts/instructions/tooling where appropriate.
- Do not invent JEI/Create/other integration APIs; prove them from the exact installed version.

## Authority
`../../VERSION-AUTHORITY.md` and `minecraft-neoforge-engineering` override generic/multi-loader examples.
