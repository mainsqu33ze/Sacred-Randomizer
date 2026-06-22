from fe8rom import ROM, ROM_BASE

rom = ROM('Fire_Emblem_the_Sacred_Stones.GBA')

# Dump raw bytes of UnitDefinition entries
# Chapter 1 table
ptr = 0x088B3C14
off = ptr - ROM_BASE

# Read multiple entries
for entry_idx in range(5):
    e_off = off + entry_idx * 0x14
    raw = rom.data[e_off:e_off+0x14]
    print(f'Entry {entry_idx}:')
    print(f'  raw bytes: {[f"0x{b:02x}" for b in raw]}')
    pid = raw[0]
    jid = raw[1]
    print(f'  pid={pid}, jid={jid}')
    print(f'  bytes 2-3: {raw[2]:3d} {raw[3]:3d}')
    print(f'  bytes 4-7: {[f"0x{b:02x}" for b in raw[4:8]]}')
    print(f'  bytes 8-11: {[f"0x{b:02x}" for b in raw[8:12]]}')
    print(f'  bytes 12-15: {[f"0x{b:02x}" for b in raw[12:16]]}')
    print(f'  bytes 16-19: {[f"0x{b:02x}" for b in raw[16:20]]}')
    print()
