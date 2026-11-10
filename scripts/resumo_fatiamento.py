"""Resumo de um fatiamento do CLI do Bambu (pasta com result.json e plate_1.gcode), pensado para multicor.

Uso:  python resumo_fatiamento.py pasta_saida [rotulo] [--faixa 5]

Mostra: tempo, gramas (total e na peça), trocas, purga (extrusão entre M620 e M621), torre, suporte,
paredes, tempo por tipo, TROCAS POR FAIXA DE ALTURA e ONDE CAI A 1ª EXTRUSÃO DEPOIS DE CADA TROCA
(torre = protegida; parede externa = pode manchar/bolinha à vista). Grava medida.json na pasta.

Notas medidas (Grogu, 09/10/2026): M620 S<n>A usa índice 0 (S0 = filamento 1); S255 = descarga final,
não é troca. Cada troca custou ~100 s e ~0,3 g (A1 + BMCU, PLA e PETG). Sem torre, a 1ª extrusão depois
da troca cai na peça (82 parede interna, 6 externa, de 89). Purgar no preenchimento NÃO reduziu a purga
nem mudou onde cai a 1ª extrusão (A1 purga na calha). Pacotes de otimização somam 7–19% menos que a
soma dos ganhos isolados: medir o pacote, não somar.
"""
import argparse, collections, json, re
ap = argparse.ArgumentParser(); ap.add_argument('pasta'); ap.add_argument('rotulo', nargs='?', default='')
ap.add_argument('--faixa', type=float, default=5.0); a = ap.parse_args()
r = json.load(open(a.pasta + '/result.json')); p = r['sliced_plates'][0]
E = collections.Counter(); dentro = False; feat = '?'; cur = None; z = 0.0; ncam = 0
por_faixa = collections.Counter(); pares = collections.Counter(); primeira = collections.Counter(); espera = False
for l in open(a.pasta + '/plate_1.gcode', encoding='utf-8', errors='ignore'):
    if l.startswith('; Z_HEIGHT:'):
        z = float(l.split(':')[1]); ncam += 1
    elif l.startswith('M620 S') and l[6].isdigit():
        dentro = True; n = int(re.match(r'M620 S(\d+)', l).group(1)) + 1
        if n < 256 and cur is not None and n != cur:
            por_faixa[int(z // a.faixa)] += 1; pares[(cur, n)] += 1; espera = True
        cur = n if n < 256 else cur
    elif l.startswith('M621 S'):
        dentro = False
    elif l.startswith('; FEATURE:'):
        feat = l.split(':', 1)[1].strip()
        if espera and not dentro: primeira[feat] += 1; espera = False
    elif l.startswith(('G1', 'G0', 'G2', 'G3')) and ' E' in l:
        m = re.search(r' E(-?[\d.]+)', l)
        if m: E['purga' if dentro else feat] += float(m.group(1))
dens = float(r.get('filament_density', [1.26])[0]) if isinstance(r.get('filament_density'), list) else 1.26
g = lambda mm: mm * 3.14159 * 0.875 ** 2 * dens / 1000
res = {'rotulo': a.rotulo, 'tempo_h': round(p['total_predication'] / 3600, 2),
       'total_g': round(sum(f['total_used_g'] for f in p['filaments']), 1),
       'na_peca_g': round(sum(f['main_used_g'] for f in p['filaments']), 1),
       'trocas': p['filament_change_times'], 'trocas_gcode': sum(por_faixa.values()), 'camadas': ncam,
       'purga_g': round(g(E['purga']), 1), 'torre_g': round(g(E['Prime tower']), 1),
       'suporte_g': round(g(E['Support']) + g(E['Support interface']), 1),
       'paredes_g': round(g(E['Inner wall']) + g(E['Outer wall']), 1),
       'por_filamento_g': {f['id']: round(f['total_used_g'], 1) for f in p['filaments']},
       'tempos_h': {k: round(v / 3600, 2) for k, v in p['feature_type_times'].items() if v > 600},
       'trocas_por_faixa_mm': {f'{k * a.faixa:g}-{(k + 1) * a.faixa:g}': v for k, v in sorted(por_faixa.items())},
       'pares_de_troca': {f'{x}->{y}': v for (x, y), v in pares.most_common()},
       'primeira_extrusao_apos_troca': dict(primeira),
       'erro': r.get('error_string', ''), 'aviso': p.get('warning_message', '')}
print(json.dumps(res, ensure_ascii=False, indent=1))
json.dump(res, open(a.pasta + '/medida.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
