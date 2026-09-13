# Narrative Authoring Migration Provenance

Source repository: `Gustavaopere/neoforge-rpg-skilltree`.

Reusable capability was derived from the narrative-authoring work developed in RPG PRs #512, #515, #518 and #521. The Factory version deliberately removes RPG-specific canon, Grimoire authority policy, Stage 08 implementation assumptions and concrete campaign IDs from the reusable implementation.

Migration boundary:

- moved/reimplemented in Factory: validators, inventory, stable-state checks, generic templates, reusable authoring skill and authoring CI;
- remains RPG-owned: campaign profile, canon/lore, Grimoire reconciliation policy, Narrative Core contracts, NPC/quest/faction/location/evidence/dialogue records and other project-specific content.

The Factory is the authority for the reusable authoring capability after this migration. Consumer repositories should not copy the Python implementation back into their trees.
