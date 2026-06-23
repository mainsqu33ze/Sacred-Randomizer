#!/usr/bin/env python3
"""
Analyze CanUnitUsePromotionItem at 0x08057DD0.

Trace the 19-entry function pointer table through jump stubs to data tables,
decode each table as class-ID allow bits/bytes, and map to item IDs.
"""
import os, sys, struct
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fe8rom import ROM, ROM_BASE, JID

rom_path = r'D:\Fire_Emblem\Custom_randomizer\Fire_Emblem_the_Sacred_Stones.GBA'
rom = ROM(rom_path)

FUNC_ADDR = 0x08057DD0
FUNC_PROLOGUE = 0x08057ED0

# 1. Read the 19-entry function pointer table
print("=" * 72)
print("STEP 1: Function pointer table at 0x%08X (19 entries)" % FUNC_ADDR)
print("=" * 72)

table_off = FUNC_ADDR - ROM_BASE
stubs = []
for i in range(19):
    ptr = rom.read_u32(table_off + i * 4)
    stubs.append(ptr)
    print("  [%2d] addr 0x%08X -> stub at 0x%08X" % (i, FUNC_ADDR + i*4, ptr))

# 2. Disassemble each stub - it should be THUMB:
#    LDR R0, [PC, #0]  (0x4800)
#    B  common          (0xE000 or similar)
#    dd 0x0880xxxx      (data table address)
print("\n" + "=" * 72)
print("STEP 2: Trace each stub to data table address")
print("=" * 72)

data_tables = []
for i, stub_addr in enumerate(stubs):
    stub_off = stub_addr - ROM_BASE  # mask off thumb bit
    # Read 8 bytes: 2 bytes LDR, 2 bytes B, 4 bytes data pointer
    raw = rom.read(stub_off, 8)
    ldr_insn = struct.unpack_from('<H', raw, 0)[0]
    b_insn   = struct.unpack_from('<H', raw, 2)[0]
    data_ptr = struct.unpack_from('<I', raw, 4)[0]
    
    # LDR R0, [PC, #0] encoding: 0x4800
    # B <offset>: 0xE0xx
    ldr_ok = (ldr_insn & 0xFF00) == 0x4800
    b_ok   = (b_insn & 0xF000) == 0xE000
    
    status = "OK" if (ldr_ok and b_ok) else "UNEXPECTED"
    print("  [%2d] stub 0x%08X: LDR=0x%04X B=0x%04X data=0x%08X  [%s]" %
          (i, stub_addr, ldr_insn, b_insn, data_ptr, status))
    data_tables.append(data_ptr)

# 3. Verify the common handler at prologue
print("\n" + "=" * 72)
print("STEP 3: Function prologue at 0x%08X" % FUNC_PROLOGUE)
print("=" * 72)
prologue_off = FUNC_PROLOGUE - ROM_BASE
raw = rom.read(prologue_off, 48)
print("  Raw bytes: " + " ".join("%02x" % b for b in raw))

# Decode a few THUMB instructions
for j in range(0, 48, 2):
    insn = struct.unpack_from('<H', raw, j)[0]
    addr = FUNC_PROLOGUE + j
    print("  0x%08X: 0x%04X" % (addr, insn))

# 4. Read each data table's contents
print("\n" + "=" * 72)
print("STEP 4: Data table contents (first 20 values)")
print("=" * 72)

# Build reverse JID lookup
jid_names = {}
for name in dir(JID):
    if not name.startswith('_'):
        val = getattr(JID, name)
        if isinstance(val, JID):
            jid_names[val.value] = name

def format_table_bytes(rom, data_addr, length=20):
    """Read bytes from a data table and format them."""
    off = data_addr - ROM_BASE
    vals = list(rom.data[off:off+length])
    return vals

def decode_table_as_class_list(rom, data_addr, max_entries=64):
    """Try to interpret the table as a list of class IDs (1 byte each, 0-terminated)."""
    off = data_addr - ROM_BASE
    classes = []
    for pos in range(off, off + max_entries):
        if pos >= len(rom.data):
            break
        b = rom.data[pos]
        if b == 0:
            break
        # Allow reasonable JID range
        if b <= 114:
            classes.append(b)
        else:
            break
    return classes

def decode_table_as_bitmask(rom, data_addr, num_classes=114):
    """Try to interpret the table as a bitmask: each class gets 1 bit, 0 = allowed."""
    off = data_addr - ROM_BASE
    allowed = []
    num_bytes = (num_classes + 7) // 8
    if off + num_bytes > len(rom.data):
        return None
    for jid in range(1, num_classes + 1):
        byte_idx = (jid - 1) // 8
        bit_idx = (jid - 1) % 8
        b = rom.data[off + byte_idx]
        if not (b & (1 << bit_idx)):
            allowed.append(jid)
    # Verify: check if 0-terminated or padding follows
    return allowed, num_bytes

# First, try decoding as a simple list of JIDs (one byte each, 0-terminated)
print("  [Method A] Interpreting as list of class IDs (1 byte each, 0-terminated):")
for i, dt in enumerate(data_tables):
    classes = decode_table_as_class_list(rom, dt, 64)
    names = []
    for c in classes:
        names.append(jid_names.get(c, "JID_%d" % c))
    raw_vals = format_table_bytes(rom, dt, 20)
    print("  [%2d] 0x%08X: %d class(es): %s" % (i, dt, len(classes), names))
    print("        Raw: %s" % " ".join("%02x" % v for v in raw_vals))

# Try Method B: bitmask (if method A gives weird results)
print("\n  [Method B] Interpreting as bitmask (0=allowed):")
for i, dt in enumerate(data_tables):
    result = decode_table_as_bitmask(rom, dt, 114)
    if result is not None:
        allowed, nbytes = result
        if len(allowed) > 0 and len(allowed) < 80:
            names = []
            for c in allowed:
                names.append(jid_names.get(c, "JID_%d" % c))
            print("  [%2d] 0x%08X: %d allowed classes: %s" % (i, dt, len(allowed), names))
        else:
            raw_vals = format_table_bytes(rom, dt, 16)
            print("  [%2d] 0x%08X: %d allowed classes (probably not bitmask)" % (i, dt, len(allowed)))
            print("        Raw: %s" % " ".join("%02x" % v for v in raw_vals))

# Method C: Check if these tables look like (class_id, class_id) 2-byte pairs
print("\n  [Method C] Interpreting as (class_id, class_id) 2-byte pairs:")
for i, dt in enumerate(data_tables):
    off = dt - ROM_BASE
    pairs = []
    valid = True
    for j in range(0, 64, 2):
        if off + j + 1 >= len(rom.data):
            break
        a = rom.data[off + j]
        b = rom.data[off + j + 1]
        if a == 0 and b == 0:
            break
        if a >= 115 or b >= 115:
            valid = False
            break
        pairs.append((a, b))
    if valid and len(pairs) > 0:
        names = []
        for a, b in pairs:
            na = jid_names.get(a, "JID_%d" % a)
            nb = jid_names.get(b, "JID_%d" % b)
            names.append("%s/%s" % (na, nb))
        print("  [%2d] 0x%08X: %d pair(s): %s" % (i, dt, len(pairs), " | ".join(names)))
    else:
        raw_vals = format_table_bytes(rom, dt, 16)
        print("  [%2d] 0x%08X: invalid pairs, raw: %s" % (i, dt, " ".join("%02x" % v for v in raw_vals)))

# 5. Search for references to the function 0x08057DD0
print("\n" + "=" * 72)
print("STEP 5: Search for references to CanUnitUsePromotionItem (0x%08X)" % FUNC_ADDR)
print("=" * 72)

# Search for the address as a 32-bit literal in ROM
target_bytes = struct.pack('<I', FUNC_ADDR | 1)  # THUMB call target
pos = 0
refs = []
while True:
    pos = rom.data.find(target_bytes, pos)
    if pos == -1:
        break
    ref_addr = ROM_BASE + pos
    refs.append(ref_addr)
    pos += 1

print("  Found %d reference(s) to 0x%08X (with thumb bit):" % (len(refs), FUNC_ADDR | 1))
for r in refs:
    print("    0x%08X" % r)

# Also search without thumb bit
target_bytes2 = struct.pack('<I', FUNC_ADDR)
pos = 0
refs2 = []
while True:
    pos = rom.data.find(target_bytes2, pos)
    if pos == -1:
        break
    ref_addr = ROM_BASE + pos
    if ref_addr not in refs:
        refs2.append(ref_addr)
    pos += 1

if refs2:
    print("  Found %d additional reference(s) to 0x%08X (no thumb bit):" % (len(refs2), FUNC_ADDR))
    for r in refs2:
        print("    0x%08X" % r)

# 6. Check item data for promotion items (item IDs 0x62-0x6A are standard)
print("\n" + "=" * 72)
print("STEP 6: Promotion item IDs and their data table index")
print("=" * 72)

# The function checks item_id and uses it as an index into the table.
# Let's look at the prologue code more carefully to understand the mapping.
# Typical FE pattern: item_id -> table_index via subtract + bounds check.
# Promotion items in FE8 are typically:
#   0x62 Master Seal (or 0x62-0x6A for class-specific items)
# Let's check what items exist

print("  Checking item IDs 0x60-0x7F for promotion-related items:")
from fe8rom import ITEM_TABLE_ADDR
for item_id in range(0x60, 0x80):
    off = (ITEM_TABLE_ADDR - ROM_BASE) + item_id * 0x24
    if off + 0x24 > len(rom.data):
        break
    raw = rom.data[off:off+0x24]
    stored_id = raw[6]
    wep_type = raw[7]
    name_id = struct.unpack_from('<H', raw, 0)[0]
    uses = raw[0x14]
    if stored_id == item_id and wep_type == 9:  # item type items
        # Check if it's a promotion item by looking at use_effect_id
        use_effect = raw[0x1E]
        print("    Item 0x%02X: name_id=%d uses=%d wep_type=%d use_effect=0x%02X" %
              (item_id, name_id, uses, wep_type, use_effect))

# Check all items for use_effect_id indicating promotion
print("\n  Items with use_effect_id indicating promotion (0x09 = promote):")
for item_id in range(256):
    off = (ITEM_TABLE_ADDR - ROM_BASE) + item_id * 0x24
    if off + 0x24 > len(rom.data):
        break
    raw = rom.data[off:off+0x24]
    stored_id = raw[6]
    if stored_id != item_id:
        continue
    use_effect = raw[0x1E]
    # 0x09 = promotion item (Master Seal), 0x4D = Talisman (maybe?)
    if use_effect in (0x09, 0x4D) or (stored_id >= 0x62 and stored_id <= 0x6A):
        name_id = struct.unpack_from('<H', raw, 0)[0]
        wep_type = raw[7]
        print("    Item 0x%02X: name_id=%d type=%d use_effect=0x%02X" %
              (item_id, name_id, wep_type, use_effect))

# 7. Try to determine which data table index each item ID uses
# by reverse-engineering the function's mapping
print("\n" + "=" * 72)
print("STEP 7: Analyze function prologue to determine item_id -> index mapping")
print("=" * 72)

# Read the function starting from the prologue
raw_prologue = rom.read(prologue_off, 128)
print("  Raw bytes at 0x%08X (first 128 bytes):" % FUNC_PROLOGUE)
for j in range(0, 128, 2):
    insn = struct.unpack_from('<H', raw_prologue, j)[0]
    addr = FUNC_PROLOGUE + j
    print("    0x%08X: 0x%04X" % (addr, insn))

# 8. Also look at the 19-item table more closely - check if items 0x62..0x74 map 
# to indices 0..18
print("\n" + "=" * 72)
print("STEP 8: Attempt mapping - typical FE arrangement")
print("=" * 72)

# In FE, promotion item tables are often indexed as (item_id - base) where base = 0x62
# 19 entries would cover 0x62..0x74 (0x62 + 18 = 0x74)
print("  If mapping is (item_id - 0x62) for 19 entries:")
for idx in range(19):
    item_id = 0x62 + idx
    dt = data_tables[idx]
    print("    Index %2d: item_id=0x%02X -> data table 0x%08X" % (idx, item_id, dt))

# Let's also look at the raw bytes at those offsets and compare with known promotion data
# Check if there's a pattern: some tables might be empty (no classes can use that item)
print("\n  Checking which data tables are non-empty (simple class list decode):")
for idx, dt in enumerate(data_tables):
    classes = decode_table_as_class_list(rom, dt, 128)
    if classes:
        names = [jid_names.get(c, "JID_%d" % c) for c in classes[:10]]
        suffix = "..." if len(classes) > 10 else ""
        print("    [%2d] 0x%08X: %d classes: %s%s" % (idx, dt, len(classes), names, suffix))
    else:
        off = dt - ROM_BASE
        first_byte = rom.data[off] if off < len(rom.data) else -1
        print("    [%2d] 0x%08X: EMPTY (first_byte=0x%02X)" % (idx, dt, first_byte))

# 9. Final comprehensive decode - show full table contents
print("\n" + "=" * 72)
print("STEP 9: Full table decode (interpreted as null-terminated JID list)")
print("=" * 72)

for idx, dt in enumerate(data_tables):
    item_id = 0x62 + idx
    classes = decode_table_as_class_list(rom, dt, 256)
    names = [jid_names.get(c, "JID_%d" % c) for c in classes]
    raw_vals = format_table_bytes(rom, dt, 32)
    print("  Item 0x%02X (idx %d) @ 0x%08X:" % (item_id, idx, dt))
    print("    %d class(es): %s" % (len(classes), ", ".join(names)))
    print("    Raw: %s" % " ".join("%02x" % v for v in raw_vals))

print("\nDone!")
