import random
import struct
from typing import Any, Dict, List, Set, Tuple, Optional

from .fe8rom import (
    ROM, CharacterData, ClassData, ItemData, PID, JID,
    CHARACTER_COUNT, CLASS_COUNT, UNIT_DEF_SIZE, ITEM_DATA_SIZE,
    WEAPON_TYPE_NAMES, DRAGONSTONE_ITEM_ID, VULNERARY_ITEM_ID,
    MONSTER_BLOCKED_ITEM_IDS, BALLISTA_ITEM_IDS, STORY_EXCLUSIVE_ITEM_IDS,
    PROMOTION_ITEM_IDS, MASTER_SEAL_ITEM_ID, STAFF_ITEM_IDS,
    PROMO_FUNCTION_TABLE_ADDR, PROMO_ITEM_TABLES, PROMO_CLASS_TABLE_BASE,
    PROMO_CLASS_FUNCTION_TABLE, rom_offset, ROM_BASE, ITEM_TABLE_ADDR,
    build_weapon_pools, CHARACTER_TABLE_ADDR, PINFO_SIZE,
    CHAPTER_DATA_TABLE, CHAPTER_INFO_SIZE, CHAPTER_ASSET_TABLE,
    ITEM_NAMES, PALETTE_CLASS_TABLE_PTR_OFF, PALETTE_INDEX_TABLE_PTR_OFF,
    PALETTE_ENTRY_SIZE, PALETTE_TABLE_ADDR, PALETTE_SET_SIZE,
    PALETTE_INTERLEAVE_COUNT, PALETTE_SUB_SIZE, PALETTE_COLORS,
    read_palette_set, deinterleave_palette, interleave_palettes,
    write_palette_set, lz77_compress, lz77_compressed_size,
    color_distance, pal15_to_rgb, rgb_to_pal15,
    swap_portrait_entries, _U16, _U32, _EVENT_CMDS_WITH_UD,
)

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None

_VERBOSE = False


def _vprint(*args, **kwargs):
    if _VERBOSE:
        print(*args, **kwargs)


PLAYABLE_PIDS = set(range(PID.EIRIKA, PID.TANA + 1))

PLAYABLE_PLAYABLE_PIDS = frozenset({
    PID.EIRIKA, PID.SETH, PID.GILLIAM, PID.FRANZ, PID.MOULDER,
    PID.VANESSA, PID.ROSS, PID.NEIMI, PID.COLM, PID.GARCIA,
    PID.INNES, PID.LUTE, PID.NATASHA, PID.CORMAG, PID.EPHRAIM,
    PID.FORDE, PID.KYLE, PID.AMELIA, PID.ARTUR, PID.GERIK,
    PID.TETHYS, PID.MARISA, PID.SALEH, PID.EWAN, PID.LARACHEL,
    PID.DOZLA, PID.RENNAC, PID.DUESSEL, PID.MYRRH, PID.KNOLL,
    PID.JOSHUA, PID.SYRENE, PID.TANA,
})

STANDARD_JIDS = frozenset({
    JID.EPHRAIM_LORD, JID.EIRIKA_LORD,
    JID.EPHRAIM_MASTER_LORD, JID.EIRIKA_MASTER_LORD,
    JID.CAVALIER, JID.CAVALIER_F,
    JID.PALADIN, JID.PALADIN_F,
    JID.ARMOR_KNIGHT, JID.ARMOR_KNIGHT_F,
    JID.GENERAL, JID.GENERAL_F,
    JID.THIEF,
    JID.MERCENARY, JID.MERCENARY_F,
    JID.HERO, JID.HERO_F,
    JID.MYRMIDON, JID.MYRMIDON_F,
    JID.SWORDMASTER, JID.SWORDMASTER_F,
    JID.ASSASSIN, JID.ASSASSIN_F,
    JID.ARCHER, JID.ARCHER_F,
    JID.SNIPER, JID.SNIPER_F,
    JID.RANGER, JID.RANGER_F,
    JID.WYVERN_RIDER, JID.WYVERN_RIDER_F,
    JID.WYVERN_LORD, JID.WYVERN_LORD_F,
    JID.WYVERN_KNIGHT, JID.WYVERN_KNIGHT_F,
    JID.MAGE, JID.MAGE_F,
    JID.SAGE, JID.SAGE_F,
    JID.MAGE_KNIGHT, JID.MAGE_KNIGHT_F,
    JID.BISHOP, JID.BISHOP_F,
    JID.SHAMAN, JID.SHAMAN_F,
    JID.DRUID, JID.DRUID_F,
    JID.SUMMONER, JID.SUMMONER_F,
    JID.ROGUE,
    JID.GREAT_KNIGHT, JID.GREAT_KNIGHT_F,
    JID.JOURNEYMAN, JID.PUPIL,
    JID.FIGHTER, JID.WARRIOR,
    JID.BRIGAND, JID.PIRATE,
    JID.BERSERKER,
    JID.MONK, JID.PRIEST, JID.BARD,
    JID.PEGASUS_KNIGHT, JID.FALCON_KNIGHT,
    JID.CLERIC, JID.TROUBADOUR, JID.VALKYRIE,
    JID.DANCER, JID.SOLDIER,
    JID.JOURNEYMAN_T2, JID.PUPIL_T2,
    JID.RECRUIT_T1, JID.RECRUIT_T2,
})

MONSTER_JIDS = frozenset({
    JID.REVENANT, JID.ENTOUMBED,
    JID.BONEWALKER, JID.BONEWALKER_BOW,
    JID.WIGHT, JID.WIGHT_BOW,
    JID.BAEL, JID.ELDER_BAEL,
    JID.CYCLOPS, JID.MAUTHEDOOG,
    JID.GWYLLGI, JID.TARVOS,
    JID.MAELDUIN, JID.MOGALL,
    JID.ARCH_MOGALL, JID.GORGON,
    JID.GORGONEGG, JID.GARGOYLE,
    JID.DEATHGOYLE, JID.DRACO_ZOMBIE,
    JID.MANAKETE_2,
})

EXTRA_MONSTER_JIDS = frozenset({0x7C, 0x7D})

ENEMY_EXCLUDED_JIDS = frozenset(
    {JID.MANAKETE, JID.BARD, JID.DANCER}
    | {0x50, 0x51}
    | {0x66}
    | set(range(0x67, 0x7C))
)

BOSS_PIDS = frozenset(set(range(0x40, 0x64)) | {0x28, 0x68, 0x6A, 0x6B, 0x6C, 0x6D})

FINAL_BOSS_PID = 0xBE

MONSTER_WEAPON_POOLS: Dict[int, List[int]] = {
    0x3B: [0x90],                          # MANAKETE_2
    0x52: [0x8B, 0xAD, 0xAE, 0xAF],        # REVENANT
    0x53: [0x8B, 0xAD, 0xAE, 0xAF],        # ENTOUMBED
    0x58: [0x8B, 0xAD, 0xAE, 0xAF],        # BAEL
    0x59: [0x8B, 0xAD, 0xAE, 0xAF],        # ELDER_BAEL
    0x5B: [0xB1, 0xB2],                     # MAUTHEDOOG
    0x5C: [0xB1, 0xB2],                     # GWYLLGI
    0x5F: [0xB3, 0xB4, 0xAC],              # MOGALL
    0x60: [0xB3, 0xB4, 0xAC],              # ARCH_MOGALL
    0x61: [0xAC, 0xAB, 0xB5],             # GORGON
}

CA_PROMOTED = 0x100

MALE_FEMALE_PAIRS = [
    (JID.EPHRAIM_LORD, JID.EIRIKA_LORD),
    (JID.EPHRAIM_MASTER_LORD, JID.EIRIKA_MASTER_LORD),
    (JID.CAVALIER, JID.CAVALIER_F),
    (JID.PALADIN, JID.PALADIN_F),
    (JID.ARMOR_KNIGHT, JID.ARMOR_KNIGHT_F),
    (JID.GENERAL, JID.GENERAL_F),
    (JID.MERCENARY, JID.MERCENARY_F),
    (JID.HERO, JID.HERO_F),
    (JID.MYRMIDON, JID.MYRMIDON_F),
    (JID.SWORDMASTER, JID.SWORDMASTER_F),
    (JID.ASSASSIN, JID.ASSASSIN_F),
    (JID.ARCHER, JID.ARCHER_F),
    (JID.SNIPER, JID.SNIPER_F),
    (JID.RANGER, JID.RANGER_F),
    (JID.WYVERN_RIDER, JID.WYVERN_RIDER_F),
    (JID.WYVERN_LORD, JID.WYVERN_LORD_F),
    (JID.WYVERN_KNIGHT, JID.WYVERN_KNIGHT_F),
    (JID.MAGE, JID.MAGE_F),
    (JID.SAGE, JID.SAGE_F),
    (JID.MAGE_KNIGHT, JID.MAGE_KNIGHT_F),
    (JID.BISHOP, JID.BISHOP_F),
    (JID.SHAMAN, JID.SHAMAN_F),
    (JID.DRUID, JID.DRUID_F),
    (JID.SUMMONER, JID.SUMMONER_F),
    (JID.GREAT_KNIGHT, JID.GREAT_KNIGHT_F),
]

TRAINEE_PIDS = frozenset({PID.ROSS, PID.AMELIA, PID.EWAN})
TRAINEE_JIDS = frozenset({JID.JOURNEYMAN, JID.PUPIL, JID.RECRUIT})

MANAKETE_JIDS = frozenset({JID.MANAKETE, JID.MANAKETE_2, JID.MANAKETE_MYRRH})

FEMALE_PLAYABLE_PIDS = frozenset({
    PID.EIRIKA, PID.VANESSA, PID.NEIMI, PID.LUTE, PID.NATASHA,
    PID.AMELIA, PID.TETHYS, PID.MARISA, PID.LARACHEL, PID.MYRRH,
    PID.SYRENE, PID.TANA,
})

MALE_EXCLUSIVE_JIDS = frozenset({
    JID.FIGHTER, JID.WARRIOR, JID.BERSERKER, JID.PIRATE,
    JID.MONK, JID.PRIEST, JID.THIEF, JID.JOURNEYMAN, JID.PUPIL,
})

FEMALE_EXCLUSIVE_JIDS = frozenset({
    JID.CLERIC, JID.TROUBADOUR, JID.VALKYRIE, JID.DANCER,
    JID.RECRUIT, JID.PEGASUS_KNIGHT, JID.FALCON_KNIGHT,
    JID.MANAKETE_MYRRH,
})

TRAINEE_PROMO_TABLE_ADDR = 0x08207044
TRAINEE_PROMO_ENTRY_SIZE = 4
TRAINEE_PROMO_COUNT = 3

# Attribute bit masks from lord classes
CHAR_LOCK_ATTRS = {
    PID.EIRIKA: (0x0A, 0x10020000, [0x09, 0x85]),
    PID.EPHRAIM: (0x14, 0x20000000, [0x78, 0x92]),
}

SPELL_ASSOC_ADDR = 0x088AFBD8
SPELL_ASSOC_ENTRY_SIZE = 16

WTYPE_EFX_MAP = {
    3: 2,    # bow
    4: 38,   # staff
    5: 22,   # anima
    6: 31,   # light
    7: 29,   # dark
}

WTYPE_FLAG_MAP = {
    3: 0,    # bow
    4: 0,    # staff
    5: 2,    # anima
    6: 5,    # light
    7: 1,    # dark
}

CHAPTER_NAMES = {
    0: 'Prologue', 1: 'Ch1: Escape!', 2: 'Ch2: The Protected',
    3: 'Ch3: Bandits of Borgo', 4: 'Ch4: Ancient Horrors',
    5: "Ch5: Empire's Reach", 6: 'Ch5x: Unbroken Heart',
    7: 'Ch6: Victims of War', 8: 'Ch7: Waterside Renvall',
    9: "Ch8: It's a Trap!", 10: 'Ch9: Distant Blade',
    11: 'Ch10: Revolt at Carcino', 12: 'Ch11: Creeping Darkness',
    13: 'Ch12: Village of Silence', 14: 'Ch13: Hamill Canyon',
    15: 'Ch14: Queen of White Dunes', 16: 'Ch15: Scorched Sand',
    17: 'Ch16: Ruled by Madness', 18: 'Ch17: River of Regrets (Eri)',
    19: 'Ch18: Two Faces of Evil (Eri)', 20: 'Ch19: Last Hope (Eri)',
    21: 'Ch20: Darkling Woods (Eri)', 22: 'Ch20: Darkling Woods (Eri)',
    23: 'Ch9: Fort Rigwald', 24: 'Ch10: Turning Traitor',
    25: 'Ch11: Phantom Ship', 26: 'Ch12: Landing at Taizel',
    27: "Ch13: Fluorspar's Oath", 28: 'Ch14: Father and Son',
    29: 'Ch15: Scorched Sand (Eph)', 30: 'Ch16: Ruled by Maddness (Eph)',
    31: 'Ch17: River of Regrets (Eph)', 32: 'Ch18: Two Faces of Evil (Eph)',
    33: 'Ch19: Last Hope (Eph)', 34: 'Ch20: Darkling Woods (Eph)',
}

EFFECT_NAMES = {0: '(none)', 1: 'Poison', 2: 'Nosferatu', 3: 'Eclipse', 4: 'Devil', 5: 'Stone'}

S_RANK_WEXP = 251

# Items with class lock (bit 12 in attributes) mapped to their allowed class JIDs.
# Shamshir (0x0C) is the only vanilla item with this flag — restricted to Myrmidon/Swordmaster.
CLASS_LOCKED_ITEM_RESTRICTIONS = {
    0x0C: frozenset({JID.MYRMIDON, JID.MYRMIDON_F, JID.SWORDMASTER, JID.SWORDMASTER_F}),
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_tier(rom: ROM, pid: int) -> int:
    cd = CharacterData(rom, pid)
    if cd.jidDefault in TRAINEE_JIDS:
        return 0
    try:
        jd = ClassData(rom, cd.jidDefault)
        if jd.attributes & CA_PROMOTED:
            return 2
    except Exception:
        pass
    return 1


def _scale_stat(val: int, factor: float, min_val: int, max_val: int) -> int:
    return max(min_val, min(max_val, int(round(val * factor))))


def _randomize_stat(orig: int, mean: Optional[float], stddev: float, lo: int, hi: int) -> int:
    if mean is None:
        center = orig
    else:
        center = mean
    return max(lo, min(hi, int(round(random.gauss(center, stddev)))))


def _distribute_growth_pool(pool_total: int, min_g: int, max_g: int) -> List[int]:
    weights = [random.random() for _ in range(7)]
    total_w = sum(weights)
    vals = [int(round(w * pool_total / total_w)) for w in weights]
    return [max(min_g, min(max_g, v)) for v in vals]


def _adjust_weapon_ranks(cd: CharacterData, new_jid: int, rom: ROM) -> None:
    jd = ClassData(rom, new_jid)
    supported = [i for i in range(8) if jd.baseWexp[i] > 0]
    max_rank = max(cd.baseWexp)
    highest_lost = max(
        (cd.baseWexp[i] for i in range(8)
         if cd.baseWexp[i] == max_rank and jd.baseWexp[i] == 0 and max_rank > 0),
        default=0
    )
    for i in range(8):
        if jd.baseWexp[i] > 0:
            cd.baseWexp[i] = max(cd.baseWexp[i], jd.baseWexp[i])
        else:
            cd.baseWexp[i] = 0
    if highest_lost > 0 and supported:
        target = min(supported, key=lambda i: cd.baseWexp[i])
        if cd.baseWexp[target] < highest_lost:
            cd.baseWexp[target] = highest_lost


def _parse_omit_classes(config: dict, key: str = 'class_randomization') -> Set[int]:
    omit = set()
    for name in config.get(key, {}).get('omit_classes', []):
        name = name.upper().strip()
        if hasattr(JID, name):
            omit.add(getattr(JID, name))
    return omit


def _is_character_female(rom: ROM, pid: int) -> bool:
    cd = CharacterData(rom, pid)
    jid = cd.jidDefault
    if jid in FEMALE_EXCLUSIVE_JIDS:
        return True
    if jid in MALE_EXCLUSIVE_JIDS:
        return False
    for male_jid, female_jid in MALE_FEMALE_PAIRS:
        if jid == female_jid:
            return True
        if jid == male_jid:
            return False
    if pid not in PLAYABLE_PLAYABLE_PIDS:
        return pid in FEMALE_PLAYABLE_PIDS
    return False


def _swap_gendered_class(jid: int, is_female: bool) -> int:
    for male_jid, female_jid in MALE_FEMALE_PAIRS:
        if is_female and jid == male_jid:
            return female_jid
        if not is_female and jid == female_jid:
            return male_jid
    return jid


def _split_class_pool(rom: ROM) -> Tuple[Set[int], Set[int]]:
    promoted = set()
    unpromoted = set()
    for jid in STANDARD_JIDS:
        jd = ClassData(rom, jid)
        if jd.attributes & CA_PROMOTED:
            promoted.add(jid)
        elif jid not in TRAINEE_JIDS:
            unpromoted.add(jid)
    return promoted, unpromoted


def _split_characters_by_tier(rom: ROM) -> Tuple[List[int], List[int]]:
    promoted_chars = []
    unpromoted_chars = []
    for pid in sorted(PLAYABLE_PLAYABLE_PIDS):
        cd = CharacterData(rom, pid)
        if ClassData(rom, cd.jidDefault).attributes & CA_PROMOTED:
            promoted_chars.append(pid)
        else:
            unpromoted_chars.append(pid)
    return promoted_chars, unpromoted_chars


def _get_con_rules(rules: dict, class_enabled) -> Tuple[bool, int, int, int]:
    if 'con' in rules:
        c = rules['con']
        return (c.get('enabled', True),
                c.get('min', 1),
                c.get('player_min', 1),
                c.get('stddev', rules.get('stddev', 3)))
    is_class_random = isinstance(class_enabled, str) and class_enabled == 'random'
    return (is_class_random, 1, 1, rules.get('stddev', 3))


def _is_class_locked_item(rom: ROM, item_id: int) -> bool:
    off = rom_offset(ITEM_TABLE_ADDR) + item_id * ITEM_DATA_SIZE
    if off + 12 > len(rom.data):
        return False
    attrs = _U32.unpack_from(rom.data, off + 0x08)[0]
    return bool(attrs & 0x1000)

def _filter_class_locked(rom: ROM, item_ids: List[int], class_jid: int) -> List[int]:
    allowed_jids = CLASS_LOCKED_ITEM_RESTRICTIONS
    return [
        iid for iid in item_ids
        if not _is_class_locked_item(rom, iid) or (iid in allowed_jids and class_jid in allowed_jids[iid])
    ]

def _pick_weapon_for_type(rom: ROM, weapon_pools: dict, char_ranks: List[int],
                          class_jid: int = None) -> Optional[int]:
    candidates = []
    for t in range(8):
        if char_ranks[t] == 0 or not weapon_pools[t]:
            continue
        max_rank = char_ranks[t]
        for item_id, rank in weapon_pools[t]:
            if rank <= max_rank:
                candidates.append(item_id)
    if class_jid is not None:
        filtered = _filter_class_locked(rom, candidates, class_jid)
        if filtered:
            return random.choice(filtered)
    return random.choice(candidates) if candidates else None


# ---------------------------------------------------------------------------
# UD array scanning (cached results)
# ---------------------------------------------------------------------------

def _ud_array_at_lenient(data: bytearray, offset: int, rom_size: int) -> int:
    if offset + ROM_BASE >= 0x088D0000:
        return 0
    pos = offset
    entries = 0
    while pos + UNIT_DEF_SIZE <= rom_size:
        chunk = data[pos:pos + UNIT_DEF_SIZE]
        if all(b == 0 for b in chunk):
            return entries
        pid = chunk[0]
        jid = chunk[1]
        if pid == 0 or jid > 127:
            return 0
        pos += UNIT_DEF_SIZE
        entries += 1
        if entries > 100:
            return 0
    return 0


def _scan_ud_arrays(data: bytearray, rom_size: int) -> List[Tuple[int, int]]:
    results = []
    for cmd_lo in _EVENT_CMDS_WITH_UD:
        pattern = bytes([cmd_lo, 0x2C])
        pos = 0
        while True:
            pos = data.find(pattern, pos)
            if pos == -1 or pos + 8 > rom_size:
                break
            ptr = _U32.unpack_from(data, pos + 4)[0]
            if not (0x08000000 <= ptr < ROM_BASE + rom_size and ptr % 4 == 0 and ptr >= 0x08800000):
                pos += 1
                continue
            ud_offset = ptr - ROM_BASE
            count = _ud_array_at_lenient(data, ud_offset, rom_size)
            if count > 0:
                results.append((ud_offset, count))
            pos += 1
    return results


def _scan_chapter_ud_arrays(data: bytearray, rom_size: int) -> List[Tuple[int, int]]:
    asset_off = CHAPTER_ASSET_TABLE - ROM_BASE
    seen = set()
    results = []

    for ch in range(35):
        ch_off = (CHAPTER_DATA_TABLE - ROM_BASE) + ch * CHAPTER_INFO_SIZE
        map_event_data_id = data[ch_off + 0x74]
        event_data_ptr = _U32.unpack_from(data, asset_off + map_event_data_id * 4)[0]
        event_data_off = event_data_ptr - ROM_BASE

        gmap_event_id = data[ch_off + 0x75]
        gmap_ptr = _U32.unpack_from(data, asset_off + gmap_event_id * 4)[0]
        gmap_off = gmap_ptr - ROM_BASE

        for off in range(0, 0x400, 4):
            val = _U32.unpack_from(data, event_data_off + off)[0]
            if val not in seen:
                ud_offset = val - ROM_BASE
                count = _ud_array_at_lenient(data, ud_offset, rom_size)
                if count > 0:
                    seen.add(val)
                    results.append((ud_offset, count))

        for off in range(0, 0x200, 4):
            val = _U32.unpack_from(data, gmap_off + off)[0]
            if val not in seen:
                ud_offset = val - ROM_BASE
                count = _ud_array_at_lenient(data, ud_offset, rom_size)
                if count > 0:
                    seen.add(val)
                    results.append((ud_offset, count))

    return results


def _scan_giveitem_events(data: bytearray, rom_size: int) -> List[Tuple[int, int, str]]:
    lo = rom_offset(0x08800000)
    hi = min(rom_offset(0x08A00000), rom_size)
    hdr = b'\x40\x0A\x00\x00'
    pos = lo
    results = []
    while True:
        pos = data.find(hdr, pos, hi)
        if pos == -1 or pos + 20 > rom_size:
            break
        if pos >= 8 and data[pos-8:pos-6] == b'\x40\x05':
            pos += 1
            continue
        ptr = _U32.unpack_from(data, pos + 4)[0]
        at_8, at_9, at_11 = data[pos + 8], data[pos + 9], data[pos + 11]
        item_id = _U32.unpack_from(data, pos + 12)[0]
        if (0x08000000 <= ptr <= 0x08FFFFFF and
            at_8 == 0x40 and at_9 == 0x05 and at_11 == 0x00 and
            0 < item_id < 0xC0):
            results.append((pos + 12, item_id, '<I'))
        pos += 1
    return results


def _scan_chest_items(rom: ROM) -> List[Tuple[int, int, str]]:
    """Scan section[2] (locationBasedEvents) of each chapter for type-0x07
    CHES entries with cmdId=0x14 (TILE_COMMAND_CHEST). Returns
    (write_offset, item_id, '<H') for each non-gold chest item."""
    data = rom.data
    seen = set()
    results = []

    for ch in range(35):
        ch_off = (CHAPTER_DATA_TABLE - ROM_BASE) + ch * CHAPTER_INFO_SIZE
        map_event_data_id = data[ch_off + 0x74]
        if map_event_data_id == 0:
            continue
        event_data_ptr = _U32.unpack_from(data, (CHAPTER_ASSET_TABLE - ROM_BASE) + map_event_data_id * 4)[0]
        if event_data_ptr == 0:
            continue
        event_data_off = event_data_ptr - ROM_BASE

        # Read section[2] = locationBasedEvents
        sec_ptr = _U32.unpack_from(data, event_data_off + 8)[0]
        if sec_ptr == 0:
            continue
        off = sec_ptr - ROM_BASE
        if off < 0 or off + 12 > len(data):
            continue

        entry_idx = 0
        while off + (entry_idx + 1) * 12 <= len(data):
            entry_off = off + entry_idx * 12
            raw = data[entry_off : entry_off + 12]
            if all(b == 0 for b in raw):
                break
            # type-0x07 = EvCheck07_CHES
            if raw[0] == 0x07:
                given_item = _U16.unpack_from(raw, 4)[0]
                x = raw[8]
                y = raw[9]
                cmd_id = _U16.unpack_from(raw, 10)[0]
                # cmdId 0x14 = TILE_COMMAND_CHEST, skip gold (0x77)
                if cmd_id == 0x14 and 0 < given_item < 0xC0 and given_item != 0x77:
                    write_off = entry_off + 4  # givenItem field
                    if write_off not in seen:
                        seen.add(write_off)
                        results.append((write_off, given_item, '<H'))
            entry_idx += 1
    return results


def _scan_loot_events(rom: ROM, giveitem_events: List[Tuple[int, int, str]],
                      include_ballista: bool = False) -> List[Tuple[int, int, str]]:
    loot_excluded = set(MONSTER_BLOCKED_ITEM_IDS) | set(STORY_EXCLUSIVE_ITEM_IDS)
    loot_excluded.update(PROMOTION_ITEM_IDS)
    loot_excluded.update({0x3D, 0x44, 0x8A})
    loot_excluded.update({0x7D, 0x7E, 0x7F, 0x80, 0xA2, 0xA3, 0xA4, 0xA5, 0xA7, 0x8A, 0x77})
    if not include_ballista:
        loot_excluded.update(BALLISTA_ITEM_IDS)
    seen = set()
    results = []
    for write_offset, item_id, pack_fmt in giveitem_events:
        if item_id not in loot_excluded and write_offset not in seen:
            seen.add(write_offset)
            results.append((write_offset, item_id, pack_fmt))
    return results


def _build_loot_pool(include_ballista: bool = False) -> List[int]:
    excluded = set(MONSTER_BLOCKED_ITEM_IDS) | set(STORY_EXCLUSIVE_ITEM_IDS)
    excluded.update({0x3D, 0x44, 0x8A})
    excluded.update(PROMOTION_ITEM_IDS)
    excluded.update({0x7D, 0x7E, 0x7F, 0x80, 0xA2, 0xA3, 0xA4, 0xA5, 0xA7, 0xBA, 0x77})
    if not include_ballista:
        excluded.update(BALLISTA_ITEM_IDS)
    return [item_id for item_id in range(1, 0xC0) if item_id not in excluded]


# ---------------------------------------------------------------------------
# Trainee promotion table
# ---------------------------------------------------------------------------

def _update_trainee_promotion_table(rom: ROM, modified_pids: Set[int]) -> int:
    off = rom_offset(TRAINEE_PROMO_TABLE_ADDR)
    patched = 0
    for i in range(TRAINEE_PROMO_COUNT):
        entry_off = off + i * TRAINEE_PROMO_ENTRY_SIZE
        pid = rom.data[entry_off]
        if pid not in modified_pids:
            continue
        cd = CharacterData(rom, pid)
        new_class = cd.jidDefault
        if new_class in MANAKETE_JIDS or new_class not in TRAINEE_JIDS:
            if not all(rom.data[entry_off + j] == 0 for j in range(4)):
                for j in range(4):
                    rom.data[entry_off + j] = 0
                patched += 1
        elif rom.data[entry_off + 2] != new_class:
            rom.data[entry_off + 2] = new_class
            patched += 1
    return patched


def _remap_trainee_table(rom: ROM) -> int:
    off = rom_offset(TRAINEE_PROMO_TABLE_ADDR)
    trainee_pids = []
    for pid in PLAYABLE_PLAYABLE_PIDS:
        cd = CharacterData(rom, pid)
        if cd.jidDefault in TRAINEE_JIDS:
            trainee_pids.append(pid)
    patched = 0
    for i in range(TRAINEE_PROMO_COUNT):
        entry_off = off + i * TRAINEE_PROMO_ENTRY_SIZE
        if i < len(trainee_pids):
            pid = trainee_pids[i]
            cd = CharacterData(rom, pid)
            if rom.data[entry_off] != pid or rom.data[entry_off + 2] != cd.jidDefault:
                rom.data[entry_off] = pid
                rom.data[entry_off + 1] = 10
                rom.data[entry_off + 2] = cd.jidDefault
                rom.data[entry_off + 3] = 0
                patched += 1
        else:
            if not all(rom.data[entry_off + j] == 0 for j in range(4)):
                for j in range(4):
                    rom.data[entry_off + j] = 0
                patched += 1
    return patched


# ---------------------------------------------------------------------------
# Recruitment order
# ---------------------------------------------------------------------------

def randomize_recruitment_order(rom: ROM, config: dict, preserve_tier: bool = True) -> Set[int]:
    rules = config.get('recruitment_randomization', {})
    if not rules.get('enabled', False):
        return set()

    pids = sorted(PLAYABLE_PLAYABLE_PIDS)
    n = len(pids)

    if preserve_tier:
        _tier_map = {pid: _get_tier(rom, pid) for pid in pids}
        tier_groups = {0: [], 1: [], 2: []}
        for pid in pids:
            tier_groups[_tier_map[pid]].append(pid)
        shuffled = list(pids)
        for t in sorted(tier_groups):
            group = tier_groups[t]
            positions = [i for i, pid in enumerate(shuffled) if _tier_map[pid] == t]
            shuffled_group = list(group)
            random.shuffle(shuffled_group)
            for pos, new_pid in zip(positions, shuffled_group):
                shuffled[pos] = new_pid
    else:
        shuffled = list(pids)
        random.shuffle(shuffled)

    char_table_off = rom_offset(CHARACTER_TABLE_ADDR)
    char_data = {}
    for pid in pids:
        off = char_table_off + (pid - 1) * PINFO_SIZE
        char_data[pid] = bytearray(rom.data[off:off + PINFO_SIZE])

    for src_pid, dst_pid in zip(pids, shuffled):
        dst_off = char_table_off + (dst_pid - 1) * PINFO_SIZE
        for j in range(PINFO_SIZE):
            if j == 4:
                continue
            rom.data[dst_off + j] = char_data[src_pid][j]
        rom.data[dst_off + 4] = dst_pid

    # Swap PaletteClassTable (7 bytes per PID)
    pal_cls_gba = _U32.unpack_from(rom.data, PALETTE_CLASS_TABLE_PTR_OFF)[0]
    pal_cls_off = pal_cls_gba - ROM_BASE
    pal_cls_data = {}
    for pid in pids:
        off = pal_cls_off + (pid - 1) * PALETTE_ENTRY_SIZE
        pal_cls_data[pid] = bytearray(rom.data[off:off + PALETTE_ENTRY_SIZE])
    for src_pid, dst_pid in zip(pids, shuffled):
        dst_off = pal_cls_off + (dst_pid - 1) * PALETTE_ENTRY_SIZE
        rom.data[dst_off:dst_off + PALETTE_ENTRY_SIZE] = pal_cls_data[src_pid]

    # Swap PaletteIndexTable (7 bytes per PID)
    pal_idx_gba = _U32.unpack_from(rom.data, PALETTE_INDEX_TABLE_PTR_OFF)[0]
    pal_idx_off = pal_idx_gba - ROM_BASE
    pal_idx_data = {}
    for pid in pids:
        off = pal_idx_off + (pid - 1) * PALETTE_ENTRY_SIZE
        pal_idx_data[pid] = bytearray(rom.data[off:off + PALETTE_ENTRY_SIZE])
    for src_pid, dst_pid in zip(pids, shuffled):
        dst_off = pal_idx_off + (dst_pid - 1) * PALETTE_ENTRY_SIZE
        rom.data[dst_off:dst_off + PALETTE_ENTRY_SIZE] = pal_idx_data[src_pid]

    # Remap portrait table entries: dst_pid's portrait slot gets src_pid's
    # original data, so the face shown matches the character who now occupies
    # that PID slot.  Copy from saved originals instead of sequential swaps
    # to avoid corrupting the permutation mapping.
    from .fe8rom import PID_TO_PORTRAIT_SLOT, PORTRAIT_TABLE_ADDR, PORTRAIT_ENTRY_SIZE
    portrait_snap = {}
    for pid in pids:
        slot = PID_TO_PORTRAIT_SLOT.get(pid)
        if slot is not None:
            off = rom_offset(PORTRAIT_TABLE_ADDR) + slot * PORTRAIT_ENTRY_SIZE
            portrait_snap[pid] = bytearray(rom.data[off:off + PORTRAIT_ENTRY_SIZE])
    remapped = 0
    for src_pid, dst_pid in zip(pids, shuffled):
        if src_pid != dst_pid and src_pid in portrait_snap and dst_pid in portrait_snap:
            dst_slot = PID_TO_PORTRAIT_SLOT[dst_pid]
            dst_off = rom_offset(PORTRAIT_TABLE_ADDR) + dst_slot * PORTRAIT_ENTRY_SIZE
            rom.data[dst_off:dst_off + PORTRAIT_ENTRY_SIZE] = portrait_snap[src_pid]
            remapped += 1
    if remapped:
        _vprint(f"Remapped {remapped} portrait table entr(y/ies) for recruitment shuffle")

    # Restore each PID's face ID (fid at offset 6, u16) to the original PID's
    # portrait slot index.  After the portrait remap, dst_pid's slot now holds
    # src_pid's portrait data, so dst_pid's fid must point to dst_pid's own
    # slot (its original value) for the UI portrait lookup to land correctly.
    for pid in pids:
        off = char_table_off + (pid - 1) * PINFO_SIZE
        orig_fid = struct.unpack_from('<H', char_data[pid], 6)[0]
        struct.pack_into('<H', rom.data, off + 6, orig_fid)

    remapped = _remap_trainee_table(rom)
    if remapped:
        _vprint(f"Remapped {remapped} trainee promotion table entr(y/ies) after recruitment shuffle")

    label = " (tier-preserving)" if preserve_tier else ""
    _vprint(f"Randomized recruitment order for {n} units{label}")
    return set(pids)


def _sync_shared_pid_classes(rom: ROM) -> None:
    sync_groups = [(42, 0x6D)]
    for src_pid, dst_pid in sync_groups:
        try:
            cd_src = CharacterData(rom, src_pid)
            cd_dst = CharacterData(rom, dst_pid)
            if cd_src.jidDefault == 0 or cd_dst.jidDefault == 0:
                continue
            if cd_src.jidDefault != cd_dst.jidDefault:
                cd_dst.jidDefault = cd_src.jidDefault
                jd = ClassData(rom, cd_src.jidDefault)
                new_ranks = list(cd_dst.baseWexp)
                for i in range(8):
                    new_ranks[i] = S_RANK_WEXP if jd.baseWexp[i] > 0 else 0
                cd_dst.baseWexp = new_ranks
                cd_dst.write(rom)
                _vprint(f"Synced PID 0x{dst_pid:02X} class to PID {src_pid} (0x{cd_src.jidDefault:02X})")
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Class randomization
# ---------------------------------------------------------------------------

def randomize_class(rom: ROM, config: dict) -> Set[int]:
    rules = config.get('class_randomization', {})
    mode = rules.get('mode', 'shuffle')
    manakete_count = rules.get('manakete_count', 1)
    gender_lock = rules.get('gender_lock', False)
    if 'shuffle' in rules and not rules.get('shuffle', True):
        mode = 'none'
        manakete_count = 0
    omit_jids = _parse_omit_classes(config)
    include_soldier = rules.get('include_soldier', False)

    modified_pids = set()

    def _assign(pid: int, new_jid: int) -> None:
        cd = CharacterData(rom, pid)
        cd.jidDefault = new_jid
        _adjust_weapon_ranks(cd, new_jid, rom)
        cd.write(rom)
        modified_pids.add(pid)

    promoted_jids, unpromoted_jids = _split_class_pool(rom)
    promoted_chars, unpromoted_chars = _split_characters_by_tier(rom)

    available_trainee = sorted(TRAINEE_JIDS - omit_jids)
    trainee_chars = sorted([p for p in unpromoted_chars if p in TRAINEE_PIDS])
    non_trainee_unpromoted = sorted([p for p in unpromoted_chars if p not in TRAINEE_PIDS])

    promoted_jids -= omit_jids
    unpromoted_jids -= omit_jids
    if not include_soldier:
        unpromoted_jids.discard(JID.SOLDIER)
    promoted_jids.discard(JID.SOLDIER)

    if gender_lock:
        def _gender_pool(jids, is_female):
            pool = set()
            for j in jids:
                sj = _swap_gendered_class(j, is_female)
                if is_female and sj in MALE_EXCLUSIVE_JIDS:
                    continue
                if not is_female and sj in FEMALE_EXCLUSIVE_JIDS:
                    continue
                pool.add(sj)
            return sorted(pool)

        def _split_by_gender(pids):
            male = [p for p in pids if not _is_character_female(rom, p)]
            female = [p for p in pids if _is_character_female(rom, p)]
            return male, female

        trainee_m, trainee_f = _split_by_gender(trainee_chars)
        promoted_m, promoted_f = _split_by_gender(promoted_chars)
        unpromoted_m, unpromoted_f = _split_by_gender(non_trainee_unpromoted)

        trainee_pool_m = _gender_pool(available_trainee, False)
        trainee_pool_f = _gender_pool(available_trainee, True)
        promoted_pool_m = _gender_pool(promoted_jids, False)
        promoted_pool_f = _gender_pool(promoted_jids, True)
        unpromoted_pool_m = _gender_pool(unpromoted_jids, False)
        unpromoted_pool_f = _gender_pool(unpromoted_jids, True)

        if mode == 'shuffle':
            if trainee_m and trainee_pool_m:
                pool = list(trainee_pool_m)
                random.shuffle(pool)
                for pid, new_jid in zip(trainee_m, pool):
                    _assign(pid, new_jid)
            if trainee_f and trainee_pool_f:
                pool = list(trainee_pool_f)
                random.shuffle(pool)
                for pid, new_jid in zip(trainee_f, pool):
                    _assign(pid, new_jid)

            if promoted_m and promoted_pool_m:
                pool = list(promoted_pool_m)
                random.shuffle(pool)
                for pid, new_jid in zip(promoted_m, pool):
                    _assign(pid, new_jid)
            if promoted_f and promoted_pool_f:
                pool = list(promoted_pool_f)
                random.shuffle(pool)
                for pid, new_jid in zip(promoted_f, pool):
                    _assign(pid, new_jid)

            if unpromoted_m and unpromoted_pool_m:
                pool = list(unpromoted_pool_m)
                random.shuffle(pool)
                for pid, new_jid in zip(unpromoted_m, pool):
                    _assign(pid, new_jid)
            if unpromoted_f and unpromoted_pool_f:
                pool = list(unpromoted_pool_f)
                random.shuffle(pool)
                for pid, new_jid in zip(unpromoted_f, pool):
                    _assign(pid, new_jid)

        elif mode == 'random':
            for pid in trainee_m:
                if trainee_pool_m:
                    _assign(pid, random.choice(trainee_pool_m))
            for pid in trainee_f:
                if trainee_pool_f:
                    _assign(pid, random.choice(trainee_pool_f))

            for pid in promoted_m:
                if promoted_pool_m:
                    _assign(pid, random.choice(promoted_pool_m))
            for pid in promoted_f:
                if promoted_pool_f:
                    _assign(pid, random.choice(promoted_pool_f))

            for pid in unpromoted_m:
                if unpromoted_pool_m:
                    _assign(pid, random.choice(unpromoted_pool_m))
            for pid in unpromoted_f:
                if unpromoted_pool_f:
                    _assign(pid, random.choice(unpromoted_pool_f))

    else:
        if mode == 'shuffle':
            if trainee_chars and available_trainee:
                trainee_pool = list(available_trainee)
                random.shuffle(trainee_pool)
                for pid, new_jid in zip(trainee_chars, trainee_pool):
                    _assign(pid, new_jid)

            if promoted_chars:
                pool_p = list(promoted_jids)
                random.shuffle(pool_p)
                for pid, new_jid in zip(promoted_chars, pool_p):
                    _assign(pid, new_jid)

            if non_trainee_unpromoted:
                pool_u = list(unpromoted_jids)
                random.shuffle(pool_u)
                for pid, new_jid in zip(non_trainee_unpromoted, pool_u):
                    _assign(pid, new_jid)

        elif mode == 'random':
            promoted_list = sorted(promoted_jids)
            unpromoted_list = sorted(unpromoted_jids)
            trainee_list = sorted(available_trainee)

            for pid in trainee_chars:
                if trainee_list:
                    _assign(pid, random.choice(trainee_list))

            for pid in promoted_chars:
                if promoted_list:
                    _assign(pid, random.choice(promoted_list))

            for pid in non_trainee_unpromoted:
                if unpromoted_list:
                    _assign(pid, random.choice(unpromoted_list))

    if manakete_count > 0 and PLAYABLE_PLAYABLE_PIDS:
        playable_all = sorted(PLAYABLE_PLAYABLE_PIDS)
        if gender_lock:
            candidates = [p for p in playable_all if _is_character_female(rom, p)]
        else:
            candidates = playable_all
        count = min(manakete_count, len(candidates))
        for pid in random.sample(candidates, count):
            _assign(pid, JID.MANAKETE_MYRRH)

    return modified_pids


# ---------------------------------------------------------------------------
# Class growths
# ---------------------------------------------------------------------------

def _randomize_class_growths(rom: ROM, jid: int, class_shuffle, rules: dict) -> bool:
    jd = ClassData(rom, jid)
    growths = [jd.growthHP, jd.growthPow, jd.growthSkl,
               jd.growthSpd, jd.growthDef, jd.growthRes,
               jd.growthLck]

    min_g = rules.get('min', 0)
    max_g = rules.get('max', 100)
    mean = rules.get('mean', None)
    stddev = rules.get('stddev', 10)
    pool_total = rules.get('pool_total', None)

    if isinstance(class_shuffle, (int, float)):
        factor = float(class_shuffle)
        if factor == 1.0:
            return False
        growths = [_scale_stat(g, factor, min_g, max_g) for g in growths]
    elif class_shuffle == 'shuffle':
        random.shuffle(growths)
    elif class_shuffle == 'random':
        growths = [_randomize_stat(g, mean, stddev, min_g, max_g) for g in growths]
    elif class_shuffle == 'random_buff':
        buff_range = rules.get('class_buff_range', 0.5)
        growths = [
            _scale_stat(g, 1.0 + random.uniform(0, buff_range), min_g, max_g)
            for g in growths
        ]
    elif class_shuffle == 'pool':
        base_total = pool_total if pool_total is not None else sum(growths)
        growths = _distribute_growth_pool(base_total, min_g, max_g)
    else:
        return False

    (jd.growthHP, jd.growthPow, jd.growthSkl,
     jd.growthSpd, jd.growthDef, jd.growthRes,
     jd.growthLck) = growths
    jd.write(rom)
    return True


# ---------------------------------------------------------------------------
# Growths
# ---------------------------------------------------------------------------

def randomize_growths(rom: ROM, config: dict) -> None:
    rules = config.get('growth_randomization', {})
    char_shuffle = rules.get('character', False)
    class_shuffle = rules.get('class', False)
    min_g = rules.get('min', 0)
    max_g = rules.get('max', 100)
    mean = rules.get('mean', None)
    stddev = rules.get('stddev', 10)
    pool_total = rules.get('pool_total', None)

    if char_shuffle:
        for pid in PLAYABLE_PLAYABLE_PIDS:
            cd = CharacterData(rom, pid)
            growths = [cd.growthHP, cd.growthPow, cd.growthSkl,
                       cd.growthSpd, cd.growthDef, cd.growthRes,
                       cd.growthLck]
            if char_shuffle == 'shuffle':
                random.shuffle(growths)
            elif char_shuffle == 'random':
                growths = [_randomize_stat(g, mean, stddev, min_g, max_g) for g in growths]
            elif char_shuffle == 'pool':
                base_total = pool_total if pool_total is not None else sum(growths)
                growths = _distribute_growth_pool(base_total, min_g, max_g)
            (cd.growthHP, cd.growthPow, cd.growthSkl,
             cd.growthSpd, cd.growthDef, cd.growthRes,
             cd.growthLck) = growths
            cd.write(rom)

    if class_shuffle:
        count = 0
        for jid in range(1, CLASS_COUNT + 1):
            if _randomize_class_growths(rom, jid, class_shuffle, rules):
                count += 1
        if count:
            _vprint(f"Randomized class growth rates for {count} class(es)")


# ---------------------------------------------------------------------------
# Base stats
# ---------------------------------------------------------------------------

def randomize_base_stats(rom: ROM, config: dict) -> None:
    rules = config.get('base_stat_randomization', {})
    char_enabled = rules.get('character', False)
    class_enabled = rules.get('class', False)
    preserve_base = rules.get('preserve_base', True)
    shuffle_con_mov = rules.get('shuffle_con_mov', True)
    mean = rules.get('mean', None)
    stddev = rules.get('stddev', 3)

    con_enabled, con_min, con_player_min, con_stddev = _get_con_rules(rules, class_enabled)

    if isinstance(char_enabled, (int, float)) and not isinstance(char_enabled, bool):
        factor = float(char_enabled)
        for pid in PLAYABLE_PLAYABLE_PIDS:
            cd = CharacterData(rom, pid)
            cd.baseHP = _scale_stat(cd.baseHP, factor, 0, 30)
            cd.basePow = _scale_stat(cd.basePow, factor, 0, 25)
            cd.baseSkl = _scale_stat(cd.baseSkl, factor, 0, 25)
            cd.baseSpd = _scale_stat(cd.baseSpd, factor, 0, 25)
            cd.baseDef = _scale_stat(cd.baseDef, factor, 0, 25)
            cd.baseRes = _scale_stat(cd.baseRes, factor, 0, 25)
            cd.baseLck = _scale_stat(cd.baseLck, factor, 0, 30)
            cd.write(rom)

    if isinstance(class_enabled, (int, float)) and not isinstance(class_enabled, bool):
        factor = float(class_enabled)
        for jid in STANDARD_JIDS:
            jd = ClassData(rom, jid)
            jd.baseHP = _scale_stat(jd.baseHP, factor, 0, 30)
            jd.basePow = _scale_stat(jd.basePow, factor, 0, 25)
            jd.baseSkl = _scale_stat(jd.baseSkl, factor, 0, 25)
            jd.baseSpd = _scale_stat(jd.baseSpd, factor, 0, 25)
            jd.baseDef = _scale_stat(jd.baseDef, factor, 0, 25)
            jd.baseRes = _scale_stat(jd.baseRes, factor, 0, 25)
            jd.baseCon = _scale_stat(jd.baseCon, factor, con_min, 25) if con_enabled else jd.baseCon
            jd.write(rom)

    if isinstance(char_enabled, str) and char_enabled == 'shuffle':
        for pid in PLAYABLE_PLAYABLE_PIDS:
            cd = CharacterData(rom, pid)
            stats = [cd.baseHP, cd.basePow, cd.baseSkl, cd.baseSpd,
                     cd.baseDef, cd.baseRes, cd.baseLck]
            random.shuffle(stats)
            (cd.baseHP, cd.basePow, cd.baseSkl, cd.baseSpd,
             cd.baseDef, cd.baseRes, cd.baseLck) = stats
            cd.write(rom)

    if isinstance(char_enabled, str) and char_enabled == 'random':
        for pid in PLAYABLE_PLAYABLE_PIDS:
            cd = CharacterData(rom, pid)
            cd.baseHP = _randomize_stat(cd.baseHP, mean, stddev, 0, 30)
            cd.basePow = _randomize_stat(cd.basePow, mean, stddev, 0, 25)
            cd.baseSkl = _randomize_stat(cd.baseSkl, mean, stddev, 0, 25)
            cd.baseSpd = _randomize_stat(cd.baseSpd, mean, stddev, 0, 25)
            cd.baseDef = _randomize_stat(cd.baseDef, mean, stddev, 0, 25)
            cd.baseRes = _randomize_stat(cd.baseRes, mean, stddev, 0, 25)
            cd.baseLck = _randomize_stat(cd.baseLck, mean, stddev, 0, 30)
            if con_enabled:
                cd.baseCon = _randomize_stat(cd.baseCon, mean, con_stddev, con_player_min, 25)
            cd.write(rom)

    if isinstance(class_enabled, str) and class_enabled == 'shuffle':
        cross_tier = rules.get('cross_tier_scramble', False)
        if cross_tier:
            groups = [list(STANDARD_JIDS)]
        else:
            prom, unpr = _split_class_pool(rom)
            groups = [sorted(prom), sorted(unpr), sorted(TRAINEE_JIDS)]
        stat_count = 8 if shuffle_con_mov and con_enabled else (7 if shuffle_con_mov else 6)
        for group in groups:
            if len(group) < 2:
                continue
            pairs = []
            for jid in group:
                jd = ClassData(rom, jid)
                stats = [jd.baseHP, jd.basePow, jd.baseSkl, jd.baseSpd,
                         jd.baseDef, jd.baseRes]
                if con_enabled and shuffle_con_mov:
                    stats.append(jd.baseCon)
                if shuffle_con_mov:
                    stats.append(jd.baseMov)
                if sum(stats[:6]) == 0:
                    continue
                if preserve_base:
                    pairs.append((jid, stats))
                else:
                    pairs.append((jid, [random.randint(0, 20) for _ in range(stat_count)]))
            if len(pairs) < 2:
                continue
            shuffled_stats = [p[1] for p in pairs]
            random.shuffle(shuffled_stats)
            for (jid, _), stats in zip(pairs, shuffled_stats):
                jd = ClassData(rom, jid)
                (jd.baseHP, jd.basePow, jd.baseSkl, jd.baseSpd,
                 jd.baseDef, jd.baseRes) = stats[:6]
                idx = 6
                if con_enabled and shuffle_con_mov:
                    jd.baseCon = stats[idx]
                    idx += 1
                if shuffle_con_mov:
                    jd.baseMov = stats[idx]
                jd.write(rom)

    if isinstance(class_enabled, str) and class_enabled == 'random':
        for jid in STANDARD_JIDS:
            jd = ClassData(rom, jid)
            jd.baseHP = _randomize_stat(jd.baseHP, mean, stddev, 0, 30)
            jd.basePow = _randomize_stat(jd.basePow, mean, stddev, 0, 25)
            jd.baseSkl = _randomize_stat(jd.baseSkl, mean, stddev, 0, 25)
            jd.baseSpd = _randomize_stat(jd.baseSpd, mean, stddev, 0, 25)
            jd.baseDef = _randomize_stat(jd.baseDef, mean, stddev, 0, 25)
            jd.baseRes = _randomize_stat(jd.baseRes, mean, stddev, 0, 25)
            if con_enabled:
                jd.baseCon = _randomize_stat(jd.baseCon, mean, con_stddev, con_min, 25)
            jd.write(rom)


# ---------------------------------------------------------------------------
# Promotion gain sync
# ---------------------------------------------------------------------------

def synchronize_promotion_gains(rom: ROM) -> None:
    changed = 0
    for male_jid, female_jid in MALE_FEMALE_PAIRS:
        try:
            jd_m = ClassData(rom, male_jid)
            jd_f = ClassData(rom, female_jid)
        except Exception:
            continue
        fields = ['promotionHp', 'promotionPow', 'promotionSkl',
                  'promotionSpd', 'promotionDef', 'promotionRes']
        dirty = False
        for f in fields:
            vm = getattr(jd_m, f)
            vf = getattr(jd_f, f)
            best = vm if vm > vf else vf
            if vm != best:
                setattr(jd_m, f, best)
                dirty = True
            if vf != best:
                setattr(jd_f, f, best)
                dirty = True
        if dirty:
            jd_m.write(rom)
            jd_f.write(rom)
            changed += 1
    if changed:
        _vprint(f"Synchronized promotion gains for {changed} class pair(s)")


# ---------------------------------------------------------------------------
# Affinity
# ---------------------------------------------------------------------------

def randomize_affinity(rom: ROM, config: dict) -> None:
    rules = config.get('affinity_randomization', {})
    if not rules.get('enabled', False):
        return
    affinities = list(range(1, 8))
    for pid in PLAYABLE_PLAYABLE_PIDS:
        cd = CharacterData(rom, pid)
        cd.affinity = random.choice(affinities)
        cd.write(rom)


# ---------------------------------------------------------------------------
# Unit definitions
# ---------------------------------------------------------------------------

def patch_unit_definitions(rom: ROM, modified_pids: Set[int],
                           ud_arrays: List[Tuple[int, int]]) -> int:
    if not modified_pids:
        return 0
    total_patched = 0
    for ud_offset, _ in ud_arrays:
        patched = 0
        arr_pos = ud_offset
        while arr_pos + UNIT_DEF_SIZE <= len(rom.data):
            chunk = rom.data[arr_pos:arr_pos + UNIT_DEF_SIZE]
            if all(b == 0 for b in chunk):
                break
            char_idx = chunk[0]
            if char_idx in modified_pids and chunk[1] != 0:
                rom.data[arr_pos + 1] = 0
                patched += 1
            arr_pos += UNIT_DEF_SIZE
        if patched:
            total_patched += patched
    return total_patched


# ---------------------------------------------------------------------------
# Weapon effects
# ---------------------------------------------------------------------------

def randomize_weapon_stats(rom: ROM, config: dict) -> None:
    rules = config.get('weapon_randomization', {})
    if not rules.get('enabled', False):
        return

    include_ballista = config.get('item_randomization', {}).get('include_ballista_items', False)
    mean = rules.get('mean', None)
    global_stddev = rules.get('stddev', 5)

    stats_to_randomize = []
    for stat_name in ('might', 'hit', 'weight', 'crit'):
        setting = rules.get(stat_name, True)
        if not setting:
            continue
        if setting is True:
            setting = 'random'
        stat_stddev = rules.get(f'{stat_name}_stddev', global_stddev)
        stats_to_randomize.append((stat_name, setting, stat_stddev))

    if not stats_to_randomize:
        return

    patched = 0
    bounds = {
        'might': (rules.get('min_might', 1), rules.get('max_might', 20)),
        'hit': (rules.get('min_hit', 30), rules.get('max_hit', 120)),
        'weight': (rules.get('min_weight', 1), rules.get('max_weight', 20)),
        'crit': (rules.get('min_crit', 0), rules.get('max_crit', 30)),
    }
    offsets = {'might': 0x15, 'hit': 0x16, 'weight': 0x17, 'crit': 0x18}

    item_table_off = rom_offset(ITEM_TABLE_ADDR)
    data_len = len(rom.data)

    for item_id in range(256):
        off = item_table_off + item_id * ITEM_DATA_SIZE
        if off + ITEM_DATA_SIZE > data_len:
            break
        raw = rom.data[off:off + ITEM_DATA_SIZE]
        stored_id = raw[6]
        wep_type = raw[7]

        if stored_id != item_id or wep_type > 7:
            continue
        if item_id in MONSTER_BLOCKED_ITEM_IDS or item_id in STORY_EXCLUSIVE_ITEM_IDS:
            continue
        if not include_ballista and item_id in BALLISTA_ITEM_IDS:
            continue
        if raw[0x14] == 0:
            continue

        for stat_name, setting, stat_stddev in stats_to_randomize:
            lo, hi = bounds[stat_name]
            orig = raw[offsets[stat_name]]
            if stat_name == 'might' and wep_type == 4:
                continue
            if setting == 'random':
                new_val = _randomize_stat(orig, mean, stat_stddev, lo, hi)
                rom.write_u8(off + offsets[stat_name], new_val)
                patched += 1
            elif isinstance(setting, (int, float)):
                new_val = _scale_stat(orig, float(setting), lo, hi)
                rom.write_u8(off + offsets[stat_name], new_val)
                patched += 1

    if patched:
        _vprint(f"Randomized stats for {patched} weapon item(s)")


def randomize_weapon_effects(rom: ROM, config: dict) -> None:
    rules = config.get('weapon_effects', {})
    chance = rules.get('enabled', False)
    if not chance:
        return

    include_ballista = config.get('item_randomization', {}).get('include_ballista_items', False)

    effect_map = {
        'poison': 0x01, 'nosferatu': 0x02, 'eclipse': 0x03,
        'devil': 0x04, 'stone': 0x05,
    }

    effect_ids = []
    weights = []
    for name, eid in effect_map.items():
        val = rules.get(name, True)
        if val is False:
            continue
        if val is True:
            w = 1
        elif isinstance(val, (int, float)):
            w = float(val)
        else:
            continue
        if w <= 0:
            continue
        effect_ids.append(eid)
        weights.append(w)

    # Brave (attr bit 5 = 0x20) and reaver (attr bit 8 = 0x100)
    brave_pct = 0
    reaver_pct = 0
    bv = rules.get('brave', 0)
    if isinstance(bv, bool):
        brave_pct = 100 if bv else 0
    elif isinstance(bv, (int, float)):
        brave_pct = float(bv)
    rv = rules.get('reaver', 0)
    if isinstance(rv, bool):
        reaver_pct = 100 if rv else 0
    elif isinstance(rv, (int, float)):
        reaver_pct = float(rv)

    has_work = bool(effect_ids) or brave_pct or reaver_pct
    if not has_work:
        return

    patched_eff = 0
    patched_brave = 0
    patched_reaver = 0
    item_table_off = rom_offset(ITEM_TABLE_ADDR)
    data_len = len(rom.data)

    for item_id in range(256):
        off = item_table_off + item_id * ITEM_DATA_SIZE
        if off + ITEM_DATA_SIZE > data_len:
            break
        raw = rom.data[off:off + ITEM_DATA_SIZE]
        stored_id = raw[6]
        wep_type = raw[7]

        if stored_id != item_id or wep_type > 7:
            continue
        if item_id in MONSTER_BLOCKED_ITEM_IDS or item_id in STORY_EXCLUSIVE_ITEM_IDS:
            continue
        if item_id in STAFF_ITEM_IDS:
            continue
        if not include_ballista and item_id in BALLISTA_ITEM_IDS:
            continue
        if raw[0x14] == 0:
            continue

        # Weapon effect ID (mutually exclusive, written to offset 0x1F)
        if effect_ids and random.randint(1, 100) <= chance:
            eff = random.choices(effect_ids, weights=weights, k=1)[0]
            rom.write_u8(off + 0x1F, eff)
            patched_eff += 1

        # Brave attribute bit 5 (0x20) at offset 0x08
        if brave_pct and random.randint(1, 100) <= brave_pct:
            attrs = rom.read_u32(off + 0x08)
            rom.write_u32(off + 0x08, attrs | 0x20)
            patched_brave += 1

        # Reaver attribute bit 8 (0x100) at offset 0x08
        if reaver_pct and random.randint(1, 100) <= reaver_pct:
            attrs = rom.read_u32(off + 0x08)
            rom.write_u32(off + 0x08, attrs | 0x100)
            patched_reaver += 1

    parts = []
    if patched_eff:
        parts.append(f"effects to {patched_eff}")
    if patched_brave:
        parts.append(f"brave to {patched_brave}")
    if patched_reaver:
        parts.append(f"reaver to {patched_reaver}")
    if parts:
        _vprint("Applied weapon " + ", ".join(parts) + " item(s)")


# ---------------------------------------------------------------------------
# Item randomization (UD array items)
# ---------------------------------------------------------------------------

def randomize_unit_items(rom: ROM, config: dict, modified_pids: Set[int],
                         weapon_pools: dict, ud_arrays: List[Tuple[int, int]]) -> int:
    data = rom.data
    total_patched = 0

    for ud_offset, _ in ud_arrays:
        patched = 0
        arr_pos = ud_offset
        while arr_pos + UNIT_DEF_SIZE <= len(data):
            chunk = data[arr_pos:arr_pos + UNIT_DEF_SIZE]
            if all(b == 0 for b in chunk):
                break
            char_idx = chunk[0]
            if char_idx not in modified_pids:
                arr_pos += UNIT_DEF_SIZE
                continue

            cd = CharacterData(rom, char_idx)
            old_items = list(chunk[12:16])
            new_items = list(old_items)

            is_manakete = cd.jidDefault in MANAKETE_JIDS

            if is_manakete:
                new_items = [DRAGONSTONE_ITEM_ID, VULNERARY_ITEM_ID, VULNERARY_ITEM_ID, 0]
            else:
                for slot_idx in range(4):
                    item_id = old_items[slot_idx]
                    if item_id == 0:
                        continue
                    idd = ItemData(rom, item_id)
                    if not idd.is_weapon():
                        continue
                    if cd.baseWexp[idd.weapon_type] > 0 and idd.weapon_rank <= cd.baseWexp[idd.weapon_type]:
                        if not (idd.attributes & 0x1000):
                            continue
                        allowed = CLASS_LOCKED_ITEM_RESTRICTIONS.get(item_id, set())
                        if cd.jidDefault in allowed:
                            continue
                    new_item_id = _pick_weapon_for_type(rom, weapon_pools, cd.baseWexp, class_jid=cd.jidDefault)
                    if new_item_id is not None:
                        new_items[slot_idx] = new_item_id

                has_weapon = any(
                    ItemData(rom, it).is_weapon()
                    for it in new_items if it != 0
                )
                if not has_weapon:
                    new_item_id = _pick_weapon_for_type(rom, weapon_pools, cd.baseWexp, class_jid=cd.jidDefault)
                    if new_item_id is not None:
                        for slot_idx in range(4):
                            if new_items[slot_idx] == 0:
                                new_items[slot_idx] = new_item_id
                                break

            if new_items != old_items:
                for slot_idx in range(4):
                    data[arr_pos + 12 + slot_idx] = new_items[slot_idx]
                patched += 1
            arr_pos += UNIT_DEF_SIZE

        if patched:
            total_patched += patched

    return total_patched


def _shuffle_unit_items(rom: ROM, ud_arrays: List[Tuple[int, int]]) -> int:
    data = rom.data
    items_by_entry = []

    for ud_offset, count in ud_arrays:
        arr_pos = ud_offset
        for entry_idx in range(count):
            if arr_pos + UNIT_DEF_SIZE > len(data):
                break
            chunk = data[arr_pos:arr_pos + UNIT_DEF_SIZE]
            char_idx = chunk[0]
            if char_idx == 0 or char_idx > 114:
                arr_pos += UNIT_DEF_SIZE
                continue
            cd = CharacterData(rom, char_idx)
            is_manakete = cd.jidDefault in MANAKETE_JIDS
            if not is_manakete:
                for slot_idx in range(4):
                    item_id = data[arr_pos + 12 + slot_idx]
                    if item_id != 0:
                        idd = ItemData(rom, item_id)
                        if idd.is_weapon():
                            items_by_entry.append((arr_pos, slot_idx, item_id))
            arr_pos += UNIT_DEF_SIZE

    if len(items_by_entry) < 2:
        return 0

    shuffled_ids = [it[2] for it in items_by_entry]
    random.shuffle(shuffled_ids)

    for (arr_pos, slot_idx, _), new_id in zip(items_by_entry, shuffled_ids):
        data[arr_pos + 12 + slot_idx] = new_id

    return len(items_by_entry)


# ---------------------------------------------------------------------------
# Prf weapon type fix
# ---------------------------------------------------------------------------

def _fix_prf_weapon_types(rom: ROM, modified_pids: Set[int]) -> None:
    for pid, (ability_val, lock_attrs, item_ids) in CHAR_LOCK_ATTRS.items():
        if pid not in modified_pids:
            continue
        char_off = rom_offset(CHARACTER_TABLE_ADDR) + (pid - 1) * PINFO_SIZE
        cur_attrs = _U32.unpack_from(rom.data, char_off + 0x28)[0]
        if not (cur_attrs & lock_attrs):
            _U32.pack_into(rom.data, char_off + 0x28, cur_attrs | lock_attrs)
        cd = CharacterData(rom, pid)
        jd = ClassData(rom, cd.jidDefault)
        usable = [i for i in range(8) if jd.baseWexp[i] > 0]
        for item_id in item_ids:
            off = rom_offset(ITEM_TABLE_ADDR) + item_id * ITEM_DATA_SIZE
            if off + ITEM_DATA_SIZE > len(rom.data):
                continue
            rom.data[off + 0x21] = ability_val
            if usable:
                orig_type = 0 if pid == PID.EIRIKA else 1
                new_type = orig_type if orig_type in usable else usable[0]
                rom.data[off + 7] = new_type

            efx = WTYPE_EFX_MAP.get(rom.data[off + 7])
            if efx is not None:
                spell_base = rom_offset(SPELL_ASSOC_ADDR)
                scan = spell_base
                terminator = scan + 0x1000
                while scan < terminator:
                    entry_item = _U16.unpack_from(rom.data, scan)[0]
                    if entry_item == 0xFFFF:
                        break
                    if entry_item == item_id:
                        _U16.pack_into(rom.data, scan + 4, efx)
                        _U16.pack_into(rom.data, scan + 14, WTYPE_FLAG_MAP.get(rom.data[off + 7], 0))
                        break
                    scan += SPELL_ASSOC_ENTRY_SIZE


# ---------------------------------------------------------------------------
# Event items
# ---------------------------------------------------------------------------

def randomize_event_items(rom: ROM, config: dict, modified_pids: Set[int],
                          weapon_pools: dict) -> int:
    include_ballista = config.get('item_randomization', {}).get('include_ballista_items', False)
    data = rom.data
    giveitem_events = _scan_giveitem_events(data, len(data))
    patched = 0

    for write_offset, item_id, pack_fmt in giveitem_events:
        if item_id in MONSTER_BLOCKED_ITEM_IDS or item_id in STORY_EXCLUSIVE_ITEM_IDS:
            continue
        if not include_ballista and item_id in BALLISTA_ITEM_IDS:
            continue

        idd = ItemData(rom, item_id)
        if not idd.is_weapon():
            continue

        candidates = []
        for t in range(8):
            if weapon_pools[t]:
                for wid, rank in weapon_pools[t]:
                    candidates.append(wid)
        if not candidates:
            continue

        new_item_id = random.choice(candidates)
        if new_item_id != item_id:
            struct.pack_into(pack_fmt, data, write_offset, new_item_id)
            patched += 1

    return patched


# ---------------------------------------------------------------------------
# Loot
# ---------------------------------------------------------------------------

def _randomize_loot(rom: ROM, giveitem_events: List[Tuple[int, int, str]],
                    include_ballista: bool = False) -> int:
    pool = _build_loot_pool(include_ballista)
    if not pool:
        return 0
    patched = 0
    for write_offset, item_id, pack_fmt in _scan_loot_events(rom, giveitem_events, include_ballista):
        new_id = random.choice(pool)
        if new_id != item_id:
            struct.pack_into(pack_fmt, rom.data, write_offset, new_id)
            patched += 1
    return patched


def _shuffle_loot(rom: ROM, giveitem_events: List[Tuple[int, int, str]],
                  include_ballista: bool = False) -> int:
    items = _scan_loot_events(rom, giveitem_events, include_ballista)
    if len(items) < 2:
        return 0
    shuffled_ids = [item_id for _, item_id, _ in items]
    random.shuffle(shuffled_ids)
    for (write_offset, _, pack_fmt), new_id in zip(items, shuffled_ids):
        cur = struct.unpack_from(pack_fmt, rom.data, write_offset)[0]
        if cur != new_id:
            struct.pack_into(pack_fmt, rom.data, write_offset, new_id)
    return len(items)


def randomize_loot(rom: ROM, config: dict,
                   giveitem_events: List[Tuple[int, int, str]]) -> int:
    rules = config.get('loot_randomization', {})
    if not rules.get('enabled', False):
        return 0
    include_ballista = config.get('item_randomization', {}).get('include_ballista_items', False)
    mode = rules.get('mode', 'random')
    if mode == 'shuffle':
        return _shuffle_loot(rom, giveitem_events, include_ballista)
    return _randomize_loot(rom, giveitem_events, include_ballista)


def _randomize_chest(rom: ROM, chest_items: List[Tuple[int, int, str]],
                     include_ballista: bool = False) -> int:
    pool = [i for i in _build_loot_pool(include_ballista) if i != 0x77]
    if not pool:
        return 0
    patched = 0
    for write_offset, item_id, pack_fmt in chest_items:
        new_id = random.choice(pool)
        if new_id != item_id:
            struct.pack_into(pack_fmt, rom.data, write_offset, new_id)
            patched += 1
    return patched


def _shuffle_chest(rom: ROM, chest_items: List[Tuple[int, int, str]],
                   include_ballista: bool = False) -> int:
    if len(chest_items) < 2:
        return 0
    shuffled_ids = [item_id for _, item_id, _ in chest_items]
    random.shuffle(shuffled_ids)
    for (write_offset, _, pack_fmt), new_id in zip(chest_items, shuffled_ids):
        cur = struct.unpack_from(pack_fmt, rom.data, write_offset)[0]
        if cur != new_id:
            struct.pack_into(pack_fmt, rom.data, write_offset, new_id)
    return len(chest_items)


def randomize_chest(rom: ROM, config: dict) -> int:
    rules = config.get('loot_randomization', {})
    if not rules.get('enabled', False):
        return 0
    include_ballista = config.get('item_randomization', {}).get('include_ballista_items', False)
    chest_items = _scan_chest_items(rom)
    if not chest_items:
        return 0
    mode = rules.get('mode', 'random')
    if mode == 'shuffle':
        return _shuffle_chest(rom, chest_items, include_ballista)
    return _randomize_chest(rom, chest_items, include_ballista)


# ---------------------------------------------------------------------------
# Promotion items
# ---------------------------------------------------------------------------

def randomize_promotion_items(rom: ROM, config: dict,
                              ud_arrays: List[Tuple[int, int]]) -> int:
    rules = config.get('promotion_items', {})
    if not rules.get('enabled', True):
        return 0

    data = rom.data
    total = 0
    master_seal_table_addr = PROMO_ITEM_TABLES[MASTER_SEAL_ITEM_ID]

    if rules.get('master_seal_universal', True):
        # Phase 1: Zero out non-MS permission tables
        for item_id, table_addr in PROMO_ITEM_TABLES.items():
            if item_id == MASTER_SEAL_ITEM_ID:
                continue
            off = rom_offset(table_addr)
            data[off:off + 0x41] = bytes(0x41)
            total += 1

        # Phase 2: Fill ALL promotion item byte-per-class tables
        MAX_TABLE_CLS = 0x40
        for item_id, table_addr in PROMO_ITEM_TABLES.items():
            if item_id not in PROMOTION_ITEM_IDS:
                continue
            tbl_off = rom_offset(table_addr)
            data[tbl_off:tbl_off + 0x41] = bytes([0x01] * 0x41)
            for cls in range(1, MAX_TABLE_CLS + 1):
                try:
                    cd = ClassData(rom, cls)
                    promo_jid = cd.jidPromotion
                    byte_val = promo_jid + 1 if promo_jid > 0 and promo_jid != cls else 0x01
                except Exception:
                    byte_val = 0x01
                pos = tbl_off + cls
                if pos < len(data):
                    data[pos] = byte_val
        total += 1

        # Phase 3: Route non-promo items to MS stub
        ft_off = rom_offset(PROMO_FUNCTION_TABLE_ADDR)
        ms_stub_addr = _U32.unpack_from(data, ft_off + 7 * 4)[0]
        for i in range(7):
            item_id = 0x62 + i
            if item_id in PROMOTION_ITEM_IDS:
                continue
            _U32.pack_into(data, ft_off + i * 4, ms_stub_addr)
            total += 1

        # Phase 4: Modify class-specific tables
        for cls in range(20):
            table_addr = PROMO_CLASS_TABLE_BASE + cls * 0x41
            if cls == 0:
                promo_jid = 0
            else:
                try:
                    promo_jid = ClassData(rom, cls).jidPromotion
                except Exception:
                    promo_jid = 0
            off = rom_offset(table_addr)
            byte_val = promo_jid + 1 if promo_jid > 0 and promo_jid != cls else 0x01
            for item_id in [MASTER_SEAL_ITEM_ID] + sorted(PROMOTION_ITEM_IDS):
                if item_id > 0x69:
                    continue
                data[off + item_id] = byte_val
            total += 1

        # Phase 4b: Redirect class 20
        cf_off = rom_offset(PROMO_CLASS_FUNCTION_TABLE)
        _U32.pack_into(data, cf_off + 20 * 4, ms_stub_addr)
        total += 1

        # Phase 5: Redirect ALL use_eff literal pools
        ALL_UE_LITERALS = [
            0x080291D0, 0x08029214, 0x08029398, 0x080293A0,
            0x080293A8, 0x080293B0, 0x080293B8, 0x080293C8,
            0x080293D0, 0x080293D8, 0x080293E0, 0x08029408,
        ]
        for lit_addr in ALL_UE_LITERALS:
            lit_off = rom_offset(lit_addr)
            old_val = _U32.unpack_from(data, lit_off)[0]
            if old_val != 0x088ADF76:
                _U32.pack_into(data, lit_off, 0x088ADF76)
                total += 1
        _vprint(f"  Redirected {len(ALL_UE_LITERALS)} use_eff handler literal(s)")

        # Phase 5b: Replace invalid JIDs
        UE_LIST = 0x088ADF76
        ue_off = rom_offset(UE_LIST)
        added = 0
        for jid_to_add in (0x01, 0x02):
            for scan_i in range(ue_off, ue_off + 64):
                if data[scan_i] == 0x00:
                    break
                if data[scan_i] in (0x7E, 0x7F) and data[scan_i] != jid_to_add:
                    data[scan_i] = jid_to_add
                    added += 1
                    break
        if added:
            total += 1
            _vprint(f"  Replaced {added} invalid JID(s) in use_eff list")

        _vprint("Applied Master Seal universal promotion")

    # Phase 6: Force use_eff=0x2D on ALL promotion items
    ms_item_off = rom_offset(ITEM_TABLE_ADDR) + MASTER_SEAL_ITEM_ID * ITEM_DATA_SIZE
    ms_use_eff = data[ms_item_off + 0x1E]
    for item_id in PROMOTION_ITEM_IDS:
        dst_off = rom_offset(ITEM_TABLE_ADDR) + item_id * ITEM_DATA_SIZE
        data[dst_off + 0x1E] = ms_use_eff
        total += 1
    _vprint(f"Set use_eff=0x{ms_use_eff:02X} for {len(PROMOTION_ITEM_IDS)} promotion items")

    # Phase 7: Replace promotion items in UD arrays
    if rules.get('replace_distribution', True):
        replaced = 0
        for ud_offset, _ in ud_arrays:
            arr_pos = ud_offset
            while arr_pos + UNIT_DEF_SIZE <= len(data):
                chunk = data[arr_pos:arr_pos + UNIT_DEF_SIZE]
                if all(b == 0 for b in chunk):
                    break
                for slot_idx in range(4):
                    item_id = data[arr_pos + 0x0C + slot_idx]
                    if item_id in PROMOTION_ITEM_IDS:
                        data[arr_pos + 0x0C + slot_idx] = MASTER_SEAL_ITEM_ID
                        replaced += 1
                arr_pos += UNIT_DEF_SIZE
        if replaced:
            _vprint(f"Replaced {replaced} promotion item(s) with Master Seal in unit definitions")

        # Phase 8: Copy MS data to other promo items
        ms_item_off = rom_offset(ITEM_TABLE_ADDR) + MASTER_SEAL_ITEM_ID * ITEM_DATA_SIZE
        ms_item_data = data[ms_item_off:ms_item_off + ITEM_DATA_SIZE]

        for item_id in PROMOTION_ITEM_IDS:
            dst_off = rom_offset(ITEM_TABLE_ADDR) + item_id * ITEM_DATA_SIZE
            for byte_idx in range(ITEM_DATA_SIZE):
                if byte_idx == 6:
                    continue
                data[dst_off + byte_idx] = ms_item_data[byte_idx]
            data[dst_off + 6] = item_id
            total += 1
        _vprint(f"Copied Master Seal item data to {len(PROMOTION_ITEM_IDS)} promotion items")

        # Phase 9: GiveItem replacement
        ev_replaced = 0
        for write_offset, item_id, pack_fmt in _scan_giveitem_events(data, len(data)):
            if item_id in PROMOTION_ITEM_IDS and item_id != MASTER_SEAL_ITEM_ID:
                struct.pack_into(pack_fmt, data, write_offset, MASTER_SEAL_ITEM_ID)
                ev_replaced += 1
        if ev_replaced:
            total += 1
            _vprint(f"Replaced {ev_replaced} promotion item(s) with Master Seal in GiveItem events")

    return total


# ---------------------------------------------------------------------------
# Enemy randomization
# ---------------------------------------------------------------------------

def _move_group_key(move_table_ptr: int) -> str:
    FLYER_PTR = 0x0880BB96
    WATER_PTRS = {0x0880B98E, 0x0880B90C}
    MOUNTAIN_PTR = 0x0880B94D
    if move_table_ptr == FLYER_PTR:
        return 'flyer'
    if move_table_ptr in WATER_PTRS:
        return 'water'
    if move_table_ptr == MOUNTAIN_PTR:
        return 'mountain'
    return 'foot'


def randomize_enemies(rom: ROM, config: dict,
                      ud_arrays: List[Tuple[int, int]],
                      ch_ud_arrays: List[Tuple[int, int]],
                      weapon_pools: Optional[dict] = None) -> int:
    rules = config.get('enemy_randomization', {})
    if not rules.get('enabled', False):
        return 0

    rand_classes = rules.get('randomize_classes', True)
    rand_items = rules.get('randomize_items', True)
    include_monsters = rules.get('include_monsters', False)
    include_bosses = rules.get('include_bosses', False)
    randomize_monster_classes = rules.get('randomize_monster_classes', False)
    omit_jids = _parse_omit_classes(config, 'enemy_randomization')

    pid_range = [p for p in range(35, 256) if p != FINAL_BOSS_PID]
    if not include_bosses:
        pid_range = [p for p in pid_range if p not in BOSS_PIDS]

    # Build enemy-eligible class pools
    enemy_jids = set(STANDARD_JIDS)
    enemy_jids.discard(JID.EIRIKA_LORD)
    enemy_jids.discard(JID.EPHRAIM_LORD)
    enemy_jids.discard(JID.EIRIKA_MASTER_LORD)
    enemy_jids.discard(JID.EPHRAIM_MASTER_LORD)
    enemy_jids -= TRAINEE_JIDS

    if include_monsters:
        enemy_jids |= MONSTER_JIDS
        enemy_jids |= EXTRA_MONSTER_JIDS

    enemy_jids -= ENEMY_EXCLUDED_JIDS
    enemy_jids -= omit_jids

    # Filter out staves-only classes
    staves_only = set()
    for jid in enemy_jids:
        try:
            jd = ClassData(rom, jid)
            has_non_staff = any(jd.baseWexp[t] > 0 for t in range(8) if t != 4)
            if not has_non_staff:
                staves_only.add(jid)
        except Exception:
            pass
    enemy_jids -= staves_only

    # Split by tier
    promoted_pool = set()
    unpromoted_pool = set()
    for jid in sorted(enemy_jids):
        jd = ClassData(rom, jid)
        if jd.attributes & CA_PROMOTED:
            promoted_pool.add(jid)
        else:
            unpromoted_pool.add(jid)

    # Group by movement category
    promoted_groups = {}
    for jid in promoted_pool:
        jd = ClassData(rom, jid)
        key = _move_group_key(jd.moveTable[0])
        promoted_groups.setdefault(key, []).append(jid)

    unpromoted_groups = {}
    for jid in unpromoted_pool:
        jd = ClassData(rom, jid)
        key = _move_group_key(jd.moveTable[0])
        unpromoted_groups.setdefault(key, []).append(jid)

    # Combine UD arrays
    all_ud_offsets = list({off for off, _ in ud_arrays} | {off for off, _ in ch_ud_arrays})

    total = 0

    # Phase A: CharacterData.jidDefault
    enemy_gender_lock = rules.get('gender_lock', False)
    if rand_classes:
        if tqdm:
            pbar = tqdm(total=len(pid_range), desc="Enemy classes (A)", unit="pid", leave=False)
        for pid in pid_range:
            cd = CharacterData(rom, pid)
            if cd.jidDefault == 0:
                if tqdm: pbar.update(1)
                continue

            orig_jid = cd.jidDefault
            if not randomize_monster_classes and (orig_jid in MONSTER_JIDS or orig_jid in EXTRA_MONSTER_JIDS):
                if tqdm: pbar.update(1)
                continue

            orig_class = ClassData(rom, orig_jid)
            is_promoted = bool(orig_class.attributes & CA_PROMOTED)
            key = _move_group_key(orig_class.moveTable[0])
            candidates = (promoted_groups if is_promoted else unpromoted_groups).get(key, [orig_jid])

            if enemy_gender_lock and pid in BOSS_PIDS:
                is_female = _is_character_female(rom, pid)
                filtered = []
                for c in candidates:
                    sj = _swap_gendered_class(c, is_female)
                    if is_female and sj in MALE_EXCLUSIVE_JIDS:
                        continue
                    if not is_female and sj in FEMALE_EXCLUSIVE_JIDS:
                        continue
                    filtered.append(sj)
                candidates = filtered if filtered else [_swap_gendered_class(orig_jid, is_female)]

            new_jid = random.choice(candidates)
            if new_jid != orig_jid:
                rom.data[cd.offset + 5] = new_jid
                total += 1
            if tqdm: pbar.update(1)
        if tqdm: pbar.close()

    # Boss buffs
    boss_buffs_rules = rules.get('boss_buffs', {})
    boss_growth_mode = boss_buffs_rules.get('growths', {}).get('mode', False)
    boss_stat_mode = boss_buffs_rules.get('base_stats', {}).get('mode', False)
    boss_max_ranks = boss_buffs_rules.get('max_weapon_ranks', True)
    boss_pids_in_scope = [p for p in pid_range if p in BOSS_PIDS]
    if boss_pids_in_scope and (boss_growth_mode or boss_stat_mode or boss_max_ranks):
        buff_growths = boss_buffs_rules.get('growths', {})
        buff_stats = boss_buffs_rules.get('base_stats', {})
        for pid in boss_pids_in_scope:
            cd = CharacterData(rom, pid)

            if boss_growth_mode:
                grow = [cd.growthHP, cd.growthPow, cd.growthSkl,
                        cd.growthSpd, cd.growthDef, cd.growthRes,
                        cd.growthLck]
                if isinstance(boss_growth_mode, (int, float)):
                    grow = [_scale_stat(g, float(boss_growth_mode), 0, 100) for g in grow]
                elif boss_growth_mode == 'random_buff':
                    br = buff_growths.get('buff_range', 0.3)
                    grow = [_scale_stat(g, 1.0 + random.uniform(0, br), 0, 100) for g in grow]
                elif boss_growth_mode == 'random':
                    m = buff_growths.get('mean', None)
                    s = buff_growths.get('stddev', 10)
                    grow = [_randomize_stat(g, m, s, 0, 100) for g in grow]
                (cd.growthHP, cd.growthPow, cd.growthSkl,
                 cd.growthSpd, cd.growthDef, cd.growthRes,
                 cd.growthLck) = grow

            if boss_stat_mode:
                caps = [30, 25, 25, 25, 25, 25, 30]
                stats = [cd.baseHP, cd.basePow, cd.baseSkl, cd.baseSpd,
                         cd.baseDef, cd.baseRes, cd.baseLck]
                if isinstance(boss_stat_mode, (int, float)):
                    stats = [_scale_stat(s, float(boss_stat_mode), 0, cap) for s, cap in zip(stats, caps)]
                elif boss_stat_mode == 'random_buff':
                    br = buff_stats.get('buff_range', 0.3)
                    offsets = [random.uniform(0, br) for _ in range(7)]
                    stats = [_scale_stat(s, 1.0 + off, 0, cap) for s, off, cap in zip(stats, offsets, caps)]
                elif boss_stat_mode == 'random':
                    m = buff_stats.get('mean', None)
                    s = buff_stats.get('stddev', 3)
                    stats = [_randomize_stat(sv, m, s, 0, cap) for sv, cap in zip(stats, caps)]
                (cd.baseHP, cd.basePow, cd.baseSkl, cd.baseSpd,
                 cd.baseDef, cd.baseRes, cd.baseLck) = stats

            if boss_max_ranks:
                jd = ClassData(rom, cd.jidDefault)
                new_ranks = list(cd.baseWexp)
                changed = False
                for i in range(8):
                    if jd.baseWexp[i] > 0:
                        if new_ranks[i] < S_RANK_WEXP:
                            new_ranks[i] = S_RANK_WEXP
                            changed = True
                    else:
                        if new_ranks[i] != 0:
                            new_ranks[i] = 0
                            changed = True
                if changed:
                    cd.baseWexp = new_ranks

            cd.write(rom)

    # Phase B + C: UD array class overrides and items
    boss_final_classes = {}
    if rand_classes or rand_items:
        include_ballista = config.get('item_randomization', {}).get('include_ballista_items', False)
        if weapon_pools is None and rand_items:
            weapon_pools = build_weapon_pools(rom, include_ballista)

        if tqdm:
            pbar = tqdm(total=len(all_ud_offsets), desc="Enemy UD arrays (B/C)", unit="arr", leave=False)

        for ud_offset in all_ud_offsets:
            arr_pos = ud_offset
            while arr_pos + UNIT_DEF_SIZE <= len(rom.data):
                chunk = rom.data[arr_pos:arr_pos + UNIT_DEF_SIZE]
                if all(b == 0 for b in chunk):
                    break

                pid = chunk[0]
                if pid <= 34 or pid > 255 or pid == FINAL_BOSS_PID:
                    arr_pos += UNIT_DEF_SIZE
                    continue
                if pid in BOSS_PIDS and not include_bosses:
                    arr_pos += UNIT_DEF_SIZE
                    continue

                orig_jid = chunk[1]
                if orig_jid == 0:
                    cd = CharacterData(rom, pid)
                    orig_jid = cd.jidDefault
                if orig_jid == 0:
                    arr_pos += UNIT_DEF_SIZE
                    continue

                new_jid = orig_jid
                if rand_classes:
                    is_monster_orig = orig_jid in MONSTER_JIDS or orig_jid in EXTRA_MONSTER_JIDS
                    if not is_monster_orig or randomize_monster_classes:
                        orig_class = ClassData(rom, orig_jid)
                        is_promoted = bool(orig_class.attributes & CA_PROMOTED)
                        key = _move_group_key(orig_class.moveTable[0])
                        candidates = (promoted_groups if is_promoted else unpromoted_groups).get(key, [orig_jid])
                        new_jid = random.choice(candidates)

                new_class = ClassData(rom, new_jid)

                if rand_classes and new_jid != orig_jid:
                    rom.data[arr_pos + 1] = new_jid
                    if pid in BOSS_PIDS:
                        boss_final_classes[pid] = new_jid

                if rand_items:
                    if not randomize_monster_classes and new_jid in MONSTER_WEAPON_POOLS:
                        arr_pos += UNIT_DEF_SIZE
                        total += 1
                        continue

                    old_items = list(chunk[12:16])
                    new_items = list(old_items)

                    for slot_idx in range(4):
                        item_id = old_items[slot_idx]
                        if item_id == 0:
                            continue
                        item = ItemData(rom, item_id)
                        if not item.is_weapon():
                            continue
                        if new_class.baseWexp[item.weapon_type] > 0:
                            if not (item.attributes & 0x1000):
                                continue
                            allowed = CLASS_LOCKED_ITEM_RESTRICTIONS.get(item_id, set())
                            if new_class.jid in allowed:
                                continue

                        new_item_id = _pick_weapon_for_type(rom, weapon_pools, new_class.baseWexp, class_jid=new_class.jid)
                        if new_item_id is not None:
                            new_items[slot_idx] = new_item_id
                        else:
                            new_items[slot_idx] = 0

                    has_weapon = any(
                        ItemData(rom, it).is_weapon()
                        for it in new_items if it != 0
                    )
                    if not has_weapon:
                        new_item_id = _pick_weapon_for_type(rom, weapon_pools, new_class.baseWexp, class_jid=new_class.jid)
                        if new_item_id is not None:
                            for slot_idx in range(4):
                                if new_items[slot_idx] == 0:
                                    new_items[slot_idx] = new_item_id
                                    break

                    if new_items != old_items:
                        rom.data[arr_pos + 12 : arr_pos + 16] = bytes(new_items)

                total += 1
                arr_pos += UNIT_DEF_SIZE

            if tqdm: pbar.update(1)
        if tqdm: pbar.close()

    # Sync CharacterData for bosses whose UD array class diverged from Phase A.
    # Phase A and Phase B+C pick classes independently; weapon ranks were set
    # based on Phase A's pick but the game uses the UD array class in battle.
    if boss_final_classes and boss_max_ranks:
        for pid, final_jid in boss_final_classes.items():
            cd = CharacterData(rom, pid)
            if cd.jidDefault == final_jid:
                continue
            cd.jidDefault = final_jid
            jd = ClassData(rom, final_jid)
            new_ranks = list(cd.baseWexp)
            changed = False
            for i in range(8):
                if jd.baseWexp[i] > 0:
                    if new_ranks[i] < S_RANK_WEXP:
                        new_ranks[i] = S_RANK_WEXP
                        changed = True
                else:
                    if new_ranks[i] != 0:
                        new_ranks[i] = 0
                        changed = True
            if changed:
                cd.baseWexp = new_ranks
            cd.write(rom)

    return total


# ---------------------------------------------------------------------------
# Portrait palette generation
# ---------------------------------------------------------------------------

def _find_class_template_palette_id(rom: ROM, jid: int) -> int:
    """Find the default palette ID for a given class JID by scanning
    PaletteClassTable for any PID that maps that JID in slot 1,
    then returning the PaletteIndexTable entry for that PID's slot 1."""
    pal_cls_gba = _U32.unpack_from(rom.data, PALETTE_CLASS_TABLE_PTR_OFF)[0]
    pal_cls_off = pal_cls_gba - ROM_BASE
    pal_idx_gba = _U32.unpack_from(rom.data, PALETTE_INDEX_TABLE_PTR_OFF)[0]
    pal_idx_off = pal_idx_gba - ROM_BASE

    for pid in range(1, 256):
        cls_off = pal_cls_off + (pid - 1) * PALETTE_ENTRY_SIZE
        if cls_off + PALETTE_ENTRY_SIZE > len(rom.data):
            break
        if rom.data[cls_off + 1] == jid:
            idx_off = pal_idx_off + (pid - 1) * PALETTE_ENTRY_SIZE
            pid_idx = rom.data[idx_off + 1]
            if pid_idx != 0:
                return pid_idx
    # Fallback: try any non-zero slot
    for pid in range(1, 256):
        cls_off = pal_cls_off + (pid - 1) * PALETTE_ENTRY_SIZE
        if cls_off + PALETTE_ENTRY_SIZE > len(rom.data):
            break
        entry = list(rom.data[cls_off:cls_off + PALETTE_ENTRY_SIZE])
        if jid in entry:
            slot = entry.index(jid)
            idx_off = pal_idx_off + (pid - 1) * PALETTE_ENTRY_SIZE
            pid_idx = rom.data[idx_off + slot]
            if pid_idx != 0:
                return pid_idx
    return 0


def _get_palette_color(pal_set: bytearray, slot: int, color_idx: int) -> int:
    """Read a single color from a palette set at the given sub-slot and color index."""
    off = color_idx * PALETTE_INTERLEAVE_COUNT * 2 + slot * 2
    return pal_set[off] | (pal_set[off + 1] << 8)


def _generate_portrait_palette(rom: ROM, pid: int, source_pal_id: int,
                                new_jid: int) -> int:
    """Generate a new palette for PID by adapting their original palette
    colors to the target class template.  Writes the new palette data
    in-place at the original palette's ROM address, but ONLY if the new
    compressed data fits within the original compressed slot.  Uses 16
    portrait-mapped colors repeated across all 5 sub-palettes to keep
    LZ77 compressed size small.

    Returns the palette ID on success, or 0 on failure."""
    target_pal_id = _find_class_template_palette_id(rom, new_jid)
    if target_pal_id == 0:
        return 0

    source_set = read_palette_set(rom, source_pal_id)
    target_set = read_palette_set(rom, target_pal_id)
    if source_set is None or target_set is None:
        return 0

    target_player = deinterleave_palette(target_set, 0)

    # Build a map: for each target color, find the nearest source color
    new_player = bytearray(PALETTE_SUB_SIZE)
    for i in range(PALETTE_COLORS):
        tc_off = i * 2
        tc = target_player[tc_off] | (target_player[tc_off + 1] << 8)

        if i == 0 or tc == 0x7FFF:
            new_player[tc_off] = target_player[tc_off]
            new_player[tc_off + 1] = target_player[tc_off + 1]
            continue

        # Find closest source PLAYER color
        best_dist = float('inf')
        best_sc = tc
        for j in range(1, PALETTE_COLORS):
            sc = _get_palette_color(source_set, 0, j)
            if sc == 0x7FFF:
                continue
            d = color_distance(tc, sc)
            if d < best_dist:
                best_dist = d
                best_sc = sc

        new_player[tc_off] = best_sc & 0xFF
        new_player[tc_off + 1] = (best_sc >> 8) & 0xFF

    # Build 160-byte set: repeat the same 16 portrait colors across all
    # 5 sub-palettes.  Heavy repetition makes LZ77 compress small.
    new_set = interleave_palettes([bytes(new_player)] * PALETTE_INTERLEAVE_COUNT)

    # --- In-place overwrite at the original palette address ---
    table_off = rom_offset(PALETTE_TABLE_ADDR) + source_pal_id * 16
    orig_ptr = _U32.unpack_from(rom.data, table_off)[0]
    if not (ROM_BASE <= orig_ptr < ROM_BASE + 0x1000000):
        return 0
    data_off = orig_ptr - ROM_BASE

    orig_comp_size = lz77_compressed_size(rom.data, data_off)
    if orig_comp_size == 0:
        return 0

    new_compressed = lz77_compress(new_set)
    new_aligned = (len(new_compressed) + 3) & ~3

    if new_aligned > orig_comp_size:
        return 0  # new data too large to fit in original slot

    # Write compressed data + zero-pad to fill the original slot exactly
    rom.data[data_off:data_off + orig_comp_size] = (
        new_compressed + b'\x00' * (orig_comp_size - len(new_compressed)))

    return source_pal_id


def _update_palette_index(rom: ROM, pid: int, new_pal_id: int, slot: int = 1) -> None:
    """Update a single slot in the PaletteIndexTable for the given PID."""
    pal_idx_gba = _U32.unpack_from(rom.data, PALETTE_INDEX_TABLE_PTR_OFF)[0]
    pal_idx_off = pal_idx_gba - ROM_BASE
    off = pal_idx_off + (pid - 1) * PALETTE_ENTRY_SIZE + slot
    rom.data[off] = new_pal_id


# ---------------------------------------------------------------------------
# Palette mapping
# ---------------------------------------------------------------------------

def _build_base_promo_lookup(rom: ROM) -> Dict[int, list]:
    pal_cls_gba = _U32.unpack_from(rom.data, PALETTE_CLASS_TABLE_PTR_OFF)[0]
    pal_cls_off = pal_cls_gba - ROM_BASE

    lookup = {}
    for pid in range(1, 256):
        entry_off = pal_cls_off + (pid - 1) * PALETTE_ENTRY_SIZE
        if entry_off + PALETTE_ENTRY_SIZE > len(rom.data):
            break
        slots = list(rom.data[entry_off:entry_off + PALETTE_ENTRY_SIZE])
        s1, s2 = slots[1], slots[2]
        p34 = [j for j in slots[3:5] if j and j != 0]
        p56 = [j for j in slots[5:7] if j and j != 0]

        if s1 and s1 != 0:
            if p34:
                lookup.setdefault(s1, []).append(p34)
            if not s2 and p56:
                lookup.setdefault(s1, []).append(p34 + p56 if p34 else p56)

        if s2 and s2 != 0 and p56:
            lookup.setdefault(s2, []).append(p56)

    result = {}
    for base, promo_lists in lookup.items():
        if len(promo_lists) == 1:
            result[base] = promo_lists[0]
        else:
            result[base] = max(promo_lists, key=len)
    return result


def _build_trainee_chain_lookup(rom: ROM) -> Dict[int, list]:
    pal_cls_gba = _U32.unpack_from(rom.data, PALETTE_CLASS_TABLE_PTR_OFF)[0]
    pal_cls_off = pal_cls_gba - ROM_BASE

    lookup = {}
    for pid in range(1, 256):
        entry_off = pal_cls_off + (pid - 1) * PALETTE_ENTRY_SIZE
        if entry_off + PALETTE_ENTRY_SIZE > len(rom.data):
            break
        slots = list(rom.data[entry_off:entry_off + PALETTE_ENTRY_SIZE])
        trainee = slots[0]
        if trainee and trainee != 0:
            chain = [j for j in slots[1:7] if j and j != 0]
            if chain:
                lookup.setdefault(trainee, []).append(chain)
    result = {}
    for trainee, chain_lists in lookup.items():
        result[trainee] = max(chain_lists, key=lambda cl: chain_lists.count(cl))
    return result


def randomize_palette_mappings(rom: ROM, pid_set: Set[int],
                               original_jids: Dict[int, int],
                               config: dict = None) -> int:
    if not pid_set:
        return 0

    portrait_enabled = False
    if config:
        class_rules = config.get('class_randomization', {})
        portrait_enabled = class_rules.get('portrait_palettes', False)

    pal_class_gba = _U32.unpack_from(rom.data, PALETTE_CLASS_TABLE_PTR_OFF)[0]
    pal_class_off = pal_class_gba - ROM_BASE

    pal_idx_gba = _U32.unpack_from(rom.data, PALETTE_INDEX_TABLE_PTR_OFF)[0]
    pal_idx_off = pal_idx_gba - ROM_BASE

    base_promo_lookup = _build_base_promo_lookup(rom)
    trainee_lookup = _build_trainee_chain_lookup(rom)

    class_to_donors = {}
    for donor_pid in range(1, 256):
        idx_off = pal_idx_off + (donor_pid - 1) * PALETTE_ENTRY_SIZE
        if idx_off + PALETTE_ENTRY_SIZE > len(rom.data):
            break
        idx_entry = rom.data[idx_off:idx_off + PALETTE_ENTRY_SIZE]
        if all(b == 0 for b in idx_entry):
            continue
        cls_off = pal_class_off + (donor_pid - 1) * PALETTE_ENTRY_SIZE
        cls_entry = rom.data[cls_off:cls_off + PALETTE_ENTRY_SIZE]
        for b in cls_entry:
            if b != 0:
                class_to_donors.setdefault(b, []).append(donor_pid)

    # Build JID → template palette ID from ORIGINAL (unmodified) data
    jid_to_template_pal = {}
    for donor_pid in range(1, 256):
        cls_off = pal_class_off + (donor_pid - 1) * PALETTE_ENTRY_SIZE
        if cls_off + PALETTE_ENTRY_SIZE > len(rom.data):
            break
        cls_entry = rom.data[cls_off:cls_off + PALETTE_ENTRY_SIZE]
        for slot in range(7):
            jid = cls_entry[slot]
            if jid != 0:
                idx_off = pal_idx_off + (donor_pid - 1) * PALETTE_ENTRY_SIZE + slot
                pal_id = rom.data[idx_off]
                if pal_id != 0 and jid not in jid_to_template_pal:
                    jid_to_template_pal[jid] = pal_id

    count = 0
    for pid in sorted(pid_set):
        new_jid = CharacterData(rom, pid).jidDefault
        if new_jid == 0:
            continue
        orig_jid = original_jids.get(pid, 0)
        if orig_jid == 0:
            continue

        entry_off = pal_class_off + (pid - 1) * PALETTE_ENTRY_SIZE
        if entry_off + PALETTE_ENTRY_SIZE > len(rom.data):
            continue

        orig = list(rom.data[entry_off:entry_off + PALETTE_ENTRY_SIZE])
        new = list(orig)

        # Find-and-replace orig_jid with new_jid
        replaced_own = False
        for i in range(7):
            if new[i] == orig_jid:
                new[i] = new_jid
                replaced_own = True
        jd = ClassData(rom, new_jid)
        if not replaced_own:
            if new_jid in TRAINEE_JIDS:
                new[0] = new_jid
            elif jd.attributes & 0x100:
                new[3] = new_jid
            else:
                new[1] = new_jid

        # Remap promotion chain
        is_promoted = bool(jd.attributes & 0x100)

        if new_jid in TRAINEE_JIDS:
            chain = trainee_lookup.get(new_jid, [])
            n = len(chain)
            new[0] = new_jid
            for i in range(1, 7):
                new[i] = chain[i - 1] if i - 1 < n else 0
            base_jid = jd.jidPromotion
            if base_jid and base_jid != 0:
                if n < 1:
                    new[1] = base_jid
                if n < 2:
                    try:
                        base_jd = ClassData(rom, base_jid)
                        if base_jd.jidPromotion and base_jd.jidPromotion != 0:
                            new[3] = base_jd.jidPromotion
                    except Exception:
                        pass
                if n < 3:
                    try:
                        base_jd = ClassData(rom, base_jid)
                        if base_jd.jidPromotion and base_jd.jidPromotion != 0:
                            try:
                                p2 = ClassData(rom, base_jd.jidPromotion)
                                if p2.jidPromotion and p2.jidPromotion != 0:
                                    new[4] = p2.jidPromotion
                            except Exception:
                                pass
                    except Exception:
                        pass
        elif is_promoted:
            new[3] = new_jid
        else:
            promos = base_promo_lookup.get(new_jid, [])
            n = len(promos)
            for i in range(4):
                new[3 + i] = promos[i] if i < n else 0
            if n < 2 and jd.jidPromotion and jd.jidPromotion != 0:
                if n < 1:
                    new[3] = jd.jidPromotion
                try:
                    jd2 = ClassData(rom, jd.jidPromotion)
                    if jd2.jidPromotion and jd2.jidPromotion != 0:
                        new[4] = jd2.jidPromotion
                except Exception:
                    pass
            for i in range(5, 7):
                new[i] = 0

        # Tier-crossing
        try:
            orig_jd = ClassData(rom, orig_jid)
            if bool(orig_jd.attributes & 0x100) and new[3] != new_jid:
                promos_for_slot3 = new[3]
                new[3] = new_jid
                if promos_for_slot3 and promos_for_slot3 != 0:
                    for i in range(4, 7):
                        if new[i] == new_jid:
                            new[i] = 0
                    for i in range(4, 7):
                        if new[i] == 0:
                            new[i] = promos_for_slot3
                            break
        except Exception:
            pass

        changes = 0
        for i in range(7):
            if new[i] != orig[i]:
                rom.data[entry_off + i] = new[i]
                changes += 1
        count += changes

    # (C.5) Portrait-based palette generation
    if portrait_enabled:
        for pid in sorted(pid_set):
            new_jid = CharacterData(rom, pid).jidDefault
            if new_jid == 0:
                continue

            idx_off = pal_idx_off + (pid - 1) * PALETTE_ENTRY_SIZE
            if idx_off + PALETTE_ENTRY_SIZE > len(rom.data):
                continue
            idx_entry = list(rom.data[idx_off:idx_off + PALETTE_ENTRY_SIZE])
            if all(b == 0 for b in idx_entry):
                continue

            source_pal_id = idx_entry[1]
            if source_pal_id == 0:
                # Try other non-zero slots
                for s in range(7):
                    if idx_entry[s] != 0:
                        source_pal_id = idx_entry[s]
                        break
            if source_pal_id == 0:
                continue

            # Don't generate if the source palette IS the target class template
            target_pal_id = jid_to_template_pal.get(new_jid, 0)
            if target_pal_id == 0 or source_pal_id == target_pal_id:
                continue

            new_pal_id = _generate_portrait_palette(rom, pid, source_pal_id, new_jid)
            if new_pal_id > 0:
                count += 1
                _vprint(f"  Generated portrait palette for PID {pid} (pal 0x{new_pal_id:02X})")

    # (D) Borrow PaletteIndexTable for PIDs with all-zero entries
    for pid in sorted(pid_set):
        new_jid = CharacterData(rom, pid).jidDefault
        if new_jid == 0:
            continue

        idx_off = pal_idx_off + (pid - 1) * PALETTE_ENTRY_SIZE
        if idx_off + PALETTE_ENTRY_SIZE > len(rom.data):
            continue
        idx_entry = list(rom.data[idx_off:idx_off + PALETTE_ENTRY_SIZE])
        if not all(b == 0 for b in idx_entry):
            continue

        donors = class_to_donors.get(new_jid, [])
        if not donors:
            continue

        player_donors = [d for d in donors if d <= len(PLAYABLE_PLAYABLE_PIDS)]
        donor_pid = player_donors[0] if player_donors else donors[0]

        donor_idx_off = pal_idx_off + (donor_pid - 1) * PALETTE_ENTRY_SIZE
        donor_entry = rom.data[donor_idx_off:donor_idx_off + PALETTE_ENTRY_SIZE]

        for i in range(PALETTE_ENTRY_SIZE):
            if donor_entry[i] != idx_entry[i]:
                rom.data[idx_off + i] = donor_entry[i]
                count += 1

    return count


# ---------------------------------------------------------------------------
# Enforce tier constraints
# ---------------------------------------------------------------------------

def _enforce_pid_tiers(rom: ROM, config: dict) -> Set[int]:
    unprompted_pids = {1, 3, 4, 5, 6, 8, 9, 10, 12, 13, 14, 15, 16, 17, 19, 20, 25, 31}
    trainee_pids = {7, 18, 24}
    weapon_req_pids = {2, 13}

    promoted_jids, unpromoted_jids = _split_class_pool(rom)
    omit_jids = _parse_omit_classes(config)
    include_soldier = config.get('class_randomization', {}).get('include_soldier', False)

    promoted_jids -= omit_jids
    unpromoted_jids -= omit_jids
    if not include_soldier:
        unpromoted_jids.discard(JID.SOLDIER)

    unpromoted_list = sorted(unpromoted_jids)
    trainee_list = sorted(TRAINEE_JIDS - omit_jids)

    def _has_weapon(jid: int) -> bool:
        try:
            jd = ClassData(rom, jid)
            return any(jd.baseWexp[t] > 0 for t in range(8) if t != 4)
        except Exception:
            return False

    fixed = set()
    for pid in unprompted_pids:
        cd = CharacterData(rom, pid)
        jid = cd.jidDefault
        if jid in TRAINEE_JIDS or jid in promoted_jids:
            pool = [j for j in unpromoted_list if not (pid in weapon_req_pids and not _has_weapon(j))]
            new_jid = random.choice(pool) if pool else random.choice(unpromoted_list)
            cd.jidDefault = new_jid
            _adjust_weapon_ranks(cd, new_jid, rom)
            cd.write(rom)
            fixed.add(pid)

    for pid in trainee_pids:
        cd = CharacterData(rom, pid)
        jid = cd.jidDefault
        if jid not in TRAINEE_JIDS:
            if not trainee_list:
                continue
            new_jid = random.choice(trainee_list)
            cd.jidDefault = new_jid
            _adjust_weapon_ranks(cd, new_jid, rom)
            cd.write(rom)
            fixed.add(pid)

    for pid in weapon_req_pids:
        cd = CharacterData(rom, pid)
        jid = cd.jidDefault
        if not _has_weapon(jid):
            if pid in unprompted_pids:
                pool = [j for j in unpromoted_list if _has_weapon(j)]
            else:
                pool = [j for j in unpromoted_list + list(promoted_jids) if _has_weapon(j)]
            if pool:
                new_jid = random.choice(pool)
                cd.jidDefault = new_jid
                _adjust_weapon_ranks(cd, new_jid, rom)
                cd.write(rom)
                fixed.add(pid)

    return fixed


# ---------------------------------------------------------------------------
# Cutscene combat weapon guarantee
# ---------------------------------------------------------------------------

def _ensure_chapter_combat_weapons(rom: ROM, config: dict,
                                    weapon_pools: dict) -> int:
    combat_types = {0, 1, 2, 3, 5, 6, 7}
    data = rom.data
    asset_off = CHAPTER_ASSET_TABLE - ROM_BASE
    fixed = 0

    # Prologue cutscene
    cutscene_off = rom_offset(0x088B3F68)
    fixed += _patch_ud_combat_weapons(rom, cutscene_off, {2}, weapon_pools, combat_types)

    targets = {0: {2}, 4: {2, 13}}
    seen_arrays = set()

    for ch, pids in targets.items():
        ch_off = (CHAPTER_DATA_TABLE - ROM_BASE) + ch * CHAPTER_INFO_SIZE
        map_event_data_id = data[ch_off + 0x74]
        event_data_ptr = _U32.unpack_from(data, asset_off + map_event_data_id * 4)[0]
        event_data_off = event_data_ptr - ROM_BASE

        gmap_event_id = data[ch_off + 0x75]
        gmap_ptr = _U32.unpack_from(data, asset_off + gmap_event_id * 4)[0]
        gmap_off = gmap_ptr - ROM_BASE

        for off in range(0, 0x400, 4):
            val = _U32.unpack_from(data, event_data_off + off)[0]
            if val in seen_arrays:
                continue
            ud_offset = val - ROM_BASE
            if _ud_array_at_lenient(data, ud_offset, len(data)) > 0:
                seen_arrays.add(val)
                fixed += _patch_ud_combat_weapons(rom, ud_offset, pids, weapon_pools, combat_types)

        for off in range(0, 0x200, 4):
            val = _U32.unpack_from(data, gmap_off + off)[0]
            if val in seen_arrays:
                continue
            ud_offset = val - ROM_BASE
            if _ud_array_at_lenient(data, ud_offset, len(data)) > 0:
                seen_arrays.add(val)
                fixed += _patch_ud_combat_weapons(rom, ud_offset, pids, weapon_pools, combat_types)

    return fixed


def _patch_ud_combat_weapons(rom: ROM, ud_offset: int, pids: Set[int],
                              weapon_pools: dict, combat_types: Set[int]) -> int:
    data = rom.data
    fixed = 0
    arr_pos = ud_offset

    while arr_pos + UNIT_DEF_SIZE <= len(data):
        chunk = data[arr_pos:arr_pos + UNIT_DEF_SIZE]
        if all(b == 0 for b in chunk):
            break
        char_idx = chunk[0]
        if char_idx not in pids:
            arr_pos += UNIT_DEF_SIZE
            continue

        cd = CharacterData(rom, char_idx)
        items = list(chunk[12:16])
        has_combat = False
        replace_slots = []

        for slot_idx in range(4):
            item_id = items[slot_idx]
            if item_id == 0:
                replace_slots.append(slot_idx)
                continue
            idd = ItemData(rom, item_id)
            if idd.is_weapon():
                if idd.weapon_type in combat_types and cd.baseWexp[idd.weapon_type] > 0:
                    has_combat = True
                    break
                replace_slots.append(slot_idx)

        if not has_combat and replace_slots:
            combat_ranks = [cd.baseWexp[t] if t != 4 else 0 for t in range(8)]
            new_id = _pick_weapon_for_type(rom, weapon_pools, combat_ranks, class_jid=cd.jidDefault)
            if new_id is None:
                combat_ranks = [1 if t != 4 else 0 for t in range(8)]
                new_id = _pick_weapon_for_type(rom, weapon_pools, combat_ranks, class_jid=cd.jidDefault)
            if new_id is not None:
                data[arr_pos + 12 + replace_slots[0]] = new_id
                fixed += 1

        arr_pos += UNIT_DEF_SIZE

    return fixed


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def _build_ud_to_chapters(rom: ROM) -> Dict[int, list]:
    data = rom.data
    asset_off = CHAPTER_ASSET_TABLE - ROM_BASE

    def is_ud_addr(addr: int) -> bool:
        if addr == 0 or addr < 0x088B0000 or addr >= 0x088D0000:
            return False
        o = addr - ROM_BASE
        if o + 20 > len(data):
            return False
        chunk = data[o:o+20]
        if all(b == 0 for b in chunk):
            return False
        ci, cj = chunk[0], chunk[1]
        return ci > 0 and ci <= 114 and cj <= 114

    script_to_uds = {}
    for pos in range(len(data) - 8):
        cmd = data[pos]
        if 0x40 <= cmd <= 0x43 and data[pos+1] == 0x2C:
            ptr = _U32.unpack_from(data, pos+4)[0]
            if 0x088B0000 <= ptr < 0x088D0000 and is_ud_addr(ptr):
                script_to_uds.setdefault(ROM_BASE + pos, set()).add(ptr)

    ud_to_scripts = {}
    for script_addr, ud_addrs in script_to_uds.items():
        for ua in ud_addrs:
            ud_to_scripts.setdefault(ua, []).append(script_addr)

    result = {}
    for ch in range(35):
        ch_off = (CHAPTER_DATA_TABLE - ROM_BASE) + ch * CHAPTER_INFO_SIZE
        map_event_data_id = data[ch_off + 0x74]
        event_data_ptr = _U32.unpack_from(data, asset_off + map_event_data_id * 4)[0]
        event_data_off = event_data_ptr - ROM_BASE

        gmap_event_id = data[ch_off + 0x75]
        gmap_ptr = _U32.unpack_from(data, asset_off + gmap_event_id * 4)[0]
        gmap_off = gmap_ptr - ROM_BASE

        chapter_name = CHAPTER_NAMES.get(ch, f'Ch{ch}')
        seen = set()

        for off in range(0, 0x400, 4):
            val = _U32.unpack_from(data, event_data_off + off)[0]
            if is_ud_addr(val) and val not in seen:
                seen.add(val)
                result.setdefault(val - ROM_BASE, []).append(chapter_name)

        for off in range(0, 0x400, 4):
            val = _U32.unpack_from(data, event_data_off + off)[0]
            if 0x089E0000 <= val < 0x08A00000 and val in script_to_uds:
                for ud_addr in script_to_uds[val]:
                    if is_ud_addr(ud_addr) and ud_addr not in seen:
                        seen.add(ud_addr)
                        result.setdefault(ud_addr - ROM_BASE, []).append(chapter_name)

        for off in range(0, 0x200, 4):
            val = _U32.unpack_from(data, gmap_off + off)[0]
            if is_ud_addr(val) and val not in seen:
                seen.add(val)
                result.setdefault(val - ROM_BASE, []).append(chapter_name)

    return result


def _find_chapters_for_gba_addr(rom: ROM, gba_addr: int) -> List[str]:
    data = rom.data
    asset_off = CHAPTER_ASSET_TABLE - ROM_BASE

    ranges = []
    for ch in range(35):
        ch_off = (CHAPTER_DATA_TABLE - ROM_BASE) + ch * CHAPTER_INFO_SIZE
        map_event_data_id = data[ch_off + 0x74]
        event_data_ptr = _U32.unpack_from(data, asset_off + map_event_data_id * 4)[0]
        if event_data_ptr == 0:
            continue
        name = CHAPTER_NAMES.get(ch, f'Ch{ch}')
        ranges.append((event_data_ptr, ch, name))

    ranges.sort()
    result = set()
    for i, (ptr, ch, name) in enumerate(ranges):
        end = ranges[i+1][0] if i+1 < len(ranges) else ptr + 0x400
        if ptr <= gba_addr < end:
            result.add(name)
    return sorted(result)


def _write_report(orig_data: bytearray, rom: ROM, config: dict,
                  seed: Optional[int], output_path: Optional[str]) -> None:
    data = rom.data

    if output_path and output_path.lower().endswith('.gba'):
        txt_path = output_path[:-4] + '.txt'
    else:
        base = output_path.rsplit('.', 1)[0] if output_path else 'output'
        txt_path = base + '.txt'

    lines = []
    lines.append('=== FE8 Randomizer Report ===')
    lines.append(f'Seed: {seed}')
    lines.append('')

    lines.append('=== Class Changes ===')
    class_changed = 0
    for pid in sorted(PLAYABLE_PLAYABLE_PIDS):
        orig_cd = CharacterData.__new__(CharacterData)
        orig_raw = orig_data[rom_offset(CHARACTER_TABLE_ADDR) + (pid - 1) * PINFO_SIZE:][:PINFO_SIZE]
        orig_cd.jidDefault = orig_raw[5]

        mod_cd = CharacterData(rom, pid)
        if orig_cd.jidDefault != mod_cd.jidDefault:
            pid_name = PID(pid).name if pid in PID._value2member_map_ else f'PID{pid}'
            old_jid_name = JID(orig_cd.jidDefault).name if orig_cd.jidDefault in JID._value2member_map_ else f'JID{orig_cd.jidDefault}'
            new_jid_name = JID(mod_cd.jidDefault).name if mod_cd.jidDefault in JID._value2member_map_ else f'JID{mod_cd.jidDefault}'
            lines.append(f'  {pid_name}: {old_jid_name} -> {new_jid_name}')
            class_changed += 1
    if class_changed == 0:
        lines.append('  (none)')
    lines.append('')

    lines.append('=== Growth Rate Totals ===')
    growth_total_min = 999
    growth_total_max = 0
    growth_total_sum = 0
    growth_total_count = 0
    for pid in sorted(PLAYABLE_PLAYABLE_PIDS):
        cd = CharacterData(rom, pid)
        total = (cd.growthHP + cd.growthPow + cd.growthSkl + cd.growthSpd
                 + cd.growthDef + cd.growthRes + cd.growthLck)
        pid_name = PID(pid).name if pid in PID._value2member_map_ else f'PID{pid}'
        lines.append(f'  {pid_name:12s}: {total:3d}  (HP={cd.growthHP:3d} Pow={cd.growthPow:3d} '
                     f'Skl={cd.growthSkl:3d} Spd={cd.growthSpd:3d} '
                     f'Def={cd.growthDef:3d} Res={cd.growthRes:3d} Lck={cd.growthLck:3d})')
        if total < growth_total_min:
            growth_total_min = total
        if total > growth_total_max:
            growth_total_max = total
        growth_total_sum += total
        growth_total_count += 1
    if growth_total_count:
        avg = growth_total_sum / growth_total_count
        lines.append(f'  --- Range: {growth_total_min} - {growth_total_max}  Avg: {avg:.1f} ---')
    lines.append('')

    lines.append('=== Weapon Effect / Attribute Changes ===')
    eff_changed = 0
    for item_id in range(256):
        off = rom_offset(ITEM_TABLE_ADDR) + item_id * ITEM_DATA_SIZE
        if off + ITEM_DATA_SIZE > len(data):
            break
        stored_id = data[off + 6]
        if stored_id != item_id:
            continue
        item_name = ITEM_NAMES.get(item_id, f'0x{item_id:02X}')
        wep_type = data[off + 7]
        type_name = WEAPON_TYPE_NAMES[wep_type] if wep_type < 8 else f'type{wep_type}'

        # Weapon effect ID at offset 0x1F
        orig_eff = orig_data[off + 0x1F] if off < len(orig_data) else 0
        mod_eff = data[off + 0x1F]
        eff_change = orig_eff != mod_eff

        # Brave/reaver attribute bits at offset 0x08
        orig_attrs = struct.unpack_from('<I', orig_data, off + 0x08)[0] if off + 4 < len(orig_data) else 0
        mod_attrs = struct.unpack_from('<I', data, off + 0x08)[0]
        brave_added = (mod_attrs & 0x20) and not (orig_attrs & 0x20)
        reaver_added = (mod_attrs & 0x100) and not (orig_attrs & 0x100)

        if eff_change or brave_added or reaver_added:
            parts = []
            if eff_change:
                from_name = EFFECT_NAMES.get(orig_eff, f'0x{orig_eff:02X}')
                to_name = EFFECT_NAMES.get(mod_eff, f'0x{mod_eff:02X}')
                parts.append(f'effect: {from_name} -> {to_name}')
            if brave_added:
                parts.append('+BRAVE')
            if reaver_added:
                parts.append('+REAVER')
            lines.append(f'  {item_name} ({type_name}): {", ".join(parts)}')
            eff_changed += 1
    if eff_changed == 0:
        lines.append('  (none)')
    lines.append('')

    lines.append('=== GiveItem Event Changes ===')
    ev_changed = 0
    for write_offset, item_id, pack_fmt in _scan_giveitem_events(data, len(data)):
        if write_offset + 4 <= len(orig_data):
            orig_item = struct.unpack_from(pack_fmt, orig_data, write_offset)[0]
            mod_item = struct.unpack_from(pack_fmt, data, write_offset)[0]
            if orig_item != mod_item:
                gba_addr = ROM_BASE + write_offset
                chapters = _find_chapters_for_gba_addr(rom, gba_addr)
                ch_label = ', '.join(chapters) if chapters else 'Unknown'
                orig_name = ITEM_NAMES.get(orig_item, f'0x{orig_item:02X}')
                mod_name = ITEM_NAMES.get(mod_item, f'0x{mod_item:02X}')
                lines.append(f'  [{ch_label}] {orig_name} -> {mod_name}')
                ev_changed += 1
    if ev_changed == 0:
        lines.append('  (none)')
    lines.append('')

    lines.append('=== Chest Item Changes ===')
    chest_changed = 0
    for write_offset, item_id, pack_fmt in _scan_chest_items(rom):
        if write_offset + 4 <= len(orig_data):
            orig_item = struct.unpack_from(pack_fmt, orig_data, write_offset)[0]
            mod_item = struct.unpack_from(pack_fmt, data, write_offset)[0]
            if orig_item != mod_item:
                gba_addr = ROM_BASE + write_offset
                chapters = _find_chapters_for_gba_addr(rom, gba_addr)
                ch_label = ', '.join(chapters) if chapters else 'Unknown'
                orig_name = ITEM_NAMES.get(orig_item, f'0x{orig_item:02X}')
                mod_name = ITEM_NAMES.get(mod_item, f'0x{mod_item:02X}')
                lines.append(f'  [{ch_label}] {orig_name} -> {mod_name}')
                chest_changed += 1
    if chest_changed == 0:
        lines.append('  (none)')
    lines.append('')

    report_text = '\n'.join(lines)
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(report_text)
    _vprint(f'Report written to {txt_path}')


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def apply_config(rom_path: str, config: dict, seed: int = None,
                 output_path: str = None, verbose: bool = False) -> str:
    global _VERBOSE
    _VERBOSE = verbose

    if seed is not None:
        random.seed(seed)
    elif 'seed' in config:
        random.seed(config['seed'])
    _vprint("Loading ROM...")
    rom = ROM(rom_path)

    if tqdm:
        _vprint("")

    original_data = bytearray(rom.data)

    # Preserve original support data (affinity + supportInfoPtr) per PID slot
    # so recruitment swaps don't change who supports whom.
    saved_support = {}
    for pid in range(1, 256):
        off = rom_offset(CHARACTER_TABLE_ADDR) + (pid - 1) * PINFO_SIZE
        if off + PINFO_SIZE > len(original_data):
            break
        affinity = original_data[off + 9]
        support_ptr = _U32.unpack_from(original_data, off + 0x2C)[0]
        saved_support[pid] = (affinity, support_ptr)

    recruit_rules = config.get('recruitment_randomization', {})
    recruit_enabled = recruit_rules.get('enabled', False)
    recruit_mode = recruit_rules.get('mode', 'pre')
    preserve_tier = recruit_rules.get('preserve_tier', True)

    # Cache scan results once
    data = rom.data
    rom_size = len(data)
    _vprint("Scanning ROM structures...")
    ud_arrays = _scan_ud_arrays(data, rom_size)
    ch_ud_arrays = _scan_chapter_ud_arrays(data, rom_size)
    giveitem_events = _scan_giveitem_events(data, rom_size)
    _vprint(f"  Found {len(ud_arrays)} UD array(s), {len(ch_ud_arrays)} chapter array(s), {len(giveitem_events)} GiveItem event(s)")

    include_ballista = config.get('item_randomization', {}).get('include_ballista_items', False)
    weapon_pools = build_weapon_pools(rom, include_ballista)

    modified_pids = set()

    if recruit_enabled and recruit_mode == 'pre':
        modified_pids |= randomize_recruitment_order(rom, config, preserve_tier)

    original_jids = {pid: CharacterData(rom, pid).jidDefault
                     for pid in range(1, 256) if CharacterData(rom, pid).jidDefault != 0}

    class_pids = randomize_class(rom, config)
    modified_pids |= class_pids
    trainee_patched = _update_trainee_promotion_table(rom, class_pids)
    if trainee_patched:
        _vprint(f"Updated {trainee_patched} trainee promotion table entr(y/ies)")
    randomize_growths(rom, config)
    randomize_base_stats(rom, config)

    if recruit_enabled and recruit_mode == 'post':
        modified_pids |= randomize_recruitment_order(rom, config, preserve_tier)

    enforced_pids = _enforce_pid_tiers(rom, config)
    if enforced_pids:
        modified_pids |= enforced_pids
        _vprint(f"Enforced class tier constraints for {len(enforced_pids)} unit(s)")

    synchronize_promotion_gains(rom)
    randomize_affinity(rom, config)
    randomize_weapon_stats(rom, config)
    randomize_weapon_effects(rom, config)

    randomize_promotion_items(rom, config, ud_arrays)

    patched = patch_unit_definitions(rom, modified_pids, ud_arrays)
    if patched:
        _vprint(f"Patched {patched} unit definition(s) to use new default classes")

    _fix_prf_weapon_types(rom, modified_pids)

    enemy_patched = randomize_enemies(rom, config, ud_arrays, ch_ud_arrays, weapon_pools)
    if enemy_patched:
        _vprint(f"Randomized {enemy_patched} generic enemy unit(s)")

    _sync_shared_pid_classes(rom)

    class_rules = config.get('class_randomization', {})
    palette_enabled = class_rules.get('palette_mapping', True)
    if palette_enabled:
        palette_pids = set(modified_pids)
        enemy_rules = config.get('enemy_randomization', {})
        include_bosses = enemy_rules.get('include_bosses', False)
        if enemy_rules.get('enabled', False):
            for pid in range(35, 256):
                if pid == FINAL_BOSS_PID:
                    continue
                if not include_bosses and pid in BOSS_PIDS:
                    continue
                palette_pids.add(pid)
        elif include_bosses:
            palette_pids |= BOSS_PIDS
        pal_count = randomize_palette_mappings(rom, palette_pids, original_jids, config)
        if pal_count:
            _vprint(f"Updated palette mappings for {pal_count} unit(s)")

    item_rules = config.get('item_randomization', {})
    mode = item_rules.get('mode', 'random')
    if mode == 'shuffle':
        shuffled = _shuffle_unit_items(rom, ud_arrays)
        if shuffled:
            _vprint(f"Shuffled {shuffled} item(s) across unit definitions")
    elif item_rules.get('enabled', True):
        item_patched = randomize_unit_items(rom, config, modified_pids, weapon_pools, ud_arrays)
        if item_patched:
            _vprint(f"Randomized items for {item_patched} unit definition(s)")

    if item_rules.get('randomize_events', False) and mode != 'shuffle':
        ev_patched = randomize_event_items(rom, config, modified_pids, weapon_pools)
        if ev_patched:
            _vprint(f"Randomized {ev_patched} event-given item(s)")

    loot_count = randomize_loot(rom, config, giveitem_events)
    if loot_count:
        mode_label = config.get('loot_randomization', {}).get('mode', 'random')
        _vprint(f"Randomized {loot_count} loot event(s) ({mode_label} mode)")

    chest_count = randomize_chest(rom, config)
    if chest_count:
        mode_label = config.get('loot_randomization', {}).get('mode', 'random')
        _vprint(f"Randomized {chest_count} chest item(s) ({mode_label} mode)")

    ch_fixed = _ensure_chapter_combat_weapons(rom, config, weapon_pools)
    if ch_fixed:
        _vprint(f"Fixed combat weapons for {ch_fixed} cutscene-critical unit(s) in ch0/ch4")

    # Verbose-only growth total summary
    if _VERBOSE:
        totals = []
        for pid in sorted(PLAYABLE_PLAYABLE_PIDS):
            cd = CharacterData(rom, pid)
            t = (cd.growthHP + cd.growthPow + cd.growthSkl + cd.growthSpd
                 + cd.growthDef + cd.growthRes + cd.growthLck)
            totals.append(t)
        if totals:
            pid_name = lambda p: PID(p).name if p in PID._value2member_map_ else f'PID{p}'
            best = max(totals)
            worst = min(totals)
            avg = sum(totals) / len(totals)
            best_pid = sorted(PLAYABLE_PLAYABLE_PIDS)[totals.index(best)]
            worst_pid = sorted(PLAYABLE_PLAYABLE_PIDS)[totals.index(worst)]
            print(f"Growth totals: min={worst} ({pid_name(worst_pid)}), "
                  f"max={best} ({pid_name(best_pid)}), avg={avg:.1f}")

    resolved_seed = seed if seed is not None else config.get('seed', None)
    _write_report(original_data, rom, config, resolved_seed, output_path)

    # Restore original support data so each PID slot keeps its original
    # support relationships and affinity regardless of randomization.
    for pid in range(1, 256):
        if pid not in saved_support:
            continue
        off = rom_offset(CHARACTER_TABLE_ADDR) + (pid - 1) * PINFO_SIZE
        if off + PINFO_SIZE > len(rom.data):
            break
        orig_affinity, orig_support_ptr = saved_support[pid]
        _U32.pack_into(rom.data, off + 0x2C, orig_support_ptr)
        rom.data[off + 9] = orig_affinity

    if output_path:
        out = output_path
    else:
        base = rom_path.rsplit('.', 1)
        if len(base) == 2:
            out = base[0] + '_randomized.' + base[1]
        else:
            out = rom_path + '_randomized.gba'
# -------------------------------------------------------------------------
    # --- Dynamic Range Adjustment for Story-Exclusive Weapons ---
    # -------------------------------------------------------------------------
    print("Adjusting exclusive weapon ranges based on randomized weapon types...")
    
    # Weapon IDs for the personal/sacred weapons
    EXCLUSIVE_WEAPONS = {
        0x09: "Rapier",
        0x78: "Reginleif",
        0x85: "Sieglinde",
        0x92: "Siegmund"
    }

    # Offsets inside the 36-byte (0x24) item structure
    TYPE_OFFSET = 0x07
    RANGE_OFFSET = 0x19

    # Resolve base offset for the item table in the ROM
    # Using 'rom_offset' helper if defined, otherwise falling back to ROM_BASE math
    try:
        item_table_base = rom_offset(ITEM_TABLE_ADDR)
    except NameError:
        item_table_base = ITEM_TABLE_ADDR - ROM_BASE

    for item_id, name in EXCLUSIVE_WEAPONS.items():
        # Calculate the starting ROM address of this item entry
        item_entry_offset = item_table_base + (item_id * ITEM_DATA_SIZE)
        
        # Read the current weapon type (Sword=0, Lance=1, Axe=2, Bow=3, Staff=4, Anima=5, Light=6, Dark=7)
        wpn_type = rom.data[item_entry_offset + TYPE_OFFSET]
        
        # Determine appropriate range based on the weapon type
        if wpn_type == 3:  # Bow
            # 2-2 Range
            min_rng = 2
            max_rng = 2
        elif wpn_type in (5, 6, 7):  # Anima, Light, Dark Magic
            # 1-2 Range
            min_rng = 1
            max_rng = 2
        elif wpn_type == 4:  # Staff
            # Staves typically default to 1-1 range or 1-Mag/2 (handled by staff effect),
            # but setting it to 1-1 base range keeps it clean.
            min_rng = 1
            max_rng = 1
        else:  # Swords, Lances, Axes, Claws, etc.
            # 1-1 Range
            min_rng = 1
            max_rng = 1

        # Encode: Max range in upper nibble, min range in lower nibble
        encoded_range = (min_rng << 4) | max_rng
        
        # Write the dynamic range byte back to the ROM
        rom.write_u8(item_entry_offset + RANGE_OFFSET, encoded_range)
        
        print(f"  -> {name} (ID: 0x{item_id:02X}) is Type {wpn_type}. Setting range to {min_rng}-{max_rng} (encoded: 0x{encoded_range:02X})")
    rom.save(out)
    return out
