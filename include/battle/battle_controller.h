#ifndef POKEHEARTGOLD_BATTLE_CONTROLLER_H
#define POKEHEARTGOLD_BATTLE_CONTROLLER_H

#include "battle/battle.h"

typedef void (*ControllerFunction)(BattleSystem *, BattleContext *ctx);

// Command 22 (move animation); the restore-sprite (56) and substitute-sprite (62) commands
// send the same layout with only the per-battler sprite fields filled in.
typedef struct MoveAnimData {
    u8 command;
    u8 unk_01;
    u16 move;
    int damage;
    u16 power;
    u16 moveAnimVariant;
    u16 friendship;
    u16 isSubstitute : 1;
    u16 isTransformed : 1;
    u16 attackerActive : 1;
    u16 defenderActive : 1;
    u16 unk_0E_4 : 12;
    u32 fieldCondition;
    u16 attacker;
    u16 defender;
    u16 species[BATTLER_MAX];
    u8 gender[BATTLER_MAX];
    u8 shiny[BATTLER_MAX];
    u8 form[BATTLER_MAX];
    u32 personality[BATTLER_MAX];
    u32 moveEffectFlags[BATTLER_MAX];
    int isEffectAnim;
    int effectAnimId;
    int terrain;
} MoveAnimData;

// Packet queues. direction 0: input replies to the battle context (ctx->battleBuffer),
// 1: commands to a battler's OpponentData, 2: command-complete notices.
void BattleController_SendLocalMessage(BattleSystem *battleSystem, int direction, int battlerId, const u8 *data, u8 size);
BOOL BattleController_RecvMessage(BattleSystem *battleSystem, const u8 *data);
void BattleSystem_TryRecvMessage(BattleSystem *battleSystem, int direction);
void SendMessage(BattleSystem *battleSystem, int direction, int battlerId, const void *data, u8 size);
BOOL BattleController_RecvCommMessage(BattleSystem *battleSystem, u8 *data);
void BattleController_EmitClearCommand(BattleSystem *battleSystem, int battlerId, int command);

void BattleController_EmitSelectedCommand(BattleSystem *battleSystem, int battlerId, u32 input);
void BattleController_EmitSelectedMove(BattleSystem *battleSystem, int battlerId, u32 input);
void BattleController_EmitSelectedTarget(BattleSystem *battleSystem, int battlerId, u32 input);
// An item selection reply
typedef struct BattleItemInput {
    u16 item;
    u8 pocket;
    u8 target;
} BattleItemInput;

void BattleController_EmitSelectedBagItem(BattleSystem *battleSystem, int battlerId, BattleItemInput input);
void BattleController_EmitPartyMenuResult(BattleSystem *battleSystem, int battlerId, u32 input);
void BattleController_EmitAlertMessageAck(BattleSystem *battleSystem, int battlerId);
void BattleController_SetMoveAnimation(BattleSystem *battleSystem, BattleContext *ctx, MoveAnimData *animData, int isEffectAnim, int effectAnimId, int attacker, int defender, u16 move);

void BattleController_EmitSetupBattleUI(BattleSystem *battleSystem, BOOL battlerId);
void BattleController_EmitSetEncounter(BattleSystem *battleSystem, int battlerId);
void BattleController_EmitShowEncounter(BattleSystem *battleSystem, int battlerId);
void BattleController_EmitShowPokemon(BattleSystem *battleSystem, int battlerId, int ball, int breakOut);
void BattleController_EmitReturnPokemon(BattleSystem *battleSystem, BattleContext *ctx, int battlerId);
void BattleController_EmitDeletePokemon(BattleSystem *battleSystem, int battlerId);
void BattleController_EmitSetTrainerEncounter(BattleSystem *battleSystem, int battlerId);
void BattleController_EmitTrainerThrowBall(BattleSystem *battleSystem, int battlerId, u32 throwType);
void BattleController_EmitTrainerSlideOut(BattleSystem *battleSystem, int battlerId);
void BattleController_EmitTrainerSlideIn(BattleSystem *battleSystem, int battlerId, u32 index);
void BattleController_EmitSlideInBackground(BattleSystem *battleSystem, int battlerId);
void BattleController_EmitSlideHealthBoxIn(BattleSystem *battleSystem, BattleContext *ctx, int battlerId, u32 delay);
void BattleController_EmitSlideHealthBoxOut(BattleSystem *battleSystem, int battlerId);
void BattleController_EmitShowPartyMenu(BattleSystem *battleSystem, BattleContext *ctx, int battlerId, u32 mode, u32 canSwitch, u32 reservedMon);
void BattleController_EmitShowYesNoMenu(BattleSystem *battleSystem, BattleContext *ctx, int battlerId, int msgId, int mode, int value, int msgParam);
void BattleController_EmitPrintLinkWaitMessage(BattleSystem *battleSystem, int battlerId);
void BattleController_EmitPrintAttackMessage(BattleSystem *battleSystem, BattleContext *ctx);
void BattleController_EmitPrintMessage(BattleSystem *battleSystem, BattleContext *ctx, BattleMessage *msg);
void BattleController_EmitPlayMoveAnimation(BattleSystem *battleSystem, BattleContext *ctx, u16 move);
void BattleController_SetMoveAnimationAttackerToDefender(BattleSystem *battleSystem, BattleContext *ctx, u16 move, int attacker, int target);
void BattleController_EmitFlickerBattlerSprite(BattleSystem *battleSystem, int battlerId, int moveStatusFlag);
void BattleController_EmitUpdateHPGauge(BattleSystem *battleSystem, BattleContext *ctx, int side);
void BattleController_EmitPlayFaintingSequence(BattleSystem *battleSystem, BattleContext *ctx, int battlerId);
void BattleController_EmitPlaySound(BattleSystem *battleSystem, BattleContext *ctx, u32 sndSeqNo, int battlerId);
void BattleController_EmitFadeOut(BattleSystem *battleSystem, BattleContext *ctx);
void BattleController_EmitToggleVanishMessage(BattleSystem *battleSystem, int battlerId, int vanish);
void BattleController_EmitSetStatusIcon(BattleSystem *battleSystem, int battlerId, int status);
void BattleController_EmitPrintTrainerMessage(BattleSystem *battleSystem, int battlerId, int msg);
void BattleController_EmitPlayStatusEffect(BattleSystem *battleSystem, BattleContext *ctx, int battlerId, int status);
void BattleController_EmitPlayStatusEffectAttackerToDefender(BattleSystem *battleSystem, BattleContext *ctx, int battlerIdA, int battlerIdB, int status);
void BattleController_EmitPrintReturnMessage(BattleSystem *battleSystem, BattleContext *ctx, int battlerId, int selectedMonIndex);
void BattleController_EmitPrintSendOutMessage(BattleSystem *battleSystem, BattleContext *ctx, int battlerId, int selectedMonIndex);
void BattleController_EmitPrintEncounterMessage(BattleSystem *battleSystem, BattleContext *ctx, int battlerId);
void BattleController_EmitPrintLeadMonMessage(BattleSystem *battleSystem, BattleContext *ctx, int battlerId);
void BattleController_EmitUpdatePartyMon(BattleSystem *battleSystem, BattleContext *ctx, int battlerId);
void BattleController_EmitRefreshPartyStatus(BattleSystem *battleSystem, BattleContext *ctx, int battlerId, int moveNo);
void BattleController_EmitSetBattleResults(BattleSystem *battleSystem);
void BattleController_EmitPlayMosaicAnimation(BattleSystem *battleSystem, int battlerId, int mosaic, int delay);
void BattleController_EmitChangeForm(BattleSystem *battleSystem, int battlerId);
void BattleController_EmitUpdateBackground(BattleSystem *battleSystem, int battlerId);
void BattleController_EmitShowInitialPartyGauge(BattleSystem *battleSystem, int battlerId);
void BattleController_EmitHideInitialPartyGauge(BattleSystem *battleSystem, int battlerId);
void BattleController_EmitShowPartyGauge(BattleSystem *battleSystem, int battlerId);
void BattleController_EmitHidePartyGauge(BattleSystem *battleSystem, int battlerId);
void BattleController_EmitLoadPartyGaugeGraphics(BattleSystem *battleSystem);
void BattleController_EmitFreePartyGaugeGraphics(BattleSystem *battleSystem);
void BattleController_EmitIncrementGameStat(BattleSystem *battleSystem, int battlerId, int flag, int id);
void BattleController_EmitRestoreSprite(BattleSystem *battleSystem, BattleContext *ctx, int battlerId);
void BattleController_EmitSpriteToOAM(BattleSystem *battleSystem, int battlerId);
void BattleController_EmitOAMToSprite(BattleSystem *battleSystem, int battlerId);
void BattleController_EmitPrintResultMessage(BattleSystem *battleSystem);
void BattleController_EmitPrintEscapeMessage(BattleSystem *battleSystem, BattleContext *ctx);
void BattleController_EmitPrintForefitMessage(BattleSystem *battleSystem);
void BattleController_EmitRefreshSprite(BattleSystem *battleSystem, BattleContext *ctx, int battlerId);
void BattleController_EmitPlayMoveHitSoundEffect(BattleSystem *battleSystem, BattleContext *ctx, int battlerId);
void BattleController_EmitPlayMusic(BattleSystem *battleSystem, int battlerId, int song);
void BattleSystem_ReloadMonData(BattleSystem *battleSystem, BattleContext *ctx, int battlerId, int monIndex);

void BattleController_EmitScreenFade(BattleSystem *battleSystem, BattleContext *ctx, u8 mode);
void BattleController_EmitSetCommandSelectionMenu(BattleSystem *battleSystem, BattleContext *ctx, int battlerId, int partySlot);
void BattleController_EmitOpenCaptureBall(BattleSystem *battleSystem, s32 battlerId, s32 ball);
void BattleController_EmitSetAlertMessage(BattleSystem *battleSystem, int battlerId, BattleMessage msg);
void BattleController_EmitStopGaugeAnimation(BattleSystem *battleSystem, int battlerId);
void BattleController_EmitShowMoveSelectMenu(BattleSystem *battleSystem, BattleContext *ctx, int battlerId);
void BattleCommand_EmitShowTargetSelectMenu(BattleSystem *battleSystem, BattleContext *ctx, int moveRange, int battlerId);
void BattleController_EmitShowBagMenu(BattleSystem *battleSystem, BattleContext *ctx, int battlerId);
void BattleController_EmitClearTouchScreen(BattleSystem *battleSystem, int battlerId);
void BattleController_EmitUpdateExpGauge(BattleSystem *battleSystem, BattleContext *ctx, int battlerId, u32 prevExp);
void BattleController_EmitPlayLevelUpAnimation(BattleSystem *battleSystem, int battlerId);
void BattleController_EmitRefreshHPGauge(BattleSystem *battleSystem, BattleContext *ctx, int battlerId);
void BattleController_EmitForgetMove(BattleSystem *battleSystem, int battlerId, u32 move, int slot);
void BattleController_EmitClearMessageBox(BattleSystem *battleSystem);

#endif
