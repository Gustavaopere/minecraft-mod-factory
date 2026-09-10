# VFX QA — Minecraft 1.21.1 / NeoForge

Use depois que o efeito já existe. Editor preview é evidência parcial, não aprovação final.

## 1. Causalidade

- [ ] cast cancelado não dispara release/impact como se tivesse concluído;
- [ ] uma ação autoritativa gera uma única sequência de apresentação;
- [ ] não há double-spawn server + client/prediction;
- [ ] impact visual ocorre no mesmo evento/posição lógica do resolve real;
- [ ] área visual não promete alcance maior/menor que o gameplay sem indicação deliberada;
- [ ] replay/reconnect/reload não duplica efeitos one-shot.

## 2. Lifecycle e cleanup

- [ ] efeitos bound a entidade param/removem corretamente em death/removal;
- [ ] dimension change não deixa efeito órfão;
- [ ] logout/despawn não deixa loop visual persistente;
- [ ] chunk unload/reload é seguro para efeitos persistentes relevantes;
- [ ] server stop não exige cleanup client-only impossível;
- [ ] cancel/interruption tem saída visual coerente;
- [ ] timers/trails/beams não crescem indefinidamente por ausência de stop condition.

## 3. Leitura visual

Validar em primeira e terceira pessoa:

- [ ] silhouette/source do cast é legível;
- [ ] release tem timing perceptível;
- [ ] travel/beam/projectile permite entender direção;
- [ ] impact/resolve é distinguível de anticipation;
- [ ] decay limpa a cena sem pop abrupto injustificado;
- [ ] friendly/hostile/self quando relevante são distinguíveis pelo conjunto de sinais, não apenas por uma única cor;
- [ ] partículas não escondem alvo, crosshair, HUD crítico ou telegraph importante.

## 4. Distância e escala

- [ ] curta distância;
- [ ] média distância;
- [ ] longa distância relevante ao spell;
- [ ] modelo/partícula não clipa de forma grave na câmera;
- [ ] escala visual combina com a hitbox/área real;
- [ ] first-person não é excessivamente intrusivo;
- [ ] third-person comunica o cast a outros jogadores.

## 5. Performance

Não use um número universal de partículas como gate. Teste o cenário de concorrência definido no Spell Presentation Contract.

- [ ] idle/no-cast não mantém emissores desnecessários;
- [ ] spam do spell não acumula instâncias sem bound;
- [ ] múltiplos casters/targets não causam crescimento não limitado;
- [ ] transparência/overdraw foi observada em cenas carregadas;
- [ ] trails/beams/post-process foram testados com múltiplas instâncias quando aplicável;
- [ ] cleanup após a cena retorna o cliente a estado estável;
- [ ] backend opcional ausente/incompatível segue fallback documentado e seguro.

## 6. Multiplayer e dedicated server

- [ ] dedicated server inicia sem carregar classes client-only do VFX;
- [ ] pelo menos dois viewers recebem o mesmo evento quando a apresentação é pública;
- [ ] viewers fora de escopo/range não recebem efeito indevido quando o provider define culling/broadcast restrito;
- [ ] parâmetros aleatórios importantes permanecem coerentes quando a concordância visual é requisito;
- [ ] latency não transforma prediction em segunda authority de gameplay.

## 7. Backend-specific

### Provider-native

- [ ] API/evento/resource confirmados na versão física;
- [ ] não há duplicação com VFX que o provider já toca automaticamente.

### Photon

- [ ] versão física confirmada antes de assumir API/formato;
- [ ] FX/timeline/resources carregam no modpack real;
- [ ] lifecycle executor/owner encerra corretamente;
- [ ] `.fxpack`/resources têm proveniência e distribuição compatíveis quando usados.

### AAA Particles / Effekseer

- [ ] versão física confirmada;
- [ ] efeito Effekseer carrega pela API/formato real da versão instalada;
- [ ] native-loading failure/fallback foi considerado;
- [ ] bind/finalization/cleanup do efeito foi testado quando aplicável.

## 8. Evidência final

Registrar:

- commit/HEAD testado;
- modlist/JAR snapshot relevante;
- backend e versão;
- screenshots/captura de vídeo para first/third person;
- logs quando lifecycle/networking for relevante;
- cenários de concurrency;
- pendências e riscos restantes.

Resultado: `PASS`, `PASS WITH DOCUMENTED LIMITATION` ou `FAIL`.
