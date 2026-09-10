# World generation

Worldgen failures can corrupt load paths or create compatibility problems long after compilation succeeds.

Before implementing worldgen:

- identify whether the project uses data-driven JSON/datagen, bootstrap code, custom placement logic, or external library APIs;
- verify registry/bootstrap keys and exact 1.21.1 codec/holder APIs;
- avoid forced chunk generation/load during normal ticking;
- define deterministic seed usage where randomness matters;
- constrain density/radius/spacing and generation cost;
- consider biome/dimension tags rather than hard-coded allowlists when appropriate;
- ensure feature placement cannot recursively trigger unsafe generation.

Test new worlds and representative generation, not only existing worlds. For persistence/state tied to generated structures, separately verify save/reload.
