/*
 * ARQUIVO GERADO pelo editor_mystery_gift.py  -  NAO EDITE A MAO (use o editor).
 * Os codigos ficam em codigos.json ao lado do editor.
 */

//Primeira flag usada. O codigo de numero N usa a flag MYSTERY_GIFT_FLAG_BASE + N.
//As flags 0x950 a 0x98F ficam reservadas para o Mystery Gift.
#define MYSTERY_GIFT_FLAG_BASE 0x950
#define MYSTERY_GIFT_MAX_CODES 64

//Musica da tela (0 = nao troca a musica do mapa)
#define MYSTERY_GIFT_MENU_MUSIC 0x111

//Flags de idioma do seu projeto (as mesmas do pacote Stars)
#define MG_FLAG_LANG_EN 0x261
#define MG_FLAG_LANG_ES 0x262

struct MysteryGiftEntry
{
	const char* code;
	u8 slot;			//Numero da flag deste codigo (nunca muda)
	u16 species;		//SPECIES_NONE = presente so de item
	u8 level;
	u8 shiny;
	u8 hiddenAbility;
	u8 nature;			//0xFF = aleatoria
	u16 heldItem;		//Item que o Pokemon segura
	u16 moves[4];		//Todos MOVE_NONE = golpes normais do nivel
	u16 rewardItem;		//Item entregue na mochila (ITEM_NONE = nenhum)
	u16 rewardQty;
};

static const struct MysteryGiftEntry sMysteryGifts[] =
{
	{ .code = "EEVEE001", .slot = 0, .species = SPECIES_EEVEE, .level = 10, .shiny = FALSE, .hiddenAbility = FALSE, .nature = 0xFF,
	  .heldItem = ITEM_NONE, .moves = {MOVE_NONE, MOVE_NONE, MOVE_NONE, MOVE_NONE}, .rewardItem = ITEM_NONE, .rewardQty = 0 },
	{ .code = "DRATINI", .slot = 1, .species = SPECIES_DRATINI, .level = 15, .shiny = TRUE, .hiddenAbility = FALSE, .nature = 0xFF,
	  .heldItem = ITEM_NONE, .moves = {MOVE_NONE, MOVE_NONE, MOVE_NONE, MOVE_NONE}, .rewardItem = ITEM_NONE, .rewardQty = 0 },
	{ .code = "MEWGIFT", .slot = 2, .species = SPECIES_MEW, .level = 30, .shiny = FALSE, .hiddenAbility = FALSE, .nature = 0xFF,
	  .heldItem = ITEM_NONE, .moves = {MOVE_NONE, MOVE_NONE, MOVE_NONE, MOVE_NONE}, .rewardItem = ITEM_NONE, .rewardQty = 0 },
	{ .code = "GOLPES01", .slot = 3, .species = SPECIES_PIKACHU, .level = 25, .shiny = FALSE, .hiddenAbility = FALSE, .nature = 0xFF,
	  .heldItem = ITEM_LIGHT_BALL, .moves = {MOVE_THUNDERBOLT, MOVE_QUICKATTACK, MOVE_IRONTAIL, MOVE_SURF}, .rewardItem = ITEM_NONE, .rewardQty = 0 },
	{ .code = "ITEM0001", .slot = 4, .species = SPECIES_NONE, .level = 5, .shiny = FALSE, .hiddenAbility = FALSE, .nature = 0xFF,
	  .heldItem = ITEM_NONE, .moves = {MOVE_NONE, MOVE_NONE, MOVE_NONE, MOVE_NONE}, .rewardItem = ITEM_MASTER_BALL, .rewardQty = 5 },
	{ .code = "COMBO001", .slot = 5, .species = SPECIES_CHARMANDER, .level = 15, .shiny = FALSE, .hiddenAbility = FALSE, .nature = NATURE_ADAMANT,
	  .heldItem = ITEM_NONE, .moves = {MOVE_EMBER, MOVE_SCRATCH, MOVE_SLASH, MOVE_NONE}, .rewardItem = ITEM_RARE_CANDY, .rewardQty = 10 },
};

/* MG_EDITOR_DATA {"projeto":"","flag_base":2384,"musica":273,"proximo_slot":6,"codigos":[{"code":"EEVEE001","species":"EEVEE","level":10,"shiny":false,"ha":false,"held":"","nature":"(aleatoria)","moves":["","","",""],"reward":"","qty":1,"slot":0},{"code":"DRATINI","species":"DRATINI","level":15,"shiny":true,"ha":false,"held":"","nature":"(aleatoria)","moves":["","","",""],"reward":"","qty":1,"slot":1},{"code":"MEWGIFT","species":"MEW","level":30,"shiny":false,"ha":false,"held":"","nature":"(aleatoria)","moves":["","","",""],"reward":"","qty":1,"slot":2},{"code":"GOLPES01","species":"PIKACHU","level":25,"shiny":false,"ha":false,"held":"LIGHT_BALL","nature":"(aleatoria)","moves":["THUNDERBOLT","QUICKATTACK","IRONTAIL","SURF"],"reward":"","qty":1,"slot":3},{"code":"ITEM0001","species":"","level":5,"shiny":false,"ha":false,"held":"","nature":"(aleatoria)","moves":["","","",""],"reward":"MASTER_BALL","qty":5,"slot":4},{"code":"COMBO001","species":"CHARMANDER","level":15,"shiny":false,"ha":false,"held":"","nature":"ADAMANT","moves":["EMBER","SCRATCH","SLASH",""],"reward":"RARE_CANDY","qty":10,"slot":5}],"idioma":"pt"} */
