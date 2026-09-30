# Ponte e teto em PETG (inclusive a face sobre suporte)

Vale para: fundo de caixa impresso como teto, ponte longa entre duas paredes e **a face de baixo
de qualquer região apoiada em suporte**. No Bambu, a 1ª camada sobre suporte com folga > 0 é
classificada como `Bridge` (PrintObject.cpp, `stBottomBridge`): quem manda nela são os ajustes
de ponte, não os de suporte. Marcação: **[M]** medido, **[C]** calculado.

## Receita (PETG Masterprint 240 °C, camada 0,20, PEI 80 °C)

```
processo   bridge_flow         1.5     (Qualidade > Fluxo da ponte)
processo   bridge_speed        10      mm/s (Velocidade > Ponte)
filamento  overhang_fan_speed  100     % (Resfriamento > Ventoinha de saliências e pontes)
padrão     thick_bridges       0       (não mexer)
padrão     bridge_angle        0       automático; em grade de células, fixar 180 (ver abaixo)
brim       outer_only, 5 mm    em cupom de pé pequeno (cupons de 2 × 8 mm soltaram sem brim)
```

- **[M] Provas:** cupons com vão de 20 e 44 mm sem suporte e vão de 20 com suporte normal
  (folga 0,24), todos bons (29/09, filamento branco); organizador inteiro sem suporte, com o
  fundo do estojo de 44 mm, aprovado pelo dono (30/09). Registro das 8 rodadas:
  `D:/Diego/Pessoal/3D/Modelagem 3D/Organizador Skadis/RESULTADOS_teto_PETG.md`.
- **[M] Os três ajustes só funcionam juntos.** Fluxo 1,5–1,6 a 50 mm/s falhou 3 vezes; fluxo 1,0
  a 20 mm/s falhou; fluxo 0,70 a 10 mm/s descolou a nervura. Reduzir o fluxo da ponte em PETG
  piora: o fio estica e cola mal no apoio.
- **[C] Por quê:** com `thick_bridges = 0` a ponte mantém o passo normal (0,383 mm) e o
  `bridge_flow` só muda a massa do fio. A fluxo 1,0 o fio redondo tem ~0,30 mm: os fios não se
  tocam e o vão abre no meio. A 1,5 o fio engorda; devagar, ele assenta e funde no vizinho.
- **[M] Em células fechadas pequenas (19,2 mm), fluxo 1,0 a 50 mm/s bastou** (painel Skadis,
  22–27/09). A receita acima é a regra; esse caso só mostra que vão curto tolera mais.

## Geometria antes de receita

- **[M] Defeito no mesmo lugar em várias configurações é ordem de impressão, não parâmetro.** Ler
  no G-code onde nasce o 1º fio da ponte. Com `bridge_angle = 90` a ponte começou no meio da
  célula (fio isolado a 6,8 mm do apoio); com 180 (0°) começou no apoio.
- **[M] O fatiador estende a ponte além do apoio** (fios de 28 mm numa célula de 19,2): passa por
  cima de nervura fina e funde células vizinhas. Fechar as células e emendar o anel à nervura.
- **[M] Frestas < ~2 mm entre feições viram pontes-fiapo**: emendar na geometria.
- **[M] Sem a receita, só a geometria salvou o teto:** camada 0,28 + linha 0,6, ou rampa de 45° no
  lugar do teto.
- **[M] Ranhura estreita nunca como teto.** A ranhura de 1,9 mm de um puxador, impressa deitada, saiu
  com material preso dentro e travou o encaixe (30/09). Em pé, com as paredes da ranhura na
  vertical, não há ponte (conferido na malha; impressão pendente).

## Diagnóstico

- **[M] Onde nasce a fenda:** parar a impressão logo após a camada de ponte e olhar contra a luz.
  As fendas já estavam lá; não é a camada de cima que abre. Script usado (constantes do caso,
  adaptar): `.../Organizador Skadis/corta_estagios.py`. Ele mantém os movimentos em Z e as
  retrações e tira só XY e extrusão; tirar os movimentos em Z quebra o arquivo.
- **Folga do suporte não conserta a face apoiada:** seis rodadas mexendo em folga, interface,
  suporte em bloco e camada 0,08 não resolveram. Ver `suportes.md` para o resto do suporte.

## Fatos do fatiador

- **[M] OrcaSlicer não reproduz a ordem de ponte do Bambu Studio**: para ordem, só vale o Bambu.
- **[M] "Camada extra de ponte (beta)" não existe no Bambu Studio** (é do Orca).
- **[M] `filament_bridge_speed` do filamento não foi aplicado**; valeu `bridge_speed` do processo.
- Pontes grossas usam passo = diâmetro do fio + 0,05 (Flow.cpp). O Bambu não tem densidade de
  ponte (o Orca tem, de 10 a 125%).
