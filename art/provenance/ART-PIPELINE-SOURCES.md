# Art Pipeline — Technical Sources

Historical source check: 2026-09-07.
Factory migration audit: 2026-09-10.

This file records upstream evidence used to author the visual pipeline. It is not version authority over the physical modlist or any runtime repository. Current version-sensitive decisions follow `../../skills/VERSION-AUTHORITY.md`.

## Blockbench

Official plugin guide retained from the historical audit:

- https://blockbench.net/wiki/docs/plugin/

The historical audit recorded that plugins are JavaScript files registered with `Plugin.register`, may create `Action` instances, may attach actions to the Tools menu and may be loaded locally for testing/internal use.

Generated API reference retained from the historical audit:

- https://web.blockbench.net/docs/

The historical implementation recorded access to the active model project, groups/elements/textures/animations, read-only reporting and animation metadata. Those symbols were used by a predecessor helper that is not canonical Factory tooling. The generated reference follows Blockbench releases, so any executable integration must re-check the exact editor version and symbols before implementation instead of inheriting old assumptions.

The migration preserves these source links as provenance; it does not claim they were freshly reverified during migration.

## GeckoLib

Historical Blockbench modeling source:

- https://github.com/bernie-g/geckolib/wiki/Making-Your-Models-%28Blockbench%29

Historical versioned sources:

- https://wiki.geckolib.com/docs/geckolib4/
- https://github.com/bernie-g/geckolib/wiki/Geo-Models-%28Geckolib4%29
- https://github.com/bernie-g/geckolib/wiki/Keyframe-Triggers-%28Geckolib4%29

The source audit recorded Blockbench authoring, hierarchy/parenting/pivots, model/animation resources and animation keyframe callbacks as relevant GeckoLib concepts. Exact Java classes, methods and signatures remain version-sensitive and must be inspected against the provider actually installed for the target runtime.

The physical modlist snapshot dated 2026-09-09 contains GeckoLib `4.9.2`. Presence/version in the physical snapshot does not by itself prove a particular API signature or runtime health.

## Source and version authority

For a generated mod, the runtime repository and latest physical modlist/JAR evidence take precedence over these upstream references. Upstream documentation supplies workflow/API evidence only after matching it to the exact physical provider version.

The Factory visual authority is `art/`; runtime ownership remains with each mod repository. Unknown or stale provider facts remain unavailable until revalidated rather than being inferred from this historical source audit.
