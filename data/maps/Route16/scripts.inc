#include "constants/scrcmd.h"
#include "maps/Route16/ids.h"
#include "msgdata/msg/msg_0354_R16.h"
#include "macros/script.inc"


	ScrDef scr_seq_R16_000
	ScrDef scr_seq_R16_001
	ScrDefEnd

scr_seq_R16_000:
	SetBikeStateLock 1
	SetFlag FLAG_UNK_149
	End

scr_seq_R16_001:
	TrainerTipsEx 2, msg_0354_R16_00000
	End
	.balign 4, 0
