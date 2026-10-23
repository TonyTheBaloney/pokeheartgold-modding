# [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] claude-opus-5-5, 2026-10-23
# The sound archive, built from sound/ (pokeemerald-style): sound/sound_data.json lists
# every sequence, bank and wave archive; tools/sound/sdat.py packs them, converting
# .mid sequences and .json banks / wave archives (with their WAV samples) on the way.
# Unchanged sources give the retail archive byte for byte. See docs/modding/music.md.
sdat_py = find_program(meson.project_source_root() / 'tools' / 'sound' / 'sdat.py')
sound_data_sdat = custom_target('gs_sound_data.sdat',
    input : meson.project_source_root() / 'sound' / 'sound_data.json',
    output : 'gs_sound_data.sdat',
    depfile : 'gs_sound_data.sdat.d',
    command : [sdat_py, 'pack', '@INPUT@', '@OUTPUT@', '--depfile', '@DEPFILE@',
               '--check-header', meson.project_source_root() / 'include' / 'constants' / 'sndseq.h'],
    depend_files : files('../../../tools/sound/sdat.py', '../../../tools/sound/sseq.py',
                         '../../../tools/sound/sbnk.py', '../../../tools/sound/swar.py',
                         '../../../include/constants/sndseq.h'),
)
nitrofs_files += sound_data_sdat
