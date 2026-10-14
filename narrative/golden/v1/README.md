# Narrative golden corpus v1

Corpus sintético mínimo da Factory. Ele existe somente para testar contratos reutilizáveis e não representa lore de nenhum consumidor.

`story/` cobre um caminho positivo de inventory, knowledge/evidence, relationship/memory/autonomy, chronology/causality e um documento auxiliar cujo `Entity ID` coincide com o ID do filename. `negative/` cobre diagnostics spoiler-safe com estado editorial inválido, referência global ausente, alvo de knowledge ausente e mismatch deliberado entre filename e `Entity ID`.

`visual-handoff.json` referencia um SVG neutro e não aprovado em `art/`. O arquivo é apenas fixture de integração para provar stable ID + provenance + containment + existência física + SHA-256 real do arquivo; ele não define a aparência canônica de personagem algum. Dimensões continuam cobertas pelos unit tests de PNG e não são inferidas a partir do SVG.

Os arquivos em `expected/` são goldens versionados. O workflow materializa os outputs atuais em `.factory-ci/narrative-golden/` e `golden_check.py` exige igualdade byte a byte.
