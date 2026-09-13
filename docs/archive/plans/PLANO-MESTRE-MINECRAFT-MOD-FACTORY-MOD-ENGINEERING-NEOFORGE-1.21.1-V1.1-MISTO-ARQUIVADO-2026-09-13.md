# PLANO MESTRE — MINECRAFT MOD FACTORY / MOD ENGINEERING — V1.1
## Control plane para criação, integração, validação e entrega de mods completos em Minecraft 1.21.1 / NeoForge 21.1.x / Java 21

> **Para agentes que executarem este plano:** cada frente de implementação deve ser convertida em um plano de execução específico com tarefas pequenas, TDD, paths reais e gates verificáveis depois de auditar a árvore do repositório. Não inventar arquivos, APIs, branches, repositórios, providers ou estados.
>
> **Plano irmão obrigatório:** `PLANO-MESTRE-UNIFICADO-MINECRAFT-MOD-FACTORY-REPO-TEXTURA-BLOCKBENCH-ASSET-MCP-V5.1.md`.

**Repositório canônico:** `Gustavaopere/minecraft-mod-factory`  
**Remote Git canônico:** `https://github.com/Gustavaopere/minecraft-mod-factory.git`  
**Estado do remote nesta revisão:** `private`, default branch `main`, repositório vazio, `BASE_SHA=UNRESOLVED_EMPTY_REPOSITORY`.

**Objetivo:** transformar a Minecraft Mod Factory em uma infraestrutura canônica para projetar, criar, integrar, testar e entregar mods completos. O mesmo Git repository abriga dois domínios lógicos: **Mod Engineering / Integration Control Plane** e **Repo Textura / Visual Authority**. A implementação final de cada mod continua sob autoridade do próprio repositório do mod.

**Arquitetura:** `minecraft-mod-factory` funciona como fábrica/control plane comum, catálogo de contratos, templates, scaffolding, validação, compatibilidade, CI, tooling artístico, handoff e automação. Ele não deve virar um “mega-mod” contendo o runtime de todos os projetos. Cada mod permanece um produto isolado, com seu próprio repositório, build, testes, versão e release. O domínio artístico fornece assets/manifests/contratos visuais; o domínio de engenharia coordena runtime scaffolding, integração e QA.

## DECISÃO ARQUITETURAL CANÔNICA — V1.1

A infraestrutura comum deixa de usar `Gustavaopere/neoforge-rpg-skilltree` como repositório central.

Destino canônico:

```text
Gustavaopere/minecraft-mod-factory
```

O repositório RPG passa a ter dois papéis apenas:

1. authority do runtime do mod RPG;
2. origem histórica para migração de tooling/contracts/validators/assets comuns já implementados.

A Factory contém duas authorities lógicas:

```text
minecraft-mod-factory
├── Mod Engineering / Integration Control Plane
└── Repo Textura / Visual & Asset Pipeline
```

Essas authorities compartilham o mesmo Git repository, mas não a mesma responsabilidade. Runtime de mods continua em repositórios próprios.

### Estado histórico de engenharia a preservar

No RPG histórico, antes da migração:

- I1 Foundation: MERGED;
- I2 Physical Modlist Catalog: MERGED;
- I3 Mod Scaffolder: MERGED;
- I4 Engineering Validators: MERGED;
- I5 Test Harness: MERGED;
- I6 structural Asset Handoff contract: MERGED via PR #506;
- I6 real estava bloqueado apenas porque o remote do Repo Textura não existia/resolvia.

Esse blocker foi substituído pela criação da Factory. **Não reimplementar I1–I6 do zero.** Migrar/reconciliar o que já foi comprovado, validar na Factory e então completar o handoff real.

### Cutoff de infraestrutura comum no RPG

Após a decisão V1.1, novas capabilities genéricas de engineering/art tooling devem nascer na Factory. Alterações no RPG devem ser específicas do runtime RPG ou necessárias para preservar/migrar trabalho histórico.

**Tech Stack alvo:**
- Minecraft `1.21.1`;
- NeoForge físico atual: `21.1.248`;
- Java `21`;
- Gradle + MDK NeoForge, preferencialmente ModDevGradle/stack oficial que estiver vigente para o target exato no momento da implementação;
- Git/GitHub;
- JUnit para lógica pura quando aplicável;
- NeoForge GameTest para comportamento in-game;
- datagen e recursos data-driven;
- Repo Textura Asset Pipeline V5 para modelos, texturas, UV, rigs, animações, VFX, GUI visual e manifests;
- adapters específicos para providers/mods somente após auditoria da versão física.

**Snapshot físico atual:** a modlist anexada contém `595` mods top-level. Esse snapshot é referência de presença/versão e deve ser refeito antes de cada integração relevante.

---

# PARTE I — AUTORIDADE, FRONTEIRAS E MODELO DE REPOSITÓRIOS

## 0. PRINCÍPIO CENTRAL

O objetivo final é permitir pedidos como:

> “crie um mod completo”

e decompô-los em authorities lógicas claras:

```text
IDEIA / SPEC DO MOD
        │
        ▼
MINECRAFT MOD FACTORY
Gustavaopere/minecraft-mod-factory
        │
        ├── MOD ENGINEERING
        │   control plane / contracts / scaffolding / CI / validators
        │
        └── REPO TEXTURA
            visual/art authority / Blockbench / assets / animation / VFX
        │
        ▼
REPO DO MOD
runtime authority
        │
        ▼
Minecraft 1.21.1
        │
        ▼
runtime + visual + perf QA
```

Compartilhar o mesmo Git repository não autoriza um domínio a assumir silenciosamente a responsabilidade do outro.

O repositório do mod continua separado por padrão.

---

## 1. RESPONSABILIDADE DO DOMÍNIO MOD ENGINEERING

O domínio Mod Engineering da Minecraft Mod Factory é responsável por:

- padrões de engenharia de mods;
- templates/scaffolding de projetos;
- contratos entre sistemas;
- catálogo de capabilities/providers/dependências;
- roteamento de tarefas para o repo correto;
- especificações e ADRs;
- geradores seguros e determinísticos;
- validators;
- compatibilidade entre mods próprios e mods externos;
- matriz da modlist física;
- contratos de handoff com Repo Textura;
- schemas de manifests;
- test harness;
- GameTest fixtures;
- CI reusable;
- dedicated-server smoke;
- integração multiplayer;
- performance gates;
- release checklist;
- auditoria de dependências e licenças;
- documentação de APIs exatas auditadas;
- templates de PR;
- status de execução;
- regressão cross-mod.

Ele pode gerar ou preparar mudanças para repos de mods, mas o código final deve ficar no repo do mod correspondente. A infraestrutura reutilizável fica na Factory.

---

## 2. RESPONSABILIDADE DO DOMÍNIO REPO TEXTURA

O domínio Repo Textura dentro da Minecraft Mod Factory continua authority para:

- concept art;
- Visual Style Bible;
- modelos;
- `.bbmodel`;
- texturas;
- UV;
- bones;
- pivôs;
- rigs;
- animações;
- VFX;
- SFX anchors/cue sheets quando aplicável;
- GUI art;
- icons;
- cinematic assets;
- Golden Samples visuais;
- visual QA;
- Blockbench tooling;
- provider-specific visual export;
- Blender/Epic Fight visual handoff;
- asset manifests.

O domínio Mod Engineering **consome** esses artefatos por contratos internos/manifestos; não os substitui.

---

## 3. RESPONSABILIDADE DO REPO DO MOD

Cada repo de mod é authority para:

- `mod_id`;
- código Java;
- registro runtime;
- regras de gameplay;
- estado autoritativo;
- BlockEntities;
- entities;
- recipes;
- inventories;
- fluids;
- energy;
- networking;
- menus;
- configs;
- worldgen;
- AI;
- multiblock logic;
- integração de APIs;
- sync client/server;
- serialization;
- migrations;
- performance runtime;
- testes específicos;
- JAR final;
- release.

---

## 4. A MINECRAFT MOD FACTORY NÃO É UM MONOREPO DE RUNTIME POR PADRÃO

Proibido assumir que todos os mods próprios serão módulos Gradle dentro da Factory.

Default:

```text
minecraft-mod-factory/       # infraestrutura comum: engineering + art
mod-rpg/                     # runtime RPG
mod-enshrouded/              # runtime próprio
mod-black-arcana/            # runtime próprio
mod-x/
...
```

A Factory pode conter Golden fixtures/projetos de prova, mas eles não transformam o repositório em authority do runtime de todos os mods.

Um monorepo de runtime só pode ser adotado para um grupo de mods se houver decisão arquitetural explícita e benefício comprovado.

---

## 5. A MINECRAFT MOD FACTORY NÃO DEVE SER DEPENDÊNCIA RUNTIME POR PADRÃO

A Minecraft Mod Factory é tooling/control plane e pipeline artístico.

Se vários mods precisarem compartilhar código runtime, criar uma decisão separada:

- duplicação aceitável;
- módulo shared source;
- biblioteca runtime própria;
- API própria versionada.

Nunca fazer mods dependerem da `minecraft-mod-factory` só porque ela existe.

---

# PARTE II — FONTES DE VERDADE

## 6. ORDEM DE AUTORIDADE PARA ENGENHARIA

Quando houver divergência:

1. build/código/testes do **repo do mod**;
2. JAR físico exato do mod/provider/dependência;
3. modlist física mais recente para presença/versão;
4. source/tag/commit da versão exata do provider;
5. documentação oficial correspondente ao target;
6. Minecraft Mod Factory — domínio Mod Engineering: contracts/ADRs/standards;
7. Minecraft Mod Factory — domínio Repo Textura: assets/manifests/Visual Style Bible;
8. documentação editorial/Notion;
9. posts, vídeos, wikis comunitárias e exemplos externos.

---

## 7. REGRA DE VERSIONAMENTO

Não usar documentação de outra versão por semelhança.

Alvo atual:

```text
Minecraft = 1.21.1
NeoForge = 21.1.248 físico no snapshot atual
Java = 21
```

Toda API de terceiros deve registrar:

```yaml
provider:
  mod_id:
  physical_version:
  source_repository:
  source_ref:
  audited_at:
  loader:
  minecraft_version:
  license:
  confidence:
```

---

## 8. ESTADOS DE EVIDÊNCIA

Usar somente:

- `CONFIRMED`
- `IMPLEMENTED`
- `MERGED`
- `PASS`
- `PENDING`
- `UNRESOLVED`
- `UNAVAILABLE`
- `DEFERRED`
- `REFERENCE_ONLY`
- `INCOMPATIBLE`
- `BLOCKED`
- `SUPERSEDED`

Nunca “pronto” sem gate explícito.

---

# PARTE III — BOOTSTRAP DA MINECRAFT MOD FACTORY

## 9. GATE I0 — REMOTE RESOLVIDO / BOOTSTRAP INICIAL PENDENTE

Remote canônico confirmado:

```text
INTEGRATION_REPO=Gustavaopere/minecraft-mod-factory
REPO_URL=https://github.com/Gustavaopere/minecraft-mod-factory.git
DEFAULT_BRANCH=main
VISIBILITY=private
BASE_SHA=UNRESOLVED_EMPTY_REPOSITORY
HISTORICAL_SOURCE_REPO=Gustavaopere/neoforge-rpg-skilltree
```

O repositório está vazio nesta revisão. Portanto o gate I0 foi dividido:

### I0A — resolução de identidade — CONFIRMED

- repository_full_name resolvido;
- remote resolvido;
- acesso confirmado;
- default branch configurada como `main`.

### I0B — bootstrap físico — PENDING

Antes da primeira migração:

1. criar commit inicial controlado;
2. registrar o primeiro SHA;
3. materializar README/instruções/STATUS/planos no layout escolhido;
4. verificar branches/PRs;
5. somente então criar branches de migração.

O antigo blocker `INTEGRATION_REPO_UNRESOLVED` está `SUPERSEDED`.

Blocker atual:

`FACTORY_EMPTY_REPOSITORY_BOOTSTRAP_PENDING`

---

## 10. ÁRVORE CONCEITUAL

Somente depois de auditar a árvore real, adaptar algo equivalente a:

```text
repo-integracao/
├── README.md
├── AGENTS.md
├── plans/
│   ├── STATUS.md
│   └── ...
├── standards/
│   ├── MOD-ENGINEERING-CONTRACT.md
│   ├── CLIENT-SERVER-CONTRACT.md
│   ├── NETWORKING-CONTRACT.md
│   ├── DATA-PERSISTENCE-CONTRACT.md
│   ├── ASSET-HANDOFF-CONTRACT.md
│   ├── COMPATIBILITY-CONTRACT.md
│   ├── TESTING-CONTRACT.md
│   ├── PERFORMANCE-CONTRACT.md
│   └── RELEASE-CONTRACT.md
├── schemas/
│   ├── mod-spec.schema.json
│   ├── dependency-profile.schema.json
│   ├── asset-handoff.schema.json
│   ├── compatibility-matrix.schema.json
│   └── test-manifest.schema.json
├── templates/
│   ├── neoforge-mod/
│   ├── addon-mod/
│   ├── compatibility-mod/
│   └── test-fixtures/
├── catalog/
│   ├── physical-modlist/
│   ├── providers/
│   ├── capabilities/
│   ├── integrations/
│   └── licenses/
├── tooling/
│   ├── scaffolder/
│   ├── validators/
│   ├── datagen/
│   ├── compatibility/
│   ├── test-harness/
│   └── release/
└── docs/
    ├── architecture/
    ├── sources/
    ├── ADR/
    └── handoffs/
```

Essa árvore é conceitual; a árvore existente vence.

---

# PARTE IV — CONTRATO DE MOD COMPLETO

## 11. MOD SPEC CANÔNICO

Antes de implementar qualquer mod, criar uma especificação com:

```yaml
identity:
  name:
  mod_id:
  repository:
  minecraft: 1.21.1
  loader: neoforge
  java: 21

purpose:
  fantasy:
  player_problem:
  core_loop:
  non_goals:

dependencies:
  required:
  optional:
  incompatible:

systems:
  blocks:
  items:
  machines:
  entities:
  worldgen:
  ui:
  networking:
  progression:
  integrations:

visual:
  repo_textura_package:
  provider_profiles:
  required_assets:

data:
  persistence:
  recipes:
  tags:
  data_maps:
  configs:

testing:
  unit:
  gametest:
  client:
  dedicated_server:
  multiplayer:
  performance:

release:
  versioning:
  distribution:
  license:
```

Campos sem evidência ficam `UNRESOLVED`, não preenchidos por adivinhação.

---

## 12. DEFINIÇÃO DE “MOD COMPLETO”

Um mod só pode ser classificado `COMPLETE` quando os gates aplicáveis tiverem evidência:

- build;
- registries;
- resources/data;
- gameplay;
- persistence;
- networking;
- client/server separation;
- visual handoff;
- asset integration;
- configs;
- compatibility;
- GameTests;
- dedicated server;
- multiplayer;
- performance;
- packaging;
- release metadata.

Nem todo mod usa todos os sistemas. Gates não aplicáveis devem ser marcados `N/A` com justificativa.

---

# PARTE V — FUNDAÇÃO NEOFORGE 1.21.1

## 13. WORKSPACE

Autoridade oficial atual do target exige:

- JDK 21;
- JVM 64-bit;
- IDE com Gradle;
- MDK NeoForge;
- `gradlew build`;
- `runClient`;
- `runServer`;
- dedicated-server test.

O template mantido pelo domínio Mod Engineering deve pinçar a configuração do MDK oficial vigente para `1.21.1`, sem transcrever cegamente exemplos de versões posteriores.

---

## 14. IDENTIDADE DO MOD

O scaffolder deve exigir:

- `mod_id`;
- mod name;
- group/package;
- version;
- authors;
- license;
- description;
- Minecraft range;
- NeoForge range;
- loader range;
- dependencies;
- incompatibilities.

Validar `mod_id` antes de gerar paths.

---

## 15. ESTRUTURA JAVA

Default recomendado:

```text
<base-package>/
├── ModMain.java
├── bootstrap/
├── registry/
├── common/
├── client/
├── network/
├── data/
├── integration/
└── feature/
```

Preferir organização por feature quando o mod crescer:

```text
feature/
├── refinery/
├── power/
├── drone/
└── corruption/
```

Cada feature deve concentrar comportamento, testes e integration points relacionados.

---

## 16. SIDE SEPARATION

Regra:

```text
logical server = gameplay authority
logical client = presentation
physical dedicated server = zero referência a classes client-only
```

Client-only:

- renderers;
- screens;
- key input;
- model layers;
- particles estritamente locais;
- shader/UI glue.

Common/server:

- gameplay;
- inventories;
- recipes;
- BlockEntity state;
- AI;
- world state;
- validation.

Dedicated server é gate obrigatório.

---

## 17. EVENT MODEL

O plano por feature deve identificar:

- mod-bus events;
- game-bus events;
- lifecycle events;
- client events;
- provider events.

Não usar evento global quando chamada direta/serviço local for suficiente.

---

# PARTE VI — REGISTRIES E CONTEÚDO BÁSICO

## 18. REGISTRATION POLICY

Preferir `DeferredRegister`/helpers NeoForge adequados.

Cobrir conforme o mod:

- items;
- blocks;
- block entities;
- menu types;
- entity types;
- particles;
- sounds;
- recipe serializers/types;
- creative tabs;
- custom data components;
- custom registries quando justificado.

Proibido criar instâncias registráveis fora da janela de registro.

---

## 19. ITEM PIPELINE

Para cada item:

```text
spec
→ registration
→ data components
→ interaction
→ model/texture handoff
→ translation
→ tags
→ recipes
→ tests
```

Usar Data Components para estado por `ItemStack` quando a semântica for de item stack.

Não usar NBT ad hoc onde o sistema de componentes do target for apropriado.

---

## 20. BLOCK PIPELINE

Para cada bloco:

```text
spec
→ block registration
→ block item
→ blockstate
→ model
→ loot
→ tags
→ tool/mining semantics
→ redstone/interactions
→ tests
```

Se o bloco armazenar estado complexo:

avaliar BlockEntity.

---

# PARTE VII — BLOCK ENTITIES E MÁQUINAS

## 21. QUANDO USAR BLOCKENTITY

Usar quando o bloco precisar de:

- dados persistentes por posição;
- inventário;
- tank;
- energia;
- processamento;
- owner;
- progress;
- state machine;
- menu;
- renderer dinâmico;
- capability por posição.

Evitar para estado que cabe naturalmente em BlockState.

---

## 22. PERSISTÊNCIA DA BLOCKENTITY

Para BlockEntities próprios:

- NBT próprio é default recomendado pelo NeoForge para persistência;
- Data Attachments são preferíveis para anexar dados a objetos existentes de outros sistemas quando essa for a semântica.

Toda alteração persistente precisa marcar dirty/state changed conforme a API target exigir.

---

## 23. MACHINE CORE CONTRACT

Uma máquina deve separar:

```text
definition
state
storage
processing
IO policy
capability exposure
sync view
visual state
menu
```

Evitar uma `BlockEntity` monolítica com todas as responsabilidades.

---

## 24. MACHINE STATE MACHINE

Estados conceituais:

```text
IDLE
STARTING
RUNNING
PAUSED
BLOCKED
ERROR
SHUTTING_DOWN
```

Só implementar estados necessários.

Transitions devem ser determinísticas e testáveis.

---

## 25. TICK POLICY

Cada máquina deve declarar:

- server tick necessário?;
- frequência;
- custo esperado;
- event-driven alternative;
- inactive behavior;
- chunk unload behavior.

Não executar trabalho caro todo tick sem necessidade.

---

# PARTE VIII — INVENTÁRIOS, FLUIDOS E ENERGIA

## 26. CAPABILITY-FIRST INTEROP

NeoForge 1.21.1 fornece capabilities para:

- `IItemHandler`;
- `IFluidHandler`;
- `IEnergyStorage`.

Usar essas interfaces para interoperabilidade quando forem semanticamente adequadas.

---

## 27. INVENTORY CONTRACT

Declarar:

- slot count;
- slot roles;
- insertion rules;
- extraction rules;
- sided access;
- automation access;
- max stack;
- serialization;
- menu exposure.

Testar automação externa.

---

## 28. FLUID CONTRACT

Declarar:

- tank count;
- capacities;
- accepted fluids/tags;
- fill/drain rules;
- sided access;
- serialization;
- recipe interaction;
- sync;
- visual fill channel para Repo Textura.

---

## 29. ENERGY CONTRACT

Declarar:

- capacity;
- max receive;
- max extract;
- sided policy;
- internal consumption;
- external capability;
- storage serialization;
- sync;
- visual charge channel.

Valores são domínio de balanceamento do mod; o domínio Mod Engineering fornece estrutura e testes, não impõe números globais.

---

## 30. CUSTOM ENERGY NETWORK

Só criar grafo de energia próprio quando `IEnergyStorage` por conexão não for suficiente.

Se necessário:

- node identity;
- edge lifecycle;
- chunk load/unload;
- graph split/merge;
- dirty propagation;
- scheduler;
- throughput semantics;
- cycle handling;
- save/load;
- multiplayer sync;
- perf benchmark.

Não implementar BFS completo a cada tick sem análise.

---

## 31. ITEM/FLUID LOGISTICS NETWORK

Se o mod tiver pipes:

- connection graph;
- endpoint discovery;
- routing;
- filters;
- priority;
- throughput;
- backpressure;
- chunk boundaries;
- invalidation;
- automation compatibility.

Separar visual de fluxo do algoritmo de transporte.

---

# PARTE IX — RECIPES E PROCESSAMENTO

## 32. DATA-DRIVEN FIRST

Recipes devem ser data-driven sempre que possível.

Pipeline:

```text
Recipe JSON/datagen
→ RecipeType
→ RecipeSerializer
→ RecipeInput
→ server-side matching
→ process plan
→ machine execution
```

Recipe logic é server-authoritative.

---

## 33. CUSTOM RECIPE CONTRACT

Declarar:

- inputs;
- catalysts;
- fluids;
- outputs;
- byproducts;
- processing duration;
- machine requirements;
- serializer;
- network representation se necessária;
- JEI/EMI integration;
- conditions.

---

## 34. DATA LOAD CONDITIONS

Usar condições data-driven para conteúdo opcional dependente de outros mods quando possível.

Não fazer `if (ModList...)` espalhado em todo código se uma data condition resolve o caso.

---

# PARTE X — MULTIBLOCOS

## 35. MULTIBLOCK AUTHORITY

Repo Textura entrega:

- visual root;
- part map;
- anchors;
- formed/unformed visuals;
- bounds;
- visual manifest.

Repo do mod entrega:

- validação;
- controller;
- formação;
- desmontagem;
- IO;
- state;
- persistence;
- gameplay.

---

## 36. MULTIBLOCK CONTRACT

Definir:

```yaml
controller:
orientation:
dimensions:
required_parts:
optional_parts:
replaceable_parts:
ports:
formation_trigger:
dissolution_rules:
chunk_behavior:
capability_aggregation:
visual_contract:
```

---

## 37. MULTIBLOCK VALIDATION

Evitar scan integral da estrutura a cada tick.

Preferir:

- validate on placement/removal;
- controller dirty flag;
- local invalidation;
- scheduled recheck;
- cached formed state;
- bounded recovery scan.

---

## 38. CHUNK BOUNDARIES

Definir comportamento explícito quando:

- parte está unloaded;
- controller unloads;
- chunk reloads;
- dimensão fecha;
- servidor reinicia.

Nunca assumir que toda estrutura fica carregada.

---

# PARTE XI — GUI, MENU E INPUT

## 39. MENU = BACKEND DE INTERAÇÃO

Menus não são data holders.

Machine/entity storage continua no data owner.

Menu referencia dados/capabilities.

---

## 40. SCREEN = CLIENT PRESENTATION

Repo Textura fornece:

- background;
- sprites;
- icons;
- gauges;
- layout intent.

Repo do mod implementa:

- Screen;
- widgets;
- user input;
- menu binding;
- tooltip logic;
- client-only rendering.

---

## 41. SERVER VALIDATION

Toda ação que altera gameplay via GUI deve ser validada no servidor.

Nunca confiar em:

- slot index do cliente sem bounds;
- amount arbitrário;
- button ID desconhecido;
- posição distante;
- permission state do cliente.

---

## 42. GUI SYNC

Escolher mecanismo mínimo:

- Slot;
- DataSlot;
- container data;
- custom payload;
- block/entity update;
- event-driven packet.

Não sincronizar a BlockEntity inteira a cada tick.

---

# PARTE XII — NETWORKING

## 43. PROTOCOL CONTRACT

NeoForge 1.21.1 usa payload registration via `RegisterPayloadHandlersEvent`.

Todo mod deve versionar o protocolo quando possuir payloads próprios.

Manifest conceitual:

```yaml
protocol_version: 1
payloads:
  - id:
    direction:
    codec:
    handler_thread:
    validation:
```

---

## 44. NETWORK SECURITY

Serverbound payload:

- validate sender;
- validate dimension;
- validate target existence;
- validate distance;
- validate permission;
- validate state;
- validate bounds;
- reject impossible values;
- schedule work on thread correto.

Client nunca é authority.

---

## 45. NETWORK BUDGET

Registrar:

- packet size;
- frequency;
- recipients;
- burst behavior;
- compression need;
- batching.

Proibido mandar state completo repetidamente se delta/event resolve.

---

# PARTE XIII — DATA STORAGE

## 46. ESCOLHA DO SISTEMA CERTO

Usar:

- BlockEntity NBT → estado do BE próprio;
- Data Components → estado do ItemStack;
- Data Attachments → dados anexados a entidades/chunks/block entities/objetos existentes quando apropriado;
- SavedData → estado de nível/global persistente;
- datapack registries/data maps → dados configuráveis/reloadable;
- config → preferências/servidor/cliente, não savegame.

---

## 47. MIGRAÇÃO DE DADOS

Todo formato persistente que possa sobreviver versões deve ter:

- version field ou estratégia equivalente;
- backward compatibility policy;
- failure behavior;
- migration test;
- corrupted-data behavior.

Não quebrar mundos silenciosamente.

---

# PARTE XIV — ENTITIES, MOBS E BOSSES

## 48. ENTITY PIPELINE

```text
entity spec
→ EntityType
→ attributes
→ spawn restrictions
→ goals/brain
→ data sync
→ persistence
→ combat hooks
→ visual provider contract
→ loot
→ sounds
→ tests
```

---

## 49. ATTRIBUTES

Registrar defaults para LivingEntity.

Não congelar valores sem spec de design.

Integrações de atributos externos devem ser adapters isolados.

---

## 50. SPAWNING

Quando spawn natural existir:

- biome rules;
- spawn placement;
- weight;
- group size;
- conditions;
- dimensions;
- caps.

Testar spawn inválido e spawn em ambiente correto.

---

## 51. AI

Separar:

- sensing;
- targeting;
- navigation;
- decision state;
- attacks;
- cooldowns;
- animation state.

Evitar AI baseada em side effects de renderer.

---

## 52. BOSS STATE

Boss complexo precisa de state machine server-authoritative:

- phases;
- transitions;
- invulnerability windows;
- summons;
- arenas;
- target selection;
- fail/reset;
- persistence quando aplicável.

Repo Textura consome estados/anchors para apresentação.

---

# PARTE XV — COMBATE, PLAYER E PROVIDERS

## 53. COMBAT PROVIDER ROUTER

Antes de implementar combate:

```text
vanilla?
Epic Fight?
Battle Arts?
custom?
provider-specific addon?
```

Nunca implementar duas authorities para o mesmo ataque sem contrato de precedência.

---

## 54. EPIC FIGHT

Se o mod depender de Epic Fight:

- auditar versão física;
- auditar API/source;
- isolar adapter;
- separar animation handoff Blender/Repo Textura;
- GameTest/functional test onde possível;
- in-game combat QA obrigatório.

---

## 55. PLAYER DATA

Escolher Data Attachments ou sistema provider conforme semântica.

Exemplos:

- skill state;
- corruption;
- custom resource;
- cooldown metadata.

Definir clone/death/dimension transfer behavior.

---

# PARTE XVI — WORLDGEN E CONTEÚDO DE MUNDO

## 56. DATA-DRIVEN WORLDGEN

Preferir datapack registries/datagen.

Cobrir conforme necessário:

- configured/placed features;
- ores;
- biomes;
- biome modifiers;
- structures;
- structure sets;
- dimensions;
- dimension types;
- damage types;
- tags.

---

## 57. BIOME MODIFIERS

Para adições compatíveis:

- add features;
- remove features quando realmente necessário;
- add spawns;
- remove spawns.

Evitar hardcode de lista de biomes quando tag é mais interoperável.

---

## 58. STRUCTURES

Estruturas precisam de:

- template/pieces;
- placement;
- biome tags;
- spacing/separation;
- loot;
- processor rules quando aplicável;
- spawn behavior;
- GameTest ou worldgen verification.

Repo Textura pode fornecer estrutura/asset source; runtime worldgen fica no mod.

---

# PARTE XVII — TAGS, DATA MAPS E INTEROPERABILIDADE

## 59. TAGS

Usar tags para membership e compatibilidade.

Preferir convenções `c:` quando NeoForge/Fabric unified tags forem apropriadas.

---

## 60. DATA MAPS

Usar Data Maps quando o comportamento puder ser:

- reloadable;
- registry-object driven;
- extensível por datapacks;
- combinável entre mods.

Evitar hardcode quando Data Map atende melhor.

---

## 61. OPTIONAL INTEGRATIONS

Integração opcional deve ser isolada em:

```text
integration/<provider>/
```

Regras:

- no classloading do provider quando ausente;
- dependency metadata correta;
- conditions/data conditions;
- smoke com provider presente;
- smoke sem provider.

---

# PARTE XVIII — LOOT, ADVANCEMENTS E DATA GENERATION

## 62. LOOT

Cobrir:

- blocks;
- entities;
- chests;
- rewards;
- modifiers quando necessário.

Preferir datagen.

---

## 63. ADVANCEMENTS

Se usados:

- data-driven;
- datagen;
- criteria;
- rewards;
- visibility;
- optional provider conditions.

---

## 64. DATAGEN COMO GATE

Gerar e validar:

- models;
- blockstates;
- recipes;
- tags;
- loot;
- advancements;
- data maps;
- language quando strategy permitir;
- provider-specific data.

CI deve detectar output stale quando generated files forem versionados.

---

# PARTE XIX — CONFIGURAÇÃO

## 65. CONFIG TYPES

Separar:

- CLIENT → apresentação/preferência local;
- COMMON → configuração compartilhada quando semântica permitir;
- SERVER → gameplay/world authority.

Não usar config para dados que pertencem ao save.

---

## 66. CONFIG VALIDATION

Cada valor deve declarar:

- range;
- default;
- comment;
- reload behavior;
- restart requirement.

Não sincronizar client config como gameplay authority.

---

# PARTE XX — SOUND, PARTICLES E PRESENTATION INTEGRATION

## 67. SOUND EVENTS

Repo Textura pode fornecer arquivos/cue sheet.

Repo do mod:

- registra SoundEvent;
- define `sounds.json`;
- escolhe logical side correto para disparo;
- evita double-play;
- usa mono quando attenuation espacial for necessária.

---

## 68. PARTICLES

Repo Textura/VFX fornece specification.

Repo do mod:

- registra ParticleType quando necessário;
- implementa factory/provider client;
- sincroniza somente parâmetros necessários;
- escolhe backend provider-specific.

Gameplay não depende da existência do particle.

---

# PARTE XXI — HANDOFF ENTRE DOMÍNIOS DA MINECRAFT MOD FACTORY

## 69. ASSET HANDOFF MANIFEST

Todo asset runtime relevante deve possuir algo equivalente:

```yaml
asset_id:
source_repo: Gustavaopere/minecraft-mod-factory
source_domain: repo-textura
source_revision:
profile:
runtime_owner:
files:
bones:
anchors:
animations:
visual_inputs:
materials:
render_constraints:
culling_bounds:
performance_notes:
qa:
```

---

## 70. CONTRACT CHECKER

O domínio Mod Engineering deve validar:

- arquivo existe;
- hash/revision;
- provider esperado;
- bone/anchor requerido;
- clip requerido;
- texture path;
- namespace;
- output destination;
- manifest schema.

Não tentar “consertar” asset silenciosamente.

---

## 71. VISUAL INPUT BINDING

Exemplo:

```text
Repo Textura:
progress: float01
active: bool
heat: float01

Repo do mod:
MachineBlockEntity#getProgress()
MachineBlockEntity#isActive()
MachineBlockEntity#getHeatFraction()
```

O binding deve ser explícito.

---

## 72. RUNTIME RENDER ADAPTER

Dependendo do profile:

- baked model;
- BER;
- GeckoLib renderer;
- AzureLib renderer;
- entity renderer;
- Animated Java handoff;
- external provider.

Escolher pelo contract, não pela preferência do agente.

---

# PARTE XXII — MODLIST E COMPATIBILITY CATALOG

## 73. PHYSICAL MODLIST SNAPSHOT

A Minecraft Mod Factory deve importar uma representação normalizada da modlist:

```yaml
snapshot:
  captured_at:
  minecraft:
  loader:
  mods:
    - mod_id:
      version:
      jar:
      top_level:
      nested:
```

Não commitar JARs de terceiros sem política/licença explícita.

---

## 74. PROVIDER CATALOG

Para cada mod que possa ser integrado:

- mod id;
- version;
- loader;
- source;
- docs;
- API surface;
- license;
- runtime health;
- known conflicts;
- optional/required;
- integration tests;
- exact JAR fingerprint se necessário.

---

## 75. API PROOF LEVELS

- `P0 PRESENCE_ONLY`
- `P1 METADATA_VERIFIED`
- `P2 SOURCE/DOC_VERIFIED`
- `P3 COMPILE_PROVEN`
- `P4 RUNTIME_SMOKE`
- `P5 INTEGRATION_TESTED`
- `P6 MULTIPLAYER/PERF_PROVEN`

Não chamar uma integração de suportada em P0.

---

# PARTE XXIII — ADAPTERS PRIORITÁRIOS DO MODPACK

## 76. CREATE FAMILY

Quando necessário:

- Create 6.0.10 físico;
- exact addon compatibility;
- kinetic/contraption boundaries;
- item/fluid interfaces;
- ponder integration;
- visual handoff;
- Flywheel/render interaction somente após API audit.

---

## 77. MAGIC PROVIDERS

Adapters independentes para providers realmente usados, por exemplo:

- Ars Nouveau;
- Iron's Spells 'n Spellbooks;
- outros presentes na modlist.

Cada adapter deve definir:

- gameplay authority;
- spell registration/data;
- attributes;
- mana/resource;
- animation hooks;
- VFX handoff;
- client/server boundary;
- tests.

Não criar “MagicAdapter” universal fictício.

---

## 78. COMBAT PROVIDERS

Epic Fight/Battle Arts e addons:

- version proof;
- event hooks;
- capability/state ownership;
- animation ownership;
- damage ownership;
- conflict policy.

---

## 79. COLONY/STRUCTURE PROVIDERS

MineColonies/Domum Ornamentum ou equivalentes:

- structure ownership;
- block substitution;
- recipes;
- build placement;
- compatibility rules;
- resource paths;
- visual asset boundaries.

---

## 80. STORAGE/LOGISTICS PROVIDERS

Tom's, Sophisticated, Create logistics etc.:

- capability compatibility;
- inventory semantics;
- automation;
- menu behavior;
- item/fluid/energy interop;
- no dupes.

---

# PARTE XXIV — TESTING STRATEGY

## 81. TEST PYRAMID

```text
pure unit tests
↑
codec/serialization tests
↑
registry/datagen validation
↑
GameTests
↑
client smoke
↑
dedicated server smoke
↑
multiplayer integration
↑
full modpack integration
↑
performance soak
```

---

## 82. PURE UNIT TESTS

Usar para:

- algorithms;
- state machines;
- routing;
- graph operations;
- recipe math;
- validation;
- codecs where independent.

Não bootar Minecraft para lógica que pode ser testada em Java puro.

---

## 83. SERIALIZATION TESTS

Round-trip:

- NBT;
- codecs;
- stream codecs;
- data components;
- SavedData;
- attachments;
- custom recipe serializers.

Cobrir malformed/old version.

---

## 84. GAMETEST

NeoForge GameTests para:

- block interaction;
- machine processing;
- inventory automation;
- fluid transfer;
- energy transfer;
- multiblock formation;
- spawn behavior;
- redstone;
- world interactions;
- persistence/reload patterns quando test harness permitir.

---

## 85. CLIENT SMOKE

Verificar:

- resources load;
- model;
- screen;
- renderer;
- particle;
- keybind;
- no missing texture;
- no render exception.

---

## 86. DEDICATED SERVER SMOKE

Obrigatório:

- mod loads;
- no client classloading;
- registries valid;
- datapacks load;
- GameTests;
- no renderer dependency;
- no mixin-side crash.

---

## 87. MULTIPLAYER

Cobrir:

- join;
- initial sync;
- dimension change;
- menu interaction;
- machine concurrent use;
- packet validation;
- reconnect;
- respawn/clone;
- tracking start/stop.

---

## 88. FULL MODPACK TEST

Depois do standalone:

- iniciar com modlist real;
- verificar conflicts;
- logs;
- mixins;
- tags;
- recipes;
- registries;
- providers;
- rendering;
- performance.

Stand-alone PASS não equivale a modpack PASS.

---

# PARTE XXV — PERFORMANCE

## 89. PERFORMANCE BUDGET

Cada sistema registra:

- tick time;
- allocations;
- scans;
- graph operations;
- packet rate;
- save size;
- chunk interactions;
- entity count;
- render cost;
- particle count.

---

## 90. MACHINE SCALE TEST

Testar:

- 1 máquina;
- 16;
- 64;
- 256 quando plausível;
- rede conectada;
- rede fragmentada;
- chunk border;
- active/inactive mix.

Budget real deve vir de benchmark.

---

## 91. ENTITY SCALE TEST

Testar contagens realistas e stress:

- AI;
- pathfinding;
- sync;
- animations;
- particles;
- despawn.

---

## 92. PROFILING

Usar profiling suportado pelo ambiente:

- Java Flight Recorder quando adequado;
- Spark/mod profiling quando presente e permitido;
- tick metrics;
- packet metrics;
- render profiling.

Registrar evidência, não sensação.

---

# PARTE XXVI — RELIABILITY E FAIL-CLOSED

## 93. FAIL-CLOSED

Bloquear quando:

- unknown provider;
- wrong version;
- missing required dependency;
- schema invalid;
- asset contract incompatible;
- protocol mismatch;
- unsafe serverbound packet;
- missing migration;
- corrupt critical state;
- integration P-level insuficiente para release.

---

## 94. FAIL-SOFT

Degradar quando:

- optional integration ausente;
- cosmetic asset ausente com fallback aprovado;
- client-only VFX backend ausente;
- optional data pack integration ausente.

Nunca degradar gameplay crítico sem declarar.

---

# PARTE XXVII — SECURITY E SUPPLY CHAIN

## 95. DEPENDENCIES

Para cada dependência:

- source/repository;
- version;
- license;
- loader;
- MC version;
- transitive risk;
- optionality;
- repository source.

Não adicionar repositório Maven global sem filtro quando puder ser restrito.

---

## 96. CODE EXECUTION

Tooling da Minecraft Mod Factory não deve aceitar:

- arbitrary shell de origem remota;
- arbitrary eval;
- plugin download automático;
- execução de código de terceiros não auditado.

Geradores operam por templates/schemas allowlisted.

---

## 97. PROVENANCE

Assets, code snippets, templates e adapters externos devem registrar:

- origem;
- licença;
- ref;
- modificações;
- permissão de redistribuição.

---

# PARTE XXVIII — CI

## 98. GATES MÍNIMOS POR MOD

```text
format/lint
compile
unit tests
datagen validation
resource validation
GameTests
build
JAR inspection
dedicated server smoke
```

Client smoke e full-pack podem ser jobs separados.

---

## 99. REUSABLE CI

A Minecraft Mod Factory pode hospedar templates/reusable workflows, desde que:

- versão pinada;
- inputs explícitos;
- não force comportamento incompatível em todos os mods;
- cada mod possa testar atualização antes de adotar.

---

## 100. NO FAKE GREEN

Não marcar PASS quando:

- workflow foi skipped;
- dependency host falhou antes do teste;
- test não executou;
- artifact não foi produzido;
- full-pack gate não iniciou.

Usar `BLOCKED_EXTERNAL` quando a evidência não foi obtida.

---

# PARTE XXIX — RELEASE ENGINEERING

## 101. VERSIONING

Definir por mod:

- SemVer ou política equivalente;
- MC/loader compatibility;
- breaking data migrations;
- protocol changes;
- asset manifest version.

---

## 102. BUILD ARTIFACT

Antes do release:

- clean build;
- expected JAR name;
- metadata;
- license;
- dependencies;
- no dev-only assets;
- no test-only code inesperado;
- no Blockbench tooling empacotado;
- dedicated server proof.

---

## 103. CHANGELOG

Gerar de commits/PRs, mas revisar manualmente.

Separar:

- features;
- fixes;
- compatibility;
- breaking;
- migrations;
- known issues.

---

# PARTE XXX — MOD SCAFFOLDER

## 104. OBJETIVO

Criar ferramenta que gera um novo repo de mod com:

- MDK correto;
- metadata;
- package;
- registries vazios mínimos;
- common/client split;
- test setup;
- CI;
- license;
- README;
- STATUS;
- integration manifest;
- Repo Textura handoff pointer.

---

## 105. INPUT DO SCAFFOLDER

```yaml
name:
mod_id:
group:
repository:
license:
minecraft: 1.21.1
neoforge:
java: 21
features:
  blocks:
  items:
  block_entities:
  entities:
  networking:
  datagen:
```

Não gerar sistemas não selecionados.

---

## 106. GOLDEN SCAFFOLD

Manter um projeto Golden mínimo:

- compila;
- runClient;
- runServer;
- GameTest server;
- datagen;
- dedicated server;
- CI.

Toda mudança no template precisa regenerar e testar Golden.

---

# PARTE XXXI — GERAÇÃO DE FEATURES

## 107. FEATURE GENERATOR POLICY

Pode gerar skeleton para:

- block;
- item;
- BlockEntity;
- menu/screen pair;
- entity;
- recipe type;
- network payload;
- config;
- integration adapter.

Mas deve:

- usar AST/template determinístico;
- gerar teste;
- atualizar registry;
- atualizar datagen;
- não sobrescrever arquivo modificado sem diff/confirmation.

---

# PARTE XXXII — WORKFLOW AGÊNTICO

## 108. PEDIDO “CRIE UM MOD”

Fluxo:

```text
1. resolver mod spec
2. decidir/confirmar repo do mod
3. auditar modlist/providers
4. criar arquitetura
5. abrir trabalho no Repo Textura para assets necessários
6. implementar vertical slice mínima
7. testar
8. integrar asset
9. runtime QA
10. repetir por feature
11. full-pack QA
12. release
```

---

## 109. VERTICAL SLICE FIRST

Primeira entrega de um mod complexo deve provar uma fatia completa.

Exemplo tech:

```text
1 item componente
+ 1 bloco máquina
+ BlockEntity
+ inventory
+ 1 recipe
+ processing
+ energy
+ menu/screen
+ asset Repo Textura
+ animation state
+ GameTest
+ dedicated server
```

Depois generalizar.

---

## 110. NÃO IMPLEMENTAR 40 SISTEMAS ANTES DO PRIMEIRO RUNTIME PROOF

Proibido:

```text
registrar 80 blocos
+ 200 recipes
+ 12 networks
+ 6 GUIs
```

antes de uma fatia end-to-end estar comprovada.

---

# PARTE XXXIII — TECH MOD “ORITECH-CLASS”

## 111. CAPABILITY TARGET

Para alegar capacidade funcional semelhante em complexidade a um grande tech mod, o framework deve provar, conforme o projeto exigir:

- animated machine runtime binding;
- item storage;
- fluid storage;
- energy storage;
- custom recipes;
- multiblock formation;
- pipe/logistics;
- machine GUI;
- network sync;
- drones/entities;
- beam/laser gameplay;
- world resources;
- upgrades;
- automation interoperability;
- large-base performance;
- dedicated server;
- multiplayer.

Isso é benchmark de capacidade, não cópia de Oritech.

---

## 112. TECH MACHINE VERTICAL SLICE

Gate mínimo:

1. registered machine block;
2. BlockEntity;
3. saved state;
4. item input/output;
5. energy capability;
6. recipe;
7. progress state;
8. server tick;
9. menu;
10. screen;
11. network/state sync;
12. Repo Textura animated asset;
13. visual input binding;
14. sound;
15. particle/VFX optional;
16. GameTest;
17. dedicated-server smoke;
18. modpack runtime smoke.

---

## 113. MULTIBLOCK VERTICAL SLICE

Gate:

- controller;
- parts;
- orientation;
- formation;
- invalidation;
- unload/reload;
- IO capability;
- visual formed state;
- asset manifest;
- GameTest;
- persistence;
- multiplayer.

---

## 114. LOGISTICS VERTICAL SLICE

Gate:

- node;
- connection;
- endpoint;
- routing;
- transfer;
- filter;
- invalidation;
- chunk boundary;
- perf;
- visualization;
- integration test with at least one external capability provider.

---

# PARTE XXXIV — MOD CLASSES SUPORTADAS

## 115. CONTENT MOD

- blocks/items;
- recipes;
- loot;
- tags;
- worldgen;
- simple interactions.

## 116. TECH MOD

- machines;
- energy;
- fluids;
- logistics;
- multiblock;
- GUI;
- entities;
- automation.

## 117. MAGIC MOD

- spell registry/provider;
- resources;
- targeting;
- cooldown;
- effects;
- VFX;
- animation;
- networking;
- progression.

## 118. RPG MOD

- attributes;
- stats;
- progression;
- perks;
- combat;
- persistence;
- UI;
- multiplayer sync.

## 119. WORLDGEN MOD

- biomes;
- features;
- structures;
- dimensions;
- spawns;
- loot.

## 120. INTEGRATION/ADDON MOD

- no duplicated authority;
- adapter-only;
- optional dependencies;
- provider present/absent tests;
- conflict policy.

---

# PARTE XXXV — STATUS E CONTINUIDADE

## 121. STATUS CANÔNICO

A Minecraft Mod Factory deve manter um STATUS canônico para o domínio Mod Engineering:

```text
CURRENT_PHASE
CURRENT_PLAN
CURRENT_BRANCH
CURRENT_PR
BASE_SHA
HEAD_SHA
LAST_COMPLETED
NEXT_ACTION
BLOCKERS
TARGET_MOD_REPO
REPO_TEXTURA_HANDOFF
LATEST_MODLIST
CI_STATE
MANUAL_ACTION_REQUIRED
```

---

## 122. RETOMADA POR OUTRO CHAT

Ao receber “PROSSIGA”:

1. ler este plano;
2. ler STATUS;
3. consultar GitHub;
4. consultar target mod repo;
5. conferir modlist;
6. conferir Repo Textura handoff;
7. identificar primeira lacuna;
8. declarar:
   - última etapa confirmada;
   - etapa atual;
   - repo;
   - branch/PR;
9. executar;
10. validar;
11. atualizar STATUS.

---

# PARTE XXXVI — ESTRATÉGIA DE PRs DO DOMÍNIO MOD ENGINEERING

## 123. PR I1 — FOUNDATION

Entregar:

- authority docs;
- schemas base;
- STATUS;
- source registry;
- mod-spec contract;
- repo routing.

Gate:

- schema tests;
- doc validator.

---

## 124. PR I2 — PHYSICAL MODLIST CATALOG

Entregar:

- parser/importer;
- normalized snapshot;
- provider identity;
- version drift;
- nested JAR distinction;
- tests.

---

## 125. PR I3 — MOD SCAFFOLDER

Entregar:

- template NeoForge 1.21.1;
- mod metadata;
- common/client split;
- test scaffold;
- CI;
- Golden generated project.

---

## 126. PR I4 — ENGINEERING VALIDATORS

- package;
- mod id;
- dependencies;
- resource paths;
- side boundaries;
- assets manifest;
- datagen drift;
- JAR inspection.

---

## 127. PR I5 — TEST HARNESS

- unit;
- GameTest;
- server smoke;
- artifact collection;
- standard reports.

---

## 128. PR I6 — REPO TEXTURA HANDOFF

- asset schema;
- manifest validator;
- source revision;
- provider binding;
- visual inputs;
- QA handoff.

---

## 129. PR I7 — PROVIDER CATALOG

- source metadata;
- API proof levels;
- license;
- compatibility;
- physical-version mapping.

---

## 130. PR I8 — FEATURE GENERATOR CORE

- block/item/BE/menu/network/recipe skeletons;
- deterministic diff;
- no overwrite;
- tests.

---

## 131. PR I9 — MACHINE FOUNDATION REFERENCE

Reference implementation in a dedicated Golden fixture, not forced into every mod:

- inventory;
- energy;
- recipe;
- progress;
- persistence;
- sync;
- menu;
- GameTest.

---

## 132. PR I10 — MULTIBLOCK REFERENCE

Golden:

- controller;
- parts;
- rotation;
- invalidation;
- chunk behavior;
- persistence;
- tests.

---

## 133. PR I11 — LOGISTICS REFERENCE

Golden:

- graph;
- transfer;
- invalidation;
- perf;
- tests.

---

## 134. PR I12 — INTEGRATION ADAPTER FRAMEWORK

- optional provider isolation;
- classloading safety;
- condition routing;
- provider present/absent tests.

---

## 135. PR I13 — RELEASE TOOLING

- version;
- changelog;
- artifact validation;
- release manifest;
- provenance.

---

## 136. PR I14 — FULL END-TO-END GOLDEN MOD

Criar um Golden mod pequeno, mas completo, que prove:

```text
Minecraft Mod Factory — Mod Engineering
+ domínio Repo Textura handoff
+ target mod build
+ machine
+ GUI
+ networking
+ persistence
+ GameTest
+ dedicated server
+ visual runtime
```

Só depois alegar “pipeline completo”.

---

# PARTE XXXVII — ORDEM DE EXECUÇÃO

## 137. ROADMAP CANÔNICO V1.1

A criação da Factory introduz uma fase de migração antes de retomar o roadmap funcional.

```text
F0 — bootstrap inicial de minecraft-mod-factory
↓
F1 — migrar/reconciliar planos, STATUS e authorities
↓
F2 — migrar/reconciliar I1–I5 já comprovados no RPG histórico
↓
F3 — migrar/reconciliar contrato estrutural I6 + domínio artístico necessário
↓
F4 — executar o handoff real I6 dentro da Factory
↓
I7 provider catalog
↓
I8 feature generator
↓
I9 machine reference
↓
I10 multiblock reference
↓
I11 logistics reference
↓
I12 adapter framework
↓
I13 release tooling
↓
I14 full Golden mod
↓
production mods
```

Regras:

- I1–I5 não voltam a `PENDING` conceitualmente; são milestones históricas a migrar e revalidar;
- I6 estrutural também não deve ser reimplementado do zero;
- I7 permanece bloqueado até a migração e o handoff real I6;
- a frente artística deve ser migrada no mesmo programa de transição, preservando seu próprio roadmap V5.1.

---

# PARTE XXXVIII — CONCORRÊNCIA COM O PLANO ARTÍSTICO V5.1

## 138. O QUE PODE ANDAR EM PARALELO

O domínio Mod Engineering da Factory pode avançar em:

- contracts;
- mod spec;
- scaffolder;
- modlist catalog;
- CI;
- test harness;
- provider catalog;

enquanto o domínio Repo Textura da mesma Factory termina:

- Live Bridge;
- mutations;
- UV;
- texture;
- animation;
- provider adapters.

---

## 139. O QUE EXIGE HANDOFF V5

Esperar capability real para:

- automatic asset generation;
- guaranteed `.bbmodel` mutations;
- automatic animation authoring;
- provider-specific visual export;
- Golden visual runtime integration.

O domínio Mod Engineering pode preparar schemas antes, mas não declarar PASS de handoff sem a capability artística V5.1 correspondente implementada e validada.

---

# PARTE XXXIX — ESTADO HISTÓRICO RELEVANTE

## 140. FRONTIER HISTÓRICA E MIGRAÇÃO

O snapshot original deste plano ficou para trás.

Estado comprovado antes da criação da Factory:

- I1 Foundation — `MERGED`;
- I2 Physical Modlist Catalog — `MERGED`;
- I3 Mod Scaffolder — `MERGED`;
- I4 Engineering Validators — `MERGED`;
- I5 Test Harness — `MERGED`;
- I6 structural Repo Textura Handoff — `MERGED` via PR #506;
- PR artística #487 — Read-only Live Bridge — `MERGED`;
- PR artística #488 — Modeling + Rig Mutations — `MERGED`;
- PR artística #507 — UV island masks — `MERGED`;
- PR artística #508 — `OPEN / TDD RED test-only` no cutoff;
- `neoforge-rpg-skilltree/main` após #507: `c4b093724228e408d91820d0bfa03bef9d3eb3bf`.

O blocker antigo do I6 era a ausência de um remote artístico real. A criação de `Gustavaopere/minecraft-mod-factory` resolve a identidade do destino, mas o I6 real continua `PENDING` até a infraestrutura/art authority ser migrada e um handoff real ser validado.

Não iniciar I7 antes disso.

---

# PARTE XL — PROTOCOLO MANUAL COM O USUÁRIO

## 141. UMA ETAPA MANUAL POR VEZ

Quando o usuário precisar:

- instalar JDK;
- abrir IDE;
- importar Gradle;
- instalar Blockbench plugin;
- copiar arquivo;
- iniciar Minecraft;
- executar comando;

responder com uma única etapa verificável.

Formato:

> Faça somente esta etapa e me mande o resultado.

Não enviar todo o tutorial quando a execução depende de resultado intermediário.

---

# PARTE XLI — SOURCE REVIEW / LICENÇAS

## 142. EXTERNAL SOURCE POLICY

Antes de copiar/adaptar:

- source;
- tag/commit;
- license;
- file;
- reason;
- changes.

Se licença não permitir ou estiver incerta:

`REFERENCE_ONLY`

---

# PARTE XLII — DEFINIÇÃO FINAL DE PRONTO

## 143. PIPELINE COMPLETO

Só afirmar que a infraestrutura consegue “fazer mods completos” quando existir evidência de:

```text
mod spec
+ scaffolder
+ registries
+ data/resources
+ gameplay architecture
+ persistence
+ networking
+ GUI
+ capabilities
+ custom recipes
+ entity/worldgen paths
+ Repo Textura handoff
+ provider adapters
+ unit tests
+ GameTests
+ client smoke
+ dedicated server
+ multiplayer
+ full modpack
+ performance
+ release artifact
```

---

## 144. MOD COMPLETO

Um mod específico só está completo quando:

- requirements aceitos;
- code merged;
- assets integrated;
- tests green;
- dedicated server green;
- multiplayer green quando aplicável;
- full modpack green;
- performance dentro do budget;
- migrations verificadas;
- release artifact validado;
- known issues registrados.

---

# PARTE XLIII — PRIMEIRO MOD GOLDEN RECOMENDADO

## 145. GOLDEN MOD DE INTEGRAÇÃO

Não usar um projeto enorme como primeiro teste.

Criar um Golden mod próprio com:

- 1 item;
- 1 material;
- 1 machine block;
- 1 BlockEntity;
- 2 slots;
- energy;
- 1 custom processing recipe;
- 1 menu;
- 1 screen;
- 1 network payload apenas se necessário;
- 1 animated machine asset vindo do Repo Textura;
- 1 progress visual;
- 1 sound;
- 1 particle;
- 1 GameTest;
- dedicated server;
- full-pack smoke.

Depois adicionar:

- multiblock;
- pipe;
- drone.

Esse Golden mod prova a infraestrutura sem acoplar o framework ao design de um mod real.

---

# PARTE XLIV — FONTES TÉCNICAS AUDITADAS PARA O TARGET

## 146. NEOFORGE 1.21.1

Documentação oficial consultada:

- Getting Started:
  https://docs.neoforged.net/docs/1.21.1/gettingstarted/
- Mod Files:
  https://docs.neoforged.net/docs/1.21.1/gettingstarted/modfiles/
- Structuring:
  https://docs.neoforged.net/docs/1.21.1/gettingstarted/structuring/
- Sides:
  https://docs.neoforged.net/docs/1.21.1/concepts/sides/
- Blocks:
  https://docs.neoforged.net/docs/1.21.1/blocks/
- Items:
  https://docs.neoforged.net/docs/1.21.1/items/
- Block Entities:
  https://docs.neoforged.net/docs/1.21.1/blockentities/
- Capabilities:
  https://docs.neoforged.net/docs/1.21.1/inventories/capabilities/
- Networking:
  https://docs.neoforged.net/docs/1.21.1/networking/
- Recipes:
  https://docs.neoforged.net/docs/1.21.1/resources/server/recipes/
- Tags:
  https://docs.neoforged.net/docs/1.21.1/resources/server/tags/
- Data Maps:
  https://docs.neoforged.net/docs/1.21.1/resources/server/datamaps/
- Saved Data:
  https://docs.neoforged.net/docs/1.21.1/datastorage/saveddata/
- Menus:
  https://docs.neoforged.net/docs/1.21.1/gui/menus/
- Screens:
  https://docs.neoforged.net/docs/1.21.1/gui/screens/
- Config:
  https://docs.neoforged.net/docs/1.21.1/misc/config/
- Game Tests:
  https://docs.neoforged.net/docs/1.21.1/misc/gametest/
- Biome Modifiers:
  https://docs.neoforged.net/docs/1.21.1/worldgen/biomemodifier/
- Particles:
  https://docs.neoforged.net/docs/1.21.1/resources/client/particles/
- Sounds:
  https://docs.neoforged.net/docs/1.21.1/resources/client/sounds/

Repetir a auditoria antes de implementar API que possa ter mudado.

---

# PARTE XLV — CHECKLIST MESTRE

## 147. MINECRAFT MOD FACTORY — MOD ENGINEERING

- [x] I0A — remote `Gustavaopere/minecraft-mod-factory` e default branch `main` resolvidos
- [ ] I0B — primeiro commit / `BASE_SHA` da Factory
- [ ] F1 — migrar/reconciliar planos + STATUS + authorities
- [ ] F2 — migrar/revalidar I1–I5 históricos
- [ ] F3 — migrar/revalidar I6 estrutural + domínio artístico
- [ ] I1 — foundation
- [ ] I2 — physical modlist catalog
- [ ] I3 — mod scaffolder
- [ ] I4 — engineering validators
- [ ] I5 — test harness
- [ ] I6 — Repo Textura handoff
- [ ] I7 — provider catalog
- [ ] I8 — feature generator
- [ ] I9 — machine Golden
- [ ] I10 — multiblock Golden
- [ ] I11 — logistics Golden
- [ ] I12 — adapter framework
- [ ] I13 — release tooling
- [ ] I14 — full end-to-end Golden mod

## 148. CAPABILITIES FUNCIONAIS

- [ ] blocks/items
- [ ] BlockEntities
- [ ] inventories
- [ ] fluids
- [ ] energy
- [ ] recipes
- [ ] menus/screens
- [ ] networking
- [ ] persistence
- [ ] data components
- [ ] attachments
- [ ] SavedData
- [ ] tags
- [ ] data maps
- [ ] configs
- [ ] entities
- [ ] AI
- [ ] worldgen
- [ ] multiblocks
- [ ] logistics
- [ ] provider integrations
- [ ] sounds
- [ ] particles
- [ ] Repo Textura runtime binding

## 149. QA

- [ ] unit
- [ ] serialization
- [ ] datagen
- [ ] GameTest
- [ ] client
- [ ] dedicated server
- [ ] multiplayer
- [ ] full modpack
- [ ] performance
- [ ] migration
- [ ] release artifact

---

# PARTE XLVI — REGRA FINAL

Quando um chat futuro receber a tarefa “criar um mod”, ele deve decidir primeiro:

```text
é arte, modelo, textura, animação, VFX ou Blockbench?
→ domínio Repo Textura da minecraft-mod-factory

é contrato, scaffolding, compatibilidade, CI, teste, catálogo ou automação comum?
→ domínio Mod Engineering da minecraft-mod-factory

é gameplay/runtime do mod?
→ repositório próprio do mod, coordenado pela Factory
```

A Minecraft Mod Factory existe para fazer essas frentes cooperarem sem duplicar authority.

A meta não é “gerar Java”.

A meta é possuir um pipeline verificável capaz de transformar uma especificação em:

```text
assets corretos
+ código correto
+ integração correta
+ testes corretos
+ runtime correto
+ release reproduzível
```

para Minecraft 1.21.1 / NeoForge.

`Gustavaopere/neoforge-rpg-skilltree` não volta a ser o repositório da infraestrutura comum: ele permanece authority do runtime RPG e origem histórica da migração.
