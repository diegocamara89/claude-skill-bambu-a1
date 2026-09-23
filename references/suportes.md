# Suporte: por que não sai, e o que medir

Tudo aqui foi medido no G-code em 20/09/2026, numa escultura de 98 mm em PETG,
camada 0,08 mm, bico 0,4, suporte `tree_slim`. Vale a regra da skill: **conferir no
G-code, nunca no menu**. Os marcadores do Bambu são `; FEATURE:`, `; Z_HEIGHT:` e
`; LAYER_HEIGHT:`, **com espaço depois do `;`** — parser escrito para `;TYPE:` devolve
zero e parece "não tem suporte nenhum".

```bash
grep -o '^; FEATURE: .*' plate_1.gcode | sort | uniq -c | sort -rn
```

## Os dois ajustes que apagam o suporte onde ele mais falta

`support_on_build_plate_only = 1` e `support_critical_regions_only = 1`. Os dois
parecem inofensivos e são a causa mais comum de "liguei o suporte e mesmo assim
deformou".

Medido, mesmo arquivo, só trocando `critical_regions_only` de 1 para 0:

| região | com 1 | com 0 |
|---|---|---|
| cabeça com óculos | 962 | **16.702** |
| colar | 796 | **6.127** |
| vaso com flor | 3.028 | **8.246** |

E com ele ligado o fatiador gerou **zero** blocos `Support interface` na placa inteira —
os 5 níveis de interface configurados não existiam no G-code.

`on_build_plate_only = 1` é pior: manda gerar suporte só onde a coluna desce até a mesa.
Numa escultura, quase todo balanço fica **em cima da própria peça**. Numa impressão real
desse busto, óculos e antebraço saíram com **zero** extrusões de suporte, e foi
exatamente onde a peça falhou.

Como conferir se uma região tem peça embaixo, antes de culpar o fatiador: lançar um raio
vertical para baixo a partir dos pontos da região e ver se acerta a malha.

## Folga em Z é múltiplo da altura de camada

A folga é distância física, mas o fatiador a resolve em camadas. Pedir um valor que cai
entre camadas não entrega o que se pediu.

| camada | valores limpos |
|---|---|
| 0,20 mm | 0,20 · 0,40 |
| 0,12 mm | 0,12 · 0,24 |
| **0,08 mm** | **0,16 (2 camadas) · 0,24 (3 camadas)** |

A 0,08 mm, **0,12 é 1,5 camada e 0,20 é 2,5** — os dois valores "de manual" caem no
vão. `independent_support_layer_height = 1` ameniza, mas não há motivo para escolher
um múltiplo quebrado.

Aumentar a folga **piora o acabamento da face apoiada** — está na wiki do Orca e é real.
Começar em 0,16 e subir para 0,24 só se sair grudado.

## Interface é espessura, não contagem

Esta é a que mais engana. Medido pela extensão em Z das extrusões `Support interface`:

| ajuste no menu | interface que sai |
|---|---|
| `interface_top_layers = 2` | **0,080 mm — uma camada** |
| `interface_top_layers = 5` | 0,160 mm (2 camadas) |
| `= 5` com `interface_spacing = 0,2` | 0,240 mm (3 camadas) |

A recomendação corrente de "2 camadas de interface" pressupõe camada de **0,20 mm**, ou
seja 0,40 mm de interface. A 0,08 mm, pedir 2 entrega **um filme de uma camada**.

E filme fino é justamente o que esfarela. O mecanismo (fórum da Prusa, usuário Neophyl):
interface mais grossa e mais fechada **sai inteira em vez de se desfazer**, e quem fica
catando pedaço com alicate é quem quebra a feição delicada. A wiki do Orca diz que mais
camadas são "harder to peel off" — não é contradição: a **força** é maior, o **estrago**
é menor.

Mais camadas andam junto com espaçamento **apertado** (0,2), não frouxo. Os dois juntos
ou nenhum.

## Custo: zero

Sete variantes (folga 0,12/0,16/0,20/0,24 × interface 2/5 × espaçamento 0,7/0,2) na mesma
placa deram **122–132 min e 9,0–9,4 g**. Escolher bem não custa tempo nem filamento.

## PETG sobre PETG solda

É propriedade do material, não ajuste. A rota oficial da Bambu é **interface de PLA sobre
corpo de PETG** — mas exige trocador funcionando. **O BMCU está presente e quebrado**
(ver skill `bmcu-370c`), então essa rota está fora por enquanto. Em PETG, contar com folga
maior e aceitar acabamento pior na face apoiada.

Para peça delicada e de aparência, PLA é mais fácil em tudo: detalhe mais nítido e suporte
que solta.

## Receita validada em impressão (22/09/2026)

Impressa e aprovada: cabeça com óculos (aro de ~1 mm), colar de elos 1,7 mm e flor com
encaixe, PETG a 240 °C, camada 0,08, bico 0,4. O óculos saiu inteiro e o suporte soltou
sem quebrar a haste — primeira vez em quatro tentativas. A placa de cupons correspondente
fica na pasta do projeto de origem (arquivo `PROVA_FINAL.3mf`).

```
support_on_build_plate_only       0      obrigatório (o cupom engana — ver abaixo)
support_critical_regions_only     0      obrigatório
top_z_overrides_xy_distance       1      achado do operador — seção própria
support_type / support_style      tree(auto) / default
support_threshold_angle           15     menor = MENOS suporte
support_object_xy_distance        0,7    contato lateral; 0,35 -> 0,7 = -39% na armação
support_top_z_distance            0,12   regra aditiva do operador: 1 camada + 0,04
support_bottom_z_distance         0,08   1 camada
support_interface_top_layers      5
support_interface_spacing         0
support_interface_speed           40
independent_support_layer_height  0
wall_generator                    arachne (detect_thin_wall fica cinza e em 0 — normal)
outer_wall_line_width             0,42   NÃO 0,33 (valor de terceiro, nunca testado)
```

### `top_z_overrides_xy_distance` é o "Z overrides X/Y" do Cura

Existe no Bambu Studio com esse nome. A chave **não tem "support" no nome**: filtro por
`support*` não acha — foi assim que eu afirmei, errado, que a opção não existia.

Medido na mesma placa de 9 peças, só trocando essa chave:

| | 0 | 1 |
|---|---|---|
| corpo de suporte | 16.940 mm | 10.774 mm (-36%) |
| óculos avulso | 1.509 mm | 433 mm (-71%) |
| interface | 9.441 mm | 9.422 mm (igual) |
| folga lateral p5, óculos | 0,76 mm | 1,09 mm |
| folga lateral p5, flor | 0,06 mm | 0,41 mm |

Menos entulho, mesmo contato com a peça, folga lateral igual ou maior. Único ponto mais
apertado: na cabeça, o pior ponto isolado caiu de 0,62 para 0,31 mm.

### Limiar de ângulo: menor = menos suporte

O fatiador apoia o que fica **abaixo** do limiar (inclinação medida da horizontal). Com 15
só leva suporte o que é quase teto. De 40 para 15 cada cupom perdeu 30–60 mm² de área
apoiada, toda na faixa 15–40°, que a impressora vence sozinha. Custo: -3 min.

### O que solda é a interface, não a quantidade de suporte

Três flores iguais em orientações diferentes. A única que soldou foi a única com
`Support interface` (159 mm, junto com 4.370 mm de corpo). A de 2.667 mm **sem** interface
saiu no alicate. Parede quase vertical (aro de óculos, ~12° de balanço) não gera interface
em nenhuma configuração — ali quem governa é `xy_distance`.

### `on_build_plate_only = 1` passa no cupom e falha na peça

Em cupom baixo tudo está perto da mesa e o suporte "só da mesa" alcança (diferença de 6%).
No busto inteiro o óculos fica a 85 mm e recebeu **zero** extrusões. Nunca validar essa
chave com cupom baixo.

### Árvore com pouca interface não causa crosta por si só (23/09/2026)

Cupom da barra de uma manga, duas cópias na mesma placa: A em árvore (82% apoiado, **20% com
interface** — idêntico ao da peça que saiu com crosta) e B em grade (94% com interface). **As duas
saíram perfeitas**; a grade deu mais trabalho para soltar. Não receitar "trocar para grade" ou
"mais interface" contra fiapo e crosta sem outra evidência — a diferença entre peça e cupom estava
em outro lugar (ver `armadilhas.md`, "o que um recorte muda").

Montar e medir esse tipo de teste: `scripts/placa_ab.py` (cópias com ajuste por objeto) e
`scripts/cobertura_suporte.py` (apoio e interface por região, no G-code).

### Refutado

- `reduce_infill_retraction_mode = Disabled` (valor de um especialista): 3.998 mm de bico
  aberto antes e depois, viagem por viagem. Não mexe em nada.

### Sobre 0,12 de folga a camada 0,08

A seção "Folga em Z é múltiplo" acima diz que 0,12 é 1,5 camada e cai no vão. A regra
aditiva do operador (camada + 0,01–0,04, lida nos três vídeos de referência) deu 0,12, e a
peça saiu boa. Não houve teste lado a lado 0,12 x 0,16 — nenhum dos dois está provado
superior, mas 0,12 não fez mal.

## Ponto de partida anterior (20/09 — superado pela receita acima)

```
support_on_build_plate_only    0        obrigatório
support_critical_regions_only  0        obrigatório
support_remove_small_overhang  0
support_style                  tree_slim
support_threshold_angle        40
support_object_xy_distance     0,5
support_top_z_distance         0,16     (2 camadas; 0,24 se sair grudado)
support_bottom_z_distance      0,16
support_interface_top_layers   5        (= 0,16 mm reais)
support_interface_spacing      0,2      (junto com o de cima, nunca sozinho)
thick_bridges                  0
wall_generator                 arachne
enable_prime_tower             0        com um filamento só
```

`wall_generator = classic` merece linha própria: ele só faz parede de largura inteira.
Feição de ~0,9 mm é 2,1 filetes de 0,42 e **não cabe** — o classic deixa vão ou some com
ela, sem avisar. Numa peça cujo conserto foi engrossar feição fina até 0,9 mm, isso
desfaz metade do trabalho em silêncio.

## Peças próximas fazem o fatiador recusar

Três peças a 6–7 mm uma da outra na mesa: **"G-code conflicts detected after slicing"**
assim que o suporte foi habilitado direito. Com o suporte capado não dava erro — o erro
só apareceu quando o suporte passou a existir. Afastar para ~40 mm resolveu. Com um
filamento só, desligar a torre de purga também libera espaço.

## O que nada disto mede

**Força de remoção.** O G-code diz onde há suporte, quanta interface e qual a geometria.
Não diz se sai fácil. Isso exige imprimir. Existe modelo de teste pronto de Top Z Distance
no MakerWorld (presets de 0,04 a 0,50), e corpo de prova recortado da própria peça também
serve — é mais barato errar em 1 h do que em 12 h.

Acervo com as fontes e as medições: notebook **"Suportes 3D — Bambu A1 (evidência)"** no
NotebookLM.
