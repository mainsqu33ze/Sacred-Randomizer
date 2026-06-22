from fe8rom import ROM, CharacterData, PID, JID, UNIT_DEF_SIZE, ROM_BASE
import struct

rom = ROM('Fire_Emblem_the_Sacred_Stones.GBA')

# Check item bytes for known characters at known UnitDef arrays
known = [
    (0x088B3C14, 0, "Seth ch1"),
    (0x088B3C14, 1, "Eirika ch1"),
    (0x088B3F68, 0, "Seth prologue"),
    (0x088B3F68, 2, "Eirika prologue"),
]

for ptr, entry_idx, label in known:
    off = (ptr - ROM_BASE) + entry_idx * UNIT_DEF_SIZE
    chunk = rom.data[off:off+UNIT_DEF_SIZE]
    ci, cj, lp, lvl = chunk[0], chunk[1], chunk[2], chunk[3]
    items = list(chunk[12:16])
    print(f"{label:20s}: ptr=0x{ptr:08X} entry={entry_idx}")
    print(f"  charIndex={ci}, classIndex={cj}")
    print(f"  items (4 bytes): {[f'0x{x:02x}' for x in items]}")
    print(f"  items decimal: {items}")
    print()

# Also check item table ranges for weapons
WPN_NAMES = ['Sword','Lance','Axe','Bow','Staff','Anima','Light','Dark']
print("Common weapon item IDs:")
for name, start, count in [
    ("Swords", 0x10, 20),
    ("Lances", 0x14, 12),
    ("Axes", 0x1C, 12),
    ("Bows", 0x24, 8),
    ("Staves", 0x2C, 12),
    ("Anima", 0x31, 10),
    ("Light", 0x38, 8),
    ("Dark", 0x3C, 8),
]:
    items = [f"0x{i:02x}" for i in range(start, start+count)]
    print(f"  {name:8s}: {items}")
