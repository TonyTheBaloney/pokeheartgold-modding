#include "global.h"

#include "application/vs_recorder/vs_recorder_screens.h"
#include "msgdata/msg.naix"
#include "msgdata/msg/msg_0013.h"

#include "assert.h"
#include "msgdata.h"
#include "pm_string.h"
#include "save.h"
#include "save_arrays.h"
#include "system.h"

enum VsRecorderRecordWriteState {
    VS_RECORDER_RECORD_WRITE_PREPARE,
    VS_RECORDER_RECORD_WRITE_SLOT,
};

// msg_0013 #332, used for names the font can't show
void VsRecorder_LoadPlaceholderTrainerName(String *str, enum HeapID heapID) {
    MsgData *msgData;
    String_SetEmpty(str);
    msgData = NewMsgDataFromNarc(MSGDATA_LOAD_LAZY, NARC_msgdata_msg, msg_0013, heapID);
    ReadMsgDataIntoString(msgData, msg_0013_00332, str);
    DestroyMsgData(msgData);
}

// writes the current recording into a save slot over several frames; sealed: the header gets the magic and its CRC
u32 VsRecorder_WriteRecordAsync(SaveData *saveData, u32 index, u32 sealed, u16 *state, void *writeState) {
    u16 crc;
    switch (*state) {
    case VS_RECORDER_RECORD_WRITE_PREPARE:
        GF_ASSERT(gBattleRecord != NULL);
        if (sealed == TRUE) {
            gBattleRecord->header.sealed = sealed;
            gBattleRecord->header.magic = BATTLE_RECORD_MAGIC;
            gBattleRecord->header.crc = SaveArray_CalcCRC16(saveData, &gBattleRecord->header, offsetof(BattleRecordHeader, videoNumber));
        }
        crc = gBattleRecord->data.crc;
        BattleRecord_Encrypt(&gBattleRecord->data, offsetof(BattleRecordData, crc), crc + (((u32)(crc ^ 0xFFFF)) << 16));
        (*state)++;
        break;
    case VS_RECORDER_RECORD_WRITE_SLOT:
        return BattleRecord_WriteSlot(saveData, gBattleRecord, index, writeState);
    }
    return 0;
}

// before the recording is uploaded
void VsRecorder_EncryptRecord(SaveData *saveData) {
    u16 crc;
    GF_ASSERT(gBattleRecord != NULL);
    crc = gBattleRecord->data.crc;
    BattleRecord_Encrypt(&gBattleRecord->data, offsetof(BattleRecordData, crc), crc + (((u32)(crc ^ 0xFFFF)) << 16));
}

// after the upload: stores the server's video number in the recording and saves it into the first slot
int VsRecorder_SaveRecordNumber(SaveData *saveData, u32 numberLow, u32 numberHigh, u16 *state, u16 *writeState) {
    BattleRecord *record;
    switch (*state) {
    case VS_RECORDER_RECORD_WRITE_PREPARE:
        GF_ASSERT(gBattleRecord != NULL);
        record = gBattleRecord;
        ((u32 *)&record->header.videoNumber)[0] = numberLow;
        ((u32 *)&record->header.videoNumber)[1] = numberHigh;
        (*state)++;
        break;
    case VS_RECORDER_RECORD_WRITE_SLOT:
        return BattleRecord_WriteSlot(saveData, gBattleRecord, 0, writeState);
    }
    return 0;
}

// seals the current recording and saves it into a slot at once
int VsRecorder_WriteRecord(SaveData *saveData, int index) {
    int result;
    u16 crc;
    GF_ASSERT(gBattleRecord != NULL);
    gBattleRecord->header.sealed = TRUE;
    gBattleRecord->header.magic = BATTLE_RECORD_MAGIC;
    gBattleRecord->header.crc = SaveArray_CalcCRC16(saveData, &gBattleRecord->header, offsetof(BattleRecordHeader, videoNumber));
    crc = gBattleRecord->data.crc;
    BattleRecord_Encrypt(&gBattleRecord->data, offsetof(BattleRecordData, crc), crc + (((u32)(crc ^ 0xFFFF)) << 16));
    Sys_SetSoftResetDisableFlag(8);
    result = SaveBattleRecord(saveData, gBattleRecord, index);
    if (result == 2) {
        result = SaveGameNormal(saveData);
    }
    Sys_ClearSoftResetDisableFlag(8);
    return result;
}
