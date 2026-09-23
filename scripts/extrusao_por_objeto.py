"""Quanto de peca, suporte e interface cada objeto da placa recebeu — medido no G-code.

As regioes saem do proprio 3MF (caixa de cada corpo em coordenadas da mesa + margem), nao
de coordenadas digitadas. Tambem mede a PRIMEIRA CAMADA por objeto: peca sem extrusao de
parede/fundo na 1a camada esta flutuando e imprime inteira sobre suporte.

Achados que este script produziu (21-22/09/2026):
  - cupom de colar: 2 mm de parede na 1a camada (cabeca: 462 mm de fundo) -> flutuava;
  - a unica flor que soldou era a unica com Support interface (159 mm);
  - a interface de suporte da placa inteira estava so sob os colares.

IDENTIDADE: o script nomeia por posicao. Quem e quem se confirma por geometria
(modelagem-3d/scripts/componentes.py) e render, nunca por contagem de faces.

Uso:  python extrusao_por_objeto.py plate_1.gcode placa.3mf [--margem 3]
"""
import argparse, re, math
from collections import defaultdict
import numpy as np, trimesh

p = argparse.ArgumentParser()
p.add_argument("gcode"); p.add_argument("tmf"); p.add_argument("--margem", type=float, default=3.0)
a = p.parse_args()
s = trimesh.load(a.tmf, file_type="3mf"); caixas = []
for node in s.graph.nodes_geometry:
    T, g = s.graph[node]; m = s.geometry[g].copy(); m.apply_transform(T)
    for c in m.split(only_watertight=False):
        if len(c.faces) < 4: continue
        lo, hi = c.bounds
        caixas.append((f"x{(lo[0]+hi[0])/2:.0f} y{(lo[1]+hi[1])/2:.0f} ({len(c.faces)} f)", lo[:2] - a.margem, hi[:2] + a.margem,
                       (hi[0] - lo[0]) * (hi[1] - lo[1])))
caixas.sort(key=lambda t: t[3])        # menor primeiro: resolve sobreposicao de margem


def reg(px, py):
    for nome, lo, hi, _ in caixas:
        if lo[0] <= px <= hi[0] and lo[1] <= py <= hi[1]: return nome
    return "fora"


x = y = z = None; feat = "?"; primeira = None
peca = defaultdict(float); sup = defaultdict(float); itf = defaultdict(float); l1 = defaultdict(float)
for ln in open(a.gcode, errors="ignore"):
    if ln.startswith("; Z_HEIGHT:"):
        z = float(ln.split(":")[1]); primeira = z if primeira is None else primeira; continue
    if ln.startswith("; FEATURE:"): feat = ln.split(":", 1)[1].strip(); continue
    if not ln or ln[0] == ";": continue
    if ln.startswith("G1 "):
        nx = re.search(r"X(-?[\d.]+)", ln); ny = re.search(r"Y(-?[\d.]+)", ln); ne = re.search(r"E(-?[\d.]+)", ln)
        ax = float(nx.group(1)) if nx else x; ay = float(ny.group(1)) if ny else y
        if ne and (nx or ny) and x is not None and float(ne.group(1)) > 0:
            d = math.hypot(ax - x, ay - y); r = reg((ax + x) / 2, (ay + y) / 2)
            if feat == "Support": sup[r] += d
            elif feat.startswith("Support"): itf[r] += d
            else:
                peca[r] += d
                if z is not None and primeira is not None and z <= primeira + 1e-6: l1[r] += d
        x, y = ax, ay
print(f"{'objeto (centro na mesa)':28} {'peca':>9} {'suporte':>9} {'interface':>10} {'peca na 1a cam.':>16}")
for nome, *_ in sorted(caixas, key=lambda t: t[0]):
    alerta = "   <<< flutua" if l1[nome] < 20 else ""
    print(f"{nome:28} {peca[nome]:8.0f}mm {sup[nome]:8.0f}mm {itf[nome]:9.0f}mm {l1[nome]:14.0f}mm{alerta}")
if sup["fora"] or itf["fora"]:
    print(f"{'fora das caixas':28} {peca['fora']:8.0f}mm {sup['fora']:8.0f}mm {itf['fora']:9.0f}mm")
