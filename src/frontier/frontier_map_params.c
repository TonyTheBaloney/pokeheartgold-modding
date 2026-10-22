#include "frontier/frontier_map_params.h"

#include "global.h"

#include "constants/sndseq.h"

#include "msgdata/msg.naix"

#include "bg_window.h"
#include "filesystem.h"
#include "gf_gfx_planes.h"
#include "heap.h"

// Per-map parameter table of the frontier maps (sFrontierMapParams, indexed by map id) and the map effect callbacks it
// points to.

typedef void (*FrontierMapEffectFunc)(FrontierMap *map, void **effect);

typedef struct FrontierMapParams {
    u32 bgMode;
    FrontierMapEffectFunc initEffect;
    FrontierMapEffectFunc exitEffect;
    u16 scriptId;
    u16 msgBank;
    u16 bgm;
    u16 bgSize;
    u16 narc;
    u16 bg3Screen;
    u16 bg3Char;
    u16 bg3Palette;
    u16 bg2Screen;
    u16 bg2Char;
    u16 bg2Palette;
    u8 scrollMode;
    u8 bg2Scrolls;
    u8 padding[4];
} FrontierMapParams;

static void FrontierMapEffect_InitAlloc(FrontierMap *map, void **effect);
static void FrontierMapEffect_ExitFree(FrontierMap *map, void **effect);
static void FrontierMapEffect_InitBgAnim(FrontierMap *map, void **effect);
static void FrontierMapEffect_ExitBgAnim(FrontierMap *map, void **effect);
static void FrontierMapEffect_InitArcadeNone(FrontierMap *map, void **effect);
static void FrontierMapEffect_ExitArcadeNone(FrontierMap *map, void **effect);
static void FrontierMapEffect_InitArcadeBlend(FrontierMap *map, void **effect);
static void FrontierMapEffect_ExitArcadeBlend(FrontierMap *map, void **effect);
static void FrontierMapEffect_InitFactoryBgPriority(FrontierMap *map, void **effect);
static void FrontierMapEffect_ExitFactoryBgPriority(FrontierMap *map, void **effect);
static void FrontierMapEffect_InitFactoryBlend(FrontierMap *map, void **effect);
static void FrontierMapEffect_ExitFactoryBlend(FrontierMap *map, void **effect);
static void FrontierMapEffect_InitTileBlink(FrontierMap *map, void **effect);
static void FrontierMapEffect_ExitTileBlink(FrontierMap *map, void **effect);
static void FrontierMapEffect_InitCastleBlend(FrontierMap *map, void **effect);
static void FrontierMapEffect_ExitCastleBlend(FrontierMap *map, void **effect);

static const FrontierMapParams sFrontierMapParams[] = {
    [0] = { .bgMode = GX_BGMODE_0, .initEffect = FrontierMapEffect_InitAlloc,             .exitEffect = FrontierMapEffect_ExitFree,              .scriptId = 4,  .msgBank = msg_0035,          .bgm = SEQ_GS_BATTLETOWER, .bgSize = GF_BG_SCR_SIZE_512x256, .narc = NARC_a_1_8_3, .bg3Screen = 1,   .bg3Char = 0,   .bg3Palette = 148, .bg2Screen = 3,                  .bg2Char = 0,                  .bg2Palette = 148,                .scrollMode = 0, .bg2Scrolls = 1 },
    [1] = { .bgMode = GX_BGMODE_0, .initEffect = NULL,                                    .exitEffect = NULL,                                    .scriptId = 0,  .msgBank = msg_0035,          .bgm = SEQ_GS_BATTLETOWER, .bgSize = GF_BG_SCR_SIZE_512x256, .narc = NARC_a_1_8_3, .bg3Screen = 2,   .bg3Char = 0,   .bg3Palette = 148, .bg2Screen = FRONTIER_MAP_NO_ID, .bg2Char = FRONTIER_MAP_NO_ID, .bg2Palette = FRONTIER_MAP_NO_ID, .scrollMode = 0, .bg2Scrolls = 1 },
    [2] = { .bgMode = GX_BGMODE_0, .initEffect = NULL,                                    .exitEffect = NULL,                                    .scriptId = 5,  .msgBank = msg_0036,          .bgm = SEQ_GS_BATTLETOWER, .bgSize = GF_BG_SCR_SIZE_512x256, .narc = NARC_a_1_8_3, .bg3Screen = 1,   .bg3Char = 0,   .bg3Palette = 148, .bg2Screen = FRONTIER_MAP_NO_ID, .bg2Char = FRONTIER_MAP_NO_ID, .bg2Palette = FRONTIER_MAP_NO_ID, .scrollMode = 0, .bg2Scrolls = 1 },
    [3] = { .bgMode = GX_BGMODE_5, .initEffect = FrontierMapEffect_InitFactoryBgPriority, .exitEffect = FrontierMapEffect_ExitFactoryBgPriority, .scriptId = 1,  .msgBank = msg_0195,          .bgm = SEQ_GS_BF_FACTORY,  .bgSize = GF_BG_SCR_SIZE_512x512, .narc = NARC_a_1_8_3, .bg3Screen = 2,   .bg3Char = 0,   .bg3Palette = 148, .bg2Screen = 3,                  .bg2Char = 0,                  .bg2Palette = 148,                .scrollMode = 1, .bg2Scrolls = 0 },
    [4] = { .bgMode = GX_BGMODE_5, .initEffect = FrontierMapEffect_InitFactoryBlend,      .exitEffect = FrontierMapEffect_ExitFactoryBlend,      .scriptId = 1,  .msgBank = msg_0195,          .bgm = SEQ_GS_BF_FACTORY,  .bgSize = GF_BG_SCR_SIZE_256x256, .narc = NARC_a_1_8_3, .bg3Screen = 1,   .bg3Char = 0,   .bg3Palette = 148, .bg2Screen = FRONTIER_MAP_NO_ID, .bg2Char = FRONTIER_MAP_NO_ID, .bg2Palette = FRONTIER_MAP_NO_ID, .scrollMode = 1, .bg2Scrolls = 1 },
    [5] = { .bgMode = GX_BGMODE_5, .initEffect = NULL,                                    .exitEffect = NULL,                                    .scriptId = 6,  .msgBank = msg_0096_D31R0201, .bgm = SEQ_GS_BATTLETOWER, .bgSize = GF_BG_SCR_SIZE_512x512, .narc = NARC_a_1_8_3, .bg3Screen = 54,  .bg3Char = 49,  .bg3Palette = 160, .bg2Screen = 55,                 .bg2Char = 49,                 .bg2Palette = 160,                .scrollMode = 1, .bg2Scrolls = 1 },
    [6] = { .bgMode = GX_BGMODE_5, .initEffect = NULL,                                    .exitEffect = NULL,                                    .scriptId = 7,  .msgBank = msg_0096_D31R0201, .bgm = SEQ_GS_BATTLETOWER, .bgSize = GF_BG_SCR_SIZE_512x512, .narc = NARC_a_1_8_3, .bg3Screen = 51,  .bg3Char = 49,  .bg3Palette = 160, .bg2Screen = 52,                 .bg2Char = 49,                 .bg2Palette = 160,                .scrollMode = 1, .bg2Scrolls = 1 },
    [7] = { .bgMode = GX_BGMODE_5, .initEffect = NULL,                                    .exitEffect = NULL,                                    .scriptId = 8,  .msgBank = msg_0097,          .bgm = SEQ_GS_BATTLETOWER, .bgSize = GF_BG_SCR_SIZE_256x256, .narc = NARC_a_1_8_3, .bg3Screen = 53,  .bg3Char = 49,  .bg3Palette = 160, .bg2Screen = FRONTIER_MAP_NO_ID, .bg2Char = FRONTIER_MAP_NO_ID, .bg2Palette = FRONTIER_MAP_NO_ID, .scrollMode = 1, .bg2Scrolls = 1 },
    [8] = { .bgMode = GX_BGMODE_5, .initEffect = NULL,                                    .exitEffect = NULL,                                    .scriptId = 9,  .msgBank = msg_0098,          .bgm = SEQ_GS_BATTLETOWER, .bgSize = GF_BG_SCR_SIZE_256x256, .narc = NARC_a_1_8_3, .bg3Screen = 50,  .bg3Char = 49,  .bg3Palette = 160, .bg2Screen = FRONTIER_MAP_NO_ID, .bg2Char = FRONTIER_MAP_NO_ID, .bg2Palette = FRONTIER_MAP_NO_ID, .scrollMode = 1, .bg2Scrolls = 1 },
    [9] = { .bgMode = GX_BGMODE_5, .initEffect = NULL,                                    .exitEffect = NULL,                                    .scriptId = 3,  .msgBank = msg_0441,          .bgm = SEQ_GS_BF_STAGE,    .bgSize = GF_BG_SCR_SIZE_256x256, .narc = NARC_a_1_8_3, .bg3Screen = 17,  .bg3Char = 16,  .bg3Palette = 151, .bg2Screen = FRONTIER_MAP_NO_ID, .bg2Char = FRONTIER_MAP_NO_ID, .bg2Palette = FRONTIER_MAP_NO_ID, .scrollMode = 1, .bg2Scrolls = 1 },
    [10] = { .bgMode = GX_BGMODE_5, .initEffect = FrontierMapEffect_InitBgAnim,            .exitEffect = FrontierMapEffect_ExitBgAnim,            .scriptId = 3,  .msgBank = msg_0441,          .bgm = SEQ_GS_BF_STAGE,    .bgSize = GF_BG_SCR_SIZE_512x512, .narc = NARC_a_1_8_3, .bg3Screen = 20,  .bg3Char = 14,  .bg3Palette = 150, .bg2Screen = 22,                 .bg2Char = 19,                 .bg2Palette = 152,                .scrollMode = 1, .bg2Scrolls = 1 },
    [11] = { .bgMode = GX_BGMODE_5, .initEffect = NULL,                                    .exitEffect = NULL,                                    .scriptId = 0,  .msgBank = msg_0032,          .bgm = SEQ_GS_BF_CASTLE,   .bgSize = GF_BG_SCR_SIZE_512x512, .narc = NARC_a_1_8_3, .bg3Screen = 26,  .bg3Char = 25,  .bg3Palette = 154, .bg2Screen = FRONTIER_MAP_NO_ID, .bg2Char = FRONTIER_MAP_NO_ID, .bg2Palette = FRONTIER_MAP_NO_ID, .scrollMode = 1, .bg2Scrolls = 1 },
    [12] = { .bgMode = GX_BGMODE_5, .initEffect = FrontierMapEffect_InitCastleBlend,       .exitEffect = FrontierMapEffect_ExitCastleBlend,       .scriptId = 0,  .msgBank = msg_0032,          .bgm = SEQ_GS_BF_CASTLE,   .bgSize = GF_BG_SCR_SIZE_256x256, .narc = NARC_a_1_8_3, .bg3Screen = 30,  .bg3Char = 29,  .bg3Palette = 159, .bg2Screen = 33,                 .bg2Char = 29,                 .bg2Palette = 159,                .scrollMode = 1, .bg2Scrolls = 1 },
    [13] = { .bgMode = GX_BGMODE_5, .initEffect = NULL,                                    .exitEffect = NULL,                                    .scriptId = 0,  .msgBank = msg_0032,          .bgm = SEQ_GS_BF_CASTLE,   .bgSize = GF_BG_SCR_SIZE_256x256, .narc = NARC_a_1_8_3, .bg3Screen = 28,  .bg3Char = 27,  .bg3Palette = 155, .bg2Screen = FRONTIER_MAP_NO_ID, .bg2Char = FRONTIER_MAP_NO_ID, .bg2Palette = FRONTIER_MAP_NO_ID, .scrollMode = 1, .bg2Scrolls = 1 },
    [14] = { .bgMode = GX_BGMODE_5, .initEffect = FrontierMapEffect_InitTileBlink,         .exitEffect = FrontierMapEffect_ExitTileBlink,         .scriptId = 10, .msgBank = msg_0018,          .bgm = SEQ_GS_BATTLETOWER, .bgSize = GF_BG_SCR_SIZE_256x256, .narc = NARC_a_1_8_3, .bg3Screen = 132, .bg3Char = 131, .bg3Palette = 191, .bg2Screen = FRONTIER_MAP_NO_ID, .bg2Char = FRONTIER_MAP_NO_ID, .bg2Palette = FRONTIER_MAP_NO_ID, .scrollMode = 1, .bg2Scrolls = 1 },
    [15] = { .bgMode = GX_BGMODE_5, .initEffect = FrontierMapEffect_InitArcadeNone,        .exitEffect = FrontierMapEffect_ExitArcadeNone,        .scriptId = 2,  .msgBank = msg_0426,          .bgm = SEQ_GS_BF_ROULETTE, .bgSize = GF_BG_SCR_SIZE_256x256, .narc = NARC_a_1_8_3, .bg3Screen = 59,  .bg3Char = 60,  .bg3Palette = 162, .bg2Screen = FRONTIER_MAP_NO_ID, .bg2Char = FRONTIER_MAP_NO_ID, .bg2Palette = FRONTIER_MAP_NO_ID, .scrollMode = 1, .bg2Scrolls = 1 },
    [16] = { .bgMode = GX_BGMODE_5, .initEffect = FrontierMapEffect_InitArcadeBlend,       .exitEffect = FrontierMapEffect_ExitArcadeBlend,       .scriptId = 2,  .msgBank = msg_0426,          .bgm = SEQ_GS_BF_ROULETTE, .bgSize = GF_BG_SCR_SIZE_512x512, .narc = NARC_a_1_8_3, .bg3Screen = 56,  .bg3Char = 58,  .bg3Palette = 161, .bg2Screen = 61,                 .bg2Char = 93,                 .bg2Palette = 188,                .scrollMode = 1, .bg2Scrolls = 1 },
};

u32 FrontierMap_GetParam(u32 mapId, enum FrontierMapParam param) {
    switch (param) {
    case MAP_PARAM_BG_MODE:
        return sFrontierMapParams[mapId].bgMode;
    case MAP_PARAM_SCRIPT_ID:
        return sFrontierMapParams[mapId].scriptId;
    case MAP_PARAM_MSG_BANK:
        return sFrontierMapParams[mapId].msgBank;
    case MAP_PARAM_BGM:
        return sFrontierMapParams[mapId].bgm;
    case MAP_PARAM_BG_SIZE:
        return sFrontierMapParams[mapId].bgSize;
    case MAP_PARAM_NARC:
        return sFrontierMapParams[mapId].narc;
    case MAP_PARAM_BG3_SCREEN:
        return sFrontierMapParams[mapId].bg3Screen;
    case MAP_PARAM_BG3_CHAR:
        return sFrontierMapParams[mapId].bg3Char;
    case MAP_PARAM_BG3_PALETTE:
        return sFrontierMapParams[mapId].bg3Palette;
    case MAP_PARAM_BG2_SCREEN:
        return sFrontierMapParams[mapId].bg2Screen;
    case MAP_PARAM_BG2_CHAR:
        return sFrontierMapParams[mapId].bg2Char;
    case MAP_PARAM_BG2_PALETTE:
        return sFrontierMapParams[mapId].bg2Palette;
    case MAP_PARAM_SCROLL_MODE:
        return sFrontierMapParams[mapId].scrollMode;
    case MAP_PARAM_BG2_SCROLLS:
        return sFrontierMapParams[mapId].bg2Scrolls;
    default:
        GF_ASSERT(FALSE);
        return 0;
    }
}

void FrontierMap_InitEffect(FrontierMap *map, void **effect, u32 mapId) {
    FrontierMapEffectFunc func = sFrontierMapParams[mapId].initEffect;
    if (func != NULL) {
        func(map, effect);
    }
}

void FrontierMap_ExitEffect(FrontierMap *map, void **effect, u32 mapId) {
    FrontierMapEffectFunc func = sFrontierMapParams[mapId].exitEffect;
    if (func != NULL) {
        func(map, effect);
    }
}

static void FrontierMapEffect_InitAlloc(FrontierMap *map, void **effect) {
    *effect = Heap_Alloc(HEAP_ID_101, 0x20);
}

static void FrontierMapEffect_ExitFree(FrontierMap *map, void **effect) {
    Heap_Free(*effect);
}

static void FrontierMapEffect_InitBgAnim(FrontierMap *map, void **effect) {
    *effect = FrontierMapBgAnim_Create(map->bgConfig, map->paletteData);
    SetBgPriority(GF_BG_LYR_MAIN_0, 1);
    SetBgPriority(GF_BG_LYR_MAIN_2, 2);
    SetBgPriority(GF_BG_LYR_MAIN_3, 3);
    GfGfx_EngineATogglePlanes(GX_PLANEMASK_BG2, GF_PLANE_TOGGLE_OFF);
}

static void FrontierMapEffect_ExitBgAnim(FrontierMap *map, void **effect) {
    FrontierMapBgAnim_Free(*effect);
}

static void FrontierMapEffect_InitArcadeNone(FrontierMap *map, void **effect) {
}

static void FrontierMapEffect_ExitArcadeNone(FrontierMap *map, void **effect) {
}

static void FrontierMapEffect_InitArcadeBlend(FrontierMap *map, void **effect) {
    SetBgPriority(GF_BG_LYR_MAIN_0, 1);
    SetBgPriority(GF_BG_LYR_MAIN_2, 2);
    SetBgPriority(GF_BG_LYR_MAIN_3, 3);
    G2_SetBlendAlpha(GX_BLEND_PLANEMASK_BG0, GX_BLEND_PLANEMASK_BG2 | GX_BLEND_PLANEMASK_BG3 | GX_BLEND_PLANEMASK_OBJ | GX_BLEND_PLANEMASK_BD, 20, 20);
    GfGfx_EngineATogglePlanes(GX_PLANEMASK_BG2, GF_PLANE_TOGGLE_OFF);
}

static void FrontierMapEffect_ExitArcadeBlend(FrontierMap *map, void **effect) {
}

static void FrontierMapEffect_InitFactoryBgPriority(FrontierMap *map, void **effect) {
    SetBgPriority(GF_BG_LYR_MAIN_2, 3);
    SetBgPriority(GF_BG_LYR_MAIN_3, 2);
}

static void FrontierMapEffect_ExitFactoryBgPriority(FrontierMap *map, void **effect) {
}

static void FrontierMapEffect_InitFactoryBlend(FrontierMap *map, void **effect) {
    G2_SetBlendAlpha(GX_BLEND_PLANEMASK_BG0, GX_BLEND_PLANEMASK_BG2 | GX_BLEND_PLANEMASK_BG3 | GX_BLEND_PLANEMASK_OBJ | GX_BLEND_PLANEMASK_BD, 20, 20);
}

static void FrontierMapEffect_ExitFactoryBlend(FrontierMap *map, void **effect) {
}

static void FrontierMapEffect_InitTileBlink(FrontierMap *map, void **effect) {
    *effect = FrontierMapTileBlink_Create(map->bgConfig);
}

static void FrontierMapEffect_ExitTileBlink(FrontierMap *map, void **effect) {
    FrontierMapTileBlink_Free(*effect);
}

static void FrontierMapEffect_InitCastleBlend(FrontierMap *map, void **effect) {
    SetBgPriority(GF_BG_LYR_MAIN_1, 0);
    SetBgPriority(GF_BG_LYR_MAIN_0, 2);
    SetBgPriority(GF_BG_LYR_MAIN_2, 2);
    SetBgPriority(GF_BG_LYR_MAIN_3, 3);
    G2_SetBlendAlpha(GX_BLEND_PLANEMASK_BG0, GX_BLEND_PLANEMASK_BG2 | GX_BLEND_PLANEMASK_BG3 | GX_BLEND_PLANEMASK_OBJ | GX_BLEND_PLANEMASK_BD, 20, 20);
}

static void FrontierMapEffect_ExitCastleBlend(FrontierMap *map, void **effect) {
}
