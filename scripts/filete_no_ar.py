"""Acha no G-code os trechos da PEÇA impressos sobre o ar: sem peça sólida logo abaixo e sem suporte.
Responde "ficou algum ponto que precisava de suporte e não tem?".

Uso:  python filete_no_ar.py plate_1.gcode projeto.3mf [--json saida.json] [--d 0.5] [--folga 0.3] [--min 4]

Critério, em duas etapas (as duas são necessárias, medido no Grogu em 09/10/2026):
 1. Candidato = ponto de extrusão da peça sem NENHUMA extrusão (peça ou suporte) a até --d mm na camada
    anterior, nem suporte/interface a até --d mm nas 3 camadas abaixo (folga do suporte).
 2. Fica só o candidato que também está FORA da seção da malha na camada anterior (alargada por --folga).
    Sem esta etapa, a parede interna da divisa entre cores (que fica dentro da peça, sobre preenchimento
    ralo) aparece como "no ar": deu 66 m falsos contra ~0,3 m reais.
Arcos G2/G3 são seguidos como arco: tratá-los como reta inventa pontos no ar (374 mil arcos no Grogu).
Precisa de manifold3d e shapely. A malha vem do próprio 3MF, na posição da mesa (confere com o G-code
a ~0,2 mm, meia largura de filete). O id do objeto no G-code ("unique label id") vem de model_settings.

Saída: grupos de pontos (mm de filete, camadas, objeto, Z, centro e extensão na mesa). Ler assim:
 - grupo grande (> ~15 mm ou > 5 camadas) em ponto baixo de feição (cotovelo, ponta de orelha, queixo):
   precisa de suporte -> subir o limiar (ver suportes.md, limiar x camada) ou pintar reforço
   (ajusta_3mf.py --reforco).
 - grupo pequeno no rosto (nariz, pálpebra, lábio, ponta de dedo): normalmente melhor sem suporte.
Mostre cada grupo na figura antes de decidir (render_pintura_3mf.py) e confira de novo depois de mudar.
"""
import argparse, json, math, os, re, sys
from collections import defaultdict
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tmf

ap = argparse.ArgumentParser()
ap.add_argument('gcode'); ap.add_argument('projeto'); ap.add_argument('--json')
ap.add_argument('--d', type=float, default=0.5); ap.add_argument('--folga', type=float, default=0.3)
ap.add_argument('--min', type=float, default=4.0, help='mm de filete mínimo para listar um grupo')
a = ap.parse_args()

PULA = ('Prime tower', 'Custom', 'Undefined')
camadas = []; cur = None; feat = ''; obj = None; x = y = None; troca = False
for l in open(a.gcode, encoding='utf-8', errors='ignore'):
    if l.startswith('; Z_HEIGHT:'):
        cur = {'z': float(l.split(':')[1]), 'peca': [], 'obj': [], 'sup': []}; camadas.append(cur); continue
    if l.startswith('; FEATURE:'): feat = l.split(':', 1)[1].strip(); continue
    if l.startswith('; start printing object, unique label id:'): obj = int(l.rsplit(':', 1)[1]); continue
    if l.startswith('; stop printing object'): obj = None; continue
    if l.startswith('M620 S'): troca = True; continue
    if l.startswith('M621 S'): troca = False; continue
    if l.startswith(('G1 ', 'G0 ', 'G2 ', 'G3 ')):
        mx = re.search(r'X(-?[\d.]+)', l); my = re.search(r'Y(-?[\d.]+)', l); me = re.search(r' E(-?[\d.]+)', l)
        ax = float(mx.group(1)) if mx else x; ay = float(my.group(1)) if my else y
        if cur is not None and me and float(me.group(1)) > 0 and (mx or my) and x is not None and not troca and feat not in PULA:
            if l.startswith(('G2 ', 'G3 ')):
                mi = re.search(r'I(-?[\d.]+)', l); mj = re.search(r'J(-?[\d.]+)', l)
                cx = x + (float(mi.group(1)) if mi else 0); cy = y + (float(mj.group(1)) if mj else 0)
                r = math.hypot(x - cx, y - cy); a0 = math.atan2(y - cy, x - cx); da = math.atan2(ay - cy, ax - cx) - a0
                if l.startswith('G2 '):
                    while da >= 0: da -= 2 * math.pi
                else:
                    while da <= 0: da += 2 * math.pi
                n = max(2, int(abs(da) * r / 0.3) + 1)
                pts = [(cx + r * math.cos(a0 + da * s), cy + r * math.sin(a0 + da * s)) for s in np.linspace(0, 1, n)]
            else:
                n = max(2, int(math.hypot(ax - x, ay - y) / 0.3) + 1)
                pts = [(x + (ax - x) * s, y + (ay - y) * s) for s in np.linspace(0, 1, n)]
            if feat.startswith('Support'):
                cur['sup'].extend(pts)
            else:
                cur['peca'].extend(pts); cur['obj'].extend([obj] * len(pts))
        x, y = ax, ay
h = np.median(np.diff([c['z'] for c in camadas])) if len(camadas) > 2 else 0.2

todo = [cKDTree(np.array(c['peca'] + c['sup'])) if c['peca'] or c['sup'] else None for c in camadas]
sup = [cKDTree(np.array(c['sup'])) if c['sup'] else None for c in camadas]
cand = defaultdict(list)  # (label, z) -> pontos
for i, c in enumerate(camadas):
    if i == 0 or not c['peca']: continue
    P = np.array(c['peca']); ok = np.zeros(len(P), bool)
    if todo[i - 1] is not None: ok |= np.isfinite(todo[i - 1].query(P, distance_upper_bound=a.d)[0])
    for k in (2, 3, 4):
        if i - k >= 0 and sup[i - k] is not None: ok |= np.isfinite(sup[i - k].query(P, distance_upper_bound=a.d)[0])
    for j in np.where(~ok)[0]:
        cand[(c['obj'][j], c['z'])].append(P[j])
print(f"camadas {len(camadas)} (altura {h:.2f}), candidatos {sum(len(v) for v in cand.values())}")

import manifold3d as m3, shapely
from shapely.geometry import Polygon
objs = {o['label']: o for o in tmf.objetos(a.projeto)}
mf = {}
def secao(lab, z):
    if lab not in mf:
        V, F, _, _ = tmf.malha(a.projeto, objs[lab], pintura=False)
        mf[lab] = m3.Manifold(m3.Mesh(vert_properties=V.astype(np.float32), tri_verts=F.astype(np.uint32)))
    geo = None
    for anel in mf[lab].slice(z).offset(a.folga, m3.JoinType.Round).to_polygons():
        if len(anel) < 3: continue
        p = Polygon(anel).buffer(0); geo = p if geo is None else geo.symmetric_difference(p)
    return geo
fica = []
for (lab, z), pts in sorted(cand.items(), key=lambda kv: (str(kv[0][0]), kv[0][1])):
    P = np.array(pts)
    if lab not in objs:
        fica += [(float(p[0]), float(p[1]), z, lab) for p in P]; continue
    g = secao(lab, z - 1.5 * h)
    dentro = shapely.contains_xy(g, P[:, 0], P[:, 1]) if g is not None else np.zeros(len(P), bool)
    fica += [(float(p[0]), float(p[1]), z, lab) for p in P[~dentro]]
print(f"no ar de verdade: {len(fica)} pontos ≈ {len(fica) * 0.3:.0f} mm de filete")

A = np.array([f[:3] for f in fica]).reshape(-1, 3); grupos = []
if len(A):
    pai = list(range(len(A)))
    def r(i):
        while pai[i] != i: pai[i] = pai[pai[i]]; i = pai[i]
        return i
    for p, q in cKDTree(A).query_pairs(1.2, output_type='ndarray'):
        rp, rq = r(p), r(q)
        if rp != rq: pai[rp] = rq
    G = defaultdict(list)
    for i in range(len(A)): G[r(i)].append(i)
    for idx in G.values():
        p = A[idx]; lab = fica[idx[0]][3]
        grupos.append({'mm_filete': round(len(idx) * 0.3, 1), 'camadas': int(len(set(np.round(p[:, 2], 3)))),
                       'objeto': objs[lab]['nome'] if lab in objs else str(lab), 'label': lab,
                       'z': [round(float(p[:, 2].min()), 2), round(float(p[:, 2].max()), 2)],
                       'centro': p.mean(0).round(2).tolist(), 'min': p.min(0).round(2).tolist(), 'max': p.max(0).round(2).tolist()})
grupos.sort(key=lambda g: -g['mm_filete'])
for i, g in enumerate(grupos):
    if g['mm_filete'] < a.min: break
    ext = (np.array(g['max'][:2]) - np.array(g['min'][:2])).round(1).tolist()
    print(f"[{i:3d}] {g['mm_filete']:6.1f} mm  {g['camadas']:3d} cam  {g['objeto']:20s} z {g['z'][0]:6.2f}-{g['z'][1]:6.2f}  "
          f"centro {g['centro'][0]:.1f},{g['centro'][1]:.1f}  extensão {ext}")
if a.json:
    json.dump({'gcode': a.gcode, 'projeto': a.projeto, 'h': float(h), 'pontos': fica, 'grupos': grupos}, open(a.json, 'w'))
