# [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] move data from JSON (tools/pokedata)
nitrofs_files += custom_target('waza_tbl.narc',
    input : files('battle_moves.json'),
    output : 'waza_tbl.narc',
    command : [
        pokedata_py, 'moves', '@INPUT@', '@OUTPUT@',
        '--include', meson.project_source_root() / 'include',
        '--nitroarc', nitroarc_exe,
        '--work', '@PRIVATE_DIR@',
    ],
    depend_files : pokedata_depends,
)
