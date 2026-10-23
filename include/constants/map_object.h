#ifndef POKEHEARTGOLD_CONSTANTS_MAP_OBJECT_H
#define POKEHEARTGOLD_CONSTANTS_MAP_OBJECT_H

// [AI-GENERATED / NOT AFFILIATED WITH PRET] claude-opus-5-5, 2026-10-21
// Status: MATCHING (constants only)

// ObjectEvent.movement: index into gMapObjectMovementCallbacks
// (asm/map_object_movement_tables.s). Names follow the callback/init names.
#define MOVEMENT_TYPE_NONE                     0
#define MOVEMENT_TYPE_PLAYER                   1
#define MOVEMENT_TYPE_LOOK_AROUND              2
#define MOVEMENT_TYPE_WANDER_AROUND            3
#define MOVEMENT_TYPE_WANDER_UP_DOWN           4
#define MOVEMENT_TYPE_WANDER_LEFT_RIGHT        5
#define MOVEMENT_TYPE_LOOK_UP_LEFT             6
#define MOVEMENT_TYPE_LOOK_UP_RIGHT            7
#define MOVEMENT_TYPE_LOOK_DOWN_LEFT           8
#define MOVEMENT_TYPE_LOOK_DOWN_RIGHT          9
#define MOVEMENT_TYPE_LOOK_UP_DOWN_LEFT        10
#define MOVEMENT_TYPE_LOOK_UP_DOWN_RIGHT       11
#define MOVEMENT_TYPE_LOOK_UP_LEFT_RIGHT       12
#define MOVEMENT_TYPE_LOOK_DOWN_LEFT_RIGHT     13
#define MOVEMENT_TYPE_FACE_UP                  14
#define MOVEMENT_TYPE_FACE_DOWN                15
#define MOVEMENT_TYPE_FACE_LEFT                16
#define MOVEMENT_TYPE_FACE_RIGHT               17
#define MOVEMENT_TYPE_SPIN_COUNTERCLOCKWISE    18
#define MOVEMENT_TYPE_SPIN_CLOCKWISE           19
#define MOVEMENT_TYPE_BACK_AND_FORTH           20
// Walk a fixed path; the direction order comes from sDirectionTable14..37
// in src/map_object_movement.c (the MOVEMENT_TYPE index is the table id + 7).
#define MOVEMENT_TYPE_PATH_NORTH_EAST_WEST_SOUTH   21
#define MOVEMENT_TYPE_PATH_EAST_WEST_SOUTH_NORTH   22
#define MOVEMENT_TYPE_PATH_SOUTH_NORTH_EAST_WEST   23
#define MOVEMENT_TYPE_PATH_WEST_SOUTH_NORTH_EAST   24
#define MOVEMENT_TYPE_PATH_WEST_EAST_SOUTH_NORTH   25
#define MOVEMENT_TYPE_PATH_WEST_EAST_SOUTH_NORTH_2 26 // same direction table as 25
#define MOVEMENT_TYPE_PATH_SOUTH_NORTH_WEST_EAST   27
#define MOVEMENT_TYPE_PATH_EAST_SOUTH_NORTH_WEST   28
#define MOVEMENT_TYPE_PATH_WEST_NORTH_SOUTH_EAST   29
#define MOVEMENT_TYPE_PATH_NORTH_SOUTH_EAST_WEST   30
#define MOVEMENT_TYPE_PATH_EAST_WEST_NORTH_SOUTH   31
#define MOVEMENT_TYPE_PATH_SOUTH_EAST_WEST_NORTH   32
#define MOVEMENT_TYPE_PATH_EAST_NORTH_SOUTH_WEST   33
#define MOVEMENT_TYPE_PATH_NORTH_SOUTH_WEST_EAST   34
#define MOVEMENT_TYPE_PATH_WEST_EAST_NORTH_SOUTH   35
#define MOVEMENT_TYPE_PATH_SOUTH_WEST_EAST_NORTH   36
#define MOVEMENT_TYPE_PATH_NORTH_WEST_SOUTH_EAST   37
#define MOVEMENT_TYPE_PATH_SOUTH_EAST_NORTH_WEST   38
#define MOVEMENT_TYPE_PATH_WEST_SOUTH_EAST_NORTH   39
#define MOVEMENT_TYPE_PATH_EAST_NORTH_WEST_SOUTH   40
#define MOVEMENT_TYPE_PATH_NORTH_EAST_SOUTH_WEST   41
#define MOVEMENT_TYPE_PATH_SOUTH_WEST_NORTH_EAST   42
#define MOVEMENT_TYPE_PATH_WEST_NORTH_EAST_SOUTH   43
#define MOVEMENT_TYPE_PATH_EAST_SOUTH_WEST_NORTH   44
#define MOVEMENT_TYPE_LOOK_UP_DOWN             45
#define MOVEMENT_TYPE_LOOK_LEFT_RIGHT          46
#define MOVEMENT_TYPE_INVALID_47               47 // NULL callback table: do not use
#define MOVEMENT_TYPE_FOLLOW_PLAYER_48         48
#define MOVEMENT_TYPE_ALTERNATING_SPIN         49
#define MOVEMENT_TYPE_FOLLOW_PARTNER           50
#define MOVEMENT_TYPE_HIDDEN_COVER_0           51
#define MOVEMENT_TYPE_HIDDEN_COVER_1           52
#define MOVEMENT_TYPE_HIDDEN_COVER_2           53
#define MOVEMENT_TYPE_HIDDEN_COVER_3           54
#define MOVEMENT_TYPE_FOLLOW_PLAYER_55         55
#define MOVEMENT_TYPE_FOLLOW_PLAYER_56         56
#define MOVEMENT_TYPE_COUNT                    57

// ObjectEvent.type. Trainer sight: MapObject_GetTrainerSightType and the
// gMapObjectTypeBehavior* tables (src/map_object_behavior.c).
#define OBJECT_TYPE_NORMAL                   0
#define OBJECT_TYPE_TRAINER                  1 // sees along its facing direction (param0 tiles)
#define OBJECT_TYPE_TRAINER_ALL_DIRECTIONS   2 // sees in all four directions (param0 tiles)
#define OBJECT_TYPE_3                        3 // no sight, no behavior; meaning unknown
#define OBJECT_TYPE_TRAINER_LOOK_SIDEWAYS    4 // facing-direction sight + LookSideways behavior
#define OBJECT_TYPE_TRAINER_SPIN             5 // facing-direction sight + Spin behavior (sequence off)
#define OBJECT_TYPE_TRAINER_SPIN_SEQUENCE    6 // facing-direction sight + Spin behavior (sequence on)
#define OBJECT_TYPE_TRAINER_WALKING_SPIN     7 // facing-direction sight; turns while walking (order 0)
#define OBJECT_TYPE_TRAINER_WALKING_SPIN_2   8 // facing-direction sight; turns while walking (order 1)

#endif // POKEHEARTGOLD_CONSTANTS_MAP_OBJECT_H
