#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Registra o  special 0x122  do Mystery Gift no seu projeto, SEM voce editar nada e SEM substituir o seu arquivo.

  python instalar_special.py  <pasta raiz do projeto CFRU>            instala
  python instalar_special.py  <pasta raiz do projeto CFRU> --remover  desfaz

O que faz: acrescenta UMA linha ("MysteryGift_Start 081601E8") no arquivo  routinepointers  do projeto,
logo depois da linha do special 0x12D. Antes disso faz uma copia de seguranca (routinepointers.bak_mysterygift)
e confere que o slot 0x122 nao esta em uso. Se rodar duas vezes, nao duplica.
"""
import os
import re
import shutil
import sys

NOME = 'MysteryGift_Start'
ENDERECO = '081601E8'          # 0x0815FD60 + 4 * 0x122
ANCORA = 'sp12D_CompareEnteredPhrase'
COMENTARIO = '##^ Mystery Gift: special 0x122'


def main(argv):
    if not argv:
        print(__doc__)
        return 1
    raiz = argv[0]
    arq = os.path.join(raiz, 'routinepointers')
    if not os.path.isfile(arq):
        print('ERRO: nao achei "%s". Passe a pasta raiz do projeto CFRU (a que tem src, include e routinepointers).' % arq)
        return 1
    with open(arq, encoding='utf-8', errors='ignore', newline='') as f:
        texto = f.read()
    nl = '\r\n' if '\r\n' in texto else '\n'
    linhas = texto.split(nl)

    if '--remover' in argv:
        novas = [l for l in linhas if not l.startswith(NOME + ' ') and not l.startswith(COMENTARIO)]
        if len(novas) == len(linhas):
            print('Nada para remover: o Mystery Gift nao estava registrado.')
            return 0
        with open(arq, 'w', encoding='utf-8', newline='') as f:
            f.write(nl.join(novas))
        print('Removido. (O backup routinepointers.bak_mysterygift continua ai, se precisar.)')
        return 0

    if any(l.startswith(NOME + ' ') for l in linhas):
        print('Ja instalado: a linha do Mystery Gift ja esta no routinepointers. Nada a fazer.')
        return 0
    em_uso = [l for l in linhas if re.search(r'(?<![0-9A-Fa-f])0?' + ENDERECO + r'(?![0-9A-Fa-f])', l, re.I)]
    if em_uso:
        print('ERRO: o endereco do special 0x122 ja esta em uso no seu routinepointers:\n  ' + em_uso[0])
        print('Nao mexi em nada. Me avise para escolhermos outro numero de special.')
        return 1
    pos = next((i for i, l in enumerate(linhas) if l.startswith(ANCORA)), None)
    if pos is None:
        print('ERRO: nao achei a linha "%s" no seu routinepointers (arquivo diferente do esperado). Nao mexi em nada.' % ANCORA)
        return 1
    shutil.copyfile(arq, arq + '.bak_mysterygift')
    linhas[pos + 1:pos + 1] = ['%s %s' % (NOME, ENDERECO), '%s (0x0815FD60 + 4*0x122)' % COMENTARIO]
    with open(arq, 'w', encoding='utf-8', newline='') as f:
        f.write(nl.join(linhas))
    print('Pronto! special 0x122 registrado. Backup: routinepointers.bak_mysterygift')
    print('Agora apague a pasta build do projeto e compile de novo.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
