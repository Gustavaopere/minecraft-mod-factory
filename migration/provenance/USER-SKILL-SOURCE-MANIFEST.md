# Manifesto das skills recebidas — 2026-09-07

SHA-256 dos ZIPs enviados pelo usuário:

| Arquivo | SHA-256 |
|---|---|
| `minecraft-ci-release.zip` | `0efe74c270681b96c639bd210d2f34dee4b866c1ff5e8afd89834b89d5ad5a36` |
| `minecraft-commands-scripting.zip` | `42e980a1c3f9740f0a397f890a573b587d9a465106c05d1017e1cf98606eb008` |
| `minecraft-datapack.zip` | `17d0a58cfe5931a726986c7e49f8d1752ec7df1d1e8753f75dbcfeadbbd64ee0` |
| `minecraft-dependency-compatibility-graph.zip` | `d7f7ff2ce5b44aa16ec4a76800fb173907c9be1da7e114f675efb6bfd64a9a24` |
| `minecraft-essentials-ops.zip` | `049c0f03cfa9de2cef270581d3455801586320dda4c3b5616ad22dde880a349e` |
| `minecraft-imagegen.zip` | `a1c3d2209edb164a14cc1abf63354a65bdcffa336ed15115a8822ad93f7bd280` |
| `minecraft-jar-reverse-engineering.zip` | `97166425ba81f11479f70f195f5507c079134c12c5cff6d7008eb93f9a012ee2` |
| `minecraft-mod-dev.zip` | `5bb06fc555963b84bde64080c211d35c379e73a7beaf3226023d5a98787ccdd3` |
| `minecraft-modding.zip` | `09ac9c9dae01ee7cd51435f2df0d803ca81037f22981697f835b6c3fef9b8e35` |
| `minecraft-modpack-bisect.zip` | `ac1a72806a6c6d04c43274e55cdbb8339908009d0659edc82589afda8b896a21` |
| `minecraft-multiloader.zip` | `5ca172816c9c3c1dfdb7f5f5c557aed9eda9ba8250221a8de7a696a5289302d6` |
| `minecraft-neoforge-engineering.zip` | `c98439e90091f4f998d45aefc534fe157e41854defa4b787a8be282279d1032a` |
| `minecraft-neoforge-modpack-debugging.zip` | `63a2d85ac53d28416412a28fdbf33e7cae9d2c88b8cff19bb3d18efb0bed948c` |
| `minecraft-plugin-dev.zip` | `2a5d24201c292959afc071edbc2f9a1259ef6427c6c951b88fe5207c654556fa` |
| `minecraft-resource-pack.zip` | `fbd08681555f2468fa227be31ce0052016058ad215a50c7898af2d21bb01de77` |
| `minecraft-server-admin.zip` | `9b8368e69f1313a6bf0f2347d5c30e17b6ec043153c2d3a10b55e0271a59ab73` |
| `minecraft-testing.zip` | `4a8c902cac129162686941ea6f3329d4a0eb71e987317cb25fc788dd39b592c9` |
| `minecraft-world-generation.zip` | `686ffa0bafe5e68665a5ecf498f2473b3cb4bfcf30bd2943f7e4e1ffdab71bee` |
| `minecraft-worldedit-ops.zip` | `44eda7187802e756c8eb66690147afc6cb3ebeb6baae3220ff8092f8bc23e181` |
| `modpack-inventory-redundancy-audit.zip` | `aa6555fa84bc1b24a3d3f652516d9a629f1ec9b48d36a7c57dd6c506ecdd5c4a` |

## Critério de importação integral

O conjunto validado recebido contém:

- **20** skills únicas;
- **142** arquivos-fonte no total;
- `SKILL.md` obrigatório em cada skill.

Arquivos `PROJECT-OVERLAY.md` são project-authored e **não** entram na contagem 142. Eles existem para restringir os bundles multi-versão ao alvo Minecraft 1.21.1 / NeoForge 21.1.x / Java 21 sem adulterar o conteúdo-fonte recebido.

A conclusão da importação deve gerar/atualizar `FULL-USER-SKILL-IMPORT.md` com contagem por skill e falhar se a soma fonte não for exatamente 142.
