#!/usr/bin/env python3
"""Map each chapter's event data to its UD arrays."""
import sys, os, struct
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fe8rom import ROM, ROM_BASE, CHAPTER_DATA_TABLE, CHAPTER_INFO_SIZE

rom_path = r'D:\Fire_Emblem\Custom_randomizer\Fire_Emblem_the_Sacred_Stones.GBA'
rom = ROM(rom_path)
data = rom.data

ASSET_TABLE = 0x088B363C
asset_off = ASSET_TABLE - ROM_BASE


def is_valid_ud(addr):
    if addr == 0:
        return False
    o = addr - ROM_BASE
    if o < 0 or o + 20 > len(data):
        return False
    if addr >= 0x088D0000:
        return False
    chunk = data[o:o+20]
    if all(b == 0 for b in chunk):
        return False
    char_idx = chunk[0]
    class_idx = chunk[1]
    return char_idx > 0 and char_idx <= 114 and class_idx <= 114


def count_ud(addr):
    if not is_valid_ud(addr):
        return 0
    o = addr - ROM_BASE
    cnt = 0
    for i in range(100):
        pos = o + i * 20
        if pos + 20 > len(data):
            return cnt
        chunk = data[pos:pos+20]
        if all(b == 0 for b in chunk):
            return cnt
        ci = chunk[0]
        cj = chunk[1]
        if ci == 0 or ci > 114 or cj > 114:
            return cnt
        cnt += 1
    return cnt


chapter_map = {
    0: 'Prologue (The Fall of Renais)',
    1: 'Ch1: Escape!',
    2: 'Ch2: The Protected',
    3: 'Ch3: Bandits of Borgo',
    4: 'Ch4: Ancient Horrors',
    5: 'Ch5: Empire\'s Reach',
    6: 'Ch5x: The Lost Prince',
    7: 'Ch6: Triumph',
    8: 'Ch7: Waterside Renvall',
    9: 'Ch8: It\'s a Trap!',
    10: 'Ch9: Distant Blade',
    11: 'Ch10: Turning Traitor',
    12: 'Ch11: Creeping Darkness',
    13: 'Ch12: Village of Silence',
    14: 'Ch13: Hamill Canyon',
    15: 'Ch14: Sacred Stone',
    16: 'Ch15: Scorched Sand',
    17: 'Ch16: Ruler of the Sea (merge)',
    18: 'Ch17: River of Regrets (Eph)',
    19: 'Ch18: Two Faces of Evil (Eph)',
    20: 'Ch19: Last Hope (Eph)',
    21: 'Ch20: Darkling Woods (Eph)',
    22: 'Ch20: Darkling Woods (Shared)',
    23: 'Ch9: Ruled by Madness (Eph)',
    24: 'Ch10: Island of the Dead (Eph)',
    25: 'Ch11: Phantom Ship (Eph)',
    26: 'Ch12: Piano (Eph)',
    27: 'Ch13: Fluorspar\'s Oath (Eph)',
    28: 'Ch14: Father and Son (Eph)',
    29: 'Ch15: Scorched Sand (Eph)',
    30: 'Ch16: Ruler of the Sea (Eph)',
    31: 'Ch17: River of Regrets (Final)',
    32: 'Ch18: Two Faces of Evil (Final)',
    33: 'Ch19: Last Hope (Final)',
    34: 'Ch20: Darkling Woods (Final)',
}

# Step 1: Build LOAD command index
ud_to_scripts = {}
for pos in range(len(data) - 8):
    cmd = data[pos]
    if 0x40 <= cmd <= 0x43 and data[pos+1] == 0x2C:
        ptr = struct.unpack_from('<I', data, pos+4)[0]
        if 0x088B0000 <= ptr < 0x088D0000:
            gba_pos = ROM_BASE + pos
            ud_to_scripts.setdefault(ptr, []).append(gba_pos)

print(f'Total unique UD arrays via LOAD commands: {len(ud_to_scripts)}')

# Build reverse: script address -> UD arrays it references
script_to_uds = {}
for ud_addr, script_addrs in ud_to_scripts.items():
    for sa in script_addrs:
        script_to_uds.setdefault(sa, set()).add(ud_addr)

print(f'Total event script addresses with LOAD commands: {len(script_to_uds)}')

# Step 2: For each chapter, find all event scripts in its event data
print()
print('=' * 100)
print('CHAPTER TO UD ARRAY MAPPING')
print('=' * 100)
print()

all_ud_map = {}

for ch in range(35):
    ch_off = (CHAPTER_DATA_TABLE - ROM_BASE) + ch * CHAPTER_INFO_SIZE
    map_event_data_id = data[ch_off + 0x74]
    gmap_event_id = data[ch_off + 0x75]

    name_ptr = struct.unpack_from('<I', data, ch_off)[0]
    name_off = name_ptr - ROM_BASE
    internal_name = bytes(b for b in data[name_off:name_off+32] if b != 0).decode('ascii', errors='replace')

    event_data_ptr = struct.unpack_from('<I', data, asset_off + map_event_data_id * 4)[0]
    event_data_off = event_data_ptr - ROM_BASE

    gmap_ptr = struct.unpack_from('<I', data, asset_off + gmap_event_id * 4)[0]
    gmap_off = gmap_ptr - ROM_BASE

    chapter_name = chapter_map.get(ch, 'Unknown')

    print(f'Ch{ch:2d} ({internal_name:6s}): {chapter_name}')
    print(f'     mapEventDataId={map_event_data_id:3d} -> EventData=0x{event_data_ptr:08X}')
    print(f'     gmapEventId={gmap_event_id:3d} -> GMap=0x{gmap_ptr:08X}')

    # Direct UD arrays in event data
    direct_uds = {}
    for off in range(0, 0x400, 4):
        val = struct.unpack_from('<I', data, event_data_off + off)[0]
        if 0x088B0000 <= val < 0x088D0000:
            cnt = count_ud(val)
            if cnt > 0 and val not in direct_uds:
                direct_uds[val] = cnt

    # UD arrays via LOAD commands in event scripts
    indirect_uds = {}
    for off in range(0, 0x400, 4):
        val = struct.unpack_from('<I', data, event_data_off + off)[0]
        if 0x089E0000 <= val < 0x08A00000:
            if val in script_to_uds:
                for ud_addr in script_to_uds[val]:
                    cnt = count_ud(ud_addr)
                    if cnt > 0 and ud_addr not in indirect_uds:
                        indirect_uds[ud_addr] = (cnt, val)

    # GMap UD arrays
    gmap_uds = {}
    for off in range(0, 0x200, 4):
        val = struct.unpack_from('<I', data, gmap_off + off)[0]
        if 0x088B0000 <= val < 0x088D0000:
            cnt = count_ud(val)
            if cnt > 0 and val not in gmap_uds:
                gmap_uds[val] = cnt

    all_ch_uds = set()

    if direct_uds:
        print('     Direct UD arrays in event data:')
        for addr, cnt in sorted(direct_uds.items()):
            label = ''
            for block_start in range(0, 0x400, 0x30):
                for ud_off in [0x28, 0x2C]:
                    check_addr = struct.unpack_from('<I', data, event_data_off + block_start + ud_off)[0]
                    if check_addr == addr:
                        label = f' [block+{block_start:#04x}+{ud_off:#04x}]'
            print(f'      0x{addr:08X} ({cnt:2d} entries){label}')
            all_ch_uds.add(addr)

    if indirect_uds:
        print('     UD arrays via script LOAD commands:')
        for addr, (cnt, script_addr) in sorted(indirect_uds.items()):
            print(f'      0x{addr:08X} ({cnt:2d} entries) [from script 0x{script_addr:08X}]')
            all_ch_uds.add(addr)

    if gmap_uds:
        print('     UD arrays in GMap data:')
        for addr, cnt in sorted(gmap_uds.items()):
            print(f'      0x{addr:08X} ({cnt:2d} entries)')
            all_ch_uds.add(addr)

    if not direct_uds and not indirect_uds and not gmap_uds:
        print('     (no UD arrays found)')
    else:
        for addr in all_ch_uds:
            all_ud_map.setdefault(addr, set()).add(f'Ch{ch}({internal_name})')

    print()

# Print reverse mapping
print()
print('=' * 100)
print('REVERSE UD ARRAY TO CHAPTER MAPPING')
print('=' * 100)
print()
print(f'All UD arrays referenced by each chapter:')
for addr in sorted(all_ud_map.keys()):
    chapters = sorted(all_ud_map[addr])
    cnt = count_ud(addr)
    print(f'  0x{addr:08X} ({cnt:2d} entries): {", ".join(chapters)}')
