# Planos — Minecraft Mod Factory

Os planos ativos são separados por authority, com mapas operacionais derivados para navegação rápida.

## Legenda de estado dos roadmaps

- ✅ — milestone encerrado com evidência aceita no `STATUS.md` canônico ou no gate correspondente.
- 🔄 — fronteira atual de execução; ainda não concluída.
- ⬜ — milestone pendente/não iniciado.
- ⛔ — bloqueado por um gate explícito.

Os ícones resumem o milestone; não promovem `REFERENCE_ONLY`, `DEFERRED`, `UNAVAILABLE` ou runtime não comprovado para `PASS`.

## Mod Engineering

Plano canônico de runtime/integração:

`PLANO-MESTRE-MINECRAFT-MOD-FACTORY-MOD-ENGINEERING-NEOFORGE-1.21.1-V1.1.md`

Escopo: runtime, arquitetura, integração, networking, persistência, providers, testes, CI, performance e release.

Mapa operacional preservado da PR #104:

`mod-engineering/`

## Textura / Apresentação

Toda a authority de planejamento de apresentação fica em:

`textura/`

Inclui UI/HUD visual, texturas, materiais, modelos, Blockbench, UV, rigs, animações, VFX/partículas, áudio/SFX, ícones, cinematics, visual QA e sound QA.

O plano mestre artístico V5.1 foi movido para essa subpasta. A antiga entrada na raiz existe somente como ponte de compatibilidade.

O roadmap artístico criado na PR #104 foi preservado dentro da mesma authority em:

`textura/roadmap/`

## Regra de separação

- comportamento/runtime → Engineering ou repo do mod;
- aparência/animação/som/apresentação → `plans/textura/`;
- conteúdo misto → duas especificações conectadas por contrato de handoff.

Os roadmaps são índices operacionais derivados. Não criam segunda authority e não substituem os planos canônicos.
