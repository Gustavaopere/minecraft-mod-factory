# Textura / Apresentação — Planos canônicos

Esta subpasta é a authority de planejamento para toda a camada de apresentação da Minecraft Mod Factory.

## Incluído

- UI e HUD visual;
- menus/screens enquanto composição visual;
- texturas e materiais;
- sprites, ícones e glyphs;
- modelos 3D e `.bbmodel`;
- UV;
- bones, pivôs e rigs;
- animações e motion design;
- VFX, partículas e aparência de beams/lasers;
- shaders estritamente de apresentação quando aplicáveis;
- áudio/SFX e cue sheets;
- anchors visuais/sonoros;
- concept art;
- Visual Style Bible;
- cinematics;
- Golden Samples;
- QA visual/sonoro;
- Blockbench/Blender/tooling de authoring;
- export e asset manifests.

## Excluído

Permanecem em Engineering ou no repo do mod:

- gameplay;
- regras server-authoritative;
- dano/custo/cooldown;
- recipes/processamento;
- storage/energia/fluidos;
- networking e validação de payloads;
- persistência;
- AI;
- worldgen;
- menu/container backend;
- autoridade de input;
- decisão de quando um evento funcional ocorre;
- registro/runtime de `SoundEvent`/`ParticleType` e adapters técnicos, salvo documentação de handoff.

## Arquivos

- `PLANO-MESTRE-UNIFICADO-MINECRAFT-MOD-FACTORY-REPO-TEXTURA-BLOCKBENCH-ASSET-MCP-V5.1.md` — plano artístico principal preservado byte-for-byte do local anterior.
- `FRONTEIRA-ENGENHARIA-TEXTURA.md` — regra normativa para separar planos mistos.
- `AUDITORIA-SEPARACAO-APRESENTACAO-2026-09-13.md` — evidência da reorganização inicial.

## Regra para novos planos

Se um plano de feature possuir comportamento e apresentação, não colocar tudo no mesmo documento por conveniência. A parte funcional especifica estados/eventos/anchors necessários; a parte de Textura define a expressão visual/sonora e referencia o contrato funcional.
