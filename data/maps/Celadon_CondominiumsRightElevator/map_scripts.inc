#include "constants/scrcmd.h"
#include "maps/Celadon_CondominiumsRightElevator/ids.h"
#include "constants/init_script_types.h"
#include "macros/script.inc"



	InitScriptEntry_OnFrameTable scr_seq_T07R0207_map_scripts_2
	InitScriptEntryEnd

scr_seq_T07R0207_map_scripts_2:
	InitScriptGoToIfEqual VAR_UNK_4125, 0, _EV_scr_seq_T07R0207_000 + 1
	InitScriptFrameTableEnd

	InitScriptEnd
