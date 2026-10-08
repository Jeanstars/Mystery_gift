#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerador dos graficos do Mystery Gift (CFRU).

Gera:
  projeto/src/mystery_gift_gfx.c   -> tiles/mapas/paletas (menu = 2 paletas x 16 = 32 cores)
  previews/paleta_32_cores.png
(As imagens de previa da tela sao capturas REAIS do emulador: veja ferramentas/teste_emulador)

Uso:  python3 gerar_mystery_gift.py <pasta_raiz_do_pacote>
Precisa de: Pillow (pip install pillow)
"""
import sys, os, math, random
from PIL import Image, ImageDraw, ImageFont

ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), '..')
W, H = 240, 160

def c5(r, g, b):  # 0..255 -> 0..31 -> de volta para 8 bits (o que o GBA realmente mostra)
    return (r >> 3, g >> 3, b >> 3)
def rgb(h):
    h = h.lstrip('#'); return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
def gba(h):  # cor como o GBA mostra
    r, g, b = c5(*rgb(h)); return (r*255//31, g*255//31, b*255//31)
def to555(h):
    r, g, b = c5(*rgb(h)); return r | (g << 5) | (b << 10)

# ---------------------------------------------------------------- paletas
# PALETA 0 (interface) - indices 1..4 sao as cores de TEXTO usadas no C
PAL0 = ['#1B1040', '#FFFFFF', '#8A7DB8', '#2A1A5E', '#FFD34D', '#B8860B', '#3E2C86', '#5B47B0',
        '#FF5E7E', '#A81E4B', '#7DE3FF', '#1E2F6E', '#0E0A24', '#E8E0FF', '#4CD99A', '#1F8F63']
# PALETA 1 (fundo degrade + brilhos)
PAL1 = ['#1B1040', '#14093A', '#1B0F4A', '#23135A', '#2C186B', '#361E7C', '#42268E', '#5030A0',
        '#5E3AB0', '#6C46BE', '#8E7BD0', '#C9BDF2', '#FFE9A8', '#FFD34D', '#FF9EC0', '#FFFFFF']
BGPAL = PAL0 + PAL1                      # 32 cores
BGPAL_RGB = [gba(c) for c in BGPAL]

# PALETA DE OBJETOS A: bau + brilhos
PALA = ['#000000', '#3A0A1E', '#E5384F', '#FF7A8A', '#A8203A', '#FFD34D', '#FFF0A0', '#C9962B',
        '#FFFFFF', '#FFF7D0', '#7DE3FF', '#FF9EC0', '#5A1230', '#FFB347', '#B8E8FF', '#8A7DB8']
# PALETA DE OBJETOS B: cursor + seta
PALB = ['#000000', '#FFD34D', '#FFFFFF', '#B8860B', '#FFF0A0', '#7DE3FF', '#0E0A24', '#FF5E7E',
        '#000000', '#000000', '#000000', '#000000', '#000000', '#000000', '#000000', '#000000']
PALA_RGB = [gba(c) for c in PALA]; PALB_RGB = [gba(c) for c in PALB]

def nearest(col, pal):
    best, bi = 1e18, 0
    for i, p in enumerate(pal):
        d = (col[0]-p[0])**2 + (col[1]-p[1])**2 + (col[2]-p[2])**2
        if d < best: best, bi = d, i
    return bi

# ---------------------------------------------------------------- desenho do fundo (RGB com cores das paletas)
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]
def gradient(draw_px, y0, y1, steps, x0=0, x1=W, flip=False):
    """degrade vertical dithered usando pal1[1..9]"""
    n = len(steps)
    for y in range(y0, y1):
        t = (y - y0) / max(1, (y1 - y0 - 1)) * (n - 1)
        if flip: t = (n - 1) - t
        lo = int(t); fr = t - lo
        for x in range(x0, x1):
            th = (BAYER[y & 3][x & 3] + 0.5) / 16.0
            k = lo + (1 if fr > th and lo + 1 < n else 0)
            draw_px((x, y), steps[k])

GRAD = [BGPAL_RGB[16 + i] for i in range(1, 10)]   # pal1[1..9]
def P0(i): return BGPAL_RGB[i]
def P1(i): return BGPAL_RGB[16 + i]

def rrect(d, box, r, fill=None, outline=None, w=1):
    d.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=w)

def mini_gift(d, x, y):  # icone 16x16 (usa pal0)
    d.rectangle((x+1, y+6, x+14, y+15), fill=P0(8), outline=P0(9))
    d.rectangle((x, y+3, x+15, y+7), fill=P0(8), outline=P0(9))
    d.rectangle((x+7, y+3, x+8, y+15), fill=P0(4))
    d.rectangle((x, y+5, x+15, y+5), fill=P0(4))
    d.ellipse((x+2, y, x+7, y+4), outline=P0(4)); d.ellipse((x+8, y, x+13, y+4), outline=P0(4))

def star4(d, cx, cy, r, col):
    d.line((cx-r, cy, cx+r, cy), fill=col); d.line((cx, cy-r, cx, cy+r), fill=col)
    d.point((cx, cy), fill=P1(15))

# ---------------------------------------------------------------- layout (os MESMOS numeros do mystery_gift.c)
# Campos do codigo: cada casa ocupa 3x2 tiles (24x16 px) e fica alinhada em tiles, porque as letras digitadas
# sao trocadas direto no mapa de tiles do BG1 (sem texto, sem fonte pequena).
SLOT_N = 8
SLOT_COL0, SLOT_ROW = 3, 5                 # primeira casa: coluna 3, linha 5 (x=24, y=40)
SLOT_CELL_W, SLOT_CELL_H = 24, 16
SLOT_X0, SLOT_Y = SLOT_COL0*8, SLOT_ROW*8
KEY_X0, KEY_Y0, KEY_PX, KEY_PY, KEY_W, KEY_H = 11, 63, 22, 19, 20, 17
KEYS = list("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ") + ['DEL', 'OK']   # 38 teclas
GLYPH_CHARS = list("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ")

def key_pos(i):
    if i < 36: return i % 10, i // 10
    return 6 + (i - 36), 3
def key_center(i):
    c, r = key_pos(i); return KEY_X0 + KEY_PX*c + KEY_W//2, KEY_Y0 + KEY_PY*r + KEY_H//2

# Fonte de pixels 5x7 (desenhada a mao), usada em tamanho dobrado (10x14)
F57 = {
'0':["01110","10001","10011","10101","11001","10001","01110"],
'1':["00100","01100","00100","00100","00100","00100","01110"],
'2':["01110","10001","00001","00010","00100","01000","11111"],
'3':["11110","00001","00001","01110","00001","00001","11110"],
'4':["00010","00110","01010","10010","11111","00010","00010"],
'5':["11111","10000","11110","00001","00001","10001","01110"],
'6':["00110","01000","10000","11110","10001","10001","01110"],
'7':["11111","00001","00010","00100","01000","01000","01000"],
'8':["01110","10001","10001","01110","10001","10001","01110"],
'9':["01110","10001","10001","01111","00001","00010","01100"],
'A':["01110","10001","10001","11111","10001","10001","10001"],
'B':["11110","10001","10001","11110","10001","10001","11110"],
'C':["01110","10001","10000","10000","10000","10001","01110"],
'D':["11110","10001","10001","10001","10001","10001","11110"],
'E':["11111","10000","10000","11110","10000","10000","11111"],
'F':["11111","10000","10000","11110","10000","10000","10000"],
'G':["01110","10001","10000","10111","10001","10001","01111"],
'H':["10001","10001","10001","11111","10001","10001","10001"],
'I':["01110","00100","00100","00100","00100","00100","01110"],
'J':["00111","00010","00010","00010","00010","10010","01100"],
'K':["10001","10010","10100","11000","10100","10010","10001"],
'L':["10000","10000","10000","10000","10000","10000","11111"],
'M':["10001","11011","10101","10101","10001","10001","10001"],
'N':["10001","11001","10101","10011","10001","10001","10001"],
'O':["01110","10001","10001","10001","10001","10001","01110"],
'P':["11110","10001","10001","11110","10000","10000","10000"],
'Q':["01110","10001","10001","10001","10101","10010","01101"],
'R':["11110","10001","10001","11110","10100","10010","10001"],
'S':["01111","10000","10000","01110","00001","00001","11110"],
'T':["11111","00100","00100","00100","00100","00100","00100"],
'U':["10001","10001","10001","10001","10001","10001","01110"],
'V':["10001","10001","10001","10001","10001","01010","00100"],
'W':["10001","10001","10001","10101","10101","11011","10001"],
'X':["10001","10001","01010","00100","01010","10001","10001"],
'Y':["10001","10001","01010","00100","00100","00100","00100"],
'Z':["11111","00001","00010","00100","01000","10000","11111"],
}

def draw_glyph2(d, x, y, ch, col, shadow=None):
    """desenha o caractere em 10x14 (5x7 dobrado) com sombra opcional (+1,+1)"""
    rows = F57[ch]
    for pass_col, off in ((shadow, 1), (col, 0)):
        if pass_col is None: continue
        for ry, row in enumerate(rows):
            for rx, c in enumerate(row):
                if c == '1':
                    X, Y = x + rx*2 + off, y + ry*2 + off
                    d.rectangle((X, Y, X+1, Y+1), fill=pass_col)

def draw_arrow(d, cx, cy, col, shadow):      # seta "apagar"
    pts = [(-6,0),(-5,-1),(-5,1),(-4,-2),(-4,2),(-3,-3),(-3,3)]
    for off, c in ((1, shadow), (0, col)):
        for (dx, dy) in pts: d.point((cx+dx+off, cy+dy+off), fill=c)
        d.rectangle((cx-5+off, cy-1+off, cx+5+off, cy+off), fill=c)      # haste
        d.rectangle((cx-4+off, cy-2+off, cx-3+off, cy+2+off), fill=c)
        d.rectangle((cx-3+off, cy-3+off, cx-2+off, cy+3+off), fill=c)

def draw_check(d, cx, cy, col, shadow):      # "ok" (visto)
    for off, c in ((1, shadow), (0, col)):
        for i in range(4): d.rectangle((cx-6+i*2+off, cy+1+i*2+off, cx-5+i*2+off, cy+2+i*2+off), fill=c)
        for i in range(7): d.rectangle((cx-0+i*2-0+off-0, cy+7-i*2-2+off, cx+1+i*2+off, cy+7-i*2-1+off), fill=c) if False else None
        for i in range(6): d.rectangle((cx+2+i*2+off, cy+6-i*2+off-3, cx+3+i*2+off, cy+7-i*2+off-3), fill=c)

def draw_slot_plate(d, x, y):                # placa de uma casa do codigo (16x16) em (x, y)
    rrect(d, (x, y, x+15, y+15), 3, P0(11), P0(2), 1)

def draw_entry_bg(slot_glyph=None):
    """slot_glyph = caractere para desenhar nas 8 casas (usado para gerar os tiles das letras); None = casas vazias"""
    img = Image.new('RGB', (W, H)); px = img.load(); d = ImageDraw.Draw(img)
    gradient(lambda p, c: px.__setitem__(p, c), 0, H, GRAD)
    rnd = random.Random(7)
    for _ in range(40):
        x, y = rnd.randrange(4, W-4), rnd.randrange(2, 36)       # sem estrelas na faixa dos campos (y>=36)
        if 22 <= y < 36 and 40 <= x < 200: continue               # nem atras do texto de instrucao
        if rnd.random() < .35: star4(d, x, y, 2, P1(11))
        else: d.point((x, y), fill=P1(rnd.choice([10, 11, 12])))
    # faixa do titulo
    rrect(d, (12, 2, 227, 21), 5, P0(3), P0(4), 2); rrect(d, (15, 5, 224, 18), 3, None, P0(5), 1)
    mini_gift(d, 20, 3); mini_gift(d, 204, 3)
    # casas do codigo
    for i in range(SLOT_N):
        x = SLOT_X0 + i*SLOT_CELL_W + 4
        draw_slot_plate(d, x, SLOT_Y)
        if slot_glyph: draw_glyph2(d, x+3, SLOT_Y+1, slot_glyph, P0(1))
    # painel do teclado
    rrect(d, (6, 59, 233, 140), 6, P0(12), P0(2), 1); rrect(d, (8, 61, 231, 138), 4, None, P0(3), 1)
    for i in range(len(KEYS)):
        c, r = key_pos(i); x = KEY_X0 + KEY_PX*c; y = KEY_Y0 + KEY_PY*r
        if KEYS[i] == 'DEL': f, hi, lo = 9, 8, 12
        elif KEYS[i] == 'OK': f, hi, lo = 15, 14, 12
        else: f, hi, lo = 6, 7, 3
        d.rectangle((x, y, x+KEY_W-1, y+KEY_H-1), fill=P0(f))
        d.line((x, y, x+KEY_W-1, y), fill=P0(hi)); d.line((x, y, x, y+KEY_H-1), fill=P0(hi))
        d.line((x, y+KEY_H-1, x+KEY_W-1, y+KEY_H-1), fill=P0(lo)); d.line((x+KEY_W-1, y, x+KEY_W-1, y+KEY_H-1), fill=P0(lo))
        if KEYS[i] == 'DEL': draw_arrow(d, x+KEY_W//2, y+KEY_H//2, P0(1), P0(12))
        elif KEYS[i] == 'OK': draw_check(d, x+KEY_W//2-1, y+KEY_H//2-3, P0(1), P0(12))
        else: draw_glyph2(d, x+4, y+1, KEYS[i], P0(1), P0(12))
    for c in (8, 9):   # casas decorativas
        x = KEY_X0 + KEY_PX*c; y = KEY_Y0 + KEY_PY*3
        d.rectangle((x, y, x+KEY_W-1, y+KEY_H-1), fill=P0(3)); mini_gift(d, x+2, y+1)
    # faixa de dicas/mensagens
    rrect(d, (6, 143, 233, 158), 4, P0(12), P0(2), 1)
    return img

def draw_stage_bg():
    img = Image.new('RGB', (W, H)); px = img.load(); d = ImageDraw.Draw(img)
    gradient(lambda p, c: px.__setitem__(p, c), 0, 112, GRAD[:8])
    # feixes de luz (usam passos mais claros da paleta 1, com xadrez)
    for (xl, xr, col) in ((86, 154, P1(8)), (100, 140, P1(9))):
        for y in range(0, 110):
            t = y / 110.0
            a = xl + (86 - xl)*0 + (xl - 40*(1-t)) if False else None
        poly = [(xl-34, 0), (xr+34, 0), (xr, 108), (xl, 108)]
        lay = Image.new('L', (W, H), 0); ImageDraw.Draw(lay).polygon(poly, fill=255); lp = lay.load()
        for y in range(0, 108):
            for x in range(W):
                if lp[x, y] and ((x + y) & 1) == 0 and (y % 4 < 3): px[x, y] = col
    rnd = random.Random(11)
    for _ in range(40):
        x, y = rnd.randrange(3, W-3), rnd.randrange(2, 96)
        if rnd.random() < .3: star4(d, x, y, 2, P1(11))
        else: d.point((x, y), fill=P1(rnd.choice([10, 11, 12])))
    # chao
    d.rectangle((0, 112, W, 121), fill=P0(12)); d.line((0, 112, W, 112), fill=P0(3))
    # pedestal
    d.ellipse((50, 104, 190, 122), fill=P0(5), outline=P0(12))
    d.ellipse((54, 102, 186, 117), fill=P0(4), outline=P0(5))
    d.ellipse((66, 104, 174, 113), fill=P0(13))
    d.ellipse((70, 105, 170, 111), fill=P0(4))
    # caixa de dialogo
    rrect(d, (6, 123, 233, 157), 6, P0(12), P0(4), 2); rrect(d, (9, 126, 230, 154), 4, None, P0(5), 1)
    return img

# ---------------------------------------------------------------- tiles
def flip(t, h, v):
    rows = [t[r*8:(r+1)*8] for r in range(8)]
    if v: rows.reverse()
    if h: rows = [list(reversed(r)) for r in rows]
    return tuple(p for r in rows for p in r)

class TileSet:
    """conjunto de tiles 4bpp; cada tile usa UMA das 2 paletas do menu. add() devolve a entrada do mapa."""
    PALS = (BGPAL_RGB[0:16], BGPAL_RGB[16:32])
    def __init__(self): self.tiles, self.seen = [], {}
    def add(self, px, x0, y0, dedupe=True):
        best = None
        for p in (0, 1):
            err, idx = 0, []
            for y in range(8):
                for x in range(8):
                    c = px[x0+x, y0+y]; i = nearest(c, self.PALS[p]); q = self.PALS[p][i]
                    err += (c[0]-q[0])**2 + (c[1]-q[1])**2 + (c[2]-q[2])**2; idx.append(i)
            if best is None or err < best[0]: best = (err, p, tuple(idx))
        _, p, idx = best
        found = None
        if dedupe:
            for h in (0, 1):
                for v in (0, 1):
                    k2 = (p, flip(idx, h, v))
                    if k2 in self.seen and found is None: found = (self.seen[k2], h, v)
        if found is None:
            self.seen[(p, idx)] = len(self.tiles); self.tiles.append(idx); found = (self.seen[(p, idx)], 0, 0)
        return found[0] | (found[1] << 10) | (found[2] << 11) | (p << 12)

def recon(tiles, entries, cols, rows):
    out = Image.new('RGB', (cols*8, rows*8)); px = out.load()
    for ty in range(rows):
        for tx in range(cols):
            e = entries[ty][tx]; t = flip(tiles[e & 0x3FF], (e >> 10) & 1, (e >> 11) & 1); p = e >> 12
            for y in range(8):
                for x in range(8): px[tx*8+x, ty*8+y] = BGPAL_RGB[p*16 + t[y*8+x]]
    return out

def tiles_to_c(name, tiles):
    words = []
    for t in tiles:
        for r in range(8):
            w = 0
            for x in range(8): w |= (t[r*8+x] & 15) << (4*x)
            words.append(w)
    return words

def tiles_to_c(name, tiles):
    words = []
    for t in tiles:
        for r in range(8):
            w = 0
            for x in range(8): w |= (t[r*8+x] & 15) << (4*x)
            words.append(w)
    return words

def emit_u32(name, words):
    s = f'const u32 {name}[] =\n{{\n'
    for i in range(0, len(words), 8):
        s += '\t' + ', '.join(f'0x{w:08X}' for w in words[i:i+8]) + ',\n'
    return s + '};\n\n'
def emit_u16(name, vals, per=10):
    s = f'const u16 {name}[] =\n{{\n'
    for i in range(0, len(vals), per):
        s += '\t' + ', '.join(f'0x{v:04X}' for v in vals[i:i+per]) + ',\n'
    return s + '};\n\n'

def newP(w, h):
    im = Image.new('P', (w, h), 0); return im, ImageDraw.Draw(im)

def box_images():
    # tampa+laco (64x32) e corpo (64x32). Juntas formam a caixa 64x64 fechada.
    lid, d = newP(64, 32)
    d.rectangle((4, 18, 59, 31), fill=1)                     # contorno
    d.rectangle((5, 19, 58, 30), fill=2); d.rectangle((5, 19, 58, 21), fill=3); d.rectangle((5, 28, 58, 30), fill=4)
    d.rectangle((28, 18, 35, 31), fill=1); d.rectangle((29, 19, 34, 31), fill=5); d.rectangle((29, 19, 30, 31), fill=6); d.rectangle((33, 19, 34, 31), fill=7)
    # laco
    d.ellipse((12, 3, 31, 20), fill=1); d.ellipse((14, 5, 29, 18), fill=5); d.ellipse((17, 8, 26, 15), fill=1); d.ellipse((18, 9, 25, 14), fill=7)
    d.ellipse((32, 3, 51, 20), fill=1); d.ellipse((34, 5, 49, 18), fill=5); d.ellipse((37, 8, 46, 15), fill=1); d.ellipse((38, 9, 45, 14), fill=7)
    d.ellipse((14, 5, 22, 9), fill=6); d.ellipse((34, 5, 42, 9), fill=6)
    d.rectangle((27, 12, 36, 21), fill=1); d.rectangle((28, 13, 35, 20), fill=5); d.rectangle((28, 13, 31, 16), fill=6); d.rectangle((34, 17, 35, 20), fill=7)
    base, d = newP(64, 32)
    d.rectangle((8, 0, 55, 31), fill=1)
    d.rectangle((9, 0, 54, 30), fill=2); d.rectangle((9, 0, 13, 30), fill=3); d.rectangle((50, 0, 54, 30), fill=4)
    d.rectangle((9, 27, 54, 30), fill=4); d.rectangle((9, 0, 54, 2), fill=12)  # sombra sob a tampa
    d.rectangle((28, 0, 35, 31), fill=1); d.rectangle((29, 0, 34, 30), fill=5); d.rectangle((29, 0, 30, 30), fill=6); d.rectangle((33, 0, 34, 30), fill=7)
    return lid, base

def burst_images():
    out = []
    for k in range(2):
        im, d = newP(64, 64); cx = cy = 31.5
        n = 8; off = (math.pi/n) * k
        for j in range(n*2):
            a = off + j*math.pi/n; L = 31 if j % 2 == 0 else 22
            for r in range(6, L):
                w = max(0, (L - r) / L * 3.2)
                for s in range(-int(w), int(w)+1):
                    x = int(cx + math.cos(a)*r - math.sin(a)*s); y = int(cy + math.sin(a)*r + math.cos(a)*s)
                    if 0 <= x < 64 and 0 <= y < 64: im.putpixel((x, y), 9 if r < 16 else (6 if r < 24 else 5))
        d.ellipse((22, 22, 41, 41), fill=9); d.ellipse((26, 26, 37, 37), fill=8)
        out.append(im)
    return out

def sparkle_image():
    im, d = newP(16, 16)
    for i in range(1, 8):
        c = 8 if i < 3 else (9 if i < 5 else 6)
        for p in ((8, 8-i), (8, 7+i), (8-i, 8), (7+i, 8)): pass
    # estrela de 4 pontas
    for i in range(0, 8):
        c = 8 if i < 2 else (9 if i < 4 else (6 if i < 6 else 5))
        w = 1 if i < 5 else 0
        for s in range(-w, w+1):
            for (x, y) in ((8+s, 7-i), (7+s, 8+i), (7-i, 8+s), (8+i, 7+s)):
                if 0 <= x < 16 and 0 <= y < 16: im.putpixel((x, y), c)
    d.rectangle((7, 7, 8, 8), fill=8)
    return im

def cursor_image():
    im, d = newP(32, 32); x0, y0, x1, y1 = 4, 5, 27, 26   # 24x22 em volta da tecla (20x17)
    L = 6
    for (cx, cy, dx, dy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        for i in range(L):
            for t in (0, 1):
                im.putpixel((cx + dx*i, cy + dy*t), 1); im.putpixel((cx + dx*t, cy + dy*i), 1)
        im.putpixel((cx + dx*2, cy + dy*2), 2)
    return im

def caret_image():
    im, d = newP(8, 8)
    d.polygon([(0, 1), (7, 1), (3, 6)], fill=1); d.line((1, 1, 6, 1), fill=2); im.putpixel((3, 5), 3)
    return im

def sprite_words(im):
    w, h = im.size; px = im.load(); words = []
    for ty in range(h//8):
        for tx in range(w//8):
            for r in range(8):
                v = 0
                for x in range(8): v |= (px[tx*8+x, ty*8+r] & 15) << (4*x)
                words.append(v)
    return words

# ---------------------------------------------------------------- main
def main():
    out_src = os.path.join(ROOT, 'projeto', 'src'); out_prev = os.path.join(ROOT, 'previews')
    os.makedirs(out_src, exist_ok=True); os.makedirs(out_prev, exist_ok=True)
    entry = draw_entry_bg(); stage = draw_stage_bg()

    # --- tela de codigo: tiles do fundo + tiles das letras (6 tiles por caractere, 3x2)
    ts1 = TileSet(); px = entry.load()
    map1 = [[ts1.add(px, tx*8, ty*8) for tx in range(30)] for ty in range(20)]
    glyph_base = len(ts1.tiles)
    glyph_map = []                               # [36][6] entradas completas (indice | paleta)
    for ch in GLYPH_CHARS:
        gi = draw_entry_bg(slot_glyph=ch); gp = gi.load()
        ents = []
        for ty in range(2):
            for tx in range(3):
                # recorte da PRIMEIRA casa (todas sao iguais: sem estrelas e degrade periodico)
                ents.append(ts1.add(gp, SLOT_X0 + tx*8, SLOT_Y + ty*8))
        glyph_map.append(ents)
    # entradas das casas vazias (para apagar uma letra) = as do mapa original
    n1 = len(ts1.tiles)
    assert n1 <= 512, f'entrada: {n1} tiles (maximo 512)'
    # --- palco
    ts2 = TileSet(); px2 = stage.load()
    map2 = [[ts2.add(px2, tx*8, ty*8) for tx in range(30)] for ty in range(20)]
    assert len(ts2.tiles) <= 512
    print('tiles: tela de codigo =', n1, '(fundo', glyph_base, '+ letras', n1-glyph_base, ') | palco =', len(ts2.tiles), '(maximo 512 cada)')

    lid, base = box_images(); b0, b1 = burst_images(); sp = sparkle_image(); cur = cursor_image(); car = caret_image()
    c = '// ARQUIVO GERADO por ferramentas/gerar_mystery_gift.py - NAO EDITE A MAO\n'
    c += '#include "defines.h"\n\n'
    c += '// Menu = 2 paletas de 16 cores = 32 cores (paleta 0 = interface/texto, paleta 1 = fundo e brilhos)\n'
    c += emit_u16('gMgPalBg', [to555(h) for h in BGPAL], 8)
    c += emit_u16('gMgPalFx', [to555(h) for h in PALA], 8)
    c += emit_u16('gMgPalCursor', [to555(h) for h in PALB], 8)
    c += emit_u32('gMgEntryTiles', tiles_to_c('', ts1.tiles)); c += f'const u32 gMgEntryTilesSize = {n1*32};\n\n'
    c += emit_u32('gMgStageTiles', tiles_to_c('', ts2.tiles)); c += f'const u32 gMgStageTilesSize = {len(ts2.tiles)*32};\n\n'
    c += emit_u16('gMgEntryMap', [v for row in map1 for v in (row + [0, 0])], 16)
    c += emit_u16('gMgStageMap', [v for row in map2 for v in (row + [0, 0])], 16)
    c += '// Letras/numeros das casas do codigo: 36 caracteres x 6 tiles (3 colunas x 2 linhas), ja com a paleta\n'
    c += emit_u16('gMgSlotGlyphs', [v for g in glyph_map for v in g], 12)
    c += emit_u32('gMgBoxLidTiles', sprite_words(lid)); c += emit_u32('gMgBoxBaseTiles', sprite_words(base))
    c += emit_u32('gMgBurstTiles', sprite_words(b0) + sprite_words(b1))
    c += emit_u32('gMgSparkleTiles', sprite_words(sp)); c += emit_u32('gMgCursorTiles', sprite_words(cur)); c += emit_u32('gMgCaretTiles', sprite_words(car))
    open(os.path.join(out_src, 'mystery_gift_gfx.c'), 'w').write(c)

    # conferencia: reconstroi a tela de codigo a partir dos tiles (o que o GBA vai mostrar) e as casas com letras
    recon(ts1.tiles, map1, 30, 20).save(os.path.join(out_prev, '_conferencia_tela_codigo.png'))
    pal = Image.new('RGB', (16*24, 2*24 + 4)); d = ImageDraw.Draw(pal)
    for i, col in enumerate(BGPAL_RGB): d.rectangle(((i % 16)*24, (i//16)*26, (i % 16)*24 + 22, (i//16)*26 + 22), fill=col)
    pal.save(os.path.join(out_prev, 'paleta_32_cores.png'))

if __name__ == '__main__':
    main()
