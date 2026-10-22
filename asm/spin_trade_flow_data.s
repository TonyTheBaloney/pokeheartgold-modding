	.include "macros.inc"
	.include "spin_trade_flow_data.inc"
	.include "global.inc"

	.public gOverlayTemplate_SpinTradeGroup
	.public gOverlayTemplate_SpinTrade
	.public gSpinTradeFlowStates

	.rodata

gOverlayTemplate_SpinTradeGroup:
	.word SpinTradeGroupApp_Init, SpinTradeGroupApp_Main, SpinTradeGroupApp_Exit, SDK_OVERLAY_OVY_85_ID
gOverlayTemplate_SpinTrade:
	.word SpinTradeApp_Init, SpinTradeApp_Main, SpinTradeApp_Exit, SDK_OVERLAY_OVY_85_ID
gSpinTradeFlowStates:
	.word SpinTradeFlow_LaunchGroupApp
	.word SpinTradeFlow_WaitGroupApp
	.word SpinTradeFlow_WaitPartyMenu
	.word SpinTradeFlow_WaitSummary
	.word SpinTradeFlow_WaitSpinTradeApp
	.word SpinTradeFlow_Finish
