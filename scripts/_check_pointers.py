from fe8rom import ROM, ROM_BASE

rom = ROM('Fire_Emblem_the_Sacred_Stones.GBA')

# Check what the pointers at bytes 8-11 point to
pointers = [
    0x088B3BC4,  # Seth
    0x088B3BF4,  # Eirika
    0x088B3BFC,  # Entry 3
    0x088B3C04,  # Entry 4
]

for ptr in pointers:
    off = ptr - ROM_BASE
    print(f"Data at 0x{ptr:08X}:")
    raw = rom.data[off:off+32]
    print(f"  {[f'0x{b:02x}' for b in raw[:24]]}")
    # Maybe it's a list of item pointers?
    for i in range(0, 8, 4):
        if off + i + 4 <= len(rom.data):
            val = int.from_bytes(rom.data[off+i:off+i+4], 'little')
            print(f"  Item {i//4}: u32 = 0x{val:08X}")
    print()

# Also check what's at 0x088B3C14 (the start of the array) minus 0x14
# to see if there's a header or pointer table
print("Data at 0x088B3C00:")
ptr = 0x088B3C00
off = ptr - ROM_BASE
raw = rom.data[off:off+0x40]
for i in range(0, 0x40, 4):
    val = int.from_bytes(rom.data[off+i:off+i+4], 'little')
    print(f"  0x{ptr+i:08X}: 0x{val:08X}")
