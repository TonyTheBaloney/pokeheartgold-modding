prebuilt_files = [
    '0',
    '2',
    '3',
    '4',
    '6',
    '7',
]

foreach f : prebuilt_files
    nitrofs_files += fs.copyfile(f)
endforeach
# [AI-GENERATED / NOT AFFILIATED WITH PRET] land data (terrain cells) from
# data/landdata/NNNN/ (tools/mapkit/mapkit/landdata.py); same bytes as the old prebuilt '5'.
# The pack step writes a depfile listing every file it read and the cell folders, so
# adding, removing or replacing a cell's files (terrain.bdhc -> heights.json after
# `mapkit terrain import`) rebuilds without reconfiguring.
mapkit_dir = meson.project_source_root() / 'tools' / 'mapkit' / 'mapkit'
nitrofs_files += custom_target('land_data',
    output : '5',
    depfile : 'land_data.d',
    command : [mapkit_sh, mapkit_root, 'landdata', 'pack', '@OUTPUT@', '--depfile', '@DEPFILE@'],
    depend_files : mapkit_sources + files(mapkit_dir / 'landdata.py', mapkit_dir / 'bdhc.py'),
)

# [AI-GENERATED / NOT AFFILIATED WITH PRET] effect animation scripts (a/0/6/1: status,
# weather, stat changes...) from data/battle_anims/effects/NNNN_*.anim; see
# docs/modding/move-animations.md.
nitrofs_files += custom_target('battle_anims_effects',
    output : '1',
    depfile : 'battle_anims_effects.d',
    command : [battleanim_py, 'build', meson.project_source_root() / 'data' / 'battle_anims' / 'effects',
        '@OUTPUT@', '--depfile', '@DEPFILE@'],
    depend_files : files('../../../../tools/battleanim/battleanim.py'),
)
