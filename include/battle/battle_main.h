#ifndef POKEHEARTGOLD_BATTLE_BATTLE_MAIN_H
#define POKEHEARTGOLD_BATTLE_BATTLE_MAIN_H

#include "battle/battle.h"
#include "battle/battle_022378C0.h"
#include "battle/battle_controller_opponent.h"

#include "bg_window.h"
#include "gf_3d_vramman.h"
#include "gf_gfx_planes.h"
#include "overlay_manager.h"
#include "poke_overlay.h"
#include "sys_task_api.h"

// The battle overlay's main module.
// (Kept apart from battle_022378C0.h: more declarations there renumber function-local statics in its includers.)

FS_EXTERN_OVERLAY(OVY_7);
FS_EXTERN_OVERLAY(OVY_10);

typedef struct BattleBgTemplateSet {
    BgTemplate templates[3];
} BattleBgTemplateSet;

extern const BattleBgTemplateSet gBattleReinitBgTemplates;
extern const BattleBgTemplateSet gBattleBgTemplates;

void BattleSystem_InitTerrainsAndBalls(BattleSystem *battleSystem);
void Battle_VBlankCallback(void *data);

// Defined in other modules that have no header declaring them yet.
void BattleSystem_TryRecvMessage(BattleSystem *battleSystem, int direction);
void BgConfig_InitBattleMenuBackgrounds(BgConfig *bgConfig);
void LoadUserFrameGfx2WithFill(BgConfig *bgConfig, u8 bgId, u16 baseTile, u8 color, u8 type, enum HeapID heapId);
u32 GetUserFrameGfx2TilesMember(u32 frame);
u32 GetUserFrameGfx2PaletteMember(u32 frame);

#endif // POKEHEARTGOLD_BATTLE_BATTLE_MAIN_H
