#ifndef POKEHEARTGOLD_APPLICATION_BAG_BAG_APP_H
#define POKEHEARTGOLD_APPLICATION_BAG_BAG_APP_H

#include <nnsys.h>

#include "bag_types_def.h"
#include "bg_window.h"
#include "camera.h"
#include "filesystem.h"
#include "message_format.h"
#include "message_printer.h"
#include "msgdata.h"
#include "options.h"
#include "player_data.h"
#include "pm_string.h"
#include "sprite_system.h"
#include "yes_no_prompt.h"

// Work of the Bag application: the touch-screen bag with the 3D bag model on the top screen.
// Launched with a BagView (BagView.pocketIndex: shown pocket, mode: launch mode, selectedAction: exit action).

// The pocket-switch screen (touch and hold a pocket tab, then slide)
typedef struct BagAppPocketSwitch {
    u8 pocket;
    u8 direction; // 0 left, 1 right, 2 none
    u8 stage;
    u8 timer;
    u8 unk_4;
    u8 unk_5[2];
    u8 flags;
} BagAppPocketSwitch;

// The 3D bag model: one open/close animation pair per pocket and a common extra animation
typedef struct BagAppModel {
    NNSG3dRenderObj renderObj;
    NNSG3dResMdl *model;
    NNSG3dResFileHeader *modelData;
    void *pocketAnimData[8];
    void *pocketAnimData2[8];
    void *extraAnimData;
    NNSG3dAnmObj *pocketAnims[8];
    NNSG3dAnmObj *pocketAnims2[8];
    NNSG3dAnmObj *extraAnim;
    u32 pocket;
} BagAppModel;

// Camera turn between the pockets' key angles
typedef struct BagAppCameraTween {
    u32 from;
    u32 to;
    u32 queued; // next target once this turn ends, -1 for none
    u16 frame;
    u16 duration;
} BagAppCameraTween;

// Top screen 3D scene
typedef struct BagAppScene {
    NNSFndAllocator allocator;
    Camera *camera;
    BagAppModel model;
    VecFx32 cameraTarget;
    CameraParam cameraParam;
    BagAppCameraTween tween;
    VecFx32 modelPos;
} BagAppScene;

// Flash (palette) or animation of a pressed button sprite, then a switch to `nextState`
typedef struct BagAppButtonFeedback {
    u8 sprite;
    u8 flashPalette : 4;
    u8 restorePalette : 4;
    u8 isAnim;
    u8 stage : 4;
    u8 timer : 4;
    int nextState;
} BagAppButtonFeedback;

typedef struct BagApp {
    BgConfig *bgConfig;
    Window windows[11];    // 0 item description, 1 TM/HM move info, 2 prompt, 3 message box, 7 CANCEL
    Window dynWindows[24]; // added while needed: 0-11 item list, 12 selected entry, 13-16 item menu labels,
                           // 17-19 quantity digits, 20 quantity label, 21 wide message, 22 money, 23 sell price
    BagView *bagView;
    Bag *bag;
    PlayerProfile *profile;
    Options *options;
    NARC *narc;
    SpriteSystem *spriteSystem;
    SpriteManager *spriteManager;
    ManagedSprite *sprites[39]; // 0 move marker, 1-6 item icons, 7-8 TM type / category, 9-16 pocket tabs, 17-18 page
                                // arrows, 19 CANCEL, 20 cursor, 21-27 slot frames, 28-31 item menu rows, 32-37
                                // quantity buttons, 38 confirm
    MessagePrinter *msgPrinter;
    MsgData *msgData;
    MessageFormat *msgFormat;
    MsgData *itemNamesMsgData;
    MsgData *moveNamesMsgData;
    String *menuStrings[16];
    u8 unk_340[8];
    u32 unk_348;
    u8 unk_34C[4];
    String *itemNames[165];
    String *msgBuf;
    String *unk_5E8;
    String *quantityTemplate;
    u8 unk_5F0[4];
    String *unusedStrings[8];
    u8 numPockets;
    u8 trainerGender;
    u8 printerId;
    u8 unk_617;
    u8 unk_618;
    BagAppPocketSwitch pocketSwitch;
    u8 unk_621[0x23];
    int cursorButton; // 0-7 pocket tabs, 8-13 item slots, 14/15 page arrows, 16 CANCEL
    u8 unk_648;
    u8 unk_649[2];
    u8 unk_64B;
    u8 unk_64C[0x20];
    u32 menuCursor; // item menu row, or the target slot while moving an item
    u8 switchPocket;
    u8 isMovingItem;
    u8 moveSource; // pocket index of the item being moved
    int unk_674;
    u8 unk_678[3];
    u8 taskState;
    int (*task)(struct BagApp *app);
    s16 quantity;
    u16 maxQuantity;
    int sellPrice;
    u8 unk_688[2];
    u8 listBank; // which of the two item list window banks is shown
    u8 unk_68B;
    void *bgPaletteBuffers[2];
    NNSG2dPaletteData *bgPalettes[2];
    void *objPaletteBuffer;
    NNSG2dPaletteData *objPalette;
    u16 itemIds[165];
    int (*itemActions[5])(struct BagApp *app);
    YesNoPrompt *yesNoPrompt;
    BagAppScene scene;
    BagAppButtonFeedback buttonFeedback;
    int chosenAction;
} BagApp;

void BagApp_DrawTopScreenUI(BagApp *app, int mode);
BOOL IsBerryOrMulch(u32 pocketId, u32 itemId);
void BagApp_AddItemNameWindows(BagApp *app);
void BagApp_RemoveItemNameWindows(BagApp *app);
void BagApp_ShowContextMenuWindows(BagApp *app);
void BagApp_RemoveContextMenuWindowsInternal(BagApp *app);
void BagApp_BufferItemName(BagApp *app, u32 slot, u32 fieldIdx);
void BagApp_BufferItemNamePlural(BagApp *app, u32 slot, u32 fieldIdx);
void BagApp_PrintItemDescriptionOnWindowMain0(BagApp *app, u16 itemId);
void BagApp_PrintTMHMDetails(BagApp *app, u16 itemId);
void BagApp_PrintTMorHMNumberOnWindow(BagApp *app, Window *window, ItemSlot *slot, int y);
void *BagApp_GetHMAndRegisteredIconNCGR(BagApp *app, NNSG2dCharacterData **charData);

void BagApp_LoadContextMenuStrings(BagApp *app);
void BagApp_UnloadContextMenuStrings(BagApp *app);
void BagApp_DrawContextMenuTopScreen(BagApp *app, const u8 *actions, int count);
void BagApp_PrintItemDescriptionOnWindow(BagApp *app, Window *window, u32 itemId);
void BagApp_ClearItemDescriptionWindow(BagApp *app, Window *window);
void BagApp_PrintPocketDescriptionOnWindow(BagApp *app, Window *window, u32 pocket);
void BagApp_ClearItemActionMessageWindow(BagApp *app);
void BagApp_RemoveContextMenuWindowsAndRedrawTopScreenUI(BagApp *app);
void BagApp_RemoveContextMenuWindows(BagApp *app);
void BagApp_PrintMoveTheItemMessage(BagApp *app);
void BagApp_PrintQuantityDigitWindows(BagApp *app, u32 numDigits);
void BagApp_PrintOkToTrashItemsMessage(BagApp *app);
u8 BagApp_PrintMessage(BagApp *app, BOOL wide);
void BagApp_CreateYesNoPrompt(BagApp *app);
void BagApp_DestroyYesNoPrompt(BagApp *app);
void BagApp_PrintSaleTotalInWindow(BagApp *app);
void BagApp_PrintMoneyOnWindow(BagApp *app, BOOL skipLabel);
void BagApp_DrawPoffinCountMsgBox_DPPt(BagApp *app);
void BagApp_PrintCancel(BagApp *app, BOOL left);
void BagApp_RedrawItemNameWindows(BagApp *app, int scroll, int unused, BOOL dim);
void BagApp_SwitchItemButtonWindowsToContextMenuMode(BagApp *app, s32 scroll, s32 slot);
void BagApp_ClearSelectedItemWindow(BagApp *app);
void BagApp_PrintPageCounter(BagApp *app, s32 itemCount, s32 scroll, s32 unused);
void BagApp_PrintContextMenuStringOnWindowCentered(Window *window, String **strings, u8 action);
void BagApp_ClearFourWindowsAt(Window *windows);
void BagApp_PrintTrashContextOptionOnWindow(BagApp *app);
void BagApp_PrintSellContextOptionOnWindow(BagApp *app);
void BagApp_ClearTextOnSellOrTrashButton(BagApp *app);
void BagApp_ClearTextOnCancelButton(BagApp *app);
void BagApp_InitSpriteRendererAndSystem(BagApp *app);
void BagApp_FreeSpriteSystem(BagApp *app);
void BagApp_UpdateSpriteAnims(BagApp *app);
void BagApp_StartPocketSwitchPressedButtonAnim_DPPt(BagApp *app);
void BagApp_StepPocketSwitchPressedButtonAnim_DPPt(BagApp *app);
void BagApp_SetCursorSpritePos_PocketsItemsContext(BagApp *app, s32 button);
void BagApp_HideCursorSprite(BagApp *app);
void BagApp_SetCursorSpritePos_ItemsOnly(BagApp *app, int slot);
void BagApp_SetCursorSpritePos_QuantitySelect(BagApp *app, s32 index);
void BagApp_LoadObjPaletteByPocket(BagApp *app, int pocket);
void BagApp_UpdateItemButtonsDrawState(BagApp *app, int count, int movingSlot, BOOL hide);
void BagApp_UpdateItemIconsVisibility(BagApp *app, BagViewPocket *pocket, int count, BOOL update);
void BagApp_ShowOnlySelectedItemIcon(BagApp *app, BagViewPocket *pocket, int slot);
void BagApp_DrawContextMenuButtonSprites(BagApp *app, const u8 *actions);
void BagApp_HideContextMenuIcons(BagApp *app);
void BagApp_CenterSelectedItemIconSprite(BagApp *app, int slot);
s32 BagApp_GetNumberWidthType(s32 max);
void BagApp_ShowQuantitySelectSpritesUI(BagApp *app, int numDigits, int max);
void BagApp_HideQuantitySelectSpritesUI(BagApp *app);
void BagApp_SetPocketIconsDrawFlag(BagApp *app, BOOL show);
void BagApp_SetBButtonSpriteDrawFlag(BagApp *app, BOOL show);

#endif // POKEHEARTGOLD_APPLICATION_BAG_BAG_APP_H
