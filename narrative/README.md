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
- aliases semânticos das seções obrigatórias de diálogo;
- opcionalmente, regras tipadas de referência por seção em `dialogue_reference_rules`.

Cada regra de referência aponta para uma chave já presente em `dialogue_required_sections` e pode declarar:

- `allowed_types`: famílias de IDs aceitas naquela seção, todas pertencentes a `entity_types`;
- `min_references`: quantidade mínima de referências estáveis **distintas** exigida na seção, com padrão `0`.

Exemplo conceitual: um consumidor pode restringir `participants` a IDs `NPC` e exigir pelo menos um participante estável, sem tornar essa política uma regra global da Factory. O validator verifica somente tipo e cardinalidade na seção; resolução/existência global dos IDs continua pertencendo a `validate_story.py`.

Veja `profiles/example.json`.

## Templates

`templates/` contém scaffolds genéricos. O consumidor deve adaptar placeholders e constraints ao seu runtime/authority local sem copiar tooling de volta para o repositório do mod.
