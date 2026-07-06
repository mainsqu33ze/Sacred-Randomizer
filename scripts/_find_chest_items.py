#!/usr/bin/env python3
"""Find chest item data tables in the FE8 ROM."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fe8rom import ROM, ROM_BASE, CHAPTER_DATA_TABLE, CHAPTER_INFO_SIZE, CHAPTER_ASSET_TABLE, ITEM_NAMES
import struct

rom = ROM('Fire_Emblem_8.GBA')
data = rom.data

# Step 1: First, get all GiveItem event locations
print("=== GiveItem events ===")
hdr = b'\x40\x0A\x00\x00'
pos = 0
giveitem_events = []  # list of (raw_offset, item_id, event_ptr)
while True:
    pos = data.find(hdr, pos, len(data))
    if pos == -1 or pos + 20 > len(data):
        break
    if pos >= 8 and data[pos-8:pos-6] == b'\x40\x05':
        pos += 1
        continue
    ptr = struct.unpack_from('<I', data, pos + 4)[0]
    at_8, at_9, at_11 = data[pos + 8], data[pos + 9], data[pos + 11]
    item_id = struct.unpack_from('<I', data, pos + 12)[0]
    if (0x08000000 <= ptr <= 0x08FFFFFF and
        at_8 == 0x40 and at_9 == 0x05 and at_11 == 0x00 and
        0 < item_id < 0xC0):
        giveitem_events.append((pos, item_id, ptr))
    pos += 1

print(f"Total GiveItem events: {len(giveitem_events)}")
print()

# Step 2: Map event script ranges to chapters
# The event data at 0x089Exxxx contains pointers to sub-scripts at 0x089Fxxxx
# Each chapter's event data = pointer table + section data
# The pointer table starts with 8 u32 pointers to sections

asset_off = CHAPTER_ASSET_TABLE - ROM_BASE

for ch_id in range(1, 25):
    ch_off = (CHAPTER_DATA_TABLE - ROM_BASE) + ch_id * CHAPTER_INFO_SIZE
    map_event_data_id = data[ch_off + 0x74]
    
    event_ptr = struct.unpack_from('<I', data, asset_off + map_event_data_id * 4)[0]
    if event_ptr == 0:
        continue
    event_off = event_ptr - ROM_BASE
    
    # Read the 8 section pointers
    sections = []
    for i in range(8):
        off = event_off + i * 4
        if off + 4 > len(data):
            break
        ptr = struct.unpack_from('<I', data, off)[0]
        sections.append(ptr)
    
    # For each section, find all referenced scripts
    # (sections can contain pointers to sub-scripts that contain GiveItem events)
    ch_items = []
    for sec_ptr in sections:
        if sec_ptr == 0:
            continue
        sec_off = sec_ptr - ROM_BASE
        if sec_off < 0 or sec_off >= len(data):
            continue
        
        # Scan this section for references to sub-scripts
        # The section format depends on its type, but we look for pointers to 0x089Fxxxx
        for scan_off in range(sec_off, min(sec_off + 0x200, len(data) - 4), 4):
            val = struct.unpack_from('<I', data, scan_off)[0]
            if 0x089F0000 <= val <= 0x089FFFFF:
                # Found a script pointer - check if any GiveItem is in this script
                sub_off = val - ROM_BASE
                for gi_pos, item_id, ev_ptr in giveitem_events:
                    if sub_off <= gi_pos < sub_off + 0x10000:
                        ch_items.append((gi_pos, item_id, val))
    
    if ch_items:
        # Deduplicate
        seen = set()
        unique_items = []
        for gi_pos, item_id, script_addr in ch_items:
            if gi_pos not in seen:
                seen.add(gi_pos)
                unique_items.append((item_id, script_addr))
        
        names = [f'{ITEM_NAMES.get(it, f"0x{it:02X}")}(0x{it:02X})' for it, _ in unique_items[:6]]
        print(f'Ch{ch_id:2d}: {len(unique_items)} items - {" | ".join(names)}')
    else:
        print(f'Ch{ch_id:2d}: (no GiveItems found)')

print()
print("=== Searching for chest item tables (3-byte entries [x,y,item_id]) ===")

# Step 3: Search for chest tables in the 0x089Exxxx-0x089Fxxxx range
# FE8 chest table format: array of [x, y, item_id] (3 bytes each), terminated by 0xFF or 0x000000
# Let's search for sequences of 3-5 entries with reasonable coordinates and valid item IDs

# Known chest chapters from Triangle Attack:
# Ch1: no chests
# Ch2: Member Card (0x71)
# Ch4: Secret Book (0x63)
# Ch5x: ? 
# Ch6: Speedwings (0x64), Talisman (0x66)
# Ch7: Brave Lance (0x28), Knight Crest (0x76)
# Ch8: Elysian Whip (0x77)
# Ch9: Wyrmslayer (0x24)
# Ch10: Silver Blade (0x17), Physic (0x36), Bolting (0x4B)
# Ch12: Hero Crest (0x75), Silver Lance (0x3E)
# Ch13: Body Ring (0x67)
# Ch14: Speedwings (0x64), Physic (0x36)
# Ch15: Silver Sword (0x1A)
# Ch17: Warp (0x2B), Restore (0x37)?
# Ch19: Goddess Icon (0x62)
# Ch20: Elixir (0x6E)

known_chest_items = {
    0x71: 'Member Card', 0x63: 'Secret Book', 0x64: 'Speedwings',
    0x66: 'Talisman', 0x28: 'Brave Lance', 0x76: 'Knight Crest',
    0x77: 'Elysian Whip', 0x24: 'Wyrmslayer', 0x17: 'Silver Blade',
    0x36: 'Physic', 0x4B: 'Bolting', 0x75: 'Hero Crest',
    0x3E: 'Silver Lance', 0x67: 'Body Ring', 0x1A: 'Silver Sword',
    0x2B: 'Warp', 0x37: 'Restore', 0x62: 'Goddess Icon',
    0x6E: 'Elixir'
}
known_ids = set(known_chest_items.keys())

# Search for chest tables in the entire 0x08800000-0x08A00000 range
# Format: [x, y, item_id] (3 bytes), terminated by [0, 0, 0] or [0xFF, 0xFF, 0xFF]
for start in range(0x080000, 0x090000 - 30, 3):
    entries = []
    valid = True
    for i in range(8):
        off = start + i * 3
        if off + 3 > len(data):
            valid = False
            break
        x, y, it = data[off], data[off+1], data[off+2]
        if it == 0 and x == 0 and y == 0:
            break  # null terminator
        if it == 0xFF or (it >= 0xC0):
            if i >= 2:
                break  # end of table (terminator)
            valid = False
            break
        if x == 0 and y == 0 and it == 0:
            break
        if x > 50 or y > 50:
            if i >= 2:
                break
            valid = False
            break
        entries.append((x, y, it))
    
    if not valid or len(entries) < 2:
        continue
    
    # Check if at least one item is a known chest item
    known_match = sum(1 for _, _, it in entries if it in known_ids)
    
    if known_match >= 1:
        gba = ROM_BASE + start
        names = [f'{ITEM_NAMES.get(it, f"0x{it:02X}")}({it:02X})' for _, _, it in entries]
        coords = [f'({x},{y})' for x, y, _ in entries]
        print(f'0x{gba:08X}: {len(entries)} entries')
        for i, (n, c) in enumerate(zip(names, coords)):
            marker = ' <-- CHEST!' if entries[i][2] in known_ids else ''
            print(f'  [{i}] {c}: {n}{marker}')

print()
print("=== Searching for [item_id, x, y, 00] format (4-byte entries) ===")
for start in range(0x080000, 0x090000 - 40, 4):
    entries = []
    valid = True
    for i in range(10):
        off = start + i * 4
        if off + 4 > len(data):
            valid = False
            break
        it, x, y, flag = data[off], data[off+1], data[off+2], data[off+3]
        if it == 0 and x == 0 and y == 0:
            break
        if it == 0xFF or it >= 0xC0 or x > 50 or y > 50:
            if i >= 2:
                break
            valid = False
            break
        if flag != 0 and not (flag == 0xFF and i == len(entries)):
            # Entries with non-zero flags might not be chests
            pass
        entries.append((x, y, it, flag))
    
    if not valid or len(entries) < 2:
        continue
    
    known_match = sum(1 for _, _, it, _ in entries if it in known_ids)
    if known_match >= 1:
        gba = ROM_BASE + start
        names = [f'{ITEM_NAMES.get(it, f"0x{it:02X}")}' for _, _, it, _ in entries]
        print(f'0x{gba:08X}: {len(entries)} entries - {" | ".join(names[:6])}')
        for i, (x, y, it, flag) in enumerate(entries[:6]):
            marker = ' <-- CHEST!' if it in known_ids else ''
            print(f'  [{i}] ({x},{y}) flag=0x{flag:02X}: {ITEM_NAMES.get(it, f"0x{it:02X}")}{marker}')
