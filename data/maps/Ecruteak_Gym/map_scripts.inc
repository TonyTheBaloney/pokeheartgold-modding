#include "constants/scrcmd.h"
#include "maps/Ecruteak_Gym/ids.h"
#include "constants/init_script_types.h"
#include "macros/script.inc"



	InitScriptEntry_OnTransition _EV_scr_seq_T27GYM0101_000 + 1
	InitScriptEntry_OnFrameTable scr_seq_T27GYM0101_map_scripts_2
	InitScriptEntryEnd

scr_seq_T27GYM0101_map_scripts_2:
	InitScriptGoToIfEqual VAR_UNK_4079, 0, _EV_scr_seq_T27GYM0101_004 + 1
	InitScriptFrameTableEnd

	InitScriptEnd
