# Registro de filamentos calibrados

Arquivo de dados. Atualize a cada calibracao — e a resposta para "esse rolo ja esta
calibrado?" e para "de onde veio esse numero?".

**O K vale para a temperatura em que foi medido.** Trocar a temperatura invalida o K.

| Marca / tipo / cor | Temp | K (PA) | Temp da medicao do K | Vazao | Chapa | Data | Estado |
|---|---|---|---|---|---|---|---|
| PLA Sunlu vermelho | 190 | **0,043** | 190 | padrao | Cool Plate 35 | 07/09/2026 | ✅ validado: zero bolinhas |
| PLA Sunlu vermelho | 220 | 0,027 | 220 | padrao | Cool Plate 35 | 07/09/2026 | ❌ gera bolinhas |
| PETG Masterprint preto (A1) | 230 | 0,084 | 230 | — | PEI 80 | 07/09/2026 | calibrado, nao validado em peca |
| PETG Masterprint (A3) | 230 | 0,083 | 230 | — | PEI 80 | 07/09/2026 | calibrado, nao validado |
| PETG Masterprint (A4) | 230 | 0,082 | 230 | — | PEI 80 | 07/09/2026 | calibrado, nao validado |
| PETG Masterprint preto | 255 | 0,048 | 255 | — | PEI 80 | 06/09/2026 | ⚠️ medicao ruidosa, nao usar |
| PETG Masterprint branco | 255 | 0,061 | 255 | — | PEI 80 | 06/09/2026 | ⚠️ medicao ruidosa, nao usar |

## Faixas de fabricante (rotulo, nao perfil)

| Material | Faixa | Padrao do perfil generico | Otimo encontrado |
|---|---|---|---|
| PLA Sunlu | 190–240 | 220 | **190** (piso) |
| PETG Masterprint | 230–270 | 255 | **230** (piso) |

Nos dois casos o otimo caiu no piso da faixa. Isso e observacao, nao lei — mas e o
primeiro lugar a testar num filamento generico novo.

## Vazao — pendencia aberta

Duas medicoes independentes indicam **sobre-extrusao de 8 a 11%**:

- preset salvo `Generic PETG Flow Rate Calibrated` = **0,84835** (padrao 0,95 → −11%)
- uma calibracao manual de Flow Rate anterior: melhores blocos em **−7/−8**

**A calibracao de Vazao manual em duas passagens nunca foi concluida e aplicada.** E a
etapa que fecharia isso. Afeta **dimensao**, nao acabamento — reduzir vazao piorou o
acabamento nesta maquina.

Teste que mede o extrusor direto, sem depender de aparencia de peca, e que nunca foi
feito: descarregar o filamento, marcar **120 mm** a partir da entrada do extrusor,
mandar extrudar **100 mm** pela tela, medir o que sobrou ate a marca.

| Sobrou | Significa |
|---|---|
| 20 mm | correto |
| 12 mm | +8% de sobre-extrusao |
| 9 mm | +11% |

Regua comum resolve: 8% de 100 mm sao 8 mm.

## Presets do Bambu Studio

Havia 9 presets acumulados de tentativas. Um deles herdava de perfil de **bico 0,2** —
se selecionado por engano no bico 0,4, sai tudo errado. Manter poucos, com nome que se
reconheca, e apagar o resto.

O **K nao fica no arquivo de perfil** — e guardado na impressora, vinculado ao nome da
calibracao e ao slot. Por isso nao aparece no JSON do preset. Confira o vinculo no `⋯`
ao lado do filamento em "Filamentos do Projeto", ou na tela de preparacao da impressao.

O Bambu Studio **nao expoe** o campo manual de pressure advance (o OrcaSlicer expoe, em
Filamento → Setting Overrides). Se precisar do valor escrito dentro do G-code para
verificacao, fatie pelo Orca com `enable_pressure_advance=1`.
