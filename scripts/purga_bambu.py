# Tabela de purga do Bambu Studio (FlushVolCalc, modo padrão) + volume do bico.
import colorsys, math, sys
def vol(src, dst, bico=92):
    s = [int(src[i:i + 2], 16) / 255 for i in (1, 3, 5)]; d = [int(dst[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    if src.upper() == dst.upper(): return 0
    h1, s1, v1 = colorsys.rgb_to_hsv(*s); h2, s2, v2 = colorsys.rgb_to_hsv(*d)
    h1 *= 2 * math.pi; h2 *= 2 * math.pi
    dx = math.cos(h1) * s1 * v1 - math.cos(h2) * s2 * v2; dy = math.sin(h1) * s1 * v1 - math.sin(h2) * s2 * v2
    hs = min(1.2, math.hypot(dx, dy)) * 230
    l1 = 0.3 * s[0] + 0.59 * s[1] + 0.11 * s[2]; l2 = 0.3 * d[0] + 0.59 * d[1] + 0.11 * d[2]
    lu = (l2 - l1) ** 0.7 * 560 if l2 >= l1 else (l1 - l2) * 80
    f = math.sqrt(hs * hs + lu * lu + hs * lu)          # 3º lado do triângulo com 120°
    return int(max(f, 60) + bico)
if __name__ == '__main__':
    cores = ['#FFFFFF', '#7C4B00', '#FCECD6', '#161616']
    real = [0, 238, 152, 165, 585, 0, 534, 153, 196, 202, 0, 182, 617, 367, 609, 0]
    calc = [vol(a, b) for a in cores for b in cores]
    print('calculado', calc); print('do arquivo', real); print('diferença máx', max(abs(x - y) for x, y in zip(calc, real)))
    for nome, g in [('ouro metálico', '#D4AF37'), ('ouro claro', '#E4BD68'), ('mostarda/ouro escuro', '#C9A227'), ('amarelo-ouro', '#F2C230'), ('vermelho (comparação)', '#C1272D')]:
        print(f'{nome:22s} {g}: branco→dourado {vol("#FFFFFF", g)}  dourado→branco {vol(g, "#FFFFFF")}  pele→dourado {vol("#FCECD6", g)}  dourado→pele {vol(g, "#FCECD6")}  marrom→dourado {vol("#7C4B00", g)}  dourado→marrom {vol(g, "#7C4B00")}')
