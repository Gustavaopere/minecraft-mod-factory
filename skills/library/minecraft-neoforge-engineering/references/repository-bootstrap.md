# Repository bootstrap

For existing repositories, run or obtain equivalent evidence before substantial edits:

```text
git status --short --branch
git branch --show-current
git rev-parse HEAD
git remote -v
java -version
<gradle-wrapper> --version
```

When allowed and useful, refresh remote refs with a non-destructive fetch. Do not reset/rebase/pull/checkout over local work simply to make state look clean.

Read authority files such as `AGENTS.md`, `README.md`, `CONTRIBUTING.md`, `plans/`, `STATUS.md`, `DECISIONS.md`, build files, CI workflows, and source relevant to the task.

Confirm from build configuration rather than assumption:

- Minecraft version;
- NeoForge version/range;
- Java toolchain;
- ModDevGradle/NeoGradle/plugin version;
- mappings/decompilation setup;
- dependencies and optional dependencies;
- mixins/access transformers;
- datagen, GameTest, server-smoke, client-run, and CI tasks.

Inventory project architecture: mod entry points, registration, event subscribers, network code, persistent state, config, client-only code, datagen/resources, tests, compatibility adapters, and existing abstractions.

If repository reality conflicts with the expected 1.21.1 / NeoForge 21.1.x / Java 21 target, report the discrepancy instead of silently coercing it.
