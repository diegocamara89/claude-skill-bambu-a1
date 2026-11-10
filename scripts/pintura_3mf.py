"""Audita a pintura de cores de um projeto 3MF multicor: regiões (ilhas) de cada cor por objeto e quais
delas CUSTAM TROCAS sozinhas (são a única ocorrência da cor naquelas camadas na placa inteira).

Uso:  python pintura_3mf.py projeto.3mf [--camada 0.2] [--json saida.json] [--max-area 50]

Para cada objeto: regiões conexas pela cor dominante do triângulo, com área (mm², tamanho impresso),
faixa de Z na mesa e a cor vizinha dominante. Depois, na placa: para cada região pequena (< --max-area),
quantas camadas ela acrescenta em que a cor dela não existiria sem ela ("camadas_proprias"). Cada uma
dessas camadas costuma custar 1 troca (~100 s e ~0,3 g na A1 com BMCU, medido no Grogu).

O que este script NÃO vê (limite medido em 09/10/2026): erro de pintura colado na região principal
(roupa pintada de pele encostada na pele) não vira ilha. Para isso: render das cores e comparação
entre figuras/lados. E ilha "escondida" se confirma por render de várias direções, inclusive DE BAIXO.
Caso de origem: Grogu, mancha verde de 2,9 mm² sob a manga a 51–54 mm = 14 trocas (−23 min, −4 g).
"""
import argparse, json, os, sys
from collections import defaultdict, Counter
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tmf

ap = argparse.ArgumentParser()
ap.add_argument('projeto'); ap.add_argument('--camada', type=float, default=0.2)
ap.add_argument('--json'); ap.add_argument('--max-area', type=float, default=50.0)
ap.add_argument('--min-area', type=float, default=0.18, help='abaixo disso o fatiador descarta (0,42 x 0,42 mm); medido: não gerou troca')
a = ap.parse_args()

regioes = []
for obj in tmf.objetos(a.projeto):
    V, F, C, _ = tmf.malha(a.projeto, obj)
    tri = V[F]; zc = tri[:, :, 2].mean(1)
    ar = np.linalg.norm(np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]), axis=1) / 2
    pai = np.arange(len(F))
    def raiz(i):
        while pai[i] != i:
            pai[i] = pai[pai[i]]; i = pai[i]
        return i
    aresta = {}; viz = defaultdict(Counter)
    for i, (p, q, r) in enumerate(F):
        for e in ((p, q), (q, r), (r, p)):
            k = (e[0], e[1]) if e[0] < e[1] else (e[1], e[0])
            j = aresta.pop(k, None)
            if j is None:
                aresta[k] = i
            elif C[i] == C[j]:
                ri, rj = raiz(i), raiz(j)
                if ri != rj: pai[ri] = rj
            else:
                viz[i][C[j]] += 1; viz[j][C[i]] += 1
    grupos = defaultdict(list)
    for i in range(len(F)):
        grupos[raiz(i)].append(i)
    for idx in grupos.values():
        idx = np.array(idx); vz = Counter()
        for i in idx:
            if i in viz: vz.update(viz[i])
        w = ar[idx]
        regioes.append({'objeto': obj['nome'], 'cor': int(C[idx[0]]), 'area_mm2': round(float(w.sum()), 3),
                        'triangulos': int(len(idx)), 'z_ini': round(float(zc[idx].min()), 2), 'z_fim': round(float(zc[idx].max()), 2),
                        'centro_mesa': [round(float(v), 2) for v in (tri[idx].mean(1) * w[:, None]).sum(0) / max(w.sum(), 1e-12)],
                        'vizinha': int(vz.most_common(1)[0][0]) if vz else None})
    print(f"{obj['nome']}: {len(F)} triângulos, {len(aresta)} arestas sem par, {sum(1 for r in regioes if r['objeto'] == obj['nome'])} regiões")

h = a.camada
def camadas(r):
    return set(range(int(r['z_ini'] // h), int(r['z_fim'] // h) + 1))
por_cor = defaultdict(Counter)
for r in regioes:
    if r['area_mm2'] < a.min_area: continue
    for k in camadas(r): por_cor[r['cor']][k] += 1
todas = set().union(*[set(c) for c in por_cor.values()]) if por_cor else set()
mistas = {k for k in todas if sum(1 for c in por_cor if por_cor[c][k]) > 1}
print(f"\ncamadas com mais de uma cor (estimativa pela malha): {len(mistas)} de {len(todas)}")
for c, cnt in sorted(por_cor.items()):
    ks = sorted(cnt); print(f"  cor {c}: z {ks[0] * h:.1f} a {(ks[-1] + 1) * h:.1f} mm")
custo = []
for r in regioes:
    if r['area_mm2'] >= a.max_area or r['area_mm2'] < a.min_area: continue
    ks = camadas(r)
    proprias = [k for k in ks if por_cor[r['cor']][k] == 1 and k in mistas]
    r['camadas_proprias'] = len(proprias)
    if proprias: custo.append(r)
custo.sort(key=lambda r: -r['camadas_proprias'])
print(f"\nregiões pequenas que criam camadas de troca sozinhas (candidatas a erro de pintura com custo): {len(custo)}")
for r in custo[:30]:
    print(f"  {r['objeto']:20s} cor {r['cor']} {r['area_mm2']:8.2f} mm²  z {r['z_ini']:.1f}-{r['z_fim']:.1f}  "
          f"vizinha {r['vizinha']}  camadas próprias {r['camadas_proprias']}  centro {r['centro_mesa']}")
print("\nmaiores regiões por objeto e cor (conferir no render se a divisa está onde deveria):")
vistos = set()
for r in sorted(regioes, key=lambda r: -r['area_mm2']):
    k = (r['objeto'], r['cor'])
    if k in vistos: continue
    vistos.add(k); print(f"  {r['objeto']:20s} cor {r['cor']} {r['area_mm2']:10.1f} mm²  z {r['z_ini']:.1f}-{r['z_fim']:.1f}")
if a.json:
    json.dump({'camada': h, 'regioes': regioes}, open(a.json, 'w'), indent=1)
