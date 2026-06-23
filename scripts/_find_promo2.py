#!/usr/bin/env python3
"""Find the exact promotion table address in FE8U ROM - v2."""
import os, sys, struct
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fe8rom import ROM, ROM_BASE, JID, ITEM_TABLE_ADDR, ITEM_DATA_SIZE

rom_path = r'D:\Fire_Emblem\Custom_randomizer\Fire_Emblem_the_Sacred_Stones.GBA'
rom = ROM(rom_path)

# Let's look at the class data to find which classes have jidPromotion
# Then search for a table that maps those classes to items
print("=== Classes with jidPromotion != 0 ===")
promotable_classes = []
from fe8rom import CLASS_TABLE_ADDR, JINFO_SIZE
for jid_val in range(1, 128):
    off = (CLASS_TABLE_ADDR - ROM_BASE) + (jid_val - 1) * JINFO_SIZE
    if off + JINFO_SIZE > len(rom.data):
        break
    raw = rom.data[off:off+8]
    class_id = raw[4]
    jidPromo = raw[5]
    if jidPromo != 0 and jidPromo != class_id:  # has a real promotion
        promotable_classes.append((jid_val, jidPromo))
        # Get class name
        jid_name = "?"
        for name in dir(JID):
            if not name.startswith('_') and getattr(JID, name) == jid_val:
                jid_name = name
                break
        if jid_val <= 10:
            print(f"  JID {jid_val:3d} ({jid_name}) -> promotes to JID {jidPromo}")

print(f"  Total promotable classes: {len(promotable_classes)}")

# 2. Now look for the promotion table
# Let me search in the item table region for references to item data
# The promotion table might be in a different format

# Let me check: what addresses are loaded as LDR in the 0x0800xxxx code area
# that point to valid-looking data structures near the item table?
print("\n=== Searching for tables referenced by code ===")
# Search in the code section for pointers to data in 0x0880xxxx-0x088Cxxxx
# that look like they might be a promotion table
for code_off in range(0x000000, 0x800000, 4):
    ptr = struct.unpack_from('<I', rom.data, code_off)[0]
    if not (0x08800000 <= ptr <= 0x08900000):
        continue
    
    table_off = ptr - ROM_BASE
    if table_off + 64 > len(rom.data):
        continue
    
    # Read the potential table data
    raw_table = rom.data[table_off:table_off+64]
    
    # Check for the promotion table format in FE8U:
    # The table starts with a header or pointer count
    # Or it's a list of (item_id, class_id) pairs
    
    # Let's check: does it look like a table of pairs?
    # A pair table would have alternating bytes that look reasonable
    
    # Count how many of the first 20 even bytes are valid item IDs (0x00-0xFF, probably 0x01-0xBF)
    valid_items = 0
    total_pairs = 0
    for i in range(0, min(60, len(raw_table)-1), 2):
        it = raw_table[i]
        cl = raw_table[i+1]
        if it == 0 and cl == 0:
            break  # terminator
        total_pairs += 1
        if 0x01 <= it <= 0xBF and 0x01 <= cl <= 127:
            if it in range(0x60, 0x7B):  # in the general item range
                valid_items += 1
    
    # If this looks like a promotion table with many valid pairs
    if total_pairs >= 10 and valid_items >= 5:
        print(f"  Code at 0x{ROM_BASE+code_off:08X} -> 0x{ptr:08X}: {total_pairs} pairs, {valid_items} valid")
        for i in range(min(15, total_pairs)):
            it = rom.data[table_off + i*2]
            cl = rom.data[table_off + i*2 + 1]
            print(f"    [{i}] item=0x{it:02X} ({it}) -> class={cl}")
        break

# 3. Also try: maybe the promotion table is in the item data itself?
# Each item has a field that indicates what class(es) it promotes
# Or maybe it's stored differently

# 4. Look in the specific region after the item table
print("\n=== Checking region after item table ===")
item_table_end = (ITEM_TABLE_ADDR - ROM_BASE) + 256 * ITEM_DATA_SIZE
print(f"  Item table ends at offset 0x{item_table_end:06X} (GBA 0x{ROM_BASE+item_table_end:08X})")

# Check what's right after the item table
for delta in [0, 0x100, 0x200, 0x500, 0x800, 0x1000]:
    off = item_table_end + delta
    if off + 20 > len(rom.data):
        continue
    raw = rom.data[off:off+20]
    addr = ROM_BASE + off
    # Check for sequences of (item_id, class_id) pairs
    pairs = []
    for i in range(0, 20, 2):
        if i+1 < len(raw):
            pairs.append((raw[i], raw[i+1]))
    print(f"  +0x{delta:04X} (GBA 0x{addr:08X}): {[f'({p[0]:3d},{p[1]:3d})' for p in pairs]}")

# 5. Let me try a unique approach: search for where item ID 0x69 (Master Seal) 
# appears frequently in a pattern that looks like a mapping table
print("\n=== Looking for Master Seal (0x69) mapping patterns ===")
# Search in the expanded data section (0x08800000-0x08A00000)
for offset in range(0x800000, 0x900000, 1):
    if offset + 60 > len(rom.data):
        break
    # Count how many times 0x69 appears in a 60-byte window
    window = rom.data[offset:offset+60]
    count_69 = window.count(0x69)
    if count_69 >= 3:
        # This could be a promotion table with Master Seal entries
        # Let's check if the surrounding data looks like a table
        # Check for alternating pattern: items followed by classes
        item_counts = {}
        for i in range(0, 60, 2):
            if i+1 < 60:
                it = window[i]
                cl = window[i+1]
                if 0 < cl <= 120:  # valid class
                    item_counts[it] = item_counts.get(it, 0) + 1
        if len(item_counts) >= 3:
            addr = ROM_BASE + offset
            print(f"  Found at 0x{addr:08X}: items {sorted(item_counts.keys())}")
            for i in range(min(10, 30)):
                it = rom.data[offset + i*2]
                cl = rom.data[offset + i*2 + 1]
                print(f"    [{i}] item=0x{it:02X} class={cl}")
            # Check for 00 00 terminator within next 200 bytes
            term_pos = -1
            for search_off in range(offset, offset + 200, 2):
                if search_off + 1 < len(rom.data) and rom.data[search_off] == 0 and rom.data[search_off+1] == 0:
                    term_pos = search_off - offset
                    break
            if term_pos > 0:
                print(f"    Terminator at +{term_pos} bytes")
                total_entries = term_pos // 2
                if total_entries >= 10:
                    print(f"    TOTAL ENTRIES: {total_entries}")
                    # List ALL entries
                    classes_for_69 = []
                    for i in range(total_entries):
                        it = rom.data[offset + i*2]
                        cl = rom.data[offset + i*2 + 1]
                        if it == 0x69:
                            classes_for_69.append(cl)
                    print(f"    Master Seal (0x69) promotes classes: {sorted(set(classes_for_69))}")
                    
                    # Check if lords and monsters are included
                    lord_classes = [1, 2]  # EPHRAIM_LORD, EIRIKA_LORD
                    monster_classes = [82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101]
                    ms_classes_set = set(classes_for_69)
                    missing_lords = [c for c in lord_classes if c not in ms_classes_set]
                    missing_monsters = [c for c in monster_classes if c not in ms_classes_set]
                    if missing_lords:
                        print(f"    Missing lord classes: {missing_lords}")
                    if missing_monsters:
                        print(f"    Missing monster classes: {missing_monsters}")
                    break

print("\nDone!")
