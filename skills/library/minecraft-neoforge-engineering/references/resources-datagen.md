# Resources, data generation, and tags

Prefer data-driven content when it improves compatibility and maintainability.

Check applicable assets/data:

- language keys;
- models/blockstates;
- recipes/loot tables;
- tags;
- advancements;
- worldgen data;
- data maps or other NeoForge data systems;
- sounds/textures/particles;
- generated resource paths and namespace.

Use project datagen when established. Do not hand-edit generated output unless repository policy says to.

Tags are often preferable to hard-coded lists for cross-mod classification. When creating tags for integration, document ownership/semantics so datapacks can safely extend them.

Validate generated resources and runtime reload/load paths where applicable; `compileJava` cannot validate malformed JSON or missing asset references.
