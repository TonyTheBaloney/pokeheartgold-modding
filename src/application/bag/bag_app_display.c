#include "global.h"

#include "constants/items.h"
#include "constants/sndseq.h"

#include "application/bag/bag_app.h"
#include "msgdata/msg/msg_0010.h"

#include "bag.h"
#include "bg_window.h"
#include "font.h"
#include "gf_gfx_loader.h"
#include "gf_gfx_planes.h"
#include "heap.h"
#include "item.h"
#include "message_format.h"
#include "move.h"
#include "msgdata.h"
#include "options.h"
#include "player_data.h"
#include "render_text.h"
#include "render_window.h"
#include "sound.h"
#include "sound_playback.h"
#include "sprite_system.h"
#include "string_util.h"
#include "text.h"
#include "type_icon_resources.h"
#include "vram_transfer_manager.h"
#include "yes_no_prompt.h"

// Bag application: item list, message boxes, quantity and money windows, sprites (cursor, item icons,
// pocket tabs, buttons).

// Cursor sprite position, animation and palette of each button, move-item slot and quantity button.
typedef struct BagAppCursorPos {
    u8 x;
    u8 y;
    u8 anim;
    u8 palette;
} BagAppCursorPos;

extern const u8 gListPocketCapacities[];
extern const BagAppCursorPos gBagAppCursorPositions[];
extern const BagAppCursorPos gBagAppMoveCursorPositions[];
extern const BagAppCursorPos gBagAppQuantityCursorPositions[];
extern const SpriteResourceCountsListUnion gBagSpriteResourceCounts;
extern const OamManagerParam gBagOamManagerParam;
extern const OamCharTransferParam gBagOamCharTransferParam;
extern const ManagedSpriteTemplate gBagSpriteTemplates[];
extern const int gQuantityButtonCounts[];
extern const int gHiddenQuantityButtonCounts[];
extern const int gHiddenQuantityButtons[][4];
extern const int gQuantityButtonSprites[][6];
extern const int gQuantityButtonAnims[][6];

static void BagApp_DrawRegisteredItemIconOnWindow(BagApp *app, Window *window, int y, BOOL secondSlot);
static BOOL BagApp_PrintMessageCallback(TextPrinterTemplate *printer, u16 event);
static int BagViewPocket_GetIndexWithAtMostXNonEmptySlots(BagViewPocket *pocket, int pocketId, int n);
static void BagApp_PrintItemNameAndMaybeQuantityOnWindow(BagApp *app, Window *window, String *name, BagViewPocket *pocket, int index);
static void PrintItemQuantityOnWindow(MessageFormat *msgFormat, MsgData *msgData, Window *window, int quantity);
static void BagApp_ReplaceItemIconResObjs(BagApp *app, int slot, u16 itemId);
static void BagApp_DrawTMHMMoveDetails(BagApp *app, u16 itemId, BOOL show);
static void BagApp_InitSpriteSystem(BagApp *app);
static void BagApp_LoadSpriteResObjs(BagApp *app);
static void BagApp_CreateSprites(BagApp *app);
static void BagApp_DPPtPocketSwitchPressedButtonAnim_Run(BagApp *app);
static void BagApp_UpdatePageNavArrowSpritesVisibility(BagApp *app);

NarcId GetMoveCategoryIconGfxNarcId(void);

static void BagApp_DrawRegisteredItemIconOnWindow(BagApp *app, Window *window, int y, BOOL secondSlot) {
    NNSG2dCharacterData *charData;
    void *buffer = BagApp_GetHMAndRegisteredIconNCGR(app, &charData);
    if (secondSlot == FALSE) {
        BlitBitmapRectToWindow(window, charData->pRawData, 24, 0, 104, 16, 0, (u16)y, 40, 16);
    } else {
        BlitBitmapRectToWindow(window, charData->pRawData, 64, 0, 104, 16, 0, (u16)y, 40, 16);
    }
    Heap_FreeExplicit(HEAP_ID_6, buffer);
}

void BagApp_LoadContextMenuStrings(BagApp *app) {
    app->menuStrings[0] = NewString_ReadMsgData(app->msgData, msg_0010_00000);
    app->menuStrings[1] = NewString_ReadMsgData(app->msgData, msg_0010_00006);
    app->menuStrings[2] = NewString_ReadMsgData(app->msgData, msg_0010_00016);
    app->menuStrings[3] = NewString_ReadMsgData(app->msgData, msg_0010_00098);
    app->menuStrings[4] = NewString_ReadMsgData(app->msgData, msg_0010_00099);
    app->menuStrings[5] = NewString_ReadMsgData(app->msgData, msg_0010_00001);
    app->menuStrings[6] = NewString_ReadMsgData(app->msgData, msg_0010_00002);
    app->menuStrings[7] = NewString_ReadMsgData(app->msgData, msg_0010_00018);
    app->menuStrings[8] = NewString_ReadMsgData(app->msgData, msg_0010_00003);
    app->menuStrings[9] = NewString_ReadMsgData(app->msgData, msg_0010_00004);
    app->menuStrings[10] = NewString_ReadMsgData(app->msgData, msg_0010_00005);
    app->menuStrings[11] = NewString_ReadMsgData(app->msgData, msg_0010_00008);
    app->menuStrings[12] = NewString_ReadMsgData(app->msgData, msg_0010_00075);
    app->menuStrings[13] = NewString_ReadMsgData(app->msgData, msg_0010_00086);
    app->menuStrings[14] = NewString_ReadMsgData(app->msgData, msg_0010_00000);
    app->menuStrings[15] = NewString_ReadMsgData(app->msgData, msg_0010_00128);
}

void BagApp_UnloadContextMenuStrings(BagApp *app) {
    u16 i;
    for (i = 0; i < 16; i++) {
        String_Delete(app->menuStrings[i]);
    }
}

void BagApp_DrawContextMenuTopScreen(BagApp *app, const u8 *actions, int count) {
    BagViewPocket *pocket;
    String *template, *string;

    if (app->bagView->pockets[app->bagView->pocketIndex].pocketId == POCKET_TMHMS) {
        FillWindowPixelBuffer(&app->windows[1], 0);
        BagApp_PrintTMHMDetails(app, app->bagView->itemId);
        ScheduleWindowCopyToVram(&app->windows[0]);
        BagApp_DrawTMHMMoveDetails(app, app->bagView->itemId, TRUE);
        BagApp_DrawTopScreenUI(app, 0);
    }
    DrawFrameAndWindow2(&app->windows[2], TRUE, 0x3E2, 12);
    FillWindowPixelBuffer(&app->windows[2], 15);
    pocket = &app->bagView->pockets[app->bagView->pocketIndex];
    if (app->bagView->mode == 6 && IsBerryOrMulch(pocket->pocketId, app->bagView->itemId) == FALSE) {
        template = NewString_ReadMsgData(app->msgData, msg_0010_00106);
    } else {
        template = NewString_ReadMsgData(app->msgData, msg_0010_00043);
    }
    string = String_New(108, HEAP_ID_6);
    BagApp_BufferItemName(app, pocket->scroll + app->cursorButton - 8, 0);
    StringExpandPlaceholders(app->msgFormat, string, template);
    AddTextPrinterParameterized(&app->windows[2], FONT_MESSAGE, string, 0, 0, TEXT_SPEED_NOTRANSFER, NULL);
    String_Delete(string);
    String_Delete(template);
    ScheduleWindowCopyToVram(&app->windows[2]);
}

void BagApp_PrintItemDescriptionOnWindow(BagApp *app, Window *window, u32 itemId) {
    FillWindowPixelBuffer(window, 0);
    BagApp_PrintItemDescriptionOnWindowMain0(app, itemId);
    ScheduleWindowCopyToVram(window);
}

void BagApp_ClearItemDescriptionWindow(BagApp *app, Window *window) {
    FillWindowPixelBuffer(window, 0);
    ScheduleWindowCopyToVram(window);
}

void BagApp_PrintPocketDescriptionOnWindow(BagApp *app, Window *window, u32 pocket) {
    String *string = NewString_ReadMsgData(app->msgData, pocket + 120);
    FillWindowPixelBuffer(window, 0);
    AddTextPrinterParameterizedWithColor(window, FONT_SYSTEM, string, 20, 0, TEXT_SPEED_NOTRANSFER, MAKE_TEXT_COLOR(15, 14, 0), NULL);
    String_Delete(string);
    ScheduleWindowCopyToVram(window);
}

void BagApp_ClearItemActionMessageWindow(BagApp *app) {
    ClearFrameAndWindow2(&app->windows[2], TRUE);
    ClearWindowTilemapAndScheduleTransfer(&app->windows[2]);
}

void BagApp_RemoveContextMenuWindowsAndRedrawTopScreenUI(BagApp *app) {
    BagApp_ClearItemActionMessageWindow(app);
    BagApp_RemoveContextMenuWindowsInternal(app);
    BagApp_DrawTMHMMoveDetails(app, ITEM_NONE, FALSE);
}

void BagApp_RemoveContextMenuWindows(BagApp *app) {
    BagApp_RemoveContextMenuWindowsInternal(app);
}

void BagApp_PrintMoveTheItemMessage(BagApp *app) {
    FillWindowPixelBuffer(&app->windows[2], 0xFF);
    String *template = NewString_ReadMsgData(app->msgData, msg_0010_00046);
    String *string = String_New(0x82, HEAP_ID_6);
    BagApp_BufferItemName(app, app->moveSource, 0);
    StringExpandPlaceholders(app->msgFormat, string, template);
    DrawFrameAndWindow2(&app->windows[2], TRUE, 0x3E2, 12);
    AddTextPrinterParameterizedWithColor(&app->windows[2], FONT_MESSAGE, string, 0, 0, TEXT_SPEED_NOTRANSFER, MAKE_TEXT_COLOR(1, 2, 0), NULL);
    ScheduleWindowCopyToVram(&app->windows[2]);
    String_Delete(string);
    String_Delete(template);
}

void BagApp_PrintQuantityDigitWindows(BagApp *app, u32 numDigits) {
    String *string;
    u32 divisor, value, i;

    GF_ASSERT(app->quantity < 1000);
    string = String_New(2, HEAP_ID_6);
    if (numDigits == 2) {
        divisor = 10;
    } else {
        divisor = 100;
    }
    value = (u32)app->quantity;
    for (i = 0; i < numDigits; i++) {
        u32 digit = value / divisor;
        Window *window;
        String16_FormatInteger(string, (int)digit, 1, PRINTING_MODE_LEFT_ALIGN, TRUE);
        value -= digit * divisor;
        divisor /= 10;
        window = &app->dynWindows[i + 17];
        FillWindowPixelBuffer(window, 0);
        AddTextPrinterParameterizedWithColor(window, FONT_SYSTEM, string, 0, 4, TEXT_SPEED_NOTRANSFER, MAKE_TEXT_COLOR(1, 2, 0), NULL);
        ScheduleWindowCopyToVram(window);
    }
    String_Delete(string);
}

void BagApp_PrintOkToTrashItemsMessage(BagApp *app) {
    String *template = NewString_ReadMsgData(app->msgData, msg_0010_00055);
    BagView *bagView = app->bagView;
    BagViewPocket *pocket = &bagView->pockets[bagView->pocketIndex];
    if (app->quantity > 1) {
        BagApp_BufferItemNamePlural(app, pocket->scroll + app->cursorButton - 8, 0);
    } else {
        BagApp_BufferItemName(app, pocket->scroll + app->cursorButton - 8, 0);
    }
    BufferIntegerAsString(app->msgFormat, 1, app->quantity, 3, PRINTING_MODE_LEFT_ALIGN, TRUE);
    StringExpandPlaceholders(app->msgFormat, app->msgBuf, template);
    String_Delete(template);
    app->printerId = (u8)BagApp_PrintMessage(app, FALSE);
}

u8 BagApp_PrintMessage(BagApp *app, BOOL wide) {
    Window *window;
    if (wide == FALSE) {
        window = &app->windows[3];
    } else {
        GF_ASSERT(app->dynWindows[21].bgConfig != NULL);
        window = &app->dynWindows[21];
    }
    FillWindowPixelBuffer(window, 15);
    DrawFrameAndWindow2(window, TRUE, 0x3E2, 12);
    ScheduleWindowCopyToVram(window);
    TextFlags_SetCanABSpeedUpPrint(TRUE);
    TextFlags_SetAutoScrollParam(0);
    u8 speed = Options_GetTextFrameDelay(app->options);
    return AddTextPrinterParameterized(window, FONT_MESSAGE, app->msgBuf, 0, 0, speed, BagApp_PrintMessageCallback);
}

static BOOL BagApp_PrintMessageCallback(TextPrinterTemplate *printer, u16 event) {
    switch (event) {
    case 1:
        return GF_IsAnySEPlaying();
    case 2:
        return IsFanfarePlaying();
    case 3:
        PlaySE(SEQ_SE_DP_PC_LOGIN);
        break;
    case 4:
        return IsSEPlaying(SEQ_SE_DP_PC_LOGIN);
    }
    return FALSE;
}

void BagApp_CreateYesNoPrompt(BagApp *app) {
    YesNoPromptTemplate template;
    template.bgConfig = app->bgConfig;
    template.bgId = GF_BG_LYR_SUB_1;
    template.tileStart = 129;
    template.plttSlot = 9;
    template.x = 25;
    template.y = 6;
    template.ignoreTouchFlag = FALSE;
    template.initialCursorPos = 0;
    template.initialCursorPos = 0;
    template.shapeParam = 0;
    app->yesNoPrompt = YesNoPrompt_Create(HEAP_ID_6);
    YesNoPrompt_InitFromTemplate(app->yesNoPrompt, &template);
}

void BagApp_DestroyYesNoPrompt(BagApp *app) {
    YesNoPrompt_Destroy(app->yesNoPrompt);
}

void BagApp_PrintSaleTotalInWindow(BagApp *app) {
    String *template;
    Window *window = &app->dynWindows[23];

    FillWindowPixelBuffer(window, 0);
    template = NewString_ReadMsgData(app->msgData, msg_0010_00083);
    BufferIntegerAsString(app->msgFormat, 0, app->sellPrice * app->quantity, 6, PRINTING_MODE_RIGHT_ALIGN, TRUE);
    StringExpandPlaceholders(app->msgFormat, app->msgBuf, template);
    FontID_String_GetWidth(FONT_SYSTEM, app->msgBuf, 0);
    AddTextPrinterParameterizedWithColor(window, FONT_SYSTEM, app->msgBuf, 0, 4, TEXT_SPEED_NOTRANSFER, MAKE_TEXT_COLOR(1, 2, 0), NULL);
    ScheduleWindowCopyToVram(window);
    String_Delete(template);
}

void BagApp_PrintMoneyOnWindow(BagApp *app, BOOL skipLabel) {
    String *string = String_New(0x100, HEAP_ID_6);
    Window *window = &app->dynWindows[22];
    if (skipLabel == FALSE) {
        FillWindowPixelBuffer(window, 0);
        String *label = NewString_ReadMsgData(app->msgData, msg_0010_00080);
        AddTextPrinterParameterizedWithColor(window, FONT_SYSTEM, label, 4, 0, TEXT_SPEED_NOTRANSFER, MAKE_TEXT_COLOR(1, 2, 0), NULL);
        String_Delete(label);
    } else {
        FillWindowPixelRect(window, 0, 0, 16, 72, 16);
    }
    String *template = NewString_ReadMsgData(app->msgData, msg_0010_00081);
    u32 money = PlayerProfile_GetMoney(app->profile);
    BufferIntegerAsString(app->msgFormat, 0, money, 6, PRINTING_MODE_RIGHT_ALIGN, TRUE);
    StringExpandPlaceholders(app->msgFormat, string, template);
    u32 width = FontID_String_GetWidth(FONT_SYSTEM, string, 0);
    AddTextPrinterParameterizedWithColor(window, FONT_SYSTEM, string, 68 - (width + 8), 16, TEXT_SPEED_NOTRANSFER, MAKE_TEXT_COLOR(1, 2, 0), NULL);
    ScheduleWindowCopyToVram(window);
    String_Delete(template);
    String_Delete(string);
}

void BagApp_DrawPoffinCountMsgBox_DPPt(BagApp *app) {
    Window *window = &app->windows[5];
    FillWindowPixelBuffer(window, 15);
    DrawFrameAndWindow1(window, TRUE, 0x3F7, 14);
    String *string = NewString_ReadMsgData(app->msgData, msg_0010_00115);
    AddTextPrinterParameterized(window, FONT_SYSTEM, string, 0, 0, TEXT_SPEED_NOTRANSFER, NULL);
    String_Delete(string);
    string = NewString_ReadMsgData(app->msgData, msg_0010_00116);
    BufferIntegerAsString(app->msgFormat, 0, 0, 3, PRINTING_MODE_RIGHT_ALIGN, TRUE);
    StringExpandPlaceholders(app->msgFormat, app->msgBuf, string);
    String_Delete(string);
    u32 width = FontID_String_GetWidth(FONT_SYSTEM, app->msgBuf, 0);
    AddTextPrinterParameterized(window, FONT_SYSTEM, app->msgBuf, 88 - width, 16, TEXT_SPEED_NOTRANSFER, NULL);
    ScheduleWindowCopyToVram(window);
}

void BagApp_PrintCancel(BagApp *app, BOOL left) {
    String *string = NewString_ReadMsgData(app->msgData, msg_0010_00008);
    FillWindowPixelBuffer(&app->windows[7], 0);
    if (left == FALSE) {
        u32 width = FontID_String_GetWidth(FONT_SYSTEM, string, 0);
        AddTextPrinterParameterizedWithColor(&app->windows[7], FONT_SYSTEM, string, ((48 - width) / 2) + 8, 0, TEXT_SPEED_NOTRANSFER, MAKE_TEXT_COLOR(15, 14, 0), NULL);
    } else {
        AddTextPrinterParameterizedWithColor(&app->windows[7], FONT_SYSTEM, string, 5, 0, TEXT_SPEED_NOTRANSFER, MAKE_TEXT_COLOR(15, 14, 0), NULL);
    }
    ScheduleWindowCopyToVram(&app->windows[7]);
    String_Delete(string);
}

static int BagViewPocket_GetIndexWithAtMostXNonEmptySlots(BagViewPocket *pocket, int pocketId, int n) {
    int i;
    int count;
    count = 0;
    for (i = 0; i < gListPocketCapacities[pocketId]; i++) {
        if (pocket->slots[i].id != ITEM_NONE && pocket->slots[i].quantity != 0) {
            count++;
            if (count == n + 1) {
                break;
            }
        }
    }
    return i;
}

// The item list alternates between two banks of six windows, so a page is drawn before the old one is cleared.
void BagApp_RedrawItemNameWindows(BagApp *app, int scroll, int unused, BOOL dim) {
    int i, k, count;
    BagViewPocket *pocket;
    int limit;
    u8 first, last;

    pocket = &app->bagView->pockets[app->bagView->pocketIndex];
    limit = pocket->itemCount - pocket->scroll;
    if (limit > 6) {
        limit = 6;
    }
    if (app->listBank == 0) {
        first = 0;
        last = 6;
    } else {
        first = 6;
        last = 0;
    }
    app->listBank ^= 1;
    BagApp_AddItemNameWindows(app);
    for (i = 0; i < 6; i++) {
        FillWindowPixelBuffer(&app->dynWindows[first + i], 0);
        ClearWindowTilemapAndScheduleTransfer(&app->dynWindows[last + i]);
    }
    count = 0;
    k = BagViewPocket_GetIndexWithAtMostXNonEmptySlots(pocket, app->bagView->pocketIndex, scroll);
    for (; k < gListPocketCapacities[app->bagView->pocketIndex]; k++) {
        if (pocket->slots[k].id != ITEM_NONE && pocket->slots[k].quantity != 0) {
            if (dim == FALSE) {
                BagApp_PrintItemNameAndMaybeQuantityOnWindow(app, &app->dynWindows[first + count], app->itemNames[k], pocket, k);
            } else if (k == app->moveSource) {
                BagApp_PrintItemNameAndMaybeQuantityOnWindow(app, &app->dynWindows[first + count], app->itemNames[k], pocket, k);
            } else {
                AddTextPrinterParameterizedWithColor(&app->dynWindows[first + count], FONT_SYSTEM, app->itemNames[k], 0, 16, TEXT_SPEED_NOTRANSFER, MAKE_TEXT_COLOR(1, 2, 0), NULL);
            }
            if (++count >= limit) {
                break;
            }
        }
    }
    for (i = 0; i < 6; i++) {
        ScheduleWindowCopyToVram(&app->dynWindows[first + i]);
    }
}

void BagApp_SwitchItemButtonWindowsToContextMenuMode(BagApp *app, s32 scroll, s32 slot) {
    u32 index = slot;
    BagView *bagView = app->bagView;
    BagViewPocket *pocket = &bagView->pockets[bagView->pocketIndex];

    index += scroll;

    s32 i = 0;
    Window *window = &app->dynWindows[0];

    for (; i < 6; i++) {
        ClearWindowTilemapAndScheduleTransfer(window);
        window++;
    }
    BagApp_RemoveItemNameWindows(app);
    ClearWindowTilemapAndScheduleTransfer(&app->windows[6]);
    BagApp_ShowContextMenuWindows(app);
    BagApp_PrintItemNameAndMaybeQuantityOnWindow(app, &app->dynWindows[12], app->itemNames[index], pocket, index);
    ScheduleWindowCopyToVram(&app->dynWindows[12]);
}

void BagApp_ClearSelectedItemWindow(BagApp *app) {
    ClearWindowTilemapAndScheduleTransfer(&app->dynWindows[12]);
}

static void BagApp_PrintItemNameAndMaybeQuantityOnWindow(BagApp *app, Window *window, String *name, BagViewPocket *pocket, int index) {
    switch (pocket->pocketId) {
    case POCKET_TMHMS:
        AddTextPrinterParameterizedWithColor(window, FONT_SYSTEM, name, 0, 0, TEXT_SPEED_NOTRANSFER, MAKE_TEXT_COLOR(1, 2, 0), NULL);
        BagApp_PrintTMorHMNumberOnWindow(app, window, &pocket->slots[index], 16);
        if (pocket->slots[index].id >= ITEM_TM01 && pocket->slots[index].id <= ITEM_TM92) {
            PrintItemQuantityOnWindow(app->msgFormat, app->msgData, window, pocket->slots[index].quantity);
        }
        break;
    case POCKET_KEY_ITEMS:
        AddTextPrinterParameterizedWithColor(window, FONT_SYSTEM, name, 0, 0, TEXT_SPEED_NOTRANSFER, MAKE_TEXT_COLOR(1, 2, 0), NULL);
        if (pocket->slots[index].id == Bag_GetRegisteredItem1(app->bag)) {
            BagApp_DrawRegisteredItemIconOnWindow(app, window, 16, FALSE);
        }
        if (pocket->slots[index].id == Bag_GetRegisteredItem2(app->bag)) {
            BagApp_DrawRegisteredItemIconOnWindow(app, window, 16, TRUE);
        }
        break;
    default:
        AddTextPrinterParameterizedWithColor(window, FONT_SYSTEM, name, 0, 0, TEXT_SPEED_NOTRANSFER, MAKE_TEXT_COLOR(1, 2, 0), NULL);
        PrintItemQuantityOnWindow(app->msgFormat, app->msgData, window, pocket->slots[index].quantity);
        break;
    }
}

static void PrintItemQuantityOnWindow(MessageFormat *msgFormat, MsgData *msgData, Window *window, int quantity) {
    BufferIntegerAsString(msgFormat, 0, quantity, 3, PRINTING_MODE_LEFT_ALIGN, TRUE);
    String *string = ReadMsgData_ExpandPlaceholders(msgFormat, msgData, 87, HEAP_ID_6);
    AddTextPrinterParameterizedWithColor(window, FONT_SYSTEM, string, 48, 16, TEXT_SPEED_NOTRANSFER, MAKE_TEXT_COLOR(1, 2, 0), NULL);
    String_Delete(string);
}

void BagApp_PrintPageCounter(BagApp *app, s32 itemCount, s32 scroll, s32 slot) {
    s32 page = (scroll + slot) / 6;
    s32 numPages;
    if (itemCount == 0) {
        numPages = 1;
    } else {
        numPages = (itemCount + 5) / 6;
    }
    FillWindowPixelBuffer(&app->windows[6], 0);
    BufferIntegerAsString(app->msgFormat, 0, page + 1, 3, PRINTING_MODE_RIGHT_ALIGN, TRUE);
    BufferIntegerAsString(app->msgFormat, 1, numPages, 3, PRINTING_MODE_RIGHT_ALIGN, TRUE);
    String *string = ReadMsgData_ExpandPlaceholders(app->msgFormat, app->msgData, msg_0010_00022, HEAP_ID_6);
    AddTextPrinterParameterizedWithColor(&app->windows[6], FONT_SYSTEM, string, 0, 0, TEXT_SPEED_NOTRANSFER, MAKE_TEXT_COLOR(15, 1, 0), NULL);
    ScheduleWindowCopyToVram(&app->windows[6]);
    String_Delete(string);
}

void BagApp_PrintContextMenuStringOnWindowCentered(Window *window, String **strings, u8 action) {
    FillWindowPixelBuffer(window, 0);
    if (action != 0xFF) {
        String **string = &strings[action];
        u32 width;
        width = GetWindowWidth(window);
        u32 textWidth = FontID_String_GetWidth(FONT_SYSTEM, *string, 0);
        AddTextPrinterParameterizedWithColor(window, FONT_SYSTEM, *string, ((width * 8) - textWidth) / 2, 0, TEXT_SPEED_NOTRANSFER, MAKE_TEXT_COLOR(15, 14, 0), NULL);
    }
    ScheduleWindowCopyToVram(window);
}

void BagApp_ClearFourWindowsAt(Window *windows) {
    s32 i;
    for (i = 0; i < 4; i++) {
        ClearWindowTilemapAndScheduleTransfer(&windows[i]);
    }
}

void BagApp_PrintTrashContextOptionOnWindow(BagApp *app) {
    AddTextPrinterParameterizedWithColor(&app->dynWindows[20], FONT_SYSTEM, app->menuStrings[5], 5, 0, TEXT_SPEED_NOTRANSFER, MAKE_TEXT_COLOR(15, 14, 0), NULL);
    ScheduleWindowCopyToVram(&app->dynWindows[20]);
}

void BagApp_PrintSellContextOptionOnWindow(BagApp *app) {
    AddTextPrinterParameterizedWithColor(&app->dynWindows[20], FONT_SYSTEM, app->menuStrings[13], 5, 0, TEXT_SPEED_NOTRANSFER, MAKE_TEXT_COLOR(15, 14, 0), NULL);
    ScheduleWindowCopyToVram(&app->dynWindows[20]);
}

void BagApp_ClearTextOnSellOrTrashButton(BagApp *app) {
    ClearWindowTilemapAndScheduleTransfer(&app->dynWindows[20]);
}

void BagApp_ClearTextOnCancelButton(BagApp *app) {
    ClearWindowTilemapAndScheduleTransfer(&app->windows[7]);
}

void BagApp_InitSpriteRendererAndSystem(BagApp *app) {
    GfGfx_EngineATogglePlanes(GX_PLANEMASK_OBJ, GF_PLANE_TOGGLE_ON);
    GfGfx_EngineBTogglePlanes(GX_PLANEMASK_OBJ, GF_PLANE_TOGGLE_ON);
    GF_CreateVramTransferManager(32, HEAP_ID_6);
    BagApp_InitSpriteSystem(app);
    BagApp_LoadSpriteResObjs(app);
    BagApp_CreateSprites(app);
    G2dRenderer_SetSubSurfaceCoords(SpriteSystem_GetRenderer(app->spriteSystem), 0, FX32_CONST(256));
}

void BagApp_FreeSpriteSystem(BagApp *app) {
    u32 i;
    for (i = 0; i < NELEMS(app->sprites); i++) {
        Sprite_DeleteAndFreeResources(app->sprites[i]);
    }
    SpriteSystem_FreeResourcesAndManager(app->spriteSystem, app->spriteManager);
    SpriteSystem_Free(app->spriteSystem);
    Heap_Free(app->objPaletteBuffer);
}

void BagApp_UpdateSpriteAnims(BagApp *app) {
    u32 i;
    for (i = 0; i < NELEMS(app->sprites); i++) {
        ManagedSprite_TickFrame(app->sprites[i]);
    }
}

static void BagApp_ReplaceItemIconResObjs(BagApp *app, int slot, u16 itemId) {
    SpriteSystem_ReplaceCharResObj(app->spriteSystem, app->spriteManager, NARC_itemtool_itemdata_item_icon, GetItemIndexMapping(itemId, ITEMNARC_NCGR), FALSE, slot + 0xC0FC);
    SpriteSystem_ReplacePlttResObj(app->spriteSystem, app->spriteManager, NARC_itemtool_itemdata_item_icon, GetItemIndexMapping(itemId, ITEMNARC_NCLR), FALSE, slot + 0xC0FB);
}

void BagApp_StartPocketSwitchPressedButtonAnim_DPPt(BagApp *app) {
    app->unk_64B = 0;
    app->unk_648 = 1;
}

void BagApp_StepPocketSwitchPressedButtonAnim_DPPt(BagApp *app) {
    switch (app->unk_648) {
    case 1:
        BagApp_DPPtPocketSwitchPressedButtonAnim_Run(app);
        break;
    case 0:
        break;
    }
}

static void BagApp_DrawTMHMMoveDetails(BagApp *app, u16 itemId, BOOL show) {
    u16 move;
    u16 type;
    u16 category;
    NarcId narc;

    ManagedSprite_SetDrawFlag(app->sprites[7], show);
    ManagedSprite_SetDrawFlag(app->sprites[8], show);
    if (show != FALSE) {
        move = TMHMGetMove(itemId);
        type = GetMoveAttr(move, MOVEATTR_TYPE);
        category = GetMoveAttr(move, MOVEATTR_CLASS);
        narc = TypeIconGfx_GetNarcId();
        SpriteSystem_ReplaceCharResObj(app->spriteSystem, app->spriteManager, narc, TypeIconGfx_GetCharFileId(type), TRUE, 0xC103);
        ManagedSprite_SetPaletteOverride(app->sprites[7], TypeIconGfx_GetPlttOverride(type) + 4);
        narc = GetMoveCategoryIconGfxNarcId();
        SpriteSystem_ReplaceCharResObj(app->spriteSystem, app->spriteManager, narc, GetMoveCategoryIconGfxCharFileId(category), TRUE, 0xC104);
        ManagedSprite_SetPaletteOverride(app->sprites[8], GetMoveCategoryIconGfxPlttOverride(category) + 4);
    }
}

static void BagApp_InitSpriteSystem(BagApp *app) {
    SpriteResourceCountsListUnion counts = gBagSpriteResourceCounts;
    app->spriteSystem = SpriteSystem_Alloc(HEAP_ID_6);
    app->spriteManager = SpriteManager_New(app->spriteSystem);
    OamManagerParam oamManagerParam = gBagOamManagerParam;
    OamCharTransferParam oamCharTransferParam = gBagOamCharTransferParam;
    SpriteSystem_Init(app->spriteSystem, &oamManagerParam, &oamCharTransferParam, 32);
    SpriteSystem_InitSprites(app->spriteSystem, app->spriteManager, NELEMS(app->sprites));
    SpriteSystem_InitManagerWithCapacities(app->spriteSystem, app->spriteManager, &counts);
}

static void BagApp_LoadSpriteResObjs(BagApp *app) {
    int i;

    SpriteSystem_LoadCharResObj(app->spriteSystem, app->spriteManager, NARC_a_0_1_5, 26, FALSE, NNS_G2D_VRAM_TYPE_2DMAIN, 0xC0F9);
    SpriteSystem_LoadCharResObj(app->spriteSystem, app->spriteManager, NARC_a_0_1_5, 6, FALSE, NNS_G2D_VRAM_TYPE_2DMAIN, 0xC0FA);
    SpriteSystem_LoadCharResObj(app->spriteSystem, app->spriteManager, NARC_a_0_1_5, 51, FALSE, NNS_G2D_VRAM_TYPE_2DSUB, 0xC0FB);
    SpriteSystem_LoadCharResObj(app->spriteSystem, app->spriteManager, NARC_a_0_6_0, 4, FALSE, NNS_G2D_VRAM_TYPE_2DMAIN, 0xC102);
    for (i = 0; i < 6; i++) {
        SpriteSystem_LoadCharResObj(app->spriteSystem, app->spriteManager, NARC_itemtool_itemdata_item_icon, GetItemIndexMapping(ITEM_NONE, ITEMNARC_NCGR), FALSE, NNS_G2D_VRAM_TYPE_2DSUB, 0xC0FC + i);
    }
    SpriteSystem_LoadMoveTypeIconCharResObj(app->spriteSystem, app->spriteManager, NNS_G2D_VRAM_TYPE_2DMAIN, 0, 0xC103);
    SpriteSystem_LoadMoveCategoryIconCharResObj(app->spriteSystem, app->spriteManager, NNS_G2D_VRAM_TYPE_2DMAIN, 0, 0xC104);
    SpriteSystem_LoadPlttResObj(app->spriteSystem, app->spriteManager, NARC_a_0_1_5, 15, FALSE, 2, NNS_G2D_VRAM_TYPE_2DMAIN, 0xC0F9);
    SpriteSystem_LoadPlttResObj(app->spriteSystem, app->spriteManager, NARC_a_0_6_0, 10, FALSE, 2, NNS_G2D_VRAM_TYPE_2DMAIN, 0xC101);
    SpriteSystem_LoadMoveTypeAndCategoryIconsPltt(app->spriteSystem, app->spriteManager, NNS_G2D_VRAM_TYPE_2DMAIN, 0xC102);
    SpriteSystem_LoadPlttResObj(app->spriteSystem, app->spriteManager, NARC_a_0_1_5, 47, FALSE, 10, NNS_G2D_VRAM_TYPE_2DSUB, 0xC0FA);
    for (i = 0; i < 6; i++) {
        SpriteSystem_LoadPlttResObj(app->spriteSystem, app->spriteManager, NARC_itemtool_itemdata_item_icon, GetItemIndexMapping(ITEM_NONE, ITEMNARC_NCLR), FALSE, 1, NNS_G2D_VRAM_TYPE_2DSUB, 0xC0FB + i);
    }
    SpriteSystem_LoadCellResObj(app->spriteSystem, app->spriteManager, NARC_a_0_1_5, 25, FALSE, 0xC0F9);
    SpriteSystem_LoadCellResObj(app->spriteSystem, app->spriteManager, NARC_a_0_1_5, 5, FALSE, 0xC0FA);
    SpriteSystem_LoadCellResObj(app->spriteSystem, app->spriteManager, NARC_a_0_1_5, 49, FALSE, 0xC0FB);
    SpriteSystem_LoadCellResObj(app->spriteSystem, app->spriteManager, NARC_itemtool_itemdata_item_icon, GetItemIconCell(), FALSE, 0xC0FC);
    SpriteSystem_LoadCellResObj(app->spriteSystem, app->spriteManager, NARC_a_0_6_0, 5, FALSE, 0xC0FD);
    SpriteSystem_LoadAnimResObj(app->spriteSystem, app->spriteManager, NARC_a_0_1_5, 21, FALSE, 0xC0F9);
    SpriteSystem_LoadAnimResObj(app->spriteSystem, app->spriteManager, NARC_a_0_1_5, 24, FALSE, 0xC0FA);
    SpriteSystem_LoadAnimResObj(app->spriteSystem, app->spriteManager, NARC_a_0_1_5, 4, FALSE, 0xC0FB);
    SpriteSystem_LoadAnimResObj(app->spriteSystem, app->spriteManager, NARC_a_0_1_5, 50, FALSE, 0xC0FC);
    SpriteSystem_LoadAnimResObj(app->spriteSystem, app->spriteManager, NARC_itemtool_itemdata_item_icon, GetItemIconAnim(), FALSE, 0xC0FD);
    SpriteSystem_LoadAnimResObj(app->spriteSystem, app->spriteManager, NARC_a_0_6_0, 6, FALSE, 0xC0FE);
    SpriteSystem_LoadMoveTypeAndCategoryIconsCellAndAnim(app->spriteSystem, app->spriteManager, 0xC0FE, 0xC0FF);
    app->objPaletteBuffer = GfGfxLoader_GetPlttData(NARC_a_0_1_5, 48, &app->objPalette, HEAP_ID_6);
}

static void BagApp_CreateSprites(BagApp *app) {
    const ManagedSpriteTemplate *template = gBagSpriteTemplates;
    u32 i;

    for (i = 0; i < NELEMS(app->sprites); i++) {
        app->sprites[i] = SpriteSystem_NewSpriteWithYOffset(app->spriteSystem, app->spriteManager, template, FX32_CONST(256));
        template ++;
    }
    ManagedSprite_SetPriority(app->sprites[19], 1);
    for (i = 0; i < 4; i++) {
        ManagedSprite_SetPriority(app->sprites[28 + i], 1);
    }
    for (i = 0; i < 8; i++) {
        ManagedSprite_SetPriority(app->sprites[9 + i], 1);
    }
    BagApp_SetPocketIconsDrawFlag(app, TRUE);
    ManagedSprite_SetDrawFlag(app->sprites[0], FALSE);
    ManagedSprite_SetDrawFlag(app->sprites[7], FALSE);
    ManagedSprite_SetDrawFlag(app->sprites[8], FALSE);
    for (i = 0; i < 4; i++) {
        ManagedSprite_SetDrawFlag(app->sprites[28 + i], FALSE);
    }
    for (i = 0; i < 6; i++) {
        ManagedSprite_SetDrawFlag(app->sprites[32 + i], FALSE);
    }
    ManagedSprite_SetDrawFlag(app->sprites[38], FALSE);
    ManagedSprite_SetPriority(app->sprites[38], 1);
}

static void BagApp_DPPtPocketSwitchPressedButtonAnim_Run(BagApp *app) {
    app->unk_648 = 0;
}

void BagApp_SetCursorSpritePos_PocketsItemsContext(BagApp *app, s32 button) {
    ManagedSprite_SetPositionXYWithSubscreenOffset(app->sprites[20], gBagAppCursorPositions[button].x, gBagAppCursorPositions[button].y, FX32_CONST(256));
    ManagedSprite_SetAnim(app->sprites[20], gBagAppCursorPositions[button].anim);
    ManagedSprite_SetPaletteOverride(app->sprites[20], gBagAppCursorPositions[button].palette);
    ManagedSprite_SetDrawFlag(app->sprites[20], TRUE);
}

void BagApp_HideCursorSprite(BagApp *app) {
    ManagedSprite_SetDrawFlag(app->sprites[20], FALSE);
}

void BagApp_SetCursorSpritePos_ItemsOnly(BagApp *app, int slot) {
    GF_ASSERT(slot < 9);
    if (slot == 8) {
        ManagedSprite_SetAnim(app->sprites[20], gBagAppMoveCursorPositions[slot].anim);
    } else {
        BagView *bagView = app->bagView;
        BagViewPocket *pocket = &bagView->pockets[bagView->pocketIndex];
        int index = pocket->scroll + slot;
        if (index == app->moveSource) {
            ManagedSprite_SetAnim(app->sprites[20], 10);
        } else if (index >= pocket->itemCount) {
            ManagedSprite_SetAnim(app->sprites[20], 40);
        } else {
            ManagedSprite_SetAnim(app->sprites[20], 20);
        }
    }
    ManagedSprite_SetPositionXYWithSubscreenOffset(app->sprites[20], gBagAppMoveCursorPositions[slot].x, gBagAppMoveCursorPositions[slot].y, FX32_CONST(256));
    ManagedSprite_SetPaletteOverride(app->sprites[20], gBagAppMoveCursorPositions[slot].palette);
}

void BagApp_SetCursorSpritePos_QuantitySelect(BagApp *app, s32 index) {
    GF_ASSERT(index < 8);
    ManagedSprite_SetPositionXYWithSubscreenOffset(app->sprites[20], gBagAppQuantityCursorPositions[index].x, gBagAppQuantityCursorPositions[index].y, FX32_CONST(256));
    ManagedSprite_SetAnim(app->sprites[20], gBagAppQuantityCursorPositions[index].anim);
    ManagedSprite_SetPaletteOverride(app->sprites[20], gBagAppQuantityCursorPositions[index].palette);
}

void BagApp_LoadObjPaletteByPocket(BagApp *app, int pocket) {
    if (pocket <= 7) {
        u16 *palette = app->objPalette->pRawData;
        GXS_LoadOBJPltt(&palette[0x80], 0, 0x100);
        GXS_LoadOBJPltt(&palette[pocket * 16], pocket * 32, 32);
    }
}

void BagApp_UpdateItemButtonsDrawState(BagApp *app, int count, int movingSlot, BOOL hideLast) {
    int i;
    if (count == 0) {
        for (i = 0; i < 6; i++) {
            ManagedSprite_SetDrawFlag(app->sprites[21 + i], FALSE);
        }
        ManagedSprite_SetDrawFlag(app->sprites[27], FALSE);
        return;
    }
    i = 0;
    do {
        if (i < count) {
            ManagedSprite_SetDrawFlag(app->sprites[21 + i], TRUE);
        } else {
            ManagedSprite_SetDrawFlag(app->sprites[21 + i], FALSE);
        }
        i++;
    } while (i < 6);
    if (movingSlot >= 0) {
        movingSlot += 21;
        ManagedSprite_SetDrawFlag(app->sprites[movingSlot], FALSE);
    }
    if (hideLast) {
        ManagedSprite_SetDrawFlag(app->sprites[27], FALSE);
    }
}

static void BagApp_UpdatePageNavArrowSpritesVisibility(BagApp *app) {
    BagView *bagView = app->bagView;
    if (bagView->pockets[bagView->pocketIndex].itemCount <= 6) {
        ManagedSprite_SetDrawFlag(app->sprites[17], FALSE);
        ManagedSprite_SetDrawFlag(app->sprites[18], FALSE);
    } else {
        ManagedSprite_SetDrawFlag(app->sprites[17], TRUE);
        ManagedSprite_SetDrawFlag(app->sprites[18], TRUE);
    }
}

void BagApp_UpdateItemIconsVisibility(BagApp *app, BagViewPocket *pocket, int count, BOOL update) {
    int i;
    for (i = 0; i < 6; i++) {
        ManagedSprite_SetPositionXYWithSubscreenOffset(app->sprites[1 + i], gBagSpriteTemplates[1 + i].x, gBagSpriteTemplates[1 + i].y, FX32_CONST(256));
        if (i < count) {
            if (update) {
                BagApp_ReplaceItemIconResObjs(app, i, app->itemIds[pocket->scroll + i]);
            }
            ManagedSprite_SetDrawFlag(app->sprites[1 + i], TRUE);
        } else {
            ManagedSprite_SetDrawFlag(app->sprites[1 + i], FALSE);
        }
    }
    BagApp_UpdatePageNavArrowSpritesVisibility(app);
}

void BagApp_ShowOnlySelectedItemIcon(BagApp *app, BagViewPocket *pocket, int index) {
    int slot = -1;
    int i;
    if (pocket->scroll == (index / 6) * 6) {
        slot = index % 6;
    }
    for (i = 0; i < 6; i++) {
        ManagedSprite_SetPositionXYWithSubscreenOffset(app->sprites[1 + i], gBagSpriteTemplates[1 + i].x, gBagSpriteTemplates[1 + i].y, FX32_CONST(256));
        if (i == slot) {
            ManagedSprite_SetDrawFlag(app->sprites[1 + i], TRUE);
        } else {
            ManagedSprite_SetDrawFlag(app->sprites[1 + i], FALSE);
        }
    }
    BagApp_UpdatePageNavArrowSpritesVisibility(app);
}

void BagApp_DrawContextMenuButtonSprites(BagApp *app, const u8 *actions) {
    s32 i;
    ManagedSprite_SetDrawFlag(app->sprites[20], TRUE);
    for (i = 0; i < 4; i++) {
        if (actions[i] != 0xFF) {
            ManagedSprite_SetDrawFlag(app->sprites[28 + i], TRUE);
        } else {
            ManagedSprite_SetDrawFlag(app->sprites[28 + i], FALSE);
        }
    }
    ManagedSprite_SetDrawFlag(app->sprites[17], FALSE);
    ManagedSprite_SetDrawFlag(app->sprites[18], FALSE);
}

void BagApp_HideContextMenuIcons(BagApp *app) {
    s32 i;
    for (i = 0; i < 4; i++) {
        ManagedSprite_SetDrawFlag(app->sprites[28 + i], FALSE);
    }
}

void BagApp_CenterSelectedItemIconSprite(BagApp *app, int slot) {
    int i;
    for (i = 0; i < 6; i++) {
        if (slot != i) {
            ManagedSprite_SetDrawFlag(app->sprites[1 + i], FALSE);
        } else {
            ManagedSprite_SetPositionXYWithSubscreenOffset(app->sprites[1 + i], 86, 76, FX32_CONST(256));
        }
    }
}

// 0: all three digits can be stepped, 1: max is below 100 (hide the hundreds), 2: max is below 10 (ones only)
s32 BagApp_GetNumberWidthType(s32 max) {
    s32 ret = 0;
    if (max < 100) {
        ret = 1;
    }
    if (max < 10) {
        ret = 2;
    }
    return ret;
}

// type 2: sell (two digits), 3: trash (three digits)
void BagApp_ShowQuantitySelectSpritesUI(BagApp *app, int type, int max) {
    int i;
    int unusedDigits;

    if (type == 2 && max > 99) {
        max = 99;
    }
    for (i = 0; i < gQuantityButtonCounts[type - 2]; i++) {
        ManagedSprite_SetDrawFlag(app->sprites[32 + gQuantityButtonSprites[type - 2][i]], TRUE);
        ManagedSprite_SetAnim(app->sprites[32 + gQuantityButtonSprites[type - 2][i]], gQuantityButtonAnims[type - 2][i]);
    }
    unusedDigits = BagApp_GetNumberWidthType(max);
    if (unusedDigits != 0) {
        if (type - 2 == 0 && unusedDigits == 2) {
            ManagedSprite_SetDrawFlag(app->sprites[32], FALSE);
            ManagedSprite_SetDrawFlag(app->sprites[35], FALSE);
        } else if (type - 2 == 1) {
            for (i = 0; i < gHiddenQuantityButtonCounts[unusedDigits - 1]; i++) {
                ManagedSprite_SetDrawFlag(app->sprites[32 + gHiddenQuantityButtons[unusedDigits - 1][i]], FALSE);
            }
        }
    }
    ManagedSprite_SetDrawFlag(app->sprites[38], TRUE);
    ManagedSprite_SetAnimationFrame(app->sprites[38], 0);
    ManagedSprite_SetAnim(app->sprites[38], 37);
    ManagedSprite_SetAnimationFrame(app->sprites[19], 0);
    ManagedSprite_SetAnim(app->sprites[19], 39);
}

void BagApp_HideQuantitySelectSpritesUI(BagApp *app) {
    s32 i;
    for (i = 0; i < 6; i++) {
        ManagedSprite_SetDrawFlag(app->sprites[32 + i], FALSE);
    }
    ManagedSprite_SetDrawFlag(app->sprites[38], FALSE);
}

void BagApp_SetPocketIconsDrawFlag(BagApp *app, BOOL show) {
    u8 hasPocket[8];
    int i;

    GF_ASSERT(show == TRUE || show == FALSE);
    MI_CpuFill8(hasPocket, 0, sizeof(hasPocket));
    for (i = 0; i < 8; i++) {
        GF_ASSERT(app->bagView->pockets[i].pocketId < 8);
        if (app->bagView->pockets[i].slots != NULL) {
            hasPocket[app->bagView->pockets[i].pocketId] = TRUE;
        }
    }
    for (i = 0; i < 8; i++) {
        if (hasPocket[i]) {
            ManagedSprite_SetDrawFlag(app->sprites[9 + i], show);
        } else {
            ManagedSprite_SetDrawFlag(app->sprites[9 + i], FALSE);
        }
    }
}

void BagApp_SetBButtonSpriteDrawFlag(BagApp *app, BOOL show) {
    ManagedSprite_SetDrawFlag(app->sprites[19], show);
}
