# Spell Presentation Contract

Preencha antes de declarar um spell/ability visualmente pronto. Este documento não substitui o contrato de gameplay do provider.

## 1. Identidade e autoridade

- Spell/ability ID:
- Mod/projeto owner do gameplay:
- Provider/framework:
- Versão física/JAR confirmada:
- Evento/boundary autoritativo de cast:
- Evento/boundary autoritativo de resolve/impact:
- Cancel/interruption boundary:
- Client/server ownership resumido:

## 2. Identidade visual

- Escola/tema:
- Função de gameplay percebida pelo jogador:
- Palette aprovada:
- Materiais/linguagem visual:
- Referências canônicas próximas:
- Elementos que NÃO devem ser copiados:
- Primeiro-person readability:
- Terceiro-person readability:

## 3. Lifecycle de apresentação

Para cada fase, marque `N/A` quando deliberadamente ausente.

### Anticipation

- Trigger causal:
- Duração/timing relativo ao cast:
- VFX:
- Animação/pose:
- Audio:
- Informação que comunica:

### Release

- Trigger causal/commit:
- VFX:
- Animação/attachment point:
- Audio:
- Camera/feedback:

### Travel / Active

- Forma: projectile / beam / area / aura / construct / instant / other
- Owner do efeito:
- VFX/model/trail:
- Audio/loop:
- Sincronização:
- Stop condition:

### Impact / Resolve

- Trigger causal:
- VFX:
- Audio:
- Área visual vs área real de gameplay:
- Feedback de hit/success/fail:

### Decay

- VFX tail:
- Audio tail:
- Cleanup/stop:
- Lifetime owner:

## 4. Backend

- Provider-native facilities usadas:
- Backend externo, se necessário: Photon / AAA+Effekseer / vanilla / outro
- Por que provider-native sozinho não basta, se houver backend externo:
- Classes/APIs/resources confirmados em fonte/JAR:
- Fallback quando backend opcional estiver ausente/incompatível:

## 5. Causalidade e multiplayer

- Uma ação autoritativa gera quantas sequências visuais:
- Deduplicação server/client:
- Prediction/preview permitido? Por quê:
- Parâmetros sincronizados:
- Random/seed policy:
- Join-in-progress relevante?:
- Death/logout/dimension-change behavior:
- Entity/block removal behavior:
- Chunk unload/server stop behavior:

## 6. Audio map

- Start/anticipation:
- Release/commit:
- Travel/active:
- Impact:
- Resolve/success:
- Cancel/fail:
- Tail/decay:
- Loop ownership/stop:
- Sound category/routing:
- Proveniência/licença dos assets:

## 7. Performance e acessibilidade

- Classe esperada de concorrência: baixa / média / alta / massiva
- Cenário real de pior caso a testar:
- Transparência/overdraw relevante:
- Trails/beams/post-process/dynamic-light relevantes:
- Reduced-particles/reduced-effects behavior quando suportado:
- Informação crítica disponível sem depender apenas de som/cor:

Não invente budgets universais. Registre medições/observações do cliente real quando existirem.

## 8. Evidência de aceitação

- Editor preview:
- Singleplayer:
- Dedicated server + client:
- Multiplayer com ≥2 viewers quando relevante:
- First person:
- Third person:
- Distância curta/média/longa:
- Spam/concurrency:
- Cancel/interruption:
- Cleanup lifecycle:
- Screenshots/video/logs:
- Pendências:

A aprovação final requer `VFX-QA.md` e, quando houver áudio project-owned, `AUDIO-QA.md`.
