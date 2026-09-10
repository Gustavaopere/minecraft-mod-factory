# Codecs and data formats

Minecraft 1.21.x uses data-driven and codec-based patterns heavily. Treat serialized formats as compatibility contracts once worlds/configs/data packs depend on them.

Check:

- stable field names and IDs;
- optional/default fields for forward evolution;
- numeric/string bounds;
- invalid/missing data behavior;
- network codec vs persistent/data codec distinction;
- registry-aware serialization context where required;
- deterministic ordering where diffs/tests depend on output.

Do not silently change persistent meaning of an existing field. Add migration/defaulting or explicitly declare incompatibility.
