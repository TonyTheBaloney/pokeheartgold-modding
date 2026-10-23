#include "constants/decorations.h"
#include "constants/items.h"
#include "constants/seals.h"

#include "pokeathlon/pokeathlon_save.h"

#include "field_system.h"
#include "mart.h"
#include "overlay_03.h"
#include "pokedex.h"
#include "save_vars_flags.h"
#include "scrcmd.h"

struct BadgeMartItems {
    u16 item_id;
    u16 tier;
};

// [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-21
// Status: MATCHING (rename only)
// Regular Poke Mart stock; an item is sold once the badge tier reaches .tier
const struct BadgeMartItems sBadgeMartItems[] = {
    { ITEM_POKE_BALL,    1 },
    { ITEM_GREAT_BALL,   3 },
    { ITEM_ULTRA_BALL,   4 },
    { ITEM_POTION,       1 },
    { ITEM_SUPER_POTION, 2 },
    { ITEM_HYPER_POTION, 4 },
    { ITEM_MAX_POTION,   5 },
    { ITEM_FULL_RESTORE, 6 },
    { ITEM_REVIVE,       3 },
    { ITEM_ANTIDOTE,     1 },
    { ITEM_PARLYZ_HEAL,  1 },
    { ITEM_AWAKENING,    2 },
    { ITEM_BURN_HEAL,    2 },
    { ITEM_ICE_HEAL,     2 },
    { ITEM_FULL_HEAL,    4 },
    { ITEM_ESCAPE_ROPE,  2 },
    { ITEM_REPEL,        2 },
    { ITEM_SUPER_REPEL,  3 },
    { ITEM_MAX_REPEL,    4 },
};

// [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-21
// Partially AI-edited: Mart_Init constants
BOOL ScrCmd_MartBuy(ScriptContext *ctx) {
    u16 unused;
    u8 badge_count;
    u8 i;
    u8 tier;
    u8 nitems;
    u16 items[64];

    unused = ScriptGetVar(ctx);

    nitems = 0;
    badge_count = 0;
    for (i = 0; i < 16; i++) {
        if (PlayerProfile_TestBadgeFlag(Save_PlayerData_GetProfile(ctx->fieldSystem->saveData), i) == TRUE) {
            badge_count++;
        }
    }
    switch (badge_count) {
    case 0:
        tier = 1;
        break;
    case 1:
    case 2:
        tier = 2;
        break;
    case 3:
    case 4:
        tier = 3;
        break;
    case 5:
    case 6:
        tier = 4;
        break;
    case 7:
        tier = 5;
        break;
    case 8:
        tier = 6;
        break;
    default:
        tier = 6;
        break;
    }
    for (i = 0; i < NELEMS(sBadgeMartItems); i++) {
        if (tier >= sBadgeMartItems[i].tier) {
            items[nitems] = sBadgeMartItems[i].item_id;
            nitems++;
        }
    }
    items[nitems] = 0xFFFF;
    Mart_Init(ctx->taskman, ctx->fieldSystem, items, MART_TYPE_NORMAL, MART_BUY, 0, 0);
    return TRUE;
}

// [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-21
// Partially AI-edited: Mart_Init constants
BOOL ScrCmd_MartSell(ScriptContext *ctx) {
    u16 dummy[1];

    dummy[0] = 0xFFFF;
    Mart_Init(ctx->taskman, ctx->fieldSystem, dummy, MART_TYPE_NORMAL, MART_SELL, 0, 0);
    return TRUE;
}

// [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-21
// Status: MATCHING (rename only)
// Per-location stock for std_special_mart (index = VAR_SPECIAL_x8004).
// Names come from the map scripts that pass each index. Shared lists:
// GoldenrodDeptStore4F is also used by the Safari Zone Gate, BlackthornPokemart
// by the Frontier Access mart, VermilionPokemart by the Safari Zone Gate.
// MahoganySouvenirShop_Rockets is sold while the Rockets run the shop.
const u16 sSpecialMartItems_CherrygrovePokemart[] = { ITEM_AIR_MAIL, ITEM_HEAL_BALL, 0xFFFF };
const u16 sSpecialMartItems_VioletPokemart[] = { ITEM_TUNNEL_MAIL, ITEM_HEAL_BALL, ITEM_NET_BALL, 0xFFFF };
const u16 sSpecialMartItems_AzaleaPokemart[] = { ITEM_BLOOM_MAIL, ITEM_HEAL_BALL, ITEM_NET_BALL, 0xFFFF };
const u16 sSpecialMartItems_GoldenrodDeptStore2F_Medicine[] = { ITEM_POTION, ITEM_SUPER_POTION, ITEM_HYPER_POTION, ITEM_MAX_POTION, ITEM_REVIVE, ITEM_ANTIDOTE, ITEM_PARLYZ_HEAL, ITEM_BURN_HEAL, ITEM_ICE_HEAL, ITEM_AWAKENING, ITEM_FULL_HEAL, 0xFFFF };
const u16 sSpecialMartItems_GoldenrodDeptStore2F_Supplies[] = { ITEM_POKE_BALL, ITEM_GREAT_BALL, ITEM_ULTRA_BALL, ITEM_ESCAPE_ROPE, ITEM_POKE_DOLL, ITEM_REPEL, ITEM_SUPER_REPEL, ITEM_MAX_REPEL, ITEM_GRASS_MAIL, ITEM_FLAME_MAIL, ITEM_BUBBLE_MAIL, ITEM_SPACE_MAIL, 0xFFFF };
const u16 sSpecialMartItems_GoldenrodDeptStore3F[] = { ITEM_X_SPEED, ITEM_X_ATTACK, ITEM_X_DEFENSE, ITEM_GUARD_SPEC_, ITEM_DIRE_HIT, ITEM_X_ACCURACY, ITEM_X_SPECIAL, ITEM_X_SP__DEF, 0xFFFF };
const u16 sSpecialMartItems_GoldenrodDeptStore4F[] = { ITEM_PROTEIN, ITEM_IRON, ITEM_CALCIUM, ITEM_ZINC, ITEM_CARBOS, ITEM_HP_UP, 0xFFFF };
const u16 sSpecialMartItems_GoldenrodDeptStore5F[] = { ITEM_TM70, ITEM_TM17, ITEM_TM54, ITEM_TM83, ITEM_TM16, ITEM_TM33, ITEM_TM22, ITEM_TM52, ITEM_TM38, ITEM_TM25, ITEM_TM14, ITEM_TM15, 0xFFFF };
const u16 sSpecialMartItems_GoldenrodTunnelHerbShop[] = { ITEM_HEAL_POWDER, ITEM_ENERGYPOWDER, ITEM_ENERGY_ROOT, ITEM_REVIVAL_HERB, 0xFFFF };
const u16 sSpecialMartItems_EcruteakPokemart[] = { ITEM_AIR_MAIL, ITEM_HEAL_BALL, ITEM_NET_BALL, 0xFFFF };
const u16 sSpecialMartItems_OlivinePokemart[] = { ITEM_HEART_MAIL, ITEM_HEAL_BALL, ITEM_NET_BALL, 0xFFFF };
const u16 sSpecialMartItems_CianwoodPharmacy[] = { ITEM_POTION, ITEM_SUPER_POTION, ITEM_HYPER_POTION, ITEM_FULL_HEAL, ITEM_REVIVE, 0xFFFF };
const u16 sSpecialMartItems_BlackthornPokemart[] = { ITEM_AIR_MAIL, ITEM_NET_BALL, ITEM_DUSK_BALL, 0xFFFF };
const u16 sSpecialMartItems_PokemonLeague[] = { ITEM_ULTRA_BALL, ITEM_MAX_REPEL, ITEM_HYPER_POTION, ITEM_MAX_POTION, ITEM_FULL_RESTORE, ITEM_REVIVE, ITEM_FULL_HEAL, 0xFFFF };
const u16 sSpecialMartItems_VermilionPokemart[] = { ITEM_AIR_MAIL, ITEM_NEST_BALL, ITEM_DUSK_BALL, ITEM_QUICK_BALL, 0xFFFF };
const u16 sSpecialMartItems_SaffronPokemart[] = { ITEM_AIR_MAIL, ITEM_DUSK_BALL, ITEM_QUICK_BALL, 0xFFFF };
const u16 sSpecialMartItems_LavenderPokemart[] = { ITEM_SNOW_MAIL, ITEM_DUSK_BALL, ITEM_QUICK_BALL, 0xFFFF };
const u16 sSpecialMartItems_CeruleanPokemart[] = { ITEM_AIR_MAIL, ITEM_QUICK_BALL, 0xFFFF };
const u16 sSpecialMartItems_CeladonDeptStore2F_Medicine[] = { ITEM_POTION, ITEM_SUPER_POTION, ITEM_HYPER_POTION, ITEM_MAX_POTION, ITEM_REVIVE, ITEM_ANTIDOTE, ITEM_PARLYZ_HEAL, ITEM_BURN_HEAL, ITEM_ICE_HEAL, ITEM_AWAKENING, ITEM_FULL_HEAL, 0xFFFF };
const u16 sSpecialMartItems_CeladonDeptStore2F_Supplies[] = { ITEM_POKE_BALL, ITEM_GREAT_BALL, ITEM_ULTRA_BALL, ITEM_ESCAPE_ROPE, ITEM_POKE_DOLL, ITEM_REPEL, ITEM_SUPER_REPEL, ITEM_MAX_REPEL, ITEM_GRASS_MAIL, ITEM_FLAME_MAIL, ITEM_BUBBLE_MAIL, ITEM_SPACE_MAIL, 0xFFFF };
const u16 sSpecialMartItems_CeladonDeptStore3F[] = { ITEM_TM21, ITEM_TM27, ITEM_TM87, ITEM_TM78, ITEM_TM12, ITEM_TM41, ITEM_TM20, ITEM_TM28, ITEM_TM76, ITEM_TM55, ITEM_TM72, ITEM_TM79, 0xFFFF };
const u16 sSpecialMartItems_CeladonDeptStore4F[] = { ITEM_AIR_MAIL, ITEM_TUNNEL_MAIL, ITEM_BLOOM_MAIL, 0xFFFF };
const u16 sSpecialMartItems_CeladonDeptStore5F_BattleItems[] = { ITEM_X_SPEED, ITEM_X_ATTACK, ITEM_X_DEFENSE, ITEM_GUARD_SPEC_, ITEM_DIRE_HIT, ITEM_X_ACCURACY, ITEM_X_SPECIAL, ITEM_X_SP__DEF, 0xFFFF };
const u16 sSpecialMartItems_CeladonDeptStore5F_Vitamins[] = { ITEM_PROTEIN, ITEM_IRON, ITEM_CALCIUM, ITEM_ZINC, ITEM_CARBOS, ITEM_HP_UP, 0xFFFF };
const u16 sSpecialMartItems_FuchsiaPokemart[] = { ITEM_STEEL_MAIL, ITEM_DUSK_BALL, ITEM_QUICK_BALL, 0xFFFF };
const u16 sSpecialMartItems_PewterPokemart[] = { ITEM_STEEL_MAIL, ITEM_NEST_BALL, ITEM_QUICK_BALL, 0xFFFF };
const u16 sSpecialMartItems_ViridianPokemart[] = { ITEM_STEEL_MAIL, ITEM_NET_BALL, ITEM_HEAL_BALL, 0xFFFF };
const u16 sSpecialMartItems_MtMoonSquareShop[] = { ITEM_POKE_DOLL, ITEM_FRESH_WATER, ITEM_SODA_POP, ITEM_LEMONADE, ITEM_REPEL, ITEM_HEART_MAIL, 0xFFFF };
const u16 sSpecialMartItems_MahoganySouvenirShop_Rockets[] = { ITEM_TINYMUSHROOM, ITEM_POKE_BALL, ITEM_POTION, 0xFFFF };
const u16 sSpecialMartItems_MahoganySouvenirShop[] = { ITEM_GREAT_BALL, ITEM_SUPER_POTION, ITEM_HYPER_POTION, ITEM_ANTIDOTE, ITEM_PARLYZ_HEAL, ITEM_SUPER_REPEL, ITEM_REVIVE, ITEM_AIR_MAIL, 0xFFFF };

const u16 *sSpecialMartItems[] = {
    sSpecialMartItems_CherrygrovePokemart,
    sSpecialMartItems_VioletPokemart,
    sSpecialMartItems_AzaleaPokemart,
    sSpecialMartItems_GoldenrodDeptStore2F_Medicine,
    sSpecialMartItems_GoldenrodDeptStore2F_Supplies,
    sSpecialMartItems_GoldenrodDeptStore3F,
    sSpecialMartItems_GoldenrodDeptStore4F,
    sSpecialMartItems_GoldenrodDeptStore5F,
    sSpecialMartItems_GoldenrodTunnelHerbShop,
    sSpecialMartItems_EcruteakPokemart,
    sSpecialMartItems_OlivinePokemart,
    sSpecialMartItems_CianwoodPharmacy,
    sSpecialMartItems_BlackthornPokemart,
    sSpecialMartItems_PokemonLeague,
    sSpecialMartItems_VermilionPokemart,
    sSpecialMartItems_SaffronPokemart,
    sSpecialMartItems_LavenderPokemart,
    sSpecialMartItems_CeruleanPokemart,
    sSpecialMartItems_CeladonDeptStore2F_Medicine,
    sSpecialMartItems_CeladonDeptStore2F_Supplies,
    sSpecialMartItems_CeladonDeptStore3F,
    sSpecialMartItems_CeladonDeptStore4F,
    sSpecialMartItems_CeladonDeptStore5F_BattleItems,
    sSpecialMartItems_CeladonDeptStore5F_Vitamins,
    sSpecialMartItems_FuchsiaPokemart,
    sSpecialMartItems_PewterPokemart,
    sSpecialMartItems_ViridianPokemart,
    sSpecialMartItems_MtMoonSquareShop,
    sSpecialMartItems_MahoganySouvenirShop_Rockets,
    sSpecialMartItems_MahoganySouvenirShop,
};

// [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-21
// Partially AI-edited: Mart_Init constants
BOOL ScrCmd_SpecialMartBuy(ScriptContext *ctx) {
    u16 which;

    which = ScriptGetVar(ctx);
    Mart_Init(ctx->taskman, ctx->fieldSystem, sSpecialMartItems[which], MART_TYPE_NORMAL, MART_BUY, 0, NULL);
    return TRUE;
}

// [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-21
// Status: MATCHING (rename only)
// Sinnoh leftover, unused in HGSS
const u16 sDecorationMartItems_Furniture[] = {
    DECORATION_YELLOW_CUSHION, DECORATION_CUPBOARD, DECORATION_TV, DECORATION_REFRIGERATOR, DECORATION_PRETTY_SINK, 0xFFFF
};
const u16 sDecorationMartItems_Dolls[] = {
    DECORATION_MUNCHLAX_DOLL, DECORATION_BONSLY_DOLL, DECORATION_MIME_JR__DOLL, DECORATION_MANTYKE_DOLL, DECORATION_BUIZEL_DOLL, DECORATION_CHATOT_DOLL, 0xFFFF
};

const u16 *sDecorationMartItems[] = {
    sDecorationMartItems_Furniture,
    sDecorationMartItems_Dolls,
};

// [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-21
// Partially AI-edited: Mart_Init constants
BOOL ScrCmd_DecorationMart(ScriptContext *ctx) {
    u16 which;

    which = ScriptGetVar(ctx);
    Mart_Init(ctx->taskman, ctx->fieldSystem, sDecorationMartItems[which], MART_TYPE_DECOR, MART_BUY, which <= 1 ? 1 : 0, NULL);
    return TRUE;
}

// [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-21
// Status: MATCHING (rename only)
// No HGSS script calls SealMart; the seven lists may be per weekday (unverified).
const u16 sSealMartItems_0[] = { SEAL_HEART_A, SEAL_STAR_B, SEAL_FIRE_A, SEAL_SONG_A, SEAL_LINE_C, SEAL_ELE_B, SEAL_PARTY_D, 0xFFFF };
const u16 sSealMartItems_1[] = { SEAL_HEART_B, SEAL_STAR_C, SEAL_FIRE_B, SEAL_FLORA_A, SEAL_SONG_B, SEAL_LINE_D, SEAL_ELE_C, 0xFFFF };
const u16 sSealMartItems_2[] = { SEAL_HEART_C, SEAL_STAR_D, SEAL_FIRE_C, SEAL_FLORA_B, SEAL_SONG_C, SEAL_SMOKE_A, SEAL_ELE_D, 0xFFFF };
const u16 sSealMartItems_3[] = { SEAL_HEART_D, SEAL_FOAMY_A, SEAL_FIRE_D, SEAL_FLORA_C, SEAL_SONG_D, SEAL_STAR_E, SEAL_SMOKE_B, 0xFFFF };
const u16 sSealMartItems_4[] = { SEAL_FOAMY_B, SEAL_PARTY_A, SEAL_FLORA_D, SEAL_SONG_E, SEAL_HEART_E, SEAL_STAR_F, SEAL_SMOKE_C, 0xFFFF };
const u16 sSealMartItems_5[] = { SEAL_FOAMY_C, SEAL_PARTY_B, SEAL_FLORA_E, SEAL_SONG_F, SEAL_HEART_F, SEAL_LINE_A, SEAL_SMOKE_D, 0xFFFF };
const u16 sSealMartItems_6[] = { SEAL_STAR_A, SEAL_SONG_G, SEAL_FOAMY_D, SEAL_FLORA_F, SEAL_LINE_B, SEAL_ELE_A, SEAL_PARTY_C, 0xFFFF };

const u16 *sSealMartItems[] = {
    sSealMartItems_0,
    sSealMartItems_1,
    sSealMartItems_2,
    sSealMartItems_3,
    sSealMartItems_4,
    sSealMartItems_5,
    sSealMartItems_6,
};

// [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-21
// Partially AI-edited: Mart_Init constants
BOOL ScrCmd_SealMart(ScriptContext *ctx) {
    u16 which;

    which = ScriptGetVar(ctx);
    Mart_Init(ctx->taskman, ctx->fieldSystem, sSealMartItems[which], MART_TYPE_SEAL, MART_BUY, 0, NULL);
    return TRUE;
}

// [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-21
// Status: MATCHING (names taken from pret upstream)
// Despite the name, these are the full stock for MART_TYPE_POKEATHLON_DAILY,
// indexed by RTC weekday (0 = Sunday), +7 once the National Dex is obtained.
const struct MartItem sPokeathlonPrizeExchangePriceOverrides_Monday[] = {
    { ITEM_RED_APRICORN, 200  },
    { ITEM_BLU_APRICORN, 200  },
    { ITEM_GRN_APRICORN, 200  },
    { ITEM_MOOMOO_MILK,  100  },
    { ITEM_MOON_STONE,   3000 },
    { ITEM_RARE_CANDY,   2000 },
    { 0xFFFF,            0    },
};
const struct MartItem sPokeathlonPrizeExchangePriceOverrides_Tuesday[] = {
    { ITEM_YLW_APRICORN, 200  },
    { ITEM_PNK_APRICORN, 200  },
    { ITEM_WHT_APRICORN, 200  },
    { ITEM_MOOMOO_MILK,  100  },
    { ITEM_FIRE_STONE,   2500 },
    { ITEM_PP_UP,        1000 },
    { 0xFFFF,            0    },
};
const struct MartItem sPokeathlonPrizeExchangePriceOverrides_Wednesday[] = {
    { ITEM_BLU_APRICORN, 200  },
    { ITEM_PNK_APRICORN, 200  },
    { ITEM_BLK_APRICORN, 200  },
    { ITEM_MOOMOO_MILK,  100  },
    { ITEM_WATER_STONE,  2500 },
    { ITEM_HEART_SCALE,  1000 },
    { 0xFFFF,            0    },
};
const struct MartItem sPokeathlonPrizeExchangePriceOverrides_Thursday[] = {
    { ITEM_YLW_APRICORN, 200  },
    { ITEM_PNK_APRICORN, 200  },
    { ITEM_WHT_APRICORN, 200  },
    { ITEM_MOOMOO_MILK,  100  },
    { ITEM_THUNDERSTONE, 2500 },
    { ITEM_PP_UP,        1000 },
    { 0xFFFF,            0    },
};
const struct MartItem sPokeathlonPrizeExchangePriceOverrides_Friday[] = {
    { ITEM_RED_APRICORN, 200  },
    { ITEM_YLW_APRICORN, 200  },
    { ITEM_GRN_APRICORN, 200  },
    { ITEM_MOOMOO_MILK,  100  },
    { ITEM_METAL_COAT,   2500 },
    { ITEM_NUGGET,       500  },
    { 0xFFFF,            0    },
};
const struct MartItem sPokeathlonPrizeExchangePriceOverrides_Saturday[] = {
    { ITEM_GRN_APRICORN, 200  },
    { ITEM_WHT_APRICORN, 200  },
    { ITEM_BLK_APRICORN, 200  },
    { ITEM_MOOMOO_MILK,  100  },
    { ITEM_LEAF_STONE,   2500 },
    { ITEM_RARE_CANDY,   2000 },
    { 0xFFFF,            0    },
};
const struct MartItem sPokeathlonPrizeExchangePriceOverrides_Sunday[] = {
    { ITEM_RED_APRICORN, 200  },
    { ITEM_BLU_APRICORN, 200  },
    { ITEM_BLK_APRICORN, 200  },
    { ITEM_MOOMOO_MILK,  100  },
    { ITEM_KINGS_ROCK,   3000 },
    { ITEM_HEART_SCALE,  1000 },
    { 0xFFFF,            0    },
};
const struct MartItem sPokeathlonPrizeExchangePriceOverrides_Sunday_NatDex[] = {
    { ITEM_RED_APRICORN, 200  },
    { ITEM_BLU_APRICORN, 200  },
    { ITEM_BLK_APRICORN, 200  },
    { ITEM_MOOMOO_MILK,  100  },
    { ITEM_KINGS_ROCK,   3000 },
    { ITEM_HEART_SCALE,  1000 },
    { ITEM_FULL_RESTORE, 500  },
    { ITEM_NUGGET,       500  },
    { ITEM_SUN_STONE,    3000 },
    { ITEM_FIRE_STONE,   2500 },
    { ITEM_SHINY_STONE,  3000 },
    { ITEM_DAWN_STONE,   3000 },
    { 0xFFFF,            0    },
};
const struct MartItem sPokeathlonPrizeExchangePriceOverrides_Monday_NatDex[] = {
    { ITEM_RED_APRICORN, 200  },
    { ITEM_BLU_APRICORN, 200  },
    { ITEM_GRN_APRICORN, 200  },
    { ITEM_MOOMOO_MILK,  100  },
    { ITEM_MOON_STONE,   3000 },
    { ITEM_RARE_CANDY,   2000 },
    { ITEM_FULL_RESTORE, 500  },
    { ITEM_KINGS_ROCK,   3000 },
    { ITEM_SUN_STONE,    3000 },
    { ITEM_WATER_STONE,  2500 },
    { ITEM_SHINY_STONE,  3000 },
    { ITEM_DUSK_STONE,   3000 },
    { 0xFFFF,            0    },
};
const struct MartItem sPokeathlonPrizeExchangePriceOverrides_Tuesday_NatDex[] = {
    { ITEM_YLW_APRICORN, 200  },
    { ITEM_PNK_APRICORN, 200  },
    { ITEM_WHT_APRICORN, 200  },
    { ITEM_MOOMOO_MILK,  100  },
    { ITEM_FIRE_STONE,   2500 },
    { ITEM_PP_UP,        1000 },
    { ITEM_FULL_RESTORE, 500  },
    { ITEM_METAL_COAT,   2500 },
    { ITEM_WATER_STONE,  2500 },
    { ITEM_LEAF_STONE,   2500 },
    { ITEM_DUSK_STONE,   3000 },
    { ITEM_DAWN_STONE,   3000 },
    { 0xFFFF,            0    },
};
const struct MartItem sPokeathlonPrizeExchangePriceOverrides_Wednesday_NatDex[] = {
    { ITEM_BLU_APRICORN, 200  },
    { ITEM_PNK_APRICORN, 200  },
    { ITEM_BLK_APRICORN, 200  },
    { ITEM_MOOMOO_MILK,  100  },
    { ITEM_WATER_STONE,  2500 },
    { ITEM_HEART_SCALE,  1000 },
    { ITEM_FULL_RESTORE, 500  },
    { ITEM_DRAGON_SCALE, 2500 },
    { ITEM_THUNDERSTONE, 2500 },
    { ITEM_MOON_STONE,   3000 },
    { ITEM_SHINY_STONE,  3000 },
    { ITEM_DAWN_STONE,   3000 },
    { 0xFFFF,            0    },
};
const struct MartItem sPokeathlonPrizeExchangePriceOverrides_Thursday_NatDex[] = {
    { ITEM_YLW_APRICORN, 200  },
    { ITEM_PNK_APRICORN, 200  },
    { ITEM_WHT_APRICORN, 200  },
    { ITEM_MOOMOO_MILK,  100  },
    { ITEM_THUNDERSTONE, 2500 },
    { ITEM_PP_UP,        1000 },
    { ITEM_FULL_RESTORE, 500  },
    { ITEM_KINGS_ROCK,   3000 },
    { ITEM_FIRE_STONE,   2500 },
    { ITEM_LEAF_STONE,   2500 },
    { ITEM_SHINY_STONE,  3000 },
    { ITEM_DUSK_STONE,   3000 },
    { 0xFFFF,            0    },
};
const struct MartItem sPokeathlonPrizeExchangePriceOverrides_Friday_NatDex[] = {
    { ITEM_RED_APRICORN, 200  },
    { ITEM_YLW_APRICORN, 200  },
    { ITEM_GRN_APRICORN, 200  },
    { ITEM_MOOMOO_MILK,  100  },
    { ITEM_METAL_COAT,   2500 },
    { ITEM_NUGGET,       500  },
    { ITEM_FULL_RESTORE, 500  },
    { ITEM_DRAGON_SCALE, 2500 },
    { ITEM_WATER_STONE,  2500 },
    { ITEM_SUN_STONE,    3000 },
    { ITEM_DUSK_STONE,   3000 },
    { ITEM_DAWN_STONE,   3000 },
    { 0xFFFF,            0    },
};
const struct MartItem sPokeathlonPrizeExchangePriceOverrides_Saturday_NatDex[] = {
    { ITEM_GRN_APRICORN, 200  },
    { ITEM_WHT_APRICORN, 200  },
    { ITEM_BLK_APRICORN, 200  },
    { ITEM_MOOMOO_MILK,  100  },
    { ITEM_LEAF_STONE,   2500 },
    { ITEM_RARE_CANDY,   2000 },
    { ITEM_FULL_RESTORE, 500  },
    { ITEM_METAL_COAT,   2500 },
    { ITEM_THUNDERSTONE, 2500 },
    { ITEM_SHINY_STONE,  3000 },
    { ITEM_DUSK_STONE,   3000 },
    { ITEM_DAWN_STONE,   3000 },
    { 0xFFFF,            0    },
};

const struct MartItem *sPokeathlonPrizeExchangePriceOverrides[] = {
    sPokeathlonPrizeExchangePriceOverrides_Sunday,
    sPokeathlonPrizeExchangePriceOverrides_Monday,
    sPokeathlonPrizeExchangePriceOverrides_Tuesday,
    sPokeathlonPrizeExchangePriceOverrides_Wednesday,
    sPokeathlonPrizeExchangePriceOverrides_Thursday,
    sPokeathlonPrizeExchangePriceOverrides_Friday,
    sPokeathlonPrizeExchangePriceOverrides_Saturday,
    sPokeathlonPrizeExchangePriceOverrides_Sunday_NatDex,
    sPokeathlonPrizeExchangePriceOverrides_Monday_NatDex,
    sPokeathlonPrizeExchangePriceOverrides_Tuesday_NatDex,
    sPokeathlonPrizeExchangePriceOverrides_Wednesday_NatDex,
    sPokeathlonPrizeExchangePriceOverrides_Thursday_NatDex,
    sPokeathlonPrizeExchangePriceOverrides_Friday_NatDex,
    sPokeathlonPrizeExchangePriceOverrides_Saturday_NatDex,
};

// [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-21
// Partially AI-edited: Mart_Init constants. The item list argument is ignored for
// this mart type, so indexing past sDecorationMartItems is harmless (original behavior).
BOOL ScrCmd_PokeathlonDailyMart(ScriptContext *ctx) {
    SaveVarsFlags *flagsys;
    RTCDate date;

    flagsys = Save_VarsFlags_Get(ctx->fieldSystem->saveData);
    GF_RTC_CopyDate(&date);

    // UB: Possibly illegal access to sDecorationMartItems between Tuesday and Saturday, inclusive
    if (Pokedex_GetNatDexFlag(Save_Pokedex_Get(ctx->fieldSystem->saveData))) {
        Mart_Init(ctx->taskman, ctx->fieldSystem, sDecorationMartItems[date.week], MART_TYPE_POKEATHLON_DAILY, MART_BUY, 0, sPokeathlonPrizeExchangePriceOverrides[date.week + 7]);
    } else {
        Mart_Init(ctx->taskman, ctx->fieldSystem, sDecorationMartItems[date.week], MART_TYPE_POKEATHLON_DAILY, MART_BUY, 0, sPokeathlonPrizeExchangePriceOverrides[date.week]);
    }
    return TRUE;
}

// [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-21
// Status: MATCHING (rename only)
// Data card stock, indexed by (first card not yet bought) / 6
const struct MartItem sPokeathlonDataCardPrices_01To06[] = {
    { ITEM_DATA_CARD_01, 500  },
    { ITEM_DATA_CARD_02, 500  },
    { ITEM_DATA_CARD_03, 1000 },
    { ITEM_DATA_CARD_04, 1000 },
    { ITEM_DATA_CARD_05, 500  },
    { ITEM_DATA_CARD_06, 500  },
    { 0xFFFF,            0    },
};
const struct MartItem sPokeathlonDataCardPrices_07To12[] = {
    { ITEM_DATA_CARD_07, 1000 },
    { ITEM_DATA_CARD_08, 1000 },
    { ITEM_DATA_CARD_09, 1000 },
    { ITEM_DATA_CARD_10, 1000 },
    { ITEM_DATA_CARD_11, 1000 },
    { ITEM_DATA_CARD_12, 1000 },
    { 0xFFFF,            0    },
};
const struct MartItem sPokeathlonDataCardPrices_13To18[] = {
    { ITEM_DATA_CARD_13, 1500 },
    { ITEM_DATA_CARD_14, 1500 },
    { ITEM_DATA_CARD_15, 1500 },
    { ITEM_DATA_CARD_16, 1000 },
    { ITEM_DATA_CARD_17, 1000 },
    { ITEM_DATA_CARD_18, 1000 },
    { 0xFFFF,            0    },
};
const struct MartItem sPokeathlonDataCardPrices_19To24[] = {
    { ITEM_DATA_CARD_19, 500  },
    { ITEM_DATA_CARD_20, 500  },
    { ITEM_DATA_CARD_21, 2000 },
    { ITEM_DATA_CARD_22, 2000 },
    { ITEM_DATA_CARD_23, 1000 },
    { ITEM_DATA_CARD_24, 1000 },
    { 0xFFFF,            0    },
};
const struct MartItem sPokeathlonDataCardPrices_25To27[] = {
    { ITEM_DATA_CARD_25, 2000 },
    { ITEM_DATA_CARD_26, 3000 },
    { ITEM_DATA_CARD_27, 9999 },
    { 0xFFFF,            0    },
};

const struct MartItem *sPokeathlonDataCardPrices[] = {
    sPokeathlonDataCardPrices_01To06,
    sPokeathlonDataCardPrices_07To12,
    sPokeathlonDataCardPrices_13To18,
    sPokeathlonDataCardPrices_19To24,
    sPokeathlonDataCardPrices_25To27,
};

// [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-21
// Partially AI-edited: Mart_Init constants
BOOL ScrCmd_PokeathlonDataCardMart(ScriptContext *ctx) {
    PokeathlonSave *pokeathlon;
    int i;

    pokeathlon = Save_Pokeathlon_Get(ctx->fieldSystem->saveData);
    for (i = 0; i < 27; i++) {
        if (!PokeathlonSave_IsDataCardBought(pokeathlon, i)) {
            break;
        }
    }
    Mart_Init(ctx->taskman, ctx->fieldSystem, sDecorationMartItems[0], MART_TYPE_DATA_CARDS, MART_BUY, 0, sPokeathlonDataCardPrices[i / 6]);
    return TRUE;
}

BOOL ScrCmd_CheckPokeathlonDailyMartHasStock(ScriptContext *ctx) {
    u16 *retPtr;
    PokeathlonSave *pokeathlon;
    SaveVarsFlags *varsFlags;
    int numItems;
    int numBought;
    RTCDate date;
    const struct MartItem *items;
    int i;

    retPtr = ScriptGetVarPointer(ctx);
    pokeathlon = Save_Pokeathlon_Get(ctx->fieldSystem->saveData);
    numItems = 0;
    numBought = 0;
    varsFlags = Save_VarsFlags_Get(ctx->fieldSystem->saveData);
    GF_RTC_CopyDate(&date);
    if (Pokedex_GetNatDexFlag(Save_Pokedex_Get(ctx->fieldSystem->saveData))) {
        items = sPokeathlonPrizeExchangePriceOverrides[date.week + 7];
    } else {
        items = sPokeathlonPrizeExchangePriceOverrides[date.week];
    }
    for (i = 0; i < 12; i++) {
        if (items[i].item_id == 0xFFFF) {
            break;
        }
        numItems++;
    }
    for (i = 0; i < 12; i++) {
        if (PokeathlonSave_IsDailyItemBought(pokeathlon, i)) {
            numBought++;
        }
    }
    if (numItems <= numBought) {
        *retPtr = FALSE;
    } else {
        *retPtr = TRUE;
    }
    return FALSE;
}

BOOL ScrCmd_CountPokeathlonDataCardsBought(ScriptContext *ctx) {
    u16 *ret_ptr;
    int i;
    PokeathlonSave *pokeathlon;

    ret_ptr = ScriptGetVarPointer(ctx);
    pokeathlon = Save_Pokeathlon_Get(ctx->fieldSystem->saveData);
    for (i = 0; i < 27; i++) {
        if (!PokeathlonSave_IsDataCardBought(pokeathlon, i)) {
            break;
        }
    }
    *ret_ptr = i;
    return FALSE;
}
