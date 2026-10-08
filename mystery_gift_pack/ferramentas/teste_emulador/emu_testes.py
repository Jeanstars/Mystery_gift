#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes no emulador (mGBA sem janela) com a tela do Mystery Gift injetada na ROM base.
  A) cada uma das 36 teclas: o caractere guardado pelo jogo e a letra desenhada na tela batem com o esperado
  B) codigos: todos os codigos da tabela sao aceitos (e na linha certa) e os que nao estao nela sao recusados
Uso:  python3 emu_testes.py A|B
"""
import os, re, subprocess, sys, tempfile, shutil
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, '/home/claude/harness'); sys.path.insert(0, '/home/claude/out/ferramentas')
from drive import *
import importlib.util
spec = importlib.util.spec_from_file_location('gen', '/home/claude/out/ferramentas/gerar_mystery_gift.py'); gen = importlib.util.module_from_spec(spec)
sys.argv_backup = sys.argv; sys.argv = ['x', '/tmp/gen_out']; spec.loader.exec_module(gen); sys.argv = sys.argv_backup
from PIL import Image

H = '/home/claude/harness'
CB2 = cb2_addr()
V8004, V8006, GSV2 = 0x20370C0, 0x20370C4, 0x2021CF0

def sessao(script_lines, nome):
    d = tempfile.mkdtemp(prefix='emu_')
    try:
        open(d + '/s.txt', 'w').write('\n'.join(script_lines).replace('@@', d) + '\n')
        subprocess.run([H + '/run', H + '/test.gba', d + '/s.txt'], cwd=d, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
        res = {}
        for l in open(d + '/res.txt'):
            k, v = l.strip().split('=')
            res[k] = int(v, 16)
        imgs = {}
        for f in os.listdir(d):
            if f.endswith('.ppm'):
                imgs[f[:-4]] = Image.open(d + '/' + f).convert('RGB').copy()
        return res, imgs
    finally:
        shutil.rmtree(d, ignore_errors=True)

def novo_script():
    s = Script(); s.run(700); s.l.append('w32 030030F4 ' + CB2); s.run(60)
    return s

def quantizar(img):
    """o que o GBA mostra: cada tile 8x8 usa a melhor das 2 paletas do menu e cores mais proximas"""
    pals = (gen.BGPAL_RGB[:16], gen.BGPAL_RGB[16:])
    out = Image.new('RGB', img.size); px = img.load(); po = out.load()
    for ty in range(img.size[1] // 8):
        for tx in range(img.size[0] // 8):
            best = None
            for p in (0, 1):
                err = 0; cores = []
                for y in range(8):
                    for x in range(8):
                        c = px[tx * 8 + x, ty * 8 + y]; i = gen.nearest(c, pals[p]); q = pals[p][i]
                        err += sum((a - b) ** 2 for a, b in zip(c, q)); cores.append(q)
                if best is None or err < best[0]: best = (err, cores)
            for k, q in enumerate(best[1]): po[tx * 8 + k % 8, ty * 8 + k // 8] = q
    return out

def parte_A():
    chars = [gen.GLYPH_CHARS[i] for i in range(36)]
    falhas = []
    def um(ch):
        s = novo_script(); s.goto(ch)
        for _ in range(8): s.press('A', 6)
        s.l.append('shot @@/slots.ppm')
        for i in range(10): s.l.append('r8 %08x' % (GSV2 + i))
        res, imgs = sessao(s.l, ch)
        return ch, res, imgs['slots']
    with ThreadPoolExecutor(4) as ex:
        resultados = list(ex.map(um, chars))
    quant = {}; maiores = []
    for ch, res, img in resultados:
        guardado = [res[GSV2 + i] if False else res.get('%08x' % (GSV2 + i)) for i in range(10)]
        esperado = [ord(ch)] * 8 + [0, 0]
        if guardado[:9] != esperado[:9]:
            falhas.append((ch, 'memoria', guardado))
        ref = quantizar(gen.draw_entry_bg(slot_glyph=ch))
        box = (gen.SLOT_X0, gen.SLOT_Y, gen.SLOT_X0 + 8 * 24, gen.SLOT_Y + 16)
        a = img.crop(box); b = ref.crop(box)
        # tolerancia: o emulador converte cor de 5 para 8 bits de um jeito um pouco diferente do gerador (diferenca de poucos niveis)
        pa, pb = a.load(), b.load()
        maior = max(max(abs(x - y) for x, y in zip(pa[i, j], pb[i, j])) for j in range(16) for i in range(192))
        ruins = sum(1 for j in range(16) for i in range(192) if max(abs(x - y) for x, y in zip(pa[i, j], pb[i, j])) > 12)
        maiores.append(maior)
        if ruins:
            falhas.append((ch, 'desenho diferente do esperado: %d pixels' % ruins, maior))
        quant[ch] = a.tobytes()
    unicos = len(set(quant.values()))
    print('A) teclas testadas: %d | letras desenhadas distintas: %d/36 | maior diferenca de cor: %d/255 | falhas: %d' % (len(chars), unicos, max(maiores), len(falhas)))
    for f in falhas[:10]: print('   FALHOU:', f)
    return not falhas and unicos == 36

def parte_B():
    import json
    d = json.load(open('/tmp/stress.json'))
    cods = [c['code'] for c in d['codigos']]
    nao = json.load(open('/tmp/stress_nao.json'))
    falhas = []
    def membro(i):
        code = cods[i]
        s = novo_script(); s.l.append('w16 %08x ffff' % V8004); s.l.append('w16 %08x 0000' % V8006)
        s.type(code)
        for k in range(len(code) + 1): s.l.append('r8 %08x' % (GSV2 + k))
        s.goto('OK'); s.press('A', 6); s.run(30)
        s.l.append('r16 %08x' % V8004); s.l.append('r16 %08x' % V8006)
        return i, sessao(s.l, code)[0]
    def naomembro(code):
        s = novo_script(); s.l.append('w16 %08x ffff' % V8004); s.l.append('w16 %08x 0000' % V8006)
        s.type(code); s.goto('OK'); s.press('A', 6); s.run(30)
        s.l.append('r16 %08x' % V8004); s.l.append('r16 %08x' % V8006)
        return code, sessao(s.l, code)[0]
    with ThreadPoolExecutor(4) as ex:
        rm = list(ex.map(membro, range(len(cods))))
        rn = list(ex.map(naomembro, nao))
    for i, res in rm:
        code = cods[i]
        guardado = [res.get('%08x' % (GSV2 + k)) for k in range(len(code) + 1)]
        if guardado != [ord(c) for c in code] + [0]:
            falhas.append((code, 'digitado errado na memoria', guardado))
        if res['%08x' % V8004] != i:
            falhas.append((code, 'NAO ACEITO ou indice errado', 'Var8004=%X esperado %d' % (res['%08x' % V8004], i)))
    for code, res in rn:
        if res['%08x' % V8004] != 0xFFFF or res['%08x' % V8006] == 0:
            falhas.append((code, 'deveria ser recusado', 'Var8004=%X msg=%d' % (res['%08x' % V8004], res['%08x' % V8006])))
    print('B) codigos da tabela aceitos: %d/%d | nao-membros recusados: %d/%d | falhas: %d' %
          (sum(1 for i, r in rm if r['%08x' % V8004] == i), len(rm), sum(1 for c, r in rn if r['%08x' % V8004] == 0xFFFF), len(rn), len(falhas)))
    for f in falhas[:12]: print('   FALHOU:', f)
    return not falhas

if __name__ == '__main__':
    ok = parte_A() if sys.argv[1] == 'A' else parte_B()
    sys.exit(0 if ok else 1)
