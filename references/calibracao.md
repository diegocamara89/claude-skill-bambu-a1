# Calibracao de filamento e diagnostico de defeito

## Parte 1 — Receita para filamento novo

Ordem oficial da Bambu, e **a ordem importa**: cada etapa depende da anterior.

### Pre-requisito, uma vez so

Nas configuracoes do **Bambu Studio**, habilite **Modo Desenvolvimento**. Sem isso as
calibracoes **manuais** nao aparecem no menu. (Nao confundir com o Developer Mode da
impressora, que e outra coisa e nao e necessario.)

### 0. Anote a temperatura do fabricante

Do rotulo do rolo, nao do perfil do fatiador. Eles divergem: o Generic PETG do Orca diz
faixa 220–270, mas o rotulo do Masterprint diz 230–260. **O rotulo vence.**

### 1. Criar o perfil do filamento

Filamentos do Projeto → criar personalizado → tipo + perfil generico + bico 0.4.
Nome que se reconheca em tres meses: `PLA Sunlu vermelho`, nao `Brand PLA`.

Em **Dispositivos**, diga a impressora qual filamento esta no slot.

### 2. Temperatura

Calibracao → **Temperatura**, na faixa do fabricante. Imprimir, escolher a melhor faixa.
Gravar no perfil (os **dois** campos: camada inicial e demais) e salvar.

Observado: PLA Sunlu no **piso** da faixa (190 de 190–240); PETG Masterprint em 240 (de
230–260; a torre de 230–250 saiu toda limpa). Nao presuma o meio da faixa.

### 3. Pressure advance (Dinamica de Fluxo)

Calibracao → **Dinamica de fluxo**. Manual (passo 0,002) ou Auto — a Auto resolve a
maioria dos casos.

> **O ponto mais importante desta skill:** rode a calibracao **na temperatura escolhida
> na etapa 2**, selecionando o preset ja alterado no primeiro passo do assistente
> ("Predefinido"). Se rodar no padrao, o K nao serve.

O K exigido **sobe muito quando a temperatura cai**:

| Material | Temperatura | K medido |
|---|---|---|
| PLA Sunlu | 220 °C | 0,027 |
| PLA Sunlu | **190 °C** | **0,043** |
| PETG Masterprint | 255 °C | 0,048–0,061 (disperso) |
| PETG Masterprint | **230 °C** | **0,082–0,084** (consistente) |

Depois, em Dispositivos → **Perfil PA**, vincule o perfil criado ao slot. Feito isso,
nao e preciso escolher calibracao na hora de imprimir.

**Dispersao entre slots do mesmo material indica temperatura de medicao alta demais, nao
defeito de hardware.** A 255 °C tres cores de PETG deram 27% de diferenca; a 230 °C, os
mesmos tres slots deram 2,4%. Nao conclua problema de alimentacao a partir da primeira.

### 4. Vazao (Flow Rate)

Calibracao → **Vazao** → Manual, duas passagens: escolher a superficie mais lisa em cada
uma. Antes de salvar, apagar o sufixo do nome para substituir o perfil existente.

Formula da passagem 1: `novo fluxo = fluxo atual × (100 + modificador) / 100`.

Afeta **dimensao**, nao acabamento. **Reduzir vazao piorou as bolinhas** nesta maquina —
nao use vazao para tentar consertar superficie.

### 5. Retracao e velocidade volumetrica maxima

So em caso especifico (TPU, ou teia persistente). Nesta A1, aumentar retracao para
1,2 mm com wipe 70% **criou cicatriz de costura** visivel. O padrao 0,8 / 0% e adequado.

Cuidado com estatistica de ecossistema: `retract_before_wipe = 70%` e o valor mais comum
entre 691 perfis de maquina, mas aqueles perfis sao de **outras** maquinas. O `0%` da A1
e ajuste do hardware dela, nao descuido.

---

## Parte 2 — Diagnostico de defeito

### Antes de qualquer teste

1. **Limpe o bico** (escova de latao a ~200 °C, ou cold pull) e confira que o HMS nao
   acusa residuo. Cada impressao herda o residuo da anterior; sem isso, pecas da mesma
   serie partem de estados diferentes e a comparacao nao vale.
2. **Pergunte a condicao de origem** do defeito: temperatura, paredes, miolo, material.
   Sem isso voce projeta teste na condicao errada.
3. **Confira as calibrações da Parte 1 e aproveite as já realizadas.** Torre boa com
   topo ruim em peça pequena pede também comparação de resfriamento e tempo de camada;
   não é motivo, por si só, para repetir a torre ou alterar a temperatura.

### Arvore por sintoma

| Sintoma | Suspeito principal | Contraprova |
|---|---|---|
| Bolinhas em superficie lisa | temperatura alta **+** PA baixo | curva de temperatura na peca real |
| Teia entre detalhes | temperatura baixa; retracao | sobe com temperatura, nao desce |
| Costura marcada / cicatriz vertical | PA baixo, ou retracao excessiva | reverter retracao ao padrao |
| Peca/perna descolando | residuo no bico batendo; aderencia | limpar bico; conferir chapa |
| Camada inicial ruim | tipo de chapa errado no perfil | `curr_bed_type` no G-code |
| Topo deformado em peça pequena, apesar de torre boa | tempo insuficiente para resfriamento entre camadas | alterar só o limiar de tempo de camada na peça que reproduz o defeito |

### Peça pequena: torre boa, topo ruim

**Caso HB20, 23/10/2026 — resultado físico RELATADO pelo usuário.** A peça em PETG
saía boa; em ABS, o topo saía ruim apesar da torre de temperatura boa. Segundo o dono,
uma tentativa com camada de 0,08 mm e passar ferro também não resolveu. Após a orientação
de mudar o limiar de tempo de camada de **3 para 12 s**, confirmou: "Era isso mesmo.
Resolveu." Isso registra uma solução para esta peça/perfil, não uma receita universal
para ABS nem uma calibração completa do rolo.

**Onde ajustar no Bambu Studio, conforme captura conferida:** Filamentos do projeto →
lápis do ABS → Resfriamento → "Ventilador de refrigeração parcial" → linha
"Limite máximo de velocidade do ventilador" → campo **"Tempo de camada"** à direita.
O campo de 3 s corresponde a `slow_down_layer_time`; foi orientado mudar para 12 s,
mantendo os limites de ventoinha de 10–20%, o tempo de 30 s da linha do limite mínimo
e marcada "Impressão lenta para melhor resfriamento da camada".

**Como aplicar o aprendizado:** diante dessa combinação de sintomas, comparar primeiro
os tempos de camada e o resfriamento dos perfis. Testar uma variável por vez na própria
peça. Camada menor melhora os degraus das inclinações; passar ferro retrabalha o topo,
mas nenhum deles garante corrigir deformação térmica. O limiar de tempo participa do
controle de desaceleração e ventilação: manter as porcentagens não prova que o comando
da ventoinha permaneceu idêntico. A velocidade mínima pode impedir alcançar 12 s;
conferir o tempo efetivo na prévia/G-code, sem apresentar o limiar como pausa obrigatória.

**Alcance da prova:** acúmulo de calor é a explicação compatível com o resultado;
temperatura local, duração efetiva das camadas e G-code final não foram medidos.
Não atribuir o defeito ao material ou à umidade apenas pelas fotos. A torre boa não
reproduz necessariamente o percurso e o tempo de camada dessa peça pequena.

**Conferir qual impressão está sendo analisada:** o `HB20_R02.3mf` recebido tinha
0,16 mm, passar ferro desligado e nenhum G-code, diferente da tentativa relatada.
O campo de 3 s foi depois confirmado na captura do Studio. Consulta ao estado da
impressora e leitura do cartão falharam por timeout: não foram verificações dos ajustes
impressos. Distinguir perfil salvo, tela atual e G-code executado; se o acesso falhar,
dar a recomendação como teste de hipótese, sem afirmar leitura da impressora ou exigir
que o usuário refaça uma calibração já boa.

### Regras de metodo, aprendidas errando

**A peca real e o instrumento, nao a torre.** Torres saiam limpas a 205 °C enquanto a
peca real tinha 40 bolinhas na mesma temperatura. Motivo medido: a peca tem ~8 movimentos
em arco por camada; a torre, ~1,6. Erro de PA se manifesta em aceleracao e desaceleracao —
prisma reto quase nao exercita o parametro.

**Diff de configuracao entre peca limpa e peca suja e o movimento de maior valor.** Duas
pecas que diferem em uma linha ensinam mais que qualquer varredura. Requer ter uma peca
limpa primeiro.

**A geometria da peca de teste pode ser a fonte do defeito.** Digitos em relevo sao
dezenas de partidas e paradas por camada; patamares escalonados criam superficie de topo
e mudam tempo de camada.

**Nao mude duas coisas entre variantes.** Cubos 25×25 comparados com torres 18×18
introduziram tempo de camada como variavel escondida.

**Registre a expectativa antes do resultado.** Evita que a interpretacao se acomode ao
que se torce para ver.

**Prefira medicao a julgamento visual.** A torre de PA "deu" 0,02 no olho; o sensor da
maquina deu 0,043 e era esse o certo. Varredura visual serve para explorar, nao concluir.

**Teste em peca sem defeito nao mede nada.** A torre de PA varreu 0,00–0,06 numa peca que
ja saia limpa e nao mostrou diferenca — e isso foi lido erradamente como "PA e irrelevante".

**Conselho de LLMs acerta metodo e erra causa.** Um council apontou 4 causas (BMCU,
costura, umidade, sobre-extrusao); o experimento seguinte derrubou as tres primeiras.
Use para desenho de experimento, nao para diagnostico.

**Diagnosticar pelo G-code que foi IMPRESSO, baixado do cartão.** O Studio salva o projeto
com o que o operador mudou antes de mandar (limiar de suporte, giro na mesa). Um refatiamento
local não é o arquivo impresso. Caso de 23/09/2026: dois diagnósticos (meu e de um verificador
externo) saíram de um refatiamento com limiar 15; o impresso tinha limiar 20 e a peça **girada
90°** na mesa. O arquivo impresso fica no cartão em `/cache/<projeto>_plate_1.gcode`
(`bambu-mcp/ftp-download.mjs`). Alinhar ao projeto pelas paredes externas antes de cruzar com a
malha.

**Um teste só serve se primeiro reproduzir o defeito.** Cupom recortado da peça que sai limpo
enquanto a peça sai ruim não aponta causa: só descarta o que foi mantido igual. Antes de testar
a correção, o cupom tem de **falhar como a peça**. Conferir antes de imprimir que ele reproduz a
condição da camada do defeito (`scripts/perfil_camadas.py`, peça × cupom) — ver
`armadilhas.md`, "o que um recorte muda".

**Descartes baratos primeiro, e eles valem.** Extrusão no ar (fio liso e silencioso) → torre de
temperatura com o mesmo rolo → bico limpo ao fim da impressão. Minutos, e descartam rolo,
temperatura e bico com segurança.

**Verificador externo erra junto com o material que recebe.** O que ele disser de novo, medir
por conta própria antes de aceitar (a afirmação da ventoinha de 23/09 foi conferida e se
confirmou; a da cobertura, feita no arquivo errado, caiu).

### Padrao de prova

So esta fechado quando se consegue **ligar e desligar o defeito a vontade**: uma
configuracao que reproduz + um parametro que elimina, confirmado duas vezes.

Curva de dose-resposta vale mais que qualquer argumento. No caso das bolinhas:
120 → 40 → 5 → 0 conforme temperatura e PA foram corrigidos.

### Teia: medir antes de mexer em retração

`python scripts/teia_gcode.py plate_1.gcode`. Na placa de 9 peças (PETG, 22/09): 98% das
viagens acima de 2 mm retraíam; 54% do bico aberto eram viagens abaixo de 1 mm (abaixo de
`retraction_minimum_travel = 1`, por projeto); 43% do bico aberto ficava dentro do suporte. A
retração não estava falhando. O que o G-code não mede é **quanto vaza** — material, umidade,
temperatura.

**Ajuste possível, NÃO testado:** se a teia voltar com o rolo seco e o bico limpo, o
próximo candidato com evidência é baixar `retraction_minimum_travel` — só com teste lado
a lado, uma variável por vez.
