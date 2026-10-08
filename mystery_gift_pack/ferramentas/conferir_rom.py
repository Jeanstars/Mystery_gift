#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Confere, na sua ROM JA COMPILADA (.gba), se cada codigo do editor realmente entrou no jogo.
Os codigos ficam gravados na ROM como texto; se um codigo aparece como FALTA, o build nao incluiu a lista nova
(apague a pasta build e compile de novo) e esse codigo daria "Codigo invalido" no jogo.

  python conferir_rom.py  SUA_ROM.gba  [codigos.json]
/ Checks your already-built ROM: every code of the editor must be inside it.
/ Verifica tu ROM ya compilada: cada código del editor debe estar dentro de ella.
"""
import json, os, sys

def main(argv):
    if not argv:
        print(__doc__); return 1
    rom = open(argv[0], 'rb').read()
    js = argv[1] if len(argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'codigos.json')
    d = json.load(open(js, encoding='utf-8'))
    faltam = []
    for c in d['codigos']:
        code = c['code']
        achou = (code.encode('ascii') + b'\x00') in rom
        print('%-9s flag 0x%X : %s' % (code, d['flag_base'] + c['slot'], 'OK (esta na ROM)' if achou else 'FALTA  <-- daria "Codigo invalido"'))
        if not achou:
            faltam.append(code)
    if faltam:
        print('\nFALTAM %d codigo(s): %s\nApague a pasta build, compile de novo e rode esta conferencia outra vez.' % (len(faltam), ', '.join(faltam)))
        return 1
    print('\nTUDO CERTO: os %d codigos estao dentro da ROM.' % len(d['codigos']))
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
