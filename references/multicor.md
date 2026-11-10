# Multicor com BMCU: baratear trocas, conferir pintura, medir

Caso de origem: Grogu nas 3 poses (MakerWorld, 3 figuras de 100 mm numa placa, pintadas em bege/verde/preto),
09/10/2026. Tudo abaixo foi medido no CLI do Bambu Studio 02.08, uma variante por vez, com
`scripts/resumo_fatiamento.py`. Projeto: `D:/Diego/Pessoal/3D/Modelagem 3D/Grogu poses/ESTADO.md`.

## Onde vai o custo

No original (PLA, 0,16, 3 paredes, torre): 13 h 15 e 225 g, com **174 trocas**. Delas saíram ~7 h
(purga 3,4 h + manobra de troca 2,8 h + torre 1,3 h) e 84 g (purga 57 g + torre 27 g). **Cada troca
custa ~100 s e ~0,3 g** (bateu em PLA e em PETG). Trocas só acontecem nas camadas com mais de uma
cor: no Grogu, 62–85 mm (mãos junto ao rosto e olhos). Abaixo, só roupa; acima, só cabeça.

## Alavancas medidas (cada uma isolada, sobre o original)

| Mudança | Trocas | Tempo | Peso | Risco |
|---|---|---|---|---|
| tirar ilha de pintura que cria camadas próprias | −14 | −23 min | −4 g | nenhum, se for erro |
| olhos sem preto (pintar à mão) | −49 | −1 h 30 | −18 g | estético; trabalho manual |
| camada 0,16 → 0,20 | −33 | −2 h 15 | −12 g | degrau nas divisas e no rosto |
| 3 → 2 paredes | 0 | −45 min | −30 g | casca mais fina |
| sem torre de purga | 0 | −1 h 20 | −22 g | 1ª extrusão após troca cai na peça |
| purga 100% → 70% | 0 | −22 min | −13 g | bege manchado depois do verde |
| ângulo de suporte 25 → 18 / 35 | 0 | 0 / +41 min | +1 / +7,5 g | árvore não é monotônica |

**Pacotes não somam:** "seguro" (ilha + 0,20 + 2 paredes) mediu −3 h 10 contra −3 h 24 somado (−7%);
"máximo" (tudo) mediu −5 h 20 contra −6 h 34 (−19%). Meça o pacote.

Por que figuras na mesma placa: as faixas de troca das três se sobrepõem, então uma troca serve às
três na mesma camada. Separadas em placas, quase dobrariam as camadas com troca.

## Medido e descartado

- **Purgar no preenchimento** (`flush_into_infill`, giroide 15%): purga igual (18,5 g), 1ª extrusão
  após troca no mesmo lugar, e +87 g e +3 h de preenchimento. A A1 purga na calha.
- **Objeto como "torre"** (purgar dentro de um objeto): o objeto sai com as cores misturadas, então não
  pode ser peça de exposição. E precisa subir até a altura das trocas com área para engolir ~0,2 cm³ por
  camada: no Grogu, ~32×32 mm maciço até 85 mm, ~110 g para aproveitar ~20 g de purga. (Calculado.)
- **Camada variável por arquivo** (`layer_heights_profile.txt`): ignorado pelo CLI (ver armadilhas).
  Fazer na interface do Studio, se quiser.
- **"Simplificar o modelo"** que o Studio sugere acima de 1 milhão de triângulos: não ganha nada na peça
  (triângulos menores que o filete) e, no PrusaSlicer de onde o Bambu veio, apaga a pintura. Fatiar
  4,3 milhões de triângulos levou 72 s no CLI. (Perda de pintura no Bambu: não testada.)

## Sem torre: o risco medido

`resumo_fatiamento.py` mostra onde cai a 1ª extrusão depois de cada troca. Com torre: 89 de 89 na torre.
Sem torre: 82 na parede interna, 6 na externa (à vista), 1 no suporte. Em PETG, que escorre mais, o risco
de bolinha ou mancha nessas externas é maior. Custo da torre no PETG máximo: +56 min e +26 g.

## Conferir a pintura

`scripts/pintura_3mf.py projeto.3mf --camada 0.2` lista, por objeto, as regiões de cada cor e quais
**criam camadas de troca sozinhas** (são a única ocorrência da cor naquelas alturas). No Grogu a primeira da
lista era o erro: verde de 2,9 mm² sob a manga, 12 camadas próprias. Fragmentos menores que um filete
(0,18 mm²) são descartados pelo fatiador e não geraram troca: o script os ignora.

Depois, **ver** cada suspeita: `scripts/render_pintura_3mf.py` (dentro do Blender) marca em magenta e
conta os pixels por vista, inclusive de baixo. "Escondido" só se der 0 em todas, e a imagem confirma.
O auditor não vê erro colado na região principal (roupa pintada de pele encostada na pele): para isso,
render das cores e comparação entre figuras e lados.

## Limpar a pintura (corrigir, não só apontar)

`scripts/limpa_pintura_3mf.py entrada.3mf saida.3mf --proteger 4 [--divisa 1,2]` grava uma cópia com:
- **ilhas** menores que `--ilha-min` (0,5 mm²) na cor vizinha dominante (vizinha que também é ilha não vota);
- com `--divisa A,B`, a divisa entre as duas cores puxada para o fundo do vinco côncavo (Dijkstra entre os
  miolos, custo alto ao cruzar vinco). Só serve onde o modelo tem vinco na divisa.

Medido no Mini Jesus (1,59 mi triângulos, 15/10/2026): original do autor 2.143 → 30 regiões (eram os pontos
brancos no cabelo marrom que o dono viu no Studio), fatiou igual e com 3 trocas a menos. Faixa serrilhada:
divisa branco/marrom de 675 → 170 mm (a limpa à mão deu 153). Proteja o que é pequeno de propósito (olhos).
Sobra sem mudar: casca solta minúscula da malha (não tem vizinha), que o fatiador descarta.

**Não copie rótulo de uma malha reduzida para a original** por vizinho mais próximo: a borda serrilha (foi o
que gerou a faixa de 675 mm). Marque na própria malha que vai ser impressa, ou limpe com `--divisa` depois.
Na malha densa, vinco arredondado tem ângulo pequeno entre faces vizinhas: separar região só por ângulo vaza
para o manto inteiro (medido: 1.018 mm² em vez de 308); na reduzida de 160 mil o mesmo limiar separou certo.

**Malha reduzida não é de graça no suporte:** 160 mil triângulos deu o mesmo suporte do original (0,3 g por
boneco); 50 mil deu 3× (0,9 g), o que somou ~10 h numa mesa de 117. Reduza para ~10% e meça o suporte.

## Uma cor a mais × uma cor que já existe (Mini Jesus, 16/10/2026, mesas de 30, CLI)

Trocas só existem em camada com mais de uma cor. Uma região nova (a faixa do manto) custa as camadas em que ela
põe uma cor que ainda não estava ali — não a área dela.

| Faixa | Tempo | Total | Trocas |
|---|---|---|---|
| sem faixa | 12,39 h | 142,9 g | 124 |
| cor pele (já usada nas mãos e no rosto) | 15,01 h | 169,0 g | 181 |
| marrom (já usada no cabelo) | 16,17 h | 195,6 g | 202 |
| dourada no 4º slot + olhos marrons, sem preto | 16,49 h | 192,0 g | 209 |

- Purga por troca menor não salva se a cor nova não divide camada com ninguém: o dourado volta ao branco com 438 mm³
  (o marrom com 585), mas criou trocas pele↔dourado e marrom↔dourado e empatou.
- Purga vai quase toda no **escuro → claro** (marrom → pele 534, marrom → branco 585 mm³: ~60% do total).
- `scripts/purga_bambu.py` reproduz a fórmula do Studio (HSV + luminância, +92 mm³ do bico na A1) para
  simular uma cor antes de ter o rolo.
- A purga é por mesa: 30 bonecos com faixa custaram R$ 0,65 cada, 64 custaram R$ 0,49.
- Largura de linha não muda trocas; purgar no preenchimento ou num objeto não muda nada na A1 (purga na calha):
  medido com objeto pintado e sem pintura, com e sem torre.

## Objeto no lugar da torre (Mini Jesus, mesa de 36, 17/10/2026, 6 fatiamentos)

Objeto de sacrifício com `flush_into_objects=1`, altura de toda a faixa com troca (aqui 42 mm), sem torre.
Contado **por objeto** (rótulo do G-code), não por tipo de extrusão.

| Mesa de 36 (203 trocas; 49 camadas têm 2 trocas) | Tempo | Total | 1ª extrusão depois da troca |
|---|---|---|---|
| torre 35 mm | 18,13 h | 216,0 g | torre 202/202 |
| 1 bloco 22 mm, filamento 1 (branco) | 17,61 h | 205,6 g | bloco 104; bonecos 99 (28 na parede externa) |
| 2 blocos 15 mm, filamento 1 | 17,66 h | 207,1 g | bloco 104; bonecos 99 (28) |
| **1 bloco 22 mm, filamento 3 (preto, quase sem uso)** | 17,62 h | 205,7 g | **bloco 150**; bonecos 53 (16) |
| 1 bloco 30 mm maciço, filamento 3 | 18,45 h | 245,8 g | bloco 150; bonecos 53 (16) |
| 2 blocos 15 mm, filamento 3 | 17,67 h | 207,2 g | bloco 150; bonecos 53 (16) |

- **Filamento do objeto = um que a camada quase nunca usa.** Com o branco, nas camadas que começam no branco o bloco
  é impresso como objeto normal **antes** da troca e não sobra nada para ela (104 → 150 só por trocar para o preto).
- **Um objeto serve a uma troca por camada**, qualquer tamanho e quantidade: o bloco maciço (176 mm³ por camada, mais
  que a purga de 111) e o segundo bloco não mudaram nada; os dois blocos saem juntos depois da mesma troca. As
  segundas trocas das camadas com 2 trocas caem nos bonecos. (Explicação anterior — "volume da purga maior que o
  objeto" — foi derrubada por este teste.)
- **Sem torre**, a purga na calha não muda (~77 g em todos): o objeto só recebe a 1ª extrusão.
  Confirmado com objeto grande (60×60×121 mm, 2 Jesus, 17/10/2026): calha 48,9 g sem objeto, 52,2 g com ele; total
  56,7 → 98,6 g, 5h42 → 8h23. **Objeto manchado não prova purga absorvida**: com "purgar neste objeto" ele é impresso
  com o filamento que estiver carregado (por isso sai colorido). Comparar com "purgar no objeto" desligado engana: aí
  o objeto vira cor própria e dobra as trocas (204 → 391). A referência certa é a mesa **sem** o objeto.
- **Com torre, o limite é o volume do objeto em cada camada e a altura dele** (8 Jesus + prendedor, 17/10/2026): o
  prendedor engoliu tudo até 21 mm (parte larga) e quase nada acima (~58 mm³ por camada); as trocas iam até 40 mm.
  Canaleta 50,1 → 36,5 g; esticado até 41 mm → 22,2 g. Duas trocas na mesma camada também cabem, se houver volume.
  Para zerar a canaleta, o objeto precisa alcançar a última troca com volume por camada ≥ a purga daquela camada.
- **Objeto de sacrifício sob medida** (`scripts/gera_sacrificio.py` + `scripts/insere_obj.py`): lê a purga por camada
  de um fatiamento com torre e sem objeto, gera prisma escalonado (45°, sem balanço) com volume ≥ purga × margem, e
  insere no 3MF (filamento 3, purga no objeto, 100% zig-zag). **Uma peça recebe uma troca por camada**: gere uma por
  `--troca 0`, `--troca 1`. Cada malha nova com `objectid` próprio (com dois `id="1"` o Studio usa a mesma malha nas
  duas). 8 Jesus, purga 70%, torre: canaleta 50,1 → 6,8 g (1 peça de 108 g) → 4,4 g (2 peças, 129 g); total
  98,8 → 161 / 178 g. A purga alterna ~100/300 mm³ por camada e a peça não pode alternar de tamanho, então o objeto
  pesa ~2× a purga que engole: **só compensa se o objeto for útil**. Offset = topo da jangada (1,6 mm com 5 camadas).
- **Objetos do dono como sacrifício (17/10/2026)**: `raft_layers=0` num objeto + torre ligada = CLI recusa (-51,
  "incorrect slicing parameters"); a jangada tem de ser igual em todos. A soma do volume por camada de **todos** os
  objetos de sacrifício tem de cobrir a purga **da camada inteira** (2 trocas): a 1ª troca já consome os objetos e a 2ª
  vai para a canaleta. Conferir sozinho: coluna "Corado" (= Flushed, purga na canaleta) no resumo do fatiamento.
- **Com a torre ligada** o "purgar neste objeto" passa a tirar purga da calha (o fórum da Bambu já dizia: sem torre o
  recurso não age). Medido na mesa de 36: bloco 22 mm a 100% **retilíneo** (o padrão "relâmpago" do perfil ignora a
  densidade) recebeu 95 mm³ por camada (26,5 g) e a purga caiu 76,3 → 61,8 g; o total **subiu** 216,0 → 227,0 g e o
  tempo 18,13 → 18,43 h. A purga absorvida = volume do objeto: ela muda de lugar, não some. Só compensa se o objeto
  de purga for algo que se imprimiria de qualquer jeito e aceita cores misturadas. Um boneco a mais (~3,4 g) absorve
  ~5% da purga de uma mesa (~76 g) e sai manchado.
- **Clone pintado do próprio boneco** (método de vídeos do Instagram: clone + "preenchimento, este objeto, suporte"
  nas opções de purga + torre desligada), testado em 1 Jesus, 17/10/2026, CLI 02.08: **sem torre o fatiador ignora o
  clone** (purga 74,0 g igual, 0 trocas nele, mesmo com o clone a 100%). **Com torre**: purga 74,0 → 70,4 g, total
  91,5 → 91,6 g com um boneco a mais (o clone sai "de graça" em material, +14 min), mas a parede externa do clone
  troca cor (pele 0,71 → 1,13 g, branco 0,82 → 0,49 g): manchado. Nos vídeos o modelo é maior e tem miolo; o Jesus
  de 37 mm é quase só casca.
- `wipe_tower_no_sparse_layers=1` (torre só nas camadas com troca, "modo objeto"): torre precisa ficar longe
  ("Object conflicts were detected" a 30 mm); no Jesus inclinado deu −0,6 g, porque as trocas começam embaixo.
- O objeto sai com as cores misturadas.

## Sequência de trabalho

1. `pintura_3mf.py` → suspeitas de pintura; render das suspeitas; `limpa_pintura_3mf.py` se houver ilhas.
2. Fatiar o original no CLI e `resumo_fatiamento.py` → trocas por faixa de altura, purga, torre.
3. Uma variante por vez (`ajusta_3mf.py`), medir, e só então o pacote escolhido; medir o pacote.
4. `filete_no_ar.py` no pacote final (suporte) e **abrir no Studio** para conferir que os ajustes vieram.
