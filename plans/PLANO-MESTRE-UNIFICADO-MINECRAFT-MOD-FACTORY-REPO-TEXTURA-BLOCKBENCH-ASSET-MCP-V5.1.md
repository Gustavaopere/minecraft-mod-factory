# PLANO MESTRE UNIFICADO — MINECRAFT MOD FACTORY / REPO TEXTURA — V5.1
## Blockbench Live Bridge / Asset MCP / pipeline artístico multi-provider / continuidade entre chats

**Projeto canônico:** Minecraft Mod Factory — domínio artístico `Repo Textura`  
**Repositório canônico:** `Gustavaopere/minecraft-mod-factory`  
**Remote Git canônico:** `https://github.com/Gustavaopere/minecraft-mod-factory.git`  
**Alvo do modpack:** Minecraft 1.21.1 / NeoForge 1.21.1 / Java 21  
**Escopo:** exclusivamente infraestrutura artística e assets: direção de arte, modelos, texturas, UV, rigs, bones, pivôs, animações, VFX/SFX anchors, export/handoff, QA, Blockbench, Blender quando necessário e automação assistida por IA  
**Fora de escopo:** gameplay, perks, quests, balanceamento, dano, stamina, cooldown, lógica funcional, IA de combate e demais regras server-authoritative  
**Revisão:** 5.1 — remote canônico resolvido + migração para Minecraft Mod Factory + continuidade + pipeline artístico multi-provider + produção visual de mods complexos/tecnológicos  
**Regra principal:** este arquivo deve permitir que um chat futuro continue o trabalho sem depender de contexto conversacional anterior.

**Autoridade deste planejamento:** esta V5 substitui as versões V1–V4 como roteiro operacional. Planos anteriores podem ser preservados apenas como histórico; quando houver divergência de planejamento, esta V5 vence, enquanto GitHub/árvore real/modlist física continuam vencendo para fatos de implementação e presença de providers.

**Objetivo ampliado de produção:** o Repo Textura deve conseguir produzir o **pacote artístico completo** necessário para mods simples ou extremamente complexos — inclusive máquinas animadas, multiblocos, redes visuais, equipamentos, drones, lasers, portas, estruturas, UI visual, VFX e famílias inteiras de assets no nível de apresentação de grandes tech mods — sem assumir a lógica funcional do mod.

## DECISÃO ARQUITETURAL CANÔNICA — V5.1

A partir desta revisão, existe um único repositório Git canônico para a infraestrutura reutilizável de produção de mods:

```text
Gustavaopere/minecraft-mod-factory
```

URL:

```text
https://github.com/Gustavaopere/minecraft-mod-factory.git
```

Dentro desse repositório coexistem duas authorities **lógicas**, não dois repositórios físicos obrigatórios:

```text
Minecraft Mod Factory
├── domínio artístico — "Repo Textura"
└── domínio de engenharia — "Mod Engineering / Integration Control Plane"
```

Regras:

- **Repo Textura** continua sendo o nome da authority artística, mas passa a significar o domínio artístico dentro de `minecraft-mod-factory`;
- **Mod Engineering / Repo Integração** passa a significar o domínio de engenharia dentro do mesmo `minecraft-mod-factory`;
- os limites entre arte e engenharia continuam contratuais e não podem ser apagados só porque compartilham o mesmo Git repository;
- os repositórios de cada mod continuam separados e continuam sendo authority do runtime daquele mod;
- `Gustavaopere/neoforge-rpg-skilltree` continua sendo authority do runtime do RPG e passa a ser apenas **origem histórica de migração** para a infraestrutura comum;
- nenhuma nova infraestrutura comum de Blockbench/assets/engineering deve ser iniciada no RPG após o cutoff de migração, salvo correção necessária para fechar/migrar trabalho já existente;
- nenhum arquivo deve ser apagado do RPG antes de a cópia/adaptação equivalente estar validada na Factory;
- `.bbmodel` e demais formatos-fonte continuam preservados; nenhuma conversão pode ocorrer silenciosamente.

### Cutoff histórico confirmado para a frente artística

- PR #487 — Read-only Live Bridge: `MERGED`;
- PR #488 — Modeling + Rig Mutations: `MERGED`;
- PR4 foi implementada em slices subsequentes;
- PR #507 — bounded UV island masks: `MERGED`;
- `neoforge-rpg-skilltree/main` após #507: `c4b093724228e408d91820d0bfa03bef9d3eb3bf`;
- PR #508 — palette sampling: aberta como **TDD RED test-only** no momento desta revisão.

Decisão para #508:

> não adicionar implementação de produção nova no RPG. Preservar a especificação RED útil e migrar/reconciliar esse trabalho para `minecraft-mod-factory` depois do bootstrap/migração da fundação artística.

> IMPORTANTE: os estados abaixo são um snapshot de continuidade. Antes de executar qualquer etapa, o agente deve verificar o GitHub e a modlist física novamente. O snapshot não substitui evidência atual.

---

# PARTE I — CONTINUIDADE, HISTÓRICO E ORDEM EXATA DE EXECUÇÃO

## 0. COMO USAR ESTE DOCUMENTO

Todo chat que receber este plano deve seguir esta ordem antes de escrever código, criar branch, editar asset ou instalar extensão:

1. ler esta **Parte I** inteira;
2. verificar qual etapa está marcada como última concluída;
3. consultar o GitHub para confirmar se PRs/branches citadas mudaram de estado;
4. confirmar acesso ao remote canônico `Gustavaopere/minecraft-mod-factory` e resolver seu HEAD atual;
5. conferir a modlist física mais recente;
6. conferir a árvore, documentação, Golden Samples, Visual Style Bible, contracts e tooling atuais do domínio artístico na Minecraft Mod Factory;
7. procurar trabalho concorrente equivalente;
8. atualizar o registro de continuidade;
9. executar **somente a primeira etapa ainda necessária**;
10. não repetir trabalho concluído sem evidência de regressão ou necessidade de migração.

Se o contexto da conversa estiver incompleto, este documento prevalece como roteiro operacional, mas fatos temporais devem ser revalidados.

---

## 0.1. ESTADO GLOBAL NO MOMENTO DESTA REVISÃO

**Nota V5.1:** o remote anteriormente pendente foi criado e autorizado explicitamente pelo usuário.

Repositório canônico da infraestrutura comum:

`Gustavaopere/minecraft-mod-factory`

Remote:

`https://github.com/Gustavaopere/minecraft-mod-factory.git`

Estado verificado no momento desta revisão:

```text
REPOSITORY_FULL_NAME=Gustavaopere/minecraft-mod-factory
VISIBILITY=private
DEFAULT_BRANCH=main
REPOSITORY_SIZE=0
BASE_SHA=UNRESOLVED_EMPTY_REPOSITORY
```

O repositório foi criado vazio, sem README, `.gitignore` ou licença gerados automaticamente. Portanto, `main` está declarada como default branch, mas ainda não existe um commit inicial que possa servir de `BASE_SHA`.

O trabalho artístico existente continua historicamente em:

`Gustavaopere/neoforge-rpg-skilltree`

Esse repositório é agora:

- authority do runtime do mod RPG;
- origem histórica para migração da infraestrutura artística já implementada;
- **não** é mais o destino para novas capabilities comuns do pipeline artístico.

A authority artística canônica é o domínio `Repo Textura` dentro de `Gustavaopere/minecraft-mod-factory`.

Não procurar nem criar um segundo repositório chamado “Repo Textura” enquanto esta decisão V5.1 permanecer vigente.

---

## 0.2. HISTÓRICO IMPLEMENTADO NO REPOSITÓRIO RPG

As PRs abaixo formam a linhagem histórica que precisa ser conhecida para não refazer trabalho.

| Marco histórico | Estado verificado | Papel no pipeline |
|---|---|---|
| PR #479 — audited Minecraft AI skill infrastructure | MERGED | infraestrutura de skills, router, protocolo de uma etapa manual por vez |
| PR #480 — art direction and Blockbench pipeline | MERGED | art direction, MODEL-ASSET-CONTRACT, VISUAL-QA, helper Blockbench read-only |
| PR #482 — spell VFX and audio skills | MERGED | contracts e QA de apresentação/VFX/áudio |
| PR #483 — complete Minecraft art pipeline and Blockbench toolkit | MERGED | Visual Style Bible, templates, skills finais, RPG Asset Toolkit read-only |
| PR #484 — Minecraft art Golden Samples | MERGED | corpus de referência + validator Golden Samples |
| PR #486 — modular core and provider/extension registry | MERGED | **PR1 do plano Blockbench/MCP** |
| PR #487 — read-only Live Bridge | MERGED | **PR2 do plano Blockbench/MCP** |
| PR #485 — Parchment repository filter | ABERTA, NÃO RELACIONADA | infraestrutura Gradle do repo RPG; não deve bloquear a frente artística |

### Regra de interpretação

PRs #479–#486 representam trabalho já feito e **não devem ser reimplementadas do zero**.

PR #487 deixou de ser a fronteira: foi mergeada. A frente avançou por PR3 e múltiplos slices de PR4 até a PR #507; a PR #508 é o primeiro trabalho ainda aberto no cutoff V5.1.

A PR #485 é uma tangente de CI/Gradle do repo RPG. Ela não pertence ao roadmap artístico e não deve voltar a consumir a frente do Repo Textura.

---

## 0.3. PONTO EXATO DE CONTINUIDADE E CUTOFF DE MIGRAÇÃO

A sequência histórica comprovada no repositório RPG chegou além do snapshot original deste plano:

```text
#479–#486 — fundação artística histórica
   ↓
#487 — PR2 Read-only Live Bridge — MERGED
   ↓
#488 — PR3 Modeling + Rig Mutations — MERGED
   ↓
PR4 — UV + Texture — CAPABILITY_PARTIAL em slices
   ↓
#490 — bounded UV/texture mutations — MERGED
   ↓
#495 — read-only UV analysis — MERGED
   ↓
#498 — texture path validation — MERGED
   ↓
#499 — UV algorithm pack — MERGED
   ↓
#502 — texture create/import — MERGED
   ↓
#505 — bounded texture paint region — MERGED
   ↓
#507 — bounded UV island masks — MERGED
   ↓
CUTOFF RPG main = c4b093724228e408d91820d0bfa03bef9d3eb3bf
   ↓
#508 — deterministic palette sampling — OPEN / TDD RED TEST-ONLY
   ↓
MIGRAÇÃO / RECONCILIAÇÃO PARA minecraft-mod-factory
   ↓
continuar PR4 restante na Factory
   ↓
fechar gates finais de PR4
   ↓
PR5 — Generic Animation Core
   ↓
PR6+ — adapters e QA conforme este plano
```

### Regra obrigatória de transição

1. não desenvolver a implementação de produção da PR #508 no RPG;
2. preservar o teste/spec RED de #508 como evidência de requisito;
3. materializar primeiro a fundação canônica na `minecraft-mod-factory`;
4. migrar/reconciliar o Asset Toolkit e seus contratos/testes;
5. só então continuar palette tools e o restante da PR4 na Factory;
6. não iniciar PR5 antes de PR4 cumprir seus gates finais.

### Repositório RPG após o cutoff

O RPG não deve receber novos componentes genéricos do pipeline artístico. Correções no RPG só são permitidas quando necessárias para:

- preservar o runtime próprio do RPG;
- fechar segurança/integridade de uma mudança histórica;
- preparar uma migração verificável;
- evitar perda de trabalho existente.

Nenhuma dessas exceções devolve ao RPG a autoridade da infraestrutura comum.

---

# 1. FASE M0 — REMOTE CANÔNICO RESOLVIDO / BOOTSTRAP PENDENTE

Objetivo: materializar `minecraft-mod-factory` como destino Git operacional.

Estado já resolvido:

```text
REPO_TEXTURA_REMOTE=https://github.com/Gustavaopere/minecraft-mod-factory.git
REPOSITORY_FULL_NAME=Gustavaopere/minecraft-mod-factory
DEFAULT_BRANCH=main
VISIBILITY=private
BASE_SHA=UNRESOLVED_EMPTY_REPOSITORY
HISTORICAL_SOURCE_REPO=Gustavaopere/neoforge-rpg-skilltree
HISTORICAL_ART_CUTOFF_SHA=c4b093724228e408d91820d0bfa03bef9d3eb3bf
ACTIVE_HISTORICAL_ART_PR=#508_TEST_ONLY_RED
```

Passos pendentes:

1. criar o primeiro commit canônico da Factory;
2. resolver o primeiro `BASE_SHA`;
3. registrar README/AGENTS/STATUS/planos no layout escolhido;
4. listar branches e PRs após o bootstrap;
5. registrar a árvore real antes de migrar arquivos;
6. não inventar diretórios antecipadamente;
7. iniciar a matriz de migração a partir do cutoff histórico.

Gate:

- o blocker `REMOTE DO REPO TEXTURA NÃO RESOLVIDO` está **SUPERSEDED**;
- o blocker atual é `FACTORY_EMPTY_REPOSITORY_BOOTSTRAP_PENDING`;
- nenhum trabalho de produção novo da PR4 deve avançar no RPG enquanto a fundação equivalente não estiver migrada.

---

# 2. FASE M1 — AUDITORIA DA ÁRVORE CANÔNICA DO REPO TEXTURA

Antes de copiar qualquer arquivo do repo RPG:

1. listar diretórios do Repo Textura;
2. localizar:
   - README/AGENTS/instruções;
   - Visual Style Bible;
   - standards/contracts;
   - skills, se existirem;
   - tools;
   - scripts/validators;
   - Golden Samples;
   - assets source;
   - exports/staging;
3. descobrir naming convention;
4. descobrir onde `.bbmodel`, texturas, animações e manifests pertencem;
5. detectar duplicação com o repo histórico.

Não criar automaticamente:

- `PROJECT-INSTRUCTIONS/`;
- `skills/`;
- `standards/`;
- `tools/`;

apenas porque esses caminhos existiam no repo RPG.

O Repo Textura decide a estrutura final.

---

# 3. FASE M2 — INVENTÁRIO DO QUE EXISTE NO REPO RPG

Auditar especificamente os deltas das PRs:

- #479;
- #480;
- #482;
- #483;
- #484;
- #486;
- #487, se aplicável.

Classificar cada arquivo/feature em:

`MIGRATE_CANONICAL`  
`MIGRATE_ADAPTED`  
`REFERENCE_ONLY`  
`RPG_SPECIFIC_DO_NOT_MIGRATE`  
`SUPERSEDED`  
`DUPLICATE_IN_REPO_TEXTURA`

Exemplos esperados de itens potencialmente migráveis:

- Visual Style Bible e fontes visuais;
- MODEL-ASSET-CONTRACT;
- Visual QA;
- VFX QA;
- templates de assets/model/animação/VFX;
- Golden Samples project-owned;
- core/validator do Asset Toolkit;
- Provider Profile Registry;
- Extension Capability Registry;
- Live Bridge read-only, se concluído;
- schemas/protocol/security docs;
- testes artísticos.

Exemplos que não devem ser trazidos só por proximidade:

- gameplay do RPG;
- perks;
- skill tree;
- Gradle Parchment fix;
- Battle Mage;
- dependências runtime não artísticas;
- workflows que só existem para o repo RPG.

---

# 4. FASE M3 — MATRIZ DE MIGRAÇÃO

Antes de copiar, criar uma tabela real:

| Origem | Destino Repo Textura | Classificação | Adaptação necessária | Teste | Status |
|---|---|---|---|---|---|

Nenhum arquivo entra por “copiar pasta inteira”.

Toda migração precisa preservar:

- autoria/proveniência;
- histórico relevante;
- licença;
- source primário;
- semântica;
- tests quando aplicável.

---

# 5. FASE M4 — MIGRAÇÃO DA FUNDAÇÃO ARTÍSTICA

Ordem recomendada:

1. contracts e standards;
2. Visual Style Bible;
3. templates;
4. validators/core read-only;
5. provider/extension registry;
6. Golden Samples;
7. Live Bridge read-only;
8. documentação/protocol/security;
9. CI específico do Repo Textura.

Depois de cada bloco:

- validar paths;
- validar links;
- rodar testes;
- revisar diff;
- só então continuar.

Não migrar todo o histórico em uma mega-PR se isso prejudicar revisão.

---

# 6. FASE M5 — RENOMEAÇÃO E DESACOPLAMENTO DO “RPG ASSET TOOLKIT”

Objetivo:

`RPG Asset Toolkit / RPG Asset MCP`

passa conceitualmente para:

`Repo Textura Asset Toolkit / Repo Textura Asset MCP`

Porém a migração deve preservar compatibilidade quando código histórico ainda depender dos nomes antigos.

Regras:

- não fazer rename destrutivo sem mapear imports/entrypoints/docs/tests;
- se necessário, manter shim temporário;
- remover o shim só depois da migração completa;
- nenhum mod runtime deve depender do MCP/Blockbench tooling.

---

# 7. FASE M6 — GOLDEN SAMPLES NO REPO TEXTURA

Os Golden Samples #484 são referência histórica útil, mas não devem ser copiados cegamente.

Auditar:

- ownership;
- provider;
- formato;
- se já existe sample melhor no Repo Textura;
- se o sample é apenas normalizado e não `.bbmodel`;
- claims de QA;
- dependências de paths do repo RPG.

Depois:

- migrar/adaptar apenas samples úteis;
- manter `REFERENCE-ONLY` quando não houver runtime proof;
- não converter fixtures em falsa evidência visual/in-game.

---

# 8. FASE M7 — STATUS CANÔNICO DE CONTINUIDADE

No domínio Repo Textura da Minecraft Mod Factory deve existir um arquivo de estado equivalente a:

`plans/STATUS.md`, `docs/STATUS.md` ou o caminho canônico que o próprio repo adotar.

Ele deve conter:

```text
CURRENT_PHASE
CURRENT_PR
CURRENT_BRANCH
BASE_SHA
HEAD_SHA
LAST_COMPLETED_PHASE
NEXT_PHASE
BLOCKERS
MANUAL_ACTION_REQUIRED
LATEST_MODLIST_SNAPSHOT
BLOCKBENCH_VERSION
```

Esse status deve ser atualizado a cada PR.

Objetivo: impedir que um chat futuro dependa de memória.

---

# 9. MAPA ENTRE O PLANO ANTIGO E O PLANO NOVO

O plano V1 possuía PRs A–G.

O plano multi-provider expandiu isso para PR1–PR14.

Mapeamento:

| Plano V1 | Plano mestre atual |
|---|---|
| PR A — Core modular + protocol | PR1 + parte da segurança/protocol; implementado historicamente em #486 |
| PR B — Read-only Live Bridge | PR2; implementação histórica em #487 |
| PR C — Modeling mutations | PR3 |
| PR D — UV + texture | PR4 |
| PR E — Animation + GeckoLib | dividido em PR5 Generic Animation + PR6 GeckoLib |
| PR F — Capture + Visual QA | distribuído entre PR5 e PR14 |
| PR G — Export + handoff | distribuído entre adapters específicos + PR14 |

Nada foi “apagado” do plano antigo. Ele foi decomposto para evitar acoplamento GeckoLib-cêntrico.

---

# 10. ROADMAP PÓS-MIGRAÇÃO — ORDEM OBRIGATÓRIA

## PR3 — MODELING + RIG MUTATIONS

Só começar quando:

- foundation migrada;
- read-only bridge disponível;
- status canônico criado.

Entregas:

- create/update/reparent bone;
- create/update/reparent cube;
- locators;
- pivots;
- hierarchy validation;
- revision;
- operation ID;
- Undo;
- rollback;
- bounded batch mutations.

Testes obrigatórios:

- stale revision;
- cycles;
- nonexistent IDs;
- rollback;
- Undo/Redo;
- duplicate operation replay;
- Golden Sample mutation smoke.

Não avançar para UV enquanto PR3 não possuir evidência real de transação segura.

---

## PR4 — UV + TEXTURE

Entregas:

- inspect UV;
- Box UV;
- per-face UV;
- pack preview/apply;
- overlap validation;
- texel density measurement;
- create/import texture;
- bounded paint;
- UV island masks;
- palette tools;
- texture validation.

Restrições:

- nenhuma pintura global arbitrária;
- source preservado;
- deterministic operations;
- seed quando houver randomness;
- dry-run para repack global.

Gate final:

- round-trip;
- visual diff;
- undo;
- texture-path validation.

---

## PR5 — GENERIC ANIMATION CORE

Entregas:

- create/update/delete animation;
- keyframes;
- loop;
- easing;
- duration;
- effect markers abstratos;
- preview;
- pose inspection;
- capture;
- loop seam validation;
- foot-slide diagnostics quando mensurável.

Regra:

generic animation não pertence a GeckoLib, AzureLib ou outro provider.

O provider adapter decide como serializar.

---

## PR6 — GECKOLIB ADAPTER

Alvo físico conhecido historicamente:

- GeckoLib 4.9.2.

Entregas:

- geckolib profiles;
- extension compatibility;
- model/animation codec/export;
- effect keyframes;
- locators;
- Golden regression;
- runtime handoff.

Não:

- transplantar GeckoLib 5;
- converter AzureLib automaticamente;
- usar animation timeline como gameplay authority.

---

## PR7 — AZURELIB ADAPTER

Alvo físico conhecido historicamente:

- AzureLib 3.1.11.

Entregas:

- profiles independentes;
- AzureLib extension resolver;
- custom easing awareness;
- IK/FABRIK authoring capability apenas se realmente comprovada;
- export;
- runtime QA.

GeckoLib ≠ AzureLib.

---

## PR8 — NEOFORGE NATIVE ANIMATION

Só iniciar após prova técnica para o target exato NeoForge 1.21.1.

Entregas condicionais:

- native profile;
- Animation-to-JSON adapter ou alternativa comprovada;
- schema/runtime consumer;
- build test;
- runtime smoke.

Se a API/runtime target não estiver comprovada:

`UNAVAILABLE / DEFERRED`

Não inventar integração.

---

## PR9 — EASY MODEL ENTITIES

Runtime físico histórico:

- Easy Model Entities 2.3.0.

Antes:

- reinspecionar JAR/source;
- verificar exporter Blockbench atual;
- verificar maturidade/release.

Entregas:

- entity profile;
- block entity profile;
- `.bbmodel` preservation;
- provider-specific validation;
- resource/datapack handoff;
- spawn/place smoke.

---

## PR10 — EMF/CEM

Runtime físico histórico:

- Entity Model Features 3.3.5.

Entregas:

- CEM profile;
- CEM Template Loader compatibility;
- EMF Animation Addon quando compatível;
- resource-pack export;
- runtime pack load;
- animation smoke.

Não usar EMF como atalho para assets mod-owned GeckoLib/AzureLib.

---

## PR11 — ANIMATED JAVA

Entregas:

- display-entity profile;
- blueprint/rig/variant awareness;
- locators;
- cameras;
- effect/function keyframes;
- datapack/resource-pack staging;
- runtime smoke.

Uso principal:

- cutscenes;
- props;
- world presentation;
- cinematics;
- scripted presentation.

Não substituir entidades server-authoritative quando inadequado.

---

## PR12 — PLAYER PROFILES

Cobrir separadamente:

### CPM
- plugin beta;
- import/export round-trip;
- `.cpmproject` preservation;
- human-confirm initially.

### Player Animation Library
- handoff de formato comprovado;
- runtime consumer profile.

### Player Animator
- API audit;
- perfil separado.

Não converter PAL ↔ Player Animator automaticamente.

---

## PR13 — EXTERNAL DCC / BLENDER / EPIC FIGHT

Epic Fight continua Blender-authoritative para custom combat animation.

Pipeline:

```text
Blockbench concept/reference/model
→ handoff manifest
→ Blender
→ Epic Fight rig/exporter
→ runtime
```

Entregas do Repo Textura:

- source/reference;
- naming/bone mapping;
- texture references;
- export/handoff manifest;
- Blender source project-owned quando pertinente;
- QA.

Não criar falsa exportação Epic Fight direto do Blockbench.

---

## PR14 — UNIFIED QA + EXPORT MANIFEST

Unificar:

- structural QA;
- visual QA;
- capture evidence;
- provider fingerprint;
- extension fingerprint;
- source hashes;
- export roots;
- staging;
- semantic diff;
- runtime target;
- handoff destinations.

Critério:

nenhum asset é considerado final apenas porque exportou.

---

# 11. INSTALAÇÃO REAL NO BLOCKBENCH — SOMENTE DEPOIS DA INFRAESTRUTURA

Quando a infraestrutura estiver pronta, a instalação no computador do usuário deve ser guiada.

Regra absoluta:

> uma única ação manual verificável por vez.

Nunca enviar 15–20 passos em uma resposta.

Sequência:

1. confirmar versão real do Blockbench;
2. usuário envia resultado/screenshot;
3. validar;
4. instalar/carregar Repo Textura Asset Toolkit;
5. usuário confirma;
6. testar status read-only;
7. só então instalar preset Base Safe;
8. validar;
9. instalar apenas o provider necessário ao primeiro Golden Sample;
10. smoke;
11. continuar.

Não instalar todos os plugins ao mesmo tempo.

---

# 12. PROTOCOLO DE RETOMADA PARA QUALQUER CHAT FUTURO

Ao receber algo como “PROSSIGA O REPO TEXTURA”, o agente deve:

1. abrir este plano;
2. localizar o status canônico no Repo Textura;
3. consultar PR/branch atual no GitHub;
4. comparar o snapshot deste plano com o estado real;
5. conferir a modlist física;
6. identificar a primeira etapa incompleta;
7. declarar em uma frase:
   - `ÚLTIMA ETAPA CONFIRMADA: ...`
   - `ETAPA ATUAL: ...`
   - `PR/BRANCH: ...`
8. executar somente essa etapa;
9. validar;
10. atualizar status;
11. só então avançar.

Se houver divergência:

`PARAR → RECONCILIAR → REGISTRAR → CONTINUAR`

Não inferir que “provavelmente terminou”.

---

# 13. FORMATO DE STATUS QUE DEVE SER MANTIDO

Exemplo:

```markdown
# STATUS — Repo Textura Asset Pipeline

Atualizado: YYYY-MM-DD HH:MM TZ

## Estado
- Fase: PR4 — UV + Texture
- Branch: feat/...
- PR: #...
- Base SHA: ...
- HEAD SHA: ...
- Última fase concluída: PR3
- Próxima fase: PR5
- Blocker: nenhum
- Ação manual pendente: não

## Evidência
- tests: PASS
- structural QA: PASS
- visual QA: PENDING
- in-game QA: N/A nesta fase

## Não fazer
- não iniciar PR5 antes do merge desta PR
- não mexer em branch concorrente X
```

---

# 14. POLÍTICA DE NÃO-REPETIÇÃO

Um chat futuro não deve:

- refazer Golden Samples já válidos;
- recriar Provider Registry já migrado;
- criar outro Live Bridge paralelo;
- reescrever contracts equivalentes;
- renomear tudo novamente;
- repetir pesquisa de plugin completa sem motivo de freshness.

Deve repetir auditoria somente quando:

- versão mudou;
- modlist mudou;
- Blockbench mudou;
- extensão mudou;
- provider mudou;
- regressão apareceu;
- fonte anterior estava incompleta.

---

# 15. POLÍTICA DE EVIDÊNCIA

Estados permitidos:

`CONFIRMED`  
`IMPLEMENTED`  
`MERGED`  
`PASS`  
`PENDING`  
`UNAVAILABLE`  
`UNRESOLVED`  
`DEFERRED`  
`REFERENCE_ONLY`

Não usar “pronto” sem gate correspondente.

Exemplos:

- GitHub merged ≠ in-game PASS;
- JSON válido ≠ visual PASS;
- plugin instalado ≠ compatible;
- provider presente ≠ API comprovada;
- mock test ≠ Blockbench real smoke;
- Blockbench preview ≠ Minecraft runtime QA.

---

# 16. SNAPSHOT FÍSICO DE CONTINUIDADE

A modlist anexada nesta revisão contém **595 mods top-level** e continua sendo autoridade auxiliar de presença/versão.

Evidência relevante confirmada no snapshot atual:

- GeckoLib 4 — 4.9.2;
- AzureLib — 3.1.11;
- Easy Model Entities — 2.3.0;
- Entity Model Features — 3.3.5;
- Player Animation Library — 1.1.6+mc.1.21.1;
- Player Animator — 2.0.4+1.21.1;
- Photon — 2.2.6.a;
- Lodestone — 1.8.2;
- Create — 6.0.10.

AAA Particles/AAA Particles World **não foram confirmados no snapshot físico atual** durante esta revisão e devem ser tratados como ausentes até nova evidência.

A lista deve ser revalidada antes de cada adapter/provider milestone.

---

# 17. RESULTADO DESEJADO DESTE PLANO MESTRE

Este documento passa a substituir, como roteiro operacional:

- o plano V1 GeckoLib-cêntrico;
- o plano V2 multi-provider;
- a revisão V3 adaptada para Repo Textura;

sem apagar o valor histórico deles.

A diferença é que esta versão registra também:

- o que já foi implementado;
- onde foi implementado;
- o que ainda está em andamento;
- quando parar de trabalhar no repo RPG;
- como migrar;
- como retomar sem memória;
- qual PR vem depois;
- quais gates impedem avanço prematuro.

---



# PARTE I-B — EXPANSÃO V5: PRODUÇÃO VISUAL DE MODS COMPLEXOS E TECNOLÓGICOS

## 18. POR QUE ESTA EXPANSÃO EXISTE

O objetivo não é apenas conseguir criar um mob, uma arma ou uma animação isolada.

O Repo Textura precisa ser capaz de fornecer a camada artística completa para mods próprios de grande escala, incluindo projetos com complexidade visual comparável a grandes mods tecnológicos.

Benchmark de referência: **Oritech**.

Fontes verificadas nesta revisão:

- CurseForge descreve Oritech como mod tecnológico com máquinas animadas, opções de processamento, logística, ferramentas/equipamentos, máquinas majoritariamente multibloco, portas animadas, connected textures, drones, lasers e grandes sistemas;
- o repositório oficial declara explicitamente:
  - **GeckoLib** para animações;
  - **Blockbench** para criação e animação dos modelos;
- existe release NeoForge para Minecraft 1.21.1 no ecossistema atual.

Referências:
- https://www.curseforge.com/minecraft/mc-mods/oritech
- https://github.com/Rearth/Oritech

Oritech é **benchmark de capacidade**, não template para copiar assets, arquitetura ou código.

---

## 19. CORREÇÃO DA IDEIA “PARA FAZER UM MOD TIPO ORITECH PRECISA SÓ DE JAVA”

Para produzir o mod completo, Java/NeoForge realmente é necessário para lógica funcional.

Porém isso é apenas uma parte do produto.

Um mod tecnológico visualmente sofisticado exige ao menos dois grandes domínios:

```text
REPO TEXTURA
    ↓
arte / authoring / animação / render specification / VFX / UI visual / QA
    ↓
HANDOFF CONTRACT
    ↓
REPOSITÓRIO DO MOD
    ↓
Java / NeoForge / BlockEntity / energia / receitas / redes / gameplay / sincronização
```

Este projeto cobre integralmente o primeiro domínio.

Ele NÃO implementa:

- armazenamento de energia;
- recipes/processamento;
- ticking;
- inventory logic;
- fluid logic;
- capability/data attachment;
- network graph;
- multiblock validation funcional;
- gameplay state;
- sincronização server-authoritative;
- menus funcionais;
- lógica de drones;
- lógica de lasers;
- regras de produção.

Ele DEVE entregar tudo que o repositório funcional precisa para implementar a apresentação corretamente.

---

## 20. NOVO CONCEITO — FULL VISUAL MOD PACKAGE

Para um mod complexo, “asset” não significa apenas um `.bbmodel`.

Cada feature visual pode gerar um pacote:

```text
feature-id/
├── brief
├── concept
├── model-source
├── texture-source
├── rig
├── animations
├── vfx-anchors
├── render-state-contract
├── multiblock-visual-contract
├── ui-visuals
├── icons
├── captures
├── structural-qa
├── visual-qa
├── export-manifest
└── handoff-manifest
```

A estrutura física real deve respeitar o Repo Textura; esta árvore é conceitual.

---

## 21. COBERTURA ARTÍSTICA DE UM TECH MOD COMPLEXO

O pipeline deve conseguir produzir:

### Máquinas

- máquinas de bloco único;
- máquinas com Block Entity;
- máquinas animadas;
- máquinas com partes móveis;
- máquinas com braços;
- máquinas com pistões;
- máquinas rotativas;
- máquinas com esteiras;
- máquinas com portas;
- máquinas com câmaras internas;
- máquinas com líquidos visíveis;
- máquinas com itens visíveis;
- máquinas com progress indicators;
- máquinas emissivas;
- máquinas com módulos/upgrades externos.

### Multiblocos

- máquinas 2×2×N;
- estruturas altas;
- estruturas horizontais;
- grandes geradores;
- refinarias;
- fornos industriais;
- aceleradores;
- torres;
- perfuratrizes;
- reatores;
- estações;
- visual de montagem/desmontagem;
- visual formado/não formado.

### Logística

- pipes;
- ducts;
- cables;
- connectors;
- ports;
- conveyors;
- item transport visuals;
- fluid transport visuals;
- energy beam/line visuals;
- junctions;
- filters visuais;
- frames;
- covers;
- upgrades.

### Entidades tecnológicas

- drones;
- robôs;
- braços móveis;
- sentries;
- constructs;
- vehicles;
- companion machines.

### Equipamentos

- ferramentas;
- armas tecnológicas;
- armaduras;
- exosuits;
- backpacks;
- devices;
- handheld scanners;
- gadgets.

### Mundo

- ores;
- resource nodes;
- pumps;
- wells;
- industrial structures;
- decorative tech blocks;
- doors;
- lights;
- panels;
- vents;
- beams;
- catwalks.

### Interface visual

- machine GUI art;
- slot art;
- progress bars;
- gauges;
- indicators;
- warning icons;
- energy/fluid/item iconography;
- tabs;
- button sprites;
- HUD components;
- status glyphs.

A lógica da GUI não pertence ao Repo Textura; os assets visuais, sim.

---

## 22. TECH VISUAL PROVIDER PROFILES

Além dos profiles gerais já definidos na Parte II, a V5 adiciona profiles conceituais de roteamento visual:

```text
tech_static_machine
tech_native_baked_machine
tech_dynamic_blockentity_renderer_handoff
tech_geckolib_animated_machine
tech_azurelib_animated_machine
tech_multiblock_visual_assembly
tech_machine_upgrade_module
tech_pipe_network_visual
tech_conveyor_visual
tech_drone_entity
tech_laser_beam_vfx
tech_connected_texture_family
tech_gui_visual_sheet
tech_equipment
tech_fluid_material_family
tech_large_machine_structure
create_flywheel_visual_handoff   # somente se API/uso forem aprovados
```

Não criar todos como schemas vazios.

Um profile só entra no registry quando possuir:

- formato;
- source;
- provider;
- capabilities;
- exporter/handoff;
- tests;
- QA;
- autoridade definida.

---

## 23. ROTEADOR DE RENDER PARA MÁQUINAS

Nem toda máquina precisa de GeckoLib.

O pipeline deve escolher o renderer pelo requisito real.

### Caso A — estático

```text
static baked JSON/model
```

Usar para:

- casing;
- frame;
- panel;
- port;
- bloco decorativo;
- máquina sem movimento.

### Caso B — modelo dinâmico sem rig esquelético

Possíveis caminhos:

- NeoForge baked/custom model;
- ModelData;
- connected texture/provider apropriado;
- renderer específico.

### Caso C — Block Entity com rendering dinâmico

Quando algo não pode ser representado adequadamente por modelo baked estático, o handoff pode exigir um `BlockEntityRenderer`.

O Repo Textura não implementa automaticamente esse Java, mas deve entregar:

- source model;
- pivôs;
- part IDs;
- transforms;
- animation intent;
- render-state contract;
- bounds;
- texture/material contract;
- performance notes.

### Caso D — animação esquelética

Provider:

- GeckoLib;
- AzureLib;
- outro runtime comprovado.

### Caso E — VFX independente

Provider/backend:

- provider-native;
- Photon;
- Lodestone;
- vanilla/custom;
- outro backend auditado.

### Regra

```text
requisito visual
→ renderer/provider adequado
→ asset contract
→ handoff
```

Nunca:

```text
“é máquina”
→ GeckoLib automaticamente
```

---

## 24. MACHINE VISUAL STATE CONTRACT

Toda máquina animada deve declarar quais estados visuais necessita do runtime.

Exemplo conceitual:

```yaml
visual_states:
  idle:
  startup:
  active:
  shutdown:
  jammed:
  error:
  overdrive:

channels:
  active: boolean
  progress: 0..1
  rpm: optional
  heat: optional
  energy_level: optional
  fluid_fill: optional
  item_progress: optional
  formed: optional
  facing: optional
```

Isso NÃO define lógica de gameplay.

Ele significa:

> “para renderizar corretamente este asset, o runtime deve me fornecer estes valores”.

O repositório funcional decide:

- de onde vêm;
- como sincronizam;
- quando mudam;
- qual regra de gameplay os controla.

---

## 25. MACHINE ANIMATION CONTRACT

Uma máquina pode possuir clips como:

```text
idle
startup
processing_loop
processing_pulse
shutdown
open
close
insert
eject
jam
error
overdrive
maintenance
```

Esses nomes são templates.

O asset contract deve declarar:

- clip;
- duração;
- loop;
- transition intent;
- moving bones;
- required anchors;
- state/channel que seleciona o clip;
- se precisa phase/progress;
- se permite interpolation;
- visual fallback.

Não colocar damage/process recipe/energy cost na animação.

---

## 26. MULTIBLOCK VISUAL CONTRACT

Para multiblocos, declarar:

```text
visual_root
controller_anchor
orientation
part_map
assembly_bounds
animation_bounds
formed_visual
unformed_visual
hidden_parts_when_formed
visible_ports
upgrade_sockets
particle_anchors
sound_anchors
maintenance_points
```

Opcionalmente:

- per-part model;
- unified model;
- hybrid model;
- renderer expectation;
- unloaded-chunk behavior expectation;
- culling notes.

Collision/estrutura física continua runtime-authoritative.

VoxelShape pode ser fornecido como **handoff/reference**, não como regra funcional automática.

---

## 27. MACHINE PORT / SOCKET SYSTEM

Máquinas complexas precisam de consistência visual entre:

- item input;
- item output;
- fluid input;
- fluid output;
- energy input;
- data/control;
- upgrade slot;
- maintenance port;
- exhaust;
- heat vent.

Criar uma linguagem visual canônica:

```text
port family
→ geometry
→ trim
→ iconography
→ color semantics
→ emissive semantics
→ orientation rules
```

Não fixar cores sem Visual Style Bible.

Portas/sockets devem ter anchors e transforms reproduzíveis.

---

## 28. MODULAR MACHINE KIT

Para evitar modelar cada máquina do zero, criar kits project-owned:

- casing families;
- corners;
- frames;
- vents;
- screens;
- glass;
- bolts/panels;
- motors;
- shafts;
- gears;
- rotors;
- coils;
- pistons;
- tanks;
- ports;
- ducts;
- conduits;
- lights;
- warning strips;
- emissive panels.

Isso permite:

```text
kit visual coerente
+ modules específicos
→ família inteira de máquinas
```

Cada kit deve respeitar:

- naming;
- texel density;
- palette;
- silhouette;
- provider constraints;
- reuse policy;
- performance budget.

---

## 29. CONNECTED TEXTURES E VARIANTES TECNOLÓGICAS

Pipeline deve suportar famílias:

- casing connected;
- glass connected;
- framed pipe;
- insulated cable;
- machine face variants;
- active/inactive;
- warning state;
- damaged visual;
- colorable variant.

Provider pode ser:

- vanilla/NeoForge model;
- connected-texture mod presente;
- custom model loader;
- resource-pack technique.

O provider real deve ser auditado.

---

## 30. CONVEYOR / ITEM TRANSPORT VISUAL

Para esteiras e transporte:

Assets podem declarar:

- belt geometry;
- direction;
- slopes;
- corners;
- junctions;
- side guards;
- item anchor path;
- visual speed;
- scrolling texture requirement;
- optional item render sockets.

A lógica que move o item é do mod.

O Repo Textura entrega o caminho/visual contract.

---

## 31. PIPE / CABLE VISUAL SYSTEM

Precisa cobrir:

- straight;
- elbow;
- T;
- cross;
- end cap;
- machine connection;
- framed;
- covered;
- transparent/inspection;
- different material/style families.

Gerar:

- connection masks;
- model parts;
- texture variants;
- culling notes;
- connected geometry contract;
- optional flow VFX.

Network calculation fica fora do Repo Textura.

---

## 32. FLUID VISUALIZATION

Para tanques/tubos/máquinas:

Asset contract pode exigir:

- fill volume;
- min/max bounds;
- fluid surface plane;
- transparency;
- emissive possibility;
- flow direction;
- bubbles/particles;
- color source;
- texture sampling rule.

Runtime fornece fluid/type/fill.

Repo Textura fornece o visual receptor.

---

## 33. LASERS / BEAMS / ENERGY VISUALS

Criar pipeline para:

- beam source anchor;
- beam end;
- width;
- core;
- glow;
- pulse;
- noise;
- impact;
- charge-up;
- decay;
- occlusion expectation;
- particle burst.

Backend provider específico.

Não confundir beam visual com raycast/hit logic.

---

## 34. DRONES / ROBÔS TECNOLÓGICOS

Usar pipeline de entidade normal, mas com contract tecnológico:

- body;
- rotors/thrusters;
- cargo socket;
- tool socket;
- beam anchor;
- lights;
- state indicators;
- idle;
- move;
- hover;
- pickup;
- dropoff;
- charge;
- damaged/deactivated.

Navigation/AI/logística são handoff para mod repo.

---

## 35. GUI VISUAL PACKAGE

Para cada máquina que possui tela:

```text
gui_background
slots
progress_elements
energy_gauge
fluid_gauge
tabs
buttons
warnings
icons
tooltips_visual_reference
state_variants
```

Entregas:

- source art;
- sprites;
- atlas if applicable;
- pixel bounds;
- nine-slice notes if applicable;
- hover/pressed/disabled variants;
- scaling contract;
- screenshot mockup.

Sem container/menu Java neste projeto.

---

## 36. ITEM / COMPONENT FAMILY GENERATOR

Tech mods grandes têm muitos componentes visualmente relacionados.

Pipeline precisa produzir famílias coerentes:

- plates;
- rods;
- gears;
- coils;
- circuits;
- processors;
- motors;
- cores;
- cells;
- dusts;
- crystals;
- tools.

Criar tokens visuais reutilizáveis:

- material;
- tier;
- function;
- hazard;
- energy class.

Objetivo:

reduzir inconsistência sem transformar todos os ícones em recolors preguiçosos.

---

## 37. TECH TIER VISUAL LANGUAGE

Se o mod tiver tiers, o Repo Textura pode definir:

- silhouette delta;
- material delta;
- detail density;
- emissive density;
- trim language;
- animation complexity;
- VFX intensity.

Tier NÃO implica balanceamento.

Ele apenas produz uma linguagem visual que o mod funcional pode mapear aos tiers reais.

---

## 38. PERFORMANCE BUDGET PARA MÁQUINAS

Mods de tecnologia podem colocar dezenas/centenas de máquinas em uma base.

Portanto cada asset deve possuir budget mensurável:

- cubes;
- bones;
- keyframe channels;
- texture memory;
- render layers;
- transparent surfaces;
- emissive surfaces;
- particle emission;
- dynamic item renders;
- dynamic fluid renders;
- animation update cost;
- culling bounds.

Não inventar limites universais fixos.

Metodologia:

```text
Golden machine
→ benchmark
→ target hardware/modpack
→ measured budget
→ profile budget
→ regression
```

---

## 39. LARGE BASE / MANY-MACHINES QA

Além de testar uma máquina isolada:

- 1 unidade;
- pequeno cluster;
- linha de produção;
- sala cheia;
- multiblocos próximos;
- pipes/cables;
- partículas ativas;
- animações simultâneas;
- shader ativo;
- Distant Horizons/stack visual relevante quando aplicável.

QA deve observar:

- FPS/frame time;
- culling;
- overdraw;
- transparency;
- particle spam;
- animation readability;
- visual noise.

---

## 40. CREATE / FLYWHEEL HANDOFF

O modpack físico atual contém Create 6.0.10 e Flywheel embutido.

Isso NÃO significa que todo mod próprio deva depender de Flywheel.

Pode existir profile futuro:

`create_flywheel_visual_handoff`

somente após:

- API exata auditada;
- licença/dependency policy;
- benefício comprovado;
- renderer compatibility;
- dedicated-server boundary;
- maintenance cost.

Caso não seja aprovado:

usar provider/render stack próprio adequado.

---

## 41. COMPLEX TECH GOLDEN SAMPLES

Adicionar progressivamente Golden Samples que representem complexidade real:

1. static machine;
2. animated single-block machine;
3. machine with door;
4. machine with rotor;
5. machine with visible fluid;
6. modular machine + upgrade socket;
7. pipe family;
8. cable family;
9. conveyor segment;
10. conveyor corner/slope;
11. drone;
12. laser emitter;
13. multiblock machine;
14. large animated multiblock;
15. GUI visual package;
16. tech armor/tool;
17. connected casing family;
18. full mini-production-line scene.

Não criar tudo antes da infraestrutura.

Cada sample entra quando a capability correspondente existir.

---

## 42. TECH MOD HANDOFF MANIFEST

Exemplo conceitual:

```yaml
asset_id: arcane_induction_furnace

visual_profile: tech_geckolib_animated_machine
runtime_owner: target-mod-repo

source:
  model: ...
  texture: ...
  animation: ...

visual_inputs:
  active: bool
  progress: float01
  heat: float01

clips:
  idle: ...
  startup: ...
  process: ...
  shutdown: ...

anchors:
  item_input: ...
  item_output: ...
  exhaust_fx: ...
  sound_loop: ...

render:
  expected_provider: geckolib
  culling_bounds: ...
  emissive: ...
  transparency: ...

qa:
  structural: PASS
  visual: PASS
  minecraft_runtime: PENDING
```

Schema final deve ser formalizado por TDD.

---

## 43. NOVA ORDEM DE PRODUÇÃO DE UMA MÁQUINA COMPLEXA

```text
Design intent
↓
Visual Style Bible
↓
machine family / tier language
↓
concept sheet
↓
render/provider decision
↓
Machine Visual Contract
↓
model
↓
UV
↓
texture/material
↓
rig
↓
animation
↓
ports/sockets
↓
VFX anchors
↓
GUI visual package
↓
multiblock visual contract (se houver)
↓
structural QA
↓
capture/visual QA
↓
performance budget check
↓
export staging
↓
handoff manifest
↓
mod repo integration
↓
Minecraft real
↓
runtime + performance QA
```

---

## 44. O QUE “MOD COMPLETO” SIGNIFICA NESTE PROJETO

Quando o usuário disser:

> “quero montar um mod completo tipo Oritech”

este Projeto deve interpretar como:

> “quero que o Repo Textura produza e documente toda a camada artística e de apresentação necessária para esse mod, além dos contratos de handoff para o repositório funcional.”

Ele NÃO deve começar a implementar:

- sistema de energia;
- recipe engine;
- multiblock controller;
- item transport algorithm;
- capability;
- menus Java;
- networking;
- worldgen rules;
- balanceamento.

Esses itens pertencem ao repo do mod.

Mas o Repo Textura pode produzir todos os assets necessários para eles.

---

## 45. COBERTURA DOS 30 BLOCOS DO ROADMAP HISTÓRICO

As notas recentes reafirmaram que a antiga lista de 16 itens era apenas a espinha dorsal das PRs.

Esta V5 considera explicitamente todos os blocos:

1. Fundação artística/instruções → Parte I + Visual Style Bible/contracts.
2. Asset Toolkit → Parte II.
3. Provider Profile Resolver → Parte II.
4. Extension Capability Registry → Parte II.
5. Presets de extensões → Parte II.
6. PR1 → histórico #486.
7. PR2 → histórico #487 / frontier.
8. Segurança/transações → Parte II.
9. PR3 Modeling/Rig → roadmap.
10. PR4 UV/Texture → roadmap.
11. Concept/art tools → Parte II + Parte I-B.
12. PR5 Animation Core → roadmap.
13. GeckoLib → PR6.
14. AzureLib → PR7.
15. NeoForge Native → PR8.
16. Easy Model Entities → PR9.
17. EMF/CEM → PR10.
18. Animated Java → PR11.
19. Player pipeline → PR12.
20. Epic Fight/Blender → PR13.
21. VFX → Parte II + handoff.
22. Ferramentas adicionais → extension matrix.
23. Capture/Visual QA → Parte II.
24. Export/staging → Parte II/PR14.
25. Golden/round-trip/drift → Parte II.
26. Security/regression → Parte II.
27. Blockbench real smoke → Parte II.
28. Provider-specific/Minecraft QA → Parte II.
29. CI/tooling → Parte II.
30. Instalação guiada → Parte I + Parte II.

A expansão tech desta Parte I-B se soma a todos eles; ela não cria um plano paralelo.

---

## 46. CHECKLIST EXTRA — CAPACIDADE “ORITECH-CLASS VISUAL”

O pipeline só pode afirmar que suporta um tech mod visualmente complexo quando conseguir demonstrar:

- [ ] machine static asset;
- [ ] animated machine;
- [ ] provider-aware Block Entity presentation;
- [ ] multiblock visual contract;
- [ ] modular machine system;
- [ ] ports/sockets;
- [ ] connected texture family;
- [ ] pipe/cable visual family;
- [ ] conveyor visual;
- [ ] item/fluid visualization contract;
- [ ] drone/robot asset;
- [ ] laser/beam VFX;
- [ ] tech equipment;
- [ ] GUI visual package;
- [ ] animation state contract;
- [ ] export/handoff manifest;
- [ ] many-machines performance QA;
- [ ] shader/modpack visual QA;
- [ ] in-game runtime QA after integration.

Até lá, usar:

`CAPABILITY_PARTIAL`

e não “suporta mod complexo completo”.

---


# PARTE II — ESPECIFICAÇÃO TÉCNICA COMPLETA DO PIPELINE

**Projeto:** **Minecraft Mod Factory** — repositório canônico da infraestrutura comum; domínio artístico lógico: **Repo Textura**
**Alvo do modpack:** Minecraft 1.21.1 / NeoForge 1.21.1 / Java 21  
**Domínio:** direção de arte, Blockbench, modelagem, texturas, UV, rigging, animação, VFX/SFX anchors, export, QA visual e automação assistida por IA  
**Estado:** **MIGRAÇÃO AUTORIZADA — remote resolvido; bootstrap e reconciliação da infraestrutura histórica pendentes antes de continuar PR4**
**Baseline:** remote canônico `Gustavaopere/minecraft-mod-factory`; default branch `main`; primeiro `BASE_SHA` permanece `UNRESOLVED_EMPTY_REPOSITORY` até o commit inicial; SHAs do RPG são apenas proveniência histórica
**Concorrência:** verificar no Repo Textura branches/PRs/worktrees ativos relacionados a Blockbench, assets, Golden Samples, VFX, Visual Style Bible, validators e tooling antes de alterar a mesma infraestrutura
**Baseline recomendado do editor para este plano:** Blockbench Desktop **5.1.6**, salvo se a máquina do usuário estiver em outra versão quando a implementação começar  
**Revisão técnica incorporada:** 3.0 — migração canônica para o Repo Textura + expansão multi-provider

> Este documento substitui, para fins de planejamento futuro, a versão anterior “PLANO — BLOCKBENCH LIVE BRIDGE / RPG ASSET MCP”.  
> O plano anterior continua válido como histórico, mas esta revisão altera uma decisão arquitetural importante: **o pipeline não é GeckoLib-cêntrico**. O projeto deve possuir perfis de authoring/runtime distintos para NeoForge nativo, GeckoLib, AzureLib, Easy Model Entities, EMF/CEM, Animated Java, CPM, bibliotecas de animação de player e handoff externo para Epic Fight/Blender.

---

# 0. RESUMO EXECUTIVO

O objetivo é transformar o pipeline artístico já criado no repositório em um sistema onde um agente autorizado possa operar o Blockbench de forma controlada, verificável e reversível.

Fluxo-alvo:

```text
Design intent
    ↓
Visual Style Bible
    ↓
Asset Brief / Model Asset Contract
    ↓
Provider Profile Resolver
    ↓
Extension Capability Registry
    ↓
Repo Textura Asset MCP
    ↓
Repo Textura Asset Toolkit / Blockbench Bridge
    ↓
Blockbench API + extensões allowlisted
    ↓
provider-specific export / handoff
    ↓
mod resources / resource pack / datapack / external DCC
    ↓
Minecraft 1.21.1 real
    ↓
Structural QA + Visual QA + runtime QA
```

A integração deve cobrir o máximo possível do ecossistema artístico do pack, porém **sem transformar “plugin instalado” em authority**.

A regra principal será:

```text
provider-native first
→ extensão oficial/provider-maintained comprovada
→ adapter próprio comprovado
→ fallback seguro
→ UNAVAILABLE quando nada seguro existir
```

Não haverá `execute_script`, `eval`, shell arbitrário, instalação automática de plugins ou escrita livre no filesystem.

---

# 0.1. AUTORIDADE E FRONTEIRA DO REPO TEXTURA NA MINECRAFT MOD FACTORY

A V5.1 elimina a ambiguidade de remote.

Remote canônico:

`Gustavaopere/minecraft-mod-factory`

O termo **Repo Textura** permanece como nome do domínio artístico e da authority visual, mas não designa mais um Git repository separado.

A partir desta revisão:

- `minecraft-mod-factory` é a fonte de verdade da infraestrutura reutilizável;
- o domínio `Repo Textura` dentro da Factory é a fonte de verdade artística;
- o domínio `Mod Engineering` dentro da mesma Factory governa contracts, scaffolding, validators, CI e integração;
- os dois domínios compartilham Git, mas mantêm fronteiras de authority;
- `Gustavaopere/neoforge-rpg-skilltree` é origem histórica da infraestrutura e continua authority apenas do runtime RPG;
- a modlist física continua sendo authority auxiliar para presença/versão de providers/runtimes;
- `.bbmodel` e demais fontes nativas de authoring devem ser preservadas conforme o provider;
- exportações para repos de mods, resource packs, datapacks ou DCCs são handoffs, não mudança de authority;
- gameplay e regras server-authoritative continuam fora do domínio artístico.

## Regra de caminhos

O novo repositório está vazio nesta revisão. Portanto qualquer árvore de diretórios deste plano continua **conceitual** até o bootstrap materializar e validar a estrutura real.

Não copiar cegamente `PROJECT-INSTRUCTIONS/`, `skills/`, `standards/` ou `tools/` do RPG. A migração deve usar matriz por arquivo/capability e preservar proveniência.

---

# 1. ESCOPO REAL DA PESQUISA DE EXTENSÕES

Não existe um registry universal contendo absolutamente todo plugin Blockbench já publicado na internet.

Esta auditoria cobre:

1. **catálogo oficial atual do Blockbench** (`JannisX11/blockbench-plugins`);
2. plugins marcados para **Minecraft: Java Edition**;
3. plugins genéricos do catálogo oficial que melhoram significativamente:
   - modelagem;
   - rigging;
   - animação;
   - UV;
   - texturas;
   - preview;
   - captura;
   - resource packs;
   - QA;
   - export/handoff;
4. plugins provider-maintained externos relevantes aos **JARs realmente presentes na modlist física**;
5. ferramentas externas obrigatórias quando o provider não usa Blockbench para a etapa correspondente, como Epic Fight + Blender.

Portanto:

- “não apareceu no catálogo oficial” ≠ “não existe”;
- “apareceu no catálogo” ≠ “serve para NeoForge 1.21.1”;
- “serve para Minecraft Java” ≠ “serve para este modpack”;
- “está instalado no Blockbench” ≠ “pode ser exposto ao MCP”.

---

# 2. AUTORIDADES

A ordem de autoridade para esta frente será:

1. **modlist física/JAR atual** — presença e versão do provider no pack;
2. código/JAR/source da versão exata do provider;
3. documentação oficial da versão pertinente;
4. catálogo oficial Blockbench para metadata de plugin;
5. source do plugin/extension;
6. Golden Samples canônicos do próprio projeto;
7. Visual Style Bible;
8. documentação editorial/Notion como contexto;
9. referências externas apenas como referência.

Quando documentação e modlist divergirem:

**a modlist física vence para presença e versão.**

Quando plugin e runtime provider divergirem:

**o runtime provider continua sendo authority do formato/comportamento que chega ao jogo.**

---

# 3. SNAPSHOT FÍSICO RELEVANTE DO MODPACK

O snapshot físico atual confirma, entre outros:

| Provider / runtime | Versão física | Papel |
|---|---:|---|
| GeckoLib 4 | 4.9.2 | modelos/animações 3D para mods |
| AzureLib | 3.1.11 | modelos/animações de mods, fork/ecossistema próprio |
| Easy Model Entities | 2.3.0 | entidades/block entities data-driven com `.bbmodel` |
| Entity Model Features | 3.3.5 | CEM/overrides de modelos por resource pack |
| Customizable Player Models | 0.6.27a | modelos/animações de avatar/player |
| Player Animation Library | 1.1.6+mc.1.21.1 | runtime de animação de player |
| Player Animator | 2.0.4+1.21.1 | outra API/runtime de animação de player |
| Epic Fight | 21.17.3.1 | combate e animações próprias |
| Sophisticated Backpacks | 3.26.1 | provider de backpacks/worn display relevante |
| Photon | 2.2.6.a | VFX/editor/runtime candidate |
| Lodestone | 1.8.2 | rendering/particle-library candidate |
| AAA Particles / AAA Particles World | **não confirmados no snapshot físico atual** | tratar como ausentes até nova verificação |
| Create | 6.0.10 | máquinas/contraptions/visual mecânico |

Esse snapshot deve ser refeito antes da implementação.

Não congelar futura API Java apenas porque a versão física foi registrada aqui.

---

# 4. BLOCKBENCH BASELINE

A release oficial mais recente verificada durante esta auditoria foi:

**Blockbench 5.1.6 — Workflow Update, Patch 6.**

Recomendação:

- usar **Blockbench Desktop**;
- tratar `5.1.6` como baseline de QA deste plano;
- registrar a versão real durante cada sessão MCP;
- rejeitar/adaptar extensões cujo `min_version` / `max_version` não aceite a versão ativa.

O plugin próprio deve usar:

- `Plugin.register(...)`;
- API oficial Blockbench;
- `blockbench-types` no desenvolvimento;
- Undo API oficial;
- `Codec` / `AnimationCodec` quando apropriado;
- APIs de `Texture`, Painter/Canvas e Timeline comprovadas na versão usada.

---

# 5. MUDANÇA ARQUITETURAL PRINCIPAL EM RELAÇÃO AO PLANO V1

## Antes

O desenho conceitual era essencialmente:

```text
Blockbench
→ GeckoLib-aware pipeline
→ export
```

## Agora

O desenho correto é:

```text
Blockbench
    ↓
Provider Profile Resolver
    ├── java_block_item
    ├── neoforge_native_animation
    ├── geckolib4_*
    ├── azurelib_*
    ├── easy_model_entities_*
    ├── emf_cem_entity
    ├── animated_java_display_entities
    ├── cpm_player_model
    ├── player_animation_library_handoff
    ├── player_animator_handoff
    ├── sophisticated_backpacks_display
    ├── voxelshape_collision
    ├── structure_reference
    └── epicfight_blender_handoff
```

Cada profile decide:

- formato de authoring;
- extensão necessária;
- capabilities permitidas;
- constraints;
- exporter;
- runtime owner;
- QA;
- limites;
- conversões permitidas/proibidas.

---

# 6. PRINCÍPIO DE NÃO-CONVERSÃO AUTOMÁTICA

Os seguintes ecossistemas NÃO são considerados intercambiáveis:

```text
GeckoLib
AzureLib
NeoForge native animation JSON
EMF/CEM
Easy Model Entities
Animated Java
CPM
Epic Fight
Player Animation Library
Player Animator
```

Mesmo quando dois usam JSON ou estruturas parecidas.

Conversão entre perfis:

- exige adapter explícito;
- exige auditoria semântica;
- deve declarar perda de informação;
- precisa preservar o source original;
- deve operar em dry-run antes de commit;
- nunca pode ser acionada silenciosamente pelo MCP.

---

# 7. NOVA CAMADA — EXTENSION CAPABILITY REGISTRY

Adicionar ao toolkit uma camada formal:

```text
extension-registry/
├── discovery
├── metadata
├── fingerprint
├── compatibility
├── allowlist
├── capability-map
└── adapter-registry
```

O registry deve distinguir:

- extensão instalada;
- extensão reconhecida;
- versão conhecida;
- versão compatível;
- extensão permitida para o profile atual;
- extensão autorizada para ser chamada pelo MCP;
- extensão somente humana;
- extensão proibida.

---

# 8. CLASSIFICAÇÃO DE EXTENSÕES

Usar estados explícitos:

- `REQUIRED_PROFILE`
- `PREFERRED`
- `OPTIONAL`
- `EXPERIMENTAL`
- `DEV_ONLY`
- `HUMAN_ONLY`
- `AUDIT_REQUIRED`
- `BLOCKED_LEGACY`
- `INCOMPATIBLE_EDITOR`
- `LOADER_MISMATCH`
- `PROVIDER_ABSENT`
- `NOT_RUNTIME_AUTHORITY`
- `DISABLED_BY_DEFAULT`

Um plugin instalado pode permanecer `DISABLED_BY_DEFAULT` para o MCP.

---

# 9. TOOLS MCP PARA EXTENSÕES

Read-only:

```text
blockbench.extensions.list
blockbench.extensions.get
blockbench.extensions.get_fingerprint
blockbench.extensions.check_compatibility
blockbench.profiles.list
blockbench.profiles.get
blockbench.profiles.resolve_for_asset
```

Não implementar em produção:

```text
blockbench.extensions.install_arbitrary
blockbench.extensions.load_url
blockbench.extensions.execute_action_by_name
blockbench.execute_script
```

Instalação continua humana e guiada.

---

# 10. FINGERPRINT DE SESSÃO

Toda sessão deve registrar:

```text
minecraft_version
loader
java_version

blockbench_version

toolkit_version
protocol_version

installed_extensions:
  plugin_id
  plugin_version

physical_providers:
  mod_id
  mod_version

active_provider_profile
project_format
project_revision
```

Esse fingerprint entra no relatório de QA/export.

---

# 11. EXTENSÕES — MATRIZ DE PROVIDERS PRINCIPAIS

## 11.1 GeckoLib Models & Animations

**Plugin do catálogo oficial:** `geckolib`  
**Versão auditada do plugin:** 4.2.5  
**Compatibilidade Blockbench:** 5.0.0 até <6.0.0 conforme catálogo atual  
**Runtime físico:** GeckoLib 4.9.2  
**Status:** `REQUIRED_PROFILE` quando um asset GeckoLib for escolhido.

Suporta authoring de:

- entidades;
- blocks/block entities;
- itens;
- armor;
- rig;
- animação;
- Molang;
- easing;
- model export;
- animation export;
- effect keyframes.

GeckoLib 4 também suporta callbacks de:

- sound keyframes;
- particle keyframes;
- custom instruction keyframes.

Esses keyframes são **presentation timing**, não gameplay authority.

### Proibição

Não instalar `GeckoLib Animation Utils` antigo no baseline Blockbench 5.x.

---

# 12. GECKOLIB ANIMATION UTILS — BLOQUEADO

**Plugin:** `animation_utils`  
**Versão auditada:** 4.1.3  
**Estado:** **MIGRAÇÃO AUTORIZADA — implementar na Minecraft Mod Factory somente após bootstrap e reconciliação com o cutoff histórico**

O próprio catálogo declara que foi substituído por `GeckoLib Models & Animations`.

Classificação:

`BLOCKED_LEGACY`

Não incluir em preset.

---

# 13. AZURELIB ANIMATOR

**Plugin:** `azurelib_utils`  
**Versão auditada:** 2.1.4  
**Runtime físico:** AzureLib 3.1.11  
**Status:** `REQUIRED_PROFILE` para assets AzureLib.

O source atual do plugin implementa:

- formato/codec AzureLib;
- model import/export;
- custom animation UI;
- keyframe overrides;
- custom easings;
- Bedrock-style interpolation;
- animation handling próprio;
- módulo FABRIK IK de authoring;
- settings/templates.

O catálogo/source permite Blockbench 5.1.6.

### Regra crítica

AzureLib é tratado como ecossistema próprio.

Não assumir compatibilidade de ida/volta com GeckoLib.

---

# 14. NEOFORGE NATIVE — ANIMATION TO JSON

**Plugin:** `animation_to_json`  
**Título:** Animation to JSON Converter  
**Versão auditada:** 1.0.1  
**Catálogo:** Minecraft Java / Animation  
**Descrição oficial:** exporta animações Blockbench para JSON do NeoForge.

Status:

`PREFERRED` quando um runtime próprio puder consumir com segurança o formato nativo pertinente.

### Gate

Antes de usar no mod:

- confirmar que a versão exata NeoForge 1.21.1 usada pelo projeto possui o runtime/API correspondente;
- validar o JSON gerado contra build real;
- criar regressão.

O plugin existir não prova sozinho que qualquer renderer do projeto já está pronto para consumi-lo.

---

# 15. EASY MODEL ENTITIES

**Runtime físico:** Easy Model Entities 2.3.0.

O provider permite usar `.bbmodel` diretamente em resource packs, com profiles data-driven para entities e block entities.

Capabilities documentadas incluem:

- host entity;
- host block entity;
- profiles;
- render profiles;
- `.bbmodel`;
- texture;
- scale;
- bounds;
- animações básicas automáticas;
- developer API.

Clips comuns reconhecidos pelo provider incluem uma família simples como:

- `idle`;
- `walk`;
- `swim`;
- `fly`;
- `attack`;
- e outros clips específicos conforme versão/provider.

Não congelar o conjunto sem reinspeção da versão física.

## Exporter Blockbench

Existe um exporter provider-maintained.

Durante a auditoria, a contribuição correspondente ao catálogo oficial ainda aparecia em PR upstream aberta.

Classificação:

`EXPERIMENTAL_PROVIDER_PLUGIN`

Regras:

- preferir release revisada se entrar no catálogo oficial;
- não instalar master automaticamente;
- development URL somente com ação humana explícita;
- pin/audit do source antes de integração MCP;
- não duplicar o exporter do provider sem necessidade.

---

# 16. ENTITY MODEL FEATURES / CEM

**Runtime físico:** Entity Model Features 3.3.5.

## CEM Template Loader

**Versão auditada:** 9.2.0  
**Blockbench:** 5.x compatível pelo catálogo.

Funções:

- carregar templates CEM;
- Java entity model resource-pack authoring;
- animation editor.

## EMF Animation Addon

**Versão auditada:** 1.0.4  
**Dependência:** `cem_template_loader`.

Adiciona funções/variáveis de animação específicas do EMF.

O próprio plugin avisa que features EMF-only podem tornar o asset incompatível com OptiFine.

Isso é aceitável como decisão consciente porque:

- EMF é o provider físico relevante;
- OptiFine não é authority do pack.

Mesmo assim:

- não usar EMF profile em assets mod-owned GeckoLib/AzureLib por conveniência;
- EMF/CEM é principalmente pipeline de resource-pack/entity override.

---

# 17. ANIMATED JAVA

**Plugin oficial:** `animated_java`  
**Versão auditada:** 1.10.2  
**Blockbench mínimo:** 5.1.4  
**Baseline 5.1.6:** compatível.

Animated Java é um backend de:

- display entities;
- data pack;
- resource pack;
- Blueprints;
- rigs;
- animations;
- variants;
- locators;
- interactions;
- cameras;
- item/block/text displays;
- function/effect keyframes.

É excelente para:

- cutscenes;
- props vivos;
- máquinas visuais scripted;
- cenografia;
- boss presentation auxiliar;
- cinematics;
- efeitos de mundo;
- cenas narrativas.

Não é substituto automático para entidade modded server-authoritative.

### Minecraft 1.21.1

Para 1.20.4–1.21.5, o próprio Animated Java documenta restrições vanilla de rotação dos cubes:

- um eixo por vez;
- incrementos permitidos de 22.5° para cube rotations.

Groups podem resolver parte da composição, mas o profile precisa respeitar o output real.

---

# 18. CUSTOMIZABLE PLAYER MODELS

**Runtime físico:** CPM 0.6.27a.

O projeto CPM possui plugin Blockbench próprio em beta.

Foi testado upstream com Blockbench Desktop 5.1.4 e permite:

- preset CPM;
- import `.cpmproject`;
- export `.cpmproject`.

Upstream alerta:

- plugin beta;
- features incompletas;
- animações CPM podem quebrar na importação.

Há issues recentes de export/import no ecossistema.

Classificação:

`EXPERIMENTAL_PROVIDER_PLUGIN` + `HUMAN_CONFIRM_REQUIRED`

Não tornar operação automática no primeiro MVP.

---

# 19. PLAYER ANIMATION LIBRARY

**Runtime físico:** Player Animation Library 1.1.6+mc.1.21.1.

O provider declara suporte a carregar animações a partir de:

- Blender;
- Blockbench JSON;
- GeckoLib format;
- Bedrock format.

Também declara:

- Molang;
- effect keyframes;
- custom pivots;
- custom bones;
- anchors úteis para partículas.

Classificação:

`RUNTIME_CONSUMER_PROFILE`

Não inventar um “PAL Blockbench plugin” se nenhum plugin específico for necessário/provado.

O bridge deve produzir/handoff um formato comprovadamente consumível pelo PAL e depois validar no runtime.

---

# 20. PLAYER ANIMATOR

**Runtime físico:** Player Animator 2.0.4+1.21.1.

É outro runtime/API de animação de player.

Classificação inicial:

`RUNTIME_CONSUMER_PROFILE / PROVIDER_API_AUDIT_REQUIRED`

Não tratar PAL e Player Animator como equivalentes.

Qualquer bridge entre ambos exige adapter real.

---

# 21. EPIC FIGHT — PIPELINE EXTERNO OBRIGATÓRIO

**Runtime físico:** Epic Fight 21.17.3.1.

A documentação oficial do Epic Fight orienta:

```text
Epic Fight Player Animation Rig
        ↓
Blender
        ↓
Epic Fight Blender JSON Exporter
        ↓
Epic Fight asset/runtime
```

Portanto:

**não criar uma falsa tool `blockbench.export_epicfight_animation`.**

Criar profile:

`epicfight_blender_handoff`

Blockbench pode ajudar em:

- concept;
- proportions;
- model references;
- texture references;
- GLTF/BLEND handoff quando semanticamente seguro.

A animação Epic Fight continua Blender-authoritative.

---

# 22. SOPHISTICATED BACKPACKS DISPLAY

**Runtime físico:** Sophisticated Backpacks 3.26.1.

O catálogo oficial inclui:

**SB Worn Display Editor**  
Versão auditada: 4.13.0.

Ele permite editar visualmente custom display keys, incluindo uso para Sophisticated Backpacks worn.

Classificação:

`OPTIONAL_CURRENT_PACK_PROVIDER_HELPER`

Antes de expor ao MCP:

- auditar keys exatas esperadas pela versão física;
- auditar serialization;
- round-trip test.

---

# 23. JAVA BLOCK / ITEM NATIVO

Profile:

`java_block_item`

Usar para:

- blocos estáticos;
- item models;
- display transforms;
- tint;
- resource-pack assets;
- variantes quando compatíveis com 1.21.1.

Extensões úteis:

- Tint Preview;
- Resource Pack Utilities;
- Resourcepack Packager;
- Group Exporter;
- Asset Browser;
- Code View;
- Quick Box-UV Layout;
- UV Locker.

---

# 24. FREE ROTATION — AUDIT REQUIRED

**Plugin:** Free Rotation  
**Versão auditada:** 1.2.1  
**Descrição:** Java Item models sem limitações de rotação.

Porém Minecraft 1.21.1 possui constraints reais em formatos vanilla/display-related.

Logo:

`AUDIT_REQUIRED`

Não assumir que o plugin remove limitações do runtime.

Precisamos descobrir qual técnica de export ele usa e validar no jogo 1.21.1.

---

# 25. VOXELSHAPE

Plugins úteis:

- VoxelShape Generators;
- Mod Utils.

Use para:

- bloco collision/selection shapes;
- geração assistida de shapes.

Não confundir:

```text
visual geometry ≠ authoritative collision
```

O MCP pode propor/generar shape, mas:

- diff;
- review;
- test in-game;
- negative bounds;
- interaction/collision tests.

---

# 26. STRUCTURE PIPELINE

Plugins úteis:

- Structure Importer;
- Structure to Model;
- Asset Browser;
- Reference Models.

Casos:

- usar estrutura Minecraft como referência;
- criar miniaturas/model representations;
- importar `.nbt` para análise;
- apoiar Stage de schematics/modelagem.

Não converter automaticamente uma construção inteira em runtime entity model sem budget explícito.

---

# 27. RESOURCE PACK UTILITIES

**Plugin:** Resource Pack Utilities  
**Versão auditada:** 1.10.0  
**Blockbench:** desktop.

Capabilities relevantes incluem utilidades para:

- resource-pack workflow;
- animação de textura/spritesheet;
- JSON utilities;
- conversões auxiliares.

Status:

`PREFERRED_RESOURCEPACK`

Mas o exporter/staging do Repo Textura Asset Toolkit continua authority do nosso pipeline de publicação.

---

# 28. ASSET BROWSER

**Versão auditada:** 1.2.2.

Permite navegar assets Minecraft dentro do Blockbench.

Status:

`PREFERRED_REFERENCE`

Uso:

- referência vanilla;
- comparar shapes;
- verificar assets;
- não copiar automaticamente conteúdo de terceiros.

---

# 29. REFERENCE MODELS

**Versão auditada:** 1.1.0  
**Blockbench:** desktop / min 5.0.

Permite carregar:

- glTF;
- GLB;
- outros projetos abertos como referência.

Status:

`PREFERRED_REFERENCE`

Muito útil para:

- proporção;
- retarget reference;
- modelos importados;
- handoff Blender.

Referência não deve ser incluída no export final sem autorização.

---

# 30. EXPORT TO BLENDER

**Plugin:** Export to Blender  
**Versão auditada:** 2.0.0  
**Desktop.**

Status:

`PREFERRED_EXTERNAL_DCC_HANDOFF`

Uso principal:

- Epic Fight;
- renders complexos;
- rig/animation workflows que Blockbench não cobre;
- análise avançada.

Não tratar `.blend` como formato runtime Minecraft.

---

# 31. GLTF IMPORTER

**Versão auditada:** 1.2.0  
**Desktop.**

Status:

`OPTIONAL_REFERENCE_IMPORT`

Import GLTF/GLB deve entrar em quarantine/reference primeiro.

Não promover meshes importadas automaticamente para profiles cuboid-only.

---

# 32. BONE VIEW

**Versão auditada:** 1.0.0.

Visualiza pivôs e conexões de groups como bones.

Status:

`PREFERRED_RIG_QA`

O MCP deve continuar calculando hierarquia estruturalmente; Bone View é ferramenta visual auxiliar.

---

# 33. DUPLICATE BONE RENAMER

Status:

`OPTIONAL_REPAIR_HELPER`

Útil para GeckoLib/Bedrock-like models.

Não chamar automaticamente em assets publicados porque renomear bone pode quebrar:

- animations;
- runtime references;
- locators;
- VFX anchors.

Se integrado:

dry-run + ref graph + explicit confirmation.

---

# 34. BATCH GROUP RENAME

**Versão auditada:** 1.3.0.

Status:

`OPTIONAL_REFACTOR_HELPER`

Mesma regra do renamer:

renome não pode ser operação cega.

O toolkit próprio deve saber atualizar referências dependentes ou rejeitar.

---

# 35. ANIMATION SLIDERS

**Versão auditada:** 0.5.0.

Status:

`PREFERRED_ANIMATION_ASSIST`

Ajuda a ajustar keyframes.

Não é exporter/runtime.

---

# 36. BAKERY

**Versão auditada:** 1.1.1.

Bakes complex animation em keyframes lineares.

Status:

`OPTIONAL_LOSSY_ANIMATION_TOOL`

Uso apenas com:

- source preservado;
- dry-run;
- cópia;
- comparação visual;
- provider capability check.

Não bakear Molang/easing automaticamente se o provider nativo puder preservá-los.

---

# 37. ANIMATED PLATFORMS

Status:

`PREFERRED_LOCOMOTION_QA`

Útil para:

- walk cycles;
- run cycles;
- criaturas;
- veículos;
- foot sliding.

O movimento do ground plane é referência visual.

Não vira root-motion gameplay authority.

---

# 38. CAMERAS

**Versão auditada:** 1.2.2.

Status:

`PREFERRED_VISUAL_QA`

Uso:

- vistas canônicas;
- animation review;
- cinematics;
- screenshot repeatability.

O Repo Textura Asset Toolkit deve definir presets próprios de câmera mesmo se o plugin auxiliar estiver presente.

---

# 39. SCENE RECORDER

Status:

`OPTIONAL_VISUAL_EVIDENCE`

Uso:

- gravação de animation preview;
- evidência de QA;
- comparação antes/depois.

Não usar vídeo como única evidência estrutural.

---

# 40. PREVIEW SCENE CUSTOMISER

Status:

`OPTIONAL_VISUAL_QA`

Criar cenários de referência:

- iluminação;
- escala;
- fundo;
- chão;
- contraste.

O QA final continua dentro do Minecraft.

---

# 41. GRAYSCALE PREVIEW

**Versão auditada:** 1.0.0.

Status:

`PREFERRED_READABILITY_QA`

Excelente para:

- hierarchy de valor;
- silhouette;
- readability;
- contraste.

---

# 42. TRANSPARENCY FIX

**Versão auditada:** 2.1.0.

Status:

`OPTIONAL_VIEWPORT_QA`

Serve para visualizar geometria dentro de containers transparentes.

Não alterar política runtime de transparência.

---

# 43. MISSING TEXTURE HIGHLIGHTER

Status:

`PREFERRED_TEXTURE_QA`

Complementa o validator próprio.

Mesmo com plugin:

o Toolkit continua validando referências de textura por conta própria.

---

# 44. TEXTURE STITCHER

**Versão auditada:** 1.0.7.

Status:

`OPTIONAL_TEXTURE_PIPELINE`

Útil quando um provider/asset contract realmente pede atlas único.

Não stitchar automaticamente texturas independentes.

---

# 45. UV LOCKER

**Versão auditada:** 1.0.0.

Status:

`PREFERRED_UV_HELPER`

Ajuda a preservar UV durante edição de geometria.

Não substitui UV validation do core.

---

# 46. QUICK BOX-UV LAYOUT

Status:

`OPTIONAL_UV_HELPER`

Útil para converter layout per-face em organização Box-UV.

Sempre dry-run em asset existente.

---

# 47. PLASTER

Status:

`PREFERRED_PIXEL_ART_HELPER`

Usar para corrigir texture bleeding quando apropriado.

Não expandir bordas sobre regiões que tenham semântica própria sem mask.

---

# 48. BRUSH TUNA

**Versão auditada:** 1.0.6  
**Blockbench mínimo observado:** 5.1.4.

Status:

`PREFERRED_TEXTURE_AUTHORING`

Preset/control de brushes.

O MCP não deve chamar brush aleatório; deve usar operações determinísticas e masks.

---

# 49. COLOUR GRADIENT GENERATOR

**Versão auditada:** 3.0.0.

Status:

`PREFERRED_PALETTE_HELPER`

Uso:

- palette ramps;
- materials;
- shading ramps.

Paleta continua derivada da Visual Style Bible / Asset Contract.

---

# 50. BRUSH COLOR RANDOMIZER

Status:

`OPTIONAL_ARTIST_ONLY`

Pode produzir variação orgânica.

Para MCP:

`DISABLED_BY_DEFAULT`

Randomness precisa de seed e bounds se alguma operação equivalente for automatizada.

---

# 51. BRUSH PLUS / SMUDGE / NOISE / CLONE BRUSH

Classificação padrão:

`OPTIONAL_ARTIST_TOOL`

Podem ser úteis manualmente, mas não precisam virar tools MCP no MVP.

Se automatizados:

- seed;
- mask;
- target texture;
- bounded region;
- Undo.

---

# 52. TEXTURE DOWNSCALER

**Versão auditada:** 1.0.0  
**Desktop / Blockbench 5.x.**

Status:

`OPTIONAL_TEXTURE_OPTIMIZATION`

Downscale somente após:

- copy;
- visual diff;
- pixel-art nearest policy;
- contract approval.

---

# 53. REPEATING TEXTURES

**Versão auditada:** 3.0.0.

Status:

`OPTIONAL_VIEWPORT_TEXTURE_HELPER`

Não presumir que wrap/repeat configurado no viewport terá o mesmo comportamento runtime em todo provider.

---

# 54. TEXTURE FILTERING

Status:

`OPTIONAL_VIEWPORT_QA`

Minecraft pixel art normalmente deve ser avaliada em nearest.

Linear pode ser útil para diagnóstico, mas não redefine texture sampling do provider.

---

# 55. BAKED AMBIENT OCCLUSION

Status:

`OPTIONAL_ART_DIRECTION`

Pode ajudar em determinados styles.

Não aplicar automaticamente porque:

- Minecraft lighting já fornece shading contextual;
- baked AO pode conflitar com emissive/style;
- resource-pack visual language pode rejeitar.

---

# 56. PBR TOOLS — NÃO INSTALAR NO BASELINE

**Plugin:** PBR Tools  
**Versão de catálogo auditada:** 1.2.2  
**Compatibilidade declarada:** Blockbench 4.10.x–4.11.x.

Baseline:

Blockbench 5.1.6.

Logo:

`INCOMPATIBLE_EDITOR / BLOCKED_LEGACY`

Não fazer downgrade do editor apenas para usar esse plugin.

PBR futuro deve ser resolvido por:

- capabilities nativas atuais do Blockbench se comprovadas;
- shader/resource-pack provider real;
- adapter próprio;
- outro plugin moderno auditado.

---

# 57. CODE VIEW

**Versão auditada:** 1.0.1.

Status:

`PREFERRED_DIAGNOSTIC`

Bom para:

- verificar raw format;
- comparar serialização;
- diagnóstico.

Read-only para MCP.

---

# 58. EXPLORER

**Versão auditada:** 1.1.0  
**Desktop / min 5.1.0.**

Status:

`OPTIONAL_WORKFLOW`

Não expor navegação livre do filesystem ao MCP.

---

# 59. BACKUP VIEWER

Status:

`PREFERRED_RECOVERY`

Não substitui Git/source control.

Pode ser útil ao usuário, não precisa de tool MCP.

---

# 60. WORKSPACES

Status:

`OPTIONAL_PROJECT_ORGANIZATION`

Bom para separar:

- Enshrouded;
- RPG;
- Black Arcana;
- technology;
- resource packs.

Não é runtime capability.

---

# 61. LIVE DEV RELOADER

**Versão auditada:** 1.1.0  
**Blockbench 5.x desktop.**

Status:

`DEV_ONLY`

Usar durante desenvolvimento do `Repo Textura Asset Toolkit`.

Nunca exigir em produção.

---

# 62. PERFORMANCE AUDIT

Status:

`DEV_ONLY / DIAGNOSTIC`

Executar quando:

- muitos plugins;
- projeto pesado;
- viewport travando;
- texture tooling custoso.

---

# 63. GROUP EXPORTER

**Versão auditada:** 1.0.0.

Status:

`OPTIONAL_MODULAR_EXPORT`

Útil para:

- submodels;
- components;
- modular assets.

Não quebrar hierarchy contract.

---

# 64. JAVA BLOCK SEQUENCER

**Versão auditada:** 1.0.0  
**Blockbench mínimo:** 5.0.5.

Converte animação em sequência de block/item models.

Status:

`OPTIONAL_SPECIAL_CASE`

Bom para:

- animações discretas;
- props;
- UI/model swaps.

Não é substituto para GeckoLib/AzureLib quando rig real é necessário.

---

# 65. NO JAVA LIMITS

Status:

`CONDITIONAL_DISPLAY_ENTITIES`

Permite modelos grandes para display-entity workflows.

Não habilitar em native Java item/block profile genérico.

---

# 66. MOD UTILS / TABULA

**Mod Utils 1.7.1**

Uso:

- importar legado Tabula;
- VoxelShape.

Status:

`LEGACY_IMPORT_HELPER`

Não transformar Tabula em source canônico novo.

---

# 67. PLUGINS JAVA DO CATÁLOGO QUE NÃO DEVEM ENTRAR NO PRESET PADRÃO

## Loader/provider mismatch

- Fabric Modded Entity — Fabric/Yarn → `LOADER_MISMATCH`.
- VoxelShape Fabric Generator → `LOADER_MISMATCH`.

## Provider ausente

- sam3DJ / SC-Peripherals → provider ausente.
- Endimator / Blueprint → provider top-level não confirmado no snapshot atual.
- Highlight Mod Shape Generator → provider ausente.
- BAMO Exporter → provider ausente.
- ThreeCore Exporter → provider ausente.
- BBS exporter → provider correspondente não é authority atual.

## OptiFine-specific

- OptiFine Player Models → OptiFine não é authority do pack.
- CEM Template Loader só entra porque **EMF** está instalado; não porque OptiFine esteja.

## Deprecated

- GeckoLib Animation Utils antigo.
- Animation to Java Converter antigo — o catálogo o marca deprecated e limitado a Blockbench 4.12.x.

Esses plugins continuam registrados na auditoria para que um agente não os “descubra” depois e os instale por engano.

---

# 68. PRESETS DE EXTENSÕES — NÃO INSTALAR TUDO AO MESMO TEMPO

## PRESET A — BASE SAFE

Recomendados:

- Repo Textura Asset Toolkit próprio;
- Asset Browser;
- Reference Models;
- Bone View;
- Cameras;
- Resource Pack Utilities;
- UV Locker;
- Missing Texture Highlighter;
- Grayscale Preview;
- Code View;
- Brush Tuna;
- Colour Gradient Generator.

Objetivo:

authoring + QA, sem provider específico.

---

# 69. PRESET B — GECKOLIB

Base Safe +

- GeckoLib Models & Animations;
- Animation Sliders;
- Animated Platforms;
- opcional Bakery;
- opcional Bone View/renamers.

Não instalar antigo GeckoLib Animation Utils.

---

# 70. PRESET C — AZURELIB

Base Safe +

- AzureLib Animator;
- Animation Sliders;
- Animated Platforms.

Não converter projeto GeckoLib automaticamente para AzureLib.

---

# 71. PRESET D — NEOFORGE NATIVE

Base Safe +

- Animation to JSON Converter;
- ferramentas de animation/rig genericamente compatíveis.

Runtime consumer precisa ser provado na versão 1.21.1 antes de export final.

---

# 72. PRESET E — EMF/CEM

Base Safe +

- CEM Template Loader;
- EMF Animation Addon.

Usar somente para assets resource-pack/CEM.

---

# 73. PRESET F — EASY MODEL ENTITIES

Base Safe +

- Easy Model Entities Exporter **somente após pin/audit de release**.

Se ainda estiver fora do catálogo oficial:

instalação manual e explícita, não automatizada.

---

# 74. PRESET G — ANIMATED JAVA

Base Safe +

- Animated Java;
- No Java Limits somente quando exigido;
- Cameras;
- preview/recording helpers.

---

# 75. PRESET H — CPM

Base Safe +

- CPM Blockbench Plugin beta.

Uso inicialmente:

`HUMAN_ONLY / EXPERIMENTAL`

até regression suite local comprovar estabilidade.

---

# 76. PRESET I — RESOURCE PACK / ITEM / BLOCK

Base Safe +

- Tint Preview;
- Resource Pack Utilities;
- Resourcepack Packager;
- Group Exporter;
- Quick Box-UV Layout;
- Texture Stitcher quando necessário.

---

# 77. PRESET J — DEV DO TOOLKIT

- Live Dev Reloader;
- Performance Audit;
- Code View;
- Backup Viewer;
- Explorer.

Não distribuir como requisito para artista/usuário final.

---

# 78. PROVIDER PROFILE CONTRACT

Cada profile precisa declarar algo equivalente a:

```yaml
id: geckolib4_entity

authority:
  minecraft: "1.21.1"
  loader: "neoforge"
  provider_mod: "geckolib"
  provider_version: "runtime-resolved"

authoring:
  primary_editor: "blockbench"
  project_format: "geckolib"
  preserve_source: true
  source_extension: ".bbmodel"

extensions:
  required:
    - id: "geckolib"
  optional:
    - id: "animation_sliders"
    - id: "bone_view"

geometry:
  cubes: true
  meshes: "provider-dependent"
  locators: true
  free_rotation: "provider-dependent"

animation:
  supported: true
  molang: true
  easing: true
  effect_keyframes: true

export:
  model: ".geo.json"
  animation: ".animation.json"
  texture: ".png"

conversion:
  automatic_cross_profile: false
```

Isso é conceitual. Schema final será definido por TDD e não copiado cegamente deste exemplo.

---

# 79. PROFILES INICIAIS OBRIGATÓRIOS

Criar/adotar, se ainda pertinentes após a branch concorrente ser mergeada:

1. `java_block_item`
2. `neoforge_native_entity_animation`
3. `geckolib4_entity`
4. `geckolib4_item`
5. `geckolib4_block`
6. `geckolib4_armor`
7. `azurelib_entity`
8. `azurelib_item`
9. `azurelib_block`
10. `azurelib_armor`
11. `easy_model_entities_entity`
12. `easy_model_entities_block_entity`
13. `emf_cem_entity`
14. `animated_java_display_entities`
15. `cpm_player_model`
16. `player_animation_library_handoff`
17. `player_animator_handoff`
18. `sophisticated_backpacks_display`
19. `voxelshape_collision`
20. `structure_reference`
21. `epicfight_blender_handoff`

Não criar profile vazio só para aumentar contagem. Cada um precisa de capability real.

---

# 80. ARQUITETURA DE REPOSITÓRIO PROPOSTA

A infraestrutura existente continua canônica.

Evolução possível:

```text
Repo Textura/
├── docs/ or standards/                    # usar os diretórios canônicos já existentes
│   ├── MODEL-ASSET-CONTRACT.md
│   ├── VISUAL-QA.md
│   ├── BLOCKBENCH-LIVE-BRIDGE-CONTRACT.md
│   ├── BLOCKBENCH-EXTENSION-POLICY.md
│   └── ASSET-PROVIDER-PROFILE-CONTRACT.md
├── skills/                                # somente se o Repo Textura já usar esta convenção
│   ├── minecraft-asset-art-direction/
│   ├── minecraft-blockbench-geckolib/
│   ├── minecraft-visual-qa/
│   ├── minecraft-vfx-engineering/
│   └── minecraft-blockbench-live-bridge/
└── tools/
    └── blockbench/
        └── repo-textura-asset-toolkit/
                ├── repo_textura_asset_toolkit.js
                ├── core/
                │   ├── project-model/
                │   ├── validator/
                │   ├── contract-profile/
                │   ├── provider-profile/
                │   ├── extension-registry/
                │   ├── transaction-engine/
                │   ├── diff-engine/
                │   ├── export-policy/
                │   └── safety-policy/
                ├── adapters/
                │   ├── blockbench-core/
                │   ├── geckolib/
                │   ├── azurelib/
                │   ├── neoforge-native/
                │   ├── easy-model-entities/
                │   ├── emf/
                │   ├── animated-java/
                │   └── external-handoff/
                ├── blockbench-plugin/
                │   ├── project-observer/
                │   ├── geometry-commands/
                │   ├── rig-commands/
                │   ├── uv-commands/
                │   ├── texture-commands/
                │   ├── animation-commands/
                │   ├── capture-commands/
                │   └── bridge-client/
                ├── mcp/
                │   ├── server/
                │   ├── schemas/
                │   ├── tool-registry/
                │   ├── session-manager/
                │   └── transport/
                └── tests/
                    ├── unit/
                    ├── profiles/
                    ├── extensions/
                    ├── protocol/
                    ├── integration/
                    ├── security/
                    └── golden/
```

Não criar diretórios antecipadamente sem necessidade.

---

# 81. ARQUITETURA DE EXECUÇÃO

Preferida:

```text
AI / MCP-capable client
        │
        ▼
Repo Textura Asset MCP sidecar
        │
        │ authenticated loopback
        ▼
Repo Textura Asset Toolkit Blockbench plugin
        │
        ├── Core Blockbench API
        ├── Provider Profile Resolver
        └── Allowlisted Extension Adapters
        │
        ▼
Active Blockbench Project
```

O MCP não implementa 3D.

O plugin não decide gameplay.

O provider profile não inventa formato.

---

# 82. SIDECAR MCP

Responsabilidades:

- JSON Schema;
- auth/session;
- replay/idempotência;
- revisions;
- bounded requests;
- permission class;
- routing;
- logging;
- result normalization.

Não:

- shell;
- arbitrary file;
- arbitrary JS;
- arbitrary plugin action.

---

# 83. TRANSPORTE LOCAL

Preferir:

```text
MCP stdio
   ↓
sidecar
   ↓
WebSocket/IPC autenticado em loopback
   ↓
Blockbench plugin
```

Requisitos:

- `127.0.0.1`/loopback;
- token efêmero;
- handshake;
- protocol version;
- capability negotiation;
- heartbeat;
- timeout;
- reconnect;
- session invalidation.

Remote/tunnel é adapter separado.

---

# 84. MODELO DE SEGURANÇA

## Classe A — read-only

- inspect;
- list;
- validate;
- capture;
- report.

## Classe B — additive/reversible

- create bone;
- create cube;
- create locator;
- create texture;
- create animation;
- add keyframe.

## Classe C — destructive/high-impact

- delete;
- global UV repack;
- texture replacement;
- subtree reparent;
- bulk rename;
- provider conversion;
- overwrite export.

Exigir:

- dry-run;
- diff;
- confirmation token;
- expected revision.

## Classe D — proibida

- `eval`;
- `execute_script`;
- shell;
- arbitrary filesystem;
- arbitrary HTTP;
- arbitrary process;
- plugin install;
- dynamic remote code.

---

# 85. INSTALLED ≠ ALLOWLISTED

Regra fundamental:

```text
plugin installed
≠
plugin trusted
≠
plugin compatible
≠
plugin MCP-exposed
```

Para uma extensão ser chamada pelo MCP:

1. source/behavior auditado;
2. versão identificada;
3. profile compatível;
4. adapter allowlisted;
5. tool schema restrito;
6. rollback/Undo quando mutável;
7. regression.

---

# 86. TRANSAÇÕES E REVISÕES

Toda mutation:

```text
project_id
project_revision
operation_id
expected_revision
dry_run
```

Fluxo:

```text
schema
↓
session
↓
profile
↓
extension capability
↓
expected revision
↓
dry-run
↓
Undo transaction
↓
mutation
↓
postcondition
↓
validation
↓
revision++
↓
result
```

Mismatch:

`FAIL-CLOSED — PROJECT_CHANGED`

---

# 87. IDEMPOTÊNCIA

Ledger por sessão:

```text
operation_id
request_hash
result_hash
revision_before
revision_after
```

Mesmo ID + mesmo payload:

replay result sem repetir mutation.

Mesmo ID + payload diferente:

`FAIL-CLOSED — REPLAY_CONFLICT`

---

# 88. OBSERVABILIDADE READ-ONLY — PRIMEIRO MILESTONE

Tools:

```text
blockbench.get_status
blockbench.get_capabilities
blockbench.get_project
blockbench.get_scene_graph
blockbench.get_selection
blockbench.get_bones
blockbench.get_elements
blockbench.get_textures
blockbench.get_animations
blockbench.get_animation
blockbench.compute_bounds
blockbench.validate
blockbench.validate_contract

blockbench.extensions.list
blockbench.extensions.get
blockbench.profiles.list
blockbench.profiles.resolve_for_asset
```

Nenhuma mutation antes desse milestone estar estável.

---

# 89. MODELING TOOLS

```text
model.create_bone
model.update_bone
model.reparent_bone
model.set_pivot

model.create_cube
model.update_cube
model.reparent_cube

model.create_locator
model.update_locator

model.apply_geometry_batch
```

`apply_geometry_batch` aceita somente operation AST allowlisted.

Nunca JS.

---

# 90. RIGGING TOOLS

```text
rig.inspect
rig.validate_hierarchy
rig.validate_pivots
rig.validate_attachment_points
rig.validate_animation_targets
rig.mirror_safe
rig.rename_preview
rig.rename_apply
```

Future:

`rig.ik_assist`

somente em profile/provider que comprove suporte e sem transformar helper de authoring em runtime assumption.

---

# 91. UV TOOLS

```text
uv.inspect
uv.generate_box
uv.set_face
uv.pack_preview
uv.pack_apply
uv.validate
uv.measure_texel_density
uv.compare_density
```

Não definir densidade global inventada.

Golden Samples + Asset Contract fornecem evidence.

---

# 92. TEXTURE TOOLS

```text
texture.list
texture.create
texture.inspect
texture.sample_palette
texture.paint_region
texture.paint_uv_island
texture.fill
texture.replace_palette
texture.import_approved
texture.validate
texture.compare
```

Mutation limitada por:

- texture ID;
- region;
- UV mask;
- dimensions;
- palette;
- alpha;
- operation bounds.

---

# 93. CONCEPT ART ≠ TEXTURE FINAL

Pipeline:

```text
prompt
↓
concept sheet
↓
art direction review
↓
model brief
↓
geometry
↓
UV
↓
texture authoring over real UV
```

Não:

```text
AI image
↓
stretch onto UV
↓
final
```

---

# 94. ANIMATION TOOLS

Core:

```text
animation.list
animation.create
animation.update_settings
animation.delete

animation.add_keyframe
animation.update_keyframe
animation.delete_keyframe

animation.set_loop_mode
animation.set_easing
animation.set_length

animation.add_effect_marker
animation.play_preview
animation.stop_preview
animation.inspect_pose
```

High-level:

```text
animation.scaffold_set
animation.validate_loop_seam
animation.validate_foot_slide
animation.compare_clips
animation.layer_preview
```

Retarget:

`animation.retarget`

somente dentro de rigs/profiles explicitamente compatíveis ou com bone map formal.

---

# 95. ANIMATION SCAFFOLD SETS

Exemplo humanoide genérico:

```text
idle
walk
run
hurt
death
attack_1
attack_2
```

Boss:

```text
idle
walk
run
stagger
attack_melee_1
attack_melee_2
attack_ranged
cast
summon
phase_transition
death
```

Spellcaster:

```text
cast_start
cast_loop
cast_release
cast_recover
```

Esses nomes são templates, não nomes globais obrigatórios.

O provider profile pode exigir outra convenção.

---

# 96. GAMEPLAY AUTHORITY

Nenhuma timeline Blockbench define automaticamente:

- dano;
- hitbox;
- stamina;
- cooldown;
- target;
- crit;
- knockback;
- resource cost;
- server-side movement.

Animation marker pode sincronizar apresentação ou acionar um adapter aprovado.

Gameplay continua no mod/provider.

---

# 97. VFX / SFX ANCHORS

O Asset Contract deve declarar anchors reais.

Exemplos apenas ilustrativos:

```text
weapon_tip
spell_origin
muzzle
hand_r_fx
hand_l_fx
head_fx
chest_fx
ground_anchor
```

Não impor universalmente.

Validar:

- existence;
- parent;
- pivot;
- transform;
- pose consistency.

---

# 98. PHOTON / LODESTONE / FALLBACK DE PARTÍCULAS — HANDOFF

Photon está presente no snapshot físico atual; Lodestone também está presente como candidate de rendering/partículas. AAA Particles/AAA Particles World não devem ser tratados como presentes sem nova confirmação física. Nenhum deles é extensão Blockbench.

O Blockbench pipeline pode fornecer:

- anchors;
- timing markers;
- transforms;
- screenshots;
- VFX brief.

A execução do efeito pertence ao backend VFX.

Não fazer o Toolkit fingir que Photon é uma animation codec do Blockbench.

---

# 99. CAPTURE / VISUAL QA

Quando APIs/extensões permitirem:

```text
capture.front
capture.side
capture.back
capture.three_quarter
capture.top
capture.animation_pose
capture.turntable_sequence
```

Manifest:

```text
project_revision
provider_profile
extension_fingerprint
camera_preset
animation
animation_time
resolution
timestamp
```

---

# 100. QA VISUAL

Avaliar:

- silhouette;
- proportions;
- scale;
- clipping;
- readability;
- UV seams;
- texture artifacts;
- value hierarchy;
- bone deformation;
- pivots;
- emissive;
- translucency;
- anchors;
- animation readability;
- foot sliding;
- loop seam.

Structural PASS ≠ visual PASS.

---

# 101. EXPORT

Tools:

```text
export.preview
export.validate_paths
export.provider
export.model
export.animation
export.texture
export.bundle
export.manifest
```

Fluxo:

```text
validate
↓
resolve provider
↓
resolve exporter
↓
preview paths
↓
staging
↓
validate output
↓
diff
↓
promote
```

---

# 102. EXPORT ROOT POLICY

Allowlisted roots:

- asset source;
- target mod resources;
- approved resource pack;
- approved datapack;
- staging temp.

Proteções:

- canonical path;
- block `..`;
- symlink escape;
- unexpected absolute paths;
- overwrite guard.

---

# 103. `.BBMODEL` SOURCE PRESERVATION

Para assets Blockbench project-owned:

`.bbmodel` permanece fonte de authoring salvo provider/contract explícito em contrário.

Nunca apagar source após export.

Também preservar:

- CPM `.cpmproject`;
- Blender `.blend` para Epic Fight quando project-owned;
- Animated Java Blueprint source;
- provider-specific source equivalente.

---

# 104. EXTENSION-SPECIFIC EXPORT

O MCP não deve “clicar em File > Export” genericamente.

Ele deve resolver:

```text
asset profile
→ provider adapter
→ compatible extension/codec
→ validated exporter
```

Se exporter não existir:

`UNAVAILABLE_EXPORTER`

---

# 105. CONVERSÃO ENTRE PROVIDERS

Todas as tools de conversão devem ser high-risk.

Fluxo:

```text
source profile
↓
target profile
↓
capability intersection
↓
loss report
↓
dry-run
↓
new project copy
↓
structural validation
↓
visual QA
```

Nunca converter in-place por padrão.

---

# 106. GOLDEN SAMPLES

Os Golden Samples históricos da PR #484 já foram mergeados no repositório RPG histórico. No Repo Textura, eles devem ser auditados, reconciliados e migrados apenas quando forem project-owned e pertinentes; não duplicar corpus equivalente já existente.

Golden Samples desejados, sem duplicar o que o outro chat já criar:

- simple mob;
- quadruped;
- humanoid;
- boss;
- animated item;
- armor;
- block entity;
- projectile/construct;
- locator-heavy;
- emissive texture;
- effect keyframes;
- Java block/item;
- EME profile;
- EMF/CEM resource-pack sample;
- Animated Java rig;
- player animation handoff.

---

# 107. ROUND-TRIP TESTS

Para cada profile:

```text
source
↓
import
↓
normalized representation
↓
edit
↓
export staging
↓
re-import when possible
↓
semantic compare
```

Não exigir bytes iguais se serializer normaliza ordem/format.

Comparar semântica.

---

# 108. EXTENSION DRIFT TESTS

Criar fixture:

```text
Blockbench version X
plugin version Y
provider version Z
```

Se versão mudar:

- rerun compatibility;
- rerun smoke;
- mark profile stale;
- block final export when incompatibility could corrupt asset.

---

# 109. TESTES UNITÁRIOS CORE

Cobrir:

- invalid vectors;
- duplicate bones;
- cycles;
- invalid pivots;
- invalid bounds;
- textures;
- UV;
- locators;
- animation targets;
- required bones;
- required animations;
- provider profile resolution;
- extension resolution;
- incompatible versions;
- stale revision;
- replay;
- rollback;
- path policy;
- schema validation.

---

# 110. SECURITY TESTS

Obrigatórios:

- path traversal;
- symlink escape;
- giant payload;
- malformed payload;
- stale revision;
- replay conflict;
- wrong token;
- expired session;
- non-loopback peer;
- unknown plugin;
- plugin version mismatch;
- plugin action not allowlisted;
- provider mismatch;
- arbitrary command attempt;
- arbitrary JS attempt.

---

# 111. BLOCKBENCH REAL SMOKE

Checklist mínima:

1. carregar Repo Textura Asset Toolkit;
2. abrir Golden Sample;
3. conectar bridge;
4. status;
5. extension fingerprint;
6. profile resolve;
7. validate;
8. create bone;
9. Undo;
10. Redo;
11. create cube;
12. Undo;
13. pivot mutation;
14. UV operation;
15. texture bounded mutation;
16. create animation;
17. add keyframe;
18. preview;
19. capture;
20. export staging;
21. close/reopen;
22. validate persistence.

---

# 112. PROVIDER-SPECIFIC SMOKES

Além do smoke base:

## GeckoLib
- new/loaded GeckoLib project;
- model;
- animation;
- effect marker;
- export;
- runtime.

## AzureLib
- Azure model;
- custom easing;
- export;
- runtime.

## EME
- profile export;
- datapack/resourcepack;
- provider validation command;
- spawn/place.

## EMF
- CEM model;
- animation;
- resource-pack load.

## Animated Java
- blueprint;
- variant;
- locator;
- function/effect keyframe;
- datapack/resourcepack runtime.

## CPM
- import/export round-trip;
- animation preservation;
- current known issues regression.

## Epic Fight
- only handoff validation, then Blender/provider workflow.

---

# 113. QA IN-GAME

Depois de export:

- model;
- texture;
- scale;
- animation;
- held alignment;
- attachments;
- anchors;
- lighting;
- emissive;
- clipping;
- multiplayer when relevant;
- client/server boundary;
- dedicated server when Java changes.

---

# 114. DEDICATED SERVER

Blockbench/MCP não entra no Minecraft runtime JAR.

Java renderer changes:

- client-only classes behind correct boundary;
- no Blockbench package/class in runtime;
- optional provider classloading safe;
- dedicated server smoke.

---

# 115. CI

Expandir gates existentes sem reduzir nenhum:

```text
node --check
node --test
profile schema tests
extension registry tests
protocol tests
security tests
golden sample tests
repository skill validator
```

Se TypeScript:

```text
typecheck
build
bundle check
artifact consistency
```

Node tooling não deve contaminar runtime Java.

---

# 116. TDD

Cada capability:

`RED → minimum GREEN → refactor → provider smoke`

Exemplos:

- extension incompatible é aceita → RED → block → GREEN;
- stale revision muta → RED → reject → GREEN;
- retry duplica cube → RED → ledger → GREEN;
- EME exporter ausente é substituído silenciosamente → RED → UNAVAILABLE → GREEN;
- GeckoLib project convertido para AzureLib sem aviso → RED → conversion gate → GREEN.

---

# 117. ESTRATÉGIA DE PRs

Não mega-PR.

## PR 1 — Core modular + Extension/Provider Registry

- extract core;
- profiles;
- extension registry;
- schemas;
- tests.

## PR 2 — Read-only Live Bridge

- sidecar;
- auth;
- fingerprint;
- observability;
- profile resolution.

## PR 3 — Modeling + Rig Mutations

- bones;
- cubes;
- locators;
- pivots;
- Undo;
- revision.

## PR 4 — UV + Texture

- deterministic UV;
- masks;
- paint;
- palette;
- validation.

## PR 5 — Generic Animation Core

- animation;
- keyframes;
- loops;
- captures;
- validation.

## PR 6 — GeckoLib Adapter

- provider profile;
- codec/export;
- effect markers;
- Golden regression.

## PR 7 — AzureLib Adapter

- independent profile;
- easing/IK authoring awareness;
- export/runtime QA.

## PR 8 — NeoForge Native Animation Adapter

Somente após target 1.21.1 API proof.

## PR 9 — EME Adapter

Somente após exporter/plugin release pin/audit.

## PR 10 — EMF/CEM Adapter

Resource-pack profile.

## PR 11 — Animated Java Adapter

Display-entity/cinematic profile.

## PR 12 — Player Profiles

- CPM experimental;
- PAL handoff;
- Player Animator audit.

## PR 13 — External DCC / Epic Fight Handoff

Sem fingir Blockbench-native.

## PR 14 — Unified QA + Export Manifest

Se ainda houver valor em separar.

PR count pode ser consolidada depois, mas não misturar providers sem necessidade.

---

# 118. GITHUB CONCURRENCY

Antes de cada PR:

1. fetch `origin/main`;
2. registrar SHA;
3. buscar PR/branch equivalente;
4. verificar Golden Samples/art changes;
5. branch da main atual;
6. implementar;
7. main avançou → merge `origin/main -> branch`;
8. conflitos semânticos;
9. rerun;
10. diff;
11. CI;
12. fetch final main;
13. reconcile;
14. revalidate;
15. merge;
16. confirmar main;
17. registrar SHA pós-merge.

Sem force-push/rebase de rotina em branch compartilhada.

---

# 119. GATE IMEDIATO DE CONCORRÊNCIA

Antes de iniciar qualquer implementação no Repo Textura:

1. confirmar o remote Git canônico da Minecraft Mod Factory e a branch padrão;
2. executar fetch;
3. registrar o SHA atual;
4. listar branches, PRs e worktrees ativos relacionados a assets, Blockbench, Golden Samples, Visual Style Bible, VFX, validators e tooling;
5. detectar arquivos sobrepostos;
6. reconciliar este plano com a documentação canônica já existente;
7. somente então iniciar a primeira PR/branch desta frente.

Se houver trabalho fundacional concorrente nos mesmos arquivos ou contratos, não duplicar nem sobrescrever silenciosamente. Integrar após reconciliação ou separar o escopo quando a independência estiver comprovada.

---

# 120. USER-GUIDED INSTALLATION

Quando chegar a hora de instalar extensões:

não mandar 20 passos de uma vez.

Formato:

> Faça somente esta etapa e me mande o resultado.

Exemplo:

1. confirmar Blockbench version;
2. usuário manda screenshot/resultado;
3. instalar Base Safe;
4. validar;
5. só então instalar provider preset necessário.

Nunca “instale todos estes plugins” de uma vez.

---

# 121. EXTENSION INSTALL POLICY

Plugin installation:

- sempre humana;
- sempre explícita;
- uma etapa por vez;
- preferir catálogo oficial;
- provider-maintained externo somente após audit;
- pin version/source;
- não instalar dev/master sem motivo;
- rollback/document removal path.

O MCP nunca terá permissão de instalar plugin.

---

# 122. CHATGPT CONNECTIVITY

O core não depende do ChatGPT.

```text
Blockbench plugin
↑
local bridge
↑
MCP server
↑
client adapter
```

Clientes podem mudar.

Se ChatGPT atual exigir remote MCP/tunnel:

isso é adapter de conectividade.

Não redesenhar o editor bridge por limitação temporária de produto.

---

# 123. REFERÊNCIAS MCP EXTERNAS

Arquiteturas comunitárias úteis como referência:

- `jasonjgardner/blockbench-mcp-plugin`;
- `sosadly/blockbench-mcp`;
- `SwagRee/BlockBenchMCP`.

Regras:

- source/license audit;
- não copiar tool schemas cegamente;
- não importar arbitrary JS;
- preferir intent-level declarative operations;
- auth;
- fail-closed;
- explicit success/failure.

---

# 124. PENDÊNCIA — PROVIDER NÃO INSTALADO, NÃO INTEGRAR

Foi encontrado também `BlockbenchLib`, uma biblioteca capaz de consumir `.bbmodel` em determinados setups.

Ela **não está na modlist física atual**.

Classificação:

`PROVIDER_ABSENT / RESEARCH_ONLY`

Não adicionar dependência apenas porque facilitaria o MCP.

---

# 125. PERFORMANCE

Limites configuráveis:

- bones/mutation;
- cubes/mutation;
- keyframes/request;
- texture pixels/request;
- screenshot batch;
- animation duration;
- payload size;
- timeout;
- export bundle size.

No profiling:

- Blockbench CPU;
- UI freeze;
- memory;
- plugin interaction;
- validation time.

---

# 126. FAIL-CLOSED

Bloquear quando:

- project unknown;
- revision mismatch;
- provider unknown;
- provider version unsupported;
- required extension missing;
- extension version mismatch;
- profile mismatch;
- exporter unknown;
- path not allowed;
- schema invalid;
- capability missing;
- conversion lossy not acknowledged.

---

# 127. FAIL-SOFT

Pode degradar quando:

- capture unavailable → Visual QA pending;
- optional extension missing → core workflow continues;
- external DCC unavailable → handoff pending;
- concept image unavailable → brief/reference workflow continues;
- optional texture helper unavailable → native authoring remains.

---

# 128. CRITÉRIOS MVP

MVP não precisa implementar todos os providers.

Obrigatório:

- [ ] Blockbench 5.x session;
- [ ] sidecar;
- [ ] auth;
- [ ] protocol;
- [ ] extension fingerprint;
- [ ] provider profile resolver;
- [ ] read-only project inspection;
- [ ] current validator preserved;
- [ ] revision/Undo;
- [ ] idempotency;
- [ ] bone/cube/locator mutations;
- [ ] UV basic;
- [ ] bounded texture mutation;
- [ ] generic animation/keyframes;
- [ ] capture;
- [ ] staging export;
- [ ] path security;
- [ ] Golden Sample;
- [ ] no arbitrary script;
- [ ] CI.

---

# 129. CRITÉRIOS V1

- [ ] GeckoLib complete profile;
- [ ] AzureLib complete profile;
- [ ] one native NeoForge profile if target API proven;
- [ ] EME profile if exporter stable;
- [ ] EMF/CEM profile;
- [ ] Animated Java profile;
- [ ] external Epic Fight handoff;
- [ ] player runtime handoff;
- [ ] extension presets;
- [ ] drift detection;
- [ ] visual evidence manifests;
- [ ] in-game examples.

---

# 130. CRITÉRIOS “TOP” / V2

Depois de V1 estável:

- semantic retarget within compatible rigs;
- pose library;
- animation layer composer;
- foot-slide metric;
- silhouette metric;
- palette harmonizer;
- UV island semantic masks;
- texture material-region system;
- deterministic procedural texture brushes;
- provider-aware asset scaffolding;
- VFX anchor preview;
- batch asset QA;
- multi-angle visual diff;
- regression screenshot corpus;
- project-wide art budget dashboards;
- optional Blender handoff automation;
- optional EME/Animated Java scene generation.

Tudo condicionado a provas.

---

# 131. RISCOS NOVOS IDENTIFICADOS PELA AUDITORIA

## Plugin collision

GeckoLib, AzureLib, CEM, Animated Java e CPM alteram formatos/animation UI.

Mitigação:

- presets;
- no “install everything”;
- capability fingerprint;
- per-profile smoke.

## External plugin beta

CPM e EME plugin paths podem ter maturidade diferente.

Mitigação:

- human-only;
- pin;
- regression.

## Version drift

Blockbench evolui rápido.

Mitigação:

- version bounds;
- blockbench-types;
- adapter layer.

## Lossy conversion

Bakery, converter, retarget, provider switching.

Mitigação:

- source copy;
- dry-run;
- semantic diff.

## Wrong authority

Epic Fight uses Blender; EMF is resource-pack; Animated Java is display/datapack.

Mitigação:

- profile-specific boundaries.

---

# 132. SOURCE / LICENSE PROVENANCE

Antes de reutilizar código externo:

registrar:

- repository;
- commit/tag;
- file;
- license;
- copied/adapted concept;
- reason;
- modifications.

Quando license incerta:

`REFERENCE_ONLY`

Não copiar code de MCP/plugin comunitário só porque funciona.

---

# 133. DOCUMENTOS A CRIAR FUTURAMENTE

Somente se ainda não existirem equivalentes após Golden Samples:

- `BLOCKBENCH-LIVE-BRIDGE-CONTRACT.md`
- `BLOCKBENCH-EXTENSION-POLICY.md`
- `BLOCKBENCH-EXTENSION-CATALOG.md`
- `ASSET-PROVIDER-PROFILES.md`
- `BLOCKBENCH-MCP-SECURITY.md`
- `BLOCKBENCH-MCP-PROTOCOL.md`
- `BLOCKBENCH-MCP-TOOLS.md`
- `BLOCKBENCH-LIVE-BRIDGE-SOURCES.md`

Consolidar documentos quando possível.

---

# 134. SKILLS

Não criar uma skill nova para cada provider.

Preferência:

- `minecraft-blockbench-geckolib` pode virar skill mais geral ou permanecer especializada;
- criar `minecraft-blockbench-live-bridge` somente se fluxo MCP justificar;
- provider profiles devem ser dados/docs, não 20 skills.

Router decide qual profile consultar.

---

# 135. EXEMPLO — MOB GECKOLIB

Pedido:

> Criar demônio corrompido quadrúpede Enshrouded.

Resolver:

```text
asset type: entity
runtime requirement: mod-owned animated entity
provider: GeckoLib if proven chosen
profile: geckolib4_entity
```

Pipeline:

```text
Visual Style Bible
→ brief
→ source references
→ GeckoLib project
→ rig
→ geometry
→ UV
→ texture
→ idle/walk/run/attack/hurt/death
→ anchors
→ structural QA
→ capture
→ visual QA
→ .geo.json/.animation.json/.png staging
→ mod integration
→ Minecraft QA
```

---

# 136. EXEMPLO — AMBIENT CRITTER EME

Se não exigir AI/physics complexa própria:

```text
profile: easy_model_entities_entity
```

Pode ser muito mais econômico que criar:

- entity class;
- renderer;
- animation controller;
- boilerplate por modelo.

Mas comportamento/provider continua vindo de EME e do profile.

---

# 137. EXEMPLO — FRESH ANIMATIONS / RESOURCE PACK OVERRIDE

```text
profile: emf_cem_entity
extensions:
  CEM Template Loader
  EMF Animation Addon
```

Não usar GeckoLib.

Output:

resource-pack/CEM/EMF.

---

# 138. EXEMPLO — CUTSCENE

```text
profile: animated_java_display_entities
```

Usar:

- groups;
- displays;
- locators;
- cameras;
- variants;
- animation;
- function keyframes.

Gameplay crítico continua fora da timeline.

---

# 139. EXEMPLO — PLAYER COMBAT EPIC FIGHT

Não:

```text
Blockbench → Epic Fight animation JSON
```

Correto:

```text
Blockbench reference/concept/model handoff
→ Blender
→ Epic Fight Player Animation Rig
→ Epic Fight Blender Exporter
→ runtime test
```

---

# 140. EXEMPLO — PLAYER COSMETIC CPM

```text
profile: cpm_player_model
```

Inicialmente:

- human-driven plugin;
- round-trip tests;
- no automatic animation conversion.

---

# 141. DEFINIÇÃO FINAL DE PRONTO

O sistema não está pronto porque:

- “MCP conectou”;
- “criou cube”;
- “exportou JSON”.

Está pronto quando existe:

```text
provider authority
+ extension registry
+ compatibility fingerprint
+ declarative tools
+ transactions
+ Undo
+ idempotency
+ structural QA
+ visual QA
+ Golden regression
+ export safety
+ provider-specific smoke
+ Minecraft runtime validation
```

---

# 142. HANDOFF PARA IMPLEMENTAÇÃO NO REPO TEXTURA

Quando esta frente for implementada:

1. confirmar o remote canônico da Minecraft Mod Factory;
2. fetch da branch padrão;
3. registrar o SHA atual;
4. revisar Golden Samples canônicos existentes;
5. revisar mudanças no Repo Textura Asset Toolkit ou tooling equivalente;
6. revisar skills, standards, Visual Style Bible e contratos de assets;
7. comparar este plano com a árvore real;
8. eliminar duplicações;
9. ajustar provider profiles à modlist física vigente;
10. procurar branch/PR equivalente;
11. iniciar somente a primeira PR ainda necessária.

Nenhum SHA, branch ou caminho histórico do antigo repositório RPG deve ser tratado como autoridade no Repo Textura.

---

# 143. MATRIZ RESUMIDA — O QUE EU INSTALARIA / USARIA

| Extensão | Status no nosso pipeline |
|---|---|
| Repo Textura Asset Toolkit | CANÔNICA / própria |
| GeckoLib Models & Animations | REQUIRED quando GeckoLib |
| AzureLib Animator | REQUIRED quando AzureLib |
| Animation to JSON | PREFERRED / NeoForge native após runtime proof |
| CEM Template Loader | REQUIRED no profile EMF/CEM |
| EMF Animation Addon | PREFERRED no profile EMF |
| Easy Model Entities Exporter | EXPERIMENTAL / provider-maintained até release audit |
| Animated Java | OPTIONAL HIGH-VALUE profile |
| CPM Blockbench Plugin | EXPERIMENTAL / HUMAN_ONLY inicialmente |
| Asset Browser | PREFERRED |
| Reference Models | PREFERRED |
| Bone View | PREFERRED |
| Cameras | PREFERRED |
| Resource Pack Utilities | PREFERRED |
| UV Locker | PREFERRED |
| Missing Texture Highlighter | PREFERRED |
| Grayscale Preview | PREFERRED |
| Brush Tuna | PREFERRED |
| Colour Gradient Generator | PREFERRED |
| Animation Sliders | PREFERRED para animation work |
| Animated Platforms | PREFERRED para locomotion QA |
| Export to Blender | PREFERRED handoff |
| GLTF Importer | OPTIONAL reference |
| Group Exporter | OPTIONAL |
| Tint Preview | PREFERRED para Java block/item tint |
| Texture Stitcher | OPTIONAL |
| Plaster | OPTIONAL/PREFERRED texture QA |
| Texture Downscaler | OPTIONAL |
| Bakery | OPTIONAL LOSSY |
| Duplicate Bone Renamer | OPTIONAL HIGH-RISK rename |
| Batch Group Rename | OPTIONAL HIGH-RISK refactor |
| VoxelShape Generators | OPTIONAL block collision |
| Structure Importer | OPTIONAL |
| Structure to Model | OPTIONAL |
| Resourcepack Packager | OPTIONAL |
| Java Block Sequencer | OPTIONAL special-case |
| No Java Limits | CONDITIONAL Animated Java/display |
| Live Dev Reloader | DEV_ONLY |
| Performance Audit | DEV_ONLY |
| PBR Tools 1.2.2 | BLOCKED on Blockbench 5.1.6 |
| GeckoLib Animation Utils legacy | BLOCKED |
| Animation to Java Converter legacy | BLOCKED/deprecated |
| Fabric Modded Entity | LOADER_MISMATCH |
| VoxelShape Fabric Generator | LOADER_MISMATCH |
| OptiFine Player Models | PROVIDER_NOT_AUTHORITY |
| SC-Peripherals/ThreeCore/BAMO/Highlight exporters | PROVIDER_ABSENT |

---

# 144. FONTES AUDITADAS

## Blockbench

- Blockbench plugin development documentation  
  https://blockbench.net/wiki/docs/plugin/
- Blockbench Reference Docs  
  https://web.blockbench.net/docs/
- Official Blockbench plugin catalog  
  https://github.com/JannisX11/blockbench-plugins
- Blockbench releases  
  https://github.com/JannisX11/blockbench/releases

## GeckoLib

- GeckoLib Blockbench authoring  
  https://github.com/bernie-g/geckolib/wiki/Making-Your-Models-(Blockbench)
- GeckoLib 4 Geo Models  
  https://github.com/bernie-g/geckolib/wiki/Geo-Models-(Geckolib4)
- GeckoLib 4 Keyframe Triggers  
  https://github.com/bernie-g/geckolib/wiki/Keyframe-Triggers-(Geckolib4)

## AzureLib

- AzureLib source/docs  
  https://github.com/AzureDoom/AzureLib
- AzureLib Animator source in Blockbench plugin catalog  
  https://github.com/JannisX11/blockbench-plugins/tree/master/src/azurelib_utils

## Easy Model Entities

- Provider source/documentation  
  https://github.com/MarkusBordihn/BOs-Easy-Model-Entities
- Blockbench exporter contribution  
  https://github.com/JannisX11/blockbench-plugins/pull/921

## CPM

- CPM Blockbench plugin documentation  
  https://github.com/tom5454/CustomPlayerModels/tree/master/Blockbench

## Player Animation Library

- Provider source  
  https://github.com/PlayerAnimationLibrary/PlayerAnimationLibrary

## Epic Fight

- Epic Fight custom animation documentation  
  https://epicfight-docs.readthedocs.io/

## Animated Java

- Project/docs  
  https://animated-java.dev/

## MCP architecture references

- jasonjgardner/blockbench-mcp-plugin
- sosadly/blockbench-mcp
- SwagRee/BlockBenchMCP

> Antes de implementar, repetir a auditoria de freshness e licenças. URLs acima são fontes técnicas, não autorização para copiar código.

---

# 145. CONCLUSÃO

O pipeline final não deve ser “um MCP que sabe mexer no Blockbench”.

Ele deve ser:

**um sistema de authoring provider-aware para Minecraft 1.21.1**, capaz de escolher a ferramenta correta, recusar caminhos incompatíveis, aproveitar extensões comprovadas e manter o mod/runtime real como authority.

A arquitetura final é:

```text
User / AI Intent
        ↓
Visual Style Bible
        ↓
Asset Contract
        ↓
Provider Profile Resolver
        ↓
Extension Capability Registry
        ↓
Repo Textura Asset MCP
        ↓
Repo Textura Asset Toolkit
        ↓
Blockbench Core API
        ├── GeckoLib
        ├── AzureLib
        ├── NeoForge native
        ├── EME
        ├── EMF/CEM
        ├── Animated Java
        ├── CPM
        └── safe generic extensions
        ↓
Provider-specific export / handoff
        ├── mod resources
        ├── resource pack
        ├── datapack
        └── Blender/Epic Fight when required
        ↓
Minecraft 1.21.1
        ↓
QA real
```

Essa é a diferença entre simplesmente automatizar cliques e construir uma pipeline artística tecnicamente correta para um modpack grande.

No contexto deste projeto, toda essa infraestrutura pertence ao **Repo Textura**. Os repositórios dos mods recebem apenas os artefatos e contratos necessários para integração no runtime; a lógica funcional continua fora do escopo deste repositório.


---

# APÊNDICE A — DISPOSIÇÃO DO CATÁLOGO OFICIAL “MINECRAFT: JAVA EDITION”

Este apêndice existe para que a implementação futura não confunda “não recomendado” com “não auditado”.

A lista é baseada no snapshot do catálogo oficial pesquisado durante esta revisão. O catálogo muda; portanto ela deve ser atualizada antes da implementação.

| Plugin / extensão | Versão auditada quando confirmada | Disposição para este projeto | Motivo |
|---|---:|---|---|
| sam3DJ | 1.1.1 | `PROVIDER_ABSENT` | Exporter ligado a SC-Peripherals/.3DJ; provider não é authority atual |
| Animated Java | 1.10.2 | `OPTIONAL_HIGH_VALUE` | Display entities, datapack/resource pack, rigs, animations, variants, locators/cameras |
| Armor Stand Animator | 1.1.0 | `OPTIONAL_NICHE` | Gera datapack para armor stands; útil em casos simples, mas Animated Java é mais completo para cenas avançadas |
| Java Item Model Animator | 1.0.0 | `OPTIONAL_NICHE` | Transições entre Java item models via resource/datapack; não substitui animação de entidade |
| Double Sided Cubes | 1.0.2 | `AUDIT_REQUIRED` | Duplica/inverte geometria para double-sided rendering; aumenta geometry budget e pode criar redundância |
| Player Statue Generator | 1.0.0 | `REFERENCE_HELPER` | Gera modelos player-shaped; não é provider de player runtime |
| Mod Utils | 1.7.1 | `LEGACY_IMPORT_HELPER` | Tabula import + VoxelShape; útil para legado/collision |
| CEM Template Loader | 9.2.0 | `REQUIRED_PROFILE` | Base do profile EMF/CEM |
| OptiFine Player Models | 1.5.2 | `PROVIDER_NOT_AUTHORITY` | OptiFine não é o provider do pack |
| Resource Pack Utilities | 1.10.0 | `PREFERRED_RESOURCEPACK` | Utilidades amplas de resource pack |
| Free Rotation | 1.2.1 | `AUDIT_REQUIRED` | Pode usar técnica de output além das limitações vanilla; validar em 1.21.1 |
| GeckoLib Animation Utils (legado) | 4.1.3 | `BLOCKED_LEGACY` | Depreciado; substituído pelo plugin GeckoLib atual |
| GeckoLib Models & Animations | 4.2.5 | `REQUIRED_PROFILE` | Authoring GeckoLib atual para Blockbench 5.x |
| Fabric Modded Entity | 0.2.2 | `LOADER_MISMATCH` | Fabric/Yarn, projeto NeoForge |
| Multi-Layer | 1.0 | `AUDIT_REQUIRED_LEGACY_FORGE` | Exporta formato multi-layer Forge; não assumir equivalência NeoForge 1.21.1 |
| VoxelShape Generators | 0.2.0 | `OPTIONAL_COLLISION` | Geração de VoxelShapes com Mojang mappings/MCP; validar code output |
| VoxelShape Fabric Generator | 1.0.0 | `LOADER_MISMATCH` | Fabric-specific |
| Endimator Animations Exporter | 1.0.0 | `PROVIDER_ABSENT` | Blueprint/Endimator não é provider físico principal confirmado |
| Tint Preview | 1.1.2 | `PREFERRED_JAVA_BLOCK_ITEM` | Preview de tint faces em Java Block/Item |
| Animation to Java Converter | 1.2.0 | `BLOCKED_DEPRECATED` | Depreciado; feature integrada ao Blockbench e plugin limitado a linha 4.x |
| Resourcepack Packager | 1.0.1 | `OPTIONAL_RESOURCEPACK` | Empacotamento; staging próprio continua authority |
| Highlight Mod Shape Generator | — | `PROVIDER_ABSENT` | Provider Highlight não é authority atual |
| BAMO Exporter | 0.5.1 | `PROVIDER_ABSENT` | BAMO não é provider atual |
| Animation to JSON Converter | 1.0.1 | `PREFERRED_AFTER_RUNTIME_PROOF` | Export NeoForge JSON; precisa prova exata no target 1.21.1 |
| AzureLib Animator | 2.1.4 | `REQUIRED_PROFILE` | AzureLib 3.1.11 físico no pack |
| EMF Animation Addon | 1.0.4 | `PREFERRED_PROFILE` | Complementa CEM para Entity Model Features |
| PBR Tools | 1.2.2 | `INCOMPATIBLE_EDITOR` | Catálogo limita a Blockbench 4.11.x; baseline é 5.1.6 |
| Outliner Group Exporter | 1.0.0 | `OPTIONAL_MODULAR_EXPORT` | Export de grupo/cubes como submodel |
| Java Block Sequencer | 1.0.0 | `OPTIONAL_SPECIAL_CASE` | Animation → sequência de block/item models |
| No Java Limits | 1.0.0 | `CONDITIONAL_DISPLAY_ENTITIES` | Modelos grandes para display entities; não usar no profile vanilla genérico |
| SB Worn Display Editor | 4.13.0 | `OPTIONAL_CURRENT_PACK_PROVIDER` | Sophisticated Backpacks físico no pack; validar keys exatas |
| Structure to Model | 1.0.0 | `OPTIONAL_STRUCTURE_REFERENCE` | Converte `.nbt` Java structure em model para referência/workflow |

## Entradas Java-provider-specific extras observadas no catálogo

Também existem exporters/formats para providers/mods específicos que não devem ser adicionados só por estarem disponíveis. A política é:

```text
provider físico ausente
→ não instalar
→ não criar adapter
→ manter apenas no catálogo de referência
```

Se algum desses providers entrar futuramente na modlist, reabrir a auditoria em vez de reutilizar esta classificação automaticamente.

---

# APÊNDICE B — FERRAMENTAS GENÉRICAS DE ALTO VALOR

Estas não precisam ter tag “Minecraft: Java Edition” para serem valiosas no nosso pipeline.

| Extensão | Disposição | Uso principal |
|---|---|---|
| Animation Sliders | `PREFERRED_ANIMATION_ASSIST` | Ajuste fino de keyframes |
| Animated Platforms | `PREFERRED_LOCOMOTION_QA` | Walk/run/vehicle cycle preview |
| Bakery | `OPTIONAL_LOSSY` | Bake de animação complexa para linear |
| Bone View | `PREFERRED_RIG_QA` | Pivôs/hierarquia visual |
| Expand Bone Timeline | `OPTIONAL_ANIMATION_QOL` | Timeline em rigs grandes |
| Batch Group Rename | `OPTIONAL_HIGH_RISK` | Renome em massa com ref-update obrigatório |
| Duplicate Bone Renamer | `OPTIONAL_HIGH_RISK` | Reparar nomes duplicados |
| Reference Models | `PREFERRED_REFERENCE` | GLTF/GLB/project tabs como referência |
| GLTF Importer | `OPTIONAL_REFERENCE_IMPORT` | Import externo em quarantine/reference |
| Export to Blender | `PREFERRED_DCC_HANDOFF` | Epic Fight/Blender workflow |
| MTools | `GENERIC_ONLY/AUDIT_PROFILE` | Mesh tools; não presumir suporte de mesh no provider Minecraft |
| UV Locker | `PREFERRED_UV` | Preservar UV ao editar geometry |
| Shape Generator | `OPTIONAL_MODELING` | Shape generation com profile constraints |
| Repeat It | `OPTIONAL_MODELING` | Repetição controlada |
| Clone Brush | `OPTIONAL_ARTIST_TOOL` | Textura |
| Creative Mode | `OPTIONAL_MODELING` | Ferramentas de criação; não runtime authority |
| Outline Creator | `AUDIT_REQUIRED` | Pode usar scale/geometry tricks; validar runtime |
| Plaster | `PREFERRED_TEXTURE_QA` | Texture bleeding/seams |
| Missing Texture Highlighter | `PREFERRED_TEXTURE_QA` | Faces sem texture |
| Brush Color Randomizer | `ARTIST_ONLY_BY_DEFAULT` | Variação aleatória, MCP exige seed |
| Brush Plus | `OPTIONAL_ARTIST_TOOL` | Textura |
| Smudge Brush | `OPTIONAL_ARTIST_TOOL` | Textura |
| Let There Be Noise | `OPTIONAL_DETERMINISTIC_ONLY` | Noise com seed se automatizado |
| Texture Downscaler | `OPTIONAL_OPTIMIZATION` | Downscale com visual diff |
| Repeating Textures | `OPTIONAL_VIEWPORT` | Preview de wrapping/repeat |
| Texture Filtering | `OPTIONAL_VIEWPORT_QA` | Comparar nearest/linear |
| Baked Ambient Occlusion | `OPTIONAL_ART_DIRECTION` | AO bake quando style permitir |
| Grayscale Preview | `PREFERRED_READABILITY_QA` | Value hierarchy |
| Transparency Fix | `OPTIONAL_VIEWPORT_QA` | Visualização através de transparência |
| Cameras | `PREFERRED_VISUAL_QA` | Capturas padronizadas |
| Preview Scene Customiser | `OPTIONAL_VISUAL_QA` | Cenário de review |
| Scene Recorder | `OPTIONAL_EVIDENCE` | Gravar animation preview |
| Menu Icon Exporter | `OPTIONAL_UI_ASSET` | Ícones/UI |
| Code View | `PREFERRED_DIAGNOSTIC` | JSON/raw format read-only |
| Explorer | `OPTIONAL_WORKFLOW` | Desktop files; não expor livremente ao MCP |
| Backup Viewer | `PREFERRED_RECOVERY` | Recuperação local |
| Workspaces | `OPTIONAL_ORGANIZATION` | Separar projetos/domínios |
| Performance Audit | `DEV_ONLY` | Profiling do editor/plugins |
| Live Dev Reloader | `DEV_ONLY` | Desenvolvimento do Toolkit |
| Structure Importer | `OPTIONAL_STRUCTURE_REFERENCE` | Import structures |
| Asset Browser | `PREFERRED_REFERENCE` | Assets Minecraft para referência |

---

# APÊNDICE C — EXTENSÕES EXTERNAS PROVIDER-MAINTAINED

## Easy Model Entities Exporter

- provider físico: Easy Model Entities 2.3.0;
- source do mod confirma workflow `.bbmodel`;
- exporter existe;
- PR de inclusão no catálogo oficial estava aberta durante esta auditoria;
- desenvolvimento via URL existe, porém não deve ser instalado automaticamente.

**Classificação:** `EXPERIMENTAL_PROVIDER_PLUGIN`.

## CPM Blockbench Plugin

- provider físico: CPM 0.6.27a;
- plugin oficial do próprio projeto CPM;
- beta;
- testado upstream em Blockbench 5.1.4;
- importa/exporta `.cpmproject`;
- upstream alerta sobre animações quebrando em import;
- issues recentes justificam smoke obrigatório.

**Classificação:** `EXPERIMENTAL_PROVIDER_PLUGIN / HUMAN_ONLY` inicialmente.

---

# APÊNDICE D — PIPELINES NÃO-BLOCKBENCH

## Epic Fight

A animação custom do Epic Fight é **Blender-authoritative**.

Ferramentas upstream:

- Epic Fight Player Animation Rig;
- Blender;
- Epic Fight Blender JSON Exporter.

O Blockbench pode preparar referências e handoff, mas não deve assumir authority do formato final.

## Player Animation Library

Pode consumir formatos vindos de Blockbench/GeckoLib/Bedrock, mas é runtime consumer.

Não precisa de plugin Blockbench próprio até prova em contrário.

## Player Animator

Runtime/API separada.

Adapter pendente de auditoria.

---

# APÊNDICE E — REGRA DE COBERTURA FUTURA

Sempre que:

- Blockbench atualizar;
- catálogo de plugins atualizar;
- modlist mudar;
- provider subir de versão;
- plugin mudar de versão;
- novo mod visual entrar no pack;

executar novamente:

```text
physical modlist scan
→ provider delta
→ official plugin catalog delta
→ external provider plugin delta
→ compatibility matrix
→ regression profile selection
```

A meta não é congelar “todos os plugins de 2026”.

A meta é manter **um catálogo vivo, auditável e provider-aware**.

---

# PARTE III — CHECKLIST MESTRE DE CONTINUIDADE

Use esta seção como painel de execução. O estado deve ser revalidado antes de marcar qualquer item.

## Histórico / origem

- [x] PR #479 — skill infrastructure — mergeada no repo RPG histórico
- [x] PR #480 — art direction + Blockbench pipeline — mergeada
- [x] PR #482 — VFX/audio skills — mergeada
- [x] PR #483 — Visual Style Bible + Toolkit — mergeada
- [x] PR #484 — Golden Samples — mergeada
- [x] PR #486 — PR1 Core + Provider/Extension Registry — mergeada
- [x] PR #487 — PR2 Read-only Live Bridge — mergeada no repo RPG histórico
- [x] PR #488 — PR3 Modeling + Rig Mutations — mergeada no repo RPG histórico
- [x] PR #507 — PR4 UV island masks slice — mergeada; cutoff histórico fixado
- [ ] PR #508 — palette sampling — OPEN / TDD RED test-only; migrar/reconciliar, não completar produção no RPG

## Migração Repo Textura

- [x] M0A — remote `Gustavaopere/minecraft-mod-factory` + default branch `main` resolvidos
- [ ] M0B — criar primeiro commit e resolver `BASE_SHA` da Factory
- [ ] M1 — auditar árvore canônica
- [ ] M2 — inventariar arte/tooling histórico
- [ ] M3 — produzir matriz de migração
- [ ] M4 — migrar fundação artística
- [ ] M5 — desacoplar naming RPG → Repo Textura
- [ ] M6 — reconciliar Golden Samples
- [ ] M7 — criar/adotar STATUS canônico

## Implementação pós-migração

- [ ] PR3 — Modeling + Rig Mutations
- [ ] PR4 — UV + Texture
- [ ] PR5 — Generic Animation Core
- [ ] PR6 — GeckoLib Adapter
- [ ] PR7 — AzureLib Adapter
- [ ] PR8 — NeoForge Native Animation Adapter
- [ ] PR9 — Easy Model Entities Adapter
- [ ] PR10 — EMF/CEM Adapter
- [ ] PR11 — Animated Java Adapter
- [ ] PR12 — Player Profiles
- [ ] PR13 — Blender / Epic Fight Handoff
- [ ] PR14 — Unified QA + Export Manifest

## Operação real

- [ ] Blockbench version confirmed
- [ ] Repo Textura Asset Toolkit installed/loaded
- [ ] Base Safe extension preset validated
- [ ] first provider preset validated
- [ ] Golden Sample real smoke
- [ ] structural QA
- [ ] visual QA
- [ ] staging export
- [ ] runtime/in-game QA
- [ ] first production asset end-to-end

---

# PARTE IV — REGRA FINAL PARA EVITAR PERDA DE CONTEXTO

Se outro chat não souber onde continuar, ele **não deve perguntar “o que estávamos fazendo?” antes de verificar as fontes**.

A ordem correta é:

```text
PLANO MESTRE
→ STATUS do domínio Repo Textura na Minecraft Mod Factory
→ GitHub PR/branch da Factory
→ modlist física
→ documentação/Golden Samples
→ primeira lacuna real
→ execução
```

Se o STATUS e o GitHub divergirem:

**GitHub + árvore real vencem para estado de implementação.**

Se modlist e documentação divergirem:

**modlist física vence para presença/versão de provider.**

Se provider/runtime e plugin divergirem:

**provider/runtime vence para formato/comportamento no Minecraft.**

Se estrutural e visual divergirem:

**nenhum PASS estrutural substitui Visual QA.**

Se preview e Minecraft divergirem:

**Minecraft real é o gate final.**


---

# APÊNDICE F — FONTES DA EXPANSÃO V5 / TECH-MOD BENCHMARK

## Oritech

- CurseForge:
  https://www.curseforge.com/minecraft/mc-mods/oritech
- Source:
  https://github.com/Rearth/Oritech

Uso no plano:

- benchmark de máquinas animadas/multiblocos;
- benchmark de pipeline Blockbench + GeckoLib;
- referência de amplitude visual de um tech mod.

Não copiar assets/código por inferência. Qualquer reutilização externa exige auditoria de licença/proveniência específica.

## NeoForge — referência de rendering

- Models 1.21.1:
  https://docs.neoforged.net/docs/1.21.1/resources/client/models/
- Baked Models 1.21.1:
  https://docs.neoforged.net/docs/1.21.1/resources/client/models/bakedmodel/
- Block Entities 1.21.1:
  https://docs.neoforged.net/docs/1.21.1/blockentities/
- BlockEntityRenderer documentation:
  https://docs.neoforged.net/docs/blockentities/ber/

Regra:

APIs/signatures da documentação corrente devem ser reinspecionadas contra a versão física alvo antes de qualquer implementação Java no repositório funcional.
