---
name: bambu-a1
description: Use para qualquer coisa envolvendo a impressora 3D Bambu Lab A1 do usuario - calibrar filamento novo, diagnosticar defeito de impressao (bolinhas/zits, teia/stringing, costura marcada, peca descolando, camada feia), gerar e fatiar peca de teste por linha de comando, enviar arquivo para a impressora, acompanhar impressao, ler codigo de erro HMS. Cobre tambem PETG e troca de chapa. TRIGGERS (PT) - bambu, impressora 3d, A1, calibrar filamento, bolinhas na peca, teia na impressao, stringing, costura marcada, pressure advance, fator K, dinamica de fluxo, flow rate, vazao, torre de temperatura, fatiar por linha de comando, orcaslicer cli, enviar para a impressora, HMS, bico entupido, peca descolou, PETG na A1. TRIGGERS (EN) - bambu lab a1, 3d print blobs, zits, stringing, pressure advance, flow rate calibration, slice via cli, upload to printer, HMS code.
---

# Bambu Lab A1 — calibracao, diagnostico e operacao

Hardware de referencia desta skill: **Bambu Lab A1**, bico 0.4 aco inox, **BMCU** (clone de AMS).
Chapas: **Cool Plate** (PLA) e **texturizada PEI** (PETG, mesa 80 °C).
Filamentos: PLA Sunlu e PETG Masterprint, ambos genericos.

Infraestrutura em `~/.claude/mcp-servers/`: MCP `bambu-mcp` + scripts em `bambu-calib/`.
Conexao local por MQTT (8883) e FTPS (990), **sem LAN Only nem Developer Mode** — o
access code vem da API cloud e esta em `~/.bambu-mcp/credentials.json`.

---

## A regra que vale mais que todas

> **Exit code 0 nao significa que o parametro pegou.**
> Verificar no G-code gerado, nunca no comando enviado.
> E verificar **origem E destino**: o valor no perfil *e* o comando emitido.

Isso nasceu de erros reais e repetidos: enum invalido revertido em silencio, variavel de
ambiente ignorada, `M900 K` ausente, temperatura do perfil em 100 °C enquanto a injecao
por camada dizia 190. Nenhum deu erro. Todos apareceram so na inspecao do arquivo final.

## A segunda regra

> **Rode as calibracoes padrao do fabricante ANTES de investigar.**

O defeito que custou dois dias de investigacao (bolinhas em superficie) era resolvido
pela sequencia oficial: **temperatura → pressure advance na temperatura escolhida →
vazao**. Hipoteses exoticas (umidade, miolo, ancoragem, overhang, retracao, BMCU) foram
todas descartadas depois. Comece pelo padrao; investigue so o que sobrar.

## Roteador

| Situacao | Leia |
|---|---|
| Filamento novo, ou defeito de acabamento | `references/calibracao.md` |
| Gerar/fatiar peca de teste, enviar, monitorar | `references/operacao.md` |
| Algo nao pegou, erro estranho, HMS | `references/armadilhas.md` |
| Que filamento ja esta calibrado | `registro-filamentos.md` |

## Configuracao validada (07/09/2026)

```
PLA Sunlu vermelho
  temperatura        190 °C        (piso da faixa do fabricante; necessario, nao muleta)
  pressure advance   0,043         (calibrado A 190 °C — nao no padrao)
  retracao           0,8 / wipe 0% (padrao; aumentar criou cicatriz de costura)
  vazao              padrao        (reduzir PIOROU as bolinhas)
  chapa              Cool Plate, mesa 35 °C
  resultado          zero bolinhas, teia reduzida em 90%

PETG Masterprint
  temperatura        230 °C        (minimo do fabricante)
  pressure advance   ~0,083        (calibrado a 230; a 255 dava ~0,05 e era ruido)
  chapa              texturizada PEI, mesa 80 °C
```

## Pendencias conhecidas

- **Calibracao de Vazao manual (2 passagens) nunca foi feita.** E a etapa que resolveria
  a sobre-extrusao de 8–11% indicada por duas medicoes independentes (preset salvo em
  0,84835 e um teste manual em −7/−8). Afeta **dimensao**, nao acabamento.
- **Teste dos 100 mm de extrusao** (regua + caneta) nunca foi feito. Mede o extrusor
  direto, sem passar por aparencia de peca.
- **Peca com perna arrancando** (`rocky final.3mf`, 210 °C, suportes ligados) nunca
  retestada com a configuracao nova.
- Se o HMS de **bico envolto em filamento** parar de aparecer com a config nova, era
  consequencia do excesso depositado. Se persistir, e sintoma proprio.
