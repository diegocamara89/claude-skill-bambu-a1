---
name: bambu-a1
description: Use para calibrar filamentos, diagnosticar defeitos de impressão e operar a Bambu Lab A1 do usuário. Cobre ABS, PETG e PLA; topo deformado em peças pequenas, resfriamento e tempo de camada, bolinhas, teia/stringing, costura, aderência, pontes e suportes; temperatura, dinâmica de fluxo/pressure advance e vazão; Bambu Studio/OrcaSlicer CLI, 3MF, G-code, multicor/BMCU, envio, monitoramento e erros HMS.
---

# Bambu Lab A1 — calibracao, diagnostico e operacao

Hardware de referencia desta skill: **Bambu Lab A1**, bico 0.4 (a impressora reporta **aço endurecido** desde 22/09/2026; há também um 0.2 inox, não validado), **BMCU** (clone de AMS)
— **funcionando** (confirmado pelo dono em 09/10/2026; ficou quebrado de 20/09 até o conserto),
entao multicor e interface de suporte em outro material estao disponiveis. Defeito nele: skill `bmcu-370c`.
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

Aproveite calibrações já feitas. Se a torre ficou boa e o topo de uma peça pequena ficou
ruim, compare o resfriamento e o tempo de camada antes de repetir a torre ou mudar a
temperatura. Caso ABS/HB20 e campo exato da interface em `references/calibracao.md`,
seção "Peça pequena: torre boa, topo ruim".

## A terceira regra

> **Diagnostico sai do G-code IMPRESSO (baixado do cartao), e teste so vale se reproduzir o defeito.**

Refatiamento local nao e o que foi impresso (o operador muda limiar e giro no Studio antes de
mandar). E cupom que sai limpo enquanto a peca sai ruim so descarta, nao aponta causa. Ver
`references/calibracao.md` (regras de metodo).

## A quarta regra

> **Fatie um arquivo por vez, e só o que a pessoa vai imprimir agora.**

Cada fatiamento pelo CLI leva minutos, e o dono fica esperando. Fatiar várias variantes numa
rodada (laço sobre 4–5 arquivos, "já que estou aqui") custou uma interrupção em 27/09/2026:
"muita demora". Entregue primeiro o arquivo que ele vai imprimir; as outras variantes e a
publicação ficam para depois, **um arquivo por comando**, com retorno curto entre eles, e só
quando o pedido exigir. Detalhe em `references/operacao.md` § Fatiar por linha de comando.

## A quinta regra

> **3MF editado por código só está pronto depois de aberto no Studio.**

O CLI lê o arquivo inteiro; a interface remonta o perfil de fábrica e só reaplica o que está em
`different_settings_to_system`. Em 09/10/2026 o Grogu fatiou certo no CLI e abriu no Studio com
limiar 25 e camada 0,16 em vez de 30 e 0,20 — e a regra já estava escrita em `operacao.md`.
Edite com `scripts/ajusta_3mf.py` (faz a lista) e confira 2–3 valores na tela do Studio.
Junto: receita de outra peça (suporte, folga, limiar) se **converte** para a camada nova
(`references/suportes.md`), não se copia.

## Roteador

| Situacao | Leia |
|---|---|
| Filamento novo, ou defeito de acabamento | `references/calibracao.md` |
| Peça pequena em ABS, torre boa e topo ruim; localizar tempo de camada | `references/calibracao.md`, seção "Peça pequena: torre boa, topo ruim" |
| Gerar/fatiar peca de teste, enviar, monitorar | `references/operacao.md` |
| Montar 3MF com varias placas por codigo; conferir furos e gravacoes no G-code | `references/operacao.md` |
| Suporte nao sai, quebrou ao remover, marca na peca, balanco deformado | `references/suportes.md` |
| Algo nao pegou, erro estranho, HMS | `references/armadilhas.md` |
| Trocou de bico; calibracao diz "Incompativel" | `references/armadilhas.md` (troca de bico) |
| Que filamento ja esta calibrado | `registro-filamentos.md` |
| Medir teia, partida ou suporte por objeto no G-code | `scripts/` (lista em `references/operacao.md`) |
| Cupom saiu limpo e a peca saiu ruim; montar teste A/B de suporte | `references/armadilhas.md` (o que um recorte muda) + `scripts/placa_ab.py` |
| Ponte, teto, face de baixo sobre suporte com fios soltos ou fendas (PETG) | `references/ponte-e-teto.md` |
| Empilhar pecas sem trocador; topo de grade granulado ou com sulco | `references/empilhamento-e-acabamento.md` |
| Defeito no BMCU (trocador de filamento), nao na impressora | skill `bmcu-370c` |
| Multicor caro: muitas trocas, purga, torre; conferir se a pintura tem erro | `references/multicor.md` + `scripts/pintura_3mf.py` e `resumo_fatiamento.py` |
| Mesa cheia (muitos bonecos): Studio sem memória, "pular objeto" indisponível, ordem dos slots | `references/operacao.md` (Enviar e acompanhar) + `scripts/corrige_mapa_3mf.py` + `bambu-mcp/ams-slots.mjs` |
| Figura impressa de cabeça para baixo, topo áspero; cor nova custa troca | `references/suportes.md` (cúpula na mesa) e `references/multicor.md` (uma cor a mais) |
| Pintura com pontinhos de outra cor, borda serrilhada | `scripts/limpa_pintura_3mf.py` (`references/multicor.md`, Limpar a pintura) |
| "Ficou algum ponto sem suporte?" antes de imprimir | `scripts/filete_no_ar.py` (placa inteira) + `references/suportes.md` |
| Editar 3MF por código (ajuste, perfil de outro projeto, reforço de suporte pintado) | `scripts/ajusta_3mf.py` + a quinta regra acima |

## Configuracao vigente

```
PLA Sunlu vermelho
  temperatura        190 °C        (piso da faixa do fabricante; necessario, nao muleta)
  pressure advance   0,043         (calibrado A 190 °C — nao no padrao)
  retracao           0,8 / wipe 0% (padrao; aumentar criou cicatriz de costura)
  vazao              padrao        (reduzir PIOROU as bolinhas)
  chapa              Cool Plate, mesa 35 °C
  resultado          zero bolinhas, teia reduzida em 90%

PETG Masterprint
  temperatura        240 °C        (rotulo 230-260)
  pressure advance   0,048         (calibrado a 240, cali 762)
  vazao              0,9405        (calibrada)
  vazao maxima       16 mm³/s      (torre sem falha ate 20)
  chapa              texturizada PEI, mesa 80 °C
  suporte            receita em references/suportes.md (escultura, camada 0,08)
  ponte / teto       fluxo da ponte 1,5 + ponte 10 mm/s + ventoinha de saliencia 100%
                     (vao 20-44 mm, com e sem suporte; references/ponte-e-teto.md)
```

## Pendencias conhecidas

- **Firmware 01.07.02.00 → 01.08.01.00 disponivel (23/09/2026), nao atualizado.** Ao atualizar,
  registrar antes e depois: K (`k`, `cali_idx`), perfil do carretel e `nozzle_type` pelo status
  MQTT, e testar de novo o inicio remoto (`references/operacao.md`, Enviar e acompanhar).
