#pragma once

/*
 * MYSTERY GIFT - presente misterioso por codigo.
 *
 *  callasm MysteryGift_Start      (ou special 0x122, com o routinepointers do pacote)
 *  waitstate
 *
 * Resultado em LASTRESULT: 1 = recebeu um presente, 0 = saiu sem receber.
 * Usa as variaveis 0x8004, 0x8005 e 0x8006 como rascunho.
 */
void MysteryGift_Start(void);
