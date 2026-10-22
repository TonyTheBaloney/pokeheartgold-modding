#ifndef POKEHEARTGOLD_CONSTANTS_DAYCARE_H
#define POKEHEARTGOLD_CONSTANTS_DAYCARE_H

// Chance(%) for parents to breed every 255 steps.
#define PARENTS_INCOMPATIBLE      0
#define PARENTS_LOW_COMPATIBILITY 20
#define PARENTS_MED_COMPATIBILITY 50
#define PARENTS_MAX_COMPATIBILITY 70

// Daycare state.
#define DAYCARE_NO_MONS     0
#define DAYCARE_EGG_WAITING 1
#define DAYCARE_ONE_MON     2
#define DAYCARE_TWO_MONS    3

#define NUM_DAYCARE_MONS  2
#define NUM_INHERITED_IVS 3
#define EGG_GENDER_MALE   0x8000 // Used to create a male egg from a female-only parent species (e.g. Nidoran).
#define MAX_EGG_MOVES     16

// [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] claude-opus-5-5, 2026-10-22
// Status: MATCHING (names for literals in LoadEggMoves, src/get_egg.c)
// Egg move table (kowaza_list.narc, built from files/poketool/personal/egg_moves.json):
// EGG_MOVES_SPECIES_OFFSET + species starts a species' moves; names as in pokeemerald.
#define EGG_MOVES_SPECIES_OFFSET 20000
#define EGG_MOVES_TERMINATOR     0xFFFF
#define EGG_MOVES_TABLE_SIZE     2045 // entries searched for a species (the retail table's length)

#endif // POKEHEARTGOLD_CONSTANTS_DAYCARE_H
