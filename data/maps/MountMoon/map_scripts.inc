#include "constants/scrcmd.h"
#include "maps/MountMoon/ids.h"
#include "constants/init_script_types.h"
#include "macros/script.inc"



	InitScriptEntry_OnFrameTable scr_seq_D02R0101_map_scripts_2
	InitScriptEntryEnd

scr_seq_D02R0101_map_scripts_2:
	InitScriptGoToIfEqual VAR_UNK_40F5, 0, _EV_scr_seq_D02R0101_000 + 1
	InitScriptFrameTableEnd

	InitScriptEnd
