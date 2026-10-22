// [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] claude-opus-5-5, 2026-10-22
// Status: MATCHING
// Partially AI-edited: game-rule literals replaced by existing constants (MAX_MON_MOVES, PARTY_SIZE, MAX_LEVEL, FRIENDSHIP_*, NATURE_NUM, ...) (see AI_WORK_LOG.md)
#ifndef POKEHEARTGOLD_BATTLE_BATTLE_PARTY_MENU_H
#define POKEHEARTGOLD_BATTLE_BATTLE_PARTY_MENU_H

#include "battle/battle.h"

#include "party.h"

enum BattlePartyMode {
    BATTLE_PARTY_MODE_SWITCH,
    BATTLE_PARTY_MODE_SWITCH_NO_CANCEL,
    BATTLE_PARTY_MODE_USE_ITEM,
    BATTLE_PARTY_MODE_LEARN_MOVE,
};

// Arguments of the in-battle party screen, filled by the battle controller before
// BattlePartyMenu_Create and read back once `done` is set.
typedef struct BattlePartyContext {
    Party *party;
    void *unk_04;
    BattleSystem *battleSystem;
    enum HeapID heapID;
    u8 unk_10;
    u8 selectedMon; // party slot picked, 6 for cancel
    u8 reservedMon; // party index the partner battler already chose to send out, 6 for none (msg 93)
    u8 unk_13;
    u8 battlingMons[2]; // party indices of the mons on the field (msg 76)
    u8 unk_16[2];
    BOOL embargo[2]; // the mon on the field in that slot is under Embargo (msg 95)
    u16 hpRestored;  // HP restored by the item used, for the battle message
    u16 item;        // item being used (BATTLE_PARTY_MODE_USE_ITEM)
    u16 move;        // move to learn (BATTLE_PARTY_MODE_LEARN_MOVE); in switch mode non-zero when the battler cannot switch out (msg 78)
    u8 unk_26[2];
    int battlerId;
    u8 partyOrder[PARTY_SIZE]; // party index of each slot on the screen
    u8 cursorActive;  // d-pad cursor state, kept between openings
    u8 pocket;        // battle pocket of item
    u8 selectedMove;  // move slot picked, 4 for the move to learn
    u8 mode;          // enum BattlePartyMode
    u8 done;          // set when the screen has closed
} BattlePartyContext;

void BattlePartyMenu_Create(BattlePartyContext *context);

#endif // POKEHEARTGOLD_BATTLE_BATTLE_PARTY_MENU_H
