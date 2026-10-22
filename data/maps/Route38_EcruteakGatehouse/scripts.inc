#include "constants/scrcmd.h"
#include "maps/Route38_EcruteakGatehouse/ids.h"
#include "msgdata/msg/msg_0395_R38R0101.h"
#include "macros/script.inc"


	ScrDef scr_seq_R38R0101_000
	ScrDef scr_seq_R38R0101_001
	ScrDefEnd

scr_seq_R38R0101_000:
	End

scr_seq_R38R0101_001:
	SimpleNPCMsg msg_0395_R38R0101_00000
	End
	.balign 4, 0
