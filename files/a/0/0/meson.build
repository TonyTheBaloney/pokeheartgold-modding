prebuilt_files = [
    '7',
    '8',
    '9',
]

foreach f : prebuilt_files
    nitrofs_files += fs.copyfile(f)
endforeach

# [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] trainer back sprites (a/0/0/6), built from
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
