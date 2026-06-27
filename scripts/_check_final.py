import sys, struct
sys.path.insert(0, '.')
from fe8rom import ROM, ROM_BASE, PALETTE_CLASS_TABLE_PTR_OFF, PALETTE_ENTRY_SIZE, CharacterData, ClassData, PID
from randomizer import _build_base_promo_lookup, TRAINEE_JIDS

rom = ROM('b_test_randomizer_rom.GBA')
pal_cls_gba = struct.unpack('<I', rom.data[PALETTE_CLASS_TABLE_PTR_OFF:PALETTE_CLASS_TABLE_PTR_OFF + 4])[0]
pal_cls_off = pal_cls_gba - ROM_BASE
base_lookup = _build_base_promo_lookup(rom)

user_pids = [0x01, 0x05, 0x06, 0x09, 0x0F, 0x1C, 0x1F, 0x20]
print('PID  Name       JID    P   Slots                    Lookup promos')
for p in user_pids:
    cd = CharacterData(rom, p)
    jid = cd.jidDefault
    jd = ClassData(rom, jid)
    off = pal_cls_off + (p - 1) * 7
    slots = list(rom.data[off:off + 7])
    name = PID(p).name if p in [v.value for v in PID] else str(p)
    h = [f'0x{s:02X}' for s in slots]
    promos = base_lookup.get(jid, [])
    pstr = [f'0x{j:02X}' for j in promos] if jid not in TRAINEE_JIDS else 'TRAINEE'
    print(f'0x{p:02X} {name:8s} JID={jid:3d} P={jd.jidPromotion:3d} {h}   {pstr}')
