---
name: bambu-a1
description: Use para qualquer coisa envolvendo a impressora 3D Bambu Lab A1 do usuario - calibrar filamento novo, diagnosticar defeito de impressao (bolinhas/zits, teia/stringing, costura marcada, peca descolando, camada feia), gerar e fatiar peca de teste por linha de comando, enviar arquivo para a impressora, acompanhar impressao, ler codigo de erro HMS. Cobre tambem PETG, troca de chapa e ajuste de suporte. TRIGGERS (PT) - bambu, impressora 3d, A1, calibrar filamento, bolinhas na peca, teia na impressao, stringing, costura marcada, pressure advance, fator K, dinamica de fluxo, flow rate, vazao, torre de temperatura, fatiar por linha de comando, orcaslicer cli, enviar para a impressora, HMS, bico entupido, peca descolou, PETG na A1, suporte nao sai, suporte grudado, quebrou ao tirar o suporte, folga do suporte, top z distance, interface de suporte, marca do suporte na peca, deformou onde tinha balanco. TRIGGERS (EN) - bambu lab a1, 3d print blobs, zits, stringing, pressure advance, flow rate calibration, slice via cli, upload to printer, HMS code, supports wont come off, support removal, support z gap, support interface layers.
---

# Bambu Lab A1 — calibracao, diagnostico e operacao

Hardware de referencia desta skill: **Bambu Lab A1**, bico 0.4 (a impressora reporta **aço endurecido** desde 22/09/2026; há também um 0.2 inox, não validado), **BMCU** (clone de AMS)
— **presente porem quebrado em 20/09/2026**, entao tudo que depende de trocar filamento
(interface de suporte em outro material, multicor) esta fora ate ele voltar. Ver skill `bmcu-370c`.
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

## A terceira regra

> **Diagnostico sai do G-code IMPRESSO (baixado do cartao), e teste so vale se reproduzir o defeito.**

Refatiamento local nao e o que foi impresso (o operador muda limiar e giro no Studio antes de
mandar). E cupom que sai limpo enquanto a peca sai ruim so descarta, nao aponta causa. Ver
`references/calibracao.md` (regras de metodo).

## Roteador

| Situacao | Leia |
|---|---|
| Filamento novo, ou defeito de acabamento | `references/calibracao.md` |
| Gerar/fatiar peca de teste, enviar, monitorar | `references/operacao.md` |
| Montar 3MF com varias placas por codigo; conferir furos e gravacoes no G-code | `references/operacao.md` |
| Suporte nao sai, quebrou ao remover, marca na peca, balanco deformado | `references/suportes.md` |
| Algo nao pegou, erro estranho, HMS | `references/armadilhas.md` |
| Trocou de bico; calibracao diz "Incompativel" | `references/armadilhas.md` (troca de bico) |
| Que filamento ja esta calibrado | `registro-filamentos.md` |
| Medir teia, partida ou suporte por objeto no G-code | `scripts/` (lista em `references/operacao.md`) |
| Cupom saiu limpo e a peca saiu ruim; montar teste A/B de suporte | `references/armadilhas.md` (o que um recorte muda) + `scripts/placa_ab.py` |
| Defeito no BMCU (trocador de filamento), nao na impressora | skill `bmcu-370c` |

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
  temperatura        240 °C        (o que ele imprime de fato; 230 e o minimo do fabricante)
  pressure advance   0,048         (calibrado a 240, cali 762; lido da impressora em 23/09)
  chapa              texturizada PEI, mesa 80 °C
  suporte            receita validada em references/suportes.md (22/09)
```

> **Resolvido (23/09/2026):** PA recalibrado a 240 °C = **0,048**. O "0,48" que circulou era
> vírgula no lugar errado — ver `registro-filamentos.md`.

## Pendencias conhecidas

- **Firmware 01.07.02.00 → 01.08.01.00 disponivel (23/09/2026).** Ao atualizar, registrar
  antes e depois: K (`k`, `cali_idx`), perfil do carretel e `nozzle_type` pelo status MQTT.

- **Calibracao de Vazao manual (2 passagens) nunca foi feita.** E a etapa que resolveria
  a sobre-extrusao de 8–11% indicada por duas medicoes independentes (preset salvo em
  0,84835 e um teste manual em −7/−8). Afeta **dimensao**, nao acabamento.
- **Teste dos 100 mm de extrusao** (regua + caneta) nunca foi feito. Mede o extrusor
  direto, sem passar por aparencia de peca.
- **Peca com perna arrancando** (`rocky final.3mf`, 210 °C, suportes ligados) nunca
  retestada com a configuracao nova.
- Se o HMS de **bico envolto em filamento** parar de aparecer com a config nova, era
  consequencia do excesso depositado. Se persistir, e sintoma proprio.
