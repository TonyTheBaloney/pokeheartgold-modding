#include "type_icon_resources.h"

#include "global.h"

static int GetMoveTypeAndCategoryIconCellFileId(void);
static int GetMoveTypeAndCategoryIconAnimFileId(void);

static const u8 sMoveCategoryGfxPlttOverrides[3] = { 0, 1, 0 };

static const int sMoveCategoryGfxCharFileIds[3] = { 244, 246, 245 };

static const int sTypeIconGfxCharFileIds[23] = {
    234, 225, 227, 235, 229, 237, 231, 228, 238, 236, 226, 241, 233, 222, 223, 230, 221, 224, 240, 219, 220, 232, 239
};

static const u8 sTypeIconGfxPlttOverrides[23] = { 0, 0, 1, 1, 0, 0, 2, 1, 0, 2, 0, 1, 2, 0, 1, 1, 2, 0, 0, 1, 1, 2, 0 };

int TypeIconGfx_GetCharFileId(int type) {
    GF_ASSERT((u32)type < NELEMS(sTypeIconGfxCharFileIds));
    return sTypeIconGfxCharFileIds[type];
}

int GetMoveTypeAndCategoryIconPlttFileId(void) {
    return 74;
}

static int GetMoveTypeAndCategoryIconCellFileId(void) {
    return 242;
}

static int GetMoveTypeAndCategoryIconAnimFileId(void) {
    return 243;
}

u32 TypeIconGfx_GetPlttOverride(u32 type) {
    GF_ASSERT(type < NELEMS(sTypeIconGfxPlttOverrides));
    return sTypeIconGfxPlttOverrides[type];
}

NarcId TypeIconGfx_GetNarcId(void) {
    return NARC_a_0_0_8;
}

void SpriteSystem_LoadMoveTypeIconCharResObj(SpriteSystem *system, SpriteManager *manager, NNS_G2D_VRAM_TYPE vram, int type, int resource) {
    NarcId narc = TypeIconGfx_GetNarcId();
    int file = TypeIconGfx_GetCharFileId(type);
    SpriteSystem_LoadCharResObj(system, manager, narc, file, TRUE, vram, resource);
}

void SpriteSystem_LoadMoveTypeAndCategoryIconsPltt(SpriteSystem *system, SpriteManager *manager, int vram, int resource) {
    NarcId narc = TypeIconGfx_GetNarcId();
    int file = GetMoveTypeAndCategoryIconPlttFileId();
    SpriteSystem_LoadPlttResObj(system, manager, narc, file, FALSE, 3, vram, resource);
}

void SpriteSystem_LoadMoveTypeAndCategoryIconsPlttToBuffer(PaletteData *palette, int buffer, SpriteSystem *system, SpriteManager *manager, int vram, int resource) {
    NarcId narc = TypeIconGfx_GetNarcId();
    int file = GetMoveTypeAndCategoryIconPlttFileId();
    SpriteSystem_LoadPaletteBuffer(palette, (PaletteBufferId)buffer, system, manager, narc, file, FALSE, 3, vram, resource);
}

void SpriteSystem_LoadMoveTypeAndCategoryIconsCellAndAnim(SpriteSystem *system, SpriteManager *manager, int cell, int animation) {
    NarcId narc = TypeIconGfx_GetNarcId();
    int file = GetMoveTypeAndCategoryIconCellFileId();
    SpriteSystem_LoadCellResObj(system, manager, narc, file, TRUE, cell);
    narc = TypeIconGfx_GetNarcId();
    file = GetMoveTypeAndCategoryIconAnimFileId();
    SpriteSystem_LoadAnimResObj(system, manager, narc, file, TRUE, animation);
}

void SpriteManager_UnloadMoveTypeIconCharResObjByTag(SpriteManager *manager, int resource) {
    SpriteManager_UnloadCharObjById(manager, resource);
}

void SpriteManager_UnloadMoveTypeAndCategoryIconPlttResObjByTag(SpriteManager *manager, int resource) {
    SpriteManager_UnloadPlttObjById(manager, resource);
}

void SpriteManager_UnloadMoveTypeAndCategoryIconCellAndAnimResObjsByTags(SpriteManager *manager, int cell, int animation) {
    SpriteManager_UnloadCellObjById(manager, cell);
    SpriteManager_UnloadAnimObjById(manager, animation);
}

ManagedSprite *SpriteSystem_CreateMoveTypeIconSprite(SpriteSystem *system, SpriteManager *manager, int type, ManagedSpriteTemplate *template) {
    ManagedSpriteTemplate copy = *template;
    copy.pal = TypeIconGfx_GetPlttOverride(type);
    return SpriteSystem_NewSprite(system, manager, &copy);
}

void MoveTypeIconSprite_DeleteAndFreeResources(ManagedSprite *sprite) {
    Sprite_DeleteAndFreeResources(sprite);
}

int GetMoveCategoryIconGfxCharFileId(u32 category) {
    GF_ASSERT(category < NELEMS(sMoveCategoryGfxCharFileIds));
    return sMoveCategoryGfxCharFileIds[category];
}

u32 GetMoveCategoryIconGfxPlttOverride(u32 category) {
    GF_ASSERT(category < NELEMS(sMoveCategoryGfxPlttOverrides));
    return sMoveCategoryGfxPlttOverrides[category];
}

NarcId GetMoveCategoryIconGfxNarcId(void) {
    return NARC_a_0_0_8;
}

void SpriteSystem_LoadMoveCategoryIconCharResObj(SpriteSystem *system, SpriteManager *manager, int vram, int category, int resource) {
    NarcId narc = GetMoveCategoryIconGfxNarcId();
    int file = GetMoveCategoryIconGfxCharFileId(category);
    SpriteSystem_LoadCharResObj(system, manager, narc, file, TRUE, vram, resource);
}

void SpriteManager_UnloadMoveCategoryIconCharResObjByTag(SpriteManager *manager, int resource) {
    SpriteManager_UnloadCharObjById(manager, resource);
}

void MoveCategoryIconSprite_DeleteAndFreeResources(ManagedSprite *sprite) {
    Sprite_DeleteAndFreeResources(sprite);
}
