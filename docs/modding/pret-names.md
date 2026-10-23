<!-- [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-23 -->

# Names taken from pret

> AI-generated; not affiliated with pret. See AI.md at the repository root.

This fork and pret/pokeheartgold decompiled much of the same code separately and named it
differently. Where pret's names were more specific, or follow the Gen 4 style pret uses
across its decomps (several come from pokeplatinum), this fork switched to them on
2026-10-23. The ROMs still match. Use this list to update anything written against the
old names.

The fork kept its own name where pret's is still a placeholder (`PlayerAvatar_GetUnk24`,
`PokeathlonCourse_GetField1ED`, `FieldSystem_UnkSub108_*`, `PartyMenu_LaunchApp_Unk1`, ...).

## Bag screen (bag_app.c) (106)

| Old (this fork) | New (pret) |
|---|---|
| `BagApp_AdvanceAnimLoop` | `FrameAdvance3dAnim` |
| `BagApp_AllocItemNameStrings` | `BagApp_CreateItemNameStrings` |
| `BagApp_ApplyTilemapCommands` | `BagApp_DrawItemBgButtons_NormalMode` |
| `BagApp_CalcPocketIconSpacing` | `BagApp_CalcPocketSelectorIconsPos` |
| `BagApp_ClampPocketScroll` | `LimitItemListScroll` |
| `BagApp_ClearField348` | `BagApp_DPPt_CreateItemListMenu` |
| `BagApp_CountPockets` | `BagApp_CountActivePockets` |
| `BagApp_CreateMessageData` | `BagApp_InitMsgSystem` |
| `BagApp_DebugCycleSubScreenLayout` | `BagApp_ProcessInput_Gardening` |
| `BagApp_Draw3D` | `BagApp_Update3D` |
| `BagApp_DrawItemMenu` | `BagApp_PrintContextMenuStrings` |
| `BagApp_DrawItemSlotFrames` | `BagApp_DrawItemBgButtons_MoveMode` |
| `BagApp_FindPocketIndex` | `BagApp_PocketIdToBagViewPosition` |
| `BagApp_Free3D` | `BagApp_Teardown3D` |
| `BagApp_FreeBagModel` | `BagApp_Free3dAssets` |
| `BagApp_FreeBgLayers` | `BagApp_TeardownBgLayers` |
| `BagApp_FreeItemNameStrings` | `BagApp_DeleteItemNameStrings` |
| `BagApp_GetAdjacentPocket` | `BagApp_GetPocketNeighbor` |
| `BagApp_GetCurrentPocketSlotValue` | `BagApp_FetchItemIdOrQuantity` |
| `BagApp_GetCursorItemId` | `BagApp_GetCurrentlySelectedItemId` |
| `BagApp_GetMoveCursorFromDpad` | `MoveItemHandleDPad` |
| `BagApp_GetMoveTargetResult` | `BagApp_MoveItem_HandleSelectedButton` |
| `BagApp_GetMovingItemPageSlot` | `BagApp_GetMoveItemOriginalSlotOnCurrentPage` |
| `BagApp_GetPageItemCount` | `BagApp_GetNumItemsOnCurrentPage` |
| `BagApp_GetTouchedButton` | `BagApp_HandleTouchInput` |
| `BagApp_GetTouchedPocket` | `BagApp_GetNextPocket_DPPt` |
| `BagApp_HandleItemMenuInput` | `BagApp_ContextMenu_HandleInput` |
| `BagApp_HandlePocketSwitchDpad` | `BagApp_DoDPadPocketSwitch_DPPt` |
| `BagApp_InitCameraTween` | `BagApp3DState_Init` |
| `BagApp_IsBerryOrMulch` | `IsBerryOrMulch` |
| `BagApp_ItemAction_ChooseForBerryPatch` | `BagApp_ItemContextMenu_UseInBerryPots` |
| `BagApp_ItemAction_Confirm` | `BagApp_ItemContextMenu_Confirm` |
| `BagApp_ItemAction_Deselect` | `BagApp_ItemContextMenu_Deselect` |
| `BagApp_ItemAction_Give` | `BagApp_ItemContextMenu_Give` |
| `BagApp_ItemAction_Move` | `BagApp_ItemContextMenu_Move` |
| `BagApp_ItemAction_Register` | `BagApp_ItemContextMenu_Register` |
| `BagApp_ItemAction_Trash` | `BagApp_ItemContextMenu_Trash` |
| `BagApp_ItemAction_Use` | `BagApp_ItemContextMenu_Use` |
| `BagApp_LoadBagModel` | `BagApp_Load3dAssets` |
| `BagApp_LoadCursorPositions` | `BagApp_InitBagViewFromCursor` |
| `BagApp_LoadInfoPanelTilemap` | `BagApp_DrawTopScreenUI` |
| `BagApp_LoadPocketItemNames` | `BagApp_SetItemNameStringsFromCurPocket` |
| `BagApp_LoadPocketSubBgPalette` | `BagApp_LoadBgPaletteByPocket` |
| `BagApp_LoadSubScreenLayout` | `BagApp_DrawScreenLayout` |
| `BagApp_PocketScrollDummy` | `RestrictItemListCursor` |
| `BagApp_PressButton` | `BagApp_HandleCursorAction` |
| `BagApp_PrintCursorDescription` | `BagApp_UpdateDescriptionOnTopScreen` |
| `BagApp_ReadItemName` | `BagApp_GetItemNameIntoString` |
| `BagApp_ReadTMHMMoveName` | `BagApp_GetTMHMMoveNameIntoString` |
| `BagApp_RedrawMovePage` | `BagApp_DrawPocketPage_MoveItemMode` |
| `BagApp_RedrawPocket` | `BagApp_DrawDefaultLayout` |
| `BagApp_RedrawPocketPage` | `BagApp_DrawPocketPage_NormalMode` |
| `BagApp_RunPocketSwitch` | `BagApp_StepPocketSelectorAnim_DPPt` |
| `BagApp_SaveCursorPositions` | `BagApp_SaveBagViewToCursor` |
| `BagApp_SetBagModelPocketAnim` | `BagApp_SwitchPlayerModelAnimsToNewPocket` |
| `BagApp_SetGraphicsBanks` | `BagApp_SetGfxBanks` |
| `BagApp_SetMenuInputState` | `BagApp_SaveMenuInputStateToBagView` |
| `BagApp_SetPocketPositionFromButton` | `BagApp_UpdateBagViewPocketCursorPos` |
| `BagApp_SetupItemMenu` | `BagApp_PrepareContextMenu` |
| `BagApp_ShouldMoveCursorToButton` | `BagApp_TouchTargetIsNotTransitioningFromItemsToPocketButtons` |
| `BagApp_ShowCancelButton` | `BagApp_SetCancelButtonDrawFlag` |
| `BagApp_StartButtonAnim` | `BagApp_SetSpriteAnimationTransitionToNextState` |
| `BagApp_StartButtonFlash` | `BagApp_SetSpritePaletteAnimTransitionToNextState` |
| `BagApp_StartCameraTween` | `BagApp3DState_BeginMoveCamera` |
| `BagApp_StartMoveItem` | `BagApp_TransitionDrawStateToMoveItemMode` |
| `BagApp_State_ButtonFeedback` | `BagAppMainTask_RunSpriteAnimTransition` |
| `BagApp_State_CancelSellQuantity` | `BagAppMainTask_SellItem_Abort` |
| `BagApp_State_CancelTrash` | `BagAppMainTask_AbortToss` |
| `BagApp_State_ChangePage` | `BagAppMainTask_TurnPocketPage` |
| `BagApp_State_CloseItemMenu` | `BagAppMainTask_CancelContextMenu` |
| `BagApp_State_CompleteSale` | `BagAppMainTask_CompleteSale` |
| `BagApp_State_DebugSubScreenLayout` | `BagAppMainTask_Gardening` |
| `BagApp_State_DropMovedItem` | `BagAppMainTask_ApplyMoveItem` |
| `BagApp_State_EndMoveItem` | `BagAppMainTask_FinishMoveItem` |
| `BagApp_State_FinishTrash` | `BagAppMainTask_CompleteToss_WaitButton` |
| `BagApp_State_HandleInput` | `BagAppMainTask_HandleInput_Normal` |
| `BagApp_State_HoldItemSelectInput` | `BagAppMainTask_HandleInput_GiveItem` |
| `BagApp_State_ItemMenuInput` | `BagAppMainTask_ContextMenu` |
| `BagApp_State_MoveItemInput` | `BagAppMainTask_MoveItem` |
| `BagApp_State_OpenItemMenu` | `BagAppMainTask_OpenContextMenu` |
| `BagApp_State_PocketSwitch` | `BagAppMainTask_SwitchPocket_DPPt` |
| `BagApp_State_RunItemAction` | `BagAppMainTask_RunContextMenuAction` |
| `BagApp_State_RunUseItemTask` | `BagAppMainTask_RunUseItemCallback` |
| `BagApp_State_SellQuantityInput` | `BagAppMainTask_SellItem_ChooseQuantity` |
| `BagApp_State_SellSelectInput` | `BagAppMainTask_HandleInput_Sell` |
| `BagApp_State_SellYesNo` | `BagAppMainTask_ConfirmSale_HandleYesNo` |
| `BagApp_State_SetupSellQuantity` | `BagAppMainTask_SellItem_ChooseQuanity_WaitMessage` |
| `BagApp_State_ShowSellPrice` | `BagAppMainTask_SellItem_PrintFinalConfirmation` |
| `BagApp_State_ShowTrashConfirm` | `BagAppMainTask_ConfirmToss_PrintMessage` |
| `BagApp_State_StartSell` | `BagAppMainTask_HandleSelectedItemForSale` |
| `BagApp_State_TrashQuantityInput` | `BagAppMainTask_Toss_SelectQuantity` |
| `BagApp_State_TrashYesNo` | `BagAppMainTask_ConfirmToss_HandleYesNo` |
| `BagApp_State_WaitCantHoldMessage` | `BagAppMainTask_GiveItemError_WaitMessage` |
| `BagApp_State_WaitItemMessage` | `BagAppMainTask_ItemUseError_WaitMessage` |
| `BagApp_State_WaitRegisterFailMessage` | `BagAppMainState_RegisterItemFailed_WaitMessage` |
| `BagApp_State_WaitSaleMessage` | `BagAppMainTask_CompleteSale_WaitMessage` |
| `BagApp_State_WaitSellPriceMessage` | `BagAppMainTask_ConfirmSale_WaitMessage` |
| `BagApp_State_WaitTrashConfirmMessage` | `BagAppMainTask_ConfirmToss_WaitMessage` |
| `BagApp_State_WaitTrashResultMessage` | `BagAppMainTask_CompleteToss_WaitMessage` |
| `BagApp_TakeUsedItem` | `BagApp_DepleteItemAfterUse` |
| `BagApp_UpdateCameraTween` | `BagApp3DState_UpdateCameraPosition` |
| `BagApp_UpdateMoveMarker` | `BagApp_SetMoveItemCursorSpritePosition` |
| `BagApp_UseItemInPlaceTask` | `BagApp_UseItemInPlaceMessage` |
| `BagApp_UseSelectedItem` | `BagApp_UseItem` |
| `BagApp_UseTMHMTask` | `BagApp_UseTMHM` |
| `BagApp_VBlankCallback` | `BagApp_VBlankIntrCB` |

## Battle controller (66)

| Old (this fork) | New (pret) |
|---|---|
| `BattleControl_EmitPartyStatusHeal` | `BattleController_EmitRefreshPartyStatus` |
| `BattleController_EmitBackgroundSlideIn` | `BattleController_EmitSlideInBackground` |
| `BattleController_EmitBattleMonToPartyMonCopy` | `BattleController_EmitUpdatePartyMon` |
| `BattleController_EmitBlankMessage` | `BattleController_EmitClearMessageBox` |
| `BattleController_EmitCancelSelection` | `BattleController_EmitStopGaugeAnimation` |
| `BattleController_EmitCommandComplete` | `BattleController_EmitClearCommand` |
| `BattleController_EmitCopyStatus2Effect` | `BattleController_EmitPlayStatusEffectAttackerToDefender` |
| `BattleController_EmitDeleteBallGauge` | `BattleController_EmitHidePartyGauge` |
| `BattleController_EmitDeleteBallGfx` | `BattleController_EmitFreePartyGaugeGraphics` |
| `BattleController_EmitDeleteStartBallGauge` | `BattleController_EmitHideInitialPartyGauge` |
| `BattleController_EmitDrawYesNoBox` | `BattleController_EmitShowYesNoMenu` |
| `BattleController_EmitEndSelection` | `BattleController_EmitClearTouchScreen` |
| `BattleController_EmitExpBarFullFlash` | `BattleController_EmitPlayLevelUpAnimation` |
| `BattleController_EmitExpBarUpdate` | `BattleController_EmitUpdateExpGauge` |
| `BattleController_EmitFadeOutBattle` | `BattleController_EmitFadeOut` |
| `BattleController_EmitForefitMessage` | `BattleController_EmitPrintForefitMessage` |
| `BattleController_EmitHealthbarSlideIn` | `BattleController_EmitSlideHealthBoxIn` |
| `BattleController_EmitHealthbarSlideOut` | `BattleController_EmitSlideHealthBoxOut` |
| `BattleController_EmitHealthbarStatus` | `BattleController_EmitSetStatusIcon` |
| `BattleController_EmitHealthbarUpdate` | `BattleController_EmitUpdateHPGauge` |
| `BattleController_EmitInitBallGauge` | `BattleController_EmitShowPartyGauge` |
| `BattleController_EmitInitStartBallGauge` | `BattleController_EmitShowInitialPartyGauge` |
| `BattleController_EmitLoadBallGfx` | `BattleController_EmitLoadPartyGaugeGraphics` |
| `BattleController_EmitMonFlicker` | `BattleController_EmitFlickerBattlerSprite` |
| `BattleController_EmitPacket` | `SendMessage` |
| `BattleController_EmitPlayEncounterAnimation` | `BattleController_EmitSetupBattleUI` |
| `BattleController_EmitPlayFaintAnimation` | `BattleController_EmitPlayFaintingSequence` |
| `BattleController_EmitPlayMoveSE` | `BattleController_EmitPlayMoveHitSoundEffect` |
| `BattleController_EmitPlaySE` | `BattleController_EmitPlaySound` |
| `BattleController_EmitPlaySong` | `BattleController_EmitPlayMusic` |
| `BattleController_EmitPokemonEncounter` | `BattleController_EmitSetEncounter` |
| `BattleController_EmitPokemonEnterBall` | `BattleController_EmitOpenCaptureBall` |
| `BattleController_EmitPokemonSendOut` | `BattleController_EmitShowPokemon` |
| `BattleController_EmitPokemonSlideIn` | `BattleController_EmitShowEncounter` |
| `BattleController_EmitPrintFirstSendOutMessage` | `BattleController_EmitPrintLeadMonMessage` |
| `BattleController_EmitPrintSelectionMessage` | `BattleController_EmitSetAlertMessage` |
| `BattleController_EmitRecallPokemon` | `BattleController_EmitReturnPokemon` |
| `BattleController_EmitRefreshHealthbar` | `BattleController_EmitRefreshHPGauge` |
| `BattleController_EmitRunAwayMessage` | `BattleController_EmitPrintEscapeMessage` |
| `BattleController_EmitSelectCommand` | `BattleController_EmitSetCommandSelectionMenu` |
| `BattleController_EmitSelectItem` | `BattleController_EmitShowBagMenu` |
| `BattleController_EmitSelectMove` | `BattleController_EmitShowMoveSelectMenu` |
| `BattleController_EmitSelectMoveToForget` | `BattleController_EmitForgetMove` |
| `BattleController_EmitSelectTarget` | `BattleCommand_EmitShowTargetSelectMenu` |
| `BattleController_EmitSetBattleBackground` | `BattleController_EmitUpdateBackground` |
| `BattleController_EmitSetStatus2Effect` | `BattleController_EmitPlayStatusEffect` |
| `BattleController_EmitShowMonList` | `BattleController_EmitShowPartyMenu` |
| `BattleController_EmitShowWaitMessage` | `BattleController_EmitPrintLinkWaitMessage` |
| `BattleController_EmitSwapToSubstituteSprite` | `BattleController_EmitRefreshSprite` |
| `BattleController_EmitThrowPokeball` | `BattleController_EmitTrainerThrowBall` |
| `BattleController_EmitToggleVanish` | `BattleController_EmitToggleVanishMessage` |
| `BattleController_EmitTrainerEncounter` | `BattleController_EmitSetTrainerEncounter` |
| `BattleController_InitBallGaugePacket` | `PartyGaugeData_New` |
| `BattleController_InitMoveAnimData` | `BattleController_SetMoveAnimation` |
| `BattleController_ProcessQueue` | `BattleSystem_TryRecvMessage` |
| `BattleController_RecvData` | `BattleController_RecvMessage` |
| `BattleController_RecvLinkData` | `BattleController_RecvCommMessage` |
| `BattleController_ReplyCommandSelection` | `BattleController_EmitSelectedCommand` |
| `BattleController_ReplyItemSelection` | `BattleController_EmitSelectedBagItem` |
| `BattleController_ReplyMoveSelection` | `BattleController_EmitSelectedMove` |
| `BattleController_ReplyPartySelection` | `BattleController_EmitPartyMenuResult` |
| `BattleController_ReplySelectionMessageDone` | `BattleController_EmitAlertMessageAck` |
| `BattleController_ReplyTargetSelection` | `BattleController_EmitSelectedTarget` |
| `BattleController_SendData` | `BattleController_SendLocalMessage` |
| `BattleController_SetMoveAnimation` | `BattleController_EmitPlayMoveAnimation` |
| `BattleController_SetMoveAnimationForBattlers` | `BattleController_SetMoveAnimationAttackerToDefender` |

## Bag screen windows (bag_app_display.c) (50)

| Old (this fork) | New (pret) |
|---|---|
| `BagApp_AddItemActionWindows` | `BagApp_ShowContextMenuWindows` |
| `BagApp_AddItemListWindows` | `BagApp_AddItemNameWindows` |
| `BagApp_AddWindows` | `BagApp_CreateMainWindows` |
| `BagApp_BufferSlotItemName` | `BagApp_BufferItemName` |
| `BagApp_BufferSlotItemNamePlural` | `BagApp_BufferItemNamePlural` |
| `BagApp_ClearCancelButtonText` | `BagApp_ClearTextOnCancelButton` |
| `BagApp_ClearDescriptionWindow` | `BagApp_ClearItemDescriptionWindow` |
| `BagApp_ClearItemMenuLabels` | `BagApp_ClearFourWindowsAt` |
| `BagApp_ClearMoveInfoWindow` | `BagApp_ClearTMHMDetailsWindow` |
| `BagApp_ClearQuantityLabel` | `BagApp_ClearTextOnSellOrTrashButton` |
| `BagApp_ClearSelectedItemEntry` | `BagApp_ClearSelectedItemWindow` |
| `BagApp_CloseItemActionWindows` | `BagApp_RemoveContextMenuWindows` |
| `BagApp_CloseItemMenuWindows` | `BagApp_RemoveContextMenuWindowsAndRedrawTopScreenUI` |
| `BagApp_CloseItemPromptWindow` | `BagApp_ClearItemActionMessageWindow` |
| `BagApp_DrawHMMarker` | `BagApp_DrawHMIconOnWindow` |
| `BagApp_DrawItemList` | `BagApp_RedrawItemNameWindows` |
| `BagApp_DrawRegisteredItemIcon` | `BagApp_DrawRegisteredItemIconOnWindow` |
| `BagApp_DrawSelectedItemEntry` | `BagApp_SwitchItemButtonWindowsToContextMenuMode` |
| `BagApp_FillBg3TileRows13And14` | `BagApp_ClearPocketNameBox` |
| `BagApp_FreeItemMenuStrings` | `BagApp_UnloadContextMenuStrings` |
| `BagApp_FreeQuantityTemplates` | `BagApp_DeleteItemCountStrings_DPPt` |
| `BagApp_FreeUnusedStrings` | `BagApp_DeletePocketNames` |
| `BagApp_GetNthItemSlotIndex` | `BagViewPocket_GetIndexWithAtMostXNonEmptySlots` |
| `BagApp_LoadItemMenuStrings` | `BagApp_LoadContextMenuStrings` |
| `BagApp_LoadListIconChars` | `BagApp_GetHMAndRegisteredIconNCGR` |
| `BagApp_LoadQuantityTemplates` | `BagApp_LoadItemCountStrings_DPPt` |
| `BagApp_LoadUnusedStrings` | `BagApp_LoadPocketNames` |
| `BagApp_MeasureQuantityText` | `BagApp_FormatTMQuantityString_DPPt` |
| `BagApp_PrintCancelButton` | `BagApp_PrintCancel` |
| `BagApp_PrintItemDescription` | `BagApp_PrintItemDescriptionOnWindowMain0` |
| `BagApp_PrintItemListEntry` | `BagApp_PrintItemNameAndMaybeQuantityOnWindow` |
| `BagApp_PrintItemMenuLabel` | `BagApp_PrintContextMenuStringOnWindowCentered` |
| `BagApp_PrintItemQuantity` | `PrintItemQuantityOnWindow` |
| `BagApp_PrintItemSelectedMessage` | `BagApp_DrawContextMenuTopScreen` |
| `BagApp_PrintMoney` | `BagApp_PrintMoneyOnWindow` |
| `BagApp_PrintMoveItemPrompt` | `BagApp_PrintMoveTheItemMessage` |
| `BagApp_PrintMsg115And116` | `BagApp_DrawPoffinCountMsgBox_DPPt` |
| `BagApp_PrintPageNumber` | `BagApp_PrintPageCounter` |
| `BagApp_PrintQuantityDigits` | `BagApp_PrintQuantityDigitWindows` |
| `BagApp_PrintSellLabel` | `BagApp_PrintSellContextOptionOnWindow` |
| `BagApp_PrintSellPrice` | `BagApp_PrintSaleTotalInWindow` |
| `BagApp_PrintTMHMMoveInfo` | `BagApp_PrintTMHMDetails` |
| `BagApp_PrintTMHMNumber` | `BagApp_PrintTMorHMNumberOnWindow` |
| `BagApp_PrintTrashConfirmMessage` | `BagApp_PrintOkToTrashItemsMessage` |
| `BagApp_PrintTrashLabel` | `BagApp_PrintTrashContextOptionOnWindow` |
| `BagApp_RemoveItemActionWindows` | `BagApp_RemoveContextMenuWindowsInternal` |
| `BagApp_RemoveItemListWindows` | `BagApp_RemoveItemNameWindows` |
| `BagApp_ShowItemDescription` | `BagApp_PrintItemDescriptionOnWindow` |
| `BagApp_ShowPocketDescription` | `BagApp_PrintPocketDescriptionOnWindow` |
| `BagApp_TextPrinterCallback` | `BagApp_PrintMessageCallback` |

## Bag screen sprites (27)

| Old (this fork) | New (pret) |
|---|---|
| `BagApp_ClearField648` | `BagApp_DPPtPocketSwitchPressedButtonAnim_Run` |
| `BagApp_CreateSpriteSystem` | `BagApp_InitSpriteSystem` |
| `BagApp_DrawItemIcons` | `BagApp_UpdateItemIconsVisibility` |
| `BagApp_FreeSprites` | `BagApp_FreeSpriteSystem` |
| `BagApp_GetUnusedDigitCount` | `BagApp_GetNumberWidthType` |
| `BagApp_HideCursor` | `BagApp_HideCursorSprite` |
| `BagApp_HideItemMenuSprites` | `BagApp_HideContextMenuIcons` |
| `BagApp_HideQuantityButtons` | `BagApp_HideQuantitySelectSpritesUI` |
| `BagApp_InitSprites` | `BagApp_InitSpriteRendererAndSystem` |
| `BagApp_LoadPocketObjPalette` | `BagApp_LoadObjPaletteByPocket` |
| `BagApp_LoadSpriteResources` | `BagApp_LoadSpriteResObjs` |
| `BagApp_SetCancelSpriteVisible` | `BagApp_SetBButtonSpriteDrawFlag` |
| `BagApp_SetCursorPosition` | `BagApp_SetCursorSpritePos_PocketsItemsContext` |
| `BagApp_SetField648` | `BagApp_StartPocketSwitchPressedButtonAnim_DPPt` |
| `BagApp_SetItemIconSprite` | `BagApp_ReplaceItemIconResObjs` |
| `BagApp_SetMoveCursorPosition` | `BagApp_SetCursorSpritePos_ItemsOnly` |
| `BagApp_SetQuantityCursorPosition` | `BagApp_SetCursorSpritePos_QuantitySelect` |
| `BagApp_ShowItemMenuSprites` | `BagApp_DrawContextMenuButtonSprites` |
| `BagApp_ShowMoveSlotSprites` | `BagApp_UpdateItemButtonsDrawState` |
| `BagApp_ShowMovingItemIcon` | `BagApp_ShowOnlySelectedItemIcon` |
| `BagApp_ShowPocketTabSprites` | `BagApp_SetPocketIconsDrawFlag` |
| `BagApp_ShowQuantityButtons` | `BagApp_ShowQuantitySelectSpritesUI` |
| `BagApp_ShowSelectedItemIcon` | `BagApp_CenterSelectedItemIconSprite` |
| `BagApp_ShowTMHMTypeIcons` | `BagApp_DrawTMHMMoveDetails` |
| `BagApp_TickSprites` | `BagApp_UpdateSpriteAnims` |
| `BagApp_UpdateField648` | `BagApp_StepPocketSwitchPressedButtonAnim_DPPt` |
| `BagApp_UpdatePageArrows` | `BagApp_UpdatePageNavArrowSpritesVisibility` |

## Type and category icons (25)

| Old (this fork) | New (pret) |
|---|---|
| `MoveCategoryIcon_DeleteSprite` | `MoveCategoryIconSprite_DeleteAndFreeResources` |
| `MoveCategoryIcon_GetCharFile` | `GetMoveCategoryIconGfxCharFileId` |
| `MoveCategoryIcon_GetNarc` | `GetMoveCategoryIconGfxNarcId` |
| `MoveCategoryIcon_GetPalette` | `GetMoveCategoryIconGfxPlttOverride` |
| `MoveCategoryIcon_LoadChar` | `SpriteSystem_LoadMoveCategoryIconCharResObj` |
| `MoveCategoryIcon_UnloadChar` | `SpriteManager_UnloadMoveCategoryIconCharResObjByTag` |
| `TypeIcon_GetAnimFile` | `GetMoveTypeAndCategoryIconAnimFileId` |
| `TypeIcon_GetCellFile` | `GetMoveTypeAndCategoryIconCellFileId` |
| `TypeIcon_GetCharFile` | `TypeIconGfx_GetCharFileId` |
| `TypeIcon_GetNarc` | `TypeIconGfx_GetNarcId` |
| `TypeIcon_GetPalette` | `TypeIconGfx_GetPlttOverride` |
| `TypeIcon_GetPlttFile` | `GetMoveTypeAndCategoryIconPlttFileId` |
| `TypeIcon_LoadCellAnim` | `SpriteSystem_LoadMoveTypeAndCategoryIconsCellAndAnim` |
| `TypeIcon_LoadChar` | `SpriteSystem_LoadMoveTypeIconCharResObj` |
| `TypeIcon_LoadPaletteBuffer` | `SpriteSystem_LoadMoveTypeAndCategoryIconsPlttToBuffer` |
| `TypeIcon_LoadPltt` | `SpriteSystem_LoadMoveTypeAndCategoryIconsPltt` |
| `TypeIcon_NewSprite` | `SpriteSystem_CreateMoveTypeIconSprite` |
| `TypeIcon_UnloadCellAnim` | `SpriteManager_UnloadMoveTypeAndCategoryIconCellAndAnimResObjsByTags` |
| `TypeIcon_UnloadChar` | `SpriteManager_UnloadMoveTypeIconCharResObjByTag` |
| `TypeIcon_UnloadPltt` | `SpriteManager_UnloadMoveTypeAndCategoryIconPlttResObjByTag` |
| `sMoveCategoryIconCharFiles` | `sMoveCategoryGfxCharFileIds` |
| `sMoveCategoryIconPalettes` | `sMoveCategoryGfxPlttOverrides` |
| `sTypeIconCharFiles` | `sTypeIconGfxCharFileIds` |
| `sTypeIconPalettes` | `sTypeIconGfxPlttOverrides` |
| `thunk_ManagedSprite_DeleteAndFreeResources` | `MoveTypeIconSprite_DeleteAndFreeResources` |

## Shop menu (11)

| Old (this fork) | New (pret) |
|---|---|
| `MartData_CheckCannotBuy` | `MartData_BuyMenu_CheckCanPurchaseItem` |
| `MartData_Destroy` | `MartData_ExitShopMenu` |
| `MartData_GetCurrency` | `MartData_BuyMenu_GetPlayerBalance` |
| `MartData_GetItemPrice` | `ShopMenu_GetItemPrice` |
| `MartData_HandleItemListInput` | `MartData_BuyMenu_HandleMoveCursor` |
| `MartData_NextPage` | `MartData_BuyMenu_PageRight` |
| `MartData_PrevPage` | `MartData_BuyMenu_PageLeft` |
| `MartData_SelectItemListButton` | `MartData_BuyMenu_PressButton` |
| `Mart_GetPriceOverride` | `GetOverriddenPriceByItemID` |
| `Task_Mart_LaunchSellBag` | `Task_Mart_OpenSellMenu` |
| `sMartCursorNeighbors` | `sMartCursorMoveDests` |

## Field 3D render objects (10)

| Old (this fork) | New (pret) |
|---|---|
| `Field3dObjectList_AddInstance` | `Field3dRenderObjManager_AllocRenderObjByIDInternal` |
| `Field3dObjectList_AddShared` | `Field3dRenderObjManager_AllocRenderObj` |
| `Field3dObjectList_Free` | `Field3dRenderObjManager_Delete` |
| `Field3dObjectList_GetOrAddInstance` | `Field3dRenderObjManager_GetOrAllocRenderObjByID` |
| `Field3dObjectList_HasModelFile` | `Field3dRenderObjManager_IsResFileHeaderLoadedByIndex` |
| `Field3dObjectList_InitNextObject` | `Field3dRenderObjManager_AllocInternal` |
| `Field3dObjectList_IsShared` | `Field3dRenderObjManager_IsModelAllocatedByIndex` |
| `Field3dObjectList_New` | `Field3dRenderObjManager_New` |
| `Field3dObjectList_ReleaseInstance` | `Field3dRenderObjManager_FreeRenderObj` |
| `Field3dObjectList_ReturnObject` | `Field3dRenderObjManager_FreeRenderObjInternal` |

## Gym puzzles (9)

| Old (this fork) | New (pret) |
|---|---|
| `AzaleaGymmick_GetVectorSignsXZ` | `AzaleaGymmick_GetSignsOfVectorXZComponents` |
| `BlackthornGymmick_GetLeadingWall` | `BlackthornGymmick_GetCurrentLeadingWallCoordinates` |
| `BlackthornGymmick_MoveLeadingWall` | `BlackthornGymmick_GetNextLeadingWallCoordinates` |
| `CianwoodGymmick_RebindAnims` | `CianwoodGymmick_RebindAnimationObjectsAndGetCount` |
| `EcruteakGymmick_UnbindCandle` | `EcruteakGymmick_UnbindCandleFromTrainerObject` |
| `FuchsiaGymmick_AdvanceWallAnims` | `FuchsiaGymmick_FrameAdvanceWallAnimations_CheckAllDone` |
| `FuchsiaGymmick_IsWallAnimPlaying` | `FuchsiaGymmick_IsWallAnimationAlreadyPlaying` |
| `FuchsiaGymmick_KillNeighborAnims` | `FuchsiaGymmick_KillNeighboringSegmentsAnims` |
| `SinjohGymmick_AdvanceAnims` | `SinjohGymmick_AdvanceAnimAndSetAnimIdIfCurrentAnimFinished` |

## Battle system message buffers (9)

| Old (this fork) | New (pret) |
|---|---|
| `BattleSystem_GetRecvBufferEndPos` | `BattleSystem_GetClientEndIndex` |
| `BattleSystem_GetRecvBufferPtr` | `BattleSystem_GetClientMessage` |
| `BattleSystem_GetRecvBufferReadPos` | `BattleSystem_GetClientReadIndex` |
| `BattleSystem_GetRecvBufferWritePos` | `BattleSystem_GetClientWriteIndex` |
| `BattleSystem_GetSendBufferEndPos` | `BattleSystem_GetServerEndIndex` |
| `BattleSystem_GetSendBufferPtr` | `BattleSystem_GetServerMessage` |
| `BattleSystem_GetSendBufferReadPos` | `BattleSystem_GetServerReadIndex` |
| `BattleSystem_GetSendBufferWritePos` | `BattleSystem_GetServerWriteIndex` |
| `BattleSystem_IsServer` | `BattleSystem_IsInitialized` |

## Math helpers (fx_util) (7)

| Old (this fork) | New (pret) |
|---|---|
| `CalcAngleBetweenVecs` | `VEC_AngleBetween` |
| `GetDistanceFromPointToLine` | `VEC_DistanceFromPointToLine` |
| `Math_CalcPerspectiveViewSize` | `FX_CalcLinearFov` |
| `Math_CalcRotationMatrixXYZ` | `MTX_Rot33Vec` |
| `Math_CalcRotationMatrixXYZDeg` | `MTX_Rot33Angles` |
| `Math_Max` | `FX_Max` |
| `Math_Min` | `FX_Min` |

## Seals (synced from pokeplatinum) (6)

| Old (this fork) | New (pret) |
|---|---|
| `Seal_GetBattleAnimResId` | `CapsuleMenu_GetSealParticleIndex` |
| `Seal_GetDescriptionMsgId` | `CapsuleMenu_GetSealNonAlphabetIndex` |
| `Seal_GetGfxCharId` | `CapsuleMenu_GetSealMemberIdx` |
| `Seal_GetNameMsgId` | `CapsuleMenu_GetSealNameIndex` |
| `Seal_IsLetterSeal` | `CapsuleMenu_IsAlphabetSeal` |
| `_02105F04` | `sSealTypeValues` |

## Touch pad (4)

| Old (this fork) | New (pret) |
|---|---|
| `GF_TouchpadResetSampling` | `EnableTouchPad` |
| `GF_TouchpadStartRecording` | `InitializeTouchPadWithExternalBuffer` |
| `GF_TouchpadStartSampling` | `InitializeTouchPad` |
| `GF_TouchpadStopSampling` | `DisableTouchPad` |

## Bag view (4)

| Old (this fork) | New (pret) |
|---|---|
| `BagView_GetSelectedAction` | `BagView_GetReturnCode` |
| `BagView_SetIsCycling` | `BagView_SetOnBike` |
| `BagView_SetItemCheckUseData` | `BagView_SetCheckUseData` |
| `BagView_SetMode` | `BagView_SetContext` |

## Sell menu task (3)

| Old (this fork) | New (pret) |
|---|---|
| `MartBag_ReturnToMart` | `Task_Bag_SellMenu_Return` |
| `MartBag_WaitBagViewExit` | `Task_Bag_SellMenu_WaitBagView` |
| `Task_MartBag` | `Task_Bag_SellMenu` |

## Billboard graphics (2)

| Old (this fork) | New (pret) |
|---|---|
| `BillboardGfxSequence_GetTexPlttIndex` | `BillboardGfxSequence_GetTexPlttIndexAt` |
| `BillboardGfxSequence_Init` | `BillboardGfxSequence_SetData` |

## Battle mon data (2)

| Old (this fork) | New (pret) |
|---|---|
| `GetBattlerStatusCondition` | `Battler_GetStatusCondition` |
| `GetBattlerVar` | `BattleMon_Get` |

## Other (4)

| Old (this fork) | New (pret) |
|---|---|
| `CheckFlag09A` | `CheckUnlockedPokeBallsInMarts` |
| `EraseFrameAndWindow1` | `ClearWindowPixelBuffer` |
| `GetPercentProgressTowardsNextLevel` | `Pokemon_GetPercentToNextLevel` |
| `StartMenu_HandleBagAction1` | `StartMenu_ShowBerryTag` |
