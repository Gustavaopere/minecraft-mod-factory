# PLANO MESTRE — MINECRAFT MOD FACTORY / MOD ENGINEERING — V1.1
## Edição reorganizada: engenharia/runtime somente

> **Reorganização documental de 2026-09-13.** O V1.1 original misturava requisitos de runtime com especificações de apresentação. O original integral, sem perda de conteúdo, foi preservado em `docs/archive/plans/PLANO-MESTRE-MINECRAFT-MOD-FACTORY-MOD-ENGINEERING-NEOFORGE-1.21.1-V1.1-MISTO-ARQUIVADO-2026-09-13.md`.
>
> Toda especificação de UI/HUD visual, textura, material, modelo, UV, rig, animação, VFX, partículas, áudio/SFX, ícones, cinematics e QA visual/sonoro pertence agora a `plans/textura/`. Este plano mantém apenas as fronteiras técnicas necessárias para o runtime consumir esses artefatos.

**Repositório canônico:** `Gustavaopere/minecraft-mod-factory`  
**Minecraft:** `1.21.1`  
**NeoForge físico do snapshot corrente:** `21.1.248`  
**Java:** `21`  
**Authority de planejamento artístico:** `plans/textura/`  
**Authority de runtime de cada mod:** repositório do próprio mod.

---

# 1. OBJETIVO E ESCOPO

O domínio Mod Engineering é o control plane técnico para criação, integração, validação e entrega de mods. Ele é responsável por arquitetura, scaffolding, contratos, schemas, provider catalog, integração, validação, test harness, CI, performance e release engineering.

Ele **não** é authority de direção de arte nem de assets.

Pertencem a Engineering:

- arquitetura Java/NeoForge;
- registries e lifecycle;
- estado autoritativo e persistência;
- BlockEntities, entities, AI e worldgen;
- inventários, fluidos, energia e capabilities;
- recipes e processamento;
- multiblock logic;
- networking e segurança;
- menus e validação de ações;
- sincronização necessária para telas/HUD/renderers;
- integração de providers;
- data generation;
- configs de gameplay/servidor;
- testes, GameTests, dedicated-server smoke e multiplayer;
- performance, CI e release;
- contrato de handoff com `plans/textura/`.

Não pertencem a Engineering como especificação artística:

- layout visual de UI/HUD;
- sprites, ícones, fontes e decoração de telas;
- texturas e materiais;
- modelos e `.bbmodel`;
- UV;
- bones, pivôs e rigs;
- clips e curvas de animação;
- VFX e aparência de partículas;
- desenho de beams/lasers;
- áudio, SFX e cue sheets;
- concept art e Visual Style Bible;
- cinematics;
- Golden Samples de apresentação;
- QA visual/sonoro.

Esses itens são canônicos em `plans/textura/README.md` e no plano V5.1 dentro dessa subpasta.

---

# 2. ORDEM DE AUTORIDADE

Quando houver divergência técnica:

1. código/build/testes do repo do mod;
2. JAR físico exato do provider/dependência;
3. modlist física mais recente para presença e versão;
4. source/tag/commit da versão exata;
5. documentação oficial compatível com Minecraft/loader alvo;
6. contracts/standards do Mod Engineering;
7. contratos de handoff de `plans/textura/` para apresentação;
8. documentação editorial/Notion;
9. fontes comunitárias.

Não inferir API por similaridade entre versões.

Estados de evidência permitidos: `CONFIRMED`, `IMPLEMENTED`, `MERGED`, `PASS`, `PENDING`, `UNRESOLVED`, `UNAVAILABLE`, `DEFERRED`, `REFERENCE_ONLY`, `INCOMPATIBLE`, `BLOCKED`, `SUPERSEDED`.

---

# 3. CONTRATO DE MOD

Antes de implementação, cada mod deve declarar ao menos:

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
  ui_runtime:
  networking:
  progression:
  integrations:

presentation_handoff:
  package:
  required_visual_states:
  required_assets:
  required_audio_cues:

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
```

`presentation_handoff` declara somente o que o runtime precisa expor/consumir. A solução estética é definida em `plans/textura/`.

---

# 4. CLIENTE, SERVIDOR E ESTADO

Servidor permanece authority de gameplay.

Cliente pode possuir:

- input local;
- cache de apresentação;
- screen/HUD renderer;
- renderer de entidade/bloco;
- factories de partículas;
- reprodução de áudio;
- interpolação exclusivamente visual.

Cliente não decide:

- custo;
- dano;
- cooldown;
- sucesso de receita;
- unlock;
- ownership;
- consumo/produção de recurso;
- formação válida de multiblock;
- recompensa/progressão.

Toda ação mutável iniciada por UI/HUD/keybind deve ser validada no servidor.

---

# 5. REGISTRIES E LIFECYCLE

Registrar pelo mecanismo NeoForge correto para a versão auditada:

- blocks;
- items;
- block entities;
- entity types;
- menu types;
- recipe types/serializers;
- data components;
- effects/attributes quando aplicável;
- sound events como identidade runtime;
- particle types como identidade runtime;
- demais registries realmente necessários.

A existência do registry de som/partícula não transfere a criação do asset para Engineering.

Evitar acesso prematuro a registry objects em static initialization.

---

# 6. BLOCKS, ITEMS E BLOCKENTITIES

Separar:

- definição/registro;
- estado persistente;
- ticking;
- capabilities;
- recipe execution;
- networking;
- menu;
- integração externa.

BlockEntity persistente deve definir save/load, dirty marking, chunk unload/reload, sync mínimo e comportamento diante de dados inválidos.

Nunca usar renderer como source of truth de estado funcional.

---

# 7. CAPABILITIES E RECURSOS

Usar capabilities/provider-native para item, fluid e energia conforme a API exata.

Regras:

- `SIMULATE` não muta;
- `EXECUTE` só ocorre após validação;
- evitar extração/inserção duplicada;
- respeitar sidedness;
- nenhuma integração pode gerar recurso grátis como fallback;
- adapters externos ficam isolados e fail-closed quando o provider não puder ser provado.

Para Create ou providers com recurso próprio, preservar o pipeline nativo em vez de criar FE/SU/heat paralelo.

---

# 8. RECIPES, DATAGEN E DADOS

Recipes devem declarar inputs, catalysts, fluids, outputs, byproducts, duração, requisitos de máquina, serializer e condições.

Preferir data-driven/datagen para:

- recipes;
- tags;
- loot;
- advancements;
- data maps;
- blockstates/models **como referência técnica de path/registry apenas**; autoria visual dos assets permanece no domínio Textura.

Data conditions devem substituir `if (ModList...)` espalhado quando aplicável.

---

# 9. MULTIBLOCOS

Engineering é authority de:

- controller;
- orientação lógica;
- validação;
- formação/desmontagem;
- ports/IO;
- estado;
- persistência;
- comportamento em chunk boundaries;
- capability aggregation;
- gameplay.

O contrato para Textura deve expor estados e anchors necessários sem definir aqui a aparência formada/não formada.

Evitar scan integral a cada tick; preferir invalidation local, dirty flags, cache e recovery bounded.

---

# 10. UI, HUD, MENU E INPUT — FRONTEIRA TÉCNICA

Engineering mantém apenas a infraestrutura funcional:

- `Menu`/container como backend de interação;
- widgets funcionais quando necessários ao código;
- input routing;
- server validation;
- Slot/DataSlot/container data/custom payload;
- snapshots/deltas necessários à apresentação;
- tooltip data sem decidir composição artística;
- acessibilidade técnica quando depender de estado/input.

`plans/textura/` define:

- composição visual da tela/HUD;
- layout;
- background;
- sprites;
- icons;
- gauges;
- tipografia/ornamentação;
- motion design;
- legibilidade visual;
- estados visuais e Golden Samples.

Não sincronizar BlockEntity inteira a cada tick se um delta/evento é suficiente.

---

# 11. NETWORKING

Payloads próprios devem possuir protocolo/versionamento quando necessário e declarar direção, codec, thread/handler e validação.

Serverbound:

- validar sender;
- dimensão;
- target;
- distância;
- permissão;
- estado;
- bounds;
- valores impossíveis;
- thread correta.

Registrar budget de tamanho/frequência/recipients/burst. Cliente nunca é authority.

---

# 12. PERSISTÊNCIA

Escolher o owner certo:

- BlockEntity data;
- Data Components;
- Data Attachments;
- SavedData;
- datapack registry/data maps;
- config.

Dados persistentes versionados devem possuir política de migração, comportamento de falha e testes de compatibilidade/corrupção.

---

# 13. ENTITIES, AI, BOSSES E COMBATE

Engineering é authority de EntityType, atributos, spawn, AI/brain/goals, targeting, navegação, combat hooks, boss state machine, persistence e provider integration.

A camada Textura recebe somente estados semânticos/anchors necessários para apresentação.

Para animação gameplay-critical:

- Engineering/provider define eventos, estados e janelas funcionais quando o provider assim exigir;
- Textura cria o clip/rig/curvas/apresentação;
- integração só ocorre por contrato explícito;
- renderer/clip não pode decidir dano, custo ou transição server-authoritative.

Epic Fight/Battle Arts/GeckoLib/AzureLib e equivalentes exigem auditoria da versão física antes de adapter específico.

---

# 14. WORLDGEN, TAGS E OPTIONAL INTEGRATIONS

Preferir datapack registries/datagen para worldgen.

Tags servem a membership/interoperabilidade; Data Maps quando behavior puder ser reloadable e extensível.

Integração opcional deve ficar isolada, não classloadar provider ausente, declarar metadata correta e ter smoke com provider presente/ausente.

Estruturas: runtime/worldgen fica no mod; assets/visual source ficam no domínio Textura.

---

# 15. CONFIGURAÇÃO

Separar CLIENT, COMMON e SERVER conforme semântica.

CLIENT é preferência/apresentação local e nunca gameplay authority.

Cada valor deve ter range, default, comentário, reload/restart behavior.

---

# 16. ÁUDIO, PARTÍCULAS E ANIMAÇÃO — SOMENTE RUNTIME BINDING

Engineering pode e deve implementar o plumbing necessário:

- registrar `SoundEvent` quando aplicável;
- disparar som no lado correto e evitar double-play;
- registrar `ParticleType` quando aplicável;
- transportar apenas parâmetros mínimos necessários;
- disparar partículas/VFX em resposta a evento real;
- expor estados/markers para animações;
- selecionar adapter de renderer/provider quando o contrato exigir.

Engineering **não** define:

- arquivo de áudio;
- identidade sonora;
- mix/volume artístico;
- cue sheet;
- aparência da partícula;
- paleta/material visual;
- curvas/clips de animação;
- rig/bones/pivôs;
- composição de VFX.

Esses elementos ficam em `plans/textura/`.

Gameplay nunca pode depender da existência de partícula, som ou renderer para ser correto.

---

# 17. HANDOFF ENGINEERING ↔ TEXTURA

O runtime deve expor um contrato mínimo e verificável, por exemplo:

```yaml
handoff_id:
runtime_owner:
asset_package:
required_states:
  - id:
    type:
    semantics:
required_events:
required_anchors:
provider_profile:
namespace:
performance_constraints:
```

Exemplo conceitual de boundary, sem especificar arte:

```text
runtime exposes: progress=float01, active=bool, heat=float01
presentation consumes those named values
```

O mapeamento, assets e QA correspondente vivem em `plans/textura/FRONTEIRA-ENGENHARIA-TEXTURA.md` e no plano artístico V5.1.

Engineering valida schema, namespace, paths e compatibilidade; não corrige asset silenciosamente.

---

# 18. PROVIDER CATALOG

Para cada integração registrar:

- mod id;
- versão física;
- loader/MC;
- source/ref;
- docs;
- API surface;
- licença;
- health;
- conflicts;
- optionality;
- proof level;
- testes.

Proof levels:

- `P0 PRESENCE_ONLY`;
- `P1 METADATA_VERIFIED`;
- `P2 SOURCE/DOC_VERIFIED`;
- `P3 COMPILE_PROVEN`;
- `P4 RUNTIME_SMOKE`;
- `P5 INTEGRATION_TESTED`;
- `P6 MULTIPLAYER/PERF_PROVEN`.

Não chamar integração de suportada em P0.

---

# 19. TESTING

Pirâmide:

1. unit tests;
2. serialization/codec;
3. registry/datagen validation;
4. GameTests;
5. client smoke;
6. dedicated-server smoke;
7. multiplayer;
8. full-modpack;
9. performance soak.

Engineering valida que o runtime **carrega e consome** o pacote de apresentação sem erro. A avaliação estética do resultado é responsabilidade de `plans/textura/`.

Client smoke técnico:

- resource load;
- screen/HUD integration sem exception;
- renderer/provider integration sem exception;
- particle/sound binding sem erro;
- keybind/input plumbing;
- ausência de missing-resource inesperado.

Dedicated server:

- zero client classloading indevido;
- registries/datapacks válidos;
- GameTests;
- nenhuma dependência de renderer/assets client-only para gameplay.

Full modpack:

- conflicts;
- mixins;
- tags/recipes/registries;
- provider coexistence;
- runtime stability;
- performance.

Visual quality e sound quality são gates do domínio Textura.

---

# 20. PERFORMANCE

Medir conforme aplicável:

- tick time;
- allocations;
- scans;
- graph operations;
- packet rate;
- save size;
- chunk interactions;
- entity count;
- custo runtime de render/particles apenas como métrica técnica de integração.

O domínio Textura é responsável por budgets artísticos e otimização de asset sem alterar gameplay.

---

# 21. FAIL-CLOSED / FAIL-SOFT

Fail-closed para provider errado, versão errada, dependência requerida ausente, schema inválido, protocolo incompatível, packet inseguro, migração crítica ausente ou integration proof insuficiente.

Fail-soft apenas para apresentação opcional quando um fallback aprovado existir. Um asset cosmético ausente nunca pode conceder poder, recurso ou bypassar regra de gameplay.

---

# 22. CI E RELEASE

Gates mínimos conforme aplicável:

```text
format/lint
compile
unit tests
datagen/resource validation
GameTests
build
JAR inspection
dedicated-server smoke
```

Client/full-pack podem ser jobs separados.

Nunca tratar skipped/bloqueio externo como PASS.

Release deve confirmar metadata, dependências, licença, migrations, protocol changes e que tooling-fonte artístico não foi empacotado indevidamente.

---

# 23. SCAFFOLDER E FEATURE GENERATORS

Scaffolder pode gerar skeleton de mod com MDK/metadata/package/registries/client-common split/tests/CI/README/STATUS e ponte para `plans/textura/`.

Feature generators podem gerar skeleton de block/item/BlockEntity/menu-screen plumbing/entity/recipe/payload/config/adapter, mas não devem gerar direção de arte como fallback.

Nenhum gerador sobrescreve arquivo modificado sem diff/decisão explícita.

---

# 24. VERTICAL SLICE

Uma fatia end-to-end de máquina pode exigir:

1. block + BlockEntity;
2. persistence;
3. inventory/fluid/energy conforme design;
4. recipe/process;
5. server tick;
6. menu/network sync;
7. `presentation_handoff` preenchido;
8. integração do pacote produzido em `plans/textura/`;
9. GameTest;
10. dedicated-server smoke;
11. client/runtime smoke;
12. modpack smoke quando aplicável.

Engineering não descreve aqui como a máquina deve parecer, animar ou soar.

---

# 25. CLASSES DE MOD SUPORTADAS

A Factory deve conseguir suportar content, tech, magic, RPG, worldgen e integration/addon mods. A classe do mod define quais sistemas de runtime serão necessários; não transfere automaticamente o design visual ao plano de Engineering.

---

# 26. CONTINUIDADE E GIT

Antes de iniciar/retomar trabalho:

- fetch da `main`;
- registrar SHA;
- procurar branch/PR equivalente;
- sincronizar a branch correta antes de editar.

Antes do handoff:

- fetch novamente;
- reconciliar `main` se avançou em área relevante;
- revisar diff;
- registrar SHA de `main` e HEAD.

Conflitos devem ser resolvidos semanticamente; não usar `ours`, `theirs` ou force-push como atalho para apagar trabalho concorrente.

---

# 27. REGRA FINAL DE SEPARAÇÃO

Qualquer novo plano ou seção deve ser classificado antes de entrar no repositório:

- se define **o que o jogo faz, quem é authority, como sincroniza, persiste, valida ou testa runtime** → Engineering/repo do mod;
- se define **como algo aparece, anima, soa ou comunica visualmente** → `plans/textura/`;
- se mistura os dois → separar em duas especificações ligadas por um handoff explícito.

Não reintroduzir especificação artística detalhada neste plano.
