#include "mart_bag_task.h"

#include "global.h"

#include "field/fieldmap.h"

#include "bag_view.h"
#include "heap.h"
#include "overlay_03.h"
#include "task.h"

typedef struct MartReturnEnv {
    u8 unk_00[4];
    BagView *bagView;
    u8 unk_08[0x26A];
    u8 state;
    u8 unk_273[0x2D];
    u16 *result;
} MartReturnEnv;

static BOOL Task_Bag_SellMenu_WaitBagView(FieldSystem *fieldSystem, MartReturnEnv *env);
static void Task_Bag_SellMenu_Return(TaskManager *taskManager);

BOOL Task_Bag_SellMenu(TaskManager *taskManager) {
    FieldSystem *fieldSystem = TaskManager_GetFieldSystem(taskManager);
    MartReturnEnv *env = TaskManager_GetEnvironment(taskManager);
    switch (env->state) {
    case 24:
        env->state = Task_Bag_SellMenu_WaitBagView(fieldSystem, env);
        break;
    case 25:
        Task_Bag_SellMenu_Return(taskManager);
        break;
    }
    return FALSE;
}

static BOOL Task_Bag_SellMenu_WaitBagView(FieldSystem *fieldSystem, MartReturnEnv *env) {
    if (FieldSystem_ApplicationIsRunning(fieldSystem)) {
        return 24;
    }
    if (env->result != NULL) {
        env->result[1] = BagView_GetSellCount(env->bagView);
    }
    Heap_Free(env->bagView);
    FieldSystem_LoadFieldOverlay(fieldSystem);
    return 25;
}

static void Task_Bag_SellMenu_Return(TaskManager *taskManager) {
    FieldSystem *fieldSystem = TaskManager_GetFieldSystem(taskManager);
    MartReturnEnv *env = TaskManager_GetEnvironment(taskManager);
    if (FieldSystem_IsOverworldRestored(fieldSystem)) {
        FieldMap_FadeScreen(1);
        TaskManager_Jump(taskManager, Task_Mart, env);
        env->state = 26;
    }
}
