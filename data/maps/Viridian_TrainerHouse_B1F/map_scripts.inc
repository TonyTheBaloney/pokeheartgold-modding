#include "constants/scrcmd.h"
#include "maps/Viridian_TrainerHouse_B1F/ids.h"
#include "constants/init_script_types.h"
#include "macros/script.inc"



	InitScriptEntry_OnTransition std_trainer_house_reset
	InitScriptEntry_OnFrameTable scr_seq_T02R0302_map_scripts_2
	InitScriptEntryEnd

scr_seq_T02R0302_map_scripts_2:
	InitScriptGoToIfEqual VAR_UNK_412E, 0, _EV_scr_seq_T02R0302_002 + 1
	InitScriptGoToIfEqual VAR_UNK_412E, 5, _EV_scr_seq_T02R0302_003 + 1
	InitScriptFrameTableEnd

	InitScriptEnd
