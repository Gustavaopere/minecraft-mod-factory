# Workflow: add world generation

1. Inspect project's existing worldgen/data bootstrap and exact 1.21.1 patterns.
2. Define deterministic generation behavior, allowed dimensions/biomes/tags, density/spacing/radius, and performance bound.
3. Verify exact registry/holder/codec/bootstrap contracts.
4. Prefer data-driven/datagen patterns already used by the project.
5. Add deterministic tests for pure placement math where possible.
6. Generate/validate data.
7. Run representative new-world generation/runtime checks.
8. Inspect logs for registry/codec/datapack errors.
9. Verify persistence/reload separately for runtime state attached to generated content.
