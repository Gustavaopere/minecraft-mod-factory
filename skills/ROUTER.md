# Router de skills da Minecraft Mod Factory

Antes de escolher uma instrução especializada, leia `VERSION-AUTHORITY.md`. Se o usuário precisar agir manualmente, aplique `USER-GUIDED-WORKFLOW.md`.

## Rotas principais

- Engenharia NeoForge, contratos, scaffolding, validators, testes, compatibilidade e release → `../engineering/` e plano V1.1.
- Blockbench, modelos, texturas, UV, rigs, animações, VFX, GUI visual e QA → `../art/` e plano V5.1.
- Runtime Java/gameplay de um mod → repositório runtime authority daquele mod; a Factory apenas coordena/gera/valida o handoff.
- Investigação de provider → modlist/JAR física exata primeiro; adapters e claims ficam indisponíveis até prova da versão alvo.

## Migração ativa

Enquanto `../migration/MIGRATION-MATRIX-F1-M3.md` estiver ativa, uma skill histórica só pode virar capability canônica da Factory depois de classificada, migrada/adaptada e revalidada. Não invente `skills/library/**` antes da onda correspondente.

## Segurança de versão

Exemplos Fabric, Forge legado, Paper ou Minecraft posterior a 1.21.1 são referência conceitual até validação específica. Provider-native assets e `.bbmodel` permanecem fonte; conversão silenciosa é proibida.
