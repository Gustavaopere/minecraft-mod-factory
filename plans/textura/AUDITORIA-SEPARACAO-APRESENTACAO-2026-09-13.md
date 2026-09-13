# Auditoria — separação de Textura/Apresentação dos planos

**Data:** 2026-09-13  
**Repositório:** `Gustavaopere/minecraft-mod-factory`  
**Main auditada:** `e7f92897f3492cc64e14c27b827b419a33bb2e5d`  
**Tree base:** `88f3742bccba3cc5bd239fc316d4b7ea77c2c926`  
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

Nenhuma PR aberta equivalente foi encontrada para esta reorganização. PRs de outras frentes não foram reutilizadas.

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
- criado índice `plans/README.md`.

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
- o plano ativo de Engineering contém somente a versão separada da responsabilidade técnica.

## Alteração de runtime

`N/A` — reorganização documental; nenhum código de mod, provider, asset binário ou pipeline de runtime foi alterado neste ciclo.
