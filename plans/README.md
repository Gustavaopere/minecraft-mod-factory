# Planos — Minecraft Mod Factory

Os planos ativos são separados por authority.

## Mod Engineering

Entrada compatível/canônica de engenharia:

`PLANO-MESTRE-MINECRAFT-MOD-FACTORY-MOD-ENGINEERING-NEOFORGE-1.21.1-V1.1.md`

Escopo: runtime, arquitetura, integração, networking, persistência, providers, testes, CI, performance e release.

## Textura / Apresentação

Todo planejamento de apresentação fica em:

`textura/`

Inclui UI/HUD visual, texturas, materiais, modelos, Blockbench, UV, rigs, animações, VFX/partículas, áudio/SFX, ícones, cinematics, visual QA e sound QA.

O plano mestre artístico V5.1 foi movido para essa subpasta. A antiga entrada na raiz existe somente como ponte de compatibilidade.

## Regra de separação

- comportamento/runtime → Engineering ou repo do mod;
- aparência/animação/som/apresentação → `plans/textura/`;
- conteúdo misto → duas especificações conectadas por contrato de handoff.

Não colocar novos detalhes artísticos no plano de Engineering.
