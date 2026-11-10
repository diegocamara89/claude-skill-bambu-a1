"""Objeto de sacrificio sob medida para "purgar neste objeto" (Bambu Studio, torre ligada).

Le a purga que cai na canaleta em cada camada (blocos ; FLUSH_START..END) de um G-code fatiado
SEM objeto de sacrificio e gera um prisma quadrado escalonado cuja camada tem volume >= purga
daquela camada x margem. Lado decresce no maximo 2*h por camada para cima (45 graus): sem balanco.

uso: gera_sacrificio.py base.gcode saida.json [--margem 1.3] [--lado-min 12] [--offset auto] [--troca n]
(peca unica recebe so UMA troca por camada: gere uma peca por --troca 0, 1...)
saida.json: {"camadas": [[z_base, z_topo, lado], ...], "purga_mm3": ..., "volume_mm3": ...}
offset = z de impressao onde o objeto comeca (topo da jangada); auto = 1a camada do objeto - h.
"""
import json, math, re, sys

A = math.pi * 1.75 ** 2 / 4


def le_purga(path, troca=None):
    """{z_impressao: mm3 na canaleta}; troca=n conta so a n-esima troca (0, 1...) de cada camada."""
    por_z, z, flush, n = {}, 0.0, False, -1
    for ln in open(path, encoding='utf-8', errors='ignore'):
        if ln.startswith('; Z_HEIGHT:'):
            z = round(float(ln.split(':')[1]), 3); por_z.setdefault(z, 0.0); n = -1; continue
        if ln.startswith('M620 S') and 'A' in ln: n += 1; continue   # cada troca tem varios blocos FLUSH
        if ln.startswith('; FLUSH_START'): flush = troca is None or n == troca; continue
        if ln.startswith('; FLUSH_END'): flush = False; continue
        if flush and ln.startswith('G1'):
            m = re.search(r'E([\d.]+)', ln)
            if m: por_z[z] += float(m.group(1)) * A
    return por_z


def projeta(por_z, offset, h, margem, lado_min):
    zs = sorted(z for z in por_z if z > offset + 1e-6)
    ult = max(z for z in zs if por_z[z] > 1)
    zs = [z for z in zs if z <= ult + 1e-6]
    req = [math.sqrt(margem * por_z[z] / h) for z in zs]
    lado = [0.0] * len(zs)
    for i in range(len(zs) - 1, -1, -1):          # de cima para baixo: 45 graus
        acima = lado[i + 1] - 2 * h if i + 1 < len(zs) else 0
        lado[i] = max(req[i], acima, lado_min)
    camadas, zb = [], offset
    for z, s in zip(zs, lado):
        camadas.append([round(zb - offset, 3), round(z - offset, 3), round(s, 2)]); zb = z
    vol = sum((c[1] - c[0]) * c[2] ** 2 for c in camadas)
    return camadas, sum(por_z[z] for z in zs), vol


def malha(camadas, passo=0.5):
    """Uniao de caixas (lado arredondado para cima no passo) -> (vertices, triangulos)."""
    import manifold3d as m3
    blocos, atual = [], None
    for zb, zt, s in camadas:
        s = math.ceil(s / passo) * passo
        if atual and atual[2] == s: atual[1] = zt
        else: atual = [zb, zt, s]; blocos.append(atual)
    sol = None
    for zb, zt, s in blocos:
        c = m3.Manifold.cube([s, s, zt - zb], center=True).translate([0, 0, (zb + zt) / 2])
        sol = c if sol is None else sol + c
    mesh = sol.to_mesh()
    return mesh.vert_properties[:, :3].tolist(), mesh.tri_verts.tolist(), blocos


if __name__ == '__main__':
    a = sys.argv[1:]
    opt = {'--margem': 1.3, '--lado-min': 12.0, '--offset': None, '--h': 0.2, '--troca': None}
    for k in list(opt):
        if k in a: i = a.index(k); opt[k] = float(a[i + 1]); del a[i:i + 2]
    base, saida = a
    pz = le_purga(base, None if opt['--troca'] is None else int(opt['--troca']))
    off = opt['--offset'] if opt['--offset'] is not None else min(z for z, v in pz.items() if v > 1) - opt['--h']
    cam, purga, vol = projeta(pz, off, opt['--h'], opt['--margem'], opt['--lado-min'])
    v, t, blocos = malha(cam)
    json.dump({'offset': off, 'camadas': cam, 'blocos': blocos, 'purga_mm3': purga, 'volume_mm3': vol,
               'vertices': v, 'triangulos': t}, open(saida, 'w'))
    print(f"purga {purga/1000*1.27:.1f} g | objeto {vol/1000*1.27:.1f} g | altura {cam[-1][1]:.1f} mm | "
          f"lado {min(c[2] for c in cam):.1f}-{max(c[2] for c in cam):.1f} mm | {len(blocos)} degraus, {len(t)} triangulos")
