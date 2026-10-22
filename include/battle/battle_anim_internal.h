#ifndef POKEHEARTGOLD_BATTLE_BATTLE_ANIM_INTERNAL_H
#define POKEHEARTGOLD_BATTLE_BATTLE_ANIM_INTERNAL_H

#include "battle/battle.h"
#include "battle/battle_anim_util.h"

#include "bg_window.h"
#include "filesystem.h"
#include "overlay_07.h"
#include "palette.h"
#include "pokepic.h"
#include "sav_chatot.h"
#include "spl.h"
#include "sprite_system.h"

typedef void (*BattleAnimRunner)(BattleAnimSystem *system);
typedef void (*BattleAnimScriptCmd)(BattleAnimSystem *system);

typedef struct BattleAnimSoundTaskData BattleAnimSoundTaskData;
typedef struct BattleAnimBrightnessFlashWork BattleAnimBrightnessFlashWork;
typedef struct BattleAnimBgSwitchWork BattleAnimBgSwitchWork;
typedef struct BattleAnimIndexedBytes BattleAnimIndexedBytes;

// Per-move data (a copy of the battle's move animation packet) and the battlers' state
typedef struct BattleAnimContext {
    u8 command;
    u8 unk_01;
    u16 move;
    int damage;
    u16 power;
    u16 friendship;
    u32 fieldCondition;
    u16 moveAnimVariant;
    u16 terrain;
    u16 attacker;
    u16 defender;
    int currentParticleSystem;
    SPLEmitter *particleSystems[16];
    SPLEmitter *emitters[16];
    u8 unk_9C[0x10];
    SpriteSystem *spriteSystem;
    MonPicData *picData[4];
    u8 battlerTypes[4];
    Pokepic *pokepics[4];
    u32 battleType;
    u16 species[4];
    u8 genders[4];
    u8 shiny[4];
    u8 forms[4];
    u32 personalities[4];
    u32 moveEffectFlags[4];
    SOUND_CHATOT *chatotCry;
    u8 *battleBgTiles;
    u16 *battleBgPalette;
    int isTransformed : 1;
    int attackerActive : 1;
    int defenderActive : 1;
    int unk_118_3 : 29;
} BattleAnimContext;

// BeginLoop/EndLoop state
typedef struct BattleAnimScriptLoop {
    u32 *start;
    u8 counter;
    u8 count;
    BOOL active;
} BattleAnimScriptLoop;

// Draw task entry of the battler sprite copies (StartBattlerSpriteDraw)
typedef struct BattleAnimBattlerSpriteDraw {
    BattleAnimSystem *system;
    SpriteManager *manager;
    ManagedSprite *sprite;
    BOOL active;
} BattleAnimBattlerSpriteDraw;

// Keeps a sprite or BG2 on a battler's pokepic
typedef struct BattleAnimFollowWork {
    void *target; // ManagedSprite or BgConfig
    u8 counter;
    u8 interval;
    Pokepic *pokepic;
    SysTask *task;
} BattleAnimFollowWork;

// Common head of the background effect task data registered in BattleAnimSystem.bgEffects
typedef struct BattleAnimBgEffect {
    u8 unk_00[0x18];
    BOOL stop;
    int kind;
} BattleAnimBgEffect;

struct BattleAnimSystem {
    enum HeapID heapId;
    NarcId scriptNarc;
    BOOL isContest;
    BOOL initialized;
    BOOL active;
    void *scriptData;
    u32 *scriptPtr;
    u32 *returnStack[3];
    BattleAnimScriptLoop loops[3];
    BattleAnimBattlerSpriteDraw battlerSpriteDraws[2];
    u8 particlePerspective[16]; // per particle system
    u8 particleFlipY[16];
    u8 unk_8C;
    u8 delay;
    u16 taskCount;
    u16 soundTaskCount;
    u32 args[10];
    BattleAnimRunner runner;
    BattleAnimContext *context;
    BgConfig *bgConfig;
    PaletteData *paletteData;
    SpriteManager *spriteManagers[4];
    ManagedSprite *sprites[10];
    ManagedSpriteTemplate spriteTemplate;
    SpriteManager *battlerSpriteManager;
    ManagedSprite *battlerSprites[5];
    BOOL battlerSpriteActive[5];
    BattleAnimFollowWork *followWorks[6]; // [5]: the battler copy on BG2
    u8 bgSwitchState;
    u8 seWaitTimer;
    u8 endPhase;
    u8 unk_17F;
    BattleAnimBgEffect *bgEffects[4];
    BattleAnimBgGraphics battleBg;
    u32 battleBgPaletteMask;
    u8 bgPriorities[4];
    NARC *narcs[6];
};

// Battler picture data handed to the pic swap helpers (BattleAnimSystem_BuildBattlerPicParams)
typedef struct BattleAnimBattlerPicParams {
    int battler;
    int sourceBattler;
    MonPicData *picData[4];
    Pokepic *pokepics[4];
    u16 species[4];
    u8 genders[4];
    u8 shiny[4];
    u8 forms[4];
    u32 personalities[4];
    u8 battlerTypes[4];
} BattleAnimBattlerPicParams;

BOOL BattleAnimSystem_IsContest(BattleAnimSystem *system);
SysTask *BattleAnimSystem_CreateTask(BattleAnimSystem *system, SysTaskFunc func, void *data, u32 priority);
SysTask *BattleAnimSystem_CreateTaskDefaultPriority(BattleAnimSystem *system, SysTaskFunc func, void *data);
SysTask *BattleAnimSystem_CreateSoundTask(BattleAnimSystem *system, SysTaskFunc func, void *data, u32 priority);
void BattleAnimSystem_DestroyTask(BattleAnimSystem *system, SysTask *task);
void BattleAnimSystem_DestroySoundTask(BattleAnimSystem *system, SysTask *task);
u16 BattleAnimSystem_GetAttacker(BattleAnimSystem *system);
u16 BattleAnimSystem_GetDefender(BattleAnimSystem *system);
SPLEmitter *BattleAnimSystem_GetCurrentParticleSystem(BattleAnimSystem *system);
SPLEmitter *BattleAnimSystem_GetParticleSystem(BattleAnimSystem *system, int index);
SPLEmitter *BattleAnimSystem_GetEmitter(BattleAnimSystem *system, int index);
BgConfig *BattleAnimSystem_GetBgConfig(BattleAnimSystem *system);
u32 BattleAnimSystem_GetArg(BattleAnimSystem *system, int index);
ManagedSprite *BattleAnimSystem_GetSprite(BattleAnimSystem *system, int index);
ManagedSprite *BattleAnimSystem_GetBattlerSprite(BattleAnimSystem *system, int index);
SpriteManager *BattleAnimSystem_GetBattlerSpriteManager(BattleAnimSystem *system);
SpriteManager *BattleAnimSystem_GetFirstSpriteManager(BattleAnimSystem *system);
SpriteSystem *BattleAnimSystem_GetSpriteSystem(BattleAnimSystem *system);
void BattleAnimSystem_InitBlend(void);
u32 BattleAnimSystem_GetMoveParam(BattleAnimSystem *system, u32 param);
void BattleAnimSystem_BuildBattlerPicParams(BattleAnimSystem *system, BattleAnimBattlerPicParams *params, u32 mode);
u32 BattleAnimSystem_GetBattleBgPaletteMask(BattleAnimSystem *system);
void BattleAnimBackground_LoadBattleBgToLayerDefault(BattleAnimSystem *system, GFBgLayer layer);
void BattleAnimBackground_ResetLayer(BattleAnimSystem *system, GFBgLayer layer);
BOOL BattleAnimSystem_ReadScriptArgs(BattleAnimSystem *system, u32 *out, int count);
void BattleAnimSystem_GetSpriteTemplate(ManagedSpriteTemplate *template, BattleAnimSystem *system);
u8 BattleAnimSystem_GetBattlerType(BattleAnimSystem *system, int battler);
u8 BattleAnimSystem_GetBattlerGender(BattleAnimSystem *system, int battler);
u16 BattleAnimSystem_GetBattlerSpecies(BattleAnimSystem *system, int battler);
u8 BattleAnimSystem_GetBattlerForm(BattleAnimSystem *system, int battler);
u32 BattleAnimSystem_GetBattlerPersonality(BattleAnimSystem *system, int battler);
Pokepic *BattleAnimSystem_GetBattlerPokepic(BattleAnimSystem *system, int battler);
PaletteData *BattleAnimSystem_GetPaletteData(BattleAnimSystem *system);
int BattleAnimSystem_GetBattlerPaletteId(BattleAnimSystem *system, int battler);
int BattleAnimSystem_GetBattlerNarcId(BattleAnimSystem *system, int battler);
int BattleAnimSystem_GetBattlerHeight(BattleAnimSystem *system, int battler);
BOOL BattleAnimSystem_IsDoubleBattle(BattleAnimSystem *system);
BOOL BattleAnimSystem_IsBattlerSemiInvulnerable(BattleAnimSystem *system, int battler);
int BattleAnimSystem_GetBasePriority(BattleAnimSystem *system);
u32 BattleAnimSystem_GetBgLayer(BattleAnimSystem *system, int index);
u32 BattleAnimSystem_GetBgMaskLayer(BattleAnimSystem *system, int index);
int BattleAnimSystem_GetBgPriority(BattleAnimSystem *system, int kind);
BOOL BattleAnimSystem_ShouldFlipSide(BattleAnimSystem *system, int side);
u32 BattleAnimSystem_GetBackgroundFile(u32 bgId, int file);
u8 BattleAnimIndexedBytes_GetCurrentValue(BattleAnimIndexedBytes *data);
void BattleAnimEmitterCb_None(SPLEmitter *emitter);
SPLEmitter *BattleAnimSystem_NewParticleSystem(enum HeapID heapId, int resId, BOOL loadNow);
SPLEmitter *BattleAnimSystem_NewParticleSystemFromNarc(enum HeapID heapId, NarcId narcId, int resId, BOOL loadNow);
SPLEmitter *BattleAnimSystem_NewParticleSystemFromOpenNarc(NARC *narc, enum HeapID heapId, int member, BOOL loadNow);
void BattleAnimSystem_FreeParticleSystem(SPLEmitter *particleSystem);
int BattleAnimSystem_GetSideSign(BattleAnimSystem *system, int battlerA, int battlerB);
void BattleAnimEmitterCb_Dummy(void);

s16 BattleAnimSystem_GetBattlerScreenCoord(BattleAnimSystem *system, int battler, u32 coord);
void BattleAnimUtil_LoadSubstituteIntoPic(BattleAnimBattlerPicParams *params, enum HeapID heapId);
void BattleAnimUtil_LoadMonIntoPicSameFacing(BattleAnimBattlerPicParams *params, enum HeapID heapId);
void BattleAnimUtil_LoadMonIntoPicOppositeFacing(BattleAnimBattlerPicParams *params, enum HeapID heapId);
void BattleAnimUtil_RestorePic(BattleAnimBattlerPicParams *params, enum HeapID heapId);

// Sound effect panning
void SetSeqTrackPan(u16 seqNo, u16 trackMask, int pan);
void SetAllSEPan(int pan);

// Particle system camera
void ParticleSystem_GetCameraUp(SPLEmitter *particleSystem, VecFx32 *out);
void ParticleSystem_SetCameraUp(SPLEmitter *particleSystem, VecFx32 *up);

#endif // POKEHEARTGOLD_BATTLE_BATTLE_ANIM_INTERNAL_H
