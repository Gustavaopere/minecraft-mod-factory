# Narrative capability release procedure

A capability narrativa só é considerada apta a release quando todos os passos abaixo passam no mesmo conjunto de contratos.

1. Executar `python3 -m unittest discover -s narrative/tests -p 'test_*.py' -v`.
2. Materializar os outputs de `narrative/golden/v1` e executar `golden_check.py` contra `manifest.json`.
3. Confirmar que diagnostics negativos continuam spoiler-safe e que os casos positivos permanecem exatos.
4. Executar `validate_story.py`, `validate_advanced.py` e `story_inventory.py` com pelo menos um profile mantido pelo repositório consumidor.
5. Quando houver authority externa, usar snapshot neutro com provenance; ausência de authority obrigatória deve falhar fechado. O gate nunca sobrescreve canon.
6. Quando houver handoff visual, validar o manifest e, no gate apropriado, usar `--check-files`.
7. Registrar o SHA da Factory e o SHA/PR do consumidor usados na prova de compatibilidade.
8. Somente depois mover o pin do consumidor e marcar o milestone/release como concluído.

Para breaking changes, seguir `COMPATIBILITY.md` e adicionar migration documentada antes da release.
