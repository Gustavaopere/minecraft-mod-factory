# Autoridade de versão para skills e instruções

## Alvo

- Minecraft: **1.21.1**
- NeoForge: **21.1.250**
- Java: **21**

A authority machine-readable do target corrente é `engineering/contracts/target-baseline.json`.

A política NeoForge é `latest-compatible-at-campaign-start`: no início de uma nova campanha, a Factory resolve a versão estável mais recente compatível com o Minecraft alvo a partir da metadata oficial; depois disso, o resultado é pinado exatamente em `target-baseline.json` e permanece imutável durante builds, testes e acceptance daquela campanha. Atualizações posteriores exigem nova resolução controlada e nova validação.

A versão exata das demais dependências deve vir do build, metadata, JARs e modlist física vigente do ambiente/repositório alvo.

## Ordem de autoridade

Para classe, método, evento, registry, resource path, pack format, assinatura, comportamento de provider ou compatibilidade:
1. código/build/metadata realmente presentes no repositório runtime alvo;
2. JAR/modlist física mais recente;
3. source/JAR/documentação oficial da versão exata;
4. `engineering/contracts/target-baseline.json` para o target da campanha e demais contracts/decisões canônicas da Minecraft Mod Factory;
5. skill project-authored aplicável;
6. skill compartilhada em `skills/library/`;
7. material `REFERENCE_ONLY` e exemplos de outras versões apenas como referência conceitual.

## Fail-closed

Se algo version-sensitive não puder ser confirmado para Minecraft 1.21.1 / NeoForge 21.1.250, não invente API, signature, registry, path ou comportamento. Não transplante silenciosamente exemplos de versões posteriores, Fabric, Forge legado ou Paper. Integrações opcionais permanecem indisponíveis até existir evidência suficiente.

A presença nominal de GeckoLib, Photon, AAA Particles/Effekseer ou qualquer outro provider não prova uma API específica; a versão física exata precisa ser verificada.
