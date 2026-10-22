#include "constants/scrcmd.h"
#include "maps/Ecruteak_Pokecenter_1F/ids.h"
#include "constants/init_script_types.h"
#include "macros/script.inc"



	InitScriptEntry_OnResume std_wireless_reset_state
	InitScriptEntry_OnFrameTable scr_seq_T27PC0101_map_scripts_2
	InitScriptEntryEnd

scr_seq_T27PC0101_map_scripts_2:
	InitScriptGoToIfEqual VAR_UNK_4133, 2, std_union_room_return
	InitScriptGoToIfEqual VAR_UNK_4133, 1, std_wireless_colosseum_return
	InitScriptGoToIfEqual VAR_UNK_410D, 0, _EV_scr_seq_T27PC0101_001 + 1
	InitScriptFrameTableEnd

	InitScriptEnd
