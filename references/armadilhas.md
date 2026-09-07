# Armadilhas verificadas

Todas foram encontradas na pratica, e **nenhuma gerou mensagem de erro**. A maioria so
apareceu na inspecao do G-code final.

## Silenciosas — as que enganam

| # | Sintoma | Causa | Correcao |
|---|---|---|---|
| 1 | `brim_width` aplicado mas sem brim no caminho | `brim_type=outer_brim` nao existe no enum; o Orca reverte para `auto_brim` **sem erro** | valor certo e `outer_only` |
| 2 | Perfil errado usado, sem aviso | variavel de ambiente lida por um script e ignorada por outro | conferir `filament_settings_id` no G-code |
| 3 | Vazao travada em 100% nas 9 faixas | tipo de faixa novo registrado na lista mas **nao** na funcao de comando; caiu no caso generico | ao criar tipo de faixa, tocar **os dois** lugares |
| 4 | `nozzle_temperature = 100` | no modo vazao, o valor da faixa e **porcentagem**, nao temperatura | cada modo precisa da propria fonte de temperatura |
| 5 | Patamar impresso na temperatura da faixa seguinte | degrau na fronteira, onde a troca ocorre | degrau no meio da faixa |
| 6 | Rotulo em relevo invadindo a faixa vizinha | dimensionado sem descontar o sulco | zona util = `BAND − sulco − 2×margem` |
| 7 | `M900 K` ausente e PA desconhecido | `enable_pressure_advance = 0` faz o fatiador **nao** emitir nada; a impressora usa o valor interno dela | comparar so pecas com PA fixado, ou garantir vinculo de perfil |
| 8 | Finalizacao quebrada apos trocar slot de AMS | `M620 S255` **nao e slot** — e marcador de descarregar/externo | reescrever so as formas com sufixo `A` |

**Corolario do #4 e #7:** verificar **origem E destino**. No bug da temperatura, o `M104`
injetado por camada estava certo (190) e o `nozzle_temperature` do perfil estava errado
(100). Conferir metade da cadeia da a mesma sensacao de seguranca que conferir tudo e nao
vale nada.

**Corolario do #3:** o resumo que o proprio gerador imprime **nao e verificacao**. Ele
mostrava os 9 pares corretos enquanto o arquivo tinha vazao constante. Contar as
ocorrencias no G-code e o que vale.

## De ambiente

| Sintoma | Causa | Correcao |
|---|---|---|
| Orca diz `No such file` para arquivo existente | MAX_PATH do Windows; o scratchpad tem ~250 chars | trabalhar em `bambu-calib/work` |
| `process not compatible with printer` | perfis `.json` da Bambu usam `inherits` e sao fragmentos | achatar a heranca (`flatten-profile.mjs`) |
| Idem, apos "limpar" o perfil | remover `setting_id`/`instantiation`/`from` quebra | achatar e **nao tocar em mais nada** |
| `Cool Plate does not support filament` | PETG exige mesa 80 °C | `curr_bed_type=Textured PEI Plate` |
| Erro sem causa visivel | `stdio:"pipe"` engolindo o stderr do Orca | sempre imprimir `e.stderr` na falha |
| Bambu Studio "substituiu valores" ao abrir | arquivo fatiado pelo Orca usa enums mais novos | e traducao na importacao, nao corrupcao — **mas nao refatie ali**, perde a injecao |
| `Invalid OpenGL version` no CLI | so a miniatura de preview | inofensivo |
| Script de rede falha com modulo nao encontrado | resolucao de modulo segue a pasta do script | rodar de dentro de `bambu-mcp/` |
| `Select-String` retorna vazio sobre array de linhas | comportamento do PowerShell | parsear G-code com **Python** |

## Estado do bico e variavel de controle

`HMS_0300-1A00-0002-0001` = **bico envolto em filamento**, detectado no nivelamento.

**Cada impressao herda o residuo da anterior.** Uma gota acumulada se solta e se deposita
na peca, produzindo bolinhas espalhadas — material-independentes, imunes a troca de bico
(o residuo volta) e atenuadas por temperatura menor.

Antes de qualquer serie comparativa: **limpar o bico** (escova de latao a ~200 °C ou cold
pull) e conferir o HMS. Sem isso, pecas da mesma serie partem de estados diferentes.

Contagens baixas (1–3 bolinhas) em pecas impressas sem essa limpeza sao indistinguiveis
de residuo. Nao construa hipotese sobre elas — foi o que aconteceu com o "achado" de que
miolo esparso causava o defeito, que depois nao se sustentou.

**Artefato de pausa:** pausar e retomar deixa uma gota na altura da retomada. Anote a
altura e descarte esse ponto.

O HMS mantem historico da sessao de impressao: um codigo listado pode ser registro do que
ja foi resolvido. Cruzar com `print_error` (0 = sem erro corrente).

## Nao documentado / nao verificado

- `HMS_0500_0400_0001_0044` — presente em **todas** as leituras, inclusive com tudo
  normal. Suspeita nao verificada de estar ligado ao BMCU nao ser um AMS reconhecido.
- Se `M221`/`M900` injetados conflitam com a compensacao nativa da A1 — levantado por um
  council, **nunca verificado**. Na pratica os comandos foram aplicados.
- Se configuracao por objeto cobre retracao/z-hop. Cobre **miolo**, isso esta provado.

## Hipoteses testadas e DESCARTADAS

Nao reinvestigar sem evidencia nova.

| Hipotese | Como caiu |
|---|---|
| Umidade do filamento | extrusao no ar sem estalo; peca limpa com o mesmo rolo |
| Bico gasto ou sujo | trocado, defeito continuou |
| Miolo / ancoragem na parede | D0 com 15% saiu limpo e cubo B com 5% sujou — inconsistente; provavelmente residuo de bico |
| Numero de paredes | 2 paredes sem miolo saiu limpo |
| Superficie de topo | 4 camadas de topo saiu limpo |
| Overhang / ponte | as torres tinham 366 overhangs e 24 pontes; a peca real, zero |
| Reducao de vazao | **piorou** as bolinhas a 220 °C |
| Aumento de retracao | **criou** cicatriz de costura |
| BMCU / alimentacao irregular | dispersao de K entre slots era ruido de medicao a 255 °C; a 230 os mesmos slots deram 2,4% |
| Saturacao termica / tempo de camada | a parede unica ficou no piso de velocidade 99% do tempo e saiu limpa |
