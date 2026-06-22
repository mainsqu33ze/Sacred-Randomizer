from fe8rom import ROM, ROM_BASE

rom = ROM('Fire_Emblem_the_Sacred_Stones.GBA')

# Search for all GBA addresses (0x08XXXXXX) in the code section (0x08000000-0x08800000)
# that point to regions containing potential item data
# An item table has: item ID at byte 0, item type at byte 1

# Let's first check known FE8U item definitions and look up their addresses
# In EA: 
# gItemData = 0x88087A8 or 0x8808A68

# Let's search for these patterns in the ROM
for addr_to_find in [0x088087A8, 0x08808A68, 0x08808C34, 0x08809000, 0x08808000, 0x0880B4A8]:
    pattern = bytearray()
    pattern += (addr_to_find & 0xFF).to_bytes(1, 'little')
    pattern += ((addr_to_find >> 8) & 0xFF).to_bytes(1, 'little')
    pattern += ((addr_to_find >> 16) & 0xFF).to_bytes(1, 'little')
    pattern += ((addr_to_find >> 24) & 0xFF).to_bytes(1, 'little')
    
    pos = 0
    count = 0
    while True:
        pos = rom.data.find(bytes(pattern), pos)
        if pos == -1:
            break
        count += 1
        pos += 1
        if count <= 3:
            addr = ROM_BASE + pos - 4
            print(f"0x{addr_to_find:08X} referenced at ROM offset 0x{pos-4:06X} (GBA 0x{addr:08X})")
    print(f"0x{addr_to_find:08X}: {count} references found")

print()

# Let's also search for what's at addresses 0x08808A68 and confirm items
for addr_hex in ['08808A68', '088087A8', '0880B4A8', '0880BC00', '0880B800', '0880C000']:
    addr = int(addr_hex, 16)
    off = addr - ROM_BASE
    if off + 0x200 > len(rom.data):
        print(f"0x{addr_hex}: out of bounds")
        continue
    print(f"\nData at 0x{addr_hex}:")
    vals = []
    for i in range(20):
        e_off = off + i * 0x20
        raw = rom.data[e_off:e_off+16]
        vals.append(raw[0])
        print(f"  [+0x{i*0x20:03X}] id={raw[0]:3d} type={raw[1]:3d} uses={raw[2]:3d} mt={raw[3]:3d}")
    print(f"  IDs: {vals}")
