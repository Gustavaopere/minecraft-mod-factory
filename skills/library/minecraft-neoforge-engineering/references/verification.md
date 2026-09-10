# Verification ladder

Use the strongest applicable evidence, not every layer mechanically.

1. static/source inspection;
2. Java compilation;
3. focused unit tests;
4. broader regression tests;
5. datagen/resource validation;
6. GameTests/integration tests;
7. dedicated-server startup/smoke/scenario;
8. client runtime/manual scenario;
9. optional-mod compatibility matrix;
10. clean build/package and CI for release work.

Compilation proves signatures/types; it does not prove registry timing, side safety, serialization correctness, save/reload, network synchronization, world behavior, rendering, or third-party compatibility.

Discover actual Gradle tasks with the wrapper rather than inventing `runGameTestServer` or similar names. Repository scripts/CI may define custom tasks.

When tests fail, inspect the first causal failure and relevant logs. Do not hide warnings globally to create a green-looking output.

A final report must say which layers actually ran and their result.
