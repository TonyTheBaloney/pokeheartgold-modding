#include "global.h"

#include "constants/items.h"
#include "constants/save_arrays.h"

#include "msgdata/msg.naix"
#include "msgdata/msg/msg_0021.h"

#include "apricorn_internal.h"

// Apricorn box save data (save array 0x26): apricorn counts, the apricorn given to Kurt, the juice being mixed
// (Apricorn juice for the Pokeathlon: 5 flavor values and a mood, updated as the player walks) and the three
// stored juice records.

typedef struct FlavorPair {
    u8 id;
    u8 value;
} FlavorPair;

static void InitApricornBox(SaveApricornBox *apricornBox);
static void ApricornBox_ClearJuiceRecords(SaveApricornBox *apricornBox);
static void ClearApricornJuice(ApricornJuice *juice);
static int ApricornBox_TakeApricorn(SaveApricornBox *apricornBox, int apricorn, u32 quantity);
static BOOL ApricornJuice_IsValid(ApricornJuice *data);
static BOOL ApricornRecord_IsSameTrainer(ApricornRecord *a, ApricornRecord *b);
static void ApricornBox_AddJuiceMildness(SaveApricornBox *box, u8 amount);
static void ApricornBox_MixQueuedApricorns(SaveApricornBox *box);
static void ApricornJuice_GetFlavors(ApricornJuice *data, u8 *out);
static u8 GetJuiceFlavorLevel(int type, u8 value);
static void PackJuiceFlavor(ApricornJuiceEntry *entry, FlavorPair *pair, int type);
static void ClearApricornJuiceRecord(ApricornRecord *record);

static const u16 sApricornBallItems[] = {
    ITEM_LEVEL_BALL,
    ITEM_MOON_BALL,
    ITEM_LURE_BALL,
    ITEM_FRIEND_BALL,
    ITEM_LOVE_BALL,
    ITEM_FAST_BALL,
    ITEM_HEAVY_BALL,
};

static const s8 sApricornFlavorDeltas[APRICORN_TYPE_COUNT][APRICORN_JUICE_FLAVOR_COUNT] = {
    { 4,  -2, 0,  0,  0  },
    { 0,  4,  -2, 0,  0  },
    { 0,  0,  4,  -2, 0  },
    { 0,  0,  0,  4,  -2 },
    { -2, 0,  0,  0,  4  },
    { -2, -2, -2, -2, -2 },
    { 2,  2,  2,  2,  2  },
};

static const ApricornJuice sApricornJuicePresets[APRICORN_JUICE_PRESET_COUNT] = {
    { 0,   116, { 22, 10, 0, 0, 0 } },
    { 150, 120, { 0, 20, 14, 0, 0 } },
    { 540, 125, { 0, 0, 28, 20, 0 } },
    { 200, 136, { 0, 0, 0, 24, 14 } },
    { 150, 104, { 12, 0, 0, 0, 20 } },
};

u32 Save_ApricornBox_sizeof(void) {
    return sizeof(SaveApricornBox);
}

u32 ApricornJuiceRecord_sizeof(void) {
    return sizeof(ApricornRecord);
}

SaveApricornBox *Save_ApricornBox_Get(SaveData *saveData) {
    return SaveArray_Get(saveData, SAVE_APRICORN_BOX);
}

static void InitApricornBox(SaveApricornBox *apricornBox) {
    MI_CpuFill8(apricornBox, 0, sizeof(SaveApricornBox));
    ClearApricornJuice(&apricornBox->juice);
    ApricornBox_ClearJuiceRecords(apricornBox);
}

static void ApricornBox_ClearJuiceRecords(SaveApricornBox *apricornBox) {
    int i;
    for (i = 0; i < APRICORN_JUICE_RECORD_COUNT; i++) {
        ClearApricornJuiceRecord(&apricornBox->juiceRecords[i]);
    }
}

void Save_ApricornBox_Init(SaveApricornBox *apricornBox) {
    InitApricornBox(apricornBox);
}

static void ClearApricornJuice(ApricornJuice *juice) {
    MI_CpuFill8(juice, 0, sizeof(ApricornJuice));
}

int ApricornBox_GiveApricorn(SaveApricornBox *apricornBox, int apricorn, u8 amount) {
    int quantity = amount;
    if (apricorn >= APRICORN_TYPE_COUNT) {
        GF_ASSERT(FALSE);
        return 0;
    }
    quantity += apricornBox->apricorns[apricorn];
    if (quantity > 99) {
        apricornBox->apricorns[apricorn] = 99;
    } else {
        apricornBox->apricorns[apricorn] = quantity;
    }
    return apricornBox->apricorns[apricorn];
}

static int ApricornBox_TakeApricorn(SaveApricornBox *apricornBox, int apricorn, u32 quantity) {
    u8 count;
    if (apricorn >= APRICORN_TYPE_COUNT) {
        GF_ASSERT(FALSE);
        return 0;
    }
    count = apricornBox->apricorns[apricorn];
    if (count >= quantity) {
        apricornBox->apricorns[apricorn] = count - quantity;
    }
    return apricornBox->apricorns[apricorn];
}

int ApricornBox_CountApricorn(SaveApricornBox *apricornBox, int apricorn) {
    if (apricorn >= APRICORN_TYPE_COUNT) {
        GF_ASSERT(FALSE);
        return 0;
    }
    return apricornBox->apricorns[apricorn];
}

void ApricornBox_SetKurtApricorn(SaveApricornBox *apricornBox, u32 apricorn, u32 quantity) {
    if (apricornBox->apricorns[apricorn] < quantity) {
        GF_ASSERT(FALSE);
        return;
    }
    apricornBox->kurtApricorn = apricorn;
    apricornBox->kurtQuantity = quantity;
    ApricornBox_TakeApricorn(apricornBox, apricorn, quantity);
}

int ApricornBox_GetKurtQuantity(SaveApricornBox *apricornBox) {
    return apricornBox->kurtQuantity;
}

int ApricornBox_GetKurtBall(SaveApricornBox *apricornBox) {
    if (apricornBox->kurtApricorn >= APRICORN_TYPE_COUNT) {
        return ITEM_POKE_BALL;
    }
    return sApricornBallItems[apricornBox->kurtApricorn];
}

void ApricornBox_SetMixState(SaveApricornBox *apricornBox, u32 value) {
    apricornBox->mixWord = (apricornBox->mixWord & 0x3FFFFFFF) | (value << 30);
}

u32 ApricornBox_GetMixState(SaveApricornBox *apricornBox) {
    return apricornBox->mixWord >> 30;
}

int ApricornBox_CountQueuedApricorns(SaveApricornBox *box) {
    int i;
    u8 count;
    u16 value;

    count = 0;
    value = box->queuedApricorns;
    for (i = 0; i < APRICORN_QUEUE_SLOT_COUNT; i++) {
        if (value & APRICORN_QUEUE_SLOT_MASK) {
            count++;
        }
        value >>= APRICORN_QUEUE_SLOT_BITS;
    }
    return count;
}

BOOL ApricornBox_QueueApricorn(SaveApricornBox *box, int apricorn, u32 value) {
    u16 slots = box->queuedApricorns;
    u16 encoded;
    int i;
    if (apricorn >= APRICORN_TYPE_COUNT) {
        GF_ASSERT(FALSE);
        return FALSE;
    }
    for (i = 0; i < APRICORN_QUEUE_SLOT_COUNT; i++) {
        if (slots & APRICORN_QUEUE_SLOT_MASK) {
            slots >>= APRICORN_QUEUE_SLOT_BITS;
            continue;
        }
        encoded = ((apricorn + 1) & APRICORN_QUEUE_SLOT_MASK) << (i * APRICORN_QUEUE_SLOT_BITS);
        box->queuedApricorns |= encoded;
        box->queuedApricorns |= APRICORN_QUEUE_MIXING;
        box->mixStartSteps = value;
        if (box->juiceServings == 0) {
            box->juiceAgingSteps = value;
        }
        box->mixWord &= 0xC0000000;
        ApricornBox_TakeApricorn(box, apricorn, 1);
        return TRUE;
    }
    return FALSE;
}

int ApricornBox_GetMixProgressLevel(SaveApricornBox *box) {
    u32 value;
    if (ApricornBox_CountQueuedApricorns(box) == 0) {
        return 0;
    }
    value = box->mixProgress;
    if (value < 50) {
        return 1;
    }
    if (value < 80) {
        return 2;
    }
    return 3;
}

void ApricornBox_AddJuiceMildnessForDays(SaveApricornBox *box, int amount) {
    int increment = amount * 10;
    int value;
    if (box->juiceServings != 0) {
        value = box->juice.mildness;
        value += increment;
        if (value > 255) {
            box->juice.mildness = 255;
        } else {
            box->juice.mildness = value;
        }
    }
}

u8 ApricornBox_GetJuiceServings(SaveApricornBox *box) {
    return box->juiceServings;
}

BOOL ApricornBox_GetJuice(SaveApricornBox *box, int index, ApricornJuice *out) {
    ApricornJuice *record;

    if (index >= APRICORN_JUICE_COUNT) {
        index = 0;
    }
    if (index <= APRICORN_JUICE_PRESET_LAST) {
        *out = sApricornJuicePresets[index];
    } else if (index <= APRICORN_JUICE_RECORD_LAST) {
        record = &box->juiceRecords[index - APRICORN_JUICE_FIRST_RECORD].data;
        if (ApricornJuice_GetFlavorTotal(record) == 0) {
            ClearApricornJuice(out);
            return FALSE;
        }
        *out = *record;
    } else {
        if (box->juiceServings == 0) {
            ClearApricornJuice(out);
            return FALSE;
        }
        *out = box->juice;
    }
    return TRUE;
}

static BOOL ApricornJuice_IsValid(ApricornJuice *data) {
    if (ApricornJuice_GetFlavorTotal(data) != 0) {
        return TRUE;
    }
    return FALSE;
}

int ApricornJuice_GetFlavorTotal(ApricornJuice *data) {
    int i;
    u16 total = 0;
    for (i = 0; i < APRICORN_JUICE_FLAVOR_COUNT; i++) {
        total += data->flavors[i];
    }
    if (total > 100) {
        total = 100;
    }
    return (u8)total;
}

void ApricornJuice_RankFlavors(ApricornJuice *juice, ApricornJuiceRanking *out) {
    FlavorPair pairs[APRICORN_JUICE_FLAVOR_COUNT];
    FlavorPair tmp;
    u8 count;
    int i, j;
    u8 minimum;
    MI_CpuFill8(out, 0, sizeof(ApricornJuiceRanking));
    MI_CpuFill8(pairs, 0, sizeof(pairs));
    count = 0;
    for (i = 0; i < APRICORN_JUICE_FLAVOR_COUNT; i++) {
        u8 value = juice->flavors[i];
        pairs[i].id = i;
        pairs[i].value = value;
        if (value) {
            count++;
        }
    }
    if (count) {
        for (i = 0; i < 5; i++) {
            for (j = i + 1; j < 5; j++) {
                u8 b = pairs[j].value, a = pairs[i].value;
                if (a > b) {
                    continue;
                }
                if (a == b && pairs[i].id < pairs[j].id) {
                    continue;
                }
                tmp = pairs[i];
                pairs[i] = pairs[j];
                pairs[j] = tmp;
            }
        }
    }
    minimum = pairs[4].value;
    for (i = 0; i < 5; i++) {
        out->order[i] = pairs[i].id;
        if (minimum == pairs[i].value) {
            out->ties++;
        }
    }
    out->count = count;
    switch (count) {
    case 0:
        out->entries[0].stat = APRICORN_JUICE_FLAVOR_NONE;
        return;
    case 1:
        PackJuiceFlavor(&out->entries[0], &pairs[0], 0);
        out->entries[1].stat = APRICORN_JUICE_FLAVOR_NONE;
        break;
    case 2:
        PackJuiceFlavor(&out->entries[0], &pairs[0], 0);
        PackJuiceFlavor(&out->entries[1], &pairs[1], 1);
        out->entries[2].stat = APRICORN_JUICE_FLAVOR_NONE;
        break;
    case 3:
        PackJuiceFlavor(&out->entries[0], &pairs[0], 0);
        PackJuiceFlavor(&out->entries[1], &pairs[1], 1);
        PackJuiceFlavor(&out->entries[2], &pairs[2], 2);
        break;
    case 4:
    case 5:
        if (pairs[0].value - pairs[3].value <= 12) {
            out->entries[0].stat = APRICORN_JUICE_FLAVOR_MIXED;
            out->entries[0].amount = pairs[0].value;
            out->entries[1].stat = APRICORN_JUICE_FLAVOR_NONE;
            out->entries[1].amount = pairs[1].value;
            out->entries[2].stat = APRICORN_JUICE_FLAVOR_NONE;
            out->entries[2].amount = pairs[2].value;
            out->count = 1;
            {
                u8 top = pairs[0].value;
                if (top > 20) {
                    out->entries[0].strength = 3;
                } else if (top > 7) {
                    out->entries[0].strength = 2;
                } else {
                    out->entries[0].strength = 1;
                }
            }
        } else {
            PackJuiceFlavor(&out->entries[0], &pairs[0], 0);
            PackJuiceFlavor(&out->entries[1], &pairs[1], 1);
            if (count == 4) {
                PackJuiceFlavor(&out->entries[2], &pairs[4], 2);
            } else {
                out->entries[2].stat = APRICORN_JUICE_FLAVOR_MIXED;
                out->entries[2].strength = 1;
                out->entries[2].amount = pairs[2].value;
            }
        }
        break;
    }
    out->count = count;
}

int ApricornJuice_GetTopMixIndex(ApricornJuice *juice) {
    ApricornJuiceRanking ranking;
    u32 value;
    ApricornJuice_RankFlavors(juice, &ranking);
    value = ranking.entries[0].stat;
    if (value >= APRICORN_JUICE_FLAVOR_MIXED) {
        value = APRICORN_JUICE_FLAVOR_MIXED;
    }
    return value;
}

int ApricornJuice_GetFlavorNameIndex(ApricornJuice *juice) {
    ApricornJuiceRanking ranking;
    ApricornJuice_RankFlavors(juice, &ranking);
    if (ranking.count == 0) {
        return 0;
    }
    return ranking.order[0] + 1;
}

int ApricornBox_UseJuiceServing(SaveApricornBox *box) {
    if (box->juiceServings == 0) {
        return 0;
    }
    box->juiceServings--;
    if (box->juiceServings == 0) {
        ClearApricornJuice(&box->juice);
        box->juiceAgingSteps = 0;
        box->mixStartSteps = 0;
        box->mixProgress = 0;
    }
    return box->juiceServings;
}

void ApricornBox_UpdateSteps(SaveApricornBox *box, u32 steps) {
    u32 difference;
    if (box->mixing != 0 || box->juiceServings != 0) {
        difference = steps - box->juiceAgingSteps;
        if (difference >= 100) {
            ApricornBox_AddJuiceMildness(box, difference / 100);
            box->juiceAgingSteps = steps - difference % 100;
        }
        if (box->mixing != 0) {
            box->mixProgress = steps - box->mixStartSteps;
            if (box->mixProgress >= 100) {
                if (box->juiceServings != 0) {
                    ApricornBox_SetMixState(box, 3);
                } else {
                    ApricornBox_SetMixState(box, 2);
                }
                ApricornBox_MixQueuedApricorns(box);
            }
        }
    }
}

ApricornRecord *ApricornRecord_New(SaveApricornBox *box, PlayerProfile *profile, u32 value, enum HeapID heapId) {
    ApricornRecord *record = Heap_AllocAtEnd(heapId, sizeof(ApricornRecord));
    MI_CpuFill8(record, 0, sizeof(ApricornRecord));
    record->trainerId = PlayerProfile_GetTrainerID(profile);
    record->gender = PlayerProfile_GetTrainerGender(profile);
    record->language = PlayerProfile_GetLanguage(profile);
    record->version = PlayerProfile_GetVersion(profile);
    StringFillEOS(record->name, 8);
    CopyU16StringArrayN(record->name, PlayerProfile_GetNamePtr(profile), 7);
    ApricornBox_GetJuice(box, APRICORN_JUICE_OWN, &record->data);
    if (value > 0xFFFF) {
        record->data.fanCount = 0xFFFF;
    } else {
        record->data.fanCount = value;
    }
    return record;
}

static BOOL ApricornRecord_IsSameTrainer(ApricornRecord *a, ApricornRecord *b) {
    if (a->trainerId != b->trainerId) {
        return FALSE;
    }
    if (a->gender != b->gender) {
        return FALSE;
    }
    if (a->version != b->version) {
        return FALSE;
    }
    if (a->language != b->language) {
        return FALSE;
    }
    if (StringNotEqual(a->name, b->name) == FALSE) {
        return TRUE;
    }
    return FALSE;
}

void ApricornBox_StoreJuiceRecords(SaveApricornBox *box, ApricornRecord *records, int count, int skip) {
    volatile int found;
    int numRecords = 0;
    int outerIndex;
    int initialIndex = 0;
    int foundIndex;
    int j;
    u32 destIndex;

    do {
        if (!ApricornJuice_IsValid(&box->juiceRecords[initialIndex].data)) {
            break;
        }
        numRecords++;
        initialIndex++;
    } while (initialIndex < APRICORN_JUICE_RECORD_COUNT);

    outerIndex = 0;
    if (count <= 0) {
        return;
    }
    do {
        if (outerIndex != skip && ApricornJuice_IsValid(&records->data)) {
            foundIndex = 0;
            found = FALSE;
            {
                ApricornRecord *boxRecord = box->juiceRecords;
                j = found;
                do {
                    if (ApricornRecord_IsSameTrainer(records, boxRecord)) {
                        foundIndex = (u8)j;
                        found = TRUE;
                        break;
                    }
                    j++;
                    boxRecord++;
                } while (j < APRICORN_JUICE_RECORD_COUNT);
            }
            if (numRecords >= APRICORN_JUICE_RECORD_COUNT) {
                destIndex = APRICORN_JUICE_RECORD_COUNT - 1;
                found = TRUE;
            } else if (found) {
                destIndex = (u8)(numRecords - 1);
            } else {
                destIndex = (u8)numRecords;
                numRecords++;
            }
            if (found && (u32)foundIndex < destIndex) {
                int limit = numRecords - 1;
                if (foundIndex < limit) {
                    do {
                        box->juiceRecords[foundIndex] = box->juiceRecords[foundIndex + 1];
                        foundIndex++;
                    } while (foundIndex < limit);
                }
            }
            box->juiceRecords[destIndex] = *records;
        }
        records++;
        outerIndex++;
    } while (outerIndex < count);
}

String *ApricornBox_GetJuiceName(SaveApricornBox *box, int type, u32 heapId) {
    String *result = String_New(9, (enum HeapID)heapId);
    if (type < 5) {
        MsgData *msgData = NewMsgDataFromNarc(MSGDATA_LOAD_LAZY, NARC_msgdata_msg, msg_0021, (enum HeapID)heapId);
        ReadMsgDataIntoString(msgData, type + msg_0021_00014, result);
        DestroyMsgData(msgData);
    } else if (type < 8) {
        int slot = (u8)(type - 5);
        if (ApricornJuice_IsValid(&box->juiceRecords[slot].data)) {
            CopyU16ArrayToString(result, box->juiceRecords[slot].name);
        }
    }
    return result;
}

String *ApricornBox_GetJuiceFlavorName(SaveApricornBox *box, u16 type, u32 heapId) {
    ApricornJuice data;
    MsgData *msgData;
    String *result;
    ApricornBox_GetJuice(box, type, &data);
    msgData = NewMsgDataFromNarc(MSGDATA_LOAD_LAZY, NARC_msgdata_msg, msg_0021, (enum HeapID)heapId);
    result = NewString_ReadMsgData(msgData, ApricornJuice_GetFlavorNameIndex(&data) + msg_0021_00019);
    DestroyMsgData(msgData);
    return result;
}

static void ApricornBox_AddJuiceMildness(SaveApricornBox *box, u8 amount) {
    int value = box->juice.mildness + amount;
    if (value > 255) {
        box->juice.mildness = 255;
    } else {
        box->juice.mildness = value;
    }
}

static void ApricornBox_MixQueuedApricorns(SaveApricornBox *box) {
    s8 values[5], order[5];
    int n;
    u8 total, action, max, index;
    u16 actions = box->queuedApricorns;
    int i, j;
    u8 reduce;
    ApricornJuice_GetFlavors(&box->juice, (u8 *)values);
    for (n = 0; n < 5; n++) {
        reduce = 0;
        action = actions & APRICORN_QUEUE_SLOT_MASK;
        if (action == 0) {
            break;
        }
        total = 0;
        index = 0;
        max = 0;
        action--;
        for (i = 0; i < 5; i++) {
            order[i] = i;
        }
        for (i = 0; i < 2; i++) {
            for (j = i + 1; j < 5; j++) {
                s8 tmp;
                if (values[order[i]] > values[order[j]] || (values[order[i]] == values[order[j]] && order[i] < order[j])) {
                    continue;
                }
                tmp = order[i];
                order[i] = order[j];
                order[j] = tmp;
            }
        }
        {
            s8 value;
            const s8 *row;
            s8 *v;
            s8 change;
            s8 old;
            row = sApricornFlavorDeltas[action];
            v = &values[0];
            for (i = 0; i < 5; i++) {
                change = *row;
                old = *v;
                value = old + change;
                if (change > 0 && values[order[0]] != 0 && order[0] != i && values[order[1]] != 0 && order[1] != i) {
                    reduce = 1;
                }
                if (value >= 63) {
                    value = 63;
                } else if (value < 0) {
                    value = 0;
                }
                if ((action == 6 || value <= old) && value > max) {
                    max = value;
                    index = i;
                }
                *v = value;
                total += value;
                row++;
                v++;
            }
        }
        actions >>= APRICORN_QUEUE_SLOT_BITS;
        if (reduce) {
            if (box->juice.mildness < 10) {
                box->juice.mildness = 0;
            } else {
                box->juice.mildness -= 10;
            }
        }
        if (action != 5 && total > 100) {
            values[index] -= total - 100;
        }
    }
    for (i = 0; i < APRICORN_JUICE_FLAVOR_COUNT; i++) {
        box->juice.flavors[i] = values[i];
    }
    box->juiceServings = 3;
    box->queuedApricorns = 0;
}

static void ApricornJuice_GetFlavors(ApricornJuice *data, u8 *out) {
    int i;
    for (i = 0; i < APRICORN_JUICE_FLAVOR_COUNT; i++) {
        out[i] = data->flavors[i];
    }
}

static u8 GetJuiceFlavorLevel(int type, u8 value) {
    if (value == 0) {
        return 0;
    }
    switch (type) {
    case 0:
        if (value > 62) {
            return 6;
        }
        if (value > 50) {
            return 5;
        }
        if (value > 40) {
            return 4;
        }
        if (value > 30) {
            return 3;
        }
        if (value > 20) {
            return 2;
        }
        if (value != 0) {
            return 1;
        }
        break;
    case 1:
        if (value > 40) {
            return 4;
        }
        if (value > 30) {
            return 3;
        }
        if (value > 20) {
            return 2;
        }
        if (value != 0) {
            return 1;
        }
        break;
    case 2:
        if (value > 20) {
            return 3;
        }
        if (value > 10) {
            return 2;
        }
        if (value != 0) {
            return 1;
        }
        break;
    }
    return 0;
}

static void PackJuiceFlavor(ApricornJuiceEntry *entry, FlavorPair *pair, int type) {
    entry->stat = pair->id;
    entry->amount = pair->value;
    entry->strength = GetJuiceFlavorLevel((u8)type, pair->value);
}

static void ClearApricornJuiceRecord(ApricornRecord *record) {
    MI_CpuFill8(record, 0, sizeof(ApricornRecord));
    ClearApricornJuice(&record->data);
    StringFillEOS(record->name, NELEMS(record->name));
}
