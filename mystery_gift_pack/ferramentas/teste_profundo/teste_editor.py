#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bateria de testes do editor (sem janela). Uso:  python teste_editor.py <pasta raiz do projeto CFRU>
Faz copias temporarias do projeto: nao altera o seu. Precisa de arm-none-eabi-gcc para os testes de compilacao.
"""
import json, os, random, re, shutil, sys, tempfile, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import editor_mystery_gift as e

RAIZ = sys.argv[1]
ok = falha = 0


def check(cond, nome, detalhe=''):
    global ok, falha
    if cond:
        ok += 1
    else:
        falha += 1
        print('  FALHOU:', nome, detalhe)


def secao(t):
    print('\n== ' + t)


def projeto_copia():
    """copia leve do projeto (src + include + routinepointers) para testar a gravacao sem tocar no original"""
    dst = tempfile.mkdtemp(prefix='CFRU resetado ')
    for sub in ('src', 'include'):
        shutil.copytree(os.path.join(RAIZ, sub), os.path.join(dst, sub),
                        ignore=shutil.ignore_patterns('*.o', '*.gba', '__pycache__'))
    return dst


def codigo(code, slot=0, **kw):
    c = e.entrada_nova(slot); c['code'] = code; c['species'] = 'EEVEE'; c.update(kw); return c


def dados(*cods):
    d = e.dados_padrao(); d['codigos'] = list(cods); return d


L = e.carregar_listas(RAIZ)

secao('1) listas lidas do projeto (respeitam #ifdef)')
check(len(L['species']) > 300 and len(L['items']) > 300 and len(L['moves']) > 300, 'listas grandes', {k: len(v) for k, v in L.items()})
check('EEVEE' in L['species'] and 'MASTER_BALL' in L['items'] and 'SURF' in L['moves'], 'nomes basicos presentes')
check(all(re.fullmatch(r'[A-Z0-9_]+', n) for k in L for n in L[k]), 'todos os nomes sao validos em C')
check(all(len(set(L[k])) == len(L[k]) for k in L), 'sem nomes duplicados')
# mini pre-processador
d_ = {}
check(e._avaliar_if('defined(X) || 1', {}) is True, 'if: defined(X) || 1')
check(e._avaliar_if('defined(X) && 1', {}) is False, 'if: defined(X) && 1 (X ausente)')
check(e._avaliar_if('A > 2', {'A': 3}) is True, 'if: A > 2')
check(e._avaliar_if('__import__("os")', {}) is None, 'if: expressao maliciosa e recusada')
tmp = tempfile.mkdtemp()
os.makedirs(os.path.join(tmp, 'src')); os.makedirs(os.path.join(tmp, 'include', 'constants'))
open(os.path.join(tmp, 'src', 'config.h'), 'w').write('#define ATIVO\n//#define COMENTADO\n')
open(os.path.join(tmp, 'include', 'constants', 'items.h'), 'w').write(
    '#define ITEM_A 1\n#ifdef INEXISTENTE\n#define ITEM_B 2\n#else\n#define ITEM_C 3\n#endif\n'
    '#ifdef ATIVO\n#define ITEM_D 4\n#endif\n#ifdef COMENTADO\n#define ITEM_E 5\n#endif\n'
    '#if defined(ATIVO) && !defined(INEXISTENTE)\n#define ITEM_F 6\n#elif 1\n#define ITEM_G 7\n#endif\n'
    '#define ITEM_H ITEM_A\n#define ITEM_I (0x10)\n/* #define ITEM_J 9 */\n#define ITEM_K 11 // comentario\n')
r = e._constantes(tmp, 'items.h', 'ITEM_')
check(r == ['A', 'C', 'D', 'F', 'K', 'I'], 'preprocessador: ifdef/else/elif/alias/comentarios (ordenado por valor)', r)
shutil.rmtree(tmp)

secao('2) validacao dos codigos')
bons = ['A', '0', 'Z', '9', 'AB12CD34', '00000000', 'ZZZZZZZZ', '12345678', 'A1B2C3D4', 'EEVEE001', '1', 'ZZ', 'Q9']
for c in bons:
    check(e.validar(dados(codigo(c)), L) == [], 'aceita %r' % c)
ruins = ['', 'ABCDEFGHI', '123456789', 'abc', 'Abc', 'A B', 'A-B', 'A_B', 'ÇÃO', 'A\n', ' ', 'A.B', 'ＡＢ', '１２３', 'A\u00a0B', '😀']
for c in ruins:
    check(e.validar(dados(codigo(c)), L) != [], 'recusa %r' % c)
check(e.validar(dados(codigo('AB', 0), codigo('AB', 1)), L) != [], 'recusa codigo repetido')
check(e.validar(dados(codigo('AB', 0), codigo('CD', 0)), L) != [], 'recusa slot repetido')
check(e.validar(dados(codigo('AB', 64)), L) != [], 'recusa slot fora da faixa')
check(e.validar(dados(codigo('AB', -1)), L) != [], 'recusa slot negativo')
check(e.validar(dados(codigo('AB', species='')), L) != [], 'recusa sem Pokemon nem item')
check(e.validar(dados(codigo('AB', level=0)), L) != [], 'recusa nivel 0')
check(e.validar(dados(codigo('AB', level=101)), L) != [], 'recusa nivel 101')
check(e.validar(dados(codigo('AB', level=1)), L) == [] and e.validar(dados(codigo('AB', level=100)), L) == [], 'aceita nivel 1 e 100')
check(e.validar(dados(codigo('AB', species='', reward='MASTER_BALL', qty=0)), L) != [], 'recusa quantidade 0')
check(e.validar(dados(codigo('AB', species='', reward='MASTER_BALL', qty=1000)), L) != [], 'recusa quantidade 1000')
check(e.validar(dados(codigo('AB', species='', reward='MASTER_BALL', qty=999)), L) == [], 'aceita quantidade 999')
check(e.validar(dados(codigo('AB', nature='XXX')), L) != [], 'recusa nature invalida')
check(all(e.validar(dados(codigo('AB', nature=n)), L) == [] for n in e.NATURES), 'aceita as 25 natures')
check(e.validar(dados(codigo('AB', species='', reward='MASTER_BALL', moves=['SURF', '', '', ''])), L) != [], 'recusa golpes sem Pokemon')
check(e.validar(dados(codigo('AB', species='NAOEXISTE')), L) != [], 'recusa Pokemon inexistente')
check(e.validar(dados(codigo('AB', held='NAOEXISTE')), L) != [], 'recusa item segurado inexistente')
check(e.validar(dados(codigo('AB', moves=['NAOEXISTE', '', '', ''])), L) != [], 'recusa golpe inexistente')
check(e.validar(dados(codigo('AB', species='', reward='ODDISH_LEAF', qty=1)), L) != [], 'recusa item de bloco #ifdef desativado (ODDISH_LEAF)')
check(len(e.validar(dados(*[codigo('C%d' % i, i) for i in range(65)]), L)) > 0, 'recusa mais de 64 codigos')
check(e.validar(dados(*[codigo('C%d' % i, i) for i in range(64)]), L) == [], 'aceita exatamente 64 codigos')
rnd = random.Random(1)
alfa = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
for _ in range(3000):
    c = ''.join(rnd.choice(alfa) for _ in range(rnd.randint(1, 8)))
    assert e.validar(dados(codigo(c)), L) == [], c
ok += 1
for _ in range(3000):
    n = rnd.randint(1, 8)
    c = ''.join(rnd.choice(alfa) for _ in range(n))
    i = rnd.randrange(n)
    c = c[:i] + rnd.choice('abcdefghijklmnopqrstuvwxyz -_.!@#çãé') + c[i + 1:]
    assert e.validar(dados(codigo(c)), L) != [], repr(c)
ok += 1
print('  fuzz: 3000 codigos validos aceitos, 3000 com um caractere proibido recusados')

secao('3) arquivo gerado (.h)')
d = e.dados_padrao()
h = e.gerar_h(d)
check(all(ord(ch) < 128 for ch in h), 'arquivo 100% ASCII')
check(h.count('.code = "') == len(d['codigos']), 'uma linha por codigo')
back = e.importar_h  # roundtrip via arquivo
tmpf = tempfile.mktemp(suffix='.h'); open(tmpf, 'w').write(h)
d2 = e.importar_h(tmpf); os.remove(tmpf)
check(d2['codigos'] == d['codigos'] and d2['flag_base'] == d['flag_base'] and d2['musica'] == d['musica'], 'ida e volta (gerar -> importar) identica')
d3 = e.dados_padrao(); d3['codigos'][0]['code'] = 'A1B2C3D4'; d3['musica'] = 0
check('MYSTERY_GIFT_MENU_MUSIC 0x0' in e.gerar_h(d3), 'musica 0 = sem musica')
check('MYSTERY_GIFT_FLAG_BASE 0x950' in h, 'flag base no arquivo')
antigo = '/* x */\nstatic const struct MysteryGiftEntry sMysteryGifts[] = {\n{"EEVEE001", SPECIES_EEVEE, 10, FALSE, FALSE, ITEM_NONE, 0xFF},\n{"DRATINI", SPECIES_DRATINI, 15, TRUE, FALSE, ITEM_LEFTOVERS, NATURE_ADAMANT},\n};'
open(tmpf, 'w').write(antigo); d4 = e.importar_h(tmpf); os.remove(tmpf)
check([c['code'] for c in d4['codigos']] == ['EEVEE001', 'DRATINI'] and d4['codigos'][1]['held'] == 'LEFTOVERS' and d4['codigos'][1]['slot'] == 1,
      'importa o formato antigo mantendo as flags (slot = posicao)')

secao('4) gravar no projeto com conferencia do compilador')
gcc = e.achar_gcc()
check(gcc is not None, 'compilador encontrado', 'sem arm-none-eabi-gcc: testes 4 serao pulados')
if gcc:
    P = projeto_copia()
    cod = os.path.join(P, 'src', 'mystery_gift_codes.h'); cfonte = os.path.join(P, 'src', 'mystery_gift.c')
    os.utime(cfonte, (1000000000, 1000000000))
    dest, est = e.escrever_h(e.dados_padrao(), P)
    check(est == 'ok' and os.path.isfile(dest), 'grava e confere: ok')
    check(os.path.getmtime(cfonte) > time.time() - 60, 'mystery_gift.c marcado para recompilar (mtime novo)')
    bom = open(cod, 'rb').read()
    ruim = e.dados_padrao(); ruim['codigos'][0]['species'] = 'NAOEXISTE'
    try:
        e.escrever_h(ruim, P); check(False, 'compilador deveria recusar Pokemon inexistente')
    except RuntimeError as ex:
        check('NADA foi gravado' in str(ex) or 'NOTHING' in str(ex), 'recusa e avisa quando nao compila')
    check(open(cod, 'rb').read() == bom, 'arquivo antigo restaurado byte a byte apos a recusa')
    ruim2 = e.dados_padrao(); ruim2['codigos'][1]['reward'] = 'ODDISH_LEAF'
    try:
        e.escrever_h(ruim2, P); check(False, 'compilador deveria recusar item de bloco desativado')
    except RuntimeError:
        check(True, 'recusa item de bloco #ifdef desativado')
    os.remove(cod)
    try:
        e.escrever_h(ruim, P)
    except RuntimeError:
        pass
    check(not os.path.exists(cod), 'sem arquivo antigo: nao deixa lixo apos a recusa')
    # caminho com espaco, aspas e barra final
    dest, est = e.escrever_h(e.dados_padrao(), '"%s/"' % P)
    check(est == 'ok', 'caminho com espaco + aspas + barra final')
    # sem compilador
    orig = e.achar_gcc; e.achar_gcc = lambda: None
    dest, est = e.escrever_h(e.dados_padrao(), P)
    e.achar_gcc = orig
    check(est == 'sem_gcc' and os.path.isfile(dest), 'sem compilador: grava e avisa (estado sem_gcc)')
    os.remove(cfonte)
    dest, est = e.escrever_h(e.dados_padrao(), P)
    check(est == 'sem_fonte', 'sem mystery_gift.c: avisa (estado sem_fonte)')
    try:
        e.escrever_h(e.dados_padrao(), os.path.join(P, 'nao_existe')); check(False, 'pasta inexistente')
    except RuntimeError:
        check(True, 'pasta inexistente levanta erro claro')
    shutil.rmtree(P)

secao('5) flags')
def flagerr(base):
    dd = e.dados_padrao(); dd['flag_base'] = base
    return e.validar(dd, L, 'pt', RAIZ)
check(flagerr(0x950) == [], '0x950 (padrao) livre')
check(flagerr(0x9C0) == [], '0x9C0 livre (ate 0x9FF)')
conf = flagerr(0x900)
check(conf and 'FLAG_' in conf[0], '0x900 conflita com flags do CFRU', conf)
check(flagerr(0x8FF) != [] and 'não serve' in flagerr(0x8FF)[0], '0x8FF (abaixo de 0x900) recusada')
check(e.validar({**e.dados_padrao(), 'flag_base': 0x18C0}, L) == [], '0x18C0 cabe (termina em 0x18FF) sem checar conflito')
check(e.validar({**e.dados_padrao(), 'flag_base': 0x18C1}, L) != [], '0x18C1 estoura o limite 0x18FF')
check(e.validar({**e.dados_padrao(), 'flag_base': 0}, L) != [], 'flag 0 recusada')
check(e.validar({**e.dados_padrao(), 'flag_base': -5}, L) != [], 'flag negativa recusada')
usadas = e.flags_em_uso(RAIZ)
check(0x900 in usadas and 0x950 not in usadas, 'detecta flags em uso (0x900 sim, 0x950 nao)')

secao('6) codigos.json (robustez)')
t = tempfile.mkdtemp(); j = os.path.join(t, 'codigos.json')
dd, av = e.carregar_json(j); check(av is None and len(dd['codigos']) == 6, 'sem arquivo: usa os exemplos')
open(j, 'w').write('{ isto nao e json'); dd, av = e.carregar_json(j)
check(av and os.path.isfile(av) and len(dd['codigos']) == 6, 'corrompido: guarda copia e recomeca')
open(j, 'w').write('[1,2,3]'); dd, av = e.carregar_json(j); check(av is not None, 'json com formato errado tratado como corrompido')
open(j, 'w').write(json.dumps({'codigos': [{'code': 'abc', 'species': 'MEW', 'slot': 3}]}))
dd, av = e.carregar_json(j)
check(av is None and dd['codigos'][0]['code'] == 'ABC' and dd['codigos'][0]['level'] == 5 and dd['proximo_slot'] >= 4 and dd['idioma'] == 'pt',
      'arquivo antigo/incompleto: completa campos, maiusculas e proximo_slot')
e.salvar_json(dd, j); check(not os.path.exists(j + '.tmp') and e.carregar_json(j)[0]['codigos'][0]['code'] == 'ABC', 'salvar e atomico (sem .tmp sobrando)')
e.salvar_idioma('es', j); check(e.carregar_json(j)[0]['idioma'] == 'es' and e.carregar_json(j)[0]['codigos'][0]['code'] == 'ABC', 'salvar idioma nao perde os codigos')
shutil.rmtree(t)

secao('7) idiomas (pt / en / es)')
check(set(e._IDX) == {'pt', 'en', 'es'} and len(e.IDIOMAS) == 3, 'tres idiomas')
vazios = [k for k, v in e.TR.items() if len(v) != 3 or not all(isinstance(s, str) and s.strip() for s in v)]
check(not vazios, 'toda chave tem 3 traducoes nao vazias', vazios)
def campos(s): return set(re.findall(r'\{(\w+)(?::[^}]*)?\}', s))
incons = [k for k, v in e.TR.items() if not (campos(v[0]) == campos(v[1]) == campos(v[2]))]
check(not incons, 'mesmos {campos} nos 3 idiomas', incons)
fonte = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'editor_mystery_gift.py'), encoding='utf-8').read()
usadas_k = set(re.findall(r"\b(?:L|t)\(\s*'([a-z_0-9A-Z]+)'", fonte)) | set(re.findall(r"\(\s*[a-z_.\[\]']+\s*,\s*'(?:[a-z_]+)'\s*\)", ''))
usadas_k |= set(re.findall(r"R\([^,]+,\s*'([a-z_0-9]+)'", fonte)) | set(re.findall(r"\('(rad_[a-z]+)',", fonte))
faltam = [k for k in usadas_k if k not in e.TR]
check(not faltam, 'toda chave usada no programa existe nas traducoes', faltam)
for lg in ('pt', 'en', 'es'):
    check(e.validar(dados(codigo('')), L, lg) and all(isinstance(m, str) and '{' not in m for m in e.validar(dados(codigo('', species='X')), L, lg)),
          'mensagens de erro formatadas em %s' % lg)
check(e.t('e_codigo', 'en', c='X', t=8) != e.t('e_codigo', 'pt', c='X', t=8) != e.t('e_codigo', 'es', c='X', t=8), 'idiomas realmente diferentes')
check(all(e.nome_musica(m, lg) for m in e.MUSICAS for lg in ('pt', 'en', 'es')), 'nomes de musica nos 3 idiomas')
check(len({e.nome_musica(m, 'pt') for m in e.MUSICAS}) == len(e.MUSICAS), 'nomes de musica distintos (a tela identifica a musica pelo nome)')

print('\nRESULTADO: %d verificacoes OK, %d FALHAS' % (ok, falha))
sys.exit(1 if falha else 0)
