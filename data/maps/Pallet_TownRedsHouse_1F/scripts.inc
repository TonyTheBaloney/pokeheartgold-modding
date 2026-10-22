#include "constants/scrcmd.h"
#include "maps/Pallet_TownRedsHouse_1F/ids.h"
#include "msgdata/msg/msg_0447_T01R0101.h"
#include "macros/script.inc"


	ScrDef scr_seq_T01R0101_000
	ScrDef scr_seq_T01R0101_001
	ScrDefEnd

scr_seq_T01R0101_000:
	SimpleNPCMsg msg_0447_T01R0101_00000
	End

scr_seq_T01R0101_001:
	PlaySE SEQ_SE_DP_SELECT
	LockAll
	NPCMsg msg_0447_T01R0101_00002
	WaitButton
	CloseMsg
	ReleaseAll
	End
	.balign 4, 0
