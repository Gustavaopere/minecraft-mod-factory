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
python narrative/tooling/visual_handoff.py --manifest <manifest.json> [--check-files]
```

Os validators escondem IDs/caminhos/detalhes por padrão. Use `--reveal` somente em revisão editorial deliberada.

## Profile

O profile JSON define:

- `story_root` e `dialogue_root`;
- famílias de IDs (`entity_types`);
- prefixes de estados editoriais estáveis;
- headings aceitos para estado editorial;
- opcionalmente, seções estruturais obrigatórias por família de entidade em `entity_required_sections`;
- opcionalmente, regras tipadas de referência nessas seções em `entity_reference_rules`;
- opcionalmente, contratos estruturais para documentos auxiliares em `auxiliary_document_contracts`;
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

### Referências tipadas por seção de entidade

`entity_reference_rules` é um contrato opt-in adicional para seções já declaradas em `entity_required_sections`. A estrutura é `tipo de entidade -> chave lógica da seção -> regra`.

Cada regra pode declarar:

- `allowed_types`: famílias de IDs estáveis aceitas naquela seção, todas pertencentes a `entity_types`;
- `min_references`: quantidade mínima de IDs estáveis **distintos** exigida na seção, com padrão `0`.

Exemplo conceitual:

```json
{
  "entity_reference_rules": {
    "EVD": {
      "provenance": {
        "allowed_types": ["NPC", "FAC", "LOC"],
        "min_references": 0
      }
    }
  }
}
```

A chave lógica precisa existir em `entity_required_sections` para o mesmo tipo. Se a seção estiver ausente ou vazia, `validate_story.py` mantém somente o erro estrutural correspondente e não duplica o problema com um erro de cardinalidade. Quando a seção está preenchida, o validator conta IDs distintos e rejeita famílias não permitidas.

A regra continua estritamente estrutural: ela não conclui que uma referência prova autoria, conhecimento, causalidade, veracidade ou cânone. A existência global do ID continua sendo validada pelo grafo de `validate_story.py`; `--strict-references` permanece responsável por promover referências não resolvidas a falha de CLI.

### Contratos de documentos auxiliares

`auxiliary_document_contracts` permite aplicar estrutura e referências tipadas a Markdown auxiliar que **não** declara uma entidade própria no H1. O consumidor seleciona os arquivos por glob relativo a `story_root` e define `required_sections` e, opcionalmente, `reference_rules`.

Exemplo:

```json
{
  "auxiliary_document_contracts": {
    "quest-lifecycle": {
      "include": ["quests/**/*-lifecycle.md"],
      "required_sections": {
        "availability": ["Availability"],
        "discovery": ["Discovery"],
        "engagement": ["Engagement"],
        "resolution": ["Resolution"]
      },
      "reference_rules": {
        "discovery": {
          "allowed_types": ["NPC", "FAC", "LOC"],
          "min_references": 0
        }
      }
    }
  }
}
```

Regras da seleção:

- `include` é uma lista não vazia de globs relativos a `story_root`;
- os padrões usam `/`, aceitam `**` para recursão e não podem ser absolutos nem conter segmento `..`;
- um match que resolva fisicamente fora de `story_root` falha fechado;
- se mais de um contrato casar com o mesmo arquivo, cada contrato é aplicado independentemente;
- somente Markdown é validado por essa capability;
- opcionalmente, `filename_identity_section` pode apontar para uma chave de `required_sections`; nesse modo, o filename precisa começar por um ID estável `TYPE-####` e a seção indicada precisa conter exatamente esse mesmo ID, sem outro ID estável adicional.

Precedência de identidade: um arquivo que contenha uma declaração H1 reconhecida como `# TYPE-#### ...` continua sendo um entity record, mesmo que o glob auxiliar case com seu caminho. Um H1 como `# Lifecycle editorial de QST-0001 ...` continua auxiliar; `QST-0001` ali é referência, não declaração.

A semântica de `required_sections` e `reference_rules` é a mesma dos contratos de entidade: aliases case-insensitive, seção precisa ter conteúdo não vazio, referências são IDs estáveis distintos, e seção ausente/vazia não gera erro duplicado de cardinalidade. Os issue codes auxiliares são `missing-auxiliary-required-section`, `empty-auxiliary-required-section`, `missing-auxiliary-section-reference`, `invalid-auxiliary-reference-type`, `missing-auxiliary-filename-identity` e `auxiliary-filename-identity-mismatch`.

Esses checks continuam estritamente estruturais. Eles não inferem verdade, cânone, causalidade, legitimidade de conhecimento, qualidade narrativa ou mecânicas de mods/providers.

### Referências tipadas de diálogo

Cada regra de referência aponta para uma chave já presente em `dialogue_required_sections` e pode declarar:

- `allowed_types`: famílias de IDs aceitas naquela seção, todas pertencentes a `entity_types`;
- `min_references`: quantidade mínima de referências estáveis **distintas** exigida na seção, com padrão `0`.

Exemplo conceitual: um consumidor pode restringir `participants` a IDs `NPC` e exigir pelo menos um participante estável, sem tornar essa política uma regra global da Factory. O validator verifica somente tipo e cardinalidade na seção; resolução/existência global dos IDs continua pertencendo a `validate_story.py`.

Veja `profiles/example.json`.

## Templates

`templates/` contém scaffolds genéricos. O consumidor deve adaptar placeholders e constraints ao seu runtime/authority local sem copiar tooling de volta para o repositório do mod.

`TEMPLATE-ASSET-BRIEF.md` fornece um handoff editorial genérico para portrait, textura/modelo de runtime, provenance e evidência final. A Factory não fixa resolução, formato de skin, renderer ou provider: esses valores devem vir do consumidor e de capability mecânica verificada. Quando o consumidor quiser tornar a estrutura obrigatória, o brief pode ser selecionado por `auxiliary_document_contracts`; isso continua separado de `visual_handoff.py --check-files`, que só deve ser usado quando arquivos de asset reais existirem.
