#!/usr/bin/env python3
"""Explore the ROM to find promotion table, chest item data, and promotion items."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fe8rom import ROM, ROM_BASE, JID, PID, ITEM_TABLE_ADDR, ITEM_DATA_SIZE, UNIT_DEF_SIZE
from fe8rom import CHARACTER_TABLE_ADDR, CLASS_TABLE_ADDR, CHAPTER_DATA_TABLE, CHAPTER_INFO_SIZE
import struct

rom_path = r'D:\Fire_Emblem\Custom_randomizer\Fire_Emblem_the_Sacred_Stones.GBA'
rom = ROM(rom_path)

# 1. Find ALL items with weapon_type == 9 (non-weapon items, includes promotion items)
print("=== Items with type 9 (non-weapon/promotion) ===")
promo_item_ids = []
for item_id in range(256):
    off = (ITEM_TABLE_ADDR - ROM_BASE) + item_id * ITEM_DATA_SIZE
    if off + ITEM_DATA_SIZE > len(rom.data):
        break
    raw = rom.data[off:off+ITEM_DATA_SIZE]
    stored_id = raw[6]
    wep_type = raw[7]
    uses = raw[0x14]
    if stored_id != item_id:
        continue
    if wep_type == 9 and uses > 0:
        might = raw[0x15]
        hit = raw[0x16]
        weight = raw[0x17]
        crit = raw[0x18]
        enc_range = raw[0x19]
        attributes = struct.unpack_from('<I', raw, 8)[0]
        wep_effect = raw[0x1F]
        name_text_id = struct.unpack_from('<H', raw, 0)[0]
        print(f"  Item 0x{item_id:02X} ({item_id:3d}): uses={uses} mt={might} hit={hit} wt={weight} crit={crit} rng={enc_range} attr=0x{attributes:08X} eff={wep_effect}")
        promo_item_ids.append(item_id)

# 2. Search for promotion table in ROM data
# The promotion table is a list of (item_id, class_id) pairs terminated by 00 00
# It maps which classes can be promoted by which items
# Search for it by looking for a sequence of (item_id, class_id) pairs
print("\n=== Searching for promotion table ===")
# Known possible addresses for FE8U promotion table
candidates = [
    0x0880C2BC, 0x0880C3BC, 0x0880C4BC, 0x0880BF10,
    0x0880B0A0, 0x0880C000, 0x0880C200, 0x0880C100,
    0x0880C2A0, 0x0880C2C0, 0x0880C2B0,
]

# Also search for the table by scanning
# The table should contain Master Seal (0x69) entries for many common classes
print("\nSearching for promotion table by scanning...")
for start_off in range(0x800000, 0x8A0000, 4):
    if start_off + 4 > len(rom.data):
        break
    # Look for a sequence that looks like item_id/class_id pairs
    # Check if this contains a Master Seal entry for a known class
    pos = start_off
    entries = []
    valid = True
    seen_items = set()
    while pos + 2 <= len(rom.data):
        item_id = rom.data[pos]
        class_id = rom.data[pos + 1]
        if item_id == 0 and class_id == 0:
            break
        if item_id not in range(0, 256) or class_id not in range(0, 128):
            valid = False
            break
        entries.append((item_id, class_id))
        seen_items.add(item_id)
        pos += 2
    
    if len(entries) >= 20 and 0x69 in seen_items:
        gba_addr = ROM_BASE + start_off
        print(f"  Found likely promotion table at ROM offset 0x{start_off:06X} (GBA 0x{gba_addr:08X}): {len(entries)} entries, items={sorted(seen_items)}")
        # Show first 30 entries
        for i, (it, cl) in enumerate(entries[:30]):
            print(f"    [{i}] item=0x{it:02X} class=0x{cl:02X}")
        if len(entries) > 30:
            print(f"    ... and {len(entries) - 30} more entries")
        break

# 3. Check chapter data for chest item tables
print("\n=== Checking chapter data for chest/treasure info ===")
# The asset table at 0x088B363C might have chest data
for ch_id in range(1, 35):
    ch_off = (CHAPTER_DATA_TABLE - ROM_BASE) + ch_id * CHAPTER_INFO_SIZE
    if ch_off + CHAPTER_INFO_SIZE > len(rom.data):
        break
    raw = rom.data[ch_off:ch_off+CHAPTER_INFO_SIZE]
    map_event_data_id = raw[0x74]
    gmap_event_id = raw[0x75]
    if ch_id <= 5:
        print(f"  Ch{ch_id}: mapEventDataId={map_event_data_id}, gmapEventId={gmap_event_id}")

# 4. Look for chest tables in the asset table area
print("\n=== Scanning for chest item tables ===")
# Chest tables typically have format: [x,y,item_id] terminated by 00 00 00
# Or: [item_id, x, y]
for start_off in range(0x880000, 0x900000, 4):
    if start_off + 4 > len(rom.data):
        break
    # Check for chest-like pattern: item IDs we know (0x62-0x6A range) at specific positions
    # A chest table might have: count, then entries of (x, y, item_id)
    # Or just flat entries terminated by 0xFF or 0x00
    raw_data = rom.data[start_off:start_off+32]
    
    # Try to find chest table: entries of [item_id, x, y] or [x, y, item_id] format
    # Look for items that are in the healing item range (0x6C= vulnerary) or
    # weapon range (0x10-0x50) or promotion range (0x62-0x6A)
    for stride in [3, 4, 5]:
        if stride == 3:
            # Check for [x, y, item_id] pattern
            item_positions = [2, 5, 8, 11, 14]
        elif stride == 4:
            item_positions = [2, 6, 10, 14, 18]
        else:
            continue
        
        items_found = []
        for i, p in enumerate(item_positions):
            if p < len(raw_data):
                items_found.append(raw_data[p])
        
        # Check if these look like valid item IDs (0-0xFF, with some in known ranges)
        valid_items = [v for v in items_found if 0 < v < 0xC0]
        if len(valid_items) >= 2 and any(0x62 <= v <= 0x6C for v in valid_items):
            # Possible chest table
            if items_found != list(range(len(items_found))):  # not sequential
                pass  # This was too noisy, skip

# 5. Check what item data looks like at 0x08809B10 for Master Seal
print("\n=== Master Seal item data check ===")
master_seal_id = 0x69
off = (ITEM_TABLE_ADDR - ROM_BASE) + master_seal_id * ITEM_DATA_SIZE
if off + ITEM_DATA_SIZE <= len(rom.data):
    raw = rom.data[off:off+ITEM_DATA_SIZE]
    print(f"  Item 0x{master_seal_id:02X}: stored_id={raw[6]} type={raw[7]} uses={raw[0x14]} mt={raw[0x15]} hit={raw[0x16]} wt={raw[0x17]} crit={raw[0x18]} rng={raw[0x19]}")
    attrs = struct.unpack_from('<I', raw, 8)[0]
    print(f"  Attributes: 0x{attrs:08X}")
    if attrs & 0x40:
        print("  -> Has promotion item flag (bit 6)")
    else:
        print("  -> Does NOT have promotion item flag (bit 6)")
    if attrs & 0x80:
        print("  -> Has promotion item flag (bit 7)")
    else:
        print("  -> Does NOT have promotion item flag (bit 7)")

# Check for attribute patterns across all promotion items
print("\n=== Attribute patterns for all type-9 items ===")
for item_id in promo_item_ids[:12]:  # limit output
    off = (ITEM_TABLE_ADDR - ROM_BASE) + item_id * ITEM_DATA_SIZE
    raw = rom.data[off:off+ITEM_DATA_SIZE]
    attrs = struct.unpack_from('<I', raw, 8)[0]
    wep_effect = raw[0x1F]
    print(f"  Item 0x{item_id:02X}: attr=0x{attrs:08X} bin={attrs:032b} effect={wep_effect}")

# 6. Check the CHAPTER_ASSET_TABLE for treasure data
print("\n=== CHAPTER_ASSET_TABLE data ===")
for i in range(30):
    off = (0x088B363C - ROM_BASE) + i * 4
    if off + 4 > len(rom.data):
        break
    ptr = struct.unpack_from('<I', rom.data, off)[0]
    if ptr != 0:
        obj_off = ptr - ROM_BASE
        if 0 <= obj_off < len(rom.data):
            peek = rom.data[obj_off:obj_off+8]
            print(f"  Asset[{i}]: ptr=0x{ptr:08X} -> {[f'0x{b:02x}' for b in peek]}")

# 7. Check what items are in the first few UD arrays (player inventories)
print("\n=== UD array items for early chapters ===")
from randomizer import _scan_ud_arrays, PLAYABLE_PLAYABLE_PIDS
for ud_offset, count in list(_scan_ud_arrays(rom))[:5]:
    print(f"  UD array at 0x{(ROM_BASE + ud_offset):08X}: {count} entries")
    for i in range(min(3, count)):
        e_off = ud_offset + i * UNIT_DEF_SIZE
        chunk = rom.data[e_off:e_off+UNIT_DEF_SIZE]
        items = [f"0x{chunk[12+j]:02x}" for j in range(4)]
        print(f"    Entry {i}: pid={chunk[0]} jid={chunk[1]} items={items}")

# 8. Find chest/treasure tables by searching for the item IDs we found
# Chest item tables in FE8 usually have entries of [byte1, byte2, byte3]
# where byte3 is the item_id, or [item_id, coord1, coord2]
print("\n=== Searching for treasure/chest item tables ===")
# Look for tables that contain multiple promo items (0x62-0x6A) in a structured format
for stride in [3, 4, 5, 8, 12]:
    # Look for tables in the 0x088Bxxxx range (chapter data area)
    for start_off in range(0x8A0000, 0x8D0000, stride):
        if start_off + stride * 8 > len(rom.data):
            break
        # Read a sequence of entries at this stride
        promo_count = 0
        total_valid = 0
        positions = []
        for i in range(8):
            pos = start_off + i * stride
            if stride == 3:
                item_id = rom.data[pos + 2] if pos + 2 < len(rom.data) else 0
            elif stride == 4:
                item_id = rom.data[pos + 2] if pos + 2 < len(rom.data) else 0
            else:
                item_id = rom.data[pos] if pos < len(rom.data) else 0
            
            if 0 < item_id < 0xC0:
                total_valid += 1
                if 0x62 <= item_id <= 0x6A:
                    promo_count += 1
                positions.append((i, item_id))
        
        if promo_count >= 2 and total_valid >= 3:
            gba = ROM_BASE + start_off
            print(f"  Stride={stride} at 0x{start_off:06X} (GBA 0x{gba:08X}): {promo_count} promo items")
            for i, it in positions:
                print(f"    [{i}] item=0x{it:02X}")
            break  # Just find one for now
    else:
        continue
    break

print("\nDone!")
