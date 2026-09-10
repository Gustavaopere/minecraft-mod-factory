# F1 / M3 Migration Matrix — Minecraft Mod Factory

Status: **frozen before migration branch creation**  
Factory authority: `Gustavaopere/minecraft-mod-factory`  
Factory audited head before this matrix: `f1db728f5f0f136ea86d0b2a6370b49f6fccb3ba`  
Historical source: `Gustavaopere/neoforge-rpg-skilltree@2ecea4178aa7ac80f99955ab045e296da25376ec`  
Concurrent historical art PR: `#509`, head `423ec39193d03b92e7a4a5a0a46417a529977f30`, draft at matrix freeze  
Physical modlist authority: RPG snapshot `2026-09-09`, 595 top-level entries, SHA-256 `7c0a23d6013101383d196526e4b6ba6940fb54a0fed10eaed5956ab015cfcc00`.

Canonical plans in this repository:

- `plans/PLANO-MESTRE-MINECRAFT-MOD-FACTORY-MOD-ENGINEERING-NEOFORGE-1.21.1-V1.1.md` — SHA-256 `29fc7f4b949b2b8dba327eb3f022f4cd84b11a352430ca821bdaec13072b8744`;
- `plans/PLANO-MESTRE-UNIFICADO-MINECRAFT-MOD-FACTORY-REPO-TEXTURA-BLOCKBENCH-ASSET-MCP-V5.1.md` — SHA-256 `723bb083d5b646812cd44a03a1ef50e8505b366923b64aba5931ee4b7b63befb`.

## Rules frozen by this matrix

The Factory now hosts two logical authorities in the same Git repository: `engineering/` for the Mod Engineering / Integration Control Plane and `art/` for the Repo Textura / Visual & Asset Pipeline. Shared reusable skill material may live under `skills/`. `migration/` is transition evidence only. These physical locations are a decision made after auditing the current sparse Factory tree; they are not inherited from historical `PROJECT-INSTRUCTIONS/` paths.

Every migrated item must preserve authorship/provenance, relevant history, license/source evidence, semantics and tests. Historical paths are not copied blindly. `.bbmodel` and other native authoring formats remain source formats; no conversion is implicit. RPG files are not deleted until an equivalent Factory capability is migrated/adapted and GREEN. Runtime Java, gameplay, the physical modlist corpus and mod-specific acceptance remain in the RPG repository.

Allowed classifications are exactly: `MIGRATE_CANONICAL`, `MIGRATE_ADAPTED`, `REFERENCE_ONLY`, `RPG_SPECIFIC_DO_NOT_MIGRATE`, `SUPERSEDED`, `DUPLICATE_IN_REPO_TEXTURA`.

## Engineering / Integration Control Plane

| Origem | Destino Factory | Classificação | Adaptação necessária | Teste / gate | Status |
|---|---|---|---|---|---|
| `PROJECT-INSTRUCTIONS/engineering/README.md` | `engineering/README.md` | `MIGRATE_ADAPTED` | Remove papel de control plane do RPG; apontar Factory como authority e repos individuais como runtime authorities | links locais + revisão de authorities | READY_WAVE_E1 |
| `PROJECT-INSTRUCTIONS/engineering/REPO-ROUTING.md` | `engineering/REPO-ROUTING.md` | `MIGRATE_ADAPTED` | Trocar central repo pelo Factory; preservar regra runtime-repo / art-domain | route assertions | READY_WAVE_E1 |
| `PROJECT-INSTRUCTIONS/engineering/AGENT-WORKFLOW.md` | `engineering/AGENT-WORKFLOW.md` | `MIGRATE_ADAPTED` | Separar workflow genérico de trechos específicos do runtime RPG e paths `PROJECT-INSTRUCTIONS` | policy/path validator | READY_WAVE_E1 |
| `PROJECT-INSTRUCTIONS/engineering/DIAGNOSTICS.md` | `engineering/DIAGNOSTICS.md` | `MIGRATE_ADAPTED` | Reauditar comandos e paths; remover checks que dependam do runtime RPG | command/path audit | READY_WAVE_E1 |
| `PROJECT-INSTRUCTIONS/engineering/TESTING.md` | `engineering/TESTING.md` | `MIGRATE_ADAPTED` | Rebasear matriz de testes para Factory + repos runtime; não declarar testes RPG como gates internos da Factory | documentation + harness consistency | READY_WAVE_E1 |
| `PROJECT-INSTRUCTIONS/engineering/STATUS.md` | nenhuma cópia canônica; referência por provenance | `REFERENCE_ONLY` | Preservar somente como histórico da origem; `STATUS.md` da Factory é a continuidade canônica | source SHA recorded | FROZEN_REFERENCE |
| planos V1/V5 históricos em `PROJECT-INSTRUCTIONS/engineering/plans/**` | planos V1.1/V5.1 já em `plans/**` | `SUPERSEDED` | Não duplicar planos antigos | exact SHA-256 dos planos novos | DONE_F0 |
| `PROJECT-INSTRUCTIONS/engineering/catalog/sources/SOURCE-REGISTRY.json` | `engineering/catalog/sources/SOURCE-REGISTRY.json` | `MIGRATE_ADAPTED` | Atualizar `integration_control_plane` para Factory; planos para V1.1/V5.1; manter modlist física como fonte externa; eliminar blocker antigo de remote Repo Textura porque o domínio visual agora está na Factory | JSON/schema + authority-order tests | READY_WAVE_E1 |
| `PROJECT-INSTRUCTIONS/engineering/catalog/physical-modlist/**` | nenhuma cópia de snapshot | `RPG_SPECIFIC_DO_NOT_MIGRATE` | Dados físicos continuam junto da authority de runtime/modpack; Factory deve consumir snapshot explicitamente quando necessário | hash `7c0a...cc00` permanece referência | STAY_RPG |
| `PROJECT-INSTRUCTIONS/engineering/contracts/MOD-SPEC-CONTRACT.md` | `engineering/contracts/MOD-SPEC-CONTRACT.md` | `MIGRATE_ADAPTED` | Atualizar paths relativos e wording Repo Textura→domínio `art/` da Factory; manter repos individuais como runtime authority | I1 validator + contract assertions | READY_WAVE_E2 |
| `PROJECT-INSTRUCTIONS/engineering/schemas/mod-spec.schema.json` | `engineering/schemas/mod-spec.schema.json` | `MIGRATE_CANONICAL` | Preservar sem alteração semântica; mudar só se teste provar dependência de path/repo | JSON parse + I1 tests | READY_WAVE_E2 |
| `PROJECT-INSTRUCTIONS/engineering/schemas/dependency-profile.schema.json` | `engineering/schemas/dependency-profile.schema.json` | `MIGRATE_CANONICAL` | Preservar sem alteração semântica | JSON parse + I1/I4 tests | READY_WAVE_E2 |
| `PROJECT-INSTRUCTIONS/engineering/schemas/asset-handoff.schema.json` | `engineering/schemas/asset-handoff.schema.json` | `MIGRATE_CANONICAL` | Preservar schema v2; resolver bindings contra authority real somente em F4 | JSON parse + I4/I6 tests | READY_WAVE_E2 |
| `PROJECT-INSTRUCTIONS/engineering/schemas/compatibility-matrix.schema.json` | `engineering/schemas/compatibility-matrix.schema.json` | `MIGRATE_CANONICAL` | Preservar semântica | JSON parse + I4 tests | READY_WAVE_E2 |
| `PROJECT-INSTRUCTIONS/engineering/schemas/test-manifest.schema.json` | `engineering/schemas/test-manifest.schema.json` | `MIGRATE_CANONICAL` | Preservar semântica | JSON parse + I5 tests | READY_WAVE_E2 |
| `PROJECT-INSTRUCTIONS/engineering/examples/**` | `engineering/examples/**` | `MIGRATE_ADAPTED` | Manter fixtures sintéticas/`UNRESOLVED`; atualizar paths e source authorities, sem fabricar evidence | I1/I4/I6 tests | READY_WAVE_E2 |
| `PROJECT-INSTRUCTIONS/engineering/templates/neoforge-mod/**` | `engineering/templates/neoforge-mod/**` | `MIGRATE_ADAPTED` | Preservar templates I3; atualizar references/workflow paths após novo layout | scaffolder golden diff + generated build check | READY_WAVE_E3 |
| `PROJECT-INSTRUCTIONS/engineering/tooling/validate-i1-foundation.py` | `engineering/tooling/validate-i1-foundation.py` | `MIGRATE_ADAPTED` | Remapear roots históricos para layout Factory sem relaxar fail-closed | `test_i1_foundation.py` | READY_WAVE_E2 |
| `PROJECT-INSTRUCTIONS/engineering/tooling/import-physical-modlist.py` | `engineering/tooling/import-physical-modlist.py` | `MIGRATE_ADAPTED` | Migrar o importador, não o snapshot; aceitar input explícito e produzir catálogo derivado sem assumir path RPG | I2 tests contra fixture local | READY_WAVE_E3 |
| `PROJECT-INSTRUCTIONS/engineering/tooling/scaffolder/**` | `engineering/tooling/scaffolder/**` | `MIGRATE_ADAPTED` | Remapear template/schema paths; preservar deterministic output e fail-closed | I3 tests + generated sample build | READY_WAVE_E3 |
| `PROJECT-INSTRUCTIONS/engineering/tooling/validators/**` | `engineering/tooling/validators/**` | `MIGRATE_ADAPTED` | Remapear schema/catalog roots; preservar regras semânticas | I4 tests | READY_WAVE_E4 |
| `PROJECT-INSTRUCTIONS/engineering/tooling/test-harness/**` | `engineering/tooling/test-harness/**` | `MIGRATE_ADAPTED` | Separar harness genérico de invocações específicas do RPG; runtime gates devem ser parametrizados por repo alvo | I5 tests + harness dry-run | READY_WAVE_E5 |
| `PROJECT-INSTRUCTIONS/engineering/tooling/asset-handoff/**` | `engineering/tooling/asset-handoff/**` | `MIGRATE_ADAPTED` | Atualizar roots e authority visual para `art/`; manter F4 fail-closed até handoff real | I6 tests + source revision/hash checks | READY_WAVE_E6 |
| `PROJECT-INSTRUCTIONS/engineering/tests/test_i1_foundation.py` | `engineering/tests/test_i1_foundation.py` | `MIGRATE_ADAPTED` | Atualizar paths, não expectativas semânticas | unittest PASS | READY_WAVE_E2 |
| `PROJECT-INSTRUCTIONS/engineering/tests/test_i2_modlist_catalog.py` | `engineering/tests/test_i2_modlist_catalog.py` | `MIGRATE_ADAPTED` | Usar fixture/snapshot explicitamente montado; não copiar catálogo físico como authority interna | unittest PASS | READY_WAVE_E3 |
| `PROJECT-INSTRUCTIONS/engineering/tests/test_i3_mod_scaffolder.py` | `engineering/tests/test_i3_mod_scaffolder.py` | `MIGRATE_ADAPTED` | Atualizar roots de templates/tooling | unittest PASS | READY_WAVE_E3 |
| `PROJECT-INSTRUCTIONS/engineering/tests/test_i4_engineering_validators.py` | `engineering/tests/test_i4_engineering_validators.py` | `MIGRATE_ADAPTED` | Atualizar roots; preservar invariants | unittest PASS | READY_WAVE_E4 |
| `PROJECT-INSTRUCTIONS/engineering/tests/test_i5_test_harness.py` | `engineering/tests/test_i5_test_harness.py` | `MIGRATE_ADAPTED` | Parametrizar runtime repository assumptions | unittest PASS | READY_WAVE_E5 |
| `PROJECT-INSTRUCTIONS/engineering/tests/test_i6_asset_handoff.py` | `engineering/tests/test_i6_asset_handoff.py` | `MIGRATE_ADAPTED` | Atualizar art authority/path; não converter structural PASS em real handoff PASS | unittest PASS | READY_WAVE_E6 |
| `PROJECT-INSTRUCTIONS/engineering/tests/fixtures/**` e `golden/**` | `engineering/tests/fixtures/**`, `engineering/tests/golden/**` | `MIGRATE_ADAPTED` | Migrar somente fixtures exigidas pelos testes acima; manter `UNRESOLVED` onde não há fato real | all I1–I6 unit tests | READY_BY_DEPENDENCY |
| `.github/workflows/mod-engineering-i1-foundation.yml` | `.github/workflows/factory-engineering-i1-foundation.yml` | `MIGRATE_ADAPTED` | Atualizar paths e nomes; não depender do Gradle/runtime RPG | workflow syntax + exact-head CI | READY_WITH_E2 |
| `.github/workflows/mod-engineering-i2-modlist-catalog.yml` | `.github/workflows/factory-engineering-i2-modlist-catalog.yml` | `MIGRATE_ADAPTED` | Input físico explícito/fixture; nenhum snapshot privado embutido | exact-head CI | READY_WITH_E3 |
| `.github/workflows/mod-engineering-i3-mod-scaffolder.yml` | `.github/workflows/factory-engineering-i3-mod-scaffolder.yml` | `MIGRATE_ADAPTED` | Atualizar roots e build do sample gerado | exact-head CI | READY_WITH_E3 |
| `.github/workflows/mod-engineering-i4-validators.yml` | `.github/workflows/factory-engineering-i4-validators.yml` | `MIGRATE_ADAPTED` | Atualizar roots | exact-head CI | READY_WITH_E4 |
| `.github/workflows/mod-engineering-i5-test-harness.yml` | `.github/workflows/factory-engineering-i5-test-harness.yml` | `MIGRATE_ADAPTED` | Migrar somente o gate estável de I5; excluir scaffolding temporário da PR #509 | exact-head CI | READY_WITH_E5 |
| `.github/workflows/mod-engineering-i6-asset-handoff.yml` | `.github/workflows/factory-engineering-i6-asset-handoff.yml` | `MIGRATE_ADAPTED` | Atualizar art authority e paths | exact-head CI | READY_WITH_E6 |
| `.github/workflows/codeql.yml`, `sonarqube.yml`, `scorecard.yml` | reavaliar após existir código executável suficiente na Factory | `REFERENCE_ONLY` | Não copiar configuração de análise do runtime RPG cegamente | security/quality plan review | DEFER |

## Repo Textura / Visual & Asset Pipeline

| Origem | Destino Factory | Classificação | Adaptação necessária | Teste / gate | Status |
|---|---|---|---|---|---|
| `docs/art/VISUAL-STYLE-BIBLE.md` | `art/VISUAL-STYLE-BIBLE.md` | `MIGRATE_ADAPTED` | Separar gramática visual reutilizável do contexto editorial específico do RPG/modpack; preservar provenance e facts como contexto versionado | link/provenance audit + visual policy review | READY_WAVE_A1 |
| `PROJECT-INSTRUCTIONS/skills/ART-PIPELINE-SOURCES.md` | `art/provenance/ART-PIPELINE-SOURCES.md` | `MIGRATE_ADAPTED` | Atualizar authority/paths e conservar fontes primárias | provenance validator | READY_WAVE_A1 |
| `PROJECT-INSTRUCTIONS/skills/VISUAL-STYLE-SOURCES.md` | `art/provenance/VISUAL-STYLE-SOURCES.md` | `MIGRATE_ADAPTED` | Marcar fatos do pack como snapshot/contexto, não Factory global | provenance validator | READY_WAVE_A1 |
| `PROJECT-INSTRUCTIONS/skills/SPELL-VFX-AUDIO-SOURCES.md` | `art/provenance/SPELL-VFX-AUDIO-SOURCES.md` | `MIGRATE_ADAPTED` | Revalidar providers contra modlist física antes de suporte real | provenance/provider audit | READY_WAVE_A1 |
| `PROJECT-INSTRUCTIONS/skills/README.md` | `skills/README.md` | `MIGRATE_ADAPTED` | Remover “neste repositório RPG”; atualizar layout `art/` e `engineering/` | router/link validator | READY_WAVE_S1 |
| `PROJECT-INSTRUCTIONS/skills/ROUTER.md` | `skills/ROUTER.md` | `MIGRATE_ADAPTED` | Atualizar paths e transformar Repo Textura em domínio visual da Factory | router tests | READY_WAVE_S1 |
| `PROJECT-INSTRUCTIONS/skills/VERSION-AUTHORITY.md` | `skills/VERSION-AUTHORITY.md` | `MIGRATE_ADAPTED` | Manter 1.21.1/NeoForge/Java 21; apontar modlist física externa | version-authority assertions | READY_WAVE_S1 |
| `PROJECT-INSTRUCTIONS/skills/USER-GUIDED-WORKFLOW.md` | `skills/USER-GUIDED-WORKFLOW.md` | `MIGRATE_CANONICAL` | Sem mudança semântica salvo links | policy validator | READY_WAVE_S1 |
| `PROJECT-INSTRUCTIONS/skills/SOURCE-MANIFEST.md` | `migration/provenance/USER-SKILL-SOURCE-MANIFEST.md` | `REFERENCE_ONLY` | Preservar hashes dos 20 ZIPs como histórico de proveniência; não promover conteúdo recebido a authority | hash/table audit | PRESERVE_REFERENCE |
| `PROJECT-INSTRUCTIONS/skills/SOURCE-AUDIT.md` | `migration/provenance/USER-SKILL-SOURCE-AUDIT.md` | `REFERENCE_ONLY` | Preservar classificação histórica; nova seleção é feita por esta matriz | provenance review | PRESERVE_REFERENCE |
| `PROJECT-INSTRUCTIONS/skills/FULL-USER-SKILL-IMPORT.md` | `migration/provenance/FULL-USER-SKILL-IMPORT.md` | `REFERENCE_ONLY` | Histórico da importação de 20 bundles/142 arquivos | count/hash evidence | PRESERVE_REFERENCE |
| project-authored `library/minecraft-asset-art-direction/**` | `art/skills/minecraft-asset-art-direction/**` | `MIGRATE_ADAPTED` | Atualizar overlays/links para Factory | skill validator | READY_WAVE_A1 |
| project-authored `library/minecraft-blockbench-geckolib/**` | `art/skills/minecraft-blockbench-geckolib/**` | `MIGRATE_ADAPTED` | Atualizar overlay e provider evidence; preservar `.bbmodel` como source | skill + provider-profile tests | READY_WAVE_A1 |
| project-authored `library/minecraft-vfx-engineering/**` | `art/skills/minecraft-vfx-engineering/**` | `MIGRATE_ADAPTED` | Provider facts permanecem fail-closed | skill/provider tests | READY_WAVE_A1 |
| project-authored `library/minecraft-spell-vfx-engineering/**` | `art/skills/minecraft-spell-vfx-engineering/**` | `MIGRATE_ADAPTED` | Manter presentation-only; remover identidade RPG | skill tests | READY_WAVE_A1 |
| project-authored `library/minecraft-spell-production/**` | `art/skills/minecraft-spell-production/**` | `MIGRATE_ADAPTED` | Runtime authority continua no mod/provider real | skill tests | READY_WAVE_A1 |
| project-authored `library/minecraft-audio-design/**` | `art/skills/minecraft-audio-design/**` | `MIGRATE_ADAPTED` | Preservar provenance/licença | skill tests | READY_WAVE_A1 |
| project-authored `library/minecraft-visual-qa/**` | `art/skills/minecraft-visual-qa/**` | `MIGRATE_ADAPTED` | Atualizar links/contexts; não transformar build PASS em visual PASS | skill + visual-QA policy tests | READY_WAVE_A1 |
| received `library/minecraft-neoforge-engineering/**` | `skills/library/minecraft-neoforge-engineering/**` | `MIGRATE_ADAPTED` | Preservar payload/overlay boundary e 1.21.1 authority | source payload + overlay validator | READY_WAVE_S2 |
| received `library/minecraft-testing/**` | `skills/library/minecraft-testing/**` | `MIGRATE_ADAPTED` | Preservar source payload; adaptar overlay | source payload + overlay validator | READY_WAVE_S2 |
| received `library/minecraft-ci-release/**` | `skills/library/minecraft-ci-release/**` | `MIGRATE_ADAPTED` | Preservar source payload; adaptar overlay | source payload + overlay validator | READY_WAVE_S2 |
| received `library/minecraft-jar-reverse-engineering/**`, `minecraft-dependency-compatibility-graph/**`, `minecraft-modpack-bisect/**`, `minecraft-neoforge-modpack-debugging/**`, `modpack-inventory-redundancy-audit/**` | `skills/library/<same>/**` | `MIGRATE_ADAPTED` | Manter uso de evidência física; overlays não podem inventar provider API | source/overlay validator | READY_WAVE_S2 |
| received data/content skills `minecraft-commands-scripting`, `minecraft-datapack`, `minecraft-resource-pack`, `minecraft-world-generation`, `minecraft-imagegen` | nenhuma cópia na primeira onda | `REFERENCE_ONLY` | Reavaliar quando feature-generator/art look-dev correspondente entrar no roadmap | capability need + version audit | DEFER |
| received `minecraft-mod-dev/**` | nenhuma cópia canônica | `REFERENCE_ONLY` | Bundle histórico incompleto; três arquivos referenciados ausentes | completeness evidence required | DEFER_INCOMPLETE |
| received `minecraft-plugin-dev`, `minecraft-server-admin`, `minecraft-essentials-ops`, `minecraft-multiloader`, `minecraft-worldedit-ops` | nenhuma cópia na primeira onda | `REFERENCE_ONLY` | Fora do alvo normal atual; só promover com decisão explícita e evidence | target/runtime decision | DEFER |
| `PROJECT-INSTRUCTIONS/skills/standards/MODEL-ASSET-CONTRACT.md` | `art/standards/MODEL-ASSET-CONTRACT.md` | `MIGRATE_ADAPTED` | Atualizar paths/naming, preservar contrato | toolkit/golden validation | READY_WAVE_A2 |
| `PROJECT-INSTRUCTIONS/skills/standards/VISUAL-QA.md` | `art/standards/VISUAL-QA.md` | `MIGRATE_ADAPTED` | Atualizar paths; manter in-game evidence requirement | visual-QA validator | READY_WAVE_A2 |
| `PROJECT-INSTRUCTIONS/skills/standards/VFX-QA.md` | `art/standards/VFX-QA.md` | `MIGRATE_ADAPTED` | Atualizar provider/path refs | VFX-QA validator | READY_WAVE_A2 |
| `PROJECT-INSTRUCTIONS/skills/standards/AUDIO-QA.md` | `art/standards/AUDIO-QA.md` | `MIGRATE_ADAPTED` | Atualizar refs; preservar provenance | audio-QA validator | READY_WAVE_A2 |
| `PROJECT-INSTRUCTIONS/skills/standards/SPELL-PRESENTATION-CONTRACT.md` | `art/standards/SPELL-PRESENTATION-CONTRACT.md` | `MIGRATE_ADAPTED` | Remover acoplamento nominal RPG mantendo provider gameplay authority | contract tests | READY_WAVE_A2 |
| Toolkit/provider/extension/security/protocol standards em `skills/standards/**` | `art/standards/**` | `MIGRATE_ADAPTED` | Renomear `RPG Asset Toolkit/MCP` para nome neutro da Factory; manter IDs/protocol shims quando compatibilidade exigir | schema/protocol/security suites | READY_WAVE_A3 |
| `PROJECT-INSTRUCTIONS/skills/templates/ASSET-BRIEF.md`, `MODEL-BRIEF.md`, `ANIMATION-BRIEF.md`, `VFX-BRIEF.md`, `SPELL-BRIEF.md`, `AUDIO-CUE-SHEET.md`, `VISUAL-QA-CHECKLIST.md` | `art/templates/<same>` | `MIGRATE_ADAPTED` | Atualizar links/naming sem mudar semântica de evidência | template/schema/link checks | READY_WAVE_A2 |
| templates README/Blockbench specialization | `art/templates/README.md`, `art/templates/blockbench/**` | `MIGRATE_ADAPTED` | Atualizar naming e toolkit paths | template validator | READY_WAVE_A2 |
| `skills/tools/blockbench/minecraft_asset_validator.js` | nenhuma cópia canônica | `SUPERSEDED` | Toolkit atual é authority; preservar histórico apenas no RPG | parity covered by Toolkit tests | DO_NOT_COPY |
| `skills/tools/blockbench/rpg-asset-toolkit/**` | `art/tooling/blockbench/asset-toolkit/**` | `MIGRATE_ADAPTED` | M5 obrigatório: desacoplar nome `RPG`, atualizar paths, preservar API/protocol compatibility shim quando necessário; bundle gerado nunca é editado à mão | aggregate Node suite + deterministic bundle + validator | READY_WAVE_A3 |
| `skills/scripts/validate_skill_repository.py` e validators de provenance/source evidence | `skills/scripts/**` / `art/tooling/validators/**` conforme responsabilidade | `MIGRATE_ADAPTED` | Dividir gate de skills compartilhadas de gate artístico; atualizar counts esperados depois da seleção, sem falsificar “27 skills” | Python compile + validator GREEN | READY_WAVE_S3_A3 |
| `skills/golden-samples/model-asset/**` | `art/golden-samples/model-asset/**` | `MIGRATE_ADAPTED` | Migrar depois do rename M5; manter `REFERENCE-ONLY`, `UNRESOLVED` e fixture normalizada não-`.bbmodel` | golden validator + Toolkit | DEFER_M6 |
| `skills/golden-samples/spell/**` | `art/golden-samples/spell/**` | `MIGRATE_ADAPTED` | Migrar depois do rename M5; revalidar providers contra modlist física; manter QA pendente sem evidence | golden/reference-evidence validators | DEFER_M6 |
| `skills/golden-samples/validate_golden_samples.js` e `validate_reference_evidence.js` | `art/golden-samples/<same>` | `MIGRATE_ADAPTED` | Atualizar paths/naming após corpus final | Node validation | DEFER_M6 |
| `.github/workflows/blockbench-mcp-sidecar.yml` | `.github/workflows/factory-art-mcp-sidecar.yml` | `MIGRATE_ADAPTED` | Atualizar paths/naming; manter read-only security baseline de PR #487 | MCP sidecar suite on exact head | READY_WITH_A3 |
| PRs #479/#480/#482/#483/#484/#486/#487 | `migration/provenance/HISTORICAL-ART-PR-LEDGER.md` ou metadata equivalente | `REFERENCE_ONLY` | Preservar milestones/hashes e usar deltas como proveniência; não copiar branches | PR/head provenance review | READY_PROVENANCE |

## Explicit non-migration / concurrency boundaries

| Origem | Destino Factory | Classificação | Adaptação necessária | Teste / gate | Status |
|---|---|---|---|---|---|
| RPG `src/**`, `build.gradle`, `gradle.properties`, `settings.gradle`, runtime resources | nenhum | `RPG_SPECIFIC_DO_NOT_MIGRATE` | Runtime continua no repo do mod | RPG build/runtime gates permanecem lá | STAY_RPG |
| gameplay/perks/skill-tree/chat-specific docs | nenhum | `RPG_SPECIFIC_DO_NOT_MIGRATE` | Nenhuma | path audit | STAY_RPG |
| PR #492 `PROJECT-INSTRUCTIONS/modlist/**` dossiers | nenhum | `RPG_SPECIFIC_DO_NOT_MIGRATE` | Modlist/editorial runtime authority permanece RPG | no overlap with Factory migration paths | STAY_RPG |
| PR #485 Parchment filtering | nenhum | `RPG_SPECIFIC_DO_NOT_MIGRATE` | Repo-specific Gradle resolution tangent; não é capability comum provada | no overlap | STAY_RPG |
| PR #509 final PR4 acceptance tests | `art/tooling/blockbench/asset-toolkit/**` tests, somente após delta estável | `MIGRATE_ADAPTED` | Reconciliar `texture.compare`, round-trip e bitmap-aware Undo acceptance com paths/naming da Factory | targeted + aggregate PR4 acceptance | CONCURRENT_WAIT_STABLE_DELTA |
| PR #509 `.github/tmp-pr4-texture-acceptance-trigger.txt` | nenhum | `RPG_SPECIFIC_DO_NOT_MIGRATE` | Scaffolding branch-local temporário | absent from Factory | DO_NOT_COPY |
| PR #509 `.github/workflows/tmp-pr4-texture-acceptance-green.yml` | nenhum | `SUPERSEDED` | Harness transitório não vira CI canônico | absent from Factory | DO_NOT_COPY |
| PR #509 alterações temporárias em `mod-engineering-i5-test-harness.yml` usadas para auto-commit | nenhum delta direto | `SUPERSEDED` | Somente requisitos/testes finais podem ser reconciliados; mecanismo temporário não | stable final diff review | DO_NOT_COPY |
| workflows RPG de Battle Mage, Volcanoes, compendium e demais runtime systems | nenhum | `RPG_SPECIFIC_DO_NOT_MIGRATE` | Nenhuma | workflow-name/path audit | STAY_RPG |

## Migration waves and gates

1. **E1 / S1 — governance and routing:** engineering authority docs, source registry, shared router/version/manual-workflow. Gate: no claim that RPG is the common control plane; no broken links; modlist remains external authority.
2. **E2 — I1 foundation:** contract, five schemas, examples, foundation validator/tests and adapted I1 workflow. Gate: migrated I1 tests GREEN on exact Factory head.
3. **E3 — I2/I3:** physical-modlist importer with fixtures only, scaffolder/templates/tests/workflows. Gate: I2/I3 GREEN; no physical catalog copied as Factory authority.
4. **E4 / E5 / E6 — I4/I5/I6 structural:** validators, test harness, asset handoff and their tests/workflows. Gate: historical semantics GREEN; I6 remains structural only until F4 real handoff.
5. **A1 / A2 — artistic foundation:** style/provenance, project-authored art skills, contracts, standards and templates. Gate: source/provenance and skill validators GREEN.
6. **A3 / M5 — Toolkit/registry/Live Bridge:** migrate PR #486/#487 capabilities, rename `RPG` surface to neutral Factory surface with explicit compatibility shims. Gate: deterministic bundle, aggregate tests, MCP security/read-only tests GREEN.
7. **M6 — Golden Samples:** migrate project-owned reference corpus only after A3/M5. Gate: reference-evidence + golden validators GREEN; no `UNRESOLVED` promoted to fact.
8. **PR4 reconciliation:** consume stable final delta from PR #509 after it stops being branch-local scaffolding; port requirements/tests/production delta, not temporary workflows. Gate: targeted PR4 acceptance + aggregate regression + deterministic bundle.

## Deletion rule

`RPG_DELETION_ALLOWED=NO` remains in force for every row. A later cleanup PR may remove duplicated historical common infrastructure from RPG only after the corresponding Factory wave is merged, revalidated and has a documented rollback/provenance boundary. Runtime/modlist-specific rows are not cleanup candidates.

## Duplicate check

At matrix freeze, the Factory tree contains only root governance/status, the two canonical plans and this migration record. No historical engineering/art capability already exists in the destination, so no current row is classified `DUPLICATE_IN_REPO_TEXTURA`. The category remains reserved for discoveries during per-wave re-audit.
