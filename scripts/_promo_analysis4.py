#!/usr/bin/env python3
"""
Read the class-specific tables (indexed by item_id from 0x62).
Also read the handler for class[0] which uses a different table pointer.
"""
import os, sys, struct
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fe8rom import ROM, ROM_BASE, JID

rom_path = r'D:\Fire_Emblem\Custom_randomizer\Fire_Emblem_the_Sacred_Stones.GBA'
rom = ROM(rom_path)

jid_names = {v.value: v.name for v in JID}

# 1. Read the class-specific data tables
# class[1] uses 0x0880CD5C, class[2] = 0x0880CD9D, etc.
# Each is 0x41 = 65 bytes apart
# class[0] handler at 0x08057FE4 loads from a different address

class_tables = {}
for i in range(1, 21):
    handler_addr = 0x08057F44 + (i - 1) * 8  # 0x08057F44, 0x08057F4C, etc.
    off = handler_addr - ROM_BASE
    # The handler: LDR R0, [PC, #0] at 4-byte aligned addr
    ldr_insn = struct.unpack_from('<H', rom.data, off)[0]
    # PC = (handler_addr & ~3) + 4
    pc_base = (handler_addr & 0xFFFFFFFC) + 4
    imm = (ldr_insn & 0xFF) * 4
    table_addr = struct.unpack_from('<I', rom.data, pc_base - ROM_BASE + imm)[0]
    class_tables[i] = table_addr

print("Class-specific data tables (indexed by item_id):")
print(f"{'Class':>8} {'JID Name':20s} {'Table Addr':12s} {'Item 0x62..0x74 values':40s}")
print("-" * 80)

for class_id in range(1, 21):
    name = jid_names.get(class_id, f"JID_{class_id}")
    table_addr = class_tables[class_id]
    off = table_addr - ROM_BASE
    # Read 19 bytes (for items 0x62-0x74)
    vals = [rom.data[off + idx] for idx in range(19)]
    
    # Show which items are usable
    usable = []
    for idx, v in enumerate(vals):
        if v != 0:
            usable.append(f"0x{0x62+idx:02X}({v:02X})")
    
    val_str = ' '.join(f"{v:02X}" for v in vals)
    print(f"  class[{class_id:2d}] {name:20s} 0x{table_addr:08X} {val_str}")
    if usable:
        print(f"          Can use items: {', '.join(usable)}")

# 2. Check what class[0] handler uses
print("\nclass[0] special handler at 0x08057FE4:")
off = 0x08057FE4 - ROM_BASE
ldr_insn = struct.unpack_from('<H', rom.data, off)[0]
print(f"  LDR insn: 0x{ldr_insn:04X}")
pc_base = (0x08057FE4 & 0xFFFFFFFC) + 4
imm = (ldr_insn & 0xFF) * 4
target_addr = pc_base + imm
print(f"  PC base: 0x{pc_base:08X}, imm: 0x{imm:02X}, target: 0x{target_addr:08X}")
table_addr = struct.unpack_from('<I', rom.data, target_addr - ROM_BASE)[0]
print(f"  Table at: 0x{table_addr:08X}")
off2 = table_addr - ROM_BASE
vals = [rom.read_u8(off2 + idx) for idx in range(19)]
print(f"  Values: {' '.join(f'{v:02X}' for v in vals)}")

# 3. Now for the 19 item-specific tables at 0x0880C848 etc.
# These are indexed by class_id (1-20).
# Let's display them as: for each item, which classes it's usable by
print("\n\nItem-specific data tables (indexed by class_id):")
print("=" * 72)

item_tables = [
    0x0880C848, 0x0880C889, 0x0880C8CA, 0x0880C90B,
    0x0880C94C, 0x0880C98D, 0x0880C9CE, 0x0880CA0F,
    0x0880CA50, 0x0880CA91, 0x0880CAD2, 0x0880CB13,
    0x0880CB54, 0x0880CB95, 0x0880CBD6, 0x0880CC17,
    0x0880CC58, 0x0880CC99, 0x0880CCDA,
]

print(f"{'Item':>8} {'Idx':>4} {'Table Addr':12s} {'Val for classes 1-20':60s}")
print("-" * 90)

for idx, dt in enumerate(item_tables):
    item_id = 0x62 + idx
    off = dt - ROM_BASE
    vals = [rom.data[off + cid] for cid in range(1, 21)]
    val_str = ' '.join(f"{v:02X}" for v in vals)
    
    # Which classes can use this item (non-zero)
    usable = [cid for cid in range(1, 21) if rom.data[off + cid] != 0]
    usable_names = ', '.join(jid_names.get(c, f"JID_{c}") for c in usable)
    
    print(f"  0x{item_id:02X}  [{idx:2d}] 0x{dt:08X} {val_str}")
    if usable:
        print(f"          Usable by ({len(usable)}): {usable_names}")

# 4. Cross-reference with the item names
print("\n\nItem names from msg table:")
for item_id in range(0x62, 0x75):
    off = (0x08809B10 - ROM_BASE) + item_id * 0x24
    raw = rom.read(off, 0x24)
    stored_id = raw[6]
    name_id = struct.unpack_from('<H', raw, 0)[0]
    wep_type = raw[7]
    use_effect = raw[0x1E]
    print(f"  0x{item_id:02X}: stored=0x{stored_id:02X} name_id={name_id} type={wep_type} use_effect=0x{use_effect:02X}")

print("\nDone!")
