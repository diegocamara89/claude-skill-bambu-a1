"""Limpa a pintura de cores de um 3MF do Bambu e grava uma cópia (pintura_3mf.py só audita; este corrige).

Uso:
  python limpa_pintura_3mf.py entrada.3mf saida.3mf [--ilha-min 0.5] [--proteger 4] [--divisa 1,2 [--banda 0.4]]
         [--json relatorio.json]

--ilha-min  ilha (região conexa de uma cor) com área impressa menor que isso, em mm², passa para a cor vizinha
            dominante. Vizinha que também é ilha não vota (senão duas ilhas encostadas trocam de cor para sempre).
--proteger  extrusores que nunca mudam nem invadem (ex.: 4 = olhos pretos de 2,5 mm²).
--divisa    A,B: puxa a divisa entre as cores A e B para o fundo do vinco côncavo mais próximo. Miolos (faces a
            mais de --banda mm da divisa atual) viram sementes; cada face da faixa de dúvida fica com a semente
            mais próxima num grafo de faces em que cruzar aresta côncava custa caro (Dijkstra). Use quando a divisa
            saiu serrilhada (cópia de rótulo de outra malha, pintura à mão) e o modelo tem vinco ali.

Ordem: divisa primeiro, ilhas depois. Faces que não mudam guardam a string de pintura original (subdivisões
finas ficam). Faces que mudam ganham a cor inteira (estado simples). Malha compartilhada por vários objetos é
limpa uma vez. Vale para paint_color; paint_supports fica intacto.

Medido no Mini Jesus (15/10/2026, 1,59 milhão de triângulos): o original do autor tinha 2.143 regiões (pontos
brancos no cabelo marrom); depois da limpeza, 24, e nenhuma ilha com troca própria. A faixa que pintei copiando
rótulo de uma malha reduzida por vizinho mais próximo saiu serrilhada; --divisa a pôs no vinco.
Depois: pintura_3mf.py na saída, render das cores (render_pintura_3mf.py) e fatiar.
Depende de numpy e scipy.
"""
import argparse, io, json, os, re, sys, zipfile
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components, dijkstra
from scipy.spatial import cKDTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tmf

ap = argparse.ArgumentParser()
ap.add_argument('entrada'); ap.add_argument('saida')
ap.add_argument('--ilha-min', type=float, default=0.5); ap.add_argument('--proteger', default='')
ap.add_argument('--divisa'); ap.add_argument('--banda', type=float, default=0.4); ap.add_argument('--json')
a = ap.parse_args()
assert os.path.abspath(a.entrada) != os.path.abspath(a.saida), 'não sobrescreva o arquivo de origem'
prot = {int(x) for x in a.proteger.split(',') if x}


def codigo(estado):
    """estado inteiro -> string paint_color (lida de trás para frente: ver tmf.py)."""
    return '%X' % (estado << 2) if estado < 3 else '%XC' % (estado - 3)


def adjacencia(F):
    """pares de faces que dividem aresta + vértices da aresta."""
    e = np.sort(np.r_[F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]], axis=1)
    face = np.tile(np.arange(len(F)), 3)
    ordem = np.lexsort((e[:, 1], e[:, 0])); e, face = e[ordem], face[ordem]
    igual = np.all(e[1:] == e[:-1], axis=1)
    return np.c_[face[:-1][igual], face[1:][igual]], e[:-1][igual]


def componentes(C, adj, n):
    ok = C[adj[:, 0]] == C[adj[:, 1]]; p = adj[ok]
    return connected_components(coo_matrix((np.ones(len(p)), (p[:, 0], p[:, 1])), shape=(n, n)), directed=False)


def limpa_ilhas(C, adj, ar):
    rodadas = []
    for _ in range(8):
        n, lab = componentes(C, adj, len(C))
        area = np.bincount(lab, weights=ar, minlength=n)
        cor = np.zeros(n, int); cor[lab] = C
        ilha = (area < a.ilha_min) & ~np.isin(cor, list(prot))
        b = lab[adj[:, 0]] != lab[adj[:, 1]]
        x, y = np.r_[lab[adj[b, 0]], lab[adj[b, 1]]], np.r_[lab[adj[b, 1]], lab[adj[b, 0]]]
        s = ilha[x] & ~ilha[y] & ~np.isin(cor[y], list(prot))
        if not s.any(): break
        votos = coo_matrix((np.ones(s.sum()), (x[s], cor[y[s]])), shape=(n, cor.max() + 1)).tocsr()
        alvo = np.full(n, -1); tem = np.flatnonzero(votos.getnnz(axis=1))
        alvo[tem] = np.asarray(votos[tem].argmax(axis=1)).ravel()
        novo = alvo[lab]; mud = (novo >= 0) & (novo != C)
        rodadas.append({'ilhas': int(ilha.sum()), 'area_mm2': round(float(area[ilha].sum()), 3), 'faces': int(mud.sum())})
        C = C.copy(); C[mud] = novo[mud]
    return C, rodadas


def ajusta_divisa(C, V, F, adj, ev, ca, cb):
    cen = V[F].mean(1); nrm = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    nrm /= np.maximum(np.linalg.norm(nrm, axis=1), 1e-12)[:, None]
    ang = np.arccos(np.clip((nrm[adj[:, 0]] * nrm[adj[:, 1]]).sum(1), -1, 1))
    # côncava: o centro da face vizinha fica do lado da normal da face
    concava = ((cen[adj[:, 1]] - cen[adj[:, 0]]) * nrm[adj[:, 0]]).sum(1) > 1e-9
    zona = (C == ca) | (C == cb)
    borda = (C[adj[:, 0]] != C[adj[:, 1]]) & zona[adj[:, 0]] & zona[adj[:, 1]]
    if not borda.any(): return C, 0
    d, _ = cKDTree(V[np.unique(ev[borda].ravel())]).query(cen)
    semente = zona & (d > a.banda); duvida = zona & (d <= a.banda)
    ok = zona[adj[:, 0]] & zona[adj[:, 1]]; p = adj[ok]
    w = np.linalg.norm(cen[p[:, 0]] - cen[p[:, 1]], axis=1) * (1 + 8 * np.where(concava[ok], ang[ok], 0) / np.radians(10))
    G = coo_matrix((np.r_[w, w], (np.r_[p[:, 0], p[:, 1]], np.r_[p[:, 1], p[:, 0]])), shape=(len(F), len(F))).tocsr()
    sem = np.flatnonzero(semente & (d < a.banda + 0.5))
    _, _, src = dijkstra(G, indices=sem, min_only=True, return_predecessors=True, limit=a.banda * 20)
    al = duvida & (src >= 0)
    novo = C.copy(); novo[al] = C[src[al]]
    return novo, int((novo != C).sum())


zin = zipfile.ZipFile(a.entrada)
novos, rel, feitos = {}, [], set()
for obj in tmf.objetos(a.entrada):
    if obj['arquivo'] in feitos: continue
    feitos.add(obj['arquivo'])
    V, F, C, _ = tmf.malha(a.entrada, obj)                      # C: extrusor dominante (0 já virou o do objeto)
    tri = V[F]; ar = np.linalg.norm(np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]), axis=1) / 2
    adj, ev = adjacencia(F)
    antes = componentes(C, adj, len(F))[0]
    C2, mud_div = C, 0
    if a.divisa:
        ca, cb = (int(x) for x in a.divisa.split(','))
        C2, mud_div = ajusta_divisa(C, V, F, adj, ev, ca, cb)
    C2, rodadas = limpa_ilhas(C2, adj, ar)
    n2, lab2 = componentes(C2, adj, len(F))
    area2 = np.bincount(lab2, weights=ar, minlength=n2)
    r = {'objeto': obj['nome'], 'arquivo': obj['arquivo'], 'regioes_antes': int(antes), 'regioes_depois': int(n2),
         'faces_divisa': mud_div, 'rodadas_ilhas': rodadas, 'faces_mudadas': int((C2 != C).sum()),
         'ilhas_que_sobraram_mm2': round(float(area2[area2 < a.ilha_min].sum()), 3)}
    rel.append(r)
    print(f"{obj['nome']}: regiões {antes} -> {n2} | faces mudadas {r['faces_mudadas']} (divisa {mud_div}) | "
          f"rodadas {[(x['ilhas'], x['area_mm2']) for x in rodadas]} | sobra < {a.ilha_min} mm²: {r['ilhas_que_sobraram_mm2']} mm² "
          f"(sem vizinha grande: casca solta ou protegida)")
    if r['faces_mudadas'] == 0: continue
    mudar = np.flatnonzero(C2 != C); k = 0; j = 0; saida = io.StringIO()
    with zin.open(obj['arquivo']) as f:
        for l in io.TextIOWrapper(f, encoding='utf-8'):
            if '<triangle ' in l:
                if j < len(mudar) and mudar[j] == k:
                    l = re.sub(r' paint_color="[^"]*"', '', l)
                    if C2[k] != obj['extrusor']:
                        l = l.replace('/>', f' paint_color="{codigo(int(C2[k]))}"/>', 1)
                    j += 1
                k += 1
            saida.write(l)
    novos[obj['arquivo']] = saida.getvalue().encode('utf-8')
zout = zipfile.ZipFile(a.saida, 'w', zipfile.ZIP_DEFLATED)
for it in zin.infolist():
    zout.writestr(it, novos.get(it.filename, zin.read(it.filename)))
zout.close()
print('gravado', a.saida)
if a.json:
    json.dump(rel, open(a.json, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
