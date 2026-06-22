import random
import struct
from fe8rom import ROM, CharacterData, ClassData, ItemData, PID, JID, CHARACTER_COUNT, CLASS_COUNT, UNIT_DEF_SIZE, ITEM_DATA_SIZE, WEAPON_TYPE_NAMES, DRAGONSTONE_ITEM_ID, VULNERARY_ITEM_ID, MONSTER_BLOCKED_ITEM_IDS, STORY_EXCLUSIVE_ITEM_IDS, rom_offset, ROM_BASE, ITEM_TABLE_ADDR, build_weapon_pools

PLAYABLE_PIDS = set(range(PID.EIRIKA, PID.TANA + 1))
PLAYABLE_PLAYABLE_PIDS = {
    PID.EIRIKA, PID.SETH, PID.GILLIAM, PID.FRANZ, PID.MOULDER,
    PID.VANESSA, PID.ROSS, PID.NEIMI, PID.COLM, PID.GARCIA,
    PID.INNES, PID.LUTE, PID.NATASHA, PID.CORMAG, PID.EPHRAIM,
    PID.FORDE, PID.KYLE, PID.AMELIA, PID.ARTUR, PID.GERIK,
    PID.TETHYS, PID.MARISA, PID.SALEH, PID.EWAN, PID.LARACHEL,
    PID.DOZLA, PID.RENNAC, PID.DUESSEL, PID.MYRRH, PID.KNOLL,
    PID.JOSHUA, PID.SYRENE, PID.TANA,
}

STANDARD_JIDS = {
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
}

MONSTER_JIDS = {
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
    JID.DEMON_KING, JID.FLEET,
    JID.PHANTOM,
}

CA_PROMOTED = 0x100  # bit 8 of class attributes

TRAINEE_PIDS = {PID.ROSS, PID.AMELIA, PID.EWAN}
TRAINEE_JIDS = {JID.JOURNEYMAN, JID.PUPIL, JID.RECRUIT}

MANAKETE_JIDS = {JID.MANAKETE, JID.MANAKETE_2, JID.MANAKETE_MYRRH}


def _adjust_weapon_ranks(cd, new_jid, rom):
    """Zero weapon ranks for types the new class can't use; use class base as floor."""
    jd = ClassData(rom, new_jid)
    for i in range(8):
        if jd.baseWexp[i] > 0:
            cd.baseWexp[i] = max(cd.baseWexp[i], jd.baseWexp[i])
        else:
            cd.baseWexp[i] = 0


def _split_class_pool(rom):
    """Separate STANDARD_JIDS into promoted and unpromoted sets using attribute bit 8.
    Excludes trainee classes from the general unpromoted pool."""
    promoted = set()
    unpromoted = set()
    for jid in STANDARD_JIDS:
        jd = ClassData(rom, jid)
        if jd.attributes & CA_PROMOTED:
            promoted.add(jid)
        elif jid not in TRAINEE_JIDS:
            unpromoted.add(jid)
    return promoted, unpromoted


def _split_characters_by_tier(rom):
    """Group playable characters by promoted/unpromoted based on original class."""
    promoted_chars = []
    unpromoted_chars = []
    for pid in sorted(PLAYABLE_PLAYABLE_PIDS):
        cd = CharacterData(rom, pid)
        original_jd = ClassData(rom, cd.jidDefault)
        if original_jd.attributes & CA_PROMOTED:
            promoted_chars.append(pid)
        else:
            unpromoted_chars.append(pid)
    return promoted_chars, unpromoted_chars


def _parse_omit_classes(config):
    """Convert omit_classes config list to a set of JID values."""
    omit = set()
    for name in config.get('class_randomization', {}).get('omit_classes', []):
        name = name.upper().strip()
        if hasattr(JID, name):
            omit.add(getattr(JID, name))
    return omit


def randomize_class(rom, config):
    rules = config.get('class_randomization', {})
    shuffle = rules.get('shuffle', True)
    preserve_base = rules.get('preserve_base', True)
    stat_scramble = rules.get('randomize_stats', False)

    modified_pids = set()
    omit_jids = _parse_omit_classes(config)

    if shuffle:
        promoted_jids, unpromoted_jids = _split_class_pool(rom)
        promoted_chars, unpromoted_chars = _split_characters_by_tier(rom)

        available_trainee = sorted(TRAINEE_JIDS - omit_jids)
        trainee_chars = sorted([p for p in unpromoted_chars if p in TRAINEE_PIDS])
        non_trainee_unpromoted = sorted([p for p in unpromoted_chars if p not in TRAINEE_PIDS])

        # Apply omit_jids to main pools
        promoted_jids -= omit_jids
        unpromoted_jids -= omit_jids

        # Shuffle trainees among trainee classes
        if trainee_chars and available_trainee:
            trainee_pool = list(available_trainee)
            random.shuffle(trainee_pool)
            for pid, new_jid in zip(trainee_chars, trainee_pool):
                cd = CharacterData(rom, pid)
                cd.jidDefault = new_jid
                _adjust_weapon_ranks(cd, new_jid, rom)
                cd.write(rom)
                modified_pids.add(pid)

        # Shuffle promoted characters
        if promoted_chars:
            pool_p = list(promoted_jids)
            random.shuffle(pool_p)
            for pid, new_jid in zip(promoted_chars, pool_p):
                cd = CharacterData(rom, pid)
                cd.jidDefault = new_jid
                _adjust_weapon_ranks(cd, new_jid, rom)
                cd.write(rom)
                modified_pids.add(pid)

        # Shuffle remaining unpromoted characters
        if non_trainee_unpromoted:
            pool_u = list(unpromoted_jids)
            random.shuffle(pool_u)
            for pid, new_jid in zip(non_trainee_unpromoted, pool_u):
                cd = CharacterData(rom, pid)
                cd.jidDefault = new_jid
                _adjust_weapon_ranks(cd, new_jid, rom)
                cd.write(rom)
                modified_pids.add(pid)

        # Pick one random character to be the Manakete
        if PLAYABLE_PLAYABLE_PIDS:
            manakete_pid = random.choice(sorted(PLAYABLE_PLAYABLE_PIDS))
            cd = CharacterData(rom, manakete_pid)
            cd.jidDefault = JID.MANAKETE_MYRRH
            _adjust_weapon_ranks(cd, JID.MANAKETE_MYRRH, rom)
            cd.write(rom)
            modified_pids.add(manakete_pid)

    if stat_scramble:
        cross_tier = rules.get('cross_tier_scramble', False)
        if cross_tier:
            groups = [list(STANDARD_JIDS)]
        else:
            prom, unpr = _split_class_pool(rom)
            groups = [sorted(prom), sorted(unpr), sorted(TRAINEE_JIDS)]

        for group in groups:
            if len(group) < 2:
                continue
            pairs = []
            for jid in group:
                jd = ClassData(rom, jid)
                stats = [jd.baseHP, jd.basePow, jd.baseSkl, jd.baseSpd,
                         jd.baseDef, jd.baseRes, jd.baseCon, jd.baseMov]
                if sum(stats[:6]) == 0:
                    continue
                if preserve_base:
                    pairs.append((jid, stats))
                else:
                    pairs.append((jid, [random.randint(0, 20) for _ in range(8)]))
            if len(pairs) < 2:
                continue
            shuffled_stats = [p[1] for p in pairs]
            random.shuffle(shuffled_stats)
            for (jid, _), stats in zip(pairs, shuffled_stats):
                jd = ClassData(rom, jid)
                (jd.baseHP, jd.basePow, jd.baseSkl, jd.baseSpd,
                 jd.baseDef, jd.baseRes, jd.baseCon, jd.baseMov) = stats
                jd.write(rom)

    return modified_pids


def _distribute_growth_pool(pool_total, min_g, max_g):
    weights = [random.random() for _ in range(7)]
    total_w = sum(weights)
    vals = [int(round(w * pool_total / total_w)) for w in weights]
    vals = [max(min_g, min(max_g, v)) for v in vals]
    return vals


def randomize_growths(rom, config):
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
        for jid in STANDARD_JIDS:
            jd = ClassData(rom, jid)
            growths = [jd.growthHP, jd.growthPow, jd.growthSkl,
                       jd.growthSpd, jd.growthDef, jd.growthRes,
                       jd.growthLck]
            if class_shuffle == 'shuffle':
                random.shuffle(growths)
            elif class_shuffle == 'random':
                growths = [_randomize_stat(g, mean, stddev, min_g, max_g) for g in growths]
            elif class_shuffle == 'pool':
                base_total = pool_total if pool_total is not None else sum(growths)
                growths = _distribute_growth_pool(base_total, min_g, max_g)
            (jd.growthHP, jd.growthPow, jd.growthSkl,
             jd.growthSpd, jd.growthDef, jd.growthRes,
             jd.growthLck) = growths
            jd.write(rom)


def _scale_stat(val, factor, min_val, max_val):
    s = int(round(val * factor))
    return max(min_val, min(max_val, s))


def _randomize_stat(orig, mean, stddev, lo, hi):
    if mean is None:
        center = orig
    else:
        center = mean
    val = int(round(random.gauss(center, stddev)))
    return max(lo, min(hi, val))


def randomize_base_stats(rom, config):
    rules = config.get('base_stat_randomization', {})
    char_enabled = rules.get('character', False)
    class_enabled = rules.get('class', False)
    mean = rules.get('mean', None)
    stddev = rules.get('stddev', 3)

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
            jd.baseCon = _scale_stat(jd.baseCon, factor, 1, 25)
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
            cd.write(rom)

    if isinstance(class_enabled, str) and class_enabled == 'shuffle':
        cross_tier = rules.get('cross_tier_scramble', False)
        if cross_tier:
            groups = [list(STANDARD_JIDS)]
        else:
            prom, unpr = _split_class_pool(rom)
            groups = [sorted(prom), sorted(unpr), sorted(TRAINEE_JIDS)]
        for group in groups:
            if len(group) < 2:
                continue
            pairs = []
            for jid in group:
                jd = ClassData(rom, jid)
                stats = [jd.baseHP, jd.basePow, jd.baseSkl, jd.baseSpd,
                         jd.baseDef, jd.baseRes]
                if sum(stats) == 0:
                    continue
                pairs.append((jid, stats))
            if len(pairs) < 2:
                continue
            shuffled = [p[1] for p in pairs]
            random.shuffle(shuffled)
            for (jid, _), stats in zip(pairs, shuffled):
                jd = ClassData(rom, jid)
                (jd.baseHP, jd.basePow, jd.baseSkl, jd.baseSpd,
                 jd.baseDef, jd.baseRes) = stats
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
            jd.baseCon = _randomize_stat(jd.baseCon, mean, stddev, 1, 25)
            jd.write(rom)


def randomize_affinity(rom, config):
    rules = config.get('affinity_randomization', {})
    if not rules.get('enabled', False):
        return
    affinities = list(range(1, 8))
    for pid in PLAYABLE_PLAYABLE_PIDS:
        cd = CharacterData(rom, pid)
        cd.affinity = random.choice(affinities)
        cd.write(rom)


# Event commands that reference a UD array via `?? 0x2C xx xx pointer`.
# LOAD1-4 (0x40-0x43) are the standard LOADUNIT commands.
# 0x54, 0x8C, 0xA8, 0xAA, 0xC4 also reference UD arrays in some event scripts.
_EVENT_CMDS_WITH_UD = (0x40, 0x41, 0x42, 0x43, 0x54, 0x8C, 0xA8, 0xAA, 0xC4)


def _ud_array_at(rom, offset):
    """Check if offset points to a valid UnitDefinition array. Returns entry count or 0."""
    pos = offset
    entries = 0
    while pos + UNIT_DEF_SIZE <= len(rom.data):
        chunk = rom.data[pos:pos + UNIT_DEF_SIZE]
        if all(b == 0 for b in chunk):
            return entries
        char_idx = chunk[0]
        class_idx = chunk[1]
        if char_idx > 200 or class_idx > 110:
            return 0
        pos += UNIT_DEF_SIZE
        entries += 1
        if entries > 100:
            return 0
    return 0


def _scan_ud_arrays(rom):
    """Yield (ud_offset, entry_count) for every UD array referenced by event commands."""
    data = rom.data
    rom_size = len(data)
    for cmd_lo in _EVENT_CMDS_WITH_UD:
        pattern = bytes([cmd_lo, 0x2C])
        pos = 0
        while True:
            pos = data.find(pattern, pos)
            if pos == -1 or pos + 8 > rom_size:
                break
            ptr = struct.unpack_from('<I', data, pos + 4)[0]
            if not (0x08000000 <= ptr < ROM_BASE + rom_size and ptr % 4 == 0 and ptr >= 0x08800000):
                pos += 1
                continue
            ud_offset = ptr - ROM_BASE
            count = _ud_array_at(rom, ud_offset)
            if count > 0:
                yield ud_offset, count
            pos += 1


def patch_unit_definitions(rom, modified_pids):
    """Scan ROM for event commands referencing UnitDefinition arrays and patch
    any class override so the unit uses jidDefault (classIndex = 0)."""
    if not modified_pids:
        return 0

    total_patched = 0
    for ud_offset, _ in _scan_ud_arrays(rom):
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


def _pick_weapon_for_type(rom, weapon_pools, char_ranks):
    """Pick a random weapon from usable weapon types, respecting max rank."""
    candidates = []
    for t in range(8):
        if char_ranks[t] == 0 or not weapon_pools[t]:
            continue
        max_rank = char_ranks[t]
        for item_id, rank in weapon_pools[t]:
            if rank <= max_rank:
                candidates.append((t, item_id))
    if not candidates:
        return None
    return random.choice(candidates)[1]


def randomize_unit_items(rom, modified_pids):
    """Assign random weapons matching each unit's new class in all UnitDefinition arrays."""
    weapon_pools = build_weapon_pools(rom)

    data = rom.data
    total_patched = 0

    for ud_offset, _ in _scan_ud_arrays(rom):
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
            jd = ClassData(rom, cd.jidDefault)

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
                        continue
                    new_item_id = _pick_weapon_for_type(rom, weapon_pools, cd.baseWexp)
                    if new_item_id is not None:
                        new_items[slot_idx] = new_item_id

                has_weapon = any(
                    ItemData(rom, it).is_weapon()
                    for it in new_items if it != 0
                )
                if not has_weapon:
                    new_item_id = _pick_weapon_for_type(rom, weapon_pools, cd.baseWexp)
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


def randomize_weapon_stats(rom, config):
    rules = config.get('weapon_randomization', {})
    if not rules.get('enabled', False):
        return

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

    for item_id in range(256):
        off = rom_offset(ITEM_TABLE_ADDR) + item_id * ITEM_DATA_SIZE
        if off + ITEM_DATA_SIZE > len(rom.data):
            break
        raw = rom.data[off:off + ITEM_DATA_SIZE]
        stored_id = raw[6]
        wep_type = raw[7]

        if stored_id != item_id:
            continue
        if wep_type > 7:
            continue
        if item_id in MONSTER_BLOCKED_ITEM_IDS or item_id in STORY_EXCLUSIVE_ITEM_IDS:
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
        print(f"Randomized stats for {patched} weapon item(s)")


def randomize_weapon_effects(rom, config):
    rules = config.get('weapon_effects', {})
    chance = rules.get('enabled', False)
    if not chance:
        return

    effect_map = {
        'poison': 0x01,
        'nosferatu': 0x02,
        'eclipse': 0x03,
        'devil': 0x04,
        'stone': 0x05,
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

    if not effect_ids:
        return

    patched = 0
    for item_id in range(256):
        off = rom_offset(ITEM_TABLE_ADDR) + item_id * ITEM_DATA_SIZE
        if off + ITEM_DATA_SIZE > len(rom.data):
            break
        raw = rom.data[off:off + ITEM_DATA_SIZE]
        stored_id = raw[6]
        wep_type = raw[7]

        if stored_id != item_id:
            continue
        if wep_type > 7:
            continue
        if item_id in MONSTER_BLOCKED_ITEM_IDS or item_id in STORY_EXCLUSIVE_ITEM_IDS:
            continue
        if raw[0x14] == 0:
            continue

        if random.randint(1, 100) <= chance:
            eff = random.choices(effect_ids, weights=weights, k=1)[0]
            rom.write_u8(off + 0x1F, eff)
            patched += 1

    if patched:
        print(f"Applied weapon effects to {patched} item(s)")


def apply_config(rom_path, config, seed=None, output_path=None):
    if seed is not None:
        random.seed(seed)
    elif 'seed' in config:
        random.seed(config['seed'])
    rom = ROM(rom_path)

    modified_pids = randomize_class(rom, config)
    randomize_growths(rom, config)
    randomize_base_stats(rom, config)
    randomize_affinity(rom, config)
    randomize_weapon_stats(rom, config)
    randomize_weapon_effects(rom, config)

    patched = patch_unit_definitions(rom, modified_pids)
    if patched:
        print(f"Patched {patched} unit definition(s) to use new default classes")

    item_rules = config.get('item_randomization', {})
    if item_rules.get('enabled', True):
        item_patched = randomize_unit_items(rom, modified_pids)
        if item_patched:
            print(f"Randomized items for {item_patched} unit definition(s)")

    if output_path:
        out = output_path
    else:
        base = rom_path.rsplit('.', 1)
        if len(base) == 2:
            out = base[0] + '_randomized.' + base[1]
        else:
            out = rom_path + '_randomized.gba'
    rom.save(out)
    return out
