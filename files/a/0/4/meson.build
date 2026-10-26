prebuilt_files = [
    '0',
    '2',
    '3',
    '5',
    '7',
    '8',
    '9',
]

foreach f : prebuilt_files
    nitrofs_files += fs.copyfile(f)
endforeach
# [AI-GENERATED / NOT AFFILIATED WITH PRET] map textures from data/area_textures/NNN/
# (PNG, JASC .pal, textures.json; tools/mapkit/mapkit/areatex.py); same bytes as the old
# prebuilt '4'. The depfile lists every file read and the set folders, so adding a
# texture rebuilds without reconfiguring.
mapkit_dir = meson.project_source_root() / 'tools' / 'mapkit' / 'mapkit'
nitrofs_files += custom_target('map_textures',
    output : '4',
    depfile : 'map_textures.d',
    command : [mapkit_sh, mapkit_root, 'areatex', 'pack', '@OUTPUT@', '--depfile', '@DEPFILE@'],
    depend_files : mapkit_sources + files(mapkit_dir / 'areatex.py', mapkit_dir / 'nsbtx.py',
        mapkit_dir / 'nsbmd.py', mapkit_dir / 'sprites.py', mapkit_dir / 'landdata.py'),
)
