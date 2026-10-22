#include "constants/scrcmd.h"
#include "maps/RuinsOfAlph_NortheastHiddenRoom/ids.h"
#include "constants/init_script_types.h"
#include "macros/script.inc"



	InitScriptEntry_OnFrameTable scr_seq_D24R0203_map_scripts_2
	InitScriptEntry_OnResume _EV_scr_seq_D24R0203_001 + 1
	InitScriptEntryEnd

scr_seq_D24R0203_map_scripts_2:
	InitScriptGoToIfEqual VAR_UNK_40CD, 1, _EV_scr_seq_D24R0203_000 + 1
	InitScriptFrameTableEnd

	InitScriptEnd
