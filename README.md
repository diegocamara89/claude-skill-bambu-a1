# bambu-a1

Skill para Claude Code que dá a um agente a capacidade de **calibrar, diagnosticar e
operar** uma Bambu Lab A1 — incluindo fatiamento por linha de comando, injeção de
parâmetros por altura, envio por FTPS e monitoramento por MQTT.

Nasceu de dois dias de investigação de um defeito real (bolinhas em superfícies lisas
que apareciam em PLA e em PETG) e carrega o que sobrou de útil: a receita que funciona,
as hipóteses que foram descartadas, e as armadilhas que não geram mensagem de erro.

## As duas regras que justificam a skill

> **Exit code 0 não significa que o parâmetro pegou.**
> Verificar no G-code gerado, nunca no comando enviado. E verificar **origem e destino**:
> o valor no perfil *e* o comando emitido.

Oito falhas silenciosas estão documentadas. Nenhuma delas gerou erro. Exemplos reais:
`brim_type=outer_brim` não existe no enum e o slicer reverte para `auto_brim` sem avisar;
um modo de teste gravou `nozzle_temperature = 100` porque o valor da faixa era percentual
de vazão, não temperatura; a metade das peças foi impressa com pressure advance
desconhecido porque `enable_pressure_advance = 0` faz o slicer não emitir `M900 K`.

> **Rode as calibrações padrão do fabricante antes de investigar.**

O defeito que custou dois dias era resolvido pela sequência oficial: **temperatura →
pressure advance na temperatura escolhida → vazão**. Umidade, bico, densidade de miolo,
overhang, retração, AMS de terceiro e saturação térmica foram todos investigados e
descartados — depois.

## O achado principal

O pressure advance exigido **sobe muito quando a temperatura cai**, e a calibração
precisa ser feita **na temperatura em que se vai imprimir**, não na padrão do perfil:

| Material | Temperatura | K medido |
|---|---|---|
| PLA genérico | 220 °C | 0,027 |
| PLA genérico | 190 °C | **0,043** |
| PETG genérico | 255 °C | 0,048–0,061 (disperso) |
| PETG genérico | 230 °C | **0,082–0,084** (consistente) |

Resultado com temperatura e K corrigidos juntos: de ~120 bolinhas para **zero**, e teia
reduzida em 90%.

Corolário útil: **dispersão de K entre slots do mesmo material indica temperatura de
medição alta demais, não defeito de hardware.** A 255 °C, três cores de PETG divergiram
27%; a 230 °C, os mesmos três slots ficaram em 2,4%.

## Estrutura

Divulgação progressiva — o `SKILL.md` é curto e roteia:

| Arquivo | Conteúdo |
|---|---|
| `SKILL.md` | regras de ouro, configuração validada, pendências, roteador |
| `references/calibracao.md` | receita para filamento novo; árvore de diagnóstico; regras de método |
| `references/operacao.md` | CLI do OrcaSlicer, injeção por altura, parâmetro por objeto, verificação obrigatória |
| `references/armadilhas.md` | 8 falhas silenciosas, 9 de ambiente, 10 hipóteses descartadas |
| `registro-filamentos.md` | registro de calibrações, com a temperatura de medição do K |

## O que dá para variar por altura

Injetando no `layer_change_gcode`, a firmware da A1 aceita `M104 S<t>` (temperatura),
`M900 K<k>` (pressure advance) e `M221 S<%>` (vazão) — o que permite uma grade de
27 combinações numa única peça.

**Não** varia por altura: retração, wipe, z-hop, largura de extrusão, altura de camada,
número de paredes, densidade de miolo, camadas de topo. Para esses há um fluxo híbrido
validado, em que o usuário define o parâmetro **por objeto** no Bambu Studio, salva o
projeto, e o agente fatia esse `.3mf` aplicando overrides por cima — a configuração por
objeto sobrevive.

## Requisitos

- **OrcaSlicer** — não o CLI do Bambu Studio, que não escreve no stdout e criptografa os
  próprios logs, tornando a depuração cega
- Node.js 18+ para os scripts de rede
- Python para parsear G-code (`Select-String` do PowerShell falha em vários casos)
- Um MCP de Bambu Lab, ou os scripts próprios, com credenciais em
  `~/.bambu-mcp/credentials.json`

## Adaptação

Os números de temperatura e K são **do hardware e dos filamentos de referência** — não
copie, recalibre. O que transfere é o método:

1. Anote a faixa do **rótulo do rolo**, não do perfil do slicer (eles divergem)
2. Calibre temperatura primeiro
3. Calibre pressure advance **naquela** temperatura
4. Calibre vazão
5. Verifique no G-code que os três valores chegaram
6. Registre com a temperatura de medição ao lado do K

## Licença

MIT.
