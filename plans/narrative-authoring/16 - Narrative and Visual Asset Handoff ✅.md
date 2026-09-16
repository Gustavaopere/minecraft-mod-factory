# 16 — Narrative and Visual Asset Handoff ✅

Status: concluído na branch de implementação; release em `main` depende do merge do PR #118.

## Objetivo

Conectar dados editoriais de personagens e locais ao pipeline visual da Factory sem misturar geração de arte com canon narrativo.

## Capability pretendida

- manifest/handoff entre fichas narrativas e IDs de assets visuais;
- suporte a referências de skin, retrato, concept art e variações aprovadas;
- preservação de stable IDs e provenance do asset;
- validação de asset ausente ou referência quebrada quando o consumidor optar pelo contrato;
- nenhuma geração automática de aparência que sobrescreva descrição canônica;
- integração reutilizável com o domínio `art/` já existente na Factory.

## Dependências

- contratos auxiliares para fichas de autoria quando necessário;
- tooling de assets visuais da Factory.

## Gate de conclusão

Contrato de handoff versionado, testes de referência cruzada e fluxo demonstrável entre narrativa e assets sem duplicar ownership.

## Evidência de conclusão

- `visual_handoff.py` valida stable IDs, kinds, approval, provenance, asset roots, containment e existência física;
- `test_visual_handoff.py` cobre manifests válidos e inválidos;
- `narrative/golden/v1/visual-handoff.json` referencia um SVG físico neutro com `approved: false` e o CI usa `--check-files`;
- Factory run `35058398971` = `success`;
- a fixture é sintética e não representa aparência canônica de NPC do consumidor.
