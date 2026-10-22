#include "constants/scrcmd.h"
#include "maps/Azalea_KurtHouse/ids.h"
#include "constants/init_script_types.h"
#include "macros/script.inc"



	InitScriptEntry_OnTransition _EV_scr_seq_T23R0501_000 + 1
	InitScriptEntry_OnFrameTable scr_seq_T23R0501_map_scripts_2
	InitScriptEntryEnd

scr_seq_T23R0501_map_scripts_2:
	InitScriptGoToIfEqual VAR_UNK_4080, 2, _EV_scr_seq_T23R0501_005 + 1
	InitScriptFrameTableEnd

	InitScriptEnd
