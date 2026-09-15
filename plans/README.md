# Plans — Minecraft Mod Factory

Este diretório mantém os dois **planos mestres canônicos** na raiz e adiciona mapas de execução separados por domínio para navegação rápida.

## Legenda de estado

- ✅ — milestone encerrado com evidência aceita no `STATUS.md` canônico, implementação presente na `main` ou gate correspondente.
- 🔄 — fronteira atual de execução; ainda não concluída.
- ⬜ — milestone pendente/não iniciado.
- ⛔ — bloqueado por um gate explícito.

> Os ícones resumem o estado do milestone. Eles não promovem `REFERENCE_ONLY`, `DEFERRED`, `UNAVAILABLE` ou runtime não comprovado para `PASS`. O arquivo do milestone registra essas limitações quando aplicáveis.

## Domínios

- [Mod Engineering / Integration Control Plane](./mod-engineering/README.md)
- [Repo Textura / Visual & Asset Pipeline](./visual-assets/README.md)
- [Narrative Authoring / Story Creation Toolkit](./narrative-authoring/README.md)

## Planos mestres canônicos

- [Mod Engineering — V1.1](./PLANO-MESTRE-MINECRAFT-MOD-FACTORY-MOD-ENGINEERING-NEOFORGE-1.21.1-V1.1.md)
- [Repo Textura / Visual & Asset Pipeline — V5.1](./PLANO-MESTRE-UNIFICADO-MINECRAFT-MOD-FACTORY-REPO-TEXTURA-BLOCKBENCH-ASSET-MCP-V5.1.md)

Os roadmaps de `mod-engineering/` e `visual-assets/` são mapas de execução derivados dos respectivos planos mestres e do `STATUS.md`; não criam uma segunda authority.

O roadmap de `narrative-authoring/` acompanha a capability reutilizável existente em `narrative/` e usa implementação/testes na `main` como evidência para ✅. O plano histórico [`2026-09-13-narrative-authoring-migration.md`](./2026-09-13-narrative-authoring-migration.md) registra a migração inicial da ferramenta narrativa para a Factory.