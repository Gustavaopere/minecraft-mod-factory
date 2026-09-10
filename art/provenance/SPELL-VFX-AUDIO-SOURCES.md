# Spell / VFX / Audio Source Audit

Historical source audit: 2026-09-07.
Physical presence revalidated for Factory migration against modlist snapshot 2026-09-09.

Este documento preserva evidência histórica e registra o estado físico atual. Documentação externa não prevalece sobre a modlist/JAR física e nenhuma API Java específica é inferida apenas por presença de provider.

## 1. Autoridade física atual

Snapshot físico 2026-09-09, SHA-256 `7c0a23d6013101383d196526e4b6ba6940fb54a0fed10eaed5956ab015cfcc00`:

- Photon `2.2.6.a` — presente;
- GeckoLib `4.9.2` — presente;
- Iron's Spells 'n Spellbooks `1.21.1-3.16.3` — presente;
- Player Animator `2.0.4+1.21.1` — presente;
- AAA Particles — ausente no snapshot físico 2026-09-09, estado `UNAVAILABLE`;
- AAA Particles: World — ausente no snapshot físico 2026-09-09, estado `UNAVAILABLE`;
- Effekseer — sem presença física independente comprovada no snapshot atual.

Presença e versão não provam API, integração saudável, suporte da Factory ou licença aplicável a um uso concreto.

## 2. Photon

Fontes históricas preservadas:

- https://github.com/Low-Drag-MC/Photon
- https://github.com/Low-Drag-MC/Photon/blob/1.21/LICENSE
- https://www.curseforge.com/minecraft/mc-mods/photon/files/8824095

O audit histórico registrou linha NeoForge 1.21.1, authored VFX, integração Java exposta pelo projeto e condições de licença na branch então examinada. Essas observações permanecem provenance, não uma confirmação nova das APIs atuais.

Para implementação, inspecionar a revisão/JAR correspondente ao Photon `2.2.6.a` e reconfirmar classes, signatures, resources e licença antes de codificar ou redistribuir.

## 3. AAA Particles / Effekseer

Fontes históricas preservadas:

- https://www.curseforge.com/minecraft/mc-mods/aaa-particles
- https://www.curseforge.com/minecraft/mc-mods/aaa-particles-world
- https://effekseer.github.io/en/documentation.html

O snapshot histórico de 2026-09-07 registrava AAA Particles `2.2.3` e AAA Particles: World `2.0.0`. Essa evidência foi supersedida para presença atual: ambos estão ausentes no snapshot físico 2026-09-09 e são `UNAVAILABLE` para o ambiente corrente.

Não reutilizar snippets, APIs, formatos ou assumptions Effekseer/AAA enquanto uma futura modlist física não comprovar presença e a versão exata não for auditada.

## 4. Iron's Spells 'n Spellbooks como referência

Fontes históricas preservadas:

- https://github.com/iron431/irons-spells-n-spellbooks/tree/1.21
- https://github.com/iron431/irons-spells-n-spellbooks/blob/1.21/LATEST_CHANGES.MD

O audit histórico tratou Iron's como referência de composição e polish de spells, não como autorização para copiar assets, código ou signatures. A versão física atual confirmada é `1.21.1-3.16.3`; qualquer integração deve ser verificada contra essa versão real.

## 5. Regra de implementação

Provider-native first:

1. confirmar o owner real do gameplay no runtime repository;
2. confirmar presença/versão no ambiente físico;
3. verificar se o provider já produz animação/VFX/som adequado;
4. evitar duplicação de presentation listeners;
5. usar backend externo somente quando fisicamente disponível e a API/formato exatos estiverem comprovados;
6. fallback deve ser explícito, seguro e não alterar a semântica de gameplay.

## 6. Pendências deliberadas

- nenhuma API Java específica do Photon é congelada neste documento;
- nenhuma API AAA/Effekseer é tratada como disponível no snapshot atual;
- nenhuma assinatura de Iron's é congelada por analogia;
- budgets numéricos de partículas/áudio não são inventados sem profiling do cliente real;
- assets de terceiros continuam sujeitos a auditoria individual de licença/proveniência.
