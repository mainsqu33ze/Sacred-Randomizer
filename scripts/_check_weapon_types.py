from fe8rom import ROM, ROM_BASE

rom = ROM('Fire_Emblem_the_Sacred_Stones.GBA')

ITEM_TABLE_ADDR = 0x08809B10
ITEM_STRIDE = 0x24

type_names = ['Sword','Lance','Axe','Bow','Staff','Anima','Light','Dark','Ballista','Item','Dragon','Monster','Dance']

# Check specific items
for item_id in [0x03, 0x17, 0x6C, 0x10, 0x14, 0x1C, 0x28, 0x2C, 0x2D, 0x31, 0x38, 0x3C]:
    off = (ITEM_TABLE_ADDR - ROM_BASE) + item_id * ITEM_STRIDE
    if off + 0x24 > len(rom.data):
        print(f'Item 0x{item_id:02X} ({item_id:3d}): out of bounds')
        continue
    raw = rom.data[off:off+0x24]
    item_id_stored = raw[0x06]
    wep_type = raw[0x07]
    max_uses = raw[0x14]
    might = raw[0x15]
    hit = raw[0x16]
    weight = raw[0x17]
    crit = raw[0x18]
    enc_range = raw[0x19]
    min_rng = enc_range & 0xF
    max_rng = (enc_range >> 4) & 0xF
    wep_rank = raw[0x1C]
    
    type_name = type_names[wep_type] if wep_type < len(type_names) else f'Unknown({wep_type})'
    print(f'Item 0x{item_id:02X} ({item_id:3d}): type={type_name}({wep_type}) uses={max_uses} mt={might} hit={hit} crit={crit} wt={weight} rng={min_rng}-{max_rng} rank={wep_rank}')

print()

# Build weapon pools: type -> list of item IDs
weapon_pools = {t: [] for t in range(8)}
# Scan all items to classify weapons
for item_id in range(256):
    off = (ITEM_TABLE_ADDR - ROM_BASE) + item_id * ITEM_STRIDE
    if off + 0x24 > len(rom.data):
        break
    raw = rom.data[off:off+0x24]
    stored_id = raw[0x06]
    wep_type = raw[0x07]
    uses = raw[0x14]
    might = raw[0x15]
    
    # Only count weapons (type 0-7) that have positive might and uses
    if wep_type <= 7 and uses > 0 and might > 0:
        weapon_pools[wep_type].append(stored_id)

print('Weapon pools:')
for t in range(8):
    type_name = type_names[t] if t < len(type_names) else f'Type{t}'
    pool = weapon_pools[t]
    print(f'  {type_name}: {[f"0x{i:02X}" for i in pool]}')
    print(f'  ({len(pool)} items)')
