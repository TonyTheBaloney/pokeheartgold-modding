#include "constants/scrcmd.h"
#include "maps/Pallet_TownRedsHouse_2F/ids.h"
#include "msgdata/msg/msg_0448_T01R0102.h"
#include "macros/script.inc"


	ScrDef scr_seq_T01R0102_000
	ScrDef scr_seq_T01R0102_001
	ScrDefEnd

scr_seq_T01R0102_000:
	PlaySE SEQ_SE_DP_SELECT
	LockAll
	NPCMsg msg_0448_T01R0102_00000
	WaitButton
	CloseMsg
	ReleaseAll
	End

scr_seq_T01R0102_001:
	PlaySE SEQ_SE_DP_SELECT
	LockAll
	NPCMsg msg_0448_T01R0102_00001
	WaitButton
	CloseMsg
	ReleaseAll
	End
	.balign 4, 0
