"""Linha do tempo da sequencia de partida da impressora: temperaturas, purga, retracao,
limpezas e nivelamento, lida do machine_start_gcode gravado no cabecalho do G-code.

Serve para responder "e normal sair filamento enquanto ela nivela?". Na A1 (perfil de
13/05/2026): purga 125 mm a 250 C, retrai so 2 mm, desce a 140 C, limpa 4 vezes e so
entao nivela. Sobra pressao e o PETG chora a 140 C — por projeto. Nao e causa de bolinha
na peca: acontece antes da 1a camada e e limpo.

O cabecalho guarda a sequencia com "\\n" literal (barra + n): o script separa por isso.

Uso:  python partida_gcode.py plate_1.gcode
"""
import re, sys

txt = open(sys.argv[1], errors="ignore").read()
m = re.search(r"^; machine_start_gcode = (.*)$", txt, re.M)
if not m: raise SystemExit("machine_start_gcode nao encontrado no cabecalho")
linhas = m.group(1).split(chr(92) + "n")
ext = ret = 0.0; ev = []
for l in linhas:
    l = l.strip()
    t = re.match(r"M10[49] S(\d+)", l)
    if t: ev.append(("temperatura -> " + t.group(1) + " C", ext, ret))
    if l.startswith("G29 A1"): ev.append(("** NIVELAMENTO DA MESA **", ext, ret))
    if "remove waste by touching start" in l: ev.append(("limpeza: raspa na borda", ext, ret))
    if "brush material wipe nozzle =====" in l and "end" not in l: ev.append(("limpeza: escova", ext, ret))
    if "exposed steel surface" in l and not l.startswith(";"): ev.append(("limpeza: circulo no aco", ext, ret))
    e = re.match(r"G[01](?: [XYZF][-\d.{}\[\]_a-z]+)* E(-?[\d.]+)", l)
    if e:
        v = float(e.group(1)); ext += v if v > 0 else 0; ret += -v if v < 0 else 0
print(f"{'etapa':34} {'purgado ate aqui':>17} {'retraido':>10}")
for nome, e, r in ev: print(f"  {nome:32} {e:14.1f} mm {r:8.1f} mm")
print(f"\ntotal antes da 1a camada: purgado {ext:.1f} mm | retraido {ret:.1f} mm")
