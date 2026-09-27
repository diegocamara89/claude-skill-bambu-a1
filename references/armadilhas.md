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

## Troca de bico e calibração (22/09/2026)

**O diâmetro do bico se troca na TELA da impressora** (Ajustes -> Manutenção -> Bico). Desde
a V02.01.01.52 o campo do Bambu Studio é só exibição, e "Sincronizar informações" puxa da
impressora e sobrescreve o que foi digitado. Sintoma: "O tipo de bico não corresponde."

**A calibração e a impressão usam o filamento do CARRETEL, não o do projeto.** Sem AMS, é o
perfil atribuído ao slot `Ext`. Se ele é de outro bico, o assistente mostra "Incompatível"
e a lista fica vazia. E a impressão herda a mesa desse perfil: uma torre rodou a 70 °C
(Bambu PETG Basic) em vez dos 80 do perfil do operador, e descolou. Conferir
`ams_recent_filament_presets` no `BambuStudio.conf`, ou `bed_target_temper` no status.

**Teste de calibração se envia com "Calibração de Dinâmica de Fluxo" OFF.** Na torre de
temperatura, ligar põe segunda variável. No padrão de PA, a automática aplica um K por cima
de todas as faixas e o teste perde o sentido.

**Padrão PA, não Torre PA.** A torre é prisma reto, quase não acelera — é por isso que já
deu K errado no olho. O padrão é feito de cantos e traz o número impresso.

**Torre de temperatura: não varrer acima do máximo do rolo.** 270->220 num rolo de 230–260:
os blocos de 270/265 fizeram teia, o bico bateu no acúmulo e a peça descolou.

**Bico 0,2 com PETG não fechou.** Vazão máxima do perfil 1 mm³/s (0,4: 8). A mesma placa
foi de 3h21 para 6h43; parede interna 3,7x. O próprio assistente avisa alta chance de falha
da calibração automática com 0,2. Torre e padrão de PA saíram sujos — confundido com o caso
abaixo. Não validado nesta máquina.

**Bolinhas e teia no PETG (21–22/09): duas mudanças juntas, causa não separada.** O bico 0,4
tinha crosta marrom no corpo inteiro e bolota na ponta; havia escorrimento com o bico a
140 °C no nivelamento e teia na placa toda. A impressão limpa veio depois de **consertar o
bico E trocar o rolo (branco -> preto)** na mesma vez. No caso do PLA, umidade e bico sujo
foram descartados (tabela acima); aqui ficaram **em aberto**. Se voltar: trocar um de cada
vez, e fazer antes a extrusão no ar (estalo ou chiado = umidade).

**Ler o estado sem abrir o Studio:** `printer_get_status` via MQTT devolve `k`,
`vt_tray.cali_idx`, `nozzle_diameter`, `nozzle_type`, `vt_tray.tray_color` e
`bed_target_temper`. Credenciais em `~/.bambu-mcp/credentials.json`.

## Três da GUI do Studio (22–27/09/2026)

**Onde está o G-code que a GUI fatiou de verdade:**
`%LOCALAPPDATA%\Temp\bamboo_model\<dia>\<hora>#<pid>#N\Metadata\.<pid>.0.gcode`; `origin.txt`
diz qual 3MF está aberto. A pasta some quando o Studio fecha: copiar na hora da conferência.

**Editar o projeto na GUI pode mover partes sem aviso** (dividir em partes e apagar uma: as
pilhas de 0,4 e 0,6 voltaram para 0,2). Depois de edição do operador, medir Z de cada corpo
no 3MF salvo e os saltos de camada no G-code.

**Salvar o 3MF na GUI pode tirar chave de filamento de `different_settings_to_system[1]`**
(`filament_max_volumetric_speed` sumiu da lista em 27/09). Conferir a vazão no G-code.

## Mais duas que não dão erro

**Onde está o G-code que a GUI fatiou de verdade:**
`%LOCALAPPDATA%\Tempamboo_model\<dia>\<hora>#<pid>#N\Metadata\.<pid>.0.gcode`; `origin.txt`
diz qual 3MF está aberto. A pasta some quando o Studio fecha: copiar na hora da conferência.

**Editar o projeto na GUI pode mover partes sem aviso** (dividir em partes e apagar uma: as
pilhas de 0,4 e 0,6 voltaram para 0,2). Depois de edição do operador, medir Z de cada corpo
no 3MF salvo e os saltos de camada no G-code.

**Salvar o 3MF na GUI pode tirar chave de filamento de `different_settings_to_system[1]`**
(`filament_max_volumetric_speed` sumiu da lista em 27/09). Conferir a vazão no G-code.

**O Bambu ignora `layer_heights_profile.txt` escrito à mão no 3MF.** Tempo idêntico
(703 min) com e sem o arquivo. Altura de camada variável tem de ser feita na interface do
Studio. Conferir no G-code pelas linhas `; LAYER_HEIGHT:` (com espaço).

**A wiki da Bambu responde 402 ao WebFetch.** Ler pelo navegador embutido
(`get_page_text`). A página de troca de bico da A1 é `wiki.bambulab.com/en/a1/maintenance/replace-hotend`.

## O que um recorte da peça muda sem avisar (23/09/2026)

Cupom recortado de uma escultura grande, mesmo arquivo de configuração, mesma impressora, mesmo
rolo. Medido na camada do defeito (barra de uma manga), peça × cupom:

| | peça inteira | cupom |
|---|---|---|
| tempo por camada | 22 s | 13 s |
| **ventoinha na parede externa** | **72%** | **89%** |
| altura dos galhos de suporte até a região | ~30 mm | ~6 mm |
| orientação na mesa | girada 90° pelo operador | a do projeto |
| tempo decorrido até a camada | 4h44 | 31 min |
| cobertura de suporte na região | 82% / 20% interface | 82% / 20% interface |

A peça saiu com crosta; o cupom, limpo. **Cobertura de suporte igual não é condição igual.**

**A ventoinha cai sozinha em peça grande.** Com `fan_cooling_layer_time = 30`, o fatiador varia a
ventoinha entre `fan_min_speed` (40) e `fan_max_speed` (90) conforme o tempo da camada: camada
demorada ventila menos. Várias figuras ou ilhas na mesma altura = camada longa = menos vento.
O cupom, de camada curta, fica no máximo. Medir com `scripts/perfil_camadas.py`.

Para o cupom reproduzir a peça: mesma ventoinha na camada crítica (forçar pelo perfil ou juntar
cópias até o tempo de camada bater), mesmo giro (`placa_ab.py --girar`), e lembrar que altura
de suporte e horas decorridas o cupom baixo não reproduz.

Em aberto (não provado): se a ventoinha a 72% é a causa da crosta. É a maior diferença medida,
não uma causa demonstrada.

## Suporte automático não chega em queixo, barba e aro de óculos

Faces inclinadas demais para o limiar (`support_threshold_angle`) ficam sem apoio mesmo com o
suporte ligado. Escultura de 98 mm, arquivo impresso: sob o queixo, **97 mm² de balanço, 12%
com suporte perto e 0% com interface**; na zona dos óculos, 43 mm² e nada. A interface parou em
Z 66,8, abaixo do rosto. Os defeitos ("vermes" de filamento pendurados) apareceram ali. A falta de
apoio está medida; que ela cause os vermes é muito provável, não provado.
Em rosto: medir com `scripts/cobertura_suporte.py --regiao` e **marcar suporte à mão** onde faltar.
