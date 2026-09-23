"""Monta uma placa 3MF com vários cupons, cada um com seus próprios ajustes de fatiador.

Uso:
  python placa_ab.py base.3mf saida.3mf A.ply "B.ply:support_type=normal(auto)" [--espaco 40] [--girar 90]

base.3mf   projeto de onde vem TODA a configuração (Metadata/project_settings.config). Use o 3MF
           que foi de fato impresso, para o cupom herdar exatamente o que a peça teve.
malha[:chave=valor,...]
           uma cópia por argumento, lado a lado em X, centradas em (128, 128). O que vem depois
           de ':' vira ajuste POR OBJETO no model_settings.config (ex.: support_type,
           sparse_infill_density). Só a cópia que declara muda; as outras seguem a base.
--girar    gira cada cópia em Z (graus) em torno do próprio centro. Use para reproduzir a
           orientação com que a peça foi para a mesa: o G-code impresso pode estar girado em
           relação ao arquivo original, e isso muda de que lado a ventoinha sopra.

Ajuste por objeto NÃO aparece no cabeçalho do G-code: o cabeçalho mostra o valor global. Conferir
nas linhas de extrusão (ex.: cobertura_suporte.py por cópia).
O script imprime a posição de cada cópia na mesa: é o --desloc para cobertura_suporte.py.

Validado em 23/09/2026: duas cópias, uma com support_type=normal(auto); o G-code saiu com árvore
numa e grade na outra.
"""
import argparse, os, sys, uuid, zipfile, io
import numpy as np, trimesh

ap = argparse.ArgumentParser()
ap.add_argument("base"); ap.add_argument("saida"); ap.add_argument("copias", nargs="+")
ap.add_argument("--espaco", type=float, default=40.0, help="distância entre centros, mm")
ap.add_argument("--girar", type=float, default=0.0)
a = ap.parse_args()

zb = zipfile.ZipFile(a.base)
cfg = zb.read("Metadata/project_settings.config")
cab_modelo = zb.read("3D/3dmodel.model").decode("utf-8")
cab_modelo = cab_modelo[:cab_modelo.index("<resources>")]
NS = ('<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" '
      'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
      'xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" '
      'xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" requiredextensions="p">\n'
      ' <metadata name="BambuStudio:3mfVersion">1</metadata>\n')

arq = {}
comps, items, rels, objs, insts, asm, cut = [], [], [], [], [], [], []
n = len(a.copias)
print(f"{'copia':24} {'centro X':>9} {'centro Y':>9} {'altura':>7}  ajustes")
for i, esp in enumerate(a.copias):
    caminho, _, extras = esp.partition(":")
    if os.path.splitext(caminho)[1].lower() == ".stl":
        print(f"AVISO {caminho}: STL arredonda para float32; prefira PLY/OBJ")
    m = trimesh.load(caminho, force="mesh", process=False)
    if a.girar:
        c = m.bounds.mean(0)
        m.apply_transform(trimesh.transformations.rotation_matrix(np.radians(a.girar), [0, 0, 1], c))
    lo, hi = m.bounds; h = hi[2] - lo[2]
    V = m.vertices - (lo + hi) / 2; F = m.faces
    x = 128 + (i - (n - 1) / 2) * a.espaco
    nome = os.path.splitext(os.path.basename(caminho))[0]
    ajustes = [kv.split("=", 1) for kv in extras.split(",") if "=" in kv]
    mid, oid, fn = 2 * i + 1, 2 * i + 2, f"object_{i + 1}.model"
    buf = io.StringIO()
    buf.write(NS + f' <resources>\n  <object id="{mid}" p:UUID="{uuid.uuid4()}" type="model">\n   <mesh>\n    <vertices>\n')
    buf.write("".join(f'     <vertex x="{v[0]:.7g}" y="{v[1]:.7g}" z="{v[2]:.7g}"/>\n' for v in V))
    buf.write("    </vertices>\n    <triangles>\n")
    buf.write("".join(f'     <triangle v1="{t[0]}" v2="{t[1]}" v3="{t[2]}"/>\n' for t in F))
    buf.write("    </triangles>\n   </mesh>\n  </object>\n </resources>\n <build/>\n</model>\n")
    arq[f"3D/Objects/{fn}"] = buf.getvalue()
    comps.append(f'  <object id="{oid}" p:UUID="{uuid.uuid4()}" type="model">\n   <components>\n'
                 f'    <component p:path="/3D/Objects/{fn}" objectid="{mid}" p:UUID="{uuid.uuid4()}" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>\n'
                 f'   </components>\n  </object>\n')
    tr = f"1 0 0 0 1 0 0 0 1 {x:.4f} 128 {h / 2:.6f}"
    items.append(f'  <item objectid="{oid}" p:UUID="{uuid.uuid4()}" transform="{tr}" printable="1"/>\n')
    rels.append(f' <Relationship Target="/3D/Objects/{fn}" Id="rel-{i + 1}" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>\n')
    extra = "".join(f'    <metadata key="{k.strip()}" value="{v.strip()}"/>\n' for k, v in ajustes)
    objs.append(f'  <object id="{oid}">\n    <metadata key="name" value="{nome}"/>\n    <metadata key="extruder" value="1"/>\n{extra}'
                f'    <metadata face_count="{len(F)}"/>\n'
                f'    <part id="{mid}" subtype="normal_part">\n      <metadata key="name" value="{nome}"/>\n'
                f'      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>\n'
                f'      <mesh_stat face_count="{len(F)}" edges_fixed="0" degenerate_facets="0" facets_removed="0" facets_reversed="0" backwards_edges="0"/>\n'
                f'    </part>\n  </object>\n')
    insts.append(f'    <model_instance>\n      <metadata key="object_id" value="{oid}"/>\n      <metadata key="instance_id" value="0"/>\n'
                 f'      <metadata key="identify_id" value="{100 + i}"/>\n    </model_instance>\n')
    asm.append(f'   <assemble_item object_id="{oid}" instance_id="0" transform="{tr}" offset="0 0 0" />\n')
    cut.append(f' <object id="{oid}">\n  <cut_id id="0" check_sum="1" connectors_cnt="0"/>\n </object>\n')
    # deslocamento que leva a malha de entrada (depois do giro) às coordenadas da mesa
    d = np.array([x, 128, h / 2]) - (lo + hi) / 2
    print(f"{nome:24} {x:9.2f} {128:9.2f} {h:7.2f}  {extras or '(base)'}   --desloc {d[0]:.4f} {d[1]:.4f} {d[2]:.4f}")

arq["3D/3dmodel.model"] = cab_modelo + "<resources>\n" + "".join(comps) + " </resources>\n" \
    + f' <build p:UUID="{uuid.uuid4()}">\n' + "".join(items) + " </build>\n</model>\n"
arq["3D/_rels/3dmodel.model.rels"] = ('<?xml version="1.0" encoding="UTF-8"?>\n<Relationships '
                                      'xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n' + "".join(rels) + "</Relationships>\n")
arq["Metadata/model_settings.config"] = (
    '<?xml version="1.0" encoding="UTF-8"?>\n<config>\n' + "".join(objs)
    + '  <plate>\n    <metadata key="plater_id" value="1"/>\n    <metadata key="plater_name" value=""/>\n'
      '    <metadata key="locked" value="false"/>\n' + "".join(insts) + "  </plate>\n  <assemble>\n" + "".join(asm)
    + "  </assemble>\n</config>\n")
arq["Metadata/cut_information.xml"] = '<?xml version="1.0" encoding="utf-8"?>\n<objects>\n' + "".join(cut) + "</objects>\n"
arq["Metadata/project_settings.config"] = cfg
arq["[Content_Types].xml"] = ('<?xml version="1.0" encoding="UTF-8"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n'
                              ' <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>\n'
                              ' <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>\n'
                              ' <Default Extension="png" ContentType="image/png"/>\n'
                              ' <Default Extension="gcode" ContentType="text/x.gcode"/>\n</Types>\n')
arq["_rels/.rels"] = ('<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
                      ' <Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>\n'
                      '</Relationships>\n')
ordem = ["[Content_Types].xml", "_rels/.rels"] + sorted(k for k in arq if k not in ("[Content_Types].xml", "_rels/.rels"))
with zipfile.ZipFile(a.saida, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    for k in ordem:
        z.writestr(k, arq[k])
print(f"salvo: {a.saida} ({os.path.getsize(a.saida) // 1024} KB). Fatiar e conferir no G-code:")
print('  "C:/Program Files/Bambu Studio/bambu-studio.exe" --slice 0 --outputdir <pasta> ' + a.saida)
