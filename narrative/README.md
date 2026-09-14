# Narrative Authoring — Minecraft Mod Factory

Este domínio contém a infraestrutura reutilizável para criar, revisar, validar e inventariar narrativa em projetos Minecraft.

## Fronteira de ownership

- **Factory**: skill, tooling, templates genéricos, contratos de profile e testes.
- **Repositório consumidor**: profile do projeto, cânone/lore, NPCs, quests, facções, locais, evidências, diálogos e regras específicas de authority/runtime.

A Factory não vira Campaign Bible e não guarda o conteúdo de uma campanha consumidora.

## Tooling

```bash
python narrative/tooling/validate_story.py --profile <profile.json> [--root <story-root>]
python narrative/tooling/validate_dialogues.py --profile <profile.json> [--root <dialogue-root>]
python narrative/tooling/story_inventory.py --profile <profile.json> [--root <story-root>] --format markdown
```

Os validators escondem IDs/caminhos/detalhes por padrão. Use `--reveal` somente em revisão editorial deliberada.

## Profile

O profile JSON define:

- `story_root` e `dialogue_root`;
- famílias de IDs (`entity_types`);
- prefixes de estados editoriais estáveis;
- headings aceitos para estado editorial;
- tipo de diálogo;
- aliases semânticos das seções obrigatórias de diálogo.

Veja `profiles/example.json`.

## Templates

`templates/` contém scaffolds genéricos. O consumidor deve adaptar placeholders e constraints ao seu runtime/authority local sem copiar tooling de volta para o repositório do mod.
