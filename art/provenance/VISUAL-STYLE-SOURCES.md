# Visual Style Sources

Migration audit: 2026-09-10.

Este documento separa o contexto editorial histórico do modpack da autoridade física atual. Ele não transforma resource packs, shaders ou mods visuais em authority de gameplay nem em requisitos globais da Factory.

## Fontes de inventário

1. modlist física 2026-09-09 — autoridade atual para JARs/mod IDs/versões, SHA-256 `7c0a23d6013101383d196526e4b6ba6940fb54a0fed10eaed5956ab015cfcc00`;
2. `Auditoria Mestre da Modlist — NeoForge 1.21.1` — snapshot editorial histórico de 2026-09-08 para resource packs, shaders e contexto visual;
3. `ART-PIPELINE-SOURCES.md` — provenance de Blockbench/GeckoLib;
4. `SPELL-VFX-AUDIO-SOURCES.md` — provenance de providers de VFX/spells/áudio.

## Contexto editorial histórico de 2026-09-08

O material histórico registrava:

- Excalibur como base visual e substituto de Whimscape;
- Fresh Animations 1.10.4;
- Fresh Animations: Extensions 1.8.1;
- Fresh Animations: Player Extension 1.1;
- Excalibur | Fresh Animations Patch;
- Mobs Refreshed 2.2 e compatibilidades Fresh Animations;
- Mandala's GUI — Dark mode 3.1 e add-ons/compatibilidades;
- Complementary Shaders — Reimagined r5.9.

Esse snapshot é `REFERENCE_ONLY`: preserva contexto de composição do pack histórico, mas **não prova presença atual**. Seus binários não foram materializados na Factory como corpus canônico e os itens acima não são defaults visuais para todo mod.

## Estado físico atual relevante

A modlist física 2026-09-09 confirma:

- GeckoLib `4.9.2`;
- Photon `2.2.6.a`;
- Iron's Spells 'n Spellbooks `1.21.1-3.16.3`;
- Player Animator `2.0.4+1.21.1`.

AAA Particles, AAA Particles: World e Effekseer não aparecem no snapshot físico atual. Evidência histórica de versões anteriores é preservada, mas não autoriza declarar esses backends disponíveis hoje.

Se contexto editorial e JAR físico divergirem sobre presença/versão de mod/provider, a evidência física mais recente vence para presença/versão. Ela ainda não prova API, compatibilidade ou runtime health.

## Limite de evidência

Como resource packs/shaders editoriais não formam um corpus binário auditável na Factory:

- nenhuma resolução universal de textura é congelada;
- nenhuma texel density universal é inferida;
- nenhuma cor exata de terceiro vira paleta project-owned por simples amostragem;
- nenhuma referência externa autoriza copiar asset;
- decisões visuais específicas devem ser registradas no contrato/brief do asset e verificadas no ambiente real quando aplicável.
