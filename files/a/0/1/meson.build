prebuilt_files = [
    '3',
    '4',
    '5',
    '9',
]

foreach f : prebuilt_files
    nitrofs_files += fs.copyfile(f)
endforeach

# [AI-GENERATED / NOT AFFILIATED WITH PRET] move animation scripts (a/0/1/0) from
# data/battle_anims/moves/NNNN_*.anim; see docs/modding/move-animations.md. The depfile
# lists every script and the folder, so adding or removing one rebuilds without reconfiguring.
nitrofs_files += custom_target('battle_anims_moves',
    output : '0',
    depfile : 'battle_anims_moves.d',
    command : [battleanim_py, 'build', meson.project_source_root() / 'data' / 'battle_anims' / 'moves',
        '@OUTPUT@', '--depfile', '@DEPFILE@'],
    depend_files : files('../../../../tools/battleanim/battleanim.py'),
)
