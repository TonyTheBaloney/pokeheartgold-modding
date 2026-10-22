#include "constants/scrcmd.h"
#include "maps/PokemonLeagueLanceRoom/ids.h"
#include "constants/init_script_types.h"
#include "macros/script.inc"



	InitScriptEntry_OnFrameTable scr_seq_T10R0601_map_scripts_2
	InitScriptEntry_OnTransition _EV_scr_seq_T10R0601_002 + 1
	InitScriptEntryEnd

scr_seq_T10R0601_map_scripts_2:
	InitScriptGoToIfEqual VAR_UNK_40C8, 0, _EV_scr_seq_T10R0601_001 + 1
	InitScriptFrameTableEnd

	InitScriptEnd
