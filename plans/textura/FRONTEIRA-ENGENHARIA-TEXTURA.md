# Fronteira normativa — Engineering ↔ Textura/Apresentação

Objetivo: impedir que planos de runtime voltem a acumular direção de arte, UI/HUD, texturas, animação, VFX ou áudio e, ao mesmo tempo, impedir que o domínio artístico passe a decidir gameplay.

## Regra principal

**Engineering produz semântica; Textura produz apresentação.**

Quando a mesma feature precisa das duas camadas, o vínculo é um contrato de handoff explícito.

| Tema | Authority Textura/Apresentação | Authority Engineering / repo do mod |
|---|---|---|
| UI/HUD | layout, sprites, icons, gauges, tipografia, motion, estados visuais, legibilidade | menu/container, data owner, sync, input routing, server validation, payloads |
| Textura/material | paleta, pixels, mapas/material presentation, atlases e source assets | resource path/namespace e carregamento técnico |
| Modelo | geometria visual, `.bbmodel`, UV, bones, pivôs | entity/block type, collision/gameplay shape quando funcional, renderer adapter plumbing |
| Animação | clips, curvas, poses, transitions visuais | estados/eventos funcionais; janelas gameplay-critical quando provider exige |
| Epic Fight/Battle Arts | authoring/handoff de animação e visual | provider adapter, combate, dano, stamina, timing funcional e authority do provider |
| VFX/partículas | aparência, composição, cores, materiais, lifetime visual | evento que dispara, parâmetros mínimos, ParticleType/factory/packet plumbing |
| Beam/laser | expressão visual | hit detection, dano, alcance, custo, cooldown e lógica server-authoritative |
| Áudio/SFX | arquivos, identidade sonora, variações, cue sheet, mix artístico | SoundEvent, side correto, trigger lógico, anti-double-play |
| Multiblock | visual root, formed/unformed presentation, part map visual, anchors | controller, validation, formation, IO, persistence, chunk behavior |
| Entity/boss | modelo/skin/rig/clips/VFX/SFX | EntityType, AI, state machine, targeting, combat, spawn, persistence |
| Estrutura/worldgen | source visual/ornamental quando aplicável | placement, biome rules, processors, loot, spawn, world authority |
| Tooltip | iconografia/composição visual | dados reais, cálculo, permissões e conteúdo funcional |
| Renderer | visual contract/provider profile | adapter técnico e seleção necessária para integrar o runtime |
| Performance | polycount/texture/VFX/audio budgets e otimização de asset | tick/network/save/runtime render integration metrics |
| QA | visual/sound QA e Golden Samples | compile/GameTest/client smoke/dedicated server/multiplayer/runtime correctness |

## Conteúdo extraído do antigo plano misto de Engineering

A reorganização classificou como apresentação e deslocou sua authority para esta subpasta:

1. lista detalhada de responsabilidades do antigo “Repo Textura”;
2. detalhes visuais de multiblocos: visual root, part map visual, formed/unformed presentation e anchors;
3. detalhes de `Screen` como background/sprites/icons/gauges/layout;
4. handoff de animação/Blender/Repo Textura para providers de combate;
5. source assets de estruturas;
6. especificação visual de sounds/particles;
7. `Asset Handoff Manifest` artístico;
8. `Visual Input Binding` como contrato de consumo;
9. escolha/descrição de perfil visual de renderer enquanto apresentação;
10. handoffs visuais de Create, magia, combate, colonies/structures e demais providers;
11. visual QA, animation/particle presentation e apresentação dentro de vertical slices;
12. UI visual, VFX, animation e áudio citados nas classes de mod.

No plano de Engineering permaneceram apenas os lados técnicos necessários para registrar, sincronizar, validar e disparar essas superfícies.

## Contrato mínimo de handoff

Engineering deve expor nomes e semântica, sem especificar a arte:

```yaml
handoff_id:
runtime_owner:
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

Textura pode então mapear esses dados para assets:

```yaml
presentation_package:
source_revision:
models:
textures:
ui:
hud:
animations:
vfx:
audio:
anchors:
provider_exports:
qa:
```

## Casos limítrofes

### Animação com hitbox/timing

O clip é artístico. A janela de hit/dano/custo é funcional. Quando o provider vincula timing de animação ao combate, o contrato deve registrar markers/eventos sem transferir authority de dano ao asset.

### HUD de recurso

Textura define como a barra/indicador aparece. Engineering/provider define o valor, range, sync e permissões. O HUD nunca materializa ou altera o recurso.

### Som com efeito gameplay

O asset e a identidade sonora ficam aqui. O efeito funcional e o evento causal ficam no runtime. Ausência do som não pode alterar o resultado gameplay.

### Partícula com área de efeito

A partícula é apresentação. A área funcional deve existir independentemente no servidor. Nunca usar a partícula como collider/authority.

### Modelo com bounds funcionais

Modelo visual fica aqui; collision/selection bounds que alteram gameplay pertencem ao runtime. O handoff registra a restrição sem deixar o asset decidir sozinho a regra.

## Regra fail-closed

Se o contrato funcional necessário para uma apresentação não estiver comprovado, o plano artístico registra `UNRESOLVED/BLOCKED` e não inventa o estado. Se o asset opcional faltar, Engineering só pode usar fallback visual previamente aprovado; nunca um fallback mecânico.
