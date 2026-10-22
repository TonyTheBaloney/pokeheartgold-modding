#include "constants/scrcmd.h"
#include "maps/Viridian/ids.h"
#include "constants/init_script_types.h"
#include "macros/script.inc"



	InitScriptEntry_OnTransition _EV_scr_seq_T02_008 + 1
	InitScriptEntry_OnFrameTable scr_seq_T02_map_scripts_2
	InitScriptEntryEnd

scr_seq_T02_map_scripts_2:
	InitScriptGoToIfEqual VAR_UNK_4096, 1, _EV_scr_seq_T02_011 + 1
	InitScriptFrameTableEnd

	InitScriptEnd
