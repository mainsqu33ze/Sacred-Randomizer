from fe8rom import ROM, ROM_BASE

rom = ROM('Fire_Emblem_the_Sacred_Stones.GBA')

# Search for Vulnerary (id=3, type=3, uses=3) throughout the ROM
# Also let's check items with known IDs at different stride sizes

# First, let's verify item 0x6C (Eirika's item in Chapter 1)
# If we can find item data, we can check its type
# Let's also verify the prologue data

# Look for the specific pattern: item id in [0,1,2,3] at intervals
for stride in [0x20, 0x24, 0x28, 0x2C, 0x30]:
    count = 0
    for off in range(0x800000, len(rom.data) - 0x200, 1):
        if rom.data[off] == 0 and rom.data[off + stride] == 1 and rom.data[off + stride*2] == 2:
            if count < 3:
                print(f"Stride=0x{stride:02X}: Found id sequence 0,1,2 at offset 0x{off:06X} (GBA 0x{ROM_BASE+off:08X})")
                for i in range(10):
                    e_off = off + i * stride
                    if e_off + 8 <= len(rom.data):
                        raw = rom.data[e_off:e_off+8]
                        print(f"  [{i}] {raw[0]:3d} {raw[1]:3d} {raw[2]:3d} {raw[3]:3d} {raw[4]:3d} {raw[5]:3d} {raw[6]:3d} {raw[7]:3d}")
            count += 1
    print(f"  Total matches: {count}")
