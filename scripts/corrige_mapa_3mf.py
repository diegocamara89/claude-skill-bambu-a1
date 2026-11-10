# Refaz o mapa de objetos de um .gcode.3mf do Bambu para o "pular objeto" da tela funcionar:
# Metadata/plate_1.json -> bbox_objects com 1 item por rótulo do G-code (+ torre, id 1000), e
# Metadata/model_settings.config -> pattern_bbox_file. Recusa se um boneco usar o id 1000 (é o da torre).
import sys, re, json, zipfile, collections
src, dst = sys.argv[1], sys.argv[2]
zi = zipfile.ZipFile(src)
g = zi.read('Metadata/plate_1.gcode').decode('utf-8', 'ignore')
cx = {}; area = collections.Counter(); cur = None; feat = ''; x = y = 0.0; torre = [1e9, 1e9, -1e9, -1e9]
for l in g.split('\n'):
    if l.startswith('; start printing object, unique label id:'): cur = int(l.split(':')[1])
    elif l.startswith('; stop printing object'): cur = None
    elif l.startswith('; FEATURE:'): feat = l[10:].strip()
    elif l.startswith(('G1 ', 'G2 ', 'G3 ')):
        mx = re.search(r'X([-\d.]+)', l); my = re.search(r'Y([-\d.]+)', l)
        if mx: x = float(mx.group(1))
        if my: y = float(my.group(1))
        if (mx or my) and re.search(r' E[\d.]', l) and 0 < x < 256 and 0 < y < 256:
            if cur is not None:
                b = cx.setdefault(cur, [1e9, 1e9, -1e9, -1e9]); b[0] = min(b[0], x); b[1] = min(b[1], y); b[2] = max(b[2], x); b[3] = max(b[3], y)
            elif feat.startswith('Prime tower'):
                torre = [min(torre[0], x), min(torre[1], y), max(torre[2], x), max(torre[3], y)]
assert 1000 not in cx, 'um objeto usa o id 1000 (reservado para a torre): renumere os identify_id e refatie'
nome = re.search(r'name="([^"]+)"', zi.read('Metadata/slice_info.config').decode()).group(1)
lh = float(re.search(r'^; layer_height = ([\d.]+)', g, re.M).group(1))
j = json.loads(zi.read('Metadata/plate_1.json'))
j['bbox_objects'] = [{'area': round((b[2] - b[0]) * (b[3] - b[1]), 3), 'bbox': b, 'id': k, 'layer_height': lh, 'name': nome} for k, b in sorted(cx.items())]
if torre[0] < 1e9: j['bbox_objects'].append({'area': 0.0, 'bbox': torre, 'id': 1000, 'layer_height': 0.0, 'name': 'wipe_tower'})
ms = zi.read('Metadata/model_settings.config').decode()
if 'pattern_bbox_file' not in ms:
    ms = ms.replace('<metadata key="pick_file" value="Metadata/pick_1.png"/>', '<metadata key="pick_file" value="Metadata/pick_1.png"/>\n    <metadata key="pattern_bbox_file" value="Metadata/plate_1.json"/>')
zo = zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED)
for it in zi.infolist():
    d = zi.read(it.filename)
    if it.filename == 'Metadata/plate_1.json': d = json.dumps(j).encode()
    elif it.filename == 'Metadata/model_settings.config': d = ms.encode()
    zo.writestr(it, d)
zo.close()
print(f'objetos no mapa: {len(cx)} (ids {min(cx)}–{max(cx)}) + torre {"sim" if torre[0] < 1e9 else "não"} | gravado {dst}')
