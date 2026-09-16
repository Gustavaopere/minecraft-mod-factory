# Narrative Profile Contract — revision 1

Este documento define o contrato público do profile do Narrative Authoring Toolkit. A revisão corrente é `1`.

## Princípios

O profile pertence ao repositório consumidor. A Factory fornece parser, validators, fixtures e regras de compatibilidade; ela não incorpora cânone específico de campanhas.

Todos os contratos avançados são opt-in. Ausência de uma capability avançada no JSON significa ausência daquela validação, não uma inferência de conteúdo ou uma autorização para preencher lacunas.

Os validators são estruturais. Eles não decidem verdade, canon, legitimidade de uma evidência, intenção, motivação, qualidade narrativa ou correção histórica.

## Chaves base obrigatórias

- `story_root`: raiz narrativa relativa ao workspace confiável.
- `dialogue_root`: raiz dos diálogos.
- `entity_types`: famílias de IDs estáveis no formato `TYPE-####`.
- `editorial_state_prefixes`: prefixes editoriais aceitos.
- `dialogue_required_sections`: aliases de headings exigidos para diálogos.

As chaves base já suportadas continuam compatíveis com profiles anteriores da revisão 1.

## Chaves base opcionais

- `editorial_state_headings`
- `dialogue_entity_type`
- `dialogue_reference_rules`
- `entity_required_sections`
- `entity_reference_rules`
- `auxiliary_document_contracts`

## Knowledge, evidence e provenance

`knowledge_evidence_contracts` é um objeto nomeado. Cada contrato declara:

- `include`: globs relativos a `story_root`;
- `required_sections`: mapa de chave lógica para aliases de heading `##`;
- `knowledge_state_sections`: seções opcionais que o consumidor pode usar para estados como observado, ouvido ou confirmado;
- `reference_rules`: regras opcionais de família e cardinalidade mínima de IDs estáveis.

A validação verifica somente estrutura, referências declaradas e existência dos alvos. Confiabilidade e suficiência probatória permanecem decisões editoriais.

## Relationships, memory e autonomy

`relationship_memory_contracts` também é opt-in. Cada contrato pode declarar seções obrigatórias, dimensões independentes, regras de referência, source/target actor, memory event, tipos permitidos de relação e estados de autonomia.

As dimensões são independentes por construção; a Factory não produz score agregado de relacionamento. `allow_self_relation` é `false` por padrão.

## Chronology e causality

`chronology_contract` declara:

- `event_types`;
- aliases para `before_headings`, `after_headings`, `causes_headings` e `caused_by_headings`;
- `causality_acyclic` quando o consumidor exige DAG causal.

O validator normaliza as relações em arestas direcionadas, rejeita self-reference, alvo ausente ou família incorreta, detecta ordens contraditórias e usa travessia determinística para detectar ciclos. Ele não infere uma aresta a partir de prosa livre.

## Authorities externas

`authority_reconcile.py` usa snapshots neutros schema 1. Cada snapshot possui `provenance.source`, `provenance.revision`, `provenance.captured_at` e registros por ID estável. Comparações apenas reportam ausência/divergência; não alteram canon e não fazem sync bidirecional implícito.

Uma authority marcada como obrigatória por `--required-external` falha fechado quando indisponível.

## Narrative → visual asset handoff

`visual_handoff.py` valida manifest schema 1 com `asset_roots` e registros `{entity_id, assets}`. Cada asset exige ID estável, `kind`, aprovação booleana, provenance `{source, revision}` e path contido em uma asset root declarada. Kinds suportados: `skin`, `portrait`, `concept-art`, `variation`.

O manifest referencia assets; não define aparência narrativa e não transfere ownership do asset para o domínio narrativo.

## Spoiler safety

CLIs exibem contagens/códigos por padrão. IDs, paths e linhas só aparecem com `--reveal`. Golden diagnostics cobrem explicitamente esse comportamento.

## Compatibilidade

A descrição machine-readable desta revisão está em `narrative/compat/profile-contract-v1.json`. A política de evolução está em `narrative/COMPATIBILITY.md`.
