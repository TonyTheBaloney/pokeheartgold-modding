// [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] claude-opus-5-5, 2026-10-22
// Status: MATCHING
// Partially AI-edited: game-rule literals replaced by existing constants (MAX_MON_MOVES, PARTY_SIZE, MAX_LEVEL, FRIENDSHIP_*, NATURE_NUM, ...) (see AI_WORK_LOG.md)
#ifndef POKEHEARTGOLD_BATTLE_RECORDING_H
#define POKEHEARTGOLD_BATTLE_RECORDING_H

#include "battle/battle_setup.h"

#include "heap.h"
#include "options.h"
#include "player_data.h"
#include "pokemon_types_def.h"
#include "save.h"
#include "save_link_ruleset.h"

#define BATTLE_RECORD_MAGIC 0xE281

// What the battle video lists show.
typedef struct BattleRecordHeader {
    u16 species[12];
    u8 forms[12];
    u16 arg;
    u8 type, sealed;
    LinkBattleRuleset rules;
    u16 magic;
    u8 unk_4A[14];
    u64 videoNumber;
    u16 crc;
    u16 padding;
} BattleRecordHeader;

typedef struct BattleRecordParty {
    u16 capacity, count;
    struct BattleRecordMon mons[PARTY_SIZE];
} BattleRecordParty;

// Encrypted while stored: the BattleSetup, the parties and every battler's inputs.
typedef struct BattleRecordData {
    u32 flags; // battle type
    int winFlag;
    int trainerId[4];
    Trainer trainer[4];
    BattleBg battleBg;
    Terrain terrain;
    u32 mapSection, mapNumber;
    TIMEOFDAY timeOfDay;
    u32 evolutionLocation, unk_100;
    BOOL metBill;
    u32 caughtBattlerId, weatherType;
    int levelUpFlag;
    u32 aiFlags[4];
    u32 battleSpecial;
    int safariBalls;
    BOOL fixedDamageMovesBanned;
    int randSeed;
    int positions[4];
    u16 player, unk_146;
    int totalTurns;
    u8 chatot[4];
    u8 commands[4][1024];
    BattleRecordParty parties[4];
    PlayerProfile profiles[4];
    Options options;
    u16 magic, crc;
} BattleRecordData;

// A recorded battle (battle video): the record in progress or one loaded from the extra save chunks.
typedef struct BattleRecord {
    u32 unk_0000;
    u8 profile[0x80]; // BattleRecord_GetProfile
    BattleRecordHeader header;
    BattleRecordData data;
} BattleRecord;

extern BattleRecord *gBattleRecord;

void BattleRecord_Create(SaveData *save, enum HeapID heapID, u32 *out);
BOOL BattleRecord_Exists(void);
void BattleRecord_SetCommand(int battlerId, u32 offset, u8 data);
u8 BattleRecord_GetCommand(int battlerId, u32 offset);

#endif // POKEHEARTGOLD_BATTLE_RECORDING_H
