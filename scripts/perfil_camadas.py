"""Compara, por faixa de altura, o que a impressora faz em cada camada — entre dois G-codes ou dentro de um.

Uso:
  python perfil_camadas.py peca.gcode:34-37:manga  peca.gcode:20-25:controle  cupom.gcode:6-9:cupom

Cada argumento é  arquivo:z0-z1[:rotulo].  Por faixa, média por camada de:
  tempo (estimado por distância/velocidade, sem aceleração — serve para COMPARAR, não para prever),
  extrusão, viagens > 1 mm e quantas sem retração, retrações,
  ventoinha na parede externa (mediana do M106 da ventoinha da peça, em % de 255),
  velocidade da feição "Overhang wall".

Para que serve: antes de confiar num cupom, conferir se ele reproduz as condições da peça inteira
na camada do defeito. Caso de 23/09/2026: na barra de uma manga, o busto tinha camadas de ~22 s e
o fatiador baixou a ventoinha da parede externa para 72%; o cupom recortado dali tinha camadas de
13 s e ventoinha a 89%. Com fan_cooling_layer_time = 30 s, a ventoinha varia entre fan_min_speed e
fan_max_speed conforme o tempo da camada: peça grande ventila menos que o cupom dela.
"""
import math, re, sys
import numpy as np


def perfil(g):
    L = {}; z = 0.0; x = y = None; fan = 0; feat = ""; ret = False; F = 3000.0
    for ln in open(g, errors="ignore"):
        if ln.startswith("; Z_HEIGHT:"): z = round(float(ln.split(":")[1]), 3); continue
        if ln.startswith("; FEATURE:"): feat = ln.split(":", 1)[1].strip(); continue
        if not ln or ln[0] == ";": continue
        c = ln.split(";")[0].split()
        if not c: continue
        d = L.setdefault(z, dict(t=0.0, ext=0.0, trav=0, trav_sem_ret=0, ret=0, fan_ow=[], ovh=[]))
        if c[0] == "M106":
            s = re.search(r"S(\d+)", ln); p = re.search(r"P(\d)", ln)
            if s and (not p or p.group(1) == "1"): fan = int(s.group(1))       # P1 = ventoinha da peça
        elif c[0] == "M107":
            fan = 0
        elif c[0] in ("G1", "G0"):
            fx = re.search(r"F([\d.]+)", ln)
            if fx: F = float(fx.group(1))
            nx = re.search(r"X(-?[\d.]+)", ln); ny = re.search(r"Y(-?[\d.]+)", ln); ne = re.search(r"E(-?[\d.]+)", ln)
            ev = float(ne.group(1)) if ne else 0.0
            if ne and not (nx or ny):
                if ev < 0: d["ret"] += 1; ret = True
                elif ev > 0: ret = False
                continue
            ax = float(nx.group(1)) if nx else x; ay = float(ny.group(1)) if ny else y
            if None not in (x, y, ax, ay) and (nx or ny):
                dist = math.hypot(ax - x, ay - y); d["t"] += dist / max(F, 1) * 60
                if ev > 0:
                    d["ext"] += dist
                    if feat == "Outer wall": d["fan_ow"].append(fan)
                    if feat == "Overhang wall": d["ovh"].append(F / 60)
                elif dist > 1.0:
                    d["trav"] += 1
                    if not ret: d["trav_sem_ret"] += 1
            x, y = ax, ay
    return L


cache = {}
print(f"{'faixa':22} {'cam.':>4} {'tempo/cam':>9} {'extrusão':>9} {'viagens':>8} {'s/ retr.':>8} {'retr.':>6} {'vent. parede ext.':>18} {'overhang':>9}")
for arg in sys.argv[1:]:
    m = re.match(                         # não guloso no caminho: aceita letra de unidade (C:\...)
r"^(.*?):(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)(?::(.*))?$", arg)
    if not m: sys.exit(f"argumento inválido: {arg}  (use arquivo:z0-z1[:rotulo])")
    g, z0, z1, rot = m.group(1), float(m.group(2)), float(m.group(3)), m.group(4) or f"Z{m.group(2)}-{m.group(3)}"
    if g not in cache: cache[g] = perfil(g)
    L = cache[g]; ks = [k for k in L if z0 <= k <= z1]
    if not ks: print(f"{rot:22} nenhuma camada nessa faixa"); continue
    med = lambda f: np.mean([f(L[k]) for k in ks])
    fans = [np.median(L[k]["fan_ow"]) for k in ks if L[k]["fan_ow"]]
    ov = [v for k in ks for v in L[k]["ovh"]]
    fan_txt = f"{100 * np.median(fans) / 255:3.0f}% ({100 * min(fans) / 255:.0f}-{100 * max(fans) / 255:.0f})" if fans else "-"
    print(f"{rot:22} {len(ks):4} {med(lambda d: d['t']):7.1f} s {med(lambda d: d['ext']):6.0f} mm {med(lambda d: d['trav']):8.1f} "
          f"{med(lambda d: d['trav_sem_ret']):8.1f} {med(lambda d: d['ret']):6.1f} {fan_txt:>18} {np.median(ov) if ov else 0:6.0f} mm/s")
