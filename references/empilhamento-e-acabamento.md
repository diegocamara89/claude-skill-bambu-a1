# Empilhar peças sem trocador e acabamento de grade (22–27/09/2026)

Caso de origem: painel Skadis (200×200×5 mm) em PETG Masterprint, bico 0,4, BMCU quebrado.
Marcação: **[M]** medido (G-code, arquivo ou impressão), **[C]** calculado.

## Empilhar PETG sobre PETG: veredito

- **[M] Folga de 1 camada solta só com pouco contato.** 9% da área encostada: soltou fácil.
  ~19%: soltou com força. Painel sem placa com chanfro (13%): **soldou e quebrou ao soltar**.
  Com grade de nervuras finas, empilhar PETG puro está descartado; próximo passo seria camada
  de interface de outro material (PLA), que exige trocador.
- **[M] A camada vazia precisa cair na grade de camadas** = 1ª camada + h·n (ex.: 0,20 + 0,28·n).
  Borda de peça fora da grade some com a camada vazia e a pilha solda sem aviso.
- **[M] Camada vazia no meio do objeto é só aviso laranja**; coluna de apoio é desnecessária.
- **[M] Toda nervura da peça de cima nasce na mesma camada** (logo após a camada vazia). Nervura
  que começa solta no ar sai como `Outer wall` a até 181 mm/s e vira emaranhado; nascendo junto
  com o resto, sai como `Overhang wall` a 30–50 mm/s e imprime bem.
- **[M] Laço fechado impresso no ar encolhe para dentro** (anel invade o túnel); reta não.
- **[M] Frestas < ~2 mm entre feições viram pontes-fiapo** — emendar na geometria.

## Ponte em PETG (teto de peça virada)

- **[M] Receita dos vídeos (fluxo da ponte 0,70 + ventoinha 100%) falhou:** fio subiu e enrolou a
  50 e 25 mm/s; a 10 mm/s a nervura de 1 linha descolou. Em PETG, reduzir o fluxo da ponte PIORA.
- **[M] Configuração fechada:** fluxo 1,0, 50 mm/s, ventoinha 100%, `bridge_angle = 180` (0°),
  células fechadas. Com 90° a ponte começou no MEIO da célula (fio isolado a 6,8 mm do apoio).

**Conclusões (o porquê):**
- **Fluxo baixo só funciona devagar, e mesmo assim cobra na colagem.** Fluxo da ponte baixo estica
  o fio (por isso só deu certo a 10 mm/s), e fluxo baixo + ventoinha máxima cola mal a ponte no
  topo da nervura. Numa peça virada essa colagem é a união estrutural placa↔nervura: foi ali que
  a nervura descolou. Com fluxo 1,0 o fio tem massa para cruzar o vão sem romper.
- **Defeito no MESMO lugar em várias configurações não é parâmetro — é ordem de impressão.** As
  três variantes de 23/09 tiveram a mesma faixa ruim; o G-code mostrou a ponte começando no meio
  da célula (1º fio sozinho no ar), indo para um lado e voltando para fechar o outro. Antes de
  mexer em fluxo/velocidade de novo, ler no G-code onde o 1º fio da ponte nasce.
- **O fatiador estende a ponte além do apoio** (fios de 28 mm numa célula de 19,2): passa por cima
  de nervura fina e funde células vizinhas. Por isso células fechadas e anel emendado à nervura.
- **Quem resolveu foi a geometria, não a receita:** com células fechadas, frestas < 2 mm fundidas
  e direção fixa, a configuração "normal" (fluxo 1,0, 50 mm/s) deu frente perfeita e teto inteiro.
- **Ponte com suporte não foi testada neste caso** — todas as rodadas foram sem suporte.

- **[M] OrcaSlicer não reproduz a ordem de ponte do Bambu Studio** — para ordem, só vale o Bambu.
- **[M] "Camada extra de ponte (beta)" não existe no Bambu Studio** (é do Orca).
- **[M] `filament_bridge_speed` do filamento não foi aplicado**; valeu `bridge_speed` do processo.

## Acabamento do topo de grade

- **[M] Nó granulado:** onde nervuras de 2 linhas se cruzam o nó alarga e a última camada vira
  `Top surface` monotonic em riscos curtos + `Gap infill` → furinhos. `top_surface_pattern =
  concentric` troca por voltas que seguem o contorno: sem custo (111,5 contra 114,9 min) e 6%
  menos retrações. Confirmado impresso em 27/09.
- **[M] O "II" (sulco entre os 2 fios de uma nervura de 2 linhas)** não sai com padrão de topo.
  Ironing (`ironing_type = top`) passa no meio da nervura e funde, mas custa +14% (60 mm/s,
  passo 0,2) a +27% (padrão). A face da mesa (PEI texturizada) não tem nem sulco nem furinho.
- **[M] Linha 0,6 + camada 0,28 com arachne** cortaram 28% do tempo do painel sem placa.

## Vazão e velocidade

- **[M] PETG Masterprint a 240 °C:** torre sem falha até 20 mm³/s → usar 16. Fabricante só
  publica 220–240 °C / mesa 70–90 °C.
- **[C] Velocidade 166% na tela** estoura a vazão e acelera a ponte: não usar em pilha.

## Início remoto

- **[M] Iniciar impressão por MQTT sem assinatura** → HMS 0500-0500-0001-0007; com assinatura
  (`gsign.mjs`) → `err_code 84033545`. Iniciar pela tela da impressora.
- **[M] A impressora muda de IP (DHCP):** achar pelo anúncio SSDP na porta UDP 2021.
