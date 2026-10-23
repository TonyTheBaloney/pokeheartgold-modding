#ifndef POKEHEARTGOLD_SEAL_DATA_H
#define POKEHEARTGOLD_SEAL_DATA_H

#include "global.h"

u8 CapsuleMenu_GetSealMemberIdx(u32 idx);
u8 CapsuleMenu_GetSealNameIndex(u8 idx);
u8 CapsuleMenu_GetSealParticleIndex(u32 idx);
BOOL CapsuleMenu_IsAlphabetSeal(u32 idx);
u32 CapsuleMenu_GetSealNonAlphabetIndex(u32 idx);

#endif // POKEHEARTGOLD_SEAL_DATA_H
