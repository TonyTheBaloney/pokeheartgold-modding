#ifndef POKEHEARTGOLD_TOUCHPAD_H
#define POKEHEARTGOLD_TOUCHPAD_H

#include "global.h"

void GF_TouchpadInit(void);
void GF_TouchpadPauseOnLidClose(void);
void GF_TouchpadResumeOnLidOpen(void);
void EnableTouchPad(void);
BOOL InitializeTouchPad(int);
BOOL DisableTouchPad(void);

#endif // POKEHEARTGOLD_TOUCHPAD_H
