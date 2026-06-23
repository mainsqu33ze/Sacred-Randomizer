#!/usr/bin/env python3
"""
Complete analysis: read handlers at 0x08057F44..0x08057FE4
and properly understand the data tables.
"""
import os, sys, struct
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fe8rom import ROM, ROM_BASE, JID

rom_path = r'D:\Fire_Emblem\Custom_randomizer\Fire_Emblem_the_Sacred_Stones.GBA'
rom = ROM(rom_path)

def decode_thumb(insn, addr):
    if insn == 0x0000:
        return "MOVS R0, R0"
    if (insn >> 11) == 0:
        rd = insn & 7; rm = (insn >> 3) & 7; imm = (insn >> 6) & 0x1F
        return f"LSLS R{rd}, R{rm}, #{imm}"
    if (insn >> 11) == 1:
        rd = insn & 7; rm = (insn >> 3) & 7; imm = (insn >> 6) & 0x1F
        return f"LSRS R{rd}, R{rm}, #{imm}"
    if (insn >> 11) == 2:
        rd = insn & 7; rm = (insn >> 3) & 7; imm = (insn >> 6) & 0x1F
        return f"ASRS R{rd}, R{rm}, #{imm}"
    if (insn & 0xF800) == 0x2000:
        rd = (insn >> 8) & 7; imm = insn & 0xFF
        return f"MOVS R{rd}, #0x{imm:02X}"
    if (insn & 0xF800) == 0x2800:
        rn = (insn >> 8) & 7; imm = insn & 0xFF
        return f"CMP R{rn}, #0x{imm:02X}"
    if (insn & 0xF800) == 0x4800:
        rd = (insn >> 8) & 7; imm = (insn & 0xFF) * 4
        target = (addr & 0xFFFFFFFC) + 4 + imm
        return f"LDR R{rd}, [PC, #0x{imm:02X}] ; [0x{target:08X}]"
    if (insn & 0xF800) == 0x7800:
        rt = insn & 7; rn = (insn >> 3) & 7; imm = (insn >> 6) & 0x1F
        return f"LDRB R{rt}, [R{rn}, #0x{imm:02X}]"
    if (insn & 0x6800) == 0x6800:
        rt = insn & 7; rn = (insn >> 3) & 7; imm = (insn >> 6) & 0x1F
        return f"LDR R{rt}, [R{rn}, #0x{imm*4:02X}]"
    if (insn & 0xFE00) == 0x1800:
        rd = insn & 7; rn = (insn >> 3) & 7; rm = (insn >> 6) & 7
        return f"ADDS R{rd}, R{rn}, R{rm}"
    if (insn & 0xF800) == 0x3800:
        rd = (insn >> 8) & 7; imm = insn & 0xFF
        return f"SUBS R{rd}, #0x{imm:02X}"
    if (insn & 0xF800) == 0x3000:
        rd = (insn >> 8) & 7; imm = insn & 0xFF
        return f"ADDS R{rd}, #0x{imm:02X}"
    if (insn & 0xF000) == 0xD000:
        cond = (insn >> 8) & 0xF; offset = insn & 0xFF
        if offset & 0x80: offset -= 0x100
        target = addr + 4 + offset * 2
        conds = ['EQ','NE','CS','CC','MI','PL','VS','VC','HI','LS','GE','LT','GT','LE','AL','NV']
        return f"B{conds[cond]} 0x{target:08X}"
    if (insn & 0xF800) == 0xE000:
        offset = insn & 0x7FF
        if offset & 0x400: offset -= 0x800
        target = addr + 4 + offset * 2
        return f"B 0x{target:08X}"
    if (insn & 0xFE00) == 0xB400:
        rlist = [f"R{r}" for r in range(8) if insn & (1 << r)]
        if insn & 0x100: rlist.append("LR")
        return f"PUSH {{{', '.join(rlist)}}}"
    if (insn & 0xFE00) == 0xBC00:
        rlist = [f"R{r}" for r in range(8) if insn & (1 << r)]
        if insn & 0x100: rlist.append("PC")
        return f"POP {{{', '.join(rlist)}}}"
    if (insn & 0xFF00) == 0x4700:
        rm = (insn >> 3) & 0xF
        if insn & 0x80: return f"BX R{rm}"
        else: return f"MOV PC, R{rm}"
    return f"0x{insn:04X}"

# Read the full handler area
print("=" * 72)
print("CLASS HANDLERS at 0x08057F44 - 0x08057FE4 (20 entries)")
print("=" * 72)

handler_addrs = []
for class_id in range(21):  # 0..20
    jt_off = (0x08057EF0 - ROM_BASE) + class_id * 4
    handler = rom.read_u32(jt_off)
    handler_addrs.append(handler)

for class_id in range(21):
    addr = handler_addrs[class_id]
    print(f"\n  class[{class_id:2d}] -> 0x{addr:08X}:")
    off = addr - ROM_BASE
    raw = rom.read(off, 16)
    for j in range(0, 16, 2):
        insn = struct.unpack_from('<H', raw, j)[0]
        a = addr + j
        if insn == 0x0000:
            break
        desc = decode_thumb(insn, a)
        print(f"    0x{a:08X}: 0x{insn:04X}  {desc}")

# Read the data table area more carefully
# The 19 data tables each 65 bytes, spaced by 0x41
# Let's decode them as BYTE ARRAYS indexed by CLASS_ID

print("\n" + "=" * 72)
print("DATA TABLE DECODE: byte at offset [class_id] for each item")
print("(non-zero = class can use this item, byte value = promoted class?)")
print("=" * 72)

data_tables = [
    0x0880C848, 0x0880C889, 0x0880C8CA, 0x0880C90B,
    0x0880C94C, 0x0880C98D, 0x0880C9CE, 0x0880CA0F,
    0x0880CA50, 0x0880CA91, 0x0880CAD2, 0x0880CB13,
    0x0880CB54, 0x0880CB95, 0x0880CBD6, 0x0880CC17,
    0x0880CC58, 0x0880CC99, 0x0880CCDA,
]

# For each class, show which item tables have a non-zero byte
print("Class IDs 1-20:")
header = "Class  "
for idx in range(19):
    header += f"  [{idx:2d}]"
print(header)

for class_id in range(1, 21):
    row = f"JID {class_id:2d}  "
    for idx, dt in enumerate(data_tables):
        off = dt - ROM_BASE
        val = rom.data[off + class_id] if off + class_id < len(rom.data) else 0
        row += f"  {val:02X} "
    print(row)

# Now let's try to understand by looking at which tables have
# non-zero for known class relationships
print("\n\nWith class names:")
jid_names = {v.value: k for k, v in JID.__dict__.items() if isinstance(v, JID)}

unpromoted_classes = range(1, 21)
for class_id in unpromoted_classes:
    name = jid_names.get(class_id, f"JID_{class_id}")
    row = f"{name:20s} "
    for idx, dt in enumerate(data_tables):
        off = dt - ROM_BASE
        val = rom.data[off + class_id] if off + class_id < len(rom.data) else 0
        if val:
            promoted_name = jid_names.get(val, f"JID_{val}")
            row += f" [{idx}]{promoted_name}"
    print(row)

print("\nDone!")
