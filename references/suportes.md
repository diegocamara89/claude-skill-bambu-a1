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

A 0,08 mm, **0,12 é 1,5 camada e 0,20 é 2,5**: caem no vão. No código do Bambu (28/09/2026): a
folga arredonda para a camada mais próxima (Slicing.cpp), salvo com
`independent_support_layer_height = 1`; o suporte em **árvore** conta a folga em camadas inteiras
(TreeSupport3D, `z_distance_top_layers`); o **normal** usa a folga exata (SupportMaterial.cpp).
A receita abaixo usa 0,12 a 0,08 (regra do operador: 1 camada + 0,04) e a peça saiu boa; não
houve teste lado a lado contra 0,16.

Aumentar a folga **piora o acabamento da face apoiada** — está na wiki do Orca e é real.
Começar em 0,16 e subir para 0,24 só se sair grudado.

### A face apoiada é ponte

A 1ª camada sobre suporte com folga > 0 é `Bridge` (PrintObject.cpp, `stBottomBridge`). Face de
baixo com fios soltos ou fendas sobre suporte em PETG: aplicar a receita de `ponte-e-teto.md`
(fluxo 1,5, 10 mm/s, ventoinha 100%) antes de mexer em folga ou interface.
`enable_support_ironing` existe, mas só aparece no modo Desenvolvedor.

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
corpo de PETG** — exige trocador funcionando. **O BMCU está funcionando** (confirmado em
09/10/2026; ver skill `bmcu-370c`), então essa rota está disponível. Sem ela, em PETG, contar
com folga maior e aceitar acabamento pior na face apoiada.

Para peça delicada e de aparência, PLA é mais fácil em tudo: detalhe mais nítido e suporte
que solta.

## Receita para escultura em PETG, camada 0,08 (validada em impressão, 22/09/2026)

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

### A mesma receita em camada 0,20 (Grogu PETG, 09/10/2026 — fatiada, impressão pendente)

Iguais: árvore(auto), mesa só 0, críticas só 0, `top_z_overrides_xy_distance` 1, xy 0,7, interface
5 / espaçamento 0 / 40 mm/s, `independent_support_layer_height` 0, arachne, filete externo 0,42.
Convertidos: **limiar 30** (20 deixou a parte de baixo das orelhas no ar, medido com `filete_no_ar.py`),
**folga de cima 0,24** (regra 1 camada + 0,04; a árvore conta camadas inteiras, então vira 1 camada),
**folga de baixo 0,20**. Custo do suporte: 28 g, contra 22 g do arquivo original (PLA, 0,16, 25°, interface de fábrica). Se soldar na
roupa, próximo passo: folga 0,40 (2 camadas).

`wall_generator = classic` só faz parede de largura inteira. Feição de ~0,9 mm é 2,1 filetes de
0,42 e **não cabe**: o classic deixa vão ou some com ela, sem avisar. Por isso arachne.

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

**O limiar depende da altura de camada.** O que importa é quanto cada camada avança para fora
(camada ÷ tan(ângulo)): 15° a 0,08 avança 0,30 mm; 20° a 0,20 avança 0,55 mm, mais que um filete.
Medido no Grogu em PETG a 0,20 (09/10/2026): limiar 20 deixou a parte de baixo das orelhas no ar
(até 11 camadas, nas 3 figuras); limiar 30 apoiou, com o mesmo tempo e peso. Para avanço de ~0,3 mm
por camada: 0,08 → 15°; 0,12 → 22°; 0,16 → 28°; 0,20 → 34°. Não copiar o 15/20 da receita abaixo
para outra camada sem refazer essa conta.

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

## Figura de cabeça para baixo: a cúpula que encosta na mesa (Mini Jesus, PETG, 16/10/2026)

De cabeça para baixo a figura gasta menos suporte (100 contra 194 mm² de balanço) e o rosto fica livre, mas o topo
da cabeça é uma cúpula: a camada 1 é só uma volta de 3,9 × 2,8 mm, e as camadas 2–3 saem **no ar** (parede no ar
+ ponte, medido no G-code baixado do cartão). Com "suporte só em regiões críticas" não houve suporte nenhum: disco
áspero com borda no topo da cabeça.

| Tentativa | Resultado |
|---|---|
| achatar 0,64 mm do topo | 1ª camada vira disco de 7 mm; **recusado** pelo dono ("ajuste feio": disco liso visível de cima) |
| reforço pintado só no topo, suporte direto da mesa | apoia 83% da borda, mas é suporte de 0,6 mm colado à mesa: dono recusou ("vai grudar tudo") |
| jangada 3 + reforço, folga 0,24 (padrão do raft é 0,10: solda PETG) | 100% da borda apoiada, folga ≥ 0,24 — não impresso |
| **inclinado** (X −158,35°, Z 180°, receita de comentário no MakerWorld) + jangada 8 / contato 0,24, suporte normal snug 20°, Z sup 0,24 / inf 0,20, interface 5/3, camada 0,20 | **"quase perfeito"**; só anéis de degrau no topo da cabeça |
| a mesma + camada 0,08 nos primeiros 2 mm (faixa de altura) | **falhou 8 vezes** na mão do dono: o cabelo não pega no suporte. Camada fina sobre interface não serve |

- Em pé o autor imprime, e nos comentários "20 impressos, 18 cabeças quebraram" ao tirar a árvore: não ir por aí.
- Faixa de altura por código: `Metadata/layer_config_ranges.xml` (`<object id="1"><range min_z max_z>` com
  `<option opt_key="layer_height">` ou `wall_loops`). O CLI respeita (conferido em `; LAYER_HEIGHT`).
- 2 paredes no boneco e 3 só na faixa do pescoço (Ø 3,4 mm): pescoço idêntico ao de 3 paredes, −95 s por boneco.
