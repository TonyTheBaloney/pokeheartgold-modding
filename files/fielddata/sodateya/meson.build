# [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] egg moves from JSON (kept with the
# other species data in files/poketool/personal/)
nitrofs_files += custom_target('kowaza_list.narc',
    input : files('../../poketool/personal/egg_moves.json'),
    output : 'kowaza_list.narc',
    command : [
        pokedata_py, 'egg-moves', '@INPUT@', '@OUTPUT@',
        '--include', meson.project_source_root() / 'include',
        '--nitroarc', nitroarc_exe,
        '--work', '@PRIVATE_DIR@',
    ],
    depend_files : pokedata_depends,
)
