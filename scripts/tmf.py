"""Leitura de projeto 3MF do Bambu Studio, sem extrair: objetos, posição na mesa, extrusor padrão,
id do G-code e malha com a pintura de cada triângulo. Usado por pintura_3mf.py, filete_no_ar.py e
ajusta_3mf.py (importe com sys.path apontando para esta pasta; não depende de nada fora da stdlib + numpy).

Formato da pintura (paint_color / paint_supports), conferido no Grogu em 09/10/2026: string hex lida
de trás para frente, um nibble por vez. Nibble: 2 bits baixos = lados divididos (0 = folha); folha ->
estado = 2 bits altos, e se der 3 o estado é o próximo nibble + 3. Dividido -> (lados + 1) filhos.
paint_color: estado 0 = extrusor padrão do objeto, n = extrusor n.  paint_supports: 1 = reforço, 2 = bloqueio.
"2C" = estado 5 inteiro; "4" = estado 1; "8" = estado 2; "0C" = estado 3; "1C" = estado 4.
"""
import io, re, zipfile
import xml.etree.ElementTree as ET
from collections import defaultdict
import numpy as np

NS = {'m': 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02',
      'p': 'http://schemas.microsoft.com/3dmanufacturing/production/2015/06'}
RV = re.compile(r'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"')
RT = re.compile(r'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"([^/]*)/>')
RPC = re.compile(r'paint_color="([0-9A-Fa-f]+)"')
RPS = re.compile(r'paint_supports="([0-9A-Fa-f]+)"')


def folhas(s):
    """{estado: fração aproximada de área} (filhos tratados como iguais)."""
    nib = [int(c, 16) for c in reversed(s)]
    pos = 0
    out = defaultdict(float)

    def le(peso):
        nonlocal pos
        code = nib[pos]; pos += 1
        lados = code & 3
        if lados == 0:
            st = code >> 2
            if st == 3:
                st = nib[pos] + 3; pos += 1
            out[st] += peso
            return
        for _ in range(lados + 1):
            le(peso / (lados + 1))
    le(1.0)
    return out


def matriz(txt):
    """transform do 3MF (12 números, vetor-linha) -> (R 3x3, t 3)."""
    M = np.array([float(v) for v in txt.split()]).reshape(4, 3)
    return M[:3], M[3]


def objetos(caminho):
    """Lista de dicts: id, nome, extrusor, arquivo (objeto interno), R, t (malha -> mesa), label (id no G-code)."""
    z = zipfile.ZipFile(caminho)
    raiz = ET.fromstring(z.read('3D/3dmodel.model'))
    comp = {}
    for o in raiz.find('m:resources', NS).findall('m:object', NS):
        c = o.find('m:components/m:component', NS)
        if c is not None:
            Rc, tc = matriz(c.get('transform', '1 0 0 0 1 0 0 0 1 0 0 0'))
            comp[o.get('id')] = (c.get('{%s}path' % NS['p']).lstrip('/'), Rc, tc)
        elif o.find('m:mesh', NS) is not None:
            comp[o.get('id')] = ('3D/3dmodel.model', np.eye(3), np.zeros(3))
    cfg = ET.fromstring(z.read('Metadata/model_settings.config')) if 'Metadata/model_settings.config' in z.namelist() else None
    info, label = {}, {}
    if cfg is not None:
        for o in cfg.findall('object'):
            md = {m.get('key'): m.get('value') for m in o.findall('metadata') if m.get('key')}
            info[o.get('id')] = md
        for mi in cfg.iter('model_instance'):
            md = {m.get('key'): m.get('value') for m in mi.findall('metadata')}
            label[md.get('object_id')] = int(md['identify_id']) if md.get('identify_id') else None
    out = []
    for it in raiz.find('m:build', NS).findall('m:item', NS):
        oid = it.get('objectid')
        arq, Rc, tc = comp[oid]
        Ri, ti = matriz(it.get('transform', '1 0 0 0 1 0 0 0 1 0 0 0'))
        md = info.get(oid, {})
        out.append({'id': oid, 'nome': md.get('name', oid), 'extrusor': int(md.get('extruder', 1)),
                    'arquivo': arq, 'R': Rc @ Ri, 't': tc @ Ri + ti, 'label': label.get(oid)})
    return out


def malha(caminho, obj, pintura=True):
    """(V na mesa Nx3, F Mx3, cores M (extrusor dominante), reforco M bool) do objeto."""
    z = zipfile.ZipFile(caminho)
    V, F, C, S = [], [], [], []
    with z.open(obj['arquivo']) as f:
        for l in io.TextIOWrapper(f, encoding='utf-8'):
            if '<vertex' in l:
                m = RV.search(l); V.append((float(m[1]), float(m[2]), float(m[3])))
            elif '<triangle ' in l:
                m = RT.search(l); F.append((int(m[1]), int(m[2]), int(m[3])))
                if pintura:
                    pc = RPC.search(m[4]); ps = RPS.search(m[4])
                    if pc:
                        e = folhas(pc[1]); st = max(e, key=e.get)
                    else:
                        st = 0
                    C.append(obj['extrusor'] if st == 0 else st)
                    S.append(bool(ps and 1 in folhas(ps[1])))
    V = np.array(V) @ obj['R'] + obj['t']
    return V, np.array(F, dtype=np.int64), np.array(C), np.array(S, bool)
