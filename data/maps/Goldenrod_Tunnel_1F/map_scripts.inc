#include "constants/scrcmd.h"
#include "maps/Goldenrod_Tunnel_1F/ids.h"
#include "constants/init_script_types.h"
#include "macros/script.inc"



	InitScriptEntry_OnTransition _EV_scr_seq_D37R0101_003 + 1
	InitScriptEntry_OnFrameTable scr_seq_D37R0101_map_scripts_2
	InitScriptEntryEnd

scr_seq_D37R0101_map_scripts_2:
	InitScriptGoToIfEqual VAR_UNK_40F8, 0, _EV_scr_seq_D37R0101_002 + 1
	InitScriptFrameTableEnd

	InitScriptEnd
