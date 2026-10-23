build_dir = meson.current_build_dir()

############################################################
###                      MAP_MATRIX                      ###
############################################################
# [AI-GENERATED / NOT AFFILIATED WITH PRET] map matrices come from data/layouts
# (tools/mapkit/mapkit/layouts.py): each layout.json is written back to its
# original <base>.bin, so the NARC and its .naix names are unchanged.
layout_jsons = []
foreach line : fs.read(meson.project_source_root() / 'data' / 'layouts' / 'layouts.txt').splitlines()
    line = line.strip()
    if line != '' and not line.startswith('#')
        layout_jsons += meson.project_source_root() / 'data' / 'layouts' / line.split()[0] / 'layout.json'
    endif
endforeach

map_matrix_narc = custom_target('map_matrix.narc',
    command : [
        mapkit_sh, mapkit_root, 'layouts', 'pack', '@OUTPUT0@',
        '--nitroarc', nitroarc_exe,
        '--work', '@PRIVATE_DIR@',
    ],
    input : layout_jsons,
    output : [
        'map_matrix.narc',
        'map_matrix.naix'
    ],
    depend_files : mapkit_sources + files(meson.project_source_root() / 'data' / 'layouts' / 'layouts.txt',
        meson.project_source_root() / 'tools' / 'mapkit' / 'mapkit' / 'layouts.py',
        meson.project_source_root() / 'tools' / 'mapkit' / 'mapkit' / 'matrix.py'),
)

nitrofs_files += map_matrix_narc
naix_headers += map_matrix_narc[1]

