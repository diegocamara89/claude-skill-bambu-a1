# Operacao: gerar, fatiar, enviar, monitorar

Tudo em `~/.claude/mcp-servers/`. Scripts de rede em `bambu-mcp/` (usam o `node_modules`
de lá — **precisam rodar daquele diretorio**). Geradores em `bambu-calib/`.

## Inventario

| Script | Funcao |
|---|---|
| `bambu-calib/flatten-profile.mjs` | achata `inherits` do perfil, aplica overrides |
| `bambu-calib/build-tower.mjs` | torre com faixas por altura: modos `temp`, `pa`, `flow`, `combo`, `grid` |
| `bambu-calib/build-singlewall.mjs` | cubo parametrizavel (paredes/miolo/topo/extras) |
| `bambu-calib/digits.mjs` | digitos 7 segmentos em relevo para rotular faixas |
| `bambu-calib/patch-ams-slot.mjs` | reescreve o slot de AMS num `.gcode` |
| `bambu-mcp/ftp-upload.mjs` | envia arquivo (confirma tamanho) |
| `bambu-mcp/ftp-list.mjs` | lista o armazenamento |
| `bambu-mcp/ftp-download.mjs` | baixa — use para **verificar o que a impressora tem** |
| `bambu-mcp/ftp-delete.mjs` | remove arquivos |
| `bambu-mcp/mqtt-status.mjs` | estado, temperaturas, progresso |
| `bambu-mcp/mqtt-error.mjs` | `print_error` e codigos HMS |
| `bambu-mcp/watch-print.mjs` | monitor continuo; registra trocas de faixa e desfecho |
| `bambu-mcp/print-start.mjs` | inicia `.gcode` remoto; simula sem `--confirmar` |

Nenhum deles imprime o access code. Ler o codigo para colar em parametro de MCP e
bloqueado pelo classificador — e os scripts nao precisam disso.

## Fatiar por linha de comando

Use **OrcaSlicer**, nao Bambu Studio: o CLI do Bambu Studio nao escreve no stdout e os
logs dele sao criptografados. O do Orca reporta o erro em `stderr` e em `00000.log`.

```
orca-slicer.exe --slice 0 --arrange 1
  --load-settings "maquina.json;processo.json"
  --load-filaments "filamento.json"
  --export-3mf saida.gcode.3mf --outputdir <dir> modelo.stl
```

- O CLI grava tambem `plate_1.gcode` no `--outputdir` — **G-code puro de graca**, sem
  precisar de flag (`--export-gcode` nao existe).
- **Um arquivo por vez, sempre.** Cada fatiamento leva minutos. Não faça laço sobre várias variantes num
  comando só: fatie o arquivo que vai ser impresso, devolva o resultado e só então (e só se o pedido
  exigir) passe para o próximo. Conferência de todas as variantes para publicação também vai uma por vez,
  avisando o que falta.
- **Trabalhe em caminho curto.** MAX_PATH do Windows: o scratchpad tem ~250 caracteres e
  o Orca diz `No such file` para arquivo existente. Use `bambu-calib/work`.
- **Nunca passe `--arrange` ao fatiar um projeto arranjado pelo usuario** — destroi o
  posicionamento dele.

## Variar parametro por altura

Injetando no `layer_change_gcode` do perfil de maquina, com condicional do Orca
(`{if layer_z < N}...{elsif}...{else}...{endif}`). A firmware da A1 aceita:

| Comando | Efeito |
|---|---|
| `M104 S<t>` | temperatura do bico |
| `M900 K<k>` | pressure advance |
| `M221 S<%>` | vazao |

**Nao varia por altura** (sao decisao do fatiador): retracao, wipe, z-hop, largura de
extrusao, altura de camada, numero de paredes, densidade de miolo, camadas de topo.

Sempre emita **os tres** comandos por faixa, mesmo os que nao estao variando, para o
estado da maquina ser explicito em cada altura.

## Parametro de fatiador diferente POR OBJETO (validado)

Resolve a limitacao acima para parametros de **processo**. Testado: 27 combinacoes
(3 temperaturas × 3 vazoes × 3 densidades de miolo) numa impressao.

1. Gere as STL (uma por variante, geometria identica).
2. **O usuario** abre no Bambu Studio, arranja, clica direito em cada objeto, define o
   parametro por objeto, e **salva o projeto `.3mf`**. Deixar UM objeto sem override:
   ele herda o global, que voce controla.
3. Fatie **esse `.3mf`** pelo CLI com `--load-settings`. A configuracao por objeto
   (`Metadata/model_settings.config`) sobrevive; os overrides valem para o global e para
   a injecao por camada.

### Como verificar que o por-objeto pegou

Nada avisa se nao pegar.

- Contar `; FEATURE: Sparse infill` por objeto, delimitando por
  `; start printing object, unique label id: N`. O objeto de 0% deve dar **zero**.
- Conferir `filament used [g]` da placa contra a **soma** das variantes fatiadas
  separadamente (bateu 53,93 g contra 54,2 g previstos).
- Pegada de cada objeto: medir **so movimentos de extrusao** (`G1 X.. Y.. E..`) das
  primeiras camadas. Incluir viagens infla o intervalo e simula sobreposicao inexistente.

## Verificacao obrigatoria antes de enviar

```python
import zipfile, re
z = zipfile.ZipFile("saida.gcode.3mf")
g = z.read([n for n in z.namelist() if n.endswith(".gcode")][0]).decode("utf-8","ignore")
for k in ["nozzle_temperature","curr_bed_type","sparse_infill_density","wall_loops",
          "brim_type","brim_width","filament_settings_id","enable_pressure_advance",
          "pressure_advance","retraction_length","retract_before_wipe"]:
    m = re.search(rf"^; {k} = (.*)$", g, re.M)
    print(f"{k:28} {m.group(1).strip() if m else '?'}")
print("M900 K:", sorted(set(re.findall(r"^M900 K([\d.]+)", g, re.M))))
print("M221 S:", sorted(set(re.findall(r"^M221 S(\d+)",   g, re.M))))
print("M104 S:", sorted(set(re.findall(r"^M104 S(\d+)",   g, re.M))))
```

No PowerShell, `Select-String` sobre array de linhas falha em varios casos que apareceram
nesta sessao. **Prefira Python** para parsear G-code.

Para verificacao maxima, **baixe o arquivo de volta da impressora** com `ftp-download.mjs`
e inspecione esse — nao a copia local.

## Montar 3MF de varias placas por codigo (validado 26/09/2026)

Para entregar "um arquivo, uma placa por kit" (ou cada kit no seu arquivo), sem o operador
arrumar nada na GUI:

1. **Estrutura:** `3D/3dmodel.model` so com `<components>` apontando para
   `3D/Objects/object_N.model` (uma malha por arquivo) e os `<item>` do `<build>`.
   Complete com `3D/_rels/3dmodel.model.rels`, `Metadata/model_settings.config` e
   `Metadata/project_settings.config`. Os demais itens podem vir de um 3MF do proprio
   Studio usado como modelo.
2. **Malha com vertices soldados** (`trimesh.load(..., process=True)` + `merge_vertices()`),
   centrada na caixa, com o `<item>` levando a posicao: `transform=... cx cy h/2`. Sopa de
   triangulos faz o Studio fechar furos (ver "Conferir furos" abaixo).
3. **Placas:** cada uma e um `<plate>` com `plater_id`, `plater_name` e os
   `<model_instance>` dos seus objetos. **Nome de placa sem `< > : / \ | ? * "`**: ao abrir, o
   Studio descarta o nome inteiro (`Plater::has_illegal_filename_characters`, 30/09/2026).
   Acento pode. Posicao: grade de `ceil(sqrt(n))` colunas, passo de
   1,2 × a mesa (256 → 307,2) em X e em −Y. Objeto de cada placa dentro da sua mesa.
4. **Processo:** copie o `project_settings` do modelo, iguale todas as chaves de processo
   ao perfil de sistema achatado (`flatten-profile.mjs process "0.20mm Standard @BBL A1"`)
   e liste em `different_settings_to_system[0]` so o que mudou de proposito. A GUI ignora
   ajuste nao listado.
5. **Validar fatiando todas as placas** no `bambu-studio.exe --slice 0 --outputdir <dir>
   arq.3mf`. O `result.json` traz `sliced_plates[]` com os `objects` de cada placa, o tempo
   e os gramas. Confira: numero de objetos por placa, `; FEATURE: Support` ausente em cada
   `plate_N.gcode` e furos abertos.

## Conferir furos e gravacoes no G-code

Antes de entregar arquivo fatiado, confira que nenhum furo saiu preenchido e que nenhuma
gravacao foi coberta:

- O leitor precisa interpolar arcos: o Studio usa `G2`/`G3`, com `I`/`J` relativos ao
  ponto atual.
- Use o **centro real** da feicao na mesa (posicao do objeto + posicao da feicao na peca).
  Em peca assimetrica, o centro da caixa engana: deu falso "furo preenchido" em todas as
  placas.
- **Controle positivo obrigatorio:** o mesmo leitor tem de achar extrusao na parede junto
  ao furo, ou na camada logo abaixo de uma gravacao. Criterio usado na gravacao: menos de
  5% dos pontos com plastico na ultima camada e mais de 85% na camada de controle.

## Enviar e acompanhar

```bash
cd ~/.claude/mcp-servers/bambu-mcp
node ftp-upload.mjs "<caminho local>" "NOME_REMOTO.gcode.3mf"
node mqtt-status.mjs
node watch-print.mjs            # em background; encerra ao terminar a peca
```

**Iniciar impressao e acao fisica: peca aval explicito.** Enviar arquivo e diferente de
iniciar — os dois merecem confirmacao separada.

- `.gcode` puro: inicia remoto por `gcode_file`, **sem** dialogo de filamento. O slot fica
  fixo nos `M620/M621 S<n>A` — use `patch-ams-slot.mjs` para trocar. **Nao** mexer no
  `S255`, que e marcador de descarregar.
- `.3mf`: inicia por `project_file`, **exige Developer Mode** na impressora. Em troca, da
  o dialogo de selecao de filamento. Foi por esta rota que a calibracao de PA foi
  aplicada corretamente — o vinculo de perfil funciona aqui.

## Desenho de peca de teste

- **Onde vai o tempo numa peca funcional pequena (medido 26/09/2026, PETG 16 mm³/s):**
  parede externa (~20%), preenchimento solido das chapas finas (~18%) e deslocamento entre
  as pecas da placa (~17%). Tirar o brim ganhou 2 min em 51, e preenchimento de 15% para
  10% ganhou 1 min. Topo com 4 camadas em vez de 5 nao mudou nada. Camada de 0,24 ganharia
  ~10%, mas muda o arredondamento de folgas pequenas: so depois dos encaixes aprovados.
- **O custo e dominado por numero de camadas**, nao por material. Tirar miolo economizou
  15% de filamento e **20 segundos**. Encurtar a peca e o que economiza.
- **Somar objetos a mesma placa e quase de graca** — ha folga ociosa por camada.
- Faixa de 6 mm (30 camadas) e pouco para separar sinal de coincidencia; use 10–20 mm.
- **Degrau/patamar nunca na fronteira entre faixas**: a troca cai na mesma camada e o
  patamar sai no valor da faixa seguinte. Ponha no meio.
- Escalonar sempre para dentro afina a peca ate desaparecer com muitas faixas; comece
  pela base mais funda.
- **Sulco negativo** (fatia recuada em todos os lados) separa faixas melhor que friso
  positivo. Rotulo deve respeitar a zona util: `BAND − altura do sulco − 2×margem`.
- **Brim: forcar `outer_only`, nunca `auto_brim`** — o auto dispensou brim em pilares
  7×7×36 mm.

## Fatiar por CLI com outro bico

Trocar `nozzle_diameter` e também `printer_settings_id`/`print_settings_id` no 3MF faz o
fatiador recusar: *"The selected printer is not compatible with the process preset in the
3mf"* (`return_code -17`, sem G-code). Manter os **nomes** de preset originais e trocar só
os **valores** (diâmetro, larguras de linha, vazão máxima) fatiou. Conferir no G-code.

## 3MF depois de "dividir em objetos" no Studio

O arquivo passa a ter vários objetos. Os nomes dos nós que o trimesh devolve **não** batem
com os do Studio (`PROVA_FINAL_8` no Studio era o nó `7`). Mapear pelo nome em
`Metadata/model_settings.config` + centro no `transform` do `<item>` em `3D/3dmodel.model`:
`modelagem-3d/scripts/componentes.py arquivo.3mf` faz isso.

## Conferir cada objeto depois de fatiar

`python scripts/extrusao_por_objeto.py plate_1.gcode placa.3mf` — peça, suporte, interface e
peça na **1ª camada** por objeto, com as regiões tiradas do próprio 3MF. Peça sem extrusão
na 1ª camada está flutuando e imprime inteira sobre suporte. Foi assim que se viu que a
interface da placa inteira estava só sob os cupons de colar. O script nomeia por posição:
identidade se confirma por geometria e render.

## Scripts desta skill (`scripts/`)

| script | mede |
|---|---|
| `teia_gcode.py` | bico aberto por faixa de viagem e por feição de destino |
| `extrusao_por_objeto.py` | peça/suporte/interface/1ª camada por objeto |
| `partida_gcode.py` | linha do tempo da partida: temperaturas, purga, retração, limpezas |
| `placa_ab.py` | monta placa 3MF com cópias, cada uma com ajuste por objeto; herda a configuração do 3MF impresso; `--girar` reproduz a orientação na mesa |
| `cobertura_suporte.py` | área de balanço com suporte e com interface perto, por região, cruzando malha e G-code |
| `perfil_camadas.py` | por faixa de Z: tempo de camada, viagens, retrações, **ventoinha na parede externa**; compara peça × cupom |
