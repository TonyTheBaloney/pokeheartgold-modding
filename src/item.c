#include "item.h"

#include "global.h"

#include "constants/balls.h"
#include "constants/items.h"
#include "constants/mail.h"
#include "constants/moves.h"

#include "agb/constants/items.h"
#include "itemtool/itemdata/item_data.naix"
#include "itemtool/itemdata/item_icon.naix"
#include "msgdata/msg.naix"

#include "filesystem.h"
#include "heap.h"
#include "msgdata.h"
#include "pm_string.h"

static const u16 sPocketCounts[POCKETS_COUNT] = {
    [POCKET_ITEMS] = NUM_BAG_ITEMS,
    [POCKET_MEDICINE] = NUM_BAG_MEDICINE,
    [POCKET_BALLS] = NUM_BAG_BALLS,
    [POCKET_TMHMS] = NUM_BAG_TMS_HMS,
    [POCKET_BERRIES] = NUM_BAG_BERRIES,
    [POCKET_MAIL] = NUM_BAG_MAIL,
    [POCKET_BATTLE_ITEMS] = NUM_BAG_BATTLE_ITEMS,
    [POCKET_KEY_ITEMS] = NUM_BAG_KEY_ITEMS,
};

static const u16 sTMHMMoves[] = {
    MOVE_FOCUS_PUNCH,  // TM01
    MOVE_DRAGON_CLAW,  // TM02
    MOVE_WATER_PULSE,  // TM03
    MOVE_CALM_MIND,    // TM04
    MOVE_ROAR,         // TM05
    MOVE_TOXIC,        // TM06
    MOVE_HAIL,         // TM07
    MOVE_BULK_UP,      // TM08
    MOVE_BULLET_SEED,  // TM09
    MOVE_HIDDEN_POWER, // TM10
    MOVE_SUNNY_DAY,    // TM11
    MOVE_TAUNT,        // TM12
    MOVE_ICE_BEAM,     // TM13
    MOVE_BLIZZARD,     // TM14
    MOVE_HYPER_BEAM,   // TM15
    MOVE_LIGHT_SCREEN, // TM16
    MOVE_PROTECT,      // TM17
    MOVE_RAIN_DANCE,   // TM18
    MOVE_GIGA_DRAIN,   // TM19
    MOVE_SAFEGUARD,    // TM20
    MOVE_FRUSTRATION,  // TM21
    MOVE_SOLAR_BEAM,   // TM22
    MOVE_IRON_TAIL,    // TM23
    MOVE_THUNDERBOLT,  // TM24
    MOVE_THUNDER,      // TM25
    MOVE_EARTHQUAKE,   // TM26
    MOVE_RETURN,       // TM27
    MOVE_DIG,          // TM28
    MOVE_PSYCHIC,      // TM29
    MOVE_SHADOW_BALL,  // TM30
    MOVE_BRICK_BREAK,  // TM31
    MOVE_DOUBLE_TEAM,  // TM32
    MOVE_REFLECT,      // TM33
    MOVE_SHOCK_WAVE,   // TM34
    MOVE_FLAMETHROWER, // TM35
    MOVE_SLUDGE_BOMB,  // TM36
    MOVE_SANDSTORM,    // TM37
    MOVE_FIRE_BLAST,   // TM38
    MOVE_ROCK_TOMB,    // TM39
    MOVE_AERIAL_ACE,   // TM40
    MOVE_TORMENT,      // TM41
    MOVE_FACADE,       // TM42
    MOVE_SECRET_POWER, // TM43
    MOVE_REST,         // TM44
    MOVE_ATTRACT,      // TM45
    MOVE_THIEF,        // TM46
    MOVE_STEEL_WING,   // TM47
    MOVE_SKILL_SWAP,   // TM48
    MOVE_SNATCH,       // TM49
    MOVE_OVERHEAT,     // TM50
    MOVE_ROOST,        // TM51
    MOVE_FOCUS_BLAST,  // TM52
    MOVE_ENERGY_BALL,  // TM53
    MOVE_FALSE_SWIPE,  // TM54
    MOVE_BRINE,        // TM55
    MOVE_FLING,        // TM56
    MOVE_CHARGE_BEAM,  // TM57
    MOVE_ENDURE,       // TM58
    MOVE_DRAGON_PULSE, // TM59
    MOVE_DRAIN_PUNCH,  // TM60
    MOVE_WILL_O_WISP,  // TM61
    MOVE_SILVER_WIND,  // TM62
    MOVE_EMBARGO,      // TM63
    MOVE_EXPLOSION,    // TM64
    MOVE_SHADOW_CLAW,  // TM65
    MOVE_PAYBACK,      // TM66
    MOVE_RECYCLE,      // TM67
    MOVE_GIGA_IMPACT,  // TM68
    MOVE_ROCK_POLISH,  // TM69
    MOVE_FLASH,        // TM70
    MOVE_STONE_EDGE,   // TM71
    MOVE_AVALANCHE,    // TM72
    MOVE_THUNDER_WAVE, // TM73
    MOVE_GYRO_BALL,    // TM74
    MOVE_SWORDS_DANCE, // TM75
    MOVE_STEALTH_ROCK, // TM76
    MOVE_PSYCH_UP,     // TM77
    MOVE_CAPTIVATE,    // TM78
    MOVE_DARK_PULSE,   // TM79
    MOVE_ROCK_SLIDE,   // TM80
    MOVE_X_SCISSOR,    // TM81
    MOVE_SLEEP_TALK,   // TM82
    MOVE_NATURAL_GIFT, // TM83
    MOVE_POISON_JAB,   // TM84
    MOVE_DREAM_EATER,  // TM85
    MOVE_GRASS_KNOT,   // TM86
    MOVE_SWAGGER,      // TM87
    MOVE_PLUCK,        // TM88
    MOVE_U_TURN,       // TM89
    MOVE_SUBSTITUTE,   // TM90
    MOVE_FLASH_CANNON, // TM91
    MOVE_TRICK_ROOM,   // TM92
    MOVE_CUT,          // HM01
    MOVE_FLY,          // HM02
    MOVE_SURF,         // HM03
    MOVE_STRENGTH,     // HM04
    MOVE_WHIRLPOOL,    // HM05
    MOVE_ROCK_SMASH,   // HM06
    MOVE_WATERFALL,    // HM07
    MOVE_ROCK_CLIMB,   // HM08
};

// [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] generated from data/items/items.json (tools/pokedata/items.py)
#include "data/items/item_narc_ids.h"

void MoveItemSlotInList(ItemSlot *slots, int from, int to, int pocket, enum HeapID heapID) {
    ItemSlot *buf;
    int i, j;
    if (from == to) {
        return;
    }

    buf = Heap_Alloc(heapID, sPocketCounts[pocket] * sizeof(ItemSlot));

    j = 0;
    for (i = 0; i < sPocketCounts[pocket]; i++) {
        if (from != i) {
            if (to == j) {
                buf[j] = slots[from];
                j++;
            }
            buf[j] = slots[i];
            j++;
        }
    }

    if (to == sPocketCounts[pocket] - 1) {
        buf[j] = slots[from];
    }

    for (j = 0; j < sPocketCounts[pocket]; j++) {
        slots[j] = buf[j];
    }

    Heap_Free(buf);
}

int GetItemIndexMapping(u16 itemId, int attrNo) {
    switch (attrNo) {
    case ITEMNARC_PARAM:
        if (itemId != ITEM_NONE && itemId != 0xFFFF) {
            return sItemNarcIds[itemId][ITEMNARC_PARAM];
        }
        break;
    case ITEMNARC_NCGR:
        if (itemId == ITEM_NONE) {
            return NARC_item_icon_item_icon_793_NCGR;
        } else if (itemId == 0xFFFF) {
            return NARC_item_icon_item_icon_795_NCGR;
        } else {
            return sItemNarcIds[itemId][ITEMNARC_NCGR];
        }
    case ITEMNARC_NCLR:
        if (itemId == ITEM_NONE) {
            return NARC_item_icon_item_icon_794_NCLR;
        } else if (itemId == 0xFFFF) {
            return NARC_item_icon_item_icon_796_NCLR;
        } else {
            return sItemNarcIds[itemId][ITEMNARC_NCLR];
        }
    case ITEMNARC_AGBCODE:
        if (itemId != ITEM_NONE && itemId != 0xFFFF) {
            return sItemNarcIds[itemId][ITEMNARC_AGBCODE];
        }
        break;
    }

    return 0;
}

u16 UpConvertItemId_Gen3to4(u16 agbcode) {
    u16 ntrcode;

    for (ntrcode = ITEM_MIN; ntrcode <= ITEM_MAX; ntrcode++) {
        if (agbcode == sItemNarcIds[ntrcode][ITEMNARC_AGBCODE]) {
            return ntrcode;
        }
    }

    return ITEM_NONE;
}

int GetItemIconCell(void) {
    return NARC_item_icon_item_icon_001_NCER;
}

int GetItemIconAnim(void) {
    return NARC_item_icon_item_icon_000_NANR;
}

void *LoadItemDataOrGfx(u16 itemId, int attrno, enum HeapID heapID) {
    if (itemId > ITEM_MAX) {
        itemId = ITEM_NONE;
    }
    switch (attrno) {
    case ITEMNARC_PARAM:
        return AllocAndReadWholeNarcMemberByIdPair(NARC_itemtool_itemdata_item_data, sItemNarcIds[itemId][ITEMNARC_PARAM], heapID);
    case ITEMNARC_NCGR:
        return AllocAndReadWholeNarcMemberByIdPair(NARC_itemtool_itemdata_item_icon, sItemNarcIds[itemId][ITEMNARC_NCGR], heapID);
    case ITEMNARC_NCLR:
        return AllocAndReadWholeNarcMemberByIdPair(NARC_itemtool_itemdata_item_icon, sItemNarcIds[itemId][ITEMNARC_NCLR], heapID);
    }

    return NULL;
}

void GetItemNameIntoString(String *dest, u16 itemId, enum HeapID heapID) {
    MsgData *msgData = NewMsgDataFromNarc(MSGDATA_LOAD_LAZY, NARC_msgdata_msg, msg_0222, heapID);
    ReadMsgDataIntoString(msgData, itemId, dest);
    DestroyMsgData(msgData);
}

void GetItemDescIntoString(String *dest, u16 itemId, enum HeapID heapID) {
    MsgData *msgData = NewMsgDataFromNarc(MSGDATA_LOAD_LAZY, NARC_msgdata_msg, msg_0221, heapID);
    ReadMsgDataIntoString(msgData, itemId, dest);
    DestroyMsgData(msgData);
}

static s32 GetItemAttrSub(ItemPartyParam *param, u16 attrno);

s32 GetItemAttr(u16 itemId, u16 attrno, enum HeapID heapID) {
    ItemData *itemData = (ItemData *)LoadItemDataOrGfx(itemId, ITEMNARC_PARAM, heapID);
    s32 ret = GetItemAttr_PreloadedItemData(itemData, attrno);
    Heap_FreeExplicit(heapID, itemData);
    return ret;
}

s32 GetItemAttr_PreloadedItemData(ItemData *itemData, u16 attrno) {
    switch (attrno) {
    case ITEMATTR_PRICE:
        return itemData->price;
    case ITEMATTR_HOLD_EFFECT:
        return itemData->holdEffect;
    case ITEMATTR_HOLD_EFFECT_PARAM:
        return itemData->holdEffectParam;
    case ITEMATTR_PREVENT_TOSS:
        return itemData->prevent_toss;
    case ITEMATTR_SELECTABLE:
        return itemData->selectable;
    case ITEMATTR_FIELD_POCKET:
        return itemData->fieldPocket;
    case ITEMATTR_FIELDUSEFUNC:
        return itemData->fieldUseFunc;
    case ITEMATTR_BATTLEUSEFUNC:
        return itemData->battleUseFunc;
    case ITEMATTR_PLUCK_EFFECT:
        return itemData->pluckEffect;
    case ITEMATTR_FLING_EFFECT:
        return itemData->flingEffect;
    case ITEMATTR_FLING_POWER:
        return itemData->flingPower;
    case ITEMATTR_NATURAL_GIFT_POWER:
        return itemData->naturalGiftPower;
    case ITEMATTR_NATURAL_GIFT_TYPE:
        return itemData->naturalGiftType;
    case ITEMATTR_BATTLE_POCKET:
        return itemData->battlePocket;
    case ITEMATTR_PARTY_USE:
        return itemData->partyUse;
    default:
        switch (itemData->partyUse) {
        case PARTYUSE_NO:
            return itemData->dummy;
        case PARTYUSE_YES:
            return GetItemAttrSub(&itemData->partyUseParam, attrno);
        }
    }

    return 0;
}

static s32 GetItemAttrSub(ItemPartyParam *partyParam, u16 attr) {
    switch (attr) {
    case ITEMATTR_SLP_HEAL:
        return partyParam->slp_heal;
    case ITEMATTR_PSN_HEAL:
        return partyParam->psn_heal;
    case ITEMATTR_BRN_HEAL:
        return partyParam->brn_heal;
    case ITEMATTR_FRZ_HEAL:
        return partyParam->frz_heal;
    case ITEMATTR_PRZ_HEAL:
        return partyParam->prz_heal;
    case ITEMATTR_CFS_HEAL:
        return partyParam->cfs_heal;
    case ITEMATTR_INF_HEAL:
        return partyParam->inf_heal;
    case ITEMATTR_GUARD_SPEC:
        return partyParam->guard_spec;
    case ITEMATTR_REVIVE:
        return partyParam->revive;
    case ITEMATTR_REVIVE_ALL:
        return partyParam->revive_all;
    case ITEMATTR_LEVEL_UP:
        return partyParam->level_up;
    case ITEMATTR_EVOLVE:
        return partyParam->evolve;
    case ITEMATTR_ATK_STAGES:
        return partyParam->atk_stages;
    case ITEMATTR_DEF_STAGES:
        return partyParam->def_stages;
    case ITEMATTR_SPATK_STAGES:
        return partyParam->spatk_stages;
    case ITEMATTR_SPDEF_STAGES:
        return partyParam->spdef_stages;
    case ITEMATTR_SPEED_STAGES:
        return partyParam->speed_stages;
    case ITEMATTR_ACCURACY_STAGES:
        return partyParam->accuracy_stages;
    case ITEMATTR_CRITRATE_STAGES:
        return partyParam->critrate_stages;
    case ITEMATTR_PP_UP:
        return partyParam->pp_up;
    case ITEMATTR_PP_MAX:
        return partyParam->pp_max;
    case ITEMATTR_PP_RESTORE:
        return partyParam->pp_restore;
    case ITEMATTR_PP_RESTORE_ALL:
        return partyParam->pp_restore_all;
    case ITEMATTR_HP_RESTORE:
        return partyParam->hp_restore;
    case ITEMATTR_HP_EV_UP:
        return partyParam->hp_ev_up;
    case ITEMATTR_ATK_EV_UP:
        return partyParam->atk_ev_up;
    case ITEMATTR_DEF_EV_UP:
        return partyParam->def_ev_up;
    case ITEMATTR_SPEED_EV_UP:
        return partyParam->speed_ev_up;
    case ITEMATTR_SPATK_EV_UP:
        return partyParam->spatk_ev_up;
    case ITEMATTR_SPDEF_EV_UP:
        return partyParam->spdef_ev_up;
    case ITEMATTR_FRIENDSHIP_MOD_LO:
        return partyParam->friendship_mod_lo;
    case ITEMATTR_FRIENDSHIP_MOD_MED:
        return partyParam->friendship_mod_med;
    case ITEMATTR_FRIENDSHIP_MOD_HI:
        return partyParam->friendship_mod_hi;
    case ITEMATTR_HP_EV_UP_PARAM:
        return partyParam->hp_ev_up_param;
    case ITEMATTR_ATK_EV_UP_PARAM:
        return partyParam->atk_ev_up_param;
    case ITEMATTR_DEF_EV_UP_PARAM:
        return partyParam->def_ev_up_param;
    case ITEMATTR_SPEED_EV_UP_PARAM:
        return partyParam->speed_ev_up_param;
    case ITEMATTR_SPATK_EV_UP_PARAM:
        return partyParam->spatk_ev_up_param;
    case ITEMATTR_SPDEF_EV_UP_PARAM:
        return partyParam->spdef_ev_up_param;
    case ITEMATTR_HP_RESTORE_PARAM:
        return partyParam->hp_restore_param;
    case ITEMATTR_PP_RESTORE_PARAM:
        return partyParam->pp_restore_param;
    case ITEMATTR_FRIENDSHIP_MOD_LO_PARAM:
        return partyParam->friendship_mod_lo_param;
    case ITEMATTR_FRIENDSHIP_MOD_MED_PARAM:
        return partyParam->friendship_mod_med_param;
    case ITEMATTR_FRIENDSHIP_MOD_HI_PARAM:
        return partyParam->friendship_mod_hi_param;
    default:
        return 0;
    }
}

u16 TMHMGetMove(u16 itemId) {
    if (itemId < ITEM_TM01 || itemId > ITEM_HM08) {
        return MOVE_NONE;
    }

    itemId -= ITEM_TM01;
    return sTMHMMoves[itemId];
}

BOOL MoveIsHM(u16 moveId) {
    u8 i;

    for (i = 0; i < NUM_HMS; i++) {
        if (sTMHMMoves[i + ITEM_HM01 - ITEM_TM01] == moveId) {
            return TRUE;
        }
    }

    return FALSE;
}

u8 ItemToTMHMId(u16 itemId) {
    if (itemId < ITEM_TM01 || itemId > ITEM_HM08) {
        return 0;
    }

    return itemId - ITEM_TM01;
}

BOOL ItemIdIsMail(u16 itemId) {
    if (itemId < FIRST_MAIL_IDX || itemId > LAST_MAIL_IDX) {
        return FALSE;
    } else {
        return TRUE;
    }
}

u8 ItemToMailId(u16 itemId) {
    if (itemId < FIRST_MAIL_IDX || itemId > LAST_MAIL_IDX) {
        return 0;
    } else {
        return itemId - ITEM_GRASS_MAIL + MAIL_GRASS;
    }
}

u16 MailToItemId(u8 mailId) {
    if (mailId >= NUM_MAIL) {
        return ITEM_NONE;
    } else {
        return mailId - MAIL_GRASS + ITEM_GRASS_MAIL;
    }
}

s32 ItemToBallId(u16 itemId) {
    if (itemId >= ITEM_MASTER_BALL && itemId <= ITEM_CHERISH_BALL) {
        return itemId - ITEM_MASTER_BALL + BALL_MASTER;
    } else if (itemId >= ITEM_FAST_BALL && itemId <= ITEM_SPORT_BALL) {
        return itemId - ITEM_FAST_BALL + BALL_FAST;
    } else {
        return BALL_POKE;
    }
}

u16 BallToItemId(s32 ballId) {
    if (ballId >= BALL_MASTER && ballId <= BALL_CHERISH) {
        return ballId - BALL_MASTER + ITEM_MASTER_BALL;
    } else if (ballId >= BALL_FAST && ballId <= BALL_SPORT) {
        return ballId - BALL_FAST + ITEM_FAST_BALL;
    } else {
        return ITEM_POKE_BALL;
    }
}

BOOL ItemIdIsBerry(u16 itemId) {
    if (itemId < FIRST_BERRY_IDX || itemId > LAST_BERRY_IDX) {
        return FALSE;
    } else {
        return TRUE;
    }
}

u16 BerryToItemId(u8 berryId) {
    if (berryId >= NUM_BERRIES) {
        return 0xFFFF;
    }
    return (u16)(berryId + FIRST_BERRY_IDX);
}

String *GetNutName(u16 berryId, enum HeapID heapID) {
    String *ret;
    MsgData *msgData;

    if (berryId != 0) {
        berryId--;
    }
    msgData = NewMsgDataFromNarc(MSGDATA_LOAD_LAZY, NARC_msgdata_msg, msg_0251, heapID);
    ret = NewString_ReadMsgData(msgData, berryId);
    DestroyMsgData(msgData);
    return ret;
}

ItemData *LoadAllItemData(enum HeapID heapID) {
    return AllocAndReadFromNarcMemberByIdPair(NARC_itemtool_itemdata_item_data, 0, heapID, 0, GetItemIndexMapping(ITEM_MAX, ITEMNARC_PARAM) * sizeof(ItemData));
}

ItemData *GetItemDataPtrFromArray(ItemData *itemData, u32 itemDataIdx) {
    return &itemData[itemDataIdx];
}

BOOL ItemIdIsNotJohtoBall(u16 itemId) {
    // stupid hack to get it to match
    if ((u16)(itemId + (u16)-ITEM_FAST_BALL) > (ITEM_PARK_BALL - ITEM_FAST_BALL)) {
        return TRUE;
    } else {
        return FALSE;
    }
}
