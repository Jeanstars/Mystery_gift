#!/bin/bash
# uso: build_harness.sh  -> gera test.gba com a tela injetada em 0x09320000
set -e
B=/home/claude/build; H=/home/claude/harness
CF="-mthumb -mno-thumb-interwork -mcpu=arm7tdmi -mtune=arm7tdmi -mno-long-calls -march=armv4t -Wall -Os"
cd $B
cp /home/claude/out/projeto/src/mystery_gift_codes.h src/; cp /home/claude/out/projeto/include/new/mystery_gift.h include/new/
for f in mystery_gift mystery_gift_gfx; do cp /home/claude/out/projeto/src/$f.c src/; arm-none-eabi-gcc $CF -c src/$f.c -o $H/$f.o; done
cp /home/claude/out/projeto/strings/mystery_gift.string strings/
python3 - <<'PY'
import sys, os, importlib.util
sys.path.insert(0, os.path.abspath('scripts'))
spec = importlib.util.spec_from_file_location('cfru_string', 'scripts/string.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
m.StringFileConverter('strings/mystery_gift.string')
PY
arm-none-eabi-as -mthumb -I ./assembly -c strings/mystery_gift.s -o $H/strings.o
arm-none-eabi-as -mthumb -I ./assembly -c assembly/thumb_compiler_helper.s -o $H/helper.o
cp $H/harness_stubs.c src/harness_stubs.c
arm-none-eabi-gcc $CF $HARNESS_DEFS -c src/harness_stubs.c -o $H/harness_stubs.o
grep -v -E '^(CreateMon|ZeroMonData|SetMonData|GetMonData|CalculateMonStats|IsMonShiny|AddBagItem|CheckBagHasSpace)[ =]' BPRE.ld > $H/BPRE_h.ld
cd $H
cat > stubs.s <<'EOS'
.thumb
.global GiveMonNatureAndAbility
.global HealMon
.global SetMonPokedexFlags
.thumb_func
GiveMonNatureAndAbility: bx lr
.thumb_func
HealMon: bx lr
.thumb_func
SetMonPokedexFlags: bx lr
.global TransferPlttBuffer
.thumb_func
TransferPlttBuffer: ldr r3, =0x08070475
 bx r3
.pool
EOS
arm-none-eabi-as -mthumb stubs.s -o stubs.o
cat > h.ld <<'EOL'
MEMORY { ROM (rx) : ORIGIN = 0x09320000, LENGTH = 0x100000 }
SECTIONS { .text : { *(.text) *(.text.*) *(.rodata) *(.rodata.*) *(.data) *(.data.*) } > ROM }
EOL
arm-none-eabi-ld -T h.ld BPRE_h.ld mystery_gift.o mystery_gift_gfx.o strings.o helper.o stubs.o harness_stubs.o -o h.elf 2>&1 | head -20
arm-none-eabi-objcopy -O binary h.elf h.bin
python3 - <<'PY'
d=bytearray(open('/home/claude/build/BPRE0.gba','rb').read())
b=open('/home/claude/harness/h.bin','rb').read()
d[0x1320000:0x1320000+len(b)]=b
open('/home/claude/harness/test.gba','wb').write(d)
print('injetado', len(b), 'bytes')
PY
arm-none-eabi-nm h.elf | grep -E " (t|T) (CB2_MysteryGift|MysteryGift_Start|Task_MysteryGift)$"
