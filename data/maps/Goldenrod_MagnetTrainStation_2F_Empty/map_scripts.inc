#include "constants/scrcmd.h"
#include "maps/Goldenrod_MagnetTrainStation_2F_Empty/ids.h"
#include "constants/init_script_types.h"
#include "macros/script.inc"



	InitScriptEntry_OnFrameTable scr_seq_T25R0503_map_scripts_2
	InitScriptEntryEnd

scr_seq_T25R0503_map_scripts_2:
	InitScriptGoToIfEqual VAR_UNK_411E, 1, _EV_scr_seq_T25R0503_000 + 1
	InitScriptFrameTableEnd

	InitScriptEnd
