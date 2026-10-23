prebuilt_files = [
    '0',
    '1',
    '2',
    '3',
    '4',
    '9',
]

foreach f : prebuilt_files
    nitrofs_files += fs.copyfile(f)
endforeach

# [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] trainer front sprites (a/0/5/8), built from
# graphics/trainers (PNG, JASC .pal) and data/trainer_graphics/front_pics.json, pokeemerald-style.
# See docs/modding/trainer-classes.md.
nitrofs_files += custom_target('trainer_front_pics',
    input : files('../../../../data/trainer_graphics/front_pics.json'),
    output : '8',
    command : [
        trainer_pics_py, 'build', 'front', '@INPUT@', '@OUTPUT@',
        '--graphics', meson.project_source_root() / 'graphics' / 'trainers',
        '--include', meson.project_source_root() / 'include',
        '--nitrogfx', nitrogfx_exe,
        '--nitroarc', nitroarc_exe,
        '--work', '@PRIVATE_DIR@',
        '--depfile', '@DEPFILE@',
    ],
    depfile : 'trainer_front_pics.d',
    depend_files : trainer_pics_depends,
)
