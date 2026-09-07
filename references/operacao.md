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
