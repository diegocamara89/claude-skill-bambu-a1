"""Roda DENTRO do Blender (pelo roda_blender.py da skill modelagem-3d). Renderiza as peças de um 3MF com a cor
pintada de cada triângulo (cores reais do projeto) e, opcionalmente, marca pontos/grupos em magenta com closes
de várias direções e CONTA os pixels magenta visíveis em cada vista.

  python <modelagem-3d>/scripts/roda_blender.py render_pintura_3mf.py --resultado res.json \
         --args projeto.3mf pasta_saida res.json [grupos.json [0,1,2]]

grupos.json: saída de filete_no_ar.py --json (centro/min/max na mesa) ou lista [{"centro":[x,y,z],"raio":r}].
Sem grupos: só as 4 vistas gerais de cada peça.

Contagem de magenta: o magenta renderizado sai ESCURECIDO pela luz (≈ 155,60,160; na sombra ≈ 117,31,122).
Filtro r>100, b>100, g<0,6·min(r,b). O primeiro filtro (r,b>200) dava 0 em tudo e levou a uma conclusão
falsa ("mancha escondida de 7 direções"). Por isso o resultado traz 'faces' (seleção não vazia) e o script
avisa quando todas as vistas dão 0: ou está escondido, ou a seleção/filtro falhou — confira a imagem.
Vistas: frente, trás, esquerda, direita, de baixo e baixo-fora. Algo "escondido" precisa de 0 também na vista de baixo.
"""
import bpy, json, os, sys, zipfile
import numpy as np
from mathutils import Vector

args = sys.argv[sys.argv.index('--') + 1:]
projeto, pasta, saida = args[0], args[1], args[2]
grupos = json.load(open(args[3])) if len(args) > 3 else []
if isinstance(grupos, dict): grupos = grupos.get('grupos', [])
if len(args) > 4: grupos = [grupos[int(i)] for i in args[4].split(',')]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tmf

os.makedirs(pasta, exist_ok=True)
cfg = json.loads(zipfile.ZipFile(projeto).read('Metadata/project_settings.config'))
hexs = cfg.get('filament_colour', [])
bpy.ops.wm.read_factory_settings(use_empty=True)
cena = bpy.context.scene
cena.render.engine = 'BLENDER_WORKBENCH'
cena.display.shading.light = 'STUDIO'; cena.display.shading.color_type = 'MATERIAL'; cena.display.shading.show_cavity = True
cena.render.resolution_x = cena.render.resolution_y = 900
cena.world = bpy.data.worlds.new('m'); cena.world.color = (0.12, 0.12, 0.13)
def srgb(hx):
    c = [int(hx[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return tuple(((v + 0.055) / 1.055) ** 2.4 if v > 0.04045 else v / 12.92 for v in c) + (1,)
cam_d = bpy.data.cameras.new('cam'); cam_d.type = 'ORTHO'; cam_d.clip_end = 5000
cam = bpy.data.objects.new('cam', cam_d); cena.collection.objects.link(cam); cena.camera = cam
res = {'imagens': [], 'marcas': [], 'avisos': []}

def mira(alvo, d, escala, arq):
    d = Vector(d).normalized(); cam.location = Vector(alvo) + d * 1000
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler(); cam_d.ortho_scale = escala
    cena.render.filepath = arq; bpy.ops.render.render(write_still=True); res['imagens'].append(arq)
    img = bpy.data.images.load(arq); px = np.array(img.pixels[:]).reshape(-1, 4)[:, :3] * 255; bpy.data.images.remove(img)
    return int(((px[:, 0] > 100) & (px[:, 2] > 100) & (px[:, 1] < 0.6 * np.minimum(px[:, 0], px[:, 2]))).sum())

for obj in tmf.objetos(projeto):
    V, F, C, _ = tmf.malha(projeto, obj)
    me = bpy.data.meshes.new(obj['nome'])
    me.vertices.add(len(V)); me.vertices.foreach_set('co', V.astype(np.float32).ravel())
    me.loops.add(F.size); me.loops.foreach_set('vertex_index', F.astype(np.int32).ravel())
    me.polygons.add(len(F)); me.polygons.foreach_set('loop_start', np.arange(0, F.size, 3, dtype=np.int32))
    me.update(); me.validate(verbose=False)
    cores = sorted(set(C.tolist()))
    for c in cores:
        m = bpy.data.materials.new(f'f{c}'); m.diffuse_color = srgb(hexs[c - 1]) if 0 < c <= len(hexs) else (0.5, 0.5, 0.5, 1)
        me.materials.append(m)
    mag = bpy.data.materials.new('mag'); mag.diffuse_color = (1, 0, 1, 1); me.materials.append(mag); imag = len(cores)
    base = np.array([cores.index(c) for c in C], dtype=np.int32); me.polygons.foreach_set('material_index', base)
    ob = bpy.data.objects.new(obj['nome'], me); cena.collection.objects.link(ob)
    lo, hi = V.min(0), V.max(0); centro = (lo + hi) / 2; alto = float((hi - lo).max())
    nome = os.path.splitext(obj['nome'])[0].replace(' ', '_')
    for vn, d in (('frente', (0, -1, 0)), ('tras', (0, 1, 0)), ('esq', (-1, 0, 0)), ('dir', (1, 0, 0))):
        mira(centro, d, alto * 1.1, f'{pasta}/{nome}_{vn}.png')
    cs = V[F].mean(1)
    for i, g in enumerate(grupos):
        if 'label' in g and g['label'] != obj['label']: continue
        p = np.array(g['centro'], float)
        if 'label' not in g and not (np.all(p >= lo - 1) and np.all(p <= hi + 1)): continue
        raio = g.get('raio') or max(np.linalg.norm(np.array(g['max']) - np.array(g['min'])) / 2, 1.0) + 0.8
        sel = np.linalg.norm(cs - p, axis=1) < raio
        mi = base.copy(); mi[sel] = imag; me.polygons.foreach_set('material_index', mi); me.update()
        fora = np.array([p[0] - centro[0], p[1] - centro[1], 0.0]); fora /= (np.linalg.norm(fora) + 1e-9)
        dirs = {'frente': (0, -1, 0), 'tras': (0, 1, 0), 'esq': (-1, 0, 0), 'dir': (1, 0, 0), 'baixo': (0, 0, -1),
                'baixo_fora': tuple(fora * 0.6 + np.array([0, 0, -0.8]))}
        cont = {vn: mira(p, d, max(30.0, raio * 8), f'{pasta}/{nome}_m{i:02d}_{vn}.png') for vn, d in dirs.items()}
        me.polygons.foreach_set('material_index', base); me.update()
        res['marcas'].append({'grupo': i, 'objeto': obj['nome'], 'faces': int(sel.sum()), 'pixels_magenta': cont})
        if sel.sum() and not any(cont.values()):
            res['avisos'].append(f'grupo {i}: {int(sel.sum())} faces e 0 pixel em todas as vistas — escondido ou falha; olhe as imagens')
        if not sel.sum():
            res['avisos'].append(f'grupo {i}: seleção vazia (raio {raio:.1f} mm)')
    ob.hide_render = True
json.dump(res, open(saida, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
