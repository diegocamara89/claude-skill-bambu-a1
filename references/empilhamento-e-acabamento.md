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
- **[M] Frestas < ~2 mm entre feições viram pontes-fiapo** — emendar na geometria (`ponte-e-teto.md`).
- **[C] Velocidade 166% na tela** estoura a vazão e acelera a ponte: não usar em pilha.

Ponte e teto em PETG: `ponte-e-teto.md`.

## Acabamento do topo de grade

- **[M] Nó granulado:** onde nervuras de 2 linhas se cruzam o nó alarga e a última camada vira
  `Top surface` monotonic em riscos curtos + `Gap infill` → furinhos. `top_surface_pattern =
  concentric` troca por voltas que seguem o contorno: sem custo (111,5 contra 114,9 min) e 6%
  menos retrações. Confirmado impresso em 27/09.
- **[M] O "II" (sulco entre os 2 fios de uma nervura de 2 linhas)** não sai com padrão de topo.
  Ironing (`ironing_type = top`) passa no meio da nervura e funde, mas custa +14% (60 mm/s,
  passo 0,2) a +27% (padrão). A face da mesa (PEI texturizada) não tem nem sulco nem furinho.
- **[M] Linha 0,6 + camada 0,28 com arachne** cortaram 28% do tempo do painel sem placa.
