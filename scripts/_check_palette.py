import sys, struct
sys.path.insert(0, '.')
from fe8rom import ROM, ROM_BASE, PALETTE_CLASS_TABLE_PTR_OFF, PALETTE_ENTRY_SIZE, CharacterData, ClassData, PID

rom = ROM('b_test_randomizer_rom.GBA')
pal_cls_gba = struct.unpack('<I', rom.data[PALETTE_CLASS_TABLE_PTR_OFF:PALETTE_CLASS_TABLE_PTR_OFF + 4])[0]
pal_cls_off = pal_cls_gba - ROM_BASE

user_pids = [0x01, 0x05, 0x07, 0x09, 0x0F, 0x1C, 0x1F, 0x20]
print('PID  Name       JID    P   Slots')
for p in user_pids:
    cd = CharacterData(rom, p)
    jid = cd.jidDefault
    jd = ClassData(rom, jid)
    off = pal_cls_off + (p - 1) * 7
    slots = list(rom.data[off:off + 7])
    name = PID(p).name if p in [v.value for v in PID] else str(p)
    h = [f'0x{s:02X}' for s in slots]
    print(f'0x{p:02X} {name:8s} JID={jid:3d} P={jd.jidPromotion:3d} {h}')

# Check what the ORIGINAL PaletteClassTable had for these classes
print()
print('Checking what backup ROM entries had for classes that now get only 1 promo:')
# Read original ROM to check for better promo data
try:
    orig_rom = ROM('..\\Fire_Emblem_the_Sacred_Stones.GBA')
    orig_pal_cls_gba = struct.unpack('<I', orig_rom.data[PALETTE_CLASS_TABLE_PTR_OFF:PALETTE_CLASS_TABLE_PTR_OFF + 4])[0]
    orig_pal_cls_off = orig_pal_cls_gba - ROM_BASE
    
    # Check what entries for JID 32, 65, 25 look like in ORIGINAL ROM
    for jid in [32, 65, 25]:
        print(f'JID {jid} (0x{jjd:02X}):')
        found = False
        for pid in range(1, 256):
            off = orig_pal_cls_off + (pid - 1) * 7
            if off + 7 > len(orig_rom.data): break
            slots = list(orig_rom.data[off:off + 7])
            if slots[0] != 0: continue  # non-trainee only
            if slots[1] == jid:
                print(f'  PID {pid:3d} slot 1: {[f"0x{s:02X}" for s in slots]}')
                found = True
            if slots[2] == jid:
                print(f'  PID {pid:3d} slot 2: {[f"0x{s:02X}" for s in slots]}')
                found = True
        if not found:
            print(f'  (no entries)')
except Exception as e:
    print(f'Error: {e}')
