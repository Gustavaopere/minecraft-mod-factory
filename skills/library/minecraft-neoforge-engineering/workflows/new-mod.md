# Workflow: create a new mod

1. Confirm target is Minecraft 1.21.1, NeoForge 21.1.x, Java 21 unless explicitly overridden.
2. Prefer an official NeoForge 1.21.1 MDK/generator baseline rather than hand-inventing Gradle setup.
3. Define mod ID, package, license, versioning, repository layout, and minimal acceptance goal.
4. Establish build first; compile an untouched/minimal baseline before adding systems.
5. Add architecture incrementally: registries/config/data/network/client packages only when needed.
6. For each gameplay system, follow `workflows/implement-feature.md`.
7. Add CI/build verification appropriate to the repository.
8. Verify dedicated-server startup as soon as common code exists, not only at release.
9. Document project-specific decisions in repository files rather than bloating this generic skill.
