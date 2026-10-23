#ifndef POKEHEARTGOLD_BATTLE_LINK_COMM_H
#define POKEHEARTGOLD_BATTLE_LINK_COMM_H
#include "global.h"

#include "battle/battle_setup.h"
#include "battle/battle_system.h"

#include "battle_record.h"
#include "bg_window.h"
#include "communication_command.h"
#include "communication_core.h"
#include "heap.h"
#include "link_synchronization.h"
#include "palette.h"
#include "render_window.h"
#include "string_util.h"
#include "sys_task.h"

// Work of the link data exchange stage (BSTATE_LINK_INIT/MAIN): the battle setup data the linked players exchange
// before the battle, one command at a time through the buffer.
typedef struct BattleLinkWork {
    BattleSetup *setup;
    BgConfig *bgConfig;
    Window *window;
    PaletteData *palette;
    SavePalPad *friends[4];
    union {
        u32 words[1024];
        Trainer trainer;
        SOUND_CHATOT chatot;
        SavePalPad palPad;
    } buffer;
    u8 received;
    u8 state;
    u16 timer;
    WaitingIcon *waitingIcon;
} BattleLinkWork;
typedef struct BattleLinkTask {
    BattleSystem *battle;
    u8 state;
} BattleLinkTask;
typedef struct BattleLinkHeader {
    u8 command, battler;
    u16 size;
} BattleLinkHeader;
extern const u32 gBattleLinkCommands[];
int Comm_GetSendBufferFreeSpace(void);
BOOL Comm_SendCommandNoCopy(int command, void *data, int size);
BOOL BattleController_RecvCommMessage(BattleSystem *battle, u8 *data);
void BattleLink_Start(BattleSystem *battle);
void BattleLink_RegisterSetupCommands(BattleLinkWork *work);
void BattleLink_QueueSendData(BattleSystem *battle, int command, int battler, u8 *data, u8 size);
BOOL BattleLink_SendAiFlags(BattleLinkWork *work, u32 value, ...);
BOOL BattleLink_PrepareProfile(BattleLinkWork *work);
BOOL BattleLink_SendProfile(BattleLinkWork *work);
BOOL BattleLink_PrepareTrainer(BattleLinkWork *work);
BOOL BattleLink_SendTrainer(BattleLinkWork *work);
BOOL BattleLink_PrepareParty(BattleLinkWork *work);
BOOL BattleLink_SendParty(BattleLinkWork *work);
BOOL BattleLink_PrepareChatot(BattleLinkWork *work);
BOOL BattleLink_SendChatot(BattleLinkWork *work);
BOOL BattleLink_PreparePalPad(BattleLinkWork *work);
BOOL BattleLink_SendPalPad(BattleLinkWork *work);
BOOL BattleLink_PreparePartnerTrainer(BattleLinkWork *work, int index);
BOOL BattleLink_SendPartnerTrainer(BattleLinkWork *work, int index, int command);
BOOL BattleLink_PreparePartnerParty(BattleLinkWork *work, int index);
BOOL BattleLink_SendPartnerParty(BattleLinkWork *work, int index, int command);

#endif
