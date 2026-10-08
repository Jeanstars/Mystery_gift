.align 2
.thumb

.include "../xse_commands.s"
.include "../xse_defines.s"
.include "../asm_defines.s"

@ Mystery Gift - scripts para ligar em NPC/porta/item (ou chamar com "call").
@ Tudo (teclado, animacao, texto, entrega do Pokemon) acontece dentro da tela.
@ LASTRESULT depois do waitstate: 1 = recebeu um presente, 0 = saiu sem receber.

.global MysteryGift_Script
.global MysteryGift_Script_Special

@ Versao com callasm: funciona sempre, nao depende de nada na tabela de specials.
MysteryGift_Script:
	lockall
	callasm MysteryGift_Start
	waitstate
	releaseall
	end

@ Versao com "special 0x122": precisa rodar ferramentas/instalar_special.py (acrescenta 1 linha no routinepointers).
@ (Sem ele o special nao faz nada e o waitstate trava - use a versao acima se tiver duvida.)
MysteryGift_Script_Special:
	lockall
	special 0x122
	waitstate
	releaseall
	end
