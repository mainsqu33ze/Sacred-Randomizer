#!/usr/bin/env python3
import os, sys, struct
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fe8rom import ROM, ROM_BASE, ITEM_TABLE_ADDR, ITEM_DATA_SIZE
rom = ROM(r'D:\Fire_Emblem\Custom_randomizer\Fire_Emblem_the_Sacred_Stones.GBA')

for item_id in [0x62, 0x63, 0x64, 0x65, 0x66, 0x67, 0x68, 0x69, 0x6A]:
    off = (ITEM_TABLE_ADDR - ROM_BASE) + item_id * ITEM_DATA_SIZE
    if off + ITEM_DATA_SIZE > len(rom.data):
        break
    raw = rom.data[off:off+ITEM_DATA_SIZE]
    p_stat = struct.unpack_from('<I', raw, 0x0C)[0]
    p_eff = struct.unpack_from('<I', raw, 0x10)[0]
    print(f'Item 0x{item_id:02X}: p_stat=0x{p_stat:08X} p_eff=0x{p_eff:08X}')
    if p_eff != 0 and p_eff >= 0x08000000:
        poff = p_eff - ROM_BASE
        if 0 <= poff < len(rom.data):
            peek = rom.data[poff:poff+32]
            classes = []
            for b in peek:
                if b == 0 or b == 0xFF:
                    break
                if b < 128:
                    classes.append(b)
            if classes:
                print(f'  effectiveness -> class list: {classes}')
            print(f'  raw bytes: {[f"0x{b:02x}" for b in peek[:16]]}')

# Also check what the ROM code at 0x08057E58 references
ptr = struct.unpack_from('<I', rom.data, 0x08057E58 - ROM_BASE)[0]
print(f'\nCode at 0x08057E58 references 0x{ptr:08X}')
if ptr >= 0x08000000:
    poff = ptr - ROM_BASE
    raw = rom.data[poff:poff+64]
    print(f'Data at 0x{ptr:08X}:')
    for i in range(0, 64, 16):
        hexb = ' '.join(f'{b:02x}' for b in raw[i:i+16])
        decb = ' '.join(f'{b:3d}' for b in raw[i:i+16])
        print(f'  {hexb}  | {decb}')

print('\nDone!')
