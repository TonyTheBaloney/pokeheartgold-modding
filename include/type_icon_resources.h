#ifndef POKEHEARTGOLD_TYPE_ICON_RESOURCES_H
#define POKEHEARTGOLD_TYPE_ICON_RESOURCES_H

#include "sprite_system.h"

int TypeIconGfx_GetCharFileId(int moveType);
int GetMoveTypeAndCategoryIconPlttFileId(void);
NarcId TypeIconGfx_GetNarcId(void);
u32 TypeIconGfx_GetPlttOverride(u32 type);
void SpriteSystem_LoadMoveTypeAndCategoryIconsPlttToBuffer(PaletteData *paletteData, int buffer, SpriteSystem *spriteSystem, SpriteManager *spriteManager, int vram, int resource);
void SpriteSystem_LoadMoveTypeAndCategoryIconsCellAndAnim(SpriteSystem *spriteSystem, SpriteManager *spriteManager, int cell, int animation);
void SpriteSystem_LoadMoveTypeIconCharResObj(SpriteSystem *spriteSystem, SpriteManager *spriteManager, NNS_G2D_VRAM_TYPE vramType, int type, int resource); // load type icon graphics?
void SpriteSystem_LoadMoveTypeAndCategoryIconsPltt(SpriteSystem *spriteSystem, SpriteManager *spriteManager, int vram, int resId);
void SpriteManager_UnloadMoveTypeIconCharResObjByTag(SpriteManager *spriteManager, int resource);
void SpriteManager_UnloadMoveTypeAndCategoryIconPlttResObjByTag(SpriteManager *spriteManager, int resource);
void SpriteManager_UnloadMoveTypeAndCategoryIconCellAndAnimResObjsByTags(SpriteManager *spriteManager, int cell, int animation);
ManagedSprite *SpriteSystem_CreateMoveTypeIconSprite(SpriteSystem *spriteSystem, SpriteManager *spriteManager, int type, ManagedSpriteTemplate *spriteTemplate);
void MoveTypeIconSprite_DeleteAndFreeResources(ManagedSprite *managedSprite);
void MoveCategoryIconSprite_DeleteAndFreeResources(ManagedSprite *managedSprite);
int GetMoveCategoryIconGfxCharFileId(u32 category);
u32 GetMoveCategoryIconGfxPlttOverride(u32 category);
NarcId GetMoveCategoryIconGfxNarcId(void);
void SpriteSystem_LoadMoveCategoryIconCharResObj(SpriteSystem *spriteSystem, SpriteManager *spriteManager, int vram, int category, int resId);
void SpriteManager_UnloadMoveCategoryIconCharResObjByTag(SpriteManager *spriteManager, int resource);

#endif // POKEHEARTGOLD_TYPE_ICON_RESOURCES_H
