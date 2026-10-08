// So para o teste no emulador: o CFRU tem uma struct Pokemon propria (campos sem criptografia); as funcoes vanilla da
// ROM base esperam o formato criptografado e entrariam em loop. No build real quem faz isso e o CFRU.
#include "defines.h"
#include "../include/constants/items.h"
void ZeroMonData(struct Pokemon* mon) { u8* p = (u8*) mon; for (u32 i = 0; i < sizeof(struct Pokemon); ++i) p[i] = 0; }
void CreateMon(struct Pokemon* mon, u16 species, u8 level, u8 fixedIV, u8 hasFixedPersonality, u32 fixedPersonality, u8 otIdType, u32 fixedOtId)
{
	(void) level; (void) fixedIV; (void) hasFixedPersonality; (void) fixedPersonality; (void) otIdType; (void) fixedOtId;
	ZeroMonData(mon); mon->species = species; mon->personality = 0x12345678; mon->otid = 0x0BAD1234;
}
void SetMonData(struct Pokemon* mon, s32 field, const void* data) { (void) mon; (void) field; (void) data; }
u32 GetMonData(const struct Pokemon* mon, s32 field, const void* data) { (void) mon; (void) field; (void) data; return 0; }
void CalculateMonStats(struct Pokemon* mon) { (void) mon; }
bool8 IsMonShiny(struct Pokemon* mon) { (void) mon; return FALSE; }
#ifdef FORCE_NOROOM
u8 GiveMonToPlayer(struct Pokemon* mon) { (void) mon; return 2; }
#else
u8 GiveMonToPlayer(struct Pokemon* mon) { (void) mon; return 0; }
#endif

bool8 AddBagItem(u16 itemId, u16 count) { (void) itemId; (void) count; return TRUE; }
bool8 CheckBagHasSpace(u16 itemId, u16 count) { (void) itemId; (void) count; return TRUE; }
const u8* ItemId_GetName(u16 itemId)
{
	static const u8 master[] = {CHAR_M, CHAR_A, CHAR_S, CHAR_T, CHAR_E, CHAR_R, CHAR_SPACE, CHAR_B, CHAR_A, CHAR_L, CHAR_L, EOS};
	static const u8 candy[] = {CHAR_R, CHAR_A, CHAR_R, CHAR_E, CHAR_SPACE, CHAR_C, CHAR_A, CHAR_N, CHAR_D, CHAR_Y, EOS};
	return (itemId == ITEM_RARE_CANDY) ? candy : master;
}

const struct BattleMove gBattleMoves[1200] = {{0}};
