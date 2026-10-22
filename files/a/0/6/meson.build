prebuilt_files = [
    '0',
    '1',
    '2',
    '3',
    '4',
    '6',
    '7',
]

foreach f : prebuilt_files
    nitrofs_files += fs.copyfile(f)
endforeach
# [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] land data (terrain cells) from
# data/landdata/NNNN/ (tools/mapkit/mapkit/landdata.py); same bytes as the old prebuilt '5'.
landdata_files = run_command(mapkit_sh, mapkit_root, 'landdata', 'files', check : true).stdout().strip().split('\n')
nitrofs_files += custom_target('land_data',
    input : landdata_files,
    output : '5',
    command : [mapkit_sh, mapkit_root, 'landdata', 'pack', '@OUTPUT@'],
    depend_files : mapkit_sources + files(meson.project_source_root() / 'tools' / 'mapkit' / 'mapkit' / 'landdata.py'),
)
