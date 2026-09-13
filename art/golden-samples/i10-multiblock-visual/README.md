# I10 Multiblock Visual Golden Source

Status: REFERENCE-ONLY — not a runtime registration and not evidence of shipped gameplay.

This directory is the Repo Textura source authority for the provider-neutral visual baseline of the I10 multiblock foundation Golden.

The five model files under `models/` are source-native Minecraft Java block-model JSON. They intentionally use only vanilla texture references and require no format conversion. Engineering consumes them byte-for-byte and owns the runtime blockstate wiring that binds server-authoritative `formed` and `facing` state.

This baseline does not claim Blockbench authoring, provider-specific animation, texture creation, or completed visual/runtime QA. Those remain pending until their dedicated gates produce evidence.
