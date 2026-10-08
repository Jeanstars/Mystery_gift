#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EDITOR DO MYSTERY GIFT / MYSTERY GIFT EDITOR / EDITOR DEL REGALO MISTERIOSO

  1. Dois cliques em ABRIR_EDITOR.bat (ou: python editor_mystery_gift.py)
  2. Escolha o idioma do programa (canto superior direito): Portugues, English ou Espanol (Latinoamerica).
  3. Clique em "Procurar..." e escolha a PASTA RAIZ do projeto CFRU (a que tem src e include).
  4. Crie/edite os codigos e clique em "SALVAR E GERAR".
  5. Compile o projeto de novo (python scripts/make.py).

ARQUIVOS QUE ESTE PROGRAMA MEXE
  ferramentas/codigos.json              seus codigos (criado/atualizado ao salvar; tambem guarda o idioma do programa)
  <projeto>/src/mystery_gift_codes.h    ESCRITO (e so ele) - a lista de codigos que vai para o jogo
  <projeto>/src/mystery_gift.c          so a DATA de modificacao e atualizada ("touch"), para o build recompilar
  <projeto>/include/constants/*.h       so LIDOS (nomes de Pokemon, itens e golpes) - nunca alterados
  <projeto>/src/config.h, include/...   so LIDOS (macros e flags em uso)
Antes de gravar, o programa COMPILA o resultado com o seu compilador (arm-none-eabi-gcc); se nao compilar, nada e gravado.

Sem janela (opcional):
  python editor_mystery_gift.py --gerar [--projeto PASTA] [--idioma pt|en|es]
  python editor_mystery_gift.py --importar ARQUIVO.h
"""
import json
import os
import re
import shutil
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
ARQ_JSON = os.path.join(AQUI, 'codigos.json')

MAX_CODIGOS = 64            # numero maximo de codigos (cada um usa 1 flag, para sempre)
TAM_CODIGO = 8              # tamanho maximo do codigo digitado (casas da tela)
FLAG_PADRAO = 0x950
FLAG_MIN = 0x900            # o CFRU so grava no save as flags de 0x900 a 0x18FF (bloco expandido)
FLAG_MAX = 0x18FF

NATURES = ['HARDY', 'LONELY', 'BRAVE', 'ADAMANT', 'NAUGHTY', 'BOLD', 'DOCILE', 'RELAXED', 'IMPISH', 'LAX', 'TIMID',
           'HASTY', 'SERIOUS', 'JOLLY', 'NAIVE', 'MODEST', 'MILD', 'QUIET', 'BASHFUL', 'RASH', 'CALM', 'GENTLE',
           'SASSY', 'CAREFUL', 'QUIRKY']
ALEATORIA = '(aleatoria)'   # valor interno (guardado no JSON); a tela mostra a traducao

# ------------------------------------------------------------------------------------------------ idiomas
IDIOMAS = [('pt', 'Português (Brasil)'), ('en', 'English'), ('es', 'Español (Latinoamérica)')]
_IDX = {'pt': 0, 'en': 1, 'es': 2}

TR = {
    # janela
    'titulo': ('Editor do Mystery Gift', 'Mystery Gift Editor', 'Editor del Regalo Misterioso'),
    'proj_frame': (' Projeto, música e idioma ', ' Project, music and language ', ' Proyecto, música e idioma '),
    'pasta_proj': ('Pasta do projeto CFRU:', 'CFRU project folder:', 'Carpeta del proyecto CFRU:'),
    'procurar': ('Procurar...', 'Browse...', 'Buscar...'),
    'musica': ('Música do menu:', 'Menu music:', 'Música del menú:'),
    'flag_ini': ('Flag inicial:', 'Starting flag:', 'Flag inicial:'),
    'idioma': ('Idioma:', 'Language:', 'Idioma:'),
    'lista_frame': (' Códigos ', ' Codes ', ' Códigos '),
    'col_codigo': ('Código', 'Code', 'Código'),
    'col_flag': ('Flag', 'Flag', 'Flag'),
    'col_tipo': ('Tipo', 'Type', 'Tipo'),
    'col_poke': ('Pokémon', 'Pokémon', 'Pokémon'),
    'col_item': ('Item', 'Item', 'Objeto'),
    'tipo_poke': ('Pokémon', 'Pokémon', 'Pokémon'),
    'tipo_item': ('Item', 'Item', 'Objeto'),
    'tipo_ambos': ('Poke+Item', 'Poke+Item', 'Poke+Objeto'),
    'form_frame': (' Editar o código selecionado ', ' Edit the selected code ', ' Editar el código seleccionado '),
    'cod_label': ('Código (A-Z e 0-9, até 8):', 'Code (A-Z and 0-9, up to 8):', 'Código (A-Z y 0-9, hasta 8):'),
    'presente_e': ('O presente é:', 'The gift is:', 'El regalo es:'),
    'rad_poke': ('Pokémon', 'Pokémon', 'Pokémon'),
    'rad_item': ('Item', 'Item', 'Objeto'),
    'rad_ambos': ('Pokémon + Item', 'Pokémon + Item', 'Pokémon + Objeto'),
    'g_poke': (' Pokémon ', ' Pokémon ', ' Pokémon '),
    'especie': ('Espécie:', 'Species:', 'Especie:'),
    'nivel': ('Nível:', 'Level:', 'Nivel:'),
    'shiny': ('Shiny', 'Shiny', 'Shiny'),
    'ha': ('Habilidade escondida', 'Hidden ability', 'Habilidad oculta'),
    'segura': ('Segura o item:', 'Holds item:', 'Objeto que lleva:'),
    'nature': ('Nature:', 'Nature:', 'Naturaleza:'),
    'aleatoria': ('(aleatória)', '(random)', '(aleatoria)'),
    'golpes_dica': ('Golpes (deixe vazio para os golpes normais do nível):',
                    'Moves (leave empty for the normal moves of the level):',
                    'Movimientos (déjalos vacíos para los movimientos normales del nivel):'),
    'golpe_n': ('Golpe {n}:', 'Move {n}:', 'Movimiento {n}:'),
    'g_item': (' Item de presente (vai para a mochila) ', ' Gift item (goes to the bag) ', ' Objeto de regalo (va a la mochila) '),
    'item_lbl': ('Item:', 'Item:', 'Objeto:'),
    'qtd': ('Quantidade:', 'Quantity:', 'Cantidad:'),
    'novo': ('Novo', 'New', 'Nuevo'),
    'duplicar': ('Duplicar', 'Duplicate', 'Duplicar'),
    'excluir': ('Excluir', 'Delete', 'Eliminar'),
    'aplicar': ('Aplicar alterações', 'Apply changes', 'Aplicar cambios'),
    'importar': ('Importar .h antigo...', 'Import old .h...', 'Importar .h antiguo...'),
    'salvar': ('SALVAR E GERAR  (escreve src/mystery_gift_codes.h)',
               'SAVE AND GENERATE  (writes src/mystery_gift_codes.h)',
               'GUARDAR Y GENERAR  (escribe src/mystery_gift_codes.h)'),
    'dica': ('Dica: a flag de cada código é fixa, então pode excluir/reordenar sem liberar códigos já resgatados.',
             'Tip: each code keeps a fixed flag, so you can delete/reorder without freeing codes already redeemed.',
             'Consejo: cada código tiene una flag fija, así que puedes eliminar/reordenar sin liberar códigos ya canjeados.'),
    'flag_deste': ('Flag deste código: {f}   (para testar de novo: clearflag {f})',
                   "This code's flag: {f}   (to test again: clearflag {f})",
                   'Flag de este código: {f}   (para probar de nuevo: clearflag {f})'),
    # musicas
    'mus_0x111': ('Celadon Game Corner (animada, de prêmios)', 'Celadon Game Corner (lively, prize corner)', 'Celadon Game Corner (animada, de premios)'),
    'mus_0x135': ('Sala de prêmios / Celadon City', 'Prize room / Celadon City', 'Sala de premios / Celadon City'),
    'mus_0x12F': ('Centro Pokémon (calma)', 'Pokémon Center (calm)', 'Centro Pokémon (tranquila)'),
    'mus_0x12D': ('Laboratório do Prof. Oak', "Prof. Oak's Lab", 'Laboratorio del Prof. Oak'),
    'mus_0x12C': ('Pallet Town', 'Pallet Town', 'Pallet Town'),
    'mus_0x134': ('Cerulean City / Fuchsia City', 'Cerulean City / Fuchsia City', 'Cerulean City / Fuchsia City'),
    'mus_0x139': ('Vermilion City', 'Vermilion City', 'Vermilion City'),
    'mus_0x13A': ('Viridian / Pewter / Saffron City', 'Viridian / Pewter / Saffron City', 'Viridian / Pewter / Saffron City'),
    'mus_0x133': ('Silph Co.', 'Silph Co.', 'Silph Co.'),
    'mus_0x14F': ('Ilhas Sevii (1, 2 e 3)', 'Sevii Islands (1, 2 and 3)', 'Islas Sevii (1, 2 y 3)'),
    'mus_0x151': ('Ilhas Sevii (7 e 6)', 'Sevii Islands (7 and 6)', 'Islas Sevii (7 y 6)'),
    'mus_0x127': ('Indigo Plateau', 'Indigo Plateau', 'Meseta Añil'),
    'mus_0': ('Nenhuma (manter a música do mapa)', 'None (keep the map music)', 'Ninguna (mantener la música del mapa)'),
    'mus_outra': ('Outra (0x{id:X})', 'Other (0x{id:X})', 'Otra (0x{id:X})'),
    # avisos de status
    'st_sem_proj': ('Escolha a pasta do projeto CFRU (botão Procurar...) para o editor conferir os nomes e poder gerar o arquivo.',
                    'Choose the CFRU project folder (Browse... button) so the editor can check the names and generate the file.',
                    'Elige la carpeta del proyecto CFRU (botón Buscar...) para que el editor verifique los nombres y genere el archivo.'),
    'st_sem_const': ('Não achei include/constants/species.h dentro dessa pasta. Escolha a pasta raiz do projeto CFRU.',
                     'Could not find include/constants/species.h inside that folder. Choose the CFRU project root folder.',
                     'No encontré include/constants/species.h dentro de esa carpeta. Elige la carpeta raíz del proyecto CFRU.'),
    'st_proj_lido': ('Projeto lido: {a} Pokémon, {b} itens, {c} golpes.', 'Project read: {a} Pokémon, {b} items, {c} moves.',
                     'Proyecto leído: {a} Pokémon, {b} objetos, {c} movimientos.'),
    'st_novo': ('Novo código criado. Preencha e clique em "Aplicar".', 'New code created. Fill it in and click "Apply".',
                'Nuevo código creado. Complétalo y haz clic en "Aplicar".'),
    'st_copia': ('Cópia criada: escolha um código novo para ela.', 'Copy created: choose a new code for it.',
                 'Copia creada: elige un código nuevo para ella.'),
    'st_excluido': ('Código excluído.', 'Code deleted.', 'Código eliminado.'),
    'st_aplicado': ('Alterações aplicadas ao código {c}. Clique em "SALVAR E GERAR" quando terminar.',
                    'Changes applied to code {c}. Click "SAVE AND GENERATE" when you are done.',
                    'Cambios aplicados al código {c}. Haz clic en "GUARDAR Y GENERAR" cuando termines.'),
    'st_gerado': ('Pronto! Gerado: {d}  -> agora é só compilar de novo. {v}', 'Done! Generated: {d}  -> now just compile again. {v}',
                  '¡Listo! Generado: {d}  -> ahora solo compila de nuevo. {v}'),
    'st_importados': ('Importados {n} códigos.', 'Imported {n} codes.', 'Se importaron {n} códigos.'),
    # caixas de dialogo
    'dlg_limite': ('Todos os {n} números de flag já foram usados (cada código usa o seu para sempre, mesmo se excluído, '
                   'para nunca liberar quem já resgatou). Não dá para criar mais códigos.',
                   'All {n} flag numbers have been used (each code keeps its own forever, even if deleted, so nobody who already '
                   'redeemed is ever freed). No more codes can be created.',
                   'Ya se usaron los {n} números de flag (cada código conserva el suyo para siempre, incluso si se elimina, '
                   'para no liberar nunca a quien ya canjeó). No se pueden crear más códigos.'),
    'dlg_excluir_t': ('Excluir', 'Delete', 'Eliminar'),
    'dlg_excluir': ('Excluir o código {c}?\n\nA flag dele (slot {s}) fica reservada e NÃO será reutilizada, para não liberar de novo quem já resgatou.',
                    'Delete code {c}?\n\nIts flag (slot {s}) stays reserved and will NOT be reused, so nobody who already redeemed it is freed.',
                    '¿Eliminar el código {c}?\n\nSu flag (slot {s}) queda reservada y NO se reutilizará, para no liberar de nuevo a quien ya canjeó.'),
    'dlg_vazio': ('(vazio)', '(empty)', '(vacío)'),
    'dlg_erro': ('Erro', 'Error', 'Error'),
    'dlg_corrija': ('Corrija o código selecionado antes de salvar (veja a mensagem em vermelho).',
                    'Fix the selected code before saving (see the red message).',
                    'Corrige el código seleccionado antes de guardar (mira el mensaje en rojo).'),
    'dlg_flag_num': ('A flag inicial deve ser um número, por exemplo 0x950.', 'The starting flag must be a number, for example 0x950.',
                     'La flag inicial debe ser un número, por ejemplo 0x950.'),
    'dlg_nao_gerar': ('Não foi possível gerar', 'Could not generate', 'No se pudo generar'),
    'dlg_salvei_json': ('Salvei o codigos.json, mas falta escolher a pasta do projeto CFRU para escrever o mystery_gift_codes.h.',
                        'I saved codigos.json, but you still need to choose the CFRU project folder to write mystery_gift_codes.h.',
                        'Guardé codigos.json, pero falta elegir la carpeta del proyecto CFRU para escribir mystery_gift_codes.h.'),
    'dlg_escolha_proj': ('Escolha o projeto', 'Choose the project', 'Elige el proyecto'),
    'dlg_erro_escrever': ('Erro ao escrever', 'Error while writing', 'Error al escribir'),
    'dlg_pronto_t': ('Pronto', 'Done', 'Listo'),
    'dlg_pronto': ('Arquivo gerado:\n{d}\n\n{v}\n\nAgora é só compilar de novo (python scripts/make.py).\n'
                   'Se um código novo ainda aparecer como inválido, apague a pasta "build" e compile outra vez.',
                   'File generated:\n{d}\n\n{v}\n\nNow just compile again (python scripts/make.py).\n'
                   'If a new code still shows as invalid, delete the "build" folder and compile again.',
                   'Archivo generado:\n{d}\n\n{v}\n\nAhora solo compila de nuevo (python scripts/make.py).\n'
                   'Si un código nuevo todavía aparece como inválido, borra la carpeta "build" y compila otra vez.'),
    'dlg_pasta_titulo': ('Escolha a pasta raiz do projeto CFRU (a que tem src e include)',
                         'Choose the CFRU project root folder (the one with src and include)',
                         'Elige la carpeta raíz del proyecto CFRU (la que tiene src e include)'),
    'dlg_imp_titulo': ('Escolha um mystery_gift_codes.h', 'Choose a mystery_gift_codes.h', 'Elige un mystery_gift_codes.h'),
    'dlg_imp_erro': ('Não consegui ler: {e}', 'Could not read it: {e}', 'No pude leerlo: {e}'),
    'dlg_imp_vazio': ('Não encontrei nenhum código nesse arquivo.', 'I did not find any code in that file.',
                      'No encontré ningún código en ese archivo.'),
    'dlg_json_corrompido': ('O codigos.json estava corrompido. Guardei uma cópia em "{b}" e comecei com os exemplos.',
                            'codigos.json was corrupted. I kept a copy at "{b}" and started with the examples.',
                            'codigos.json estaba dañado. Guardé una copia en "{b}" y empecé con los ejemplos.'),
    # verificacao com o compilador
    'ver_ok': ('Conferido com o compilador: OK.', 'Checked with the compiler: OK.', 'Verificado con el compilador: OK.'),
    'ver_sem_gcc': ('ATENÇÃO: não achei o compilador (arm-none-eabi-gcc); não consegui conferir se o arquivo compila.',
                    'WARNING: I could not find the compiler (arm-none-eabi-gcc); I could not check that the file compiles.',
                    'ATENCIÓN: no encontré el compilador (arm-none-eabi-gcc); no pude verificar que el archivo compile.'),
    'ver_sem_fonte': ('ATENÇÃO: não achei src/mystery_gift.c no projeto (copiou a pasta "projeto" do pacote?); não consegui conferir.',
                      'WARNING: src/mystery_gift.c was not found in the project (did you copy the package "projeto" folder?); not checked.',
                      'ATENCIÓN: no encontré src/mystery_gift.c en el proyecto (¿copiaste la carpeta "projeto" del paquete?); no se verificó.'),
    'ver_falhou': ('O compilador recusou o resultado. NADA foi gravado.\n{e}',
                   'The compiler rejected the result. NOTHING was written.\n{e}',
                   'El compilador rechazó el resultado. NO se escribió NADA.\n{e}'),
    # erros de validacao
    'e_nenhum': ('Não há nenhum código.', 'There are no codes.', 'No hay ningún código.'),
    'e_max': ('Máximo de {m} códigos (tem {n}).', 'Maximum of {m} codes (you have {n}).', 'Máximo de {m} códigos (tienes {n}).'),
    'e_codigo': ('{c}: o código deve ter de 1 a {t} caracteres, só letras A-Z e números 0-9.',
                 '{c}: the code must have 1 to {t} characters, only letters A-Z and numbers 0-9.',
                 '{c}: el código debe tener de 1 a {t} caracteres, solo letras A-Z y números 0-9.'),
    'e_repetido': ('{c}: código repetido.', '{c}: duplicated code.', '{c}: código repetido.'),
    'e_slot_rep': ('{c}: número de flag (slot {s}) repetido.', '{c}: duplicated flag number (slot {s}).', '{c}: número de flag (slot {s}) repetido.'),
    'e_slot_fora': ('{c}: slot fora de 0..{m}.', '{c}: slot out of range 0..{m}.', '{c}: slot fuera de 0..{m}.'),
    'e_sem_presente': ('{c}: escolha um Pokémon e/ou um item de presente.', '{c}: choose a Pokémon and/or a gift item.',
                       '{c}: elige un Pokémon y/o un objeto de regalo.'),
    'e_nivel': ('{c}: o nível deve ser de 1 a 100.', '{c}: the level must be from 1 to 100.', '{c}: el nivel debe ser de 1 a 100.'),
    'e_qtd': ('{c}: a quantidade do item deve ser de 1 a 999.', '{c}: the item quantity must be from 1 to 999.',
              '{c}: la cantidad del objeto debe ser de 1 a 999.'),
    'e_nature': ('{c}: nature inválida.', '{c}: invalid nature.', '{c}: naturaleza inválida.'),
    'e_nao_existe': ('{c}: {r} "{v}" não existe no projeto (ou fica num bloco desativado do código).',
                     '{c}: {r} "{v}" does not exist in the project (or sits in a disabled block of the code).',
                     '{c}: {r} "{v}" no existe en el proyecto (o está en un bloque desactivado del código).'),
    'r_poke': ('Pokémon', 'Pokémon', 'Pokémon'),
    'r_held': ('item segurado', 'held item', 'objeto que lleva'),
    'r_reward': ('item de presente', 'gift item', 'objeto de regalo'),
    'r_move': ('golpe', 'move', 'movimiento'),
    'e_golpes_sem_poke': ('{c}: golpes só valem quando há um Pokémon.', '{c}: moves only apply when there is a Pokémon.',
                          '{c}: los movimientos solo valen cuando hay un Pokémon.'),
    'e_flag_faixa': ('A flag inicial 0x{b:X} não serve: o CFRU só grava no save as flags 0x{lo:X} a 0x{hi:X}, e o bloco usa 0x{b:X} a 0x{fim:X}.',
                     'Starting flag 0x{b:X} is not valid: CFRU only saves flags 0x{lo:X} to 0x{hi:X}, and the block uses 0x{b:X} to 0x{fim:X}.',
                     'La flag inicial 0x{b:X} no sirve: CFRU solo guarda las flags 0x{lo:X} a 0x{hi:X}, y el bloque usa 0x{b:X} a 0x{fim:X}.'),
    'e_flag_conflito': ('CONFLITO DE FLAG: o bloco 0x{b:X}-0x{fim:X} inclui flags que o projeto já usa ({l}). Escolha outra flag inicial (ex.: 0x{s:X}).',
                        'FLAG CONFLICT: block 0x{b:X}-0x{fim:X} includes flags the project already uses ({l}). Choose another starting flag (e.g. 0x{s:X}).',
                        'CONFLICTO DE FLAG: el bloque 0x{b:X}-0x{fim:X} incluye flags que el proyecto ya usa ({l}). Elige otra flag inicial (ej.: 0x{s:X}).'),
}


def t(chave, lang='pt', **kw):
    txt = TR[chave][_IDX.get(lang, 0)]
    return txt.format(**kw) if kw else txt


# ------------------------------------------------------------------------------------------------ musicas (ids lidos dos mapas da ROM)
MUSICAS = [0x111, 0x135, 0x12F, 0x12D, 0x12C, 0x134, 0x139, 0x13A, 0x133, 0x14F, 0x151, 0x127, 0]


def nome_musica(mid, lang):
    chave = 'mus_0' if mid == 0 else 'mus_0x%X' % mid
    return t(chave, lang) if chave in TR else t('mus_outra', lang, id=mid)


# ------------------------------------------------------------------------------------------------ mini pre-processador (so para ler constantes)
def _avaliar_if(expr, defs):
    """avalia '#if EXPR'. Devolve True/False, ou None se nao der para saber."""
    expr = re.sub(r'/\*.*?\*/', '', expr)
    expr = re.sub(r'//.*', '', expr).strip()
    expr = re.sub(r'defined\s*\(\s*(\w+)\s*\)', lambda m: '1' if m.group(1) in defs else '0', expr)
    expr = re.sub(r'defined\s+(\w+)', lambda m: '1' if m.group(1) in defs else '0', expr)

    def ident(m):
        v = defs.get(m.group(0))
        return str(v) if isinstance(v, int) and not isinstance(v, bool) else '0'
    expr = re.sub(r'\b[A-Za-z_]\w*\b', ident, expr)
    expr = expr.replace('&&', ' and ').replace('||', ' or ')
    expr = re.sub(r'!(?!=)', ' not ', expr)
    toks = re.findall(r'0[xX][0-9a-fA-F]+|\d+|and|or|not|==|!=|<=|>=|<|>|\(|\)|\+|-|\*|%', expr)
    if re.sub(r'\s+', '', ''.join(toks)) != re.sub(r'\s+', '', expr):
        return None
    try:
        return bool(eval(' '.join(toks), {'__builtins__': {}}, {}))
    except Exception:
        return None


def _varrer(arq, defs, prefixo=None):
    """le um .h respeitando #if/#ifdef/#ifndef/#else/#elif/#endif. Atualiza 'defs'. Devolve {nome: valor} das constantes ativas."""
    achados = {}
    if not os.path.isfile(arq):
        return achados
    with open(arq, encoding='utf-8', errors='ignore') as f:
        texto = f.read()
    texto = re.sub(r'/\*.*?\*/', lambda m: '\n' * m.group(0).count('\n'), texto, flags=re.S)
    linhas, acum = [], ''
    for l in texto.split('\n'):
        if l.rstrip().endswith('\\'):
            acum += l.rstrip()[:-1] + ' '
            continue
        linhas.append(acum + l)
        acum = ''
    pilha = []   # (pai_ativo, ativo_agora, algum_ramo_ja_ativo)
    ativo = True
    for l in linhas:
        m = re.match(r'\s*#\s*(\w+)\s*(.*)$', l)
        if not m:
            continue
        d, resto = m.group(1), re.sub(r'//.*', '', m.group(2)).strip()
        if d in ('ifdef', 'ifndef', 'if'):
            if d == 'if':
                v = _avaliar_if(resto, defs)
                v = True if v is None else v      # incerto: conta como ativo (o compilador confere no fim)
            else:
                nome = resto.split()[0] if resto.split() else ''
                v = (nome in defs) if d == 'ifdef' else (nome not in defs)
            pilha.append((ativo, v, v))
            ativo = ativo and v
        elif d == 'elif' and pilha:
            pai, _, ja = pilha.pop()
            v = False if ja else (_avaliar_if(resto, defs) in (True, None))
            pilha.append((pai, v, ja or v))
            ativo = pai and v
        elif d == 'else' and pilha:
            pai, _, ja = pilha.pop()
            pilha.append((pai, not ja, True))
            ativo = pai and not ja
        elif d == 'endif' and pilha:
            pai, _, _ = pilha.pop()
            ativo = pai
        elif ativo and d == 'define':
            mm = re.match(r'(\w+)(?:\s+(.*))?$', resto)
            if not mm:
                continue
            nome, val = mm.group(1), (mm.group(2) or '').strip()
            if re.fullmatch(r'\(?\s*(0[xX][0-9a-fA-F]+|\d+)\s*\)?', val):
                num = int(re.sub(r'[()\s]', '', val), 0)
                defs[nome] = num
                if prefixo and nome.startswith(prefixo):
                    achados[nome] = num
            else:
                defs[nome] = True if val == '' else val
                achados.pop(nome, None)         # virou alias: nao e uma constante numerica
        elif ativo and d == 'undef':
            nome = resto.split()[0] if resto.split() else ''
            defs.pop(nome, None)
            achados.pop(nome, None)
    return achados


def _constantes(raiz, arq, prefixo, excluir=()):
    base = {}
    _varrer(os.path.join(raiz, 'src', 'config.h'), base)          # macros do projeto (ex.: UNBOUND nao definido)
    achados = _varrer(os.path.join(raiz, 'include', 'constants', arq), dict(base), prefixo)
    out = []
    for nome, val in sorted(achados.items(), key=lambda kv: (kv[1], kv[0])):
        curto = nome[len(prefixo):]
        if any(x in nome for x in excluir):
            continue
        if curto in ('NONE', 'COUNT', 'EGG') or curto.endswith('_COUNT') or curto.startswith('NUM_'):
            continue
        if not re.fullmatch(r'[A-Z0-9_]+', curto):
            continue
        out.append(curto)
    return out


def limpar_caminho(p):
    return (p or '').strip().strip('"').strip("'").strip()


def carregar_listas(raiz):
    raiz = limpar_caminho(raiz)
    return {
        'species': _constantes(raiz, 'species.h', 'SPECIES_'),
        'items': _constantes(raiz, 'items.h', 'ITEM_', ('ITEM_EFFECT_', 'FREE_SPACE', 'SHINY_SPACE', 'ITEM_TM_CASE_')),
        'moves': _constantes(raiz, 'moves.h', 'MOVE_', ('MOVE_EFFECT_',)),
    }


def flags_em_uso(raiz):
    """{valor: 'FLAG_X'} das flags 0x900-0x18FF definidas pelo projeto (qualquer #define FLAG_ numerico)"""
    raiz = limpar_caminho(raiz)
    usadas = {}
    for p in (os.path.join(raiz, 'include'), os.path.join(raiz, 'src')):
        for dp, _, fs in os.walk(p):
            for fn in fs:
                if not fn.endswith('.h') or 'mystery_gift' in fn:
                    continue
                try:
                    txt = open(os.path.join(dp, fn), encoding='utf-8', errors='ignore').read()
                except OSError:
                    continue
                for m in re.finditer(r'#\s*define\s+(FLAG_\w+)\s+\(?\s*(0[xX][0-9a-fA-F]+|\d+)\s*\)?', txt):
                    v = int(m.group(2), 0)
                    if FLAG_MIN <= v <= FLAG_MAX:
                        usadas.setdefault(v, m.group(1))
    return usadas


# ------------------------------------------------------------------------------------------------ dados
def entrada_nova(slot):
    return {'code': '', 'species': '', 'level': 5, 'shiny': False, 'ha': False, 'held': '', 'nature': ALEATORIA,
            'moves': ['', '', '', ''], 'reward': '', 'qty': 1, 'slot': slot}


def dados_padrao():
    def e(code, slot, **kw):
        x = entrada_nova(slot); x['code'] = code; x.update(kw); return x
    return {
        'projeto': '', 'flag_base': FLAG_PADRAO, 'musica': 0x111, 'proximo_slot': 6, 'idioma': 'pt',
        'codigos': [
            e('EEVEE001', 0, species='EEVEE', level=10),
            e('DRATINI', 1, species='DRATINI', level=15, shiny=True),
            e('MEWGIFT', 2, species='MEW', level=30),
            e('GOLPES01', 3, species='PIKACHU', level=25, held='LIGHT_BALL',
              moves=['THUNDERBOLT', 'QUICKATTACK', 'IRONTAIL', 'SURF']),
            e('ITEM0001', 4, reward='MASTER_BALL', qty=5),
            e('COMBO001', 5, species='CHARMANDER', level=15, nature='ADAMANT',
              moves=['EMBER', 'SCRATCH', 'SLASH', ''], reward='RARE_CANDY', qty=10),
        ],
    }


def _completar(d):
    base = dados_padrao()
    for k in ('projeto', 'flag_base', 'musica', 'proximo_slot', 'idioma'):
        d.setdefault(k, base[k])
    d.setdefault('codigos', [])
    for c in d['codigos']:
        for k, v in entrada_nova(0).items():
            c.setdefault(k, v)
        c['code'] = str(c['code']).strip().upper()
        c['moves'] = (list(c['moves']) + ['', '', '', ''])[:4]
    usados = [c['slot'] for c in d['codigos']]
    if usados:
        d['proximo_slot'] = max(d['proximo_slot'], max(usados) + 1)
    return d


def carregar_json(caminho=None):
    """le o codigos.json. Se estiver corrompido: guarda uma copia e recomeca com os exemplos. Devolve (dados, aviso|None)."""
    caminho = caminho or ARQ_JSON
    if not os.path.isfile(caminho):
        return dados_padrao(), None
    try:
        with open(caminho, encoding='utf-8') as f:
            d = json.load(f)
        if not isinstance(d, dict):
            raise ValueError('formato inesperado')
        return _completar(d), None
    except Exception:
        bkp = caminho + '.corrompido'
        n = 1
        while os.path.exists(bkp):
            n += 1
            bkp = '%s.corrompido%d' % (caminho, n)
        try:
            shutil.copyfile(caminho, bkp)
        except OSError:
            pass
        return dados_padrao(), bkp


def salvar_json(d, caminho=None):
    caminho = caminho or ARQ_JSON
    tmp = caminho + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    os.replace(tmp, caminho)          # troca atomica: nunca fica um arquivo pela metade


def salvar_idioma(lang, caminho=None):
    caminho = caminho or ARQ_JSON
    d, _ = carregar_json(caminho)
    d['idioma'] = lang
    salvar_json(d, caminho)


# ------------------------------------------------------------------------------------------------ validacao
def validar(d, listas=None, lang='pt', raiz=None):
    """devolve lista de mensagens de erro (vazia = tudo certo)"""
    erros = []
    cods = d['codigos']
    if 'flag_base' in d:
        b = d['flag_base']
        fim = b + MAX_CODIGOS - 1
        if not (FLAG_MIN <= b and fim <= FLAG_MAX):
            erros.append(t('e_flag_faixa', lang, b=b, lo=FLAG_MIN, hi=FLAG_MAX, fim=fim))
        elif raiz:
            usadas = flags_em_uso(raiz)
            conf = sorted(v for v in usadas if b <= v <= fim)
            if conf:
                sugestao = next((x for x in range(FLAG_MIN, FLAG_MAX - MAX_CODIGOS, 16)
                                 if not any(x <= v < x + MAX_CODIGOS for v in usadas)), FLAG_MIN)
                lista = ', '.join('%s=0x%X' % (usadas[v], v) for v in conf[:4]) + (' ...' if len(conf) > 4 else '')
                erros.append(t('e_flag_conflito', lang, b=b, fim=fim, l=lista, s=sugestao))
        if not cods:
            erros.append(t('e_nenhum', lang))
    if len(cods) > MAX_CODIGOS:
        erros.append(t('e_max', lang, m=MAX_CODIGOS, n=len(cods)))
    vistos, slots = {}, {}
    for i, c in enumerate(cods, 1):
        nome = c['code'] or '(%d)' % i
        if not re.fullmatch(r'[A-Z0-9]{1,%d}' % TAM_CODIGO, c['code']):
            erros.append(t('e_codigo', lang, c=nome, t=TAM_CODIGO))
        if c['code'] in vistos:
            erros.append(t('e_repetido', lang, c=nome))
        vistos[c['code']] = True
        if c['slot'] in slots:
            erros.append(t('e_slot_rep', lang, c=nome, s=c['slot']))
        slots[c['slot']] = True
        if not (0 <= c['slot'] < MAX_CODIGOS):
            erros.append(t('e_slot_fora', lang, c=nome, m=MAX_CODIGOS - 1))
        if not c['species'] and not c['reward']:
            erros.append(t('e_sem_presente', lang, c=nome))
        if c['species'] and not (1 <= int(c['level']) <= 100):
            erros.append(t('e_nivel', lang, c=nome))
        if c['reward'] and not (1 <= int(c['qty']) <= 999):
            erros.append(t('e_qtd', lang, c=nome))
        if c['nature'] != ALEATORIA and c['nature'] not in NATURES:
            erros.append(t('e_nature', lang, c=nome))
        if listas:
            def existe(chave, valor, rotulo):
                if valor and listas[chave] and valor not in listas[chave]:
                    erros.append(t('e_nao_existe', lang, c=nome, r=t(rotulo, lang), v=valor))
            existe('species', c['species'], 'r_poke')
            existe('items', c['held'], 'r_held')
            existe('items', c['reward'], 'r_reward')
            for m in c['moves']:
                existe('moves', m, 'r_move')
        if not c['species'] and any(c['moves']):
            erros.append(t('e_golpes_sem_poke', lang, c=nome))
    return erros


# ------------------------------------------------------------------------------------------------ gerar o .h (somente ASCII)
def gerar_h(d):
    L = []
    L.append('/*')
    L.append(' * ARQUIVO GERADO pelo editor_mystery_gift.py  -  NAO EDITE A MAO (use o editor).')
    L.append(' * Os codigos ficam em codigos.json ao lado do editor.')
    L.append(' */')
    L.append('')
    L.append('//Primeira flag usada. O codigo de numero N usa a flag MYSTERY_GIFT_FLAG_BASE + N.')
    L.append('//As flags 0x%X a 0x%X ficam reservadas para o Mystery Gift.' % (d['flag_base'], d['flag_base'] + MAX_CODIGOS - 1))
    L.append('#define MYSTERY_GIFT_FLAG_BASE 0x%X' % d['flag_base'])
    L.append('#define MYSTERY_GIFT_MAX_CODES %d' % MAX_CODIGOS)
    L.append('')
    L.append('//Musica da tela (0 = nao troca a musica do mapa)')
    L.append('#define MYSTERY_GIFT_MENU_MUSIC 0x%X' % d['musica'])
    L.append('')
    L.append('//Flags de idioma do seu projeto (as mesmas do pacote Stars)')
    L.append('#define MG_FLAG_LANG_EN 0x261')
    L.append('#define MG_FLAG_LANG_ES 0x262')
    L.append('')
    L.append('struct MysteryGiftEntry')
    L.append('{')
    L.append('\tconst char* code;')
    L.append('\tu8 slot;\t\t\t//Numero da flag deste codigo (nunca muda)')
    L.append('\tu16 species;\t\t//SPECIES_NONE = presente so de item')
    L.append('\tu8 level;')
    L.append('\tu8 shiny;')
    L.append('\tu8 hiddenAbility;')
    L.append('\tu8 nature;\t\t\t//0xFF = aleatoria')
    L.append('\tu16 heldItem;\t\t//Item que o Pokemon segura')
    L.append('\tu16 moves[4];\t\t//Todos MOVE_NONE = golpes normais do nivel')
    L.append('\tu16 rewardItem;\t\t//Item entregue na mochila (ITEM_NONE = nenhum)')
    L.append('\tu16 rewardQty;')
    L.append('};')
    L.append('')
    L.append('static const struct MysteryGiftEntry sMysteryGifts[] =')
    L.append('{')
    for c in d['codigos']:
        sp = 'SPECIES_' + c['species'] if c['species'] else 'SPECIES_NONE'
        held = 'ITEM_' + c['held'] if c['held'] else 'ITEM_NONE'
        rw = 'ITEM_' + c['reward'] if c['reward'] else 'ITEM_NONE'
        nat = 'NATURE_' + c['nature'] if c['nature'] != ALEATORIA else '0xFF'
        mv = ', '.join(('MOVE_' + m) if m else 'MOVE_NONE' for m in c['moves'])
        L.append('\t{ .code = "%s", .slot = %d, .species = %s, .level = %d, .shiny = %s, .hiddenAbility = %s, .nature = %s,'
                 % (c['code'], c['slot'], sp, int(c['level']), 'TRUE' if c['shiny'] else 'FALSE',
                    'TRUE' if c['ha'] else 'FALSE', nat))
        L.append('\t  .heldItem = %s, .moves = {%s}, .rewardItem = %s, .rewardQty = %d },'
                 % (held, mv, rw, int(c['qty']) if c['reward'] else 0))
    L.append('};')
    L.append('')
    dados = json.dumps(d, ensure_ascii=True, separators=(',', ':'))
    L.append('/* MG_EDITOR_DATA ' + dados.replace('*/', '* /') + ' */')
    L.append('')
    txt = '\n'.join(L)
    txt.encode('ascii')                 # garante: o arquivo e 100% ASCII (sem problema de codificacao no Windows)
    return txt


# ------------------------------------------------------------------------------------------------ conferir com o compilador
def achar_gcc():
    cands = [shutil.which('arm-none-eabi-gcc'), shutil.which('arm-none-eabi-gcc.exe')]
    dk = os.environ.get('DEVKITARM')
    if dk:
        cands += [os.path.join(dk, 'bin', 'arm-none-eabi-gcc'), os.path.join(dk, 'bin', 'arm-none-eabi-gcc.exe')]
    cands += [r'C:\devkitPro\devkitARM\bin\arm-none-eabi-gcc.exe', '/opt/devkitpro/devkitARM/bin/arm-none-eabi-gcc']
    return next((c for c in cands if c and os.path.isfile(c)), None)


def compilar_verificacao(raiz, gcc):
    """checagem de sintaxe do src/mystery_gift.c (que inclui o .h). Devolve (ok, texto_do_erro)"""
    cmd = [gcc, '-mthumb', '-mcpu=arm7tdmi', '-march=armv4t', '-fsyntax-only', '-w', os.path.join('src', 'mystery_gift.c')]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=raiz, timeout=120)
    except subprocess.TimeoutExpired:
        return False, 'timeout'
    if r.returncode == 0:
        return True, ''
    linhas = [l for l in (r.stderr or r.stdout).splitlines() if 'error' in l]
    return False, '\n'.join(linhas[:6]) or (r.stderr or r.stdout)[:600]


def escrever_h(d, raiz, lang='pt'):
    """Escreve <raiz>/src/mystery_gift_codes.h SOMENTE se o resultado compilar. Devolve (caminho, estado) onde estado em
    'ok' | 'sem_gcc' | 'sem_fonte'. Em caso de falha do compilador levanta RuntimeError e restaura o arquivo antigo."""
    raiz = limpar_caminho(raiz)
    pasta = os.path.join(raiz, 'src')
    if not os.path.isdir(pasta):
        raise RuntimeError('"%s" nao existe. / does not exist.' % pasta)
    destino = os.path.join(pasta, 'mystery_gift_codes.h')
    fonte = os.path.join(pasta, 'mystery_gift.c')
    texto = gerar_h(d)
    antigo = None
    if os.path.isfile(destino):
        with open(destino, 'rb') as f:
            antigo = f.read()
    with open(destino, 'w', encoding='ascii', newline='\n') as f:
        f.write(texto)
    estado = 'sem_fonte'
    if os.path.isfile(fonte):
        gcc = achar_gcc()
        if gcc:
            ok, erro = compilar_verificacao(raiz, gcc)
            if not ok:
                if antigo is None:
                    os.remove(destino)
                else:
                    with open(destino, 'wb') as f:
                        f.write(antigo)
                raise RuntimeError(t('ver_falhou', lang, e=erro))
            estado = 'ok'
        else:
            estado = 'sem_gcc'
        # O build do CFRU so recompila um .c quando o PROPRIO .c fica mais novo que o objeto (nao acompanha os .h).
        os.utime(fonte, None)
    return destino, estado


def texto_estado(estado, lang):
    return {'ok': t('ver_ok', lang), 'sem_gcc': t('ver_sem_gcc', lang), 'sem_fonte': t('ver_sem_fonte', lang)}[estado]


# ------------------------------------------------------------------------------------------------ importar .h antigo/novo
def importar_h(caminho):
    with open(caminho, encoding='utf-8', errors='ignore') as f:
        txt = f.read()
    m = re.search(r'/\* MG_EDITOR_DATA (.*?) \*/', txt, re.S)
    if m:
        return _completar(json.loads(m.group(1)))
    d = dados_padrao(); d['codigos'] = []
    base = re.search(r'#define\s+MYSTERY_GIFT_FLAG_BASE\s+(0x[0-9A-Fa-f]+|\d+)', txt)
    if base:
        d['flag_base'] = int(base.group(1), 0)
    pad = re.compile(r'\{\s*"([A-Za-z0-9]+)"\s*,\s*SPECIES_(\w+)\s*,\s*(\d+)\s*,\s*(TRUE|FALSE)\s*,\s*(TRUE|FALSE)\s*,'
                     r'\s*ITEM_(\w+)\s*,\s*(\w+)\s*\}')
    for i, mm in enumerate(pad.finditer(txt)):
        e = entrada_nova(i)
        e.update(code=mm.group(1).upper(), species=mm.group(2), level=int(mm.group(3)), shiny=mm.group(4) == 'TRUE',
                 ha=mm.group(5) == 'TRUE', held='' if mm.group(6) == 'NONE' else mm.group(6),
                 nature=ALEATORIA if not mm.group(7).startswith('NATURE_') else mm.group(7)[7:])
        d['codigos'].append(e)
    d['proximo_slot'] = len(d['codigos'])
    return d


# ------------------------------------------------------------------------------------------------ interface (tkinter)
def abrir_janela():
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox

    d, aviso_json = carregar_json()
    estado = {'listas': {'species': [], 'items': [], 'moves': []}, 'sel': None, 'bloq': False,
              'lang': d.get('idioma', 'pt') if d.get('idioma') in _IDX else 'pt'}
    L = lambda k, **kw: t(k, estado['lang'], **kw)

    root = tk.Tk()
    try:
        ttk.Style().theme_use('clam')
    except tk.TclError:
        pass
    reg = []                                  # (widget, chave, opcao, kwargs) - atualizados ao trocar de idioma

    def R(widget, chave, opcao='text', **kw):
        reg.append((widget, chave, opcao, kw))
        widget.configure(**{opcao: L(chave, **kw)})
        return widget

    # ---- barra de cima
    topo = ttk.LabelFrame(root)
    R(topo, 'proj_frame')
    topo.pack(fill='x', padx=8, pady=(8, 4))
    v_proj = tk.StringVar(value=d['projeto'])
    v_flag = tk.StringVar(value='0x%X' % d['flag_base'])
    v_mus = tk.StringVar()
    v_idioma = tk.StringVar()

    R(ttk.Label(topo), 'pasta_proj').grid(row=0, column=0, sticky='w', padx=6, pady=4)
    ttk.Entry(topo, textvariable=v_proj, width=60).grid(row=0, column=1, sticky='we', padx=4)
    R(ttk.Button(topo, command=lambda: escolher_pasta()), 'procurar').grid(row=0, column=2, padx=4)
    R(ttk.Label(topo), 'idioma').grid(row=0, column=3, sticky='e', padx=(10, 2))
    cb_idioma = ttk.Combobox(topo, textvariable=v_idioma, values=[n for _, n in IDIOMAS], state='readonly', width=22)
    cb_idioma.grid(row=0, column=4, padx=(0, 8))
    R(ttk.Label(topo), 'musica').grid(row=1, column=0, sticky='w', padx=6, pady=4)
    cb_mus = ttk.Combobox(topo, textvariable=v_mus, state='readonly', width=48)
    cb_mus.grid(row=1, column=1, sticky='w', padx=4)
    R(ttk.Label(topo), 'flag_ini').grid(row=1, column=3, sticky='e', padx=(10, 2))
    ttk.Entry(topo, textvariable=v_flag, width=9).grid(row=1, column=4, sticky='w', padx=(0, 8))
    topo.columnconfigure(1, weight=1)

    corpo = ttk.Frame(root)
    corpo.pack(fill='both', expand=True, padx=8, pady=4)

    # ---- lista
    esq = ttk.LabelFrame(corpo)
    R(esq, 'lista_frame')
    esq.pack(side='left', fill='y')
    cols = ('code', 'flag', 'tipo', 'poke', 'item')
    tv = ttk.Treeview(esq, columns=cols, show='headings', height=18, selectmode='browse')
    larg = {'code': 90, 'flag': 60, 'tipo': 115, 'poke': 130, 'item': 160}
    chaves_col = {'code': 'col_codigo', 'flag': 'col_flag', 'tipo': 'col_tipo', 'poke': 'col_poke', 'item': 'col_item'}
    for c in cols:
        tv.column(c, width=larg[c], anchor='w')
    tv.pack(side='left', fill='y', padx=(6, 0), pady=6)
    sb = ttk.Scrollbar(esq, orient='vertical', command=tv.yview)
    sb.pack(side='left', fill='y', pady=6, padx=(0, 6))
    tv.configure(yscrollcommand=sb.set)

    # ---- formulario
    dir_ = ttk.LabelFrame(corpo)
    R(dir_, 'form_frame')
    dir_.pack(side='left', fill='both', expand=True, padx=(8, 0))

    f = {k: tk.StringVar() for k in ('code', 'species', 'held', 'nature', 'm1', 'm2', 'm3', 'm4', 'reward')}
    f['level'] = tk.IntVar(value=5)
    f['qty'] = tk.IntVar(value=1)
    f['shiny'] = tk.BooleanVar()
    f['ha'] = tk.BooleanVar()
    f['tipo'] = tk.StringVar(value='poke')

    def combo_busca(pai, var, chave, largura=26):
        cb = ttk.Combobox(pai, textvariable=var, width=largura)

        def filtrar(ev=None):
            if ev is not None and ev.keysym in ('Up', 'Down', 'Return', 'Escape', 'Tab'):
                return
            txt = var.get().strip().upper().replace(' ', '_')
            base = estado['listas'][chave]
            cb['values'] = [n for n in base if txt in n][:300] if txt else base[:300]
        cb.bind('<KeyRelease>', filtrar)
        cb.bind('<FocusIn>', lambda e: (filtrar(), cb.after(1, lambda: cb.select_range(0, 'end'))))
        return cb

    def sel_tudo(w):
        w.bind('<FocusIn>', lambda e: w.after(1, lambda: w.select_range(0, 'end')), add='+')
        w.bind('<Control-a>', lambda e: (w.select_range(0, 'end'), 'break')[1])

    R(ttk.Label(dir_), 'cod_label').grid(row=0, column=0, sticky='w', padx=8, pady=(8, 2))
    e_code = ttk.Entry(dir_, textvariable=f['code'], width=14, font=('Consolas', 12, 'bold'))
    e_code.grid(row=0, column=1, sticky='w', pady=(8, 2))
    sel_tudo(e_code)

    def forcar_maiusculo(*_):
        v = re.sub(r'[^A-Za-z0-9]', '', f['code'].get()).upper()[:TAM_CODIGO]
        if v != f['code'].get():
            f['code'].set(v)
    f['code'].trace_add('write', forcar_maiusculo)

    flaginfo = tk.StringVar(value='')
    tipo_fr = ttk.Frame(dir_)
    tipo_fr.grid(row=1, column=0, columnspan=2, sticky='w', padx=8, pady=4)
    R(ttk.Label(tipo_fr), 'presente_e').pack(side='left')
    for chave, val in (('rad_poke', 'poke'), ('rad_item', 'item'), ('rad_ambos', 'ambos')):
        rb = ttk.Radiobutton(tipo_fr, value=val, variable=f['tipo'], command=lambda: atualizar_tipo())
        R(rb, chave).pack(side='left', padx=8)

    g_poke = ttk.LabelFrame(dir_)
    R(g_poke, 'g_poke')
    g_poke.grid(row=2, column=0, columnspan=2, sticky='we', padx=8, pady=4)
    R(ttk.Label(g_poke), 'especie').grid(row=0, column=0, sticky='w', padx=6, pady=3)
    c_sp = combo_busca(g_poke, f['species'], 'species'); c_sp.grid(row=0, column=1, sticky='w')
    R(ttk.Label(g_poke), 'nivel').grid(row=0, column=2, sticky='e', padx=(14, 2))
    sp_nivel = ttk.Spinbox(g_poke, from_=1, to=100, textvariable=f['level'], width=5)
    sp_nivel.grid(row=0, column=3, sticky='w'); sel_tudo(sp_nivel)
    R(ttk.Checkbutton(g_poke, variable=f['shiny']), 'shiny').grid(row=1, column=1, sticky='w', pady=2)
    R(ttk.Checkbutton(g_poke, variable=f['ha']), 'ha').grid(row=1, column=2, columnspan=2, sticky='w', pady=2)
    R(ttk.Label(g_poke), 'segura').grid(row=2, column=0, sticky='w', padx=6, pady=3)
    c_held = combo_busca(g_poke, f['held'], 'items'); c_held.grid(row=2, column=1, sticky='w')
    R(ttk.Label(g_poke), 'nature').grid(row=2, column=2, sticky='e', padx=(14, 2))
    cb_nat = ttk.Combobox(g_poke, textvariable=f['nature'], state='readonly', width=12)
    cb_nat.grid(row=2, column=3, sticky='w')
    R(ttk.Label(g_poke), 'golpes_dica').grid(row=3, column=0, columnspan=4, sticky='w', padx=6, pady=(8, 0))
    c_mv = []
    for i in range(4):
        R(ttk.Label(g_poke), 'golpe_n', n=i + 1).grid(row=4 + i // 2, column=(i % 2) * 2, sticky='e', padx=(6, 2), pady=2)
        cb = combo_busca(g_poke, f['m%d' % (i + 1)], 'moves', 22)
        cb.grid(row=4 + i // 2, column=(i % 2) * 2 + 1, sticky='w', pady=2)
        c_mv.append(cb)

    g_item = ttk.LabelFrame(dir_)
    R(g_item, 'g_item')
    g_item.grid(row=3, column=0, columnspan=2, sticky='we', padx=8, pady=4)
    R(ttk.Label(g_item), 'item_lbl').grid(row=0, column=0, sticky='w', padx=6, pady=4)
    c_rw = combo_busca(g_item, f['reward'], 'items'); c_rw.grid(row=0, column=1, sticky='w')
    R(ttk.Label(g_item), 'qtd').grid(row=0, column=2, sticky='e', padx=(14, 2))
    sp_qtd = ttk.Spinbox(g_item, from_=1, to=999, textvariable=f['qty'], width=6)
    sp_qtd.grid(row=0, column=3, sticky='w'); sel_tudo(sp_qtd)

    botoes = ttk.Frame(dir_)
    botoes.grid(row=4, column=0, columnspan=2, sticky='we', padx=8, pady=8)
    ttk.Label(dir_, textvariable=flaginfo, foreground='#036').grid(row=5, column=0, columnspan=2, sticky='w', padx=8, pady=(0, 6))
    status = tk.StringVar(value='')
    lbl_status = ttk.Label(root, textvariable=status, foreground='#a00', wraplength=1000, justify='left')
    lbl_status.pack(fill='x', padx=10)

    def aviso(txt, ok=False):
        lbl_status.configure(foreground='#060' if ok else '#a00')
        status.set(txt)

    # ---------------- apoio de idioma
    def nat_para_tela(n):
        return L('aleatoria') if n == ALEATORIA else n

    def tela_para_nat(s):
        return ALEATORIA if (not s or s in TR['aleatoria']) else s

    def listar_musicas():
        cb_mus['values'] = [nome_musica(m, estado['lang']) for m in MUSICAS]
        v_mus.set(nome_musica(d['musica'], estado['lang']))

    def musica_id():
        nome = v_mus.get()
        for m in MUSICAS:
            if nome_musica(m, estado['lang']) == nome:
                return m
        return d['musica']

    def tipo_de(c):
        if c['species'] and c['reward']:
            return L('tipo_ambos')
        return L('tipo_poke') if c['species'] else L('tipo_item')

    def flag_de(c):
        try:
            base = int(v_flag.get().strip(), 0)
        except ValueError:
            base = d['flag_base']
        return '0x%X' % (base + c['slot'])

    def linha_valores(c):
        it = ('%s x%d' % (c['reward'], c['qty'])) if c['reward'] else '-'
        return (c['code'], flag_de(c), tipo_de(c), c['species'] or '-', it)

    def aplicar_idioma():
        root.title(L('titulo'))
        for w, chave, opcao, kw in reg:
            w.configure(**{opcao: L(chave, **kw)})
        for c in cols:
            tv.heading(c, text=L(chaves_col[c]))
        cb_nat['values'] = [L('aleatoria')] + NATURES
        listar_musicas()
        v_idioma.set(dict(IDIOMAS)[estado['lang']])
        rodape_dica.configure(text=L('dica'))
        btn_salvar.configure(text=L('salvar'))
        for w, chave in ((b_novo, 'novo'), (b_dup, 'duplicar'), (b_exc, 'excluir'), (b_apl, 'aplicar'), (b_imp, 'importar')):
            w.configure(text=L(chave))
        i = indice_sel()
        recarregar_lista(i)
        if i is not None and i < len(d['codigos']):
            preencher(d['codigos'][i])
        else:
            atualizar_tipo()
        status.set('')

    def ao_trocar_idioma(_=None):
        nova = estado['lang']
        for k, n in IDIOMAS:
            if n == v_idioma.get():
                nova = k
        if nova != estado['lang']:
            # guarda o que esta no formulario antes de redesenhar (a troca nao perde nada)
            if estado['sel'] is not None and estado['sel'] < len(d['codigos']):
                d['codigos'][estado['sel']] = ler_form(d['codigos'][estado['sel']]['slot'])
            estado['lang'] = nova
            d['idioma'] = nova
            try:
                salvar_idioma(nova)
            except OSError:
                pass
            aplicar_idioma()
    cb_idioma.bind('<<ComboboxSelected>>', ao_trocar_idioma)

    # ---------------- logica
    def recarregar_lista(selecionar=None):
        estado['bloq'] = True
        root.after_idle(lambda: estado.update(bloq=False))
        tv.delete(*tv.get_children())
        for i, c in enumerate(d['codigos']):
            tv.insert('', 'end', iid=str(i), values=linha_valores(c))
        if selecionar is not None and 0 <= selecionar < len(d['codigos']):
            tv.selection_set(str(selecionar)); tv.see(str(selecionar))

    def atualizar_tipo():
        tp = f['tipo'].get()
        for ch in g_poke.winfo_children():
            try:
                ch.configure(state='normal' if tp in ('poke', 'ambos') else 'disabled')
            except tk.TclError:
                pass
        for ch in g_item.winfo_children():
            try:
                ch.configure(state='normal' if tp in ('item', 'ambos') else 'disabled')
            except tk.TclError:
                pass
        cb_nat.configure(state='readonly' if tp in ('poke', 'ambos') else 'disabled')

    def preencher(c):
        flaginfo.set(L('flag_deste', f=flag_de(c)))
        f['code'].set(c['code']); f['species'].set(c['species']); f['level'].set(c['level'])
        f['shiny'].set(c['shiny']); f['ha'].set(c['ha']); f['held'].set(c['held']); f['nature'].set(nat_para_tela(c['nature']))
        for i in range(4):
            f['m%d' % (i + 1)].set(c['moves'][i])
        f['reward'].set(c['reward']); f['qty'].set(c['qty'] or 1)
        f['tipo'].set('ambos' if c['species'] and c['reward'] else ('poke' if c['species'] or not c['reward'] else 'item'))
        atualizar_tipo()

    def ler_form(slot):
        c = entrada_nova(slot)
        tp = f['tipo'].get()
        c['code'] = f['code'].get().strip().upper()
        if tp in ('poke', 'ambos'):
            c['species'] = f['species'].get().strip().upper().replace(' ', '_')
            try:
                c['level'] = int(f['level'].get())
            except (tk.TclError, ValueError):
                c['level'] = 0
            c['shiny'] = bool(f['shiny'].get()); c['ha'] = bool(f['ha'].get())
            c['held'] = f['held'].get().strip().upper().replace(' ', '_')
            c['nature'] = tela_para_nat(f['nature'].get())
            c['moves'] = [f['m%d' % (i + 1)].get().strip().upper().replace(' ', '_') for i in range(4)]
        if tp in ('item', 'ambos'):
            c['reward'] = f['reward'].get().strip().upper().replace(' ', '_')
            try:
                c['qty'] = int(f['qty'].get())
            except (tk.TclError, ValueError):
                c['qty'] = 0
        return c

    def indice_sel():
        s = tv.selection()
        return int(s[0]) if s else None

    def listas_ou_none():
        return estado['listas'] if any(estado['listas'].values()) else None

    def aplicar(mostrar=True):
        i = estado['sel']
        if i is None or i >= len(d['codigos']):
            return True
        novo_c = ler_form(d['codigos'][i]['slot'])
        d['codigos'][i] = novo_c
        erros = validar({'codigos': [novo_c]}, listas_ou_none(), estado['lang'])
        recarregar_lista(i)
        if erros:
            aviso(' | '.join(erros))
            return False
        if mostrar:
            aviso(L('st_aplicado', c=novo_c['code']), True)
        return True

    def ao_selecionar(_=None, force=False):
        if estado['bloq'] and not force:
            return
        i = indice_sel()
        if i is None:
            return
        ant = estado['sel']
        if ant is not None and ant != i and ant < len(d['codigos']) and not force:
            d['codigos'][ant] = ler_form(d['codigos'][ant]['slot'])
            tv.item(str(ant), values=linha_valores(d['codigos'][ant]))
        estado['sel'] = i
        preencher(d['codigos'][i])
        aviso('')
    tv.bind('<<TreeviewSelect>>', ao_selecionar)

    def proximo_slot_livre():
        """nunca reaproveita o slot de um codigo excluido (a flag dele pode estar ligada em saves de jogadores)"""
        usados = {c['slot'] for c in d['codigos']}
        n = max(d.get('proximo_slot', 0), (max(usados) + 1) if usados else 0)
        return n if n < MAX_CODIGOS else None

    def novo():
        aplicar(False)
        s = proximo_slot_livre()
        if s is None:
            messagebox.showwarning('!', L('dlg_limite', n=MAX_CODIGOS))
            return
        d['proximo_slot'] = s + 1
        d['codigos'].append(entrada_nova(s))
        i = len(d['codigos']) - 1
        estado['sel'] = i
        recarregar_lista(i); preencher(d['codigos'][i]); e_code.focus_set()
        aviso(L('st_novo'), True)

    def duplicar():
        i = indice_sel()
        if i is None:
            return
        aplicar(False)
        s = proximo_slot_livre()
        if s is None:
            messagebox.showwarning('!', L('dlg_limite', n=MAX_CODIGOS))
            return
        d['proximo_slot'] = s + 1
        c = json.loads(json.dumps(d['codigos'][i])); c['slot'] = s; c['code'] = ''
        d['codigos'].append(c)
        j = len(d['codigos']) - 1
        estado['sel'] = j
        recarregar_lista(j); preencher(c); e_code.focus_set()
        aviso(L('st_copia'), True)

    def excluir():
        i = indice_sel()
        if i is None:
            return
        c = d['codigos'][i]
        if not messagebox.askyesno(L('dlg_excluir_t'), L('dlg_excluir', c=c['code'] or L('dlg_vazio'), s=c['slot'])):
            return
        d['proximo_slot'] = max(d.get('proximo_slot', 0), c['slot'] + 1)
        del d['codigos'][i]
        estado['sel'] = None
        recarregar_lista(min(i, len(d['codigos']) - 1) if d['codigos'] else None)
        if d['codigos']:
            ao_selecionar(force=True)
        aviso(L('st_excluido'), True)

    def escolher_pasta():
        p = filedialog.askdirectory(title=L('dlg_pasta_titulo'))
        if p:
            v_proj.set(p); ler_projeto()

    def ler_projeto():
        raiz = limpar_caminho(v_proj.get())
        estado['listas'] = carregar_listas(raiz) if raiz else {'species': [], 'items': [], 'moves': []}
        n = estado['listas']
        for cb, ch in ((c_sp, 'species'), (c_held, 'items'), (c_rw, 'items')) + tuple((m, 'moves') for m in c_mv):
            cb['values'] = n[ch][:300]
        if not raiz:
            aviso(L('st_sem_proj'))
        elif not any(n.values()):
            aviso(L('st_sem_const'))
        else:
            aviso(L('st_proj_lido', a=len(n['species']), b=len(n['items']), c=len(n['moves'])), True)

    def ler_flag_base():
        try:
            return int(v_flag.get().strip(), 0)
        except ValueError:
            return None

    def salvar_e_gerar():
        lang = estado['lang']
        if not aplicar(False):
            messagebox.showerror(L('dlg_erro'), L('dlg_corrija'))
            return
        fb = ler_flag_base()
        if fb is None:
            messagebox.showerror(L('dlg_erro'), L('dlg_flag_num'))
            return
        d['flag_base'] = fb
        d['projeto'] = limpar_caminho(v_proj.get())
        d['musica'] = musica_id()
        d['idioma'] = lang
        erros = validar(d, listas_ou_none(), lang, d['projeto'] or None)
        if erros:
            aviso(' | '.join(erros[:6]))
            messagebox.showerror(L('dlg_nao_gerar'), '\n'.join(erros[:12]))
            return
        salvar_json(d)
        if not d['projeto']:
            messagebox.showwarning(L('dlg_escolha_proj'), L('dlg_salvei_json'))
            return
        try:
            dest, est = escrever_h(d, d['projeto'], lang)
        except Exception as ex:
            aviso(str(ex).split('\n')[0])
            messagebox.showerror(L('dlg_erro_escrever'), str(ex))
            return
        v = texto_estado(est, lang)
        aviso(L('st_gerado', d=dest, v=v), est == 'ok')
        (messagebox.showinfo if est == 'ok' else messagebox.showwarning)(L('dlg_pronto_t'), L('dlg_pronto', d=dest, v=v))

    def importar():
        p = filedialog.askopenfilename(title=L('dlg_imp_titulo'), filetypes=[('Header C', '*.h'), ('*', '*.*')])
        if not p:
            return
        try:
            novo_d = importar_h(p)
        except Exception as ex:
            messagebox.showerror(L('dlg_erro'), L('dlg_imp_erro', e=ex))
            return
        if not novo_d['codigos']:
            messagebox.showwarning('!', L('dlg_imp_vazio'))
            return
        for k in ('codigos', 'flag_base', 'musica', 'proximo_slot'):
            d[k] = novo_d[k]
        v_flag.set('0x%X' % d['flag_base'])
        estado['sel'] = None
        recarregar_lista(0); ao_selecionar(force=True)
        listar_musicas()
        aviso(L('st_importados', n=len(d['codigos'])), True)

    b_novo = ttk.Button(botoes, command=novo); b_novo.pack(side='left')
    b_dup = ttk.Button(botoes, command=duplicar); b_dup.pack(side='left', padx=4)
    b_exc = ttk.Button(botoes, command=excluir); b_exc.pack(side='left')
    b_apl = ttk.Button(botoes, command=aplicar); b_apl.pack(side='left', padx=(16, 0))
    b_imp = ttk.Button(botoes, command=importar); b_imp.pack(side='right')

    rodape = ttk.Frame(root)
    rodape.pack(fill='x', padx=8, pady=(2, 8))
    btn_salvar = ttk.Button(rodape, command=salvar_e_gerar)
    btn_salvar.pack(side='right', ipadx=10, ipady=4)
    rodape_dica = ttk.Label(rodape, foreground='#555')
    rodape_dica.pack(side='left')

    def ao_mudar_flag_base(*_):
        s_ = indice_sel()
        recarregar_lista(s_)
        if s_ is not None and s_ < len(d['codigos']):
            preencher(d['codigos'][s_])
    v_flag.trace_add('write', ao_mudar_flag_base)

    aplicar_idioma()
    ler_projeto()
    recarregar_lista(0 if d['codigos'] else None)
    if d['codigos']:
        estado['sel'] = 0
        preencher(d['codigos'][0])
    if aviso_json:
        root.after(300, lambda: messagebox.showwarning('!', L('dlg_json_corrompido', b=aviso_json)))
    root.update_idletasks()
    root.minsize(root.winfo_reqwidth(), root.winfo_reqheight())
    root.mainloop()


# ------------------------------------------------------------------------------------------------ linha de comando
def main(argv):
    lang = 'pt'
    if '--idioma' in argv:
        lang = argv[argv.index('--idioma') + 1]
        if lang not in _IDX:
            print('--idioma: pt, en ou es')
            return 1
    if '--gerar' in argv:
        d, _aviso = carregar_json()
        raiz = d['projeto']
        if '--projeto' in argv:
            raiz = argv[argv.index('--projeto') + 1]
        raiz = limpar_caminho(raiz)
        listas = carregar_listas(raiz) if raiz else None
        erros = validar(d, listas if listas and any(listas.values()) else None, lang, raiz or None)
        if erros:
            print('ERROS:\n - ' + '\n - '.join(erros))
            return 1
        try:
            dest, est = escrever_h(d, raiz, lang)
        except Exception as ex:
            print(ex)
            return 1
        print('OK:', dest, '|', texto_estado(est, lang))
        return 0
    if '--importar' in argv:
        d = importar_h(argv[argv.index('--importar') + 1])
        salvar_json(d)
        print('%d codes -> %s' % (len(d['codigos']), ARQ_JSON))
        return 0
    abrir_janela()
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
