#include "battle_link_comm.h"

static void BattleLink_RecvData(int sender, int size, u8 *data, BattleSystem *battle);
static void BattleLink_RecvAiFlags(int sender, int unused, u32 *data, BattleLinkWork *work);
static void BattleLink_RecvProfile(int sender, int unused, void *data, BattleLinkWork *work);
static void BattleLink_RecvTrainer(int sender, int unused, void *data, BattleLinkWork *work);
static void BattleLink_RecvParty(int sender, int unused, void *data, BattleLinkWork *work);
static void BattleLink_RecvChatot(int sender, int unused, void *data, BattleLinkWork *work);
static void BattleLink_RecvPartnerTrainer(int sender, int unused, void *data, BattleLinkWork *work);
static void BattleLink_RecvPartnerParty(int sender, int unused, void *data, BattleLinkWork *work);
static void BattleLink_SendTask(SysTask *task, void *ptr);
static void BattleLink_RecvTask(SysTask *task, void *ptr);
static void BattleLink_RecvEnd(int sender, int unused, void *data, BattleSystem *battle);
static void BattleLink_BuildPalPad(PlayerProfile *profile, SavePalPad *friends, SavePalPad *out);
static void BattleLink_RecvPalPad(int sender, int unused, SavePalPad *data, BattleLinkWork *work);
static u32 BattleLink_GetPalPadSize(void);

enum BattleLinkTaskState {
    BATTLE_LINK_STATE_RUN,
    BATTLE_LINK_STATE_END = 255,
};

void BattleLink_Start(BattleSystem *battle) {
    BattleLinkTask *send, *recv;
    if (BattleSystem_GetBattleSpecial(battle) & BATTLE_SPECIAL_RECORDING) {
        return;
    }
    send = Heap_Alloc(HEAP_ID_BATTLE, sizeof(BattleLinkTask));
    recv = Heap_Alloc(HEAP_ID_BATTLE, sizeof(BattleLinkTask));
    Comm_RegisterCommandTable(gBattleLinkCommands, 12, battle);
    send->battle = battle;
    send->state = BATTLE_LINK_STATE_RUN;
    recv->battle = battle;
    recv->state = BATTLE_LINK_STATE_RUN;
    BattleSystem_SetLinkSendStatePtr(battle, &send->state);
    BattleSystem_SetLinkRecvStatePtr(battle, &recv->state);
    SysTask_CreateOnMainQueue(BattleLink_SendTask, send, 0);
    SysTask_CreateOnMainQueue(BattleLink_RecvTask, recv, 0);
}

void BattleLink_RegisterSetupCommands(BattleLinkWork *work) {
    Comm_RegisterCommandTable(gBattleLinkCommands, 12, work);
}

static u32 BattleLink_GetAiFlagsSize(void) {
    return 4;
}

static u32 BattleLink_GetProfileSize(void) {
    return PlayerProfile_sizeof();
}

static u32 BattleLink_GetPartySize(void) {
    return PartyCore_sizeof();
}

static u32 BattleLink_GetChatotSize(void) {
    return 1000;
}

static u32 BattleLink_GetTrainerSize(void) {
    return sizeof(Trainer);
}

static void *BattleLink_GetProfileRecvBuffer(int sender, BattleLinkWork *work) {
    BattleSetup *setup = work->setup;
    if (setup->battleType & BATTLE_TYPE_FRONTIER) {
        return setup->profile[sender * 2];
    }
    return setup->profile[sender];
}

static void *BattleLink_GetTrainerRecvBuffer(int sender, BattleLinkWork *work) {
    BattleSetup *setup = work->setup;
    if (setup->battleType & BATTLE_TYPE_FRONTIER) {
        return &setup->trainer[sender * 2];
    }
    return &setup->trainer[sender];
}

static void *BattleLink_GetPartyRecvBuffer(int sender, BattleLinkWork *work) {
    BattleSetup *setup = work->setup;
    if (setup->battleType & BATTLE_TYPE_FRONTIER) {
        return setup->party[sender * 2];
    }
    return setup->party[sender];
}

static void *BattleLink_GetChatotRecvBuffer(int sender, BattleLinkWork *work) {
    BattleSetup *setup = work->setup;
    if (setup->battleType & BATTLE_TYPE_FRONTIER) {
        return setup->chatot[sender * 2];
    }
    return setup->chatot[sender];
}

static void *BattleLink_GetTrainer1RecvBuffer(int sender, BattleLinkWork *work) {
    return &work->setup->trainer[1];
}

static void *BattleLink_GetTrainer3RecvBuffer(int sender, BattleLinkWork *work) {
    return &work->setup->trainer[3];
}

static void *BattleLink_GetParty1RecvBuffer(int sender, BattleLinkWork *work) {
    return work->setup->party[1];
}

static void *BattleLink_GetParty3RecvBuffer(int sender, BattleLinkWork *work) {
    return work->setup->party[3];
}

static void *BattleLink_GetPalPadRecvBuffer(int sender, BattleLinkWork *work) {
    return work->friends[sender];
}

const u32 gBattleLinkCommands[] = {
    (u32)BattleLink_RecvEnd,
    (u32)CommCmd_GetSizeVariable,
    0,
    (u32)BattleLink_RecvData,
    (u32)CommCmd_GetSizeVariable,
    0,
    (u32)BattleLink_RecvAiFlags,
    (u32)BattleLink_GetAiFlagsSize,
    0,
    (u32)BattleLink_RecvProfile,
    (u32)BattleLink_GetProfileSize,
    (u32)BattleLink_GetProfileRecvBuffer,
    (u32)BattleLink_RecvTrainer,
    (u32)BattleLink_GetTrainerSize,
    (u32)BattleLink_GetTrainerRecvBuffer,
    (u32)BattleLink_RecvParty,
    (u32)BattleLink_GetPartySize,
    (u32)BattleLink_GetPartyRecvBuffer,
    (u32)BattleLink_RecvChatot,
    (u32)BattleLink_GetChatotSize,
    (u32)BattleLink_GetChatotRecvBuffer,
    (u32)BattleLink_RecvPartnerTrainer,
    (u32)BattleLink_GetTrainerSize,
    (u32)BattleLink_GetTrainer1RecvBuffer,
    (u32)BattleLink_RecvPartnerTrainer,
    (u32)BattleLink_GetTrainerSize,
    (u32)BattleLink_GetTrainer3RecvBuffer,
    (u32)BattleLink_RecvPartnerParty,
    (u32)BattleLink_GetPartySize,
    (u32)BattleLink_GetParty1RecvBuffer,
    (u32)BattleLink_RecvPartnerParty,
    (u32)BattleLink_GetPartySize,
    (u32)BattleLink_GetParty3RecvBuffer,
    (u32)BattleLink_RecvPalPad,
    (u32)BattleLink_GetPalPadSize,
    (u32)BattleLink_GetPalPadRecvBuffer,
};

void BattleLink_QueueSendData(BattleSystem *battle, int command, int battler, u8 *data, u8 size) {
    u8 *header;
    u8 *buffer;
    u16 *write;
    u16 *end;
    int i;

    header = Heap_Alloc(HEAP_ID_BATTLE, 4);
    buffer = BattleSystem_GetServerMessage(battle);
    write = BattleSystem_GetServerWriteIndex(battle);
    end = BattleSystem_GetServerEndIndex(battle);
    if ((u32)(*write + 5 + size) > 0x1000) {
        *end = *write;
        *write = 0;
    }
    header[0] = command;
    header[1] = battler;
    *(u16 *)&header[2] = size;
    for (i = 0; (u32)i < 4; i++) {
        buffer[*write] = header[i];
        (*write)++;
    }
    for (i = 0; i < size; i++) {
        buffer[*write] = data[i];
        (*write)++;
    }
    Heap_Free(header);
}

static void BattleLink_RecvData(int sender, int size, u8 *data, BattleSystem *battle) {
    int i;
    u8 *buffer = BattleSystem_GetClientMessage(battle);
    u16 *write = BattleSystem_GetClientWriteIndex(battle);
    u16 *end = BattleSystem_GetClientEndIndex(battle);
    if (*write + size + 1 > 4096) {
        *end = *write;
        *write = 0;
    }
    for (i = 0; i < size; i++) {
        buffer[*write] = data[i];
        (*write)++;
    }
}

BOOL BattleLink_SendAiFlags(BattleLinkWork *work, u32 value, ...) {
    if (Comm_GetSendBufferFreeSpace() != 264) {
        return FALSE;
    }
    if (LinkSync_IsSynced(51) == 0) {
        return FALSE;
    }
    return Comm_SendCommand(24, &value, 4);
}

static void BattleLink_RecvAiFlags(int sender, int unused, u32 *data, BattleLinkWork *work) {
    work->setup->aiFlags[sender] = *data;
    BattleRecord_SetAiFlags(sender, work->setup->aiFlags[sender]);
    work->received++;
}

BOOL BattleLink_PrepareProfile(BattleLinkWork *work) {
    if (Comm_GetSendBufferFreeSpace() != 264) {
        return FALSE;
    }
    PlayerProfile_Copy(work->setup->profile[0], (PlayerProfile *)&work->buffer);
    return TRUE;
}

BOOL BattleLink_SendProfile(BattleLinkWork *work) {
    if (Comm_GetSendBufferFreeSpace() != 264) {
        return FALSE;
    }
    if (LinkSync_IsSynced(52) == 0) {
        return FALSE;
    }
    return Comm_SendCommandNoCopy(25, &work->buffer, PlayerProfile_sizeof());
}

static void BattleLink_RecvProfile(int sender, int unused, void *data, BattleLinkWork *work) {
    work->received++;
}

BOOL BattleLink_PrepareTrainer(BattleLinkWork *work) {
    if (Comm_GetSendBufferFreeSpace() != 264) {
        return FALSE;
    }
    work->buffer.trainer = work->setup->trainer[0];
    return TRUE;
}

BOOL BattleLink_SendTrainer(BattleLinkWork *work) {
    if (Comm_GetSendBufferFreeSpace() != 264) {
        return FALSE;
    }
    if (LinkSync_IsSynced(53) == 0) {
        return FALSE;
    }
    return Comm_SendCommandNoCopy(26, &work->buffer, 52);
}

static void BattleLink_RecvTrainer(int sender, int unused, void *data, BattleLinkWork *work) {
    work->received++;
}

BOOL BattleLink_PrepareParty(BattleLinkWork *work) {
    if (Comm_GetSendBufferFreeSpace() != 264) {
        return FALSE;
    }
    Party_Copy(work->setup->party[0], (Party *)&work->buffer);
    return TRUE;
}

BOOL BattleLink_SendParty(BattleLinkWork *work) {
    if (Comm_GetSendBufferFreeSpace() != 264) {
        return FALSE;
    }
    if (LinkSync_IsSynced(54) == 0) {
        return FALSE;
    }
    return Comm_SendCommandNoCopy(27, &work->buffer, PartyCore_sizeof());
}

static void BattleLink_RecvParty(int sender, int unused, void *data, BattleLinkWork *work) {
    work->received++;
}

BOOL BattleLink_PrepareChatot(BattleLinkWork *work) {
    if (Comm_GetSendBufferFreeSpace() != 264) {
        return FALSE;
    }
    Chatot_Copy(&work->buffer.chatot, work->setup->chatot[0]);
    return TRUE;
}

BOOL BattleLink_SendChatot(BattleLinkWork *work) {
    if (Comm_GetSendBufferFreeSpace() != 264) {
        return FALSE;
    }
    if (LinkSync_IsSynced(55) == 0) {
        return FALSE;
    }
    return Comm_SendCommandNoCopy(28, &work->buffer, 1000);
}

BOOL BattleLink_PreparePalPad(BattleLinkWork *work) {
    BattleSetup *setup;
    int index;
    int i;
    if (Comm_GetSendBufferFreeSpace() != 264) {
        return FALSE;
    }
    setup = work->setup;
    if (setup->battleType & BATTLE_TYPE_FRONTIER) {
        index = Comm_GetLocalNetId() * 8;
    } else {
        index = Comm_GetLocalNetId() * 4;
    }
    BattleLink_BuildPalPad(*(PlayerProfile **)((u8 *)setup->profile + index), setup->palPad, (SavePalPad *)&work->buffer);
    for (i = 0; i < 4; i++) {
        work->friends[i] = Heap_Alloc(HEAP_ID_BATTLE, sizeof(SavePalPad));
    }
    return TRUE;
}

BOOL BattleLink_SendPalPad(BattleLinkWork *work) {
    if (Comm_GetSendBufferFreeSpace() != 264) {
        return FALSE;
    }
    if (LinkSync_IsSynced(56) == 0) {
        return FALSE;
    }
    return Comm_SendCommandNoCopy(33, &work->buffer, 1000);
}

static void BattleLink_RecvChatot(int sender, int unused, void *data, BattleLinkWork *work) {
    work->received++;
}

BOOL BattleLink_PreparePartnerTrainer(BattleLinkWork *work, int index) {
    if (Comm_GetSendBufferFreeSpace() != 264) {
        return FALSE;
    }
    work->buffer.trainer = work->setup->trainer[index];
    return TRUE;
}

BOOL BattleLink_SendPartnerTrainer(BattleLinkWork *work, int index, int command) {
    if (Comm_GetSendBufferFreeSpace() != 264) {
        return FALSE;
    }
    if (!LinkSync_IsSynced((u8)command)) {
        return FALSE;
    }
    if (index == 1) {
        return Comm_SendCommandNoCopy(29, &work->buffer, 52);
    }
    return Comm_SendCommandNoCopy(30, &work->buffer, 52);
}

static void BattleLink_RecvPartnerTrainer(int sender, int unused, void *data, BattleLinkWork *work) {
    work->received++;
}

BOOL BattleLink_PreparePartnerParty(BattleLinkWork *work, int index) {
    if (Comm_GetSendBufferFreeSpace() != 264) {
        return FALSE;
    }
    Party_Copy(work->setup->party[index], (Party *)&work->buffer);
    return TRUE;
}

BOOL BattleLink_SendPartnerParty(BattleLinkWork *work, int index, int command) {
    if (Comm_GetSendBufferFreeSpace() != 264) {
        return FALSE;
    }
    if (!LinkSync_IsSynced((u8)command)) {
        return FALSE;
    }
    if (index == 1) {
        return Comm_SendCommandNoCopy(31, &work->buffer, PartyCore_sizeof());
    }
    return Comm_SendCommandNoCopy(32, &work->buffer, PartyCore_sizeof());
}

static void BattleLink_RecvPartnerParty(int sender, int unused, void *data, BattleLinkWork *work) {
    work->received++;
}

static void BattleLink_SendTask(SysTask *task, void *ptr) {
    BattleLinkTask *work = ptr;
    u8 *buffer = BattleSystem_GetServerMessage(work->battle);
    u16 *read = BattleSystem_GetServerReadIndex(work->battle);
    u16 *write = BattleSystem_GetServerWriteIndex(work->battle);
    u16 *end = BattleSystem_GetServerEndIndex(work->battle);
    switch (work->state) {
    case BATTLE_LINK_STATE_RUN: {
        int size;
        if (Comm_GetSendBufferFreeSpace() != 264) {
            break;
        }
        if (*read == *write) {
            break;
        }
        if (*read == *end) {
            *read = 0;
            *end = 0;
        }
        size = (buffer[*read + 2] | (buffer[*read + 3] << 8)) + 4;
        if (Comm_SendCommand(23, &buffer[*read], size) == TRUE) {
            *read += size;
        }
        break;
    }
    case BATTLE_LINK_STATE_END:
    default:
        Heap_Free(work);
        SysTask_Destroy(task);
        break;
    }
}

static void BattleLink_RecvTask(SysTask *task, void *ptr) {
    BattleLinkTask *work = ptr;
    u8 *buffer = BattleSystem_GetClientMessage(work->battle);
    u16 *read = BattleSystem_GetClientReadIndex(work->battle);
    u16 *write = BattleSystem_GetClientWriteIndex(work->battle);
    u16 *end = BattleSystem_GetClientEndIndex(work->battle);
    switch (work->state) {
    case BATTLE_LINK_STATE_RUN:
        if (*read == *write) {
            break;
        }
        if (*read == *end) {
            *read = 0;
            *end = 0;
        }
        if (BattleController_RecvCommMessage(work->battle, &buffer[*read]) == TRUE) {
            *read += (buffer[*read + 2] | (buffer[*read + 3] << 8)) + 4;
        }
        break;
    case BATTLE_LINK_STATE_END:
    default:
        Heap_Free(work);
        SysTask_Destroy(task);
        break;
    }
}

static void BattleLink_RecvEnd(int sender, int unused, void *data, BattleSystem *battle) {
    BattleSystem_SetLinkSendState(battle, BATTLE_LINK_STATE_END);
    BattleSystem_SetLinkRecvState(battle, BATTLE_LINK_STATE_END);
    BattleSystem_SetBattleFinished(battle, 1);
}

static void BattleLink_BuildPalPad(PlayerProfile *profile, SavePalPad *friends, SavePalPad *out) {
    int i;
    CopyU16StringArray(out->name, PlayerProfile_GetNamePtr(profile));
    out->otid = PlayerProfile_GetTrainerID(profile);
    out->language = PlayerProfile_GetLanguage(profile);
    out->version = PlayerProfile_GetVersion(profile);
    out->gender = PlayerProfile_GetTrainerGender(profile);
    for (i = 0; i < 16; i++) {
        out->friendOtIds[i] = friends[i].otid;
        out->friendVersions[i] = friends[i].version;
        out->friendLanguages[i] = friends[i].language;
        out->friendGenders[i] = friends[i].gender;
    }
}

static void BattleLink_RecvPalPad(int sender, int unused, SavePalPad *data, BattleLinkWork *work) {
    if (sender != Comm_GetLocalNetId()) {
        SavePalPad_Merge(work->setup->palPad, data, 1, HEAP_ID_BATTLE);
    }
    work->received++;
}

static u32 BattleLink_GetPalPadSize(void) {
    return 0x88;
}
