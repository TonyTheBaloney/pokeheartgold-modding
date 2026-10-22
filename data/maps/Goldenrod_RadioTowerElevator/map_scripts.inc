#include "constants/scrcmd.h"
#include "maps/Goldenrod_RadioTowerElevator/ids.h"
#include "constants/init_script_types.h"
#include "macros/script.inc"



	InitScriptEntry_OnFrameTable scr_seq_D23R0107_map_scripts_2
	InitScriptEntryEnd

scr_seq_D23R0107_map_scripts_2:
	InitScriptGoToIfEqual VAR_UNK_4125, 0, _EV_scr_seq_D23R0107_000 + 1
	InitScriptFrameTableEnd

	InitScriptEnd
