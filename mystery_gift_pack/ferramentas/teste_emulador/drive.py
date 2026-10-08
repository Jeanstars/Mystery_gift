#!/usr/bin/env python3
"""Gera o roteiro do emulador: digita um codigo navegando no teclado (mesma logica do C) e tira capturas."""
import sys, collections, subprocess, os
from PIL import Image
H='/home/claude/harness'
KEYS=list("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ")+['DEL','OK']
def pos(i): return (i%10,i//10) if i<36 else (6+(i-36),3)
def idx(c,r): return r*10+c if r<3 else (30+c if c<6 else 36+(c-6))
def rowlen(r): return 8 if r==3 else 10
def move(i,d):
    c,r=pos(i)
    if d=='RIGHT': c=0 if c+1>=rowlen(r) else c+1
    elif d=='LEFT': c=rowlen(r)-1 if c==0 else c-1
    elif d=='DOWN':
        r=0 if r>=3 else r+1; c=min(c,rowlen(r)-1)
    elif d=='UP':
        r=3 if r==0 else r-1; c=min(c,rowlen(r)-1)
    return idx(c,r)
def path(a,b):
    q=collections.deque([(a,[])]); seen={a}
    while q:
        i,p=q.popleft()
        if i==b: return p
        for d in ('RIGHT','LEFT','DOWN','UP'):
            j=move(i,d)
            if j not in seen: seen.add(j); q.append((j,p+[d]))
class Script:
    def __init__(s): s.l=[]; s.cur=10; s.n=0
    def run(s,n): s.l.append(f'run {n}')
    def press(s,k,n=8): s.l.append(f'press {k} {n}')
    def shot(s,name): s.l.append(f'shot {H}/shots/{name}.ppm'); s.n+=1
    def goto(s,key):
        t=KEYS.index(key)
        for d in path(s.cur,t): s.press(d,6)
        s.cur=t
    def type(s,text):
        for ch in text: s.goto(ch); s.press('A',6)
    def save(s,fn): open(fn,'w').write('\n'.join(s.l)+'\n')

def cb2_addr():
    out=subprocess.check_output(['arm-none-eabi-nm','/home/claude/harness/h.elf']).decode()
    for l in out.splitlines():
        p=l.split()
        if len(p)==3 and p[2]=='CB2_MysteryGift': return '%08X'%(int(p[0],16)|1)
    raise SystemExit('CB2_MysteryGift nao encontrado')
