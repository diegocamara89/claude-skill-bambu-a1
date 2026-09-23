"""Teia (stringing) medida no G-code, antes de mexer em retracao.

Para cada viagem (movimento sem extrusao): distancia, se houve retracao antes, e em qual
feicao ela termina. Mostra quanto percurso o bico faz ABERTO, por faixa de distancia e por
destino.

Placa de 9 pecas em 21/09/2026: 98% das viagens > 2 mm retraiam; 54% do bico aberto eram
viagens < 1 mm (abaixo de retraction_minimum_travel, por projeto); 43% ficava dentro do
suporte. A retracao nao estava falhando — o que o G-code nao mede e quanto VAZA
(material e temperatura). Marcadores do Bambu: "; FEATURE:" com espaco depois do ";".

Uso:  python teia_gcode.py plate_1.gcode
"""
import re, sys, math
from collections import Counter

FX = [(0.2, 0.5), (0.5, 1.0), (1.0, 2.0), (2.0, 5.0), (5.0, 1e9)]
x = y = None; feat = "?"; retraido = False
n = Counter(); ns = Counter(); mm = Counter(); por_dest = Counter()
for ln in open(sys.argv[1], errors="ignore"):
    if ln.startswith("; FEATURE:"):
        feat = ln.split(":", 1)[1].strip(); continue
    if not ln or ln[0] == ";":
        continue
    if ln.startswith("G1 ") or ln.startswith("G0 "):
        nx = re.search(r"X(-?[\d.]+)", ln); ny = re.search(r"Y(-?[\d.]+)", ln); ne = re.search(r"E(-?[\d.]+)", ln)
        if ne and not nx and not ny:
            e = float(ne.group(1)); retraido = e < 0 if e != 0 else retraido
            continue
        if nx or ny:
            ax = float(nx.group(1)) if nx else x; ay = float(ny.group(1)) if ny else y
            if ne is None and x is not None and y is not None:
                d = math.hypot(ax - x, ay - y)
                for a, b in FX:
                    if a <= d < b:
                        k = f"{a}-{b if b < 1e8 else 'inf'} mm"; n[k] += 1
                        if not retraido:
                            ns[k] += 1; mm[k] += d; por_dest[feat] += d
                        break
            x, y = ax, ay
print(f"{'faixa':>12} {'viagens':>8} {'sem retr':>9} {'%':>5} {'mm abertos':>11}")
tot = 0.0
for a, b in FX:
    k = f"{a}-{b if b < 1e8 else 'inf'} mm"
    if n[k]:
        print(f"{k:>12} {n[k]:8d} {ns[k]:9d} {100*ns[k]/n[k]:4.0f}% {mm[k]:11.0f}"); tot += mm[k]
print(f"\ntotal de bico aberto (viagens > 0,2 mm): {tot:.0f} mm")
print("por feicao de destino:")
for f, v in por_dest.most_common(8):
    print(f"   {f[:30]:30} {v:8.0f} mm  ({100*v/tot:.0f}%)")
