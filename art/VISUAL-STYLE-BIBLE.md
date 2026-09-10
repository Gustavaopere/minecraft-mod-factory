# Visual Style Bible — Minecraft Mod Factory

Status: **canônico para a gramática visual reutilizável de assets project-owned; contexto histórico do pack é apenas referência**  
Alvo técnico atual: Minecraft 1.21.1 · NeoForge 21.1.248 · Java 21  
Autoridade de versão/presença: `../skills/VERSION-AUTHORITY.md`

## 1. Objetivo e autoridade

Esta Bíblia evita que assets próprios tecnicamente corretos pareçam pertencer a jogos diferentes. Ela define uma gramática visual reutilizável para modelos, texturas, animações, VFX, áudio representado em UI e presentation feedback sem transformar resource packs, shaders ou VFX client-side em autoridade de gameplay.

A Factory é autoridade do pipeline visual em `art/`. O repositório runtime de cada mod continua autoridade sobre gameplay, registries, networking, persistence e release. Esta Bíblia **não autoriza copiar** texturas, modelos, animações, sons ou efeitos de terceiros. Referências externas continuam sujeitas a licença e proveniência.

## 2. Contexto histórico do pack

O material histórico auditado em 2026-09-08 registrava Excalibur como base visual, Fresh Animations e extensões, família Mobs Refreshed, Mandala's GUI em dark mode, Complementary Shaders — Reimagined e outras camadas de apresentação. Esse inventário veio de um snapshot editorial do modpack e **não é regra global da Factory** nem prova de presença atual.

Os nomes e versões desse snapshot são preservados em `provenance/VISUAL-STYLE-SOURCES.md`. A modlist física mais recente continua autoridade para JARs/mod IDs/versões; resource packs e shaders editoriais são apenas contexto até existir evidência física equivalente.

Os domínios Black Arcana, Enshrouded Shroud, Volcanoes e Create presentes na Bíblia histórica são exemplos de direção de arte específica do pack. Eles podem orientar um mod que explicitamente adote esse contexto, mas não são defaults de todo mod produzido pela Factory.

## 3. Princípios visuais reutilizáveis

### 3.1 Minecraft-readable first

- Silhueta deve continuar legível em distância real de gameplay.
- Geometria deve preservar leitura voxel/Blockbench; detalhe não justifica microgeometria sem função visual.
- Proporção estilizada é preferível a realismo fotográfico quando o realismo prejudica a leitura Minecraft.
- Forma primária > forma secundária > detalhe. Textura, emissive e glow não devem mascarar uma forma primária ruim.

### 3.2 Material antes de emissive

- Metal deve ler como metal por valor, bordas, desgaste e contraste, não apenas brilho.
- Pedra deve preservar massa/porosidade sem ruído fotográfico fino.
- Madeira deve ter direção/fibra estilizada coerente com escala.
- Tecido deve comunicar dobra/estrutura em poucos clusters, evitando noise uniforme.
- Emissive/glow é sinal semântico e focal; não substitui definição do material base.

### 3.3 Shader enhancement, not dependency

Assets devem permanecer compreensíveis sem depender de bloom, volumetrics ou exposição específica de shader. Um shader pode melhorar a cena, mas não pode ser a única razão pela qual símbolo, telegraph, contraste de item ou feedback é legível.

### 3.4 Coerência sem cópia

Quando um mod precisa coexistir com um contexto visual existente, compare silhueta, densidade de detalhe, material, valor e escala. Não copie pixels, modelos, animações ou efeitos de terceiros por semelhança visual.

## 4. Textura, resolução e texel density

Não existe resolução global fixa para todo asset.

Antes de escolher resolução:

1. selecionar uma referência apropriada por tamanho e função;
2. medir a relação pixel ↔ unidade Minecraft em faces comparáveis quando houver corpus auditável;
3. registrar resolução e densidade escolhidas em `standards/MODEL-ASSET-CONTRACT.md` ou no brief correspondente;
4. manter densidade consistente entre partes visualmente equivalentes;
5. justificar exceções quando interface, emissive, boss ou item de proximidade exigir mais detalhe.

Sem corpus binário auditável, não congele número universal de pixels por bloco. Um Golden Sample pode escolher uma resolução local como exemplo; isso não vira regra global.

## 5. Paleta e contraste

- Paleta deve ter hierarquia: base dominante, material secundário, detalhe focal e emissive/acento quando aplicável.
- Estados importantes de gameplay não podem depender apenas de uma única cor.
- Saturação máxima deve ser reservada a foco, perigo, magia ativa ou feedback equivalente.
- Silhueta e valor devem continuar distinguíveis em iluminação clara e escura.

## 6. Linguagem por domínio

A Factory não impõe um único tema ficcional. Cada mod deve declarar seu domínio no brief/contrato e manter uma gramática coerente.

### 6.1 Fantasia / base estilizada

Pedra, madeira, metais, couro e tecido devem preservar leitura material e escala Minecraft. Ornamento deve reforçar função ou identidade, não preencher toda superfície por padrão.

### 6.2 Arcano / magia

Geometria limpa, símbolos localizados e energia com direção. O efeito deve comunicar origem, trajetória e resolução. Evitar nuvem de partículas sem forma ou timing causal.

### 6.3 Tecnologia / máquina

Estrutura, eixo, conexão, função e manutenção visual devem ser compreensíveis. Forma deve explicar função antes do ornamento. Referências de mods de terceiros não autorizam copiar texturas ou geometria.

### 6.4 Domínios específicos do pack histórico

Black Arcana, Enshrouded Shroud, Volcanoes e Create permanecem documentados como contexto histórico em `provenance/VISUAL-STYLE-SOURCES.md`. Regras específicas desses domínios só entram em um mod quando sua especificação as adota explicitamente.

## 7. Modelos e silhueta

Todo modelo final deve registrar:

- função e distância típica de visualização;
- tamanho em unidades Minecraft;
- silhouette statement em uma frase;
- shape language;
- hierarquia/bones e attachment points;
- bounds e áreas de interação visual;
- vistas frontal, lateral, traseira, três-quartos e escala in-game.

Modelos de item também devem ser verificados em GUI, ground, first-person e third-person quando esses contexts existirem. O contrato canônico é `standards/MODEL-ASSET-CONTRACT.md`.

## 8. Animação

Animação project-owned deve assumir coexistência com o runtime real do mod e com providers fisicamente confirmados, nunca isolamento por default.

- Idle deve ter vida sem disputar atenção com gameplay.
- Attack/cast precisa de anticipation legível antes do commit quando a mecânica permitir.
- Impact visual deve alinhar com o boundary real de gameplay.
- Loops precisam de ciclo limpo e owner claro.
- Evitar clipping crítico com corpo/equipamento e conflito óbvio com first-person/third-person.
- Animação não pode criar uma segunda autoridade de hit/cast.

## 9. VFX

Lifecycle geral:

`ANTICIPATION -> CHARGE -> RELEASE -> TRAVEL/ACTIVE -> IMPACT -> LINGER -> DECAY`

Nem todo efeito precisa de todas as fases; omissão deve ser deliberada.

Ordem de decisão:

1. recurso provider-native comprovado para a versão física;
2. vanilla/NeoForge para efeito simples;
3. backend externo fisicamente presente e cuja API/formato exatos tenham sido verificados;
4. fallback explícito quando o backend for opcional ou indisponível.

Photon está presente no snapshot físico atual; isso prova presença/versão, não uma API específica. AAA Particles/Effekseer aparecia em evidência histórica, mas está ausente no snapshot físico 2026-09-09 e não é backend disponível por default. Consulte `provenance/SPELL-VFX-AUDIO-SOURCES.md`.

Não empilhe backends para o mesmo evento por padrão e não use particle count como métrica universal de qualidade.

## 10. UI e ícones

- Ícones devem sobreviver a fundos claros/escuros relevantes e a estados desabilitados/cooldown.
- Borda/shape não deve depender apenas de cor.
- Símbolos devem ser legíveis em tamanho real da HUD/inventário.
- Mockup ampliado não substitui QA no jogo.

O uso histórico de Mandala dark é contexto, não requisito global.

## 11. Proveniência

Para cada asset project-owned, registrar:

- autor/origem;
- ferramenta/processo;
- licença ou status original;
- referências usadas;
- alterações derivativas quando houver base licenciada;
- restrições de redistribuição/atribuição.

Imagem/áudio gerado por IA não é automaticamente rights-clear; registrar termos/proveniência aplicáveis à criação.

## 12. Gate de aprovação

Nenhum asset é final apenas porque compila ou exporta. Aprovação exige, conforme aplicável:

- contrato preenchido;
- structural QA;
- `standards/VISUAL-QA.md` no Minecraft real;
- contexts de câmera relevantes;
- iluminação clara/escura;
- animação/impact timing;
- multiplayer/performance/lifecycle para VFX persistente;
- pendências explícitas quando alguma evidência não puder ser produzida.

Use os standards já migrados em `standards/`. Skills e tooling ainda não migrados não são tratados como dependência canônica desta Bíblia.
