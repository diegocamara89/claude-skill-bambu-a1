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
- **Ponte com suporte não foi testada neste caso** — todas as rodadas foram sem suporte. Foi
  testada depois: ver a receita de 28–30/09 abaixo.

## Ponte longa e teto sobre suporte em PETG: receita validada (28–30/09/2026)

Caso: fundo de estojo impresso como teto (vão de 44 mm, apoiado em 3 lados) e cupons de teto de
2,2 mm sobre 2 paredes (vão 20 mm), PETG Masterprint 240 °C, camada 0,20, PEI 80 °C. Defeito:
fios soltos e fendas em lente no meio do vão, com e sem suporte. Registro completo das 8 rodadas:
`D:/Diego/Pessoal/3D/Modelagem 3D/Organizador Skadis/RESULTADOS_teto_PETG.md`.

```
processo   bridge_flow         1.5     (Qualidade > Fluxo da ponte)
processo   bridge_speed        10      mm/s (Velocidade > Ponte)
filamento  overhang_fan_speed  100     % (Resfriamento > Ventoinha de saliências e pontes)
padrão     thick_bridges       0       (não mexer)
brim       outer_only, 5 mm    em cupom de pé pequeno (sem brim os cupons de 2 × 8 mm soltaram)
```

- **[M] Rodada 7:** vão 20 e 44 mm sem suporte, e vão 20 com suporte normal (folga 0,24), todos
  bons (cupons em filamento branco). **[M] 30/09:** o organizador inteiro impresso com a receita,
  sem suporte em nenhuma peça (estojo de 44 mm incluso): o dono aprovou tudo.
- **[M] Só funciona junto.** Fluxo 1,5–1,6 a 50 mm/s falhou 3 vezes (rodadas 2, 4, 5), fluxo 1,0
  a 20 mm/s falhou, fluxo 0,70 a 10 mm/s descolou (seção acima). O que faltava era a velocidade.
- **[M] Onde nasce o defeito:** parando a impressão logo após a camada de ponte (`corta_estagios.py`
  na mesma pasta), as fendas já estavam lá e a luz passava. Não é a camada de cima que abre.
- **[C] Por quê:** com `thick_bridges = 0` a ponte mantém o passo normal (0,383 mm) e o
  `bridge_flow` só muda a massa do fio. A fluxo 1,0 o fio redondo tem ~0,30 mm: os fios não se
  tocam e o vão abre no meio. A 1,5 o fio engorda; devagar ele assenta e funde no vizinho.
- **Antes da receita, só a geometria salvava:** camada 0,28 + linha 0,6 (2 vezes) e rampa de 45°
  no lugar do teto. Continua valendo para quem não quer ponte a 10 mm/s.
- **Isto não contradiz a seção acima:** lá as células eram de 19,2 mm e fechadas, e fluxo 1,0 a
  50 mm/s bastou. Para vão ≥ 20 mm ou teto sobre suporte, usar a receita.

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
