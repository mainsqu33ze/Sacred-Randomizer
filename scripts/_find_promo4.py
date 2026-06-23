#!/usr/bin/env python3
"""Find the EXACT promotion table - dumping candidate ranges."""
import os, sys, struct
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fe8rom import ROM, ROM_BASE, JID

rom_path = r'D:\Fire_Emblem\Custom_randomizer\Fire_Emblem_the_Sacred_Stones.GBA'
rom = ROM(rom_path)

# Dump bytes around known promotion table addresses
# Common FE8U address: 0x0880C2BC
for addr in [0x0880C2BC, 0x0880C2B0, 0x0880C2A0, 0x0880C260, 0x0880C268]:
    off = addr - ROM_BASE
    if off + 64 > len(rom.data):
        continue
    raw = rom.data[off:off+64]
    print(f"\n=== Data at 0x{addr:08X} ===")
    for row in range(8):
        offset_in_row = row * 8
        bytes_hex = ' '.join(f'{b:02x}' for b in raw[offset_in_row:offset_in_row+8])
        bytes_dec = ' '.join(f'{b:3d}' for b in raw[offset_in_row:offset_in_row+8])
        print(f"  {addr+offset_in_row:08X}: {bytes_hex}  | {bytes_dec}")

# Search for the promotion table by looking for code that compares item IDs
# against known promotion item values
print("\n=== Looking for promotion item references in ROM ===")
# The FE8U ROM has an array of promotion item IDs somewhere
# Look for sequences: 0x62, 0x63, 0x64, 0x65, 0x66, 0x67, 0x68, 0x69 (the standard promotion items)
# or slight variations
promo_search_range = [0x62, 0x63, 0x64, 0x65, 0x66, 0x67, 0x68, 0x69]
# Search at 4-byte intervals (for ARM literal tables)
for stride in [1, 2, 4]:
    for start_off in range(0x800000, 0x8C0000, stride):
        if start_off + stride * 8 > len(rom.data):
            break
        # Check for sequential promo items at this stride
        found = True
        for i, expected in enumerate(promo_search_range):
            if rom.data[start_off + i * stride] != expected:
                found = False
                break
        if found:
            addr = ROM_BASE + start_off
            print(f"  Found promo item sequence at 0x{addr:08X} (stride={stride})")

# Search for any byte table that contains 0x62, 0x63, 0x64, 0x65, 0x66 in sequence
for start_off in range(0x800000, 0x8C0000, 1):
    if start_off + 5 > len(rom.data):
        break
    if (rom.data[start_off] == 0x62 and rom.data[start_off+1] == 0x63 and
        rom.data[start_off+2] == 0x64 and rom.data[start_off+3] == 0x65 and
        rom.data[start_off+4] == 0x66):
        addr = ROM_BASE + start_off
        print(f"\n  Found sequential promo items at 0x{addr:08X}:")
        raw = rom.data[start_off:start_off+32]
        for i in range(0, 32, 8):
            print(f"    {addr+start_off+i:08X}: {' '.join(f'{b:02x}' for b in raw[i:i+8])}")

# Try to find the function that handles promotion
# Search for TBB (table branch) instructions that might dispatch on promotion item type
# Or search for the literal pool containing the promotion table address

# In FE8U, the function at ~0x08057E00 is often the promotion function
# Let me check what literal pool entries exist near the promotion-checking code
# Literal pools are typically after BL instructions
# Look for 0x0880xxxx in the code section (0x08000000-0x08800000)
# that might be the promotion table
print("\n=== Searching for 0x0880xxxx addresses in code (literal pool candidates) ===")
# Check around known FE8U promotion-related code addresses
for code_area_start in range(0x057000, 0x058000, 4):
    if code_area_start + 2000 > len(rom.data):
        break
    ptr = struct.unpack_from('<I', rom.data, code_area_start)[0]
    if 0x0880C200 <= ptr <= 0x0880C400:
        # Check if the data at this address looks like a promotion table
        table_off = ptr - ROM_BASE
        raw = rom.data[table_off:table_off+200]
        pairs = []
        i = 0
        while i + 1 < 200:
            it = raw[i]
            cl = raw[i+1]
            if it == 0 and cl == 0:
                break
            if cl > 127:
                break
            pairs.append((it, cl))
            i += 2
        
        if len(pairs) >= 30:
            addr = ROM_BASE + code_area_start
            print(f"  LDR at 0x{addr:08X} -> 0x{ptr:08X}: {len(pairs)} potential entries")
            # Show all unique items
            items = set(it for it, cl in pairs)
            print(f"    Items: {sorted(items)}")
            for i, (it, cl) in enumerate(pairs[:20]):
                print(f"    [{i}] item=0x{it:02X} class={cl}")

print("\nDone!")
