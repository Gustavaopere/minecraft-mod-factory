# MOD SPEC CONTRACT

Status: canonical I1 contract for defining a mod before runtime implementation.

## Purpose

Every new mod must begin from a versioned specification that validates against `../schemas/mod-spec.schema.json`. The specification is a control-plane contract; it does not move runtime ownership into this repository.

The mod's own repository remains the **runtime authority** for Java code, registries, state, persistence, networking, gameplay rules, tests, packaging and release. The Factory `art/` domain (Repo Textura authority) remains the artistic source of truth for provider-native source assets and visual handoffs.

## Required rules

1. Target fields are explicit: Minecraft `1.21.1`, loader `neoforge`, NeoForge `21.1.248` for the current physical snapshot, Java `21`.
2. `identity.mod_id` must be lowercase and match the schema. A human-readable name never substitutes for the registry identifier.
3. Unknown facts are recorded as `UNRESOLVED`. Do not infer repositories, provider versions, source refs, APIs, licenses, paths, capabilities or compatibility.
4. Dependency claims require a dependency profile and evidence appropriate to the claimed state.
5. Visual work references a Repo Textura package/handoff under the Factory art authority; functional code remains in the runtime authority repository.
6. Provider-native source formats are preserved. A conversion must be explicit in an asset handoff and carry evidence; silent conversion is prohibited.
7. Compatibility and test states use the canonical evidence-state vocabulary from the master plan.
8. A spec is not `COMPLETE` merely because the JSON validates. Completion requires applicable runtime, integration, visual, compatibility, performance and release gates to have evidence.

## Canonical companion schemas

- `../schemas/mod-spec.schema.json`
- `../schemas/dependency-profile.schema.json`
- `../schemas/asset-handoff.schema.json`
- `../schemas/compatibility-matrix.schema.json`
- `../schemas/test-manifest.schema.json`

Examples under `../examples/` are synthetic fixtures. They intentionally contain `UNRESOLVED` values and must not be treated as production facts.

## Source authority

Engineering claims follow the order recorded in `../catalog/sources/SOURCE-REGISTRY.json`. A lower-authority source cannot silently override a higher-authority physical or repository fact.

For a concrete mod, the spec must name or resolve its runtime repository before Java implementation begins. For art, `Gustavaopere/minecraft-mod-factory` with authority root `art/` is the resolved repository authority; the concrete asset package path, source revision and delivery target remain `UNRESOLVED` until a real handoff supplies evidence.

## Validation

```bash
python3 engineering/tooling/validate-i1-foundation.py
python3 -m unittest engineering/tests/test_i1_foundation.py
```

Both commands must pass on the exact branch/PR head.
