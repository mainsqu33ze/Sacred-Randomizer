#!/usr/bin/env python3
"""
Better analysis: read the full code flow and the data tables properly.
"""
import os, sys, struct
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fe8rom import ROM, ROM_BASE, JID

rom_path = r'D:\Fire_Emblem\Custom_randomizer\Fire_Emblem_the_Sacred_Stones.GBA'
rom = ROM(rom_path)

# 1. Read the common code area: between last stub end (0x8057EBC) and prologue (0x8057ED0)
print("=== Code between stubs and prologue ===")
common_start = 0x08057EBE
common_off = common_start - ROM_BASE
raw = rom.read(common_off, 18 + 64)  # 0x08057EBE to 0x08057ED0 is 18 bytes, read extra

print("Address       Bytes     THUMB instruction")
for i in range(0, len(raw), 2):
    addr = common_start + i
    insn = struct.unpack_from('<H', raw, i)[0]
    # Simple THUMB decode
    op = (insn >> 10) & 0x1F  # top 5 bits for many classes
    high_byte = insn >> 8
    low_byte = insn & 0xFF
    
    # Check common instruction patterns
    if (insn & 0xF800) == 0x4800:  # LDR Rd, [PC, #imm]
        rd = (insn >> 8) & 0x7
        imm = (insn & 0xFF) * 4
        target = (addr & 0xFFFFFFFC) + 4 + imm
        desc = f"LDR R{rd}, [PC, #0x{imm:02X}] ; target=0x{target:08X}"
    elif (insn & 0xF000) == 0xE000:  # B (unconditional)
        offset = insn & 0x7FF
        if offset & 0x400:  # sign extend
            offset = offset - 0x800
        target = addr + 4 + offset * 2
        desc = f"B 0x{target:08X}"
    elif (insn & 0xFF00) == 0xB500:  # PUSH {LR}
        desc = "PUSH {LR}"
    elif (insn & 0xFF00) == 0xBC00:  # POP {{reglist}}
        desc = "POP {...}"
    elif (insn & 0xFF00) == 0x4700:  # BX Rs / MOV PC, Rs
        rm = (insn >> 3) & 0xF
        if insn & 0x80:
            desc = f"BX R{rm}"
        else:
            desc = f"MOV PC, R{rm}"
    elif (insn & 0xF800) == 0x1800:  # ADDS Rd, Rn, Rm
        rd = insn & 0x7
        rn = (insn >> 3) & 0x7
        rm = (insn >> 6) & 0x7
        desc = f"ADDS R{rd}, R{rn}, R{rm}"
    elif (insn & 0xF800) == 0x6800:  # LDR Rt, [Rn, #imm]
        rt = insn & 0x7
        rn = (insn >> 3) & 0x7
        imm = (insn >> 6) & 0x1F
        desc = f"LDR R{rt}, [R{rn}, #0x{imm*4:02X}]"
    elif (insn & 0xF800) == 0x0000:  # LSLS Rd, Rm, #imm
        if (insn >> 11) == 0:
            rd = insn & 0x7
            rm = (insn >> 3) & 0x7
            imm = (insn >> 6) & 0x1F
            desc = f"LSLS R{rd}, R{rm}, #{imm}"
        else:
            desc = f"0x{insn:04X} [unknown]"
    elif (insn & 0xF800) == 0x0800:  # LSRS Rd, Rm, #imm
        rd = insn & 0x7
        rm = (insn >> 3) & 0x7
        imm = (insn >> 6) & 0x1F
        desc = f"LSRS R{rd}, R{rm}, #{imm}"
    elif (insn & 0xF800) == 0x2000:  # MOVS Rd, #imm8
        rd = (insn >> 8) & 0x7
        imm = insn & 0xFF
        desc = f"MOVS R{rd}, #0x{imm:02X}"
    elif (insn & 0xF000) == 0xD000:  # Bcond
        cond = (insn >> 8) & 0xF
        offset = insn & 0xFF
        if offset & 0x80:
            offset = offset - 0x100
        target = addr + 4 + offset * 2
        cond_names = ['EQ','NE','CS','CC','MI','PL','VS','VC','HI','LS','GE','LT','GT','LE','AL','NV']
        desc = f"B{cond_names[cond]} 0x{target:08X}"
    elif (insn & 0xFF00) == 0xDE00:  # undefined
        desc = f"0x{insn:04X} [???]"
    else:
        desc = f"0x{insn:04X} [unknown]"
    
    print(f"  0x{addr:08X}: {insn:04X}       {desc}")

# 2. Read data tables properly with their actual spacing
print("\n=== Data table structure analysis ===")
data_tables = [
    0x0880C848, 0x0880C889, 0x0880C8CA, 0x0880C90B,
    0x0880C94C, 0x0880C98D, 0x0880C9CE, 0x0880CA0F,
    0x0880CA50, 0x0880CA91, 0x0880CAD2, 0x0880CB13,
    0x0880CB54, 0x0880CB95, 0x0880CBD6, 0x0880CC17,
    0x0880CC58, 0x0880CC99, 0x0880CCDA,
]

# Check spacing
print("Table spacing:")
for i in range(1, len(data_tables)):
    delta = data_tables[i] - data_tables[i-1]
    print(f"  [{i-1}] -> [{i}]: 0x{delta:X} ({delta} bytes)")

# Print raw first 64 bytes of each table
print("\nRaw tables (first 65 bytes each):")
for idx, dt in enumerate(data_tables):
    off = dt - ROM_BASE
    raw_data = bytes(rom.data[off:off+65])
    hex_str = ' '.join(f'{b:02x}' for b in raw_data)
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in raw_data)
    print(f"\n  [{idx:2d}] 0x{dt:08X}:")
    # Print in rows of 16
    for row in range(0, 65, 16):
        chunk = raw_data[row:row+16]
        hex_row = ' '.join(f'{b:02x}' for b in chunk)
        print(f"        {hex_row}")

# 3. Decode as (class_from, class_to) 2-byte pairs (classic FE promotion table format)
# In standard FE, each entry is: class_id (unpromoted) + promoted_class_id
# 0x0000 terminates
print("\n=== Decode as (from, to) promo pairs (2 bytes each, 0x0000 = terminator) ===")
for idx, dt in enumerate(data_tables):
    off = dt - ROM_BASE
    pairs = []
    i = 0
    while i < 128:
        if off + i + 1 >= len(rom.data):
            break
        a = rom.data[off + i]
        b = rom.data[off + i + 1]
        if a == 0 and b == 0:
            break
        # Only valid JIDs (1-114)
        if a > 114 or b > 114:
            break
        pairs.append((a, b))
        i += 2
    
    # Look up names
    if pairs:
        pair_strs = []
        for a, b in pairs[:16]:
            na = [n for n in dir(JID) if getattr(JID, n) == a]
            nb = [n for n in dir(JID) if getattr(JID, n) == b]
            na = na[0] if na else f"JID_{a}"
            nb = nb[0] if nb else f"JID_{b}"
            pair_strs.append(f"{na}->{nb}")
        print(f"  [{idx:2d}] {len(pairs)} entries: {', '.join(pair_strs)}")
    else:
        print(f"  [{idx:2d}] invalid format (raw start: {' '.join(f'{b:02x}' for b in bytes(rom.data[off:off+8]))})")

# 4. Check the jump table at 0x08057EF0
print("\n=== Jump table at 0x08057EF0 (indexed by class_id) ===")
jt_off = 0x08057EF0 - ROM_BASE
for i in range(32):  # Read up to 32 entries
    ptr = rom.read_u32(jt_off + i * 4)
    if ptr >= 0x08000000 and ptr <= 0x08800000:
        print(f"  class[{i:2d}] -> handler at 0x{ptr:08X}")
    else:
        print(f"  class[{i:2d}] -> 0x{ptr:08X} (invalid)")
        if ptr == 0:
            break

# 5. Now let's check what items reference this function
# In FE8, promotion items are typically at 0x62-0x74 (19 items for 19 table entries)
print("\n=== Item -> index mapping ===")
print("Assuming 19 entries at 0x08057DD0 map to item IDs 0x62-0x74:")
for i in range(19):
    item_id = 0x62 + i
    off = (0x08809B10 - ROM_BASE) + item_id * 0x24
    raw = bytes(rom.data[off:off+0x24])
    stored_id = raw[6]
    name_id = struct.unpack_from('<H', raw, 0)[0]
    use_effect = raw[0x1E]
    wep_type = raw[7]
    print(f"  Item 0x{item_id:02X} (table idx {i:2d}): name_id={name_id}, stored={stored_id:#x}, type={wep_type}, use_effect={use_effect:#04x}")

# 6. Try to find where 0x08057DD0 is referenced in code
# Look for the pointer in code sections (0x08000000-0x08800000)
print("\n=== Searching for references to 0x08057DD0 ===")
# Search for the address as a 32-bit word in the ROM
target = struct.pack('<I', 0x08057DD0)
pos = 0
found = []
while True:
    pos = rom.data.find(target, pos)
    if pos == -1:
        break
    addr = ROM_BASE + pos
    # Check if this looks like code (in the 0x08000000-0x08800000 range)
    if addr <= 0x08800000:
        found.append(addr)
    pos += 1

print(f"Found {len(found)} reference(s):")
for addr in found:
    # Show surrounding context
    ctx_start = max(0, addr - ROM_BASE - 8)
    ctx = rom.data[ctx_start:ctx_start + 20]
    print(f"  0x{addr:08X}: {' '.join(f'{b:02x}' for b in ctx)}")

print("\nDone!")
