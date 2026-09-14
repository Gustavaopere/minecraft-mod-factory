# NPC Visual Asset Tooling Migration Provenance

Source repository: `Gustavaopere/neoforge-rpg-skilltree`.

Source work: RPG PR #548, before merge, where the first reusable NPC visual-asset contract and manifest validator were prototyped alongside campaign-specific Iren Valmor data.

Source revision used for reconciliation: `18042a081c5bc04d279dfee4b5b9f8b4cb7f4aa2`.

Relevant source paths at that revision:

- `historia/assets/npcs/README.md` — mixed reusable portrait/skin production rules with consumer-specific policy;
- `historia/assets/npcs/validate_manifest.py` — first campaign-local manifest validator;
- `historia/assets/npcs/manifest.json` — consumer-specific policy and asset records;
- `historia/03-npcs/principais/NPC-0003-iren-valmor-asset-brief.md` — NPC-specific production requirements and provenance.

## Reconciliation decision

The original work mixed two ownership domains. This migration separates them instead of copying the RPG tree verbatim.

Moved/reimplemented in Factory:

- generic portrait/concept versus skin separation;
- reusable production-state vocabulary;
- generic provenance and finality gates;
- reusable manifest validator;
- validator unit tests and CI;
- routing from narrative authoring to the art-production domain.

Remains consumer-owned in `Gustavaopere/neoforge-rpg-skilltree`:

- Iren Valmor and all campaign identities/canon;
- project-specific portrait and skin policy values;
- `historia/assets/npcs/manifest.json` consumer data;
- actual portraits/skins and per-NPC briefs;
- provider/runtime evidence such as the renderer actually used by the modpack;
- Grimoire reconciliation and campaign editorial approval.

## Deliberate differences from the source prototype

- Factory policy is parameterized; it does not hard-code the RPG's `2048×2048` portrait target or `64×64` humanoid skin target as universal defaults.
- Factory tooling does not name Iren, Easy NPC, the RPG repository path or any campaign-specific authority.
- Repository-relative path confinement is part of the reusable contract.
- `FINAL` assets are validated against the appropriate consumer policy regardless of whether a redundant convenience flag is present.
- Campaign art remains in the consumer repository; only reusable capability is centralized.

## Consumer cleanup

RPG PR #548 removes the campaign-local generic validator/contract and consumes the pinned Factory validator through its CI workflow. A separate RPG cleanup PR removes legacy generic narrative template snapshots already superseded by Factory-owned `narrative/templates/`.

After this migration, the Factory is the authority for the reusable NPC visual-production contract and validator. Consumers should keep only project-specific configuration/data/content and should not copy the Python implementation back into campaign trees.
