"""Gera uma cópia de um projeto 3MF com ajustes de configuração e/ou reforço de suporte pintado.

Uso:
  python ajusta_3mf.py entrada.3mf saida.3mf [--set chave=valor ...] [--copiar-filamento outro.3mf]
         [--reforco grupos.json --grupos 0,1,2 [--raio 1.5]]

--set chave=valor     valor em JSON ("30", "[\"0.7\"]") ou texto. Se a chave guarda lista e o valor é
                      escalar, repete o valor para todos os itens (ex.: um por filamento).
--copiar-filamento    copia os ajustes de filamento do 1º filamento de outro projeto para todos os
                      filamentos deste (perfil calibrado; cores e purga deste projeto ficam).
--reforco             pinta reforço de suporte (paint_supports="4") nos triângulos voltados para baixo a
                      até --raio mm dos pontos dos grupos escolhidos (saída de filete_no_ar.py --json).

SEMPRE atualiza Metadata/project_settings.config -> different_settings_to_system. Motivo (medido
09/10/2026, Grogu): o Studio, ao ABRIR o projeto, remonta o perfil de fábrica e só reaplica as chaves
dessa lista. Arquivo com limiar 30 e camada 0,20 abriu mostrando 25 e 0,16. O CLI lê o arquivo inteiro,
então o fatiamento por linha de comando não mostra o problema: conferir abrindo no Studio.
Depois de gerar: fatiar e conferir no G-code (cabeçalho "; chave = valor") E abrir no Studio.
"""
import argparse, io, json, os, re, sys, zipfile
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tmf

ap = argparse.ArgumentParser()
ap.add_argument('entrada'); ap.add_argument('saida')
ap.add_argument('--set', action='append', default=[]); ap.add_argument('--copiar-filamento')
ap.add_argument('--reforco'); ap.add_argument('--grupos', default=''); ap.add_argument('--raio', type=float, default=1.5)
a = ap.parse_args()
assert os.path.abspath(a.entrada) != os.path.abspath(a.saida), 'não sobrescreva o arquivo de origem'

zin = zipfile.ZipFile(a.entrada)
cfg = json.loads(zin.read('Metadata/project_settings.config'))
nfil = len(cfg['filament_colour'])
aj = {}
PROJETO = {'flush_multiplier', 'curr_bed_type'}                       # do projeto, não de perfil
IDENT = {'filament_settings_id', 'filament_ids', 'filament_vendor', 'filament_type'}
NAO_COPIAR = {'filament_colour', 'filament_colour_type', 'filament_map', 'filament_volume_map', 'flush_volumes_matrix',
              'flush_volumes_vector', 'flush_multiplier', 'filament_multi_colour', 'filament_nozzle_map'}
if a.copiar_filamento:
    outro = json.loads(zipfile.ZipFile(a.copiar_filamento).read('Metadata/project_settings.config'))
    for k, v in outro.items():
        if k in NAO_COPIAR or k not in cfg: continue
        if isinstance(v, list) and isinstance(cfg[k], list) and len(cfg[k]) == nfil and len(v) >= 1 and v[:1] != cfg[k][:1]:
            aj[k] = v[:1] * nfil
    if outro.get('curr_bed_type') and outro['curr_bed_type'] != cfg.get('curr_bed_type'):
        aj['curr_bed_type'] = outro['curr_bed_type']
for s in a.set:
    k, v = s.split('=', 1)
    assert k in cfg, f'chave inexistente no projeto: {k}'
    try: v = json.loads(v)
    except json.JSONDecodeError: pass
    if isinstance(v, (int, float)): v = str(v)
    if isinstance(cfg[k], list) and not isinstance(v, list): v = [v] * len(cfg[k])
    aj[k] = v
dif = cfg.get('different_settings_to_system', [''] * (nfil + 2))
proc = set(dif[0].split(';')) - {''}; fil = set()
for k, v in aj.items():
    cfg[k] = v
    if k in PROJETO or k in IDENT: continue
    (fil if isinstance(v, list) and len(v) == nfil and k.startswith(('filament_', 'nozzle_', 'hot_plate', 'cool_plate', 'eng_plate',
     'textured_plate', 'supertack', 'fan_', 'overhang_fan', 'additional_cooling', 'close_', 'slow_down_layer', 'pre_start',
     'temperature_', 'impact_', 'reduce_fan', 'during_print', 'complete_print', 'full_fan', 'first_x_layer'))
     else proc).add(k)
dif[0] = ';'.join(sorted(proc))
for i in range(1, 1 + nfil):
    dif[i] = ';'.join(sorted((set(dif[i].split(';')) - {''}) | fil))
cfg['different_settings_to_system'] = dif
print('ajustes:', {k: (v[0] if isinstance(v, list) and v else v) for k, v in aj.items()})

reforco = {}
if a.reforco:
    d = json.load(open(a.reforco)); h = d.get('h', 0.2)
    escolhidos = [d['grupos'][int(i)] for i in a.grupos.split(',') if i != '']
    from scipy.spatial import cKDTree
    for obj in tmf.objetos(a.entrada):
        gs = [g for g in escolhidos if g['label'] == obj['label']]
        if not gs: continue
        pts = np.array([p[:3] for p in d['pontos'] if p[3] == obj['label'] and any(
            all(g['min'][k] - 0.01 <= p[k] <= g['max'][k] + 0.01 for k in range(3)) for g in gs)], float)
        pts[:, 2] -= h
        V, F, _, _ = tmf.malha(a.entrada, obj, pintura=False)
        tri = V[F]; c = tri.mean(1); n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
        sel = np.where(np.isfinite(cKDTree(pts).query(c, distance_upper_bound=a.raio)[0]) & (n[:, 2] < -0.2))[0]
        reforco[obj['arquivo']] = set(sel.tolist())
        print(f"reforço em {obj['nome']}: {len(sel)} triângulos, z {c[sel, 2].min():.1f}-{c[sel, 2].max():.1f}" if len(sel) else f"reforço em {obj['nome']}: nada")

zout = zipfile.ZipFile(a.saida, 'w', zipfile.ZIP_DEFLATED, compresslevel=1)
for it in zin.infolist():
    if it.filename == 'Metadata/project_settings.config':
        zout.writestr(it.filename, json.dumps(cfg, indent=4)); continue
    if it.filename in reforco:
        alvo = reforco[it.filename]; n = 0
        with zin.open(it) as f, zout.open(it.filename, 'w', force_zip64=True) as w:
            for l in io.TextIOWrapper(f, encoding='utf-8'):
                if '<triangle ' in l:
                    if n in alvo:
                        l = re.sub(r' paint_supports="[0-9A-Fa-f]*"', '', l).replace('/>', ' paint_supports="4"/>', 1)
                    n += 1
                w.write(l.encode('utf-8'))
        continue
    zout.writestr(it, zin.read(it))
zout.close()
print('gravado', a.saida)
