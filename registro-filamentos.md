# Registro de filamentos calibrados

Arquivo de dados: só o que vale hoje. Atualize a cada calibracao — e a resposta para "esse rolo
ja esta calibrado?" e para "de onde veio esse numero?".

**O K vale para a temperatura em que foi medido.** Trocar a temperatura invalida o K.

| Marca / tipo / cor | Temp | K (PA) | Temp da medicao do K | Vazao | Chapa | Data | Estado |
|---|---|---|---|---|---|---|---|
| PLA Sunlu vermelho | 190 | **0,043** | 190 | padrao | Cool Plate 35 | 07/09/2026 | ✅ validado: zero bolinhas |
| PETG Masterprint (cor do dia da calibração não registrada) | 240 | **0,048** | 240 | 0,9405 (calibrada) | PEI 80 | 20/09/2026 | ✅ lido na impressora (`k = 0.0480`, cali 762); peças boas com o preto desde 22/09 |
| PETG Masterprint branco | 240 | 0,048 (herdado, não medido neste rolo) | 240 | 0,9405 | PEI 80 | 23/09/2026 | torre 230–250 toda limpa, extrusão no ar lisa; cupons limpos |
| Generic PETG @A1 0.2 nozzle - 240 | 240 | — | — | — | PEI 80 | 22/09/2026 | ❌ bico 0,2: calibração não concluída |

PETG Masterprint: vazão máxima **16 mm³/s** (torre sem falha até 20, a 240 °C).

O bico 0,4 é reportado como **aço endurecido** (`hardened_steel`) desde 22/09: conduz menos
calor e costuma pedir alguns graus a mais. Se o acabamento mudar, é o primeiro lugar a olhar.

## Faixas de fabricante (rotulo, nao perfil)

| Material | Faixa do rótulo | Padrao do perfil generico | Em uso |
|---|---|---|---|
| PLA Sunlu | 190–240 | 220 | **190** |
| PETG Masterprint | 230–260 | 255 | **240** |

## Presets do Bambu Studio (30/09/2026)

Filamento: `Generic PETG 240` (o de uso), `Generic PETG @BBL A1 0.2 nozzle - 240` (herda de
perfil de **bico 0,2**: selecionado por engano no bico 0,4, sai tudo errado) e
`SUNLU Silk PLA+ @BBL A11`. Manter poucos, com nome que se reconheca.

O **K nao fica no arquivo de perfil** — e guardado na impressora, vinculado ao nome da
calibracao e ao slot. Por isso nao aparece no JSON do preset. Confira o vinculo no `⋯`
ao lado do filamento em "Filamentos do Projeto", ou na tela de preparacao da impressao.

O Bambu Studio **nao expoe** o campo manual de pressure advance (o OrcaSlicer expoe, em
Filamento → Setting Overrides). Se precisar do valor escrito dentro do G-code para
verificacao, fatie pelo Orca com `enable_pressure_advance=1`.
