#include "constants/scrcmd.h"
#include "maps/Route35_NationalParkPokeathalonGatehouse/ids.h"
#include "constants/init_script_types.h"
#include "macros/script.inc"



	InitScriptEntry_OnFrameTable scr_seq_R35R0201_map_scripts_2
	InitScriptEntry_OnResume _EV_scr_seq_R35R0201_009 + 1
	InitScriptEntry_OnTransition _EV_scr_seq_R35R0201_012 + 1
	InitScriptEntryEnd

scr_seq_R35R0201_map_scripts_2:
	InitScriptGoToIfEqual VAR_UNK_4118, 1, _EV_scr_seq_R35R0201_010 + 1
	InitScriptFrameTableEnd

	InitScriptEnd
