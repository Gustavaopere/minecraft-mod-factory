# Audio QA — Minecraft 1.21.1 / NeoForge

Use para qualquer áudio project-owned ou integração de som adicionada por spell, ability, entidade, item, máquina ou ambiente.

## 1. Evento e causalidade

- [ ] cada cue está ligado a um evento real de gameplay/presentation;
- [ ] cast/release/impact não tocam duas vezes por server + client;
- [ ] cancel/interruption não toca success/impact indevido;
- [ ] replay/reload não repete sons one-shot;
- [ ] loops possuem owner, start policy e stop/fade policy explícitos;
- [ ] loops não são reiniciados por tick.

## 2. Multiplayer

- [ ] foi confirmado se o provider já transmite/toca o som antes de adicionar networking;
- [ ] cada listener pretendido recebe um único evento;
- [ ] viewers não-intencionados não recebem cue global indevida;
- [ ] local-only feedback não mente sobre estado autoritativo;
- [ ] latency/prediction não produz double playback.

## 3. Lifecycle

Quando o som pertence a entidade/bloco/efeito persistente:

- [ ] removal/despawn;
- [ ] death;
- [ ] logout;
- [ ] dimension change;
- [ ] chunk unload/reload;
- [ ] owner replacement;
- [ ] server/world shutdown quando relevante.

Nenhum desses cenários deve deixar loop órfão.

## 4. Mix e legibilidade

Testar no modpack real, não apenas no editor:

- [ ] volume relativo a combate, ambience, UI e spells do provider;
- [ ] transient de release/impact continua legível sem ser excessivo;
- [ ] loops não mascaram cues importantes;
- [ ] casts repetidos não geram fadiga sonora desnecessária;
- [ ] variação de pitch/variant preserva identidade e timing;
- [ ] spatialização faz sentido em first/third person;
- [ ] distâncias relevantes ao gameplay foram ouvidas;
- [ ] categoria/routing permite controle adequado pelo usuário quando a API/provider oferece isso.

Não fixe loudness/attenuation por regra universal. Ajuste por comparação e teste real.

## 5. Acessibilidade

- [ ] informação crítica não depende exclusivamente de áudio;
- [ ] cues de perigo importantes possuem apoio visual/tátil quando o sistema permitir;
- [ ] sons muito agudos/graves/repetitivos foram avaliados por fadiga;
- [ ] variações não removem a capacidade de reconhecer o evento.

## 6. Proveniência

Para cada asset:

- [ ] origem/autor registrado;
- [ ] licença ou produção original registrada;
- [ ] modificações/processamento registrados;
- [ ] atribuição necessária identificada;
- [ ] redistribuição pelo mod/repositório permitida;
- [ ] asset gerado por IA, se houver, registra provider/termos aplicáveis ao momento da criação.

Não aceitar asset simplesmente porque está disponível para download.

## 7. Dedicated server

- [ ] dedicated server inicia sem classloading client-only do pipeline de áudio;
- [ ] resources/event registration usados existem na versão alvo;
- [ ] ausência de backend opcional não derruba o servidor;
- [ ] fallback, quando existir, é explícito e não altera gameplay.

## 8. Evidência final

Registrar:

- commit/HEAD;
- modlist/JAR snapshot;
- lista de sound events/resources realmente usados;
- origem/licença dos arquivos;
- cenário first-person/third-person/multiplayer;
- teste de spam/repetição;
- teste de loop cleanup;
- pendências.

Resultado: `PASS`, `PASS WITH DOCUMENTED LIMITATION` ou `FAIL`.
