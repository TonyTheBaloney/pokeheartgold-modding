prebuilt_files = [
    '9',
]

# [AI-GENERATED / NOT AFFILIATED WITH PRET] battle backgrounds (a/0/0/7) and battle sprites
# (a/0/0/8), built from the folders in graphics/ (PNG, JASC .pal, JSON; members.json gives
# the order). See docs/modding/graphics-sources.md.
foreach narc : [['7', 'battle_backgrounds'], ['8', 'battle_sprites']]
    nitrofs_files += custom_target(narc[1],
        input : files('../../../../graphics' / narc[1] / 'members.json'),
        output : narc[0],
        command : [
            narcgfx_py, 'build', '@INPUT@', '@OUTPUT@',
            '--nitrogfx', nitrogfx_exe,
            '--nitroarc', nitroarc_exe,
            '--work', '@PRIVATE_DIR@',
            '--depfile', '@DEPFILE@',
        ],
        depfile : narc[1] + '.d',
        depend_files : narcgfx_depends,
    )
endforeach

foreach f : prebuilt_files
    nitrofs_files += fs.copyfile(f)
endforeach

# [AI-GENERATED / NOT AFFILIATED WITH PRET] trainer back sprites (a/0/0/6), built from
# graphics/trainers (PNG, JASC .pal) and data/trainer_graphics/back_pics.json, pokeemerald-style.
# See docs/modding/trainer-classes.md.
nitrofs_files += custom_target('trainer_back_pics',
    input : files('../../../../data/trainer_graphics/back_pics.json'),
    output : '6',
    command : [
        trainer_pics_py, 'build', 'back', '@INPUT@', '@OUTPUT@',
        '--graphics', meson.project_source_root() / 'graphics' / 'trainers',
        '--include', meson.project_source_root() / 'include',
        '--nitrogfx', nitrogfx_exe,
        '--nitroarc', nitroarc_exe,
        '--work', '@PRIVATE_DIR@',
        '--depfile', '@DEPFILE@',
    ],
    depfile : 'trainer_back_pics.d',
    depend_files : trainer_pics_depends,
)
