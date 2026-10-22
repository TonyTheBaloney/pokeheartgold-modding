#ifndef POKEHEARTGOLD_GLOBAL_H
#define POKEHEARTGOLD_GLOBAL_H

#ifndef PM_ASM
#include <nitro.h>
// Like <nitro/code16.h>, but FX_Mul stays inline: game code was built that way.
#pragma thumb on
#undef FX_Mul32x64c
#undef MATH_CountLeadingZeros
#define FX_Mul32x64c(v32, v64c)   FX_Mul32x64cFunc(v32, v64c)
#define MATH_CountLeadingZeros(x) MATH_CountLeadingZerosFunc(x)
#include <nnsys.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>
// MSL defines NULL as 0L; the game was built with the SDK's C definition.
#undef NULL
#define NULL ((void *)0)
#endif

#include "constants/global.h"

#include "assert.h"
#include "config.h" // MUST COME BEFORE ANY OTHER GAMEFREAK HEADERS
#include "pm_version.h"

#define NELEMS(a) (sizeof(a) / sizeof(*(a)))

typedef struct {
    int x;
    int y;
    int z;
} Vec32;

#define ARRAY_ASSIGN_EX(dest, src, as_type, count)            \
    {                                                         \
        struct tmp {                                          \
            as_type _[count];                                 \
        };                                                    \
        *(struct tmp *)&(dest) = *(const struct tmp *)&(src); \
    }

#define ARRAY_ASSIGN(dest, src) ARRAY_ASSIGN_EX(dest, src, typeof(*(dest)), NELEMS(dest))

#endif // POKEHEARTGOLD_GLOBAL_H
