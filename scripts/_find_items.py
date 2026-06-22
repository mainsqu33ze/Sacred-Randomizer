from fe8rom import ROM, ROM_BASE
import struct

rom = ROM('Fire_Emblem_the_Sacred_Stones.GBA')

# Try to find the item table. Known offsets from EA: 0x088087A8
# Each item entry is 0x20 bytes, byte 0 = item ID, byte 1 = item type
ITEM_TABLE_CANDIDATES = [0x088087A8, 0x08808C34, 0x088089E0]

for guess in ITEM_TABLE_CANDIDATES:
    off = guess - ROM_BASE
    print(f'Trying item table at 0x{guess:08X}:')
    found = True
    for item_id in range(0x10, 0x20):
        entry_off = off + item_id * 0x20
        if entry_off + 4 > len(rom.data):
            found = False
            break
        raw = rom.data[entry_off:entry_off+4]
        stored_id = raw[0]
        item_type = raw[1]
        if stored_id != item_id:
            found = False
            break
    if found:
        print(f'  VALID - item IDs match at positions!')
        for item_id in range(0x10, min(0x50, 0x20)):
            entry_off = off + item_id * 0x20
            raw = rom.data[entry_off:entry_off+4]
            print(f'  Item 0x{item_id:02X}: type={raw[1]:3d} uses={raw[2]:3d} mt={raw[3]:3d}')
        break
    else:
        print(f'  NOT valid')

# If none found, try to find it by scanning for expected pattern
if not found:
    print("\nSearching for item table...")
    # Search for a sequence where item ID 0x10 is followed by item type byte
    for base_off in range(0x800000, 0x810000, 4):
        if base_off + 0x100 > len(rom.data):
            break
        # Check if this looks like an item table: sequential item IDs starting from 0x00 or 0x01
        match = True
        for i in range(5):
            if rom.data[base_off + i * 0x20] != i:
                match = False
                break
        if match:
            print(f'  Possible item table at ROM offset 0x{base_off:06X} (GBA 0x{ROM_BASE+base_off:08X})')
            for i in range(20):
                raw = rom.data[base_off + i * 0x20:base_off + i * 0x20 + 8]
                print(f'  [{i:3d}] id={raw[0]:3d} type={raw[1]:3d} uses={raw[2]:3d} mt={raw[3]:3d} hit={raw[4]:3d} crit={raw[5]:3d} wt={raw[6]:3d} rng={raw[7]:3d}')
            break
