# Auditoria — separação de Textura/Apresentação dos planos

**Data:** 2026-09-13  
**Repositório:** `Gustavaopere/minecraft-mod-factory`  
**Main inicialmente auditada:** `e7f92897f3492cc64e14c27b827b419a33bb2e5d`  
**Tree base inicial:** `88f3742bccba3cc5bd239fc316d4b7ea77c2c926`  
**Main reconciliada durante o ciclo:** `8981771689535288e4792d1cba17a95b59c37a03`  
**Alvo:** Minecraft 1.21.1 / NeoForge `21.1.248` / Java 21  
**Modlist física disponível no projeto:** 595 entradas top-level; continua authority para presença/versão.

## Fontes verificadas antes da reorganização

- modlist física mais recente disponível no projeto;
- Auditoria Mestre da Modlist no Notion;
- `main` da Factory;
- `STATUS.md`;
- `plans/`;
- plano Mod Engineering V1.1;
- plano Repo Textura V5.1;
- PRs abertas procurando trabalho equivalente de separação de planos.

Na checagem inicial não havia PR equivalente visível. Durante a execução surgiu a PR #104, `docs(plans): organize roadmaps by domain`, baseada na mesma `main` inicial e tocando `plans/README.md`, `plans/mod-engineering/` e `plans/visual-assets/`. Ela foi tratada como trabalho concorrente relevante, não descartada.

A PR #104 foi então mergeada em `main` por fluxo concorrente (`8981771689535288e4792d1cba17a95b59c37a03`). A branch desta reorganização foi sincronizada novamente com essa `main` e o conflito de topologia foi resolvido semanticamente: o roadmap de Engineering permaneceu em `plans/mod-engineering/` e o roadmap visual foi preservado integralmente sob `plans/textura/roadmap/`, evitando uma segunda authority artística fora da pasta canônica.

## Achado

A Factory já possuía `art/` como authority física de tooling/assets e `engineering/` como authority técnica, porém os dois planos mestres estavam juntos na raiz de `plans/` e o plano de Engineering ainda continha especificações detalhadas de apresentação.

Isso criava três problemas:

1. novos chats podiam tratar detalhes visuais do Engineering como authority artística concorrente;
2. UI/HUD, animação, VFX e áudio ficavam espalhados;
3. uma feature mista podia ser planejada novamente como documento monolítico.

## Correção aplicada

- criada `plans/textura/`;
- movido o plano artístico V5.1 para a nova subpasta preservando o blob original;
- mantida na raiz somente uma ponte de compatibilidade para o path antigo;
- preservado o plano Engineering V1.1 misto integral em `docs/archive/plans/`;
- reescrito o plano Engineering ativo como documento runtime-only no mesmo path para evitar quebrar referências existentes;
- criada fronteira normativa Engineering ↔ Textura;
- criado/reconciliado o índice `plans/README.md`;
- preservado `plans/mod-engineering/` vindo da PR #104;
- realocado, sem alterar conteúdo dos milestones, `plans/visual-assets/` para `plans/textura/roadmap/` após a PR #104 entrar em `main`.

## Classificação de authority

### Textura/Apresentação

UI/HUD visual, texturas, materiais, modelos, UV, rigs, animações, VFX/partículas visuais, áudio/SFX, icons, cinematics, concept art, Golden Samples e QA visual/sonoro.

### Engineering / repo do mod

Gameplay, state, networking, persistence, menu backend, input validation, registries, provider adapters, worldgen, AI, processing, data authority e testes de runtime.

### Compartilhado somente por contrato

Estados/eventos/anchors, namespace/resource paths, provider profile, performance constraints e runtime smoke de integração.

## Preservação

Nenhum conteúdo histórico foi descartado:

- o plano artístico foi movido por referência ao mesmo blob Git;
- o plano Engineering misto original foi arquivado pelo mesmo blob Git;
- o plano ativo de Engineering contém somente a versão separada da responsabilidade técnica;
- os roadmaps da PR #104 foram preservados, com o domínio visual apenas realocado para dentro de `plans/textura/`.

## Sincronização Git

- `main` inicial: `e7f92897f3492cc64e14c27b827b419a33bb2e5d`;
- PR #104 head incorporado: `363deed4be9de8f74a07f4a3ec598f00c0f156dd`;
- merge da PR #104 em `main`: `8981771689535288e4792d1cba17a95b59c37a03`;
- branch de separação reconciliada com essa `main` sem rebase/force-push e preservando ambos os trabalhos.

## Alteração de runtime

`N/A` — reorganização documental; nenhum código de mod, provider, asset binário ou pipeline de runtime foi alterado neste ciclo.
