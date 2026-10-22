#include "constants/scrcmd.h"
#include "maps/Route3_Pokecenter_1F/ids.h"
#include "msgdata/msg/msg_0327_R03PC0101.h"
#include "macros/script.inc"


	ScrDef scr_seq_R03PC0101_000
	ScrDef scr_seq_R03PC0101_001
	ScrDef scr_seq_R03PC0101_002
	ScrDefEnd

scr_seq_R03PC0101_000:
	SetVar VAR_SPECIAL_x8007, 0
	CallStd std_nurse_joy
	End

scr_seq_R03PC0101_001:
	SimpleNPCMsg msg_0327_R03PC0101_00000
	End

scr_seq_R03PC0101_002:
	SimpleNPCMsg msg_0327_R03PC0101_00001
	End
	.balign 4, 0
