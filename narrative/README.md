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
- opcionalmente, seções estruturais obrigatórias por família de entidade em `entity_required_sections`;
- tipo de diálogo;
- aliases semânticos das seções obrigatórias de diálogo;
- opcionalmente, regras tipadas de referência por seção em `dialogue_reference_rules`.

### Seções obrigatórias por tipo de entidade

`entity_required_sections` é um contrato opt-in de estrutura Markdown. Cada chave de primeiro nível deve ser uma família já presente em `entity_types`; dentro dela, cada chave lógica declara um ou mais aliases aceitos para um heading `##`.

Exemplo conceitual:

```json
{
  "entity_required_sections": {
    "EVD": {
      "provenance": ["Provenance", "Origem/proveniência"],
      "limits": ["What it does NOT prove"]
    }
  }
}
```

Para um registro que realmente declare um ID `EVD-####` no H1, `validate_story.py` exige que cada seção configurada exista e contenha pelo menos uma linha não vazia antes do próximo heading `##`. Aliases são comparados sem distinguir maiúsculas/minúsculas. Tipos não configurados e arquivos auxiliares sem declaração de entidade não recebem essa exigência estrutural.

A validação é deliberadamente sintática: presença e conteúdo não vazio. Ela não decide se a prosa é verdadeira, suficiente, coerente ou canônica; essas decisões permanecem no processo editorial do consumidor.

### Referências tipadas de diálogo

Cada regra de referência aponta para uma chave já presente em `dialogue_required_sections` e pode declarar:

- `allowed_types`: famílias de IDs aceitas naquela seção, todas pertencentes a `entity_types`;
- `min_references`: quantidade mínima de referências estáveis **distintas** exigida na seção, com padrão `0`.

Exemplo conceitual: um consumidor pode restringir `participants` a IDs `NPC` e exigir pelo menos um participante estável, sem tornar essa política uma regra global da Factory. O validator verifica somente tipo e cardinalidade na seção; resolução/existência global dos IDs continua pertencendo a `validate_story.py`.

Veja `profiles/example.json`.

## Templates

`templates/` contém scaffolds genéricos. O consumidor deve adaptar placeholders e constraints ao seu runtime/authority local sem copiar tooling de volta para o repositório do mod.
