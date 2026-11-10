# Reduz a malha mantendo a pintura: vértices na divisa de cor ganham peso alto (não somem),
# depois cada triângulo novo herda a cor do triângulo original mais próximo.
import re, sys, numpy as np, pymeshlab
from scipy.spatial import cKDTree
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import tmf
src, dst, alvo = sys.argv[1], sys.argv[2], int(sys.argv[3])
txt = open(src, encoding='utf-8').read()
V = np.array(re.findall(r'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"', txt), float)
T = re.findall(r'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"([^/]*)/>', txt)
F = np.array([t[:3] for t in T], int)
C = np.zeros(len(F), int)
for i, t in enumerate(T):
    m = tmf.RPC.search(t[3])
    if m: e = tmf.folhas(m[1]); C[i] = max(e, key=e.get)
del txt, T
print('original', len(V), len(F), 'cores', np.bincount(C))
# vértice na divisa = toca triângulos de cores diferentes
vmin = np.full(len(V), 99); vmax = np.full(len(V), -1)
for k in range(3):
    np.minimum.at(vmin, F[:,k], C); np.maximum.at(vmax, F[:,k], C)
q = np.where(vmin != vmax, 1.0, 0.0)
ms = pymeshlab.MeshSet()
ms.add_mesh(pymeshlab.Mesh(vertex_matrix=V, face_matrix=F, v_scalar_array=q))
ms.meshing_decimation_quadric_edge_collapse(targetfacenum=alvo, qualitythr=0.5, preserveboundary=True, boundaryweight=2,
    preservenormal=True, preservetopology=True, optimalplacement=True, planarquadric=True, qualityweight=True, autoclean=True)
m = ms.current_mesh(); V2 = m.vertex_matrix(); F2 = m.face_matrix()
cen0 = V[F].mean(1); cen2 = V2[F2].mean(1)
_, idx = cKDTree(cen0).query(cen2); C2 = C[idx]
print('reduzida', len(V2), len(F2), 'cores', np.bincount(C2))
COD = {1: '4', 2: '8', 3: '0C', 4: '1C', 5: '2C'}
cab = open(src, encoding='utf-8').read(3000)
cab = cab[:cab.index('<vertices>')]
with open(dst, 'w', encoding='utf-8', newline='\n') as f:
    f.write(cab + '<vertices>\n')
    f.writelines(f'     <vertex x="{x:.6g}" y="{y:.6g}" z="{z:.6g}"/>\n' for x, y, z in V2)
    f.write('    </vertices>\n    <triangles>\n')
    f.writelines(f'     <triangle v1="{a}" v2="{b}" v3="{c}"' + (f' paint_color="{COD[k]}"' if k else '') + '/>\n' for (a, b, c), k in zip(F2, C2))
    f.write('    </triangles>\n   </mesh>\n  </object>\n </resources>\n <build/>\n</model>\n')
