#!/usr/bin/env python3
"""Find the promotion table by brute force search with multiple formats."""
import os, sys, struct
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fe8rom import ROM, ROM_BASE, JID, CLASS_TABLE_ADDR, JINFO_SIZE

rom_path = r'D:\Fire_Emblem\Custom_randomizer\Fire_Emblem_the_Sacred_Stones.GBA'
rom = ROM(rom_path)

# Get all classes that can promote
promotable = []
for jid_val in range(1, 128):
    off = (CLASS_TABLE_ADDR - ROM_BASE) + (jid_val - 1) * JINFO_SIZE
    if off + JINFO_SIZE > len(rom.data):
        break
    raw = rom.data[off:off+8]
    class_id = raw[4]
    jidPromo = raw[5]
    if jidPromo != 0 and jidPromo != class_id:
        promotable.append((jid_val, jidPromo))
print(f"Found {len(promotable)} promotable classes")

# Let's search for the PROMOTION TABLE using the approach:
# For each class that CAN promote, there must be an entry in the promotion table
# for Master Seal (0x69), unless Master Seal doesn't promote that class.
# In vanilla FE8, Master Seal promotes most base classes.
# Let's find the table by looking for 0x69 (Master Seal) followed by a valid class ID.

# Search with stride=2 (for u8,u8 pairs)
print("\n=== Searching for 0x69 followed by valid class IDs (stride=2) ===")
for start_off in range(0x800000, 0x900000, 2):
    if start_off + 200 > len(rom.data):
        break
    # Check if this starts with 0x69
    if rom.data[start_off] != 0x69:
        continue
    # The next byte should be a class ID
    class_id = rom.data[start_off + 1]
    if class_id > 120:
        continue
    
    # Now verify this is part of a real promotion table
    # Check 10 consecutive entries
    entries = []
    valid = True
    for i in range(200):
        pos = start_off + i * 2
        if pos + 1 >= len(rom.data):
            valid = False
            break
        it = rom.data[pos]
        cl = rom.data[pos + 1]
        if it == 0 and cl == 0:
            break  # terminator
        if cl > 120:
            valid = False
            break
        if it > 0xBF and it != 0xFF:
            # Most promotion items are in the 0x00-0xBF range
            valid = False
            break
        entries.append((it, cl))
    
    if valid and len(entries) >= 15:
        # Check that this contains MULTIPLE different promotion items
        items_set = set(it for it, cl in entries)
        promo_items = [it for it in items_set if 0x62 <= it <= 0x6A]
        if len(promo_items) >= 2 and 0x69 in promo_items:
            addr = ROM_BASE + start_off
            print(f"\n  FOUND at GBA 0x{addr:08X}: {len(entries)} entries, {len(promo_items)} promo items: {sorted(promo_items)}")
            for i, (it, cl) in enumerate(entries[:20]):
                print(f"    [{i}] item=0x{it:02X} class={cl}")
            
            # Check which classes Master Seal promotes
            ms_classes = [cl for it, cl in entries if it == 0x69]
            print(f"  Master Seal (0x69) promotes {len(ms_classes)} classes: {sorted(set(ms_classes))}")
            
            # Check missing classes
            promo_class_ids = set(ms_classes)
            missing = []
            for jid_val, _ in promotable:
                if jid_val not in promo_class_ids:
                    # Find the JID name
                    jid_name = "?"
                    for name in dir(JID):
                        if not name.startswith('_') and getattr(JID, name) == jid_val:
                            jid_name = name
                            break
                    missing.append((jid_val, jid_name))
            if missing:
                print(f"  NOT promoted by Master Seal: {missing[:20]}...")
            break

if not any(True for _ in []):
    # Also search for the table using a different method:
    # Look for clusters of bytes that look like promotion data
    print("\n=== Searching for EA-style promotion tables ===")
    # In EA, PROMOTION_TABLE is defined as:
    # {PromotionItem1, {classes...}}, {PromotionItem2, {classes...}}
    # Often stored as: [item, count, class1, class2, ...]
    # Search for Master Seal (0x69) followed by count > 5
    for start_off in range(0x800000, 0x900000, 1):
        if start_off + 50 > len(rom.data):
            break
        if rom.data[start_off] != 0x69:
            continue
        count = rom.data[start_off + 1]
        if count < 5 or count > 80:
            continue
        
        # Verify the data
        pos = start_off
        total_entries = 0
        while pos + 1 < len(rom.data):
            it = rom.data[pos]
            cnt = rom.data[pos + 1]
            if it == 0 and cnt == 0:
                break
            if cnt > 80 or pos + 2 + cnt > len(rom.data):
                break
            classes = list(rom.data[pos+2:pos+2+cnt])
            if any(c > 120 for c in classes):
                break
            total_entries += 1
            pos += 2 + cnt
            if total_entries > 5:
                break
        
        if total_entries >= 3:
            addr = ROM_BASE + start_off
            print(f"  FOUND EA-style at 0x{addr:08X}: {total_entries} entries")
            pos = start_off
            for i in range(total_entries):
                it = rom.data[pos]
                cnt = rom.data[pos + 1]
                classes = list(rom.data[pos+2:pos+2+cnt])
                print(f"    [{i}] item=0x{it:02X} count={cnt} classes={classes[:10]}{'...' if cnt>10 else ''}")
                pos += 2 + cnt
            break

# Also try searching for the 0x088ADF00 area that had promo items
print("\n=== Data at 0x088ADF00 (chapter event area) ===")
off = 0x088ADF00 - ROM_BASE
raw = rom.data[off:off+128]
for row in range(16):
    bytes_hex = ' '.join(f'{b:02x}' for b in raw[row*8:row*8+8])
    print(f"  {ROM_BASE+off+row*8:08X}: {bytes_hex}")

print("\nDone!")
