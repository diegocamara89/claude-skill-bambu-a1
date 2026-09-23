"""Quanto de cada balanço tem suporte e interface embaixo, medido no G-code, por região.

Uso:
  python cobertura_suporte.py malha.ply plate_1.gcode [--desloc TX TY TZ | --mesa 128 128]
         [--girar GRAUS] [--regiao nome X0 Y0 Z0 X1 Y1 Z1 ...] [--folga 0.3]

malha      a MESMA malha que foi fatiada (PLY/OBJ/3MF; STL funciona, mas arredonda).
--mesa     põe a malha com centro XY no ponto e base em Z = 0 (o que o fatiador faz ao centralizar).
--desloc   translação exata malha -> mesa (placa_ab.py imprime uma por cópia).
--girar    giro em Z (graus) em torno do centro da malha ANTES de posicionar. O G-code que foi
           impresso pode estar girado em relação ao projeto: alinhar pelas paredes externas antes.
           Sinal errado dá cobertura perto de zero na peça inteira (medido: +90 deu 3%, -90 deu 24%).
--regiao   caixas em coordenadas da MESA. Sem nenhuma, mede a peça inteira.

Balanço = face voltada para baixo, a menos de 40° da horizontal, acima de 0,5 mm.
Apoiada = extrusão de Support/Support interface até 1,0 mm em XY e até --folga abaixo da face.
É critério geométrico: diz onde há suporte perto, não se ele encostou nem se é rígido.

Marcadores do Bambu: "; FEATURE:" e "; Z_HEIGHT:" com espaço depois do ";".

Caso de 23/09/2026: busto impresso e cupom recortado dele tiveram a MESMA cobertura na barra de
uma manga (82% apoiado, 20% com interface) e resultado físico oposto. Cobertura igual não quer
dizer condição igual — ver references/armadilhas.md (o que um recorte muda).
"""
import argparse, math, re
import numpy as np, trimesh
from scipy.spatial import cKDTree

ap = argparse.ArgumentParser()
ap.add_argument("malha"); ap.add_argument("gcode")
ap.add_argument("--desloc", nargs=3, type=float)
ap.add_argument("--mesa", nargs=2, type=float)
ap.add_argument("--girar", type=float, default=0.0)
ap.add_argument("--regiao", nargs=7, action="append", default=[], metavar=("NOME", "X0", "Y0", "Z0", "X1", "Y1", "Z1"))
ap.add_argument("--folga", type=float, default=0.3)
ap.add_argument("--raio", type=float, default=1.0)
a = ap.parse_args()

m = trimesh.load(a.malha, force="mesh", process=False)
if a.girar:
    m.apply_transform(trimesh.transformations.rotation_matrix(np.radians(a.girar), [0, 0, 1], m.bounds.mean(0)))
lo, hi = m.bounds
if a.desloc:
    m.apply_translation(a.desloc)
elif a.mesa:
    m.apply_translation([a.mesa[0] - (lo[0] + hi[0]) / 2, a.mesa[1] - (lo[1] + hi[1]) / 2, -lo[2]])

sup, itf = [], []
x = y = None; z = 0.0; feat = ""
for ln in open(a.gcode, errors="ignore"):
    if ln.startswith("; Z_HEIGHT:"): z = float(ln.split(":")[1]); continue
    if ln.startswith("; FEATURE:"): feat = ln.split(":", 1)[1].strip(); continue
    if not ln or ln[0] == ";": continue
    if ln.startswith("G1 ") or ln.startswith("G0 "):
        nx = re.search(r"X(-?[\d.]+)", ln); ny = re.search(r"Y(-?[\d.]+)", ln); ne = re.search(r"E(-?[\d.]+)", ln)
        ax = float(nx.group(1)) if nx else x; ay = float(ny.group(1)) if ny else y
        if ne and (nx or ny) and x is not None and y is not None and float(ne.group(1)) > 0 and feat.startswith("Support"):
            k = max(2, int(math.hypot(ax - x, ay - y) / 0.4) + 1)
            alvo = sup if feat == "Support" else itf
            for s in np.linspace(0, 1, k): alvo.append((x + (ax - x) * s, y + (ay - y) * s, z))
        x, y = ax, ay
S = np.array(sup).reshape(-1, 3); I = np.array(itf).reshape(-1, 3)

tri = m.vertices[m.faces]; ct = tri.mean(1)
nrm = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]); ar = np.linalg.norm(nrm, axis=1) / 2
nrm = nrm / np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-12)
cosd = -nrm[:, 2]; th = np.degrees(np.arccos(np.clip(cosd, -1, 1)))
bal = (cosd > 1e-6) & (ct[:, 2] > 0.5) & (th < 40)


def cobre(pts):
    ok = np.zeros(len(ct), bool)
    if len(pts) == 0: return ok
    t = cKDTree(pts[:, :2]); idx = np.where(bal)[0]
    for i, v in zip(idx, t.query_ball_point(ct[idx, :2], r=a.raio)):
        if v:
            dz = ct[i, 2] - pts[v, 2]
            ok[i] = bool(np.any((dz > -0.05) & (dz < a.folga)))
    return ok


ms = cobre(np.vstack([S, I])); mi = cobre(I)
print(f"pontos de suporte {len(S)} (até Z {S[:, 2].max() if len(S) else 0:.2f}), "
      f"interface {len(I)} (até Z {I[:, 2].max() if len(I) else 0:.2f})")
regs = [("peça inteira", np.ones(len(ct), bool))] + [
    (r[0], np.all((ct >= np.array(r[1:4], float)) & (ct <= np.array(r[4:7], float)), axis=1)) for r in a.regiao]
print(f"{'regiao':24} {'balanço':>10} {'apoiado':>16} {'com interface':>18}")
for nome, sel in regs:
    A = ar[bal & sel].sum(); B = ar[bal & sel & ms].sum(); C = ar[bal & sel & mi].sum()
    print(f"{nome:24} {A:7.1f} mm2 {B:8.1f} ({100 * B / max(A, 1e-9):3.0f}%) {C:9.1f} ({100 * C / max(A, 1e-9):3.0f}%)")
