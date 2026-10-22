# [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] claude-opus-5-5, 2026-10-21
# Per-map folders (pokeemerald-style data/maps/<MapName>/). Each line of
# maps.txt names a folder and the original bank names. The zone_event JSON and
# the MapHeader entry are generated from map.json; scripts and text are copied
# back to their original base names, so every NARC is unchanged.
# See tools/mapkit/mapkit/layout.py.

mapkit_sh = find_program(meson.project_source_root() / 'tools' / 'mapkit' / 'mapkit.sh')
mapkit_root = ['--root', meson.project_source_root()]
# regenerate when the generator changes
mapkit_sources = files(
    '../../tools/mapkit/mapkit.sh',
    '../../tools/mapkit/mapkit/cli.py',
    '../../tools/mapkit/mapkit/layout.py',
    '../../tools/mapkit/mapkit/repo.py',
)

maps_zone_event_json = []
maps_scr_seq_asm = []
maps_text_banks = []
maps_text_bank_names = []
maps_headers = []

foreach line : fs.read('maps.txt').splitlines()
    line = line.strip()
    if line == '' or line.startswith('#')
        continue
    endif
    parts = line.split()
    dir = parts[0]
    map_id = parts[1]
    banks = {}
    foreach kv : parts
        if kv.contains('=')
            banks += { kv.split('=')[0]: kv.split('=')[1] }
        endif
    endforeach

    # A bank written @Folder belongs to another map's folder; only the owner builds it.
    if not banks['events'].startswith('@')
        maps_zone_event_json += custom_target('events_' + map_id,
            input: dir / 'map.json',
            output: banks['events'] + '.json',
            command: [mapkit_sh, mapkit_root, 'gen-events', '@INPUT@', '@OUTPUT@'],
            depend_files: mapkit_sources,
        )
    endif
    maps_headers += custom_target('header_' + map_id,
        input: [dir / 'map.json', 'maps.txt'],
        output: 'header_' + map_id + '.h',
        command: [mapkit_sh, mapkit_root, 'gen-header', '@INPUT0@', '@OUTPUT@'],
        depend_files: mapkit_sources,
    )
    if not banks['scripts'].startswith('@')
        maps_scr_seq_asm += fs.copyfile(dir / 'scripts.inc', banks['scripts'] + '.s')
    endif
    if not banks['init'].startswith('@')
        maps_scr_seq_asm += fs.copyfile(dir / 'map_scripts.inc', banks['init'] + '.s')
    endif
    if not banks['text'].startswith('@')
        maps_text_banks += fs.copyfile(dir / 'text.json', banks['text'] + '.json')
        maps_text_bank_names += banks['text'] + '.json'
    endif
endforeach
