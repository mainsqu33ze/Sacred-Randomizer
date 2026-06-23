#!/usr/bin/env python3
"""Find the exact promotion table address in FE8U ROM."""
import os, sys, struct
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fe8rom import ROM, ROM_BASE, ITEM_TABLE_ADDR, ITEM_DATA_SIZE

rom_path = r'D:\Fire_Emblem\Custom_randomizer\Fire_Emblem_the_Sacred_Stones.GBA'
rom = ROM(rom_path)

# First, let's check known FE8U promotion table address candidates
# These are documented in various FE8 hacking resources
candidates = [
    0x0880C2BC, 0x0880C268, 0x0880C2C0, 0x0880C200,
    0x0880C280, 0x0880C300, 0x0880BE10, 0x0880C2A0,
    0x0880BEA0, 0x0880C320,
]

print("=== Checking known candidates ===")
for addr in candidates:
    off = addr - ROM_BASE
    if off + 200 > len(rom.data):
        print(f"  0x{addr:08X}: out of bounds")
        continue
    # Read the first 40 bytes
    raw = rom.data[off:off+40]
    # Check if it looks like a promotion table
    # Look for entries where item_id in [0x62..0x6A] (promotion items)
    promo_item_ids = set(range(0x62, 0x6B))  # 0x62-0x6A
    items_seen = []
    valid = True
    for i in range(0, min(40, 200), 2):
        if i + 1 >= 40:
            break
        item_id = raw[i]
        class_id = raw[i+1]
        if item_id == 0 and class_id == 0:
            break
        if item_id == 0xFF:
            continue  # skip padding-like bytes
        if class_id > 127:
            valid = False
            break
        if item_id in promo_item_ids:
            items_seen.append((item_id, class_id))
    
    if valid and items_seen:
        print(f"  0x{addr:08X}: PROMISING - {len(items_seen)} promo items found")
        for it, cl in items_seen[:10]:
            print(f"    item=0x{it:02X} class={cl}")
        # Read more
        print(f"    First 20 bytes: {[f'0x{b:02x}' for b in rom.data[off:off+20]]}")

# 2. Search for the table by looking for the specific pattern:
# A sequence of (item_id, class_id) pairs where item_id is a promotion item (0x62-0x6A)
# and class_id is a valid JID (1-78 for playable classes, up to 114 for all)
print("\n=== Searching by promotion item pattern ===")
PROMO_ITEM_RANGE = set(range(0x62, 0x6B))  # 0x62-0x6A

# Search in the data section (after code, roughly 0x08800000-0x08A00000)
for start_off in range(0x800000, 0x880000, 2):
    if start_off + 200 > len(rom.data):
        break
    
    # Check if this starts with a promotion item entry
    first_item = rom.data[start_off]
    first_class = rom.data[start_off + 1]
    if first_item not in PROMO_ITEM_RANGE:
        continue
    if first_class > 100:
        continue
    
    # Verify the first few entries look like a promotion table
    entries = []
    valid = True
    pos = start_off
    while pos + 2 <= len(rom.data):
        it = rom.data[pos]
        cl = rom.data[pos + 1]
        if it == 0 and cl == 0:
            break
        if cl > 127:
            valid = False
            break
        entries.append((it, cl))
        pos += 2
        if len(entries) > 200:
            break
    
    if not valid or len(entries) < 3:
        continue
    
    # Check if this has Master Seal (0x69) entries for common classes
    has_master_seal = any(it == 0x69 for it, cl in entries)
    has_other_promo = any(it in PROMO_ITEM_RANGE and it != 0x69 for it, cl in entries)
    promo_item_ids_found = set(it for it, cl in entries if it in PROMO_ITEM_RANGE)
    
    if has_master_seal and has_other_promo and len(promo_item_ids_found) >= 2:
        addr = ROM_BASE + start_off
        print(f"  0x{addr:08X}: {len(entries)} entries, promo items: {sorted(promo_item_ids_found)}")
        # Show all unique class entries for Master Seal
        ms_classes = [cl for it, cl in entries if it == 0x69]
        print(f"    Master Seal promotes {len(ms_classes)} classes: {sorted(set(ms_classes))}")
        # Show the first 20 entries
        for i, (it, cl) in enumerate(entries[:20]):
            print(f"    [{i}] item=0x{it:02X} class={cl}")
        if len(entries) > 20:
            print(f"    ... and {len(entries)-20} more entries")
        # Check what comes before this table - is it referenced?
        break

# 3. Also try to find the table by looking for references in the code section
# The code loads the table address, so we can look for the pattern that references it
print("\n=== Searching for promotion table references in code ===")
# Check in the 0x08000000-0x08800000 range (game code)
for code_off in range(0x000000, 0x800000, 4):
    if code_off + 4 > len(rom.data):
        break
    ptr = struct.unpack_from('<I', rom.data, code_off)[0]
    # Check if this pointer points to a promotion table
    if 0x08800000 <= ptr <= 0x08A00000:
        # Check if the pointed-to data has promotion items
        table_off = ptr - ROM_BASE
        if table_off + 20 > len(rom.data):
            continue
        # Read some bytes and check
        raw = rom.data[table_off:table_off+20]
        promo_count = sum(1 for v in raw[0:20:2] if v in PROMO_ITEM_RANGE)
        if promo_count >= 3:
            print(f"  LDR reference at 0x{ROM_BASE+code_off:08X} -> 0x{ptr:08X} ({promo_count} promo items in first 20 bytes)")
            # Show first 10 entries
            for i in range(10):
                if table_off + i*2 + 1 < len(rom.data):
                    it = rom.data[table_off + i*2]
                    cl = rom.data[table_off + i*2 + 1]
                    print(f"    [{i}] item=0x{it:02X} class={cl}")
            break

print("\n=== Done ===")
