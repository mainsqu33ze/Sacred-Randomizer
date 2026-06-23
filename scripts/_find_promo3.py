#!/usr/bin/env python3
"""Find the exact promotion table - v3."""
import os, sys, struct
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fe8rom import ROM, ROM_BASE, JID, ITEM_TABLE_ADDR, ITEM_DATA_SIZE, CLASS_TABLE_ADDR, JINFO_SIZE

rom_path = r'D:\Fire_Emblem\Custom_randomizer\Fire_Emblem_the_Sacred_Stones.GBA'
rom = ROM(rom_path)

# Let me check multiple candidate addresses directly
candidates_to_check = [
    0x0880C2BC, 0x0880C2C0, 0x0880C280, 0x0880C200, 0x0880C300,
    0x0880C268, 0x0880C250, 0x0880C220, 0x0880C240, 0x0880C290,
    0x0880C2A0, 0x0880C2B0, 0x0880C2D0, 0x0880C2E0, 0x0880C2F0,
    0x0880C310, 0x0880C320, 0x0880C330, 0x0880C340, 0x0880C350,
    0x0880BE60, 0x0880BE80, 0x0880BEA0, 0x0880BEC0, 0x0880BEE0,
    0x0880BF00, 0x0880BF10, 0x0880BF20, 
    0x0880C100, 0x0880C110, 0x0880C120, 0x0880C130,
    0x0880C400, 0x0880C410, 0x0880C420, 0x0880C430, 0x0880C440,
]

print("=== Checking specific addresses for valid promotion table ===")
for addr in candidates_to_check:
    off = addr - ROM_BASE
    if off + 100 > len(rom.data):
        continue
    
    # Read a chunk
    raw = rom.data[off:off+100]
    
    # Count valid pairs: (item in 0x60-0x6B, class in 1-120) or (item in 0x62-0x6A, class in 1-120)
    pairs = []
    promo_pairs = []
    i = 0
    while i + 1 < 100:
        it = raw[i]
        cl = raw[i+1]
        if it == 0 and cl == 0:
            pairs.append((-1, -1))  # terminator
            break
        if cl <= 120:
            pairs.append((it, cl))
            if 0x60 <= it <= 0x6B:
                promo_pairs.append((it, cl))
        else:
            # Invalid class - this is not a promotion table
            pairs = []
            break
        i += 2
    
    if len(pairs) >= 5 and len(promo_pairs) >= 2:
        print(f"\n  0x{addr:08X}: {len(pairs)} total pairs, {len(promo_pairs)} promo pairs")
        for i, (it, cl) in enumerate(pairs[:15]):
            if it == -1:
                print(f"    [{i}] TERMINATOR (00 00)")
                break
            print(f"    [{i}] item=0x{it:02X} ({it:3d}) class={cl:3d}")

# Also check if the master seal is even referenced anywhere as a promotion mapping
# by looking for the address of the promotion table in the ROM's code section
# The game code would load a pointer to the promotion table
print("\n=== Searching for promotion table pointers in code ===")
# Known FE8U address for promotion-related code
# The table pointer is typically embedded as a literal in the code section
# Search for addresses that, when checked, contain promotion item data

# Look for a pointer that references the start of a promotion table near 0x0880xxxx
for code_off in range(0x000000, 0x800000, 4):
    ptr = struct.unpack_from('<I', rom.data, code_off)[0]
    if not (0x0880BE00 <= ptr <= 0x0880C500):  # narrow range near item tables
        continue
    table_off = ptr - ROM_BASE
    if table_off + 50 > len(rom.data):
        continue
    
    raw = rom.data[table_off:table_off+50]
    
    # Check if this looks like a table of pairs
    i = 0
    valid_entries = []
    while i + 1 < 50:
        it = raw[i]
        cl = raw[i+1]
        if it == 0 and cl == 0:
            break
        if cl > 127:
            valid_entries = []
            break
        valid_entries.append((it, cl))
        i += 2
    
    if 5 <= len(valid_entries) <= 100 and any(it in range(0x60, 0x6B) for it, cl in valid_entries):
        print(f"  Code ref at 0x{ROM_BASE+code_off:08X} -> 0x{ptr:08X}: {len(valid_entries)} entries")
        for i, (it, cl) in enumerate(valid_entries[:12]):
            print(f"    [{i}] item=0x{it:02X} class={cl}")
        # Show ALL Master Seal entries
        ms_entries = [(it, cl) for it, cl in valid_entries if it == 0x69]
        if ms_entries:
            print(f"    Master Seal entries: {[(it, cl) for it, cl in ms_entries]}")
        break

# 3. Let me check if the promotion table is stored differently
# Maybe it's a table of (item_id, num_classes, class1, class2, ...)
print("\n=== Trying variable-length format ===")
for start_off in range(0x800000, 0x8A0000, 1):
    if start_off + 30 > len(rom.data):
        break
    
    # Check for format: [item_id:1][count:1][class_ids:count*1]
    first_item = rom.data[start_off]
    first_count = rom.data[start_off + 1]
    
    if first_item not in range(0x60, 0x6B):
        continue
    if first_count < 1 or first_count > 50:
        continue
    
    # Verify the structure
    pos = start_off
    entries = []
    valid = True
    while pos + 1 < len(rom.data):
        item_id = rom.data[pos]
        count = rom.data[pos + 1]
        if item_id == 0 and count == 0:
            break
        if item_id not in range(0, 0xC0) or count > 50:
            valid = False
            break
        if pos + 2 + count > len(rom.data):
            valid = False
            break
        classes = list(rom.data[pos+2:pos+2+count])
        if any(c > 127 for c in classes):
            valid = False
            break
        entries.append((item_id, classes))
        pos += 2 + count
        if len(entries) > 50:
            break
    
    if valid and len(entries) >= 3:
        addr = ROM_BASE + start_off
        items_found = set(it for it, _ in entries)
        if 0x69 in items_found:
            print(f"\n  Variable-length table at 0x{addr:08X}: {len(entries)} entries, items={sorted(items_found)}")
            for i, (it, classes) in enumerate(entries[:10]):
                print(f"    [{i}] item=0x{it:02X}: classes={classes}")

print("\nDone!")
