# [AI-GENERATED / LOCAL ONLY / DO NOT UPSTREAM] claude-opus-5-5, 2026-10-22
# Items (pokeemerald-style src/data/items.h, as JSON): data/items/items.json holds every
# item's name, description, data, icon and Gen 3 id; tools/pokedata/items.py makes the
# files the game used to keep separately. See docs/modding/items.md.
items_py = find_program(meson.project_source_root() / 'tools' / 'pokedata' / 'items.py')
items_gen = custom_target('items',
    input : files('items.json'),
    output : ['item_data.csv', 'msg_0222.json', 'msg_0221.json', 'item_narc_ids.h'],
    command : [items_py, 'build', '@INPUT@', '@OUTDIR@', '--include', meson.project_source_root() / 'include'],
    depend_files : files('../../tools/pokedata/items.py', '../../include/constants/items.h',
                         '../../include/constants/pokemon.h'),
)
items_csv = items_gen[0]
# item names and descriptions replace these banks in files/msgdata/msg
item_text_banks = [items_gen[1], items_gen[2]]
item_text_bank_names = ['msg_0222.json', 'msg_0221.json']
items_header = items_gen[3]   # included by src/item.c
