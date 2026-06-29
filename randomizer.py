import random
import struct
from fe8rom import ROM, CharacterData, ClassData, ItemData, PID, JID, CHARACTER_COUNT, CLASS_COUNT, UNIT_DEF_SIZE, ITEM_DATA_SIZE, WEAPON_TYPE_NAMES, DRAGONSTONE_ITEM_ID, VULNERARY_ITEM_ID, MONSTER_BLOCKED_ITEM_IDS, STORY_EXCLUSIVE_ITEM_IDS, PROMOTION_ITEM_IDS, MASTER_SEAL_ITEM_ID, PROMO_FUNCTION_TABLE_ADDR, PROMO_ITEM_TABLES, PROMO_CLASS_TABLE_BASE, PROMO_CLASS_FUNCTION_TABLE, rom_offset, ROM_BASE, ITEM_TABLE_ADDR, build_weapon_pools, CHARACTER_TABLE_ADDR, PINFO_SIZE, CHAPTER_DATA_TABLE, CHAPTER_INFO_SIZE, CHAPTER_ASSET_TABLE, ITEM_NAMES

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
    JID.MANAKETE_2,  # 0x3B
}

# Additional monster JIDs beyond the enum range (0x7C-0x7D = 124-125)
EXTRA_MONSTER_JIDS = {0x7C, 0x7D}

# JIDs that generic enemies should never be randomized into.
# Covers: Manakete (0x0E), Bard (0x46), Dancer (0x4D),
# Demon King (0x66), unused/civilian JIDs (0x67-0x7B),
# and special monster classes (0x50=FLEET, 0x51=PHANTOM).
ENEMY_EXCLUDED_JIDS = {
    JID.MANAKETE, JID.BARD, JID.DANCER,
} | {0x50, 0x51} | {0x66} | set(range(0x67, 0x7C))

# Boss PIDs — set of PIDs treated as unique boss units.
# Default covers PIDs 0x40–0x63 (64–99) and some stragglers 0x68–0x6D (104–109)
# matching the user's ROM layout.  Excluded by default unless include_bosses: true.
BOSS_PIDS = set(range(0x40, 0x64)) | {0x68, 0x6A, 0x6B, 0x6C, 0x6D}
# Final boss PID — always excluded from randomization regardless of settings.
FINAL_BOSS_PID = 0xBE

# Limited weapon pools for specific monster classes that can only use
# a narrow set of items rather than standard weapon pool picks.
MONSTER_WEAPON_POOLS = {
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

CA_PROMOTED = 0x100  # bit 8 of class attributes

# Male/female class pairs — same class with gendered variant.
# Both classes in each pair get the same promotion gains (max of the two values).
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

TRAINEE_PIDS = {PID.ROSS, PID.AMELIA, PID.EWAN}
TRAINEE_JIDS = {JID.JOURNEYMAN, JID.PUPIL, JID.RECRUIT}

MANAKETE_JIDS = {JID.MANAKETE, JID.MANAKETE_2, JID.MANAKETE_MYRRH}


def _adjust_weapon_ranks(cd, new_jid, rom):
    """Zero weapon ranks for types the new class can't use; use class base as floor.
    Transfers the character's highest lost weapon rank to an available type."""
    jd = ClassData(rom, new_jid)
    supported = [i for i in range(8) if jd.baseWexp[i] > 0]

    max_rank = max(cd.baseWexp)
    highest_lost = 0
    for i in range(8):
        if cd.baseWexp[i] == max_rank and jd.baseWexp[i] == 0 and max_rank > 0:
            highest_lost = max_rank
            break

    for i in range(8):
        if jd.baseWexp[i] > 0:
            cd.baseWexp[i] = max(cd.baseWexp[i], jd.baseWexp[i])
        else:
            cd.baseWexp[i] = 0

    if highest_lost > 0 and supported:
        target = min(supported, key=lambda i: cd.baseWexp[i])
        if cd.baseWexp[target] < highest_lost:
            cd.baseWexp[target] = highest_lost


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
    mode = rules.get('mode', 'shuffle')
    manakete_count = rules.get('manakete_count', 1)
    # Backward compat: old shuffle: false meant no changes at all
    if 'shuffle' in rules and not rules.get('shuffle', True):
        mode = 'none'
        manakete_count = 0
    omit_jids = _parse_omit_classes(config)
    include_soldier = rules.get('include_soldier', False)

    modified_pids = set()

    def _assign(pid, new_jid):
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
    # Soldier has no promotion path in vanilla, so also remove from promoted if somehow present
    promoted_jids.discard(JID.SOLDIER)

    if mode == 'shuffle':
        # Permute classes within each tier (no replacement)
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
        # Sampling with replacement — each character picks independently from their tier
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

    # Manakete assignment — overwrites whatever the mode assigned
    if manakete_count > 0 and PLAYABLE_PLAYABLE_PIDS:
        playable_all = sorted(PLAYABLE_PLAYABLE_PIDS)
        count = min(manakete_count, len(playable_all))
        for pid in random.sample(playable_all, count):
            _assign(pid, JID.MANAKETE_MYRRH)

    return modified_pids


def _distribute_growth_pool(pool_total, min_g, max_g):
    weights = [random.random() for _ in range(7)]
    total_w = sum(weights)
    vals = [int(round(w * pool_total / total_w)) for w in weights]
    vals = [max(min_g, min(max_g, v)) for v in vals]
    return vals


def _randomize_class_growths(rom, jid, class_shuffle, rules):
    """Apply one class growth mode to a single JID. Returns True if changed."""
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
            _scale_stat(g, 1.0 + random.uniform(-buff_range, buff_range), min_g, max_g)
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
        from fe8rom import CLASS_COUNT
        count = 0
        for jid in range(1, CLASS_COUNT + 1):
            if _randomize_class_growths(rom, jid, class_shuffle, rules):
                count += 1
        if count:
            print(f"Randomized class growth rates for {count} class(es)")


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


def _get_con_rules(rules, class_enabled):
    """Return (con_enabled, con_class_min, con_player_min, con_stddev) tuple.
    
    If the user explicitly provides a 'con' subsection, use its settings.
    Otherwise fall back to legacy behaviour (no Con for character random,
    Con with global stddev for class random).  'min' applies to class bases;
    'player_min' applies to player unit bases (defaults to 1).
    """
    if 'con' in rules:
        c = rules['con']
        return (c.get('enabled', True),
                c.get('min', 1),
                c.get('player_min', 1),
                c.get('stddev', rules.get('stddev', 3)))
    # legacy: character random preserves Con, class random randomizes it
    is_class_random = isinstance(class_enabled, str) and class_enabled == 'random'
    return (is_class_random, 1, 1, rules.get('stddev', 3))


def randomize_base_stats(rom, config):
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
            shuffled = [p[1] for p in pairs]
            random.shuffle(shuffled)
            for (jid, _), stats in zip(pairs, shuffled):
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


def synchronize_promotion_gains(rom):
    """Sync promotionHp/Pow/Skl/Spd/Def/Res between male/female class pairs.

    For each MALE_FEMALE_PAIRS entry, reads both classes' promotion stat
    bonuses, takes the higher value per stat, and writes the max back to
    both.  This ensures e.g. Hero and Hero_F grant the same promotion
    bonuses regardless of which gendered variant a unit promotes into.
    """
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
            best = max(vm, vf)
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
        print(f"Synchronized promotion gains for {changed} class pair(s)")


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
    # Reject arrays in compressed animation data (0x088D0000+)
    if offset + ROM_BASE >= 0x088D0000:
        return 0
    pos = offset
    entries = 0
    while pos + UNIT_DEF_SIZE <= len(rom.data):
        chunk = rom.data[pos:pos + UNIT_DEF_SIZE]
        if all(b == 0 for b in chunk):
            return entries
        char_idx = chunk[0]
        class_idx = chunk[1]
        if char_idx == 0 or char_idx > 114 or class_idx > 114:
            return 0
        pos += UNIT_DEF_SIZE
        entries += 1
        if entries > 100:
            return 0
    return 0


def _scan_ud_arrays(rom):
    """Yield (ud_offset, entry_count) for every UD array referenced by event commands.
    
    Uses _ud_array_at_lenient so arrays with PID > 114 (legitimate generic enemies)
    are not incorrectly rejected.
    """
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
            count = _ud_array_at_lenient(rom, ud_offset)
            if count > 0:
                yield ud_offset, count
            pos += 1


def _ud_array_at_lenient(rom, offset):
    """Lenient UD array validation for chapter data arrays.
    
    Unlike _ud_array_at, allows entries with pid > 114 (NPC/allied units
    that the game places alongside generic enemies in chapter data UD arrays).
    Only rejects arrays with pid=0 mid-array, class_idx > 127, or >100 entries.
    """
    if offset + ROM_BASE >= 0x088D0000:
        return 0
    pos = offset
    entries = 0
    while pos + UNIT_DEF_SIZE <= len(rom.data):
        chunk = rom.data[pos:pos + UNIT_DEF_SIZE]
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


def _scan_chapter_ud_arrays(rom):
    """Yield (ud_offset, entry_count) for UD arrays referenced by chapter data.
    
    Covers two sources per chapter:
      - Direct UD pointers embedded in event data (scanned up to 0x400 bytes)
      - GMap UD arrays (scanned up to 0x200 bytes)
    """
    data = rom.data
    asset_off = CHAPTER_ASSET_TABLE - ROM_BASE
    seen = set()

    for ch in range(35):
        ch_off = (CHAPTER_DATA_TABLE - ROM_BASE) + ch * CHAPTER_INFO_SIZE
        
        map_event_data_id = data[ch_off + 0x74]
        event_data_ptr = struct.unpack_from('<I', data, asset_off + map_event_data_id * 4)[0]
        event_data_off = event_data_ptr - ROM_BASE
        
        gmap_event_id = data[ch_off + 0x75]
        gmap_ptr = struct.unpack_from('<I', data, asset_off + gmap_event_id * 4)[0]
        gmap_off = gmap_ptr - ROM_BASE

        # Direct UD pointers in event data
        for off in range(0, 0x400, 4):
            val = struct.unpack_from('<I', data, event_data_off + off)[0]
            if val not in seen:
                ud_offset = val - ROM_BASE
                count = _ud_array_at_lenient(rom, ud_offset)
                if count > 0:
                    seen.add(val)
                    yield ud_offset, count

        # GMap UD arrays
        for off in range(0, 0x200, 4):
            val = struct.unpack_from('<I', data, gmap_off + off)[0]
            if val not in seen:
                ud_offset = val - ROM_BASE
                count = _ud_array_at_lenient(rom, ud_offset)
                if count > 0:
                    seen.add(val)
                    yield ud_offset, count


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


def _scan_giveitem_events(rom):
    """Yield (offset, item_id) for GiveItem commands in event data region.

    Searches for the 40-format GiveItem command:
      40 0A 00 00 40 1F 59 08 40 05 [slot] 00 [item_id_u32] [pid_field]
    at event data region 0x08800000-0x08A00000.
    """
    data = rom.data
    lo = rom_offset(0x08800000)
    hi = min(rom_offset(0x08A00000), len(data))
    hdr = b'\x40\x0A\x00\x00\x40\x1F\x59\x08\x40\x05'
    pos = lo
    seen = set()
    while True:
        pos = data.find(hdr, pos, hi)
        if pos == -1:
            break
        if pos + 20 > len(data):
            break
        item_id = struct.unpack_from('<I', data, pos + 12)[0]
        if 0 < item_id < 0xC0:
            if pos not in seen:
                seen.add(pos)
                yield pos, item_id
        pos += 1


def _scan_loot_events(rom):
    """Yield (offset, item_id) for GiveItem (40-format) commands in event data.

    Delegates to _scan_giveitem_events but filters out promotion items
    (including Master Seal placed by Phase 9), story-exclusive items,
    monster-blocked items, and dummy items — these are not loot.
    """
    loot_excluded = set(MONSTER_BLOCKED_ITEM_IDS) | set(STORY_EXCLUSIVE_ITEM_IDS)
    loot_excluded.update(PROMOTION_ITEM_IDS)
    loot_excluded.update({0x3D, 0x44, 0x8A})  # dummy items
    for offset, item_id in _scan_giveitem_events(rom):
        if item_id not in loot_excluded:
            yield offset, item_id


def _build_loot_pool(rom):
    """Build list of eligible item IDs for random loot replacement.

    Includes all items 0x01-0xBF that are not monster-blocked,
    story-exclusive, or dummy entries.
    """
    excluded = set(MONSTER_BLOCKED_ITEM_IDS) | set(STORY_EXCLUSIVE_ITEM_IDS)
    excluded.update({0x3D, 0x44, 0x8A})  # dummy items
    excluded.update(PROMOTION_ITEM_IDS)  # promotion items reserved for promo phase
    pool = []
    for item_id in range(1, 0xC0):
        if item_id not in excluded:
            pool.append(item_id)
    return pool


def _shuffle_loot(rom):
    """Collect all GiveItem loot item IDs, shuffle them, and redistribute."""
    items = list(_scan_loot_events(rom))
    if len(items) < 2:
        return 0
    shuffled_ids = [item_id for _, item_id in items]
    random.shuffle(shuffled_ids)
    for (offset, _), new_id in zip(items, shuffled_ids):
        cur = struct.unpack_from('<I', rom.data, offset + 12)[0]
        if cur != new_id:
            struct.pack_into('<I', rom.data, offset + 12, new_id)
    return len(items)


def _randomize_loot(rom):
    """Replace each GiveItem loot item with a random eligible replacement."""
    pool = _build_loot_pool(rom)
    if not pool:
        return 0
    patched = 0
    for offset, item_id in _scan_loot_events(rom):
        new_id = random.choice(pool)
        if new_id != item_id:
            struct.pack_into('<I', rom.data, offset + 12, new_id)
            patched += 1
    return patched


def randomize_loot(rom, config):
    """Randomize loot items from all GiveItem events.

    Two modes controlled by ``loot_randomization.mode``:
      * ``'shuffle'`` — collect all items, permute them, redistribute.
      * ``'random'`` — each item replaced with a random eligible item.
    """
    rules = config.get('loot_randomization', {})
    if not rules.get('enabled', False):
        return 0
    mode = rules.get('mode', 'random')
    if mode == 'shuffle':
        return _shuffle_loot(rom)
    return _randomize_loot(rom)


def randomize_event_items(rom, modified_pids):
    """Randomize items given via GiveItem event commands in chapter data.
    
    Replaces weapon items with random weapons from the pools. Non-weapon items
    (vulneraries, keys, promo items) are left as-is. Skips story-exclusive
    and monster-blocked items.
    """
    weapon_pools = build_weapon_pools(rom)
    data = rom.data
    patched = 0

    for offset, item_id in _scan_giveitem_events(rom):
        if item_id in MONSTER_BLOCKED_ITEM_IDS or item_id in STORY_EXCLUSIVE_ITEM_IDS:
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
            struct.pack_into('<I', data, offset + 12, new_item_id)
            patched += 1

    return patched


def _shuffle_unit_items(rom):
    """Shuffle all non-zero weapon items across UD arrays.
    
    Collects all weapon items from UD arrays, permutes them, and writes back.
    Non-weapon items and empty slots are preserved in place.
    Manakete inventories are excluded from shuffle (keep dragonstone).
    """
    data = rom.data
    items_by_entry = []

    for ud_offset, count in _scan_ud_arrays(rom):
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


def randomize_promotion_items(rom, config):
    """Make all promotion items behave as Master Seal, usable by all classes.
    Replaces items 0x62-0x68 in UD arrays with Master Seals."""
    rules = config.get('promotion_items', {})
    if not rules.get('enabled', True):
        return 0

    import struct
    data = rom.data
    total = 0

    master_seal_table_addr = PROMO_ITEM_TABLES[MASTER_SEAL_ITEM_ID]

    if rules.get('master_seal_universal', True):
        # Phase 1: Zero out item-specific permission tables for non-Master Seal items
        for item_id, table_addr in PROMO_ITEM_TABLES.items():
            if item_id == MASTER_SEAL_ITEM_ID:
                continue
            off = rom_offset(table_addr)
            data[off:off + 0x41] = bytes(0x41)
            total += 1

        # Phase 2: Fill ALL promotion item byte-per-class tables (0x41 bytes, classes 0-64).
        # Previously only filled Master Seal (0x88); now also fills items 0x64-0x68 so
        # FE Builder (which reads these tables directly) sees universal permissions.
        MAX_TABLE_CLS = 0x40
        from fe8rom import CharacterData, ClassData
        for item_id, table_addr in PROMO_ITEM_TABLES.items():
            if item_id not in PROMOTION_ITEM_IDS:
                continue
            tbl_off = rom_offset(table_addr)
            data[tbl_off:tbl_off + 0x41] = bytes([0x01] * 0x41)
            for cls in range(1, MAX_TABLE_CLS + 1):
                try:
                    cd = ClassData(rom, cls)
                    promo_jid = cd.jidPromotion
                    if promo_jid > 0 and promo_jid != cls:
                        byte_val = promo_jid + 1
                    else:
                        byte_val = 0x01
                except Exception:
                    byte_val = 0x01
                pos = tbl_off + cls
                if pos < len(data):
                    data[pos] = byte_val
        total += 1

        # Phase 3: Route items 0x64-0x68 to use 0x088ADF76 via function table
        # Entries 2-6 (items 0x64-0x68) keep their ORIGINAL handler addresses so
        # FE Builder can trace them to their handler literals (redirected in Phase 5
        # from old byte-per-class tables to 0x088ADF76).
        # Entries 0-1 (items 0x62-0x63, not promotion items) still redirect to
        # Master Seal stub for backward compatibility.
        ft_off = rom_offset(PROMO_FUNCTION_TABLE_ADDR)
        ms_stub_addr = struct.unpack_from('<I', data, ft_off + 7 * 4)[0]
        for i in range(7):
            item_id = 0x62 + i
            if item_id in PROMOTION_ITEM_IDS:
                # Keep original handler address — FE Builder traces it to its literal
                continue
            else:
                struct.pack_into('<I', data, ft_off + i * 4, ms_stub_addr)
            total += 1

        # Phase 4: Modify class-specific tables so Master Seal works for classes 0-19
        # Each class table is 0x41 (65) bytes, indexed by item_id
        # Class 20 is excluded because its table overflows into the pointer table at 0x0880D270
        for cls in range(20):
            table_addr = PROMO_CLASS_TABLE_BASE + cls * 0x41
            # Get the class's standard promotion JID from ClassData
            if cls == 0:
                # NONE class - no promotion
                promo_jid = 0
            else:
                try:
                    cd = ClassData(rom, cls)
                    promo_jid = cd.jidPromotion
                except Exception:
                    promo_jid = 0

            off = rom_offset(table_addr)
            byte_val = promo_jid + 1 if promo_jid > 0 and promo_jid != cls else 0x01
            for item_id in [MASTER_SEAL_ITEM_ID] + sorted(PROMOTION_ITEM_IDS):
                if item_id > 0x69:
                    continue
                data[off + item_id] = byte_val
            total += 1

        # Phase 4b: Redirect class 20's handler to use Master Seal's item-specific table
        # Class 20's class-specific table at 0x0880D22F cannot hold item_ids > 0x40 (overflows)
        # Instead, reroute to Master Seal's handler which reads from 0x0880CA0F[class_id]
        cf_off = rom_offset(PROMO_CLASS_FUNCTION_TABLE)
        struct.pack_into('<I', data, cf_off + 20 * 4, ms_stub_addr)
        total += 1

        # Phase 5: Redirect ALL use_eff handler literal pools to 0x088ADF76
        # The main use_eff=0x2D handler at 0x080293E8 loads its table from 0x08029408.
        # Sub-dispatch handlers at 0x080293C4 (use_eff 0x2E), 0x080293CC (use_eff 0x2F),
        # and 0x080293D4 (use_eff 0x20) each have their own literals for old lists:
        #   0x080293C8 → 0x088ADFA4 (item 0x98's old count-1 list)
        #   0x080293D0 → 0x088ADFA6 (item 0x99's old count-1 list)
        #   0x080293D8 → 0x088ADF96 (item 0x8A's old count-2 list)
        #   0x080293E0 → 0x088ADFA3 (unused old list)
        # Vanilla 0x08029408 → 0x088ADF9E (3-entry list: BRIGAND,PIRATE,THIEF).
        # All redirect to the 31-entry list at 0x088ADF76.
        ALL_UE_LITERALS = [
            0x080291D0,  # pre-dispatch 0x98 check (LDR at 0x080291CC) - dead, overwritten by next
            0x08029214,  # pre-dispatch 0x98/0x99 check (LDR at 0x080291D4) - actual value used
            0x08029398,  # sub-dispatch use_eff 0x19 literal (item 0x64 old handler)
            0x080293A0,  # sub-dispatch use_eff 0x1A literal (item 0x65 old handler)
            0x080293A8,  # sub-dispatch use_eff 0x1B literal (item 0x66 old handler)
            0x080293B0,  # sub-dispatch use_eff 0x1C literal (item 0x67 old handler)
            0x080293B8,  # sub-dispatch use_eff 0x1D literal (item 0x68 old handler)
            0x080293C8,  # use_eff 0x2E sub-dispatch literal (item 0x98 old handler)
            0x080293D0,  # use_eff 0x2F sub-dispatch literal (item 0x99 old handler)
            0x080293D8,  # use_eff 0x20 sub-dispatch literal (item 0x8A old handler)
            0x080293E0,  # use_eff 0x2E/0x2F shared sub-dispatch literal
            0x08029408,  # use_eff 0x2D main handler literal (Master Seal)
        ]
        for lit_addr in ALL_UE_LITERALS:
            lit_off = rom_offset(lit_addr)
            old_val = struct.unpack_from('<I', data, lit_off)[0]
            if old_val != 0x088ADF76:
                struct.pack_into('<I', data, lit_off, 0x088ADF76)
                total += 1
        print(f"  Redirected {len(ALL_UE_LITERALS)} use_eff handler literal(s) to 0x088ADF76")

        # Phase 5b: Replace invalid JIDs (0x7E=126, 0x7F=127) in the 31-entry list at 0x088ADF76
        # with lord class IDs so EPHRAIM_LORD and EIRIKA_LORD can use Master Seal.
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
            print(f"  Replaced {added} invalid JID(s) in use_eff list with lord classes")

        print("Applied Master Seal universal promotion")

    # Phase 6: Force use_eff=0x2D on ALL promotion items unconditionally
    # This ensures they all go through the 0x2D handler (checks 0x088ADF76),
    # regardless of the replace_distribution setting.
    ms_item_off = rom_offset(ITEM_TABLE_ADDR) + MASTER_SEAL_ITEM_ID * ITEM_DATA_SIZE
    ms_use_eff = data[ms_item_off + 0x1E]
    for item_id in PROMOTION_ITEM_IDS:
        dst_off = rom_offset(ITEM_TABLE_ADDR) + item_id * ITEM_DATA_SIZE
        data[dst_off + 0x1E] = ms_use_eff
        total += 1
    print(f"Set use_eff=0x{ms_use_eff:02X} for {len(PROMOTION_ITEM_IDS)} promotion items")

    # Phase 7: Replace promotion items in UD arrays
    if rules.get('replace_distribution', True):
        replaced = 0
        for ud_offset, _ in _scan_ud_arrays(rom):
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
            print(f"Replaced {replaced} promotion item(s) with Master Seal in unit definitions")

        # Phase 8: Copy Master Seal's item data to other promotion items
        # This makes items 0x62-0x68 look identical to Master Seal (same icon, name, effect)
        ms_item_off = rom_offset(ITEM_TABLE_ADDR) + MASTER_SEAL_ITEM_ID * ITEM_DATA_SIZE
        ms_item_data = data[ms_item_off:ms_item_off + ITEM_DATA_SIZE]

        for item_id in PROMOTION_ITEM_IDS:
            dst_off = rom_offset(ITEM_TABLE_ADDR) + item_id * ITEM_DATA_SIZE
            # Copy all bytes except number field (offset 6) which must stay as the correct item ID
            for byte_idx in range(ITEM_DATA_SIZE):
                if byte_idx == 6:
                    continue  # preserve original number/stored_id
                data[dst_off + byte_idx] = ms_item_data[byte_idx]
            # Set number field explicitly
            data[dst_off + 6] = item_id
            total += 1
        print(f"Copied Master Seal item data to {len(PROMOTION_ITEM_IDS)} promotion items")

        # Phase 9: Replace promotion items in GiveItem event commands
        # Scans ROM data section for 40-format GiveItem commands
        # and replaces any promotion item with Master Seal 0x88.
        ev_replaced = 0
        hdr = b'\x40\x0A\x00\x00\x40\x1F\x59\x08\x40\x05'
        lo = rom_offset(0x08800000)
        hi = rom_offset(0x08A00000)
        pos = lo
        while pos + 20 < hi:
            pos = data.find(hdr, pos, hi)
            if pos == -1:
                break
            item_id = struct.unpack_from('<I', data, pos + 12)[0]
            if item_id in PROMOTION_ITEM_IDS:
                if item_id != MASTER_SEAL_ITEM_ID:
                    struct.pack_into('<I', data, pos + 12, MASTER_SEAL_ITEM_ID)
                    ev_replaced += 1
            pos += 1
        if ev_replaced:
            total += 1
            print(f"Replaced {ev_replaced} promotion item(s) with Master Seal in GiveItem events")

    return total


def _parse_enemy_omit_classes(config):
    """Convert enemy_randomization.omit_classes config list to a set of JID values."""
    omit = set()
    for name in config.get('enemy_randomization', {}).get('omit_classes', []):
        name = name.upper().strip()
        if hasattr(JID, name):
            omit.add(getattr(JID, name))
    return omit


def _move_group_key(move_table_ptr):
    """Map a moveTable[0] pointer to a movement group key.
    
    Classes with the same movement key can be randomized into each other
    without terrain-traversal issues.  The user specifies the only pointers
    that deserve special grouping — everything else is standard foot.
    """
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


def randomize_enemies(rom, config):
    """Randomizes generic enemy classes and items.

    Operates on two levels:
      (A) CharacterData.jidDefault — changes the default class for every
          non-playable PID (PID > 34).  This affects placements where the
          UD entry has class_idx = 0.
      (B) UD array class override bytes — directly modifies the class byte
          in every UD entry whose PID is non-playable.  This covers the
          per-deployment overrides that FE Builder's Unit Placer shows.
      (C) UD array items — per-deployment weapon randomization replicating
          the player unit mode:random logic (pick any weapon the new class
          can actually use, rather than rank-matching).
    """
    rules = config.get('enemy_randomization', {})
    if not rules.get('enabled', False):
        return 0

    rand_classes = rules.get('randomize_classes', True)
    rand_items = rules.get('randomize_items', True)
    include_monsters = rules.get('include_monsters', False)
    include_bosses = rules.get('include_bosses', False)
    randomize_monster_classes = rules.get('randomize_monster_classes', False)
    omit_jids = _parse_enemy_omit_classes(config)

    # Determine which PIDs to process
    pid_range = range(35, 256)
    pid_range = [p for p in pid_range if p != FINAL_BOSS_PID]
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

    # Split by tier
    promoted_pool = set()
    unpromoted_pool = set()
    for jid in sorted(enemy_jids):
        jd = ClassData(rom, jid)
        if jd.attributes & CA_PROMOTED:
            promoted_pool.add(jid)
        else:
            unpromoted_pool.add(jid)

    # Group by movement category (not raw pointer) so foot classes share a pool
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

    # Collect all UD arrays once (used by both class and item phases)
    all_ud_offsets = set()
    for off, _ in _scan_ud_arrays(rom):
        all_ud_offsets.add(off)
    for off, _ in _scan_chapter_ud_arrays(rom):
        all_ud_offsets.add(off)

    total = 0

    # Phase A: Randomize CharacterData.jidDefault for non-playable PIDs
    if rand_classes:
        for pid in pid_range:
            cd = CharacterData(rom, pid)
            if cd.jidDefault == 0:
                continue

            orig_jid = cd.jidDefault

            # If monsters are excluded from class randomization and orig is a monster, keep it
            if not randomize_monster_classes and (orig_jid in MONSTER_JIDS or orig_jid in EXTRA_MONSTER_JIDS):
                continue

            orig_class = ClassData(rom, orig_jid)
            is_promoted = bool(orig_class.attributes & CA_PROMOTED)
            key = _move_group_key(orig_class.moveTable[0])

            candidates = (promoted_groups if is_promoted else unpromoted_groups).get(key, [orig_jid])
            new_jid = random.choice(candidates)

            if new_jid != orig_jid:
                rom.data[cd.offset + 5] = new_jid
                total += 1

    # Boss buffs: apply growth/stat/weapon-rank buffs to boss PIDs
    boss_buffs_rules = rules.get('boss_buffs', {})
    boss_growth_mode = boss_buffs_rules.get('growths', {}).get('mode', False)
    boss_stat_mode = boss_buffs_rules.get('base_stats', {}).get('mode', False)
    boss_max_ranks = boss_buffs_rules.get('max_weapon_ranks', True)
    boss_pids_in_scope = [p for p in pid_range if p in BOSS_PIDS]
    if boss_pids_in_scope and (boss_growth_mode or boss_stat_mode or boss_max_ranks):
        S_RANK_WEXP = 251
        buff_growths = boss_buffs_rules.get('growths', {})
        buff_stats = boss_buffs_rules.get('base_stats', {})
        for pid in boss_pids_in_scope:
            cd = CharacterData(rom, pid)

            # Growth rate buff
            if boss_growth_mode:
                grow = [cd.growthHP, cd.growthPow, cd.growthSkl,
                        cd.growthSpd, cd.growthDef, cd.growthRes,
                        cd.growthLck]
                if isinstance(boss_growth_mode, (int, float)):
                    grow = [_scale_stat(g, float(boss_growth_mode), 0, 100) for g in grow]
                elif boss_growth_mode == 'random_buff':
                    br = buff_growths.get('buff_range', 0.3)
                    grow = [_scale_stat(g, 1.0 + random.uniform(-br, br), 0, 100) for g in grow]
                elif boss_growth_mode == 'random':
                    m = buff_growths.get('mean', None)
                    s = buff_growths.get('stddev', 10)
                    grow = [_randomize_stat(g, m, s, 0, 100) for g in grow]
                (cd.growthHP, cd.growthPow, cd.growthSkl,
                 cd.growthSpd, cd.growthDef, cd.growthRes,
                 cd.growthLck) = grow

            # Base stat buff
            if boss_stat_mode:
                caps = [30, 25, 25, 25, 25, 25, 30]
                stats = [cd.baseHP, cd.basePow, cd.baseSkl, cd.baseSpd,
                         cd.baseDef, cd.baseRes, cd.baseLck]
                if isinstance(boss_stat_mode, (int, float)):
                    stats = [_scale_stat(s, float(boss_stat_mode), 0, cap) for s, cap in zip(stats, caps)]
                elif boss_stat_mode == 'random_buff':
                    br = buff_stats.get('buff_range', 0.3)
                    offsets = [random.uniform(-br, br) for _ in range(7)]
                    stats = [_scale_stat(s, 1.0 + off, 0, cap) for s, off, cap in zip(stats, offsets, caps)]
                elif boss_stat_mode == 'random':
                    m = buff_stats.get('mean', None)
                    s = buff_stats.get('stddev', 3)
                    stats = [_randomize_stat(sv, m, s, 0, cap) for sv, cap in zip(stats, caps)]
                (cd.baseHP, cd.basePow, cd.baseSkl, cd.baseSpd,
                 cd.baseDef, cd.baseRes, cd.baseLck) = stats

            # Max weapon ranks: S-rank for types new class can use, zero for others
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
    if rand_classes or rand_items:
        wep_pools = build_weapon_pools(rom) if rand_items else None

        for ud_offset in all_ud_offsets:
            arr_pos = ud_offset
            while arr_pos + UNIT_DEF_SIZE <= len(rom.data):
                chunk = rom.data[arr_pos:arr_pos + UNIT_DEF_SIZE]
                if all(b == 0 for b in chunk):
                    break

                pid = chunk[0]
                if pid <= 34 or pid > 255:
                    arr_pos += UNIT_DEF_SIZE
                    continue
                if pid == FINAL_BOSS_PID:  # final boss — never randomize
                    arr_pos += UNIT_DEF_SIZE
                    continue
                if pid in BOSS_PIDS and not include_bosses:
                    arr_pos += UNIT_DEF_SIZE
                    continue

                # Resolve original class (override byte first, then jidDefault)
                orig_jid = chunk[1]
                if orig_jid == 0:
                    cd = CharacterData(rom, pid)
                    orig_jid = cd.jidDefault
                if orig_jid == 0:
                    arr_pos += UNIT_DEF_SIZE
                    continue

                # Determine new class
                new_jid = orig_jid
                if rand_classes:
                    is_monster_orig = orig_jid in MONSTER_JIDS or orig_jid in EXTRA_MONSTER_JIDS
                    if not is_monster_orig or randomize_monster_classes:
                        orig_class = ClassData(rom, orig_jid)
                        is_promoted = bool(orig_class.attributes & CA_PROMOTED)
                        key = _move_group_key(orig_class.moveTable[0])
                        candidates = (promoted_groups if is_promoted else unpromoted_groups).get(key, [orig_jid])
                        new_jid = random.choice(candidates)
                    # else: keep monster class as-is

                new_class = ClassData(rom, new_jid)

                if rand_classes and new_jid != orig_jid:
                    rom.data[arr_pos + 1] = new_jid

                # Phase C: item randomization
                if rand_items:
                    # If monster classes aren't being randomized and this is a
                    # limited-pool monster, leave its original weapons untouched.
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

                        # Keep weapon if new class allows this weapon type (ignore rank)
                        if new_class.baseWexp[item.weapon_type] > 0:
                            continue

                        # Pick a random weapon the new class can actually use
                        new_item_id = _pick_weapon_for_type(rom, wep_pools, new_class.baseWexp)
                        if new_item_id is not None:
                            new_items[slot_idx] = new_item_id
                        else:
                            new_items[slot_idx] = 0

                    # Ensure at least one weapon exists
                    has_weapon = any(
                        ItemData(rom, it).is_weapon()
                        for it in new_items if it != 0
                    )
                    if not has_weapon:
                        new_item_id = _pick_weapon_for_type(rom, wep_pools, new_class.baseWexp)
                        if new_item_id is not None:
                            for slot_idx in range(4):
                                if new_items[slot_idx] == 0:
                                    new_items[slot_idx] = new_item_id
                                    break

                    if new_items != old_items:
                        rom.data[arr_pos + 12 : arr_pos + 16] = bytes(new_items)

                total += 1
                arr_pos += UNIT_DEF_SIZE

    return total


def _build_base_promo_lookup(rom):
    """Build class -> list of promotion JIDs from ALL PaletteClassTable entries.

    Scans slots 1-2 (base / alternative base) in every entry and correctly
    associates promotions:
      * Class in slot 1 → promos from slots 3-4 (primary branch), plus
        slots 5-6 when slot 2 is empty (no secondary base).
      * Class in slot 2 → promos from slots 5-6 (secondary branch).
    This captures branched-promotion data from trainee entries (e.g. the
    Journeyman_M alternative in slot 2 of Amelia's Recruit entry).
    """
    import struct
    from fe8rom import PALETTE_CLASS_TABLE_PTR_OFF, PALETTE_ENTRY_SIZE, ROM_BASE
    pal_cls_gba = struct.unpack('<I', rom.data[PALETTE_CLASS_TABLE_PTR_OFF:PALETTE_CLASS_TABLE_PTR_OFF + 4])[0]
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

        # Class at slot 1 (primary base) → slots 3-4 are its promos
        if s1 and s1 != 0:
            if p34:
                lookup.setdefault(s1, []).append(p34)
            # If slot 2 is empty, slots 5-6 also belong to slot 1
            if not s2 and p56:
                lookup.setdefault(s1, []).append(p34 + p56 if p34 else p56)

        # Class at slot 2 (secondary base) → slots 5-6 are its promos
        if s2 and s2 != 0 and p56:
            lookup.setdefault(s2, []).append(p56)

    result = {}
    for base, promo_lists in lookup.items():
        if len(promo_lists) == 1:
            result[base] = promo_lists[0]
        else:
            # Take the longest list (most complete promo data)
            result[base] = max(promo_lists, key=len)
    return result


def _build_trainee_chain_lookup(rom):
    """Build trainee_class -> full chain [base, promo, ...] from trainee PaletteClassTable entries."""
    import struct
    from fe8rom import PALETTE_CLASS_TABLE_PTR_OFF, PALETTE_ENTRY_SIZE, ROM_BASE
    pal_cls_gba = struct.unpack('<I', rom.data[PALETTE_CLASS_TABLE_PTR_OFF:PALETTE_CLASS_TABLE_PTR_OFF + 4])[0]
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


def randomize_palette_mappings(rom, pid_set, original_jids):
    """Update palette class table so randomized characters keep their custom palettes.

    Hybrid approach:
      (A) Find-and-replace the character's ORIGINAL class JID with their NEW
          class JID in all 7 slots of their PaletteClassTable entry.  This
          preserves any existing branched-promotion structure inherited from
          the old class.
      (B) For the promotion slots (3-6 for base classes, 0-6 for trainees),
          use a global lookup built from the ORIGINAL PaletteClassTable to
          fill in promotions appropriate for the NEW class.
      (C) The PaletteIndexTable (palette IDs) is left untouched — the
          character keeps their palette colours.
      (D) For characters with an all-zero PaletteIndexTable (e.g. Eirika,
          Ephraim), borrow a donor's PaletteIndexTable entry whose
          PaletteClassTable maps the same new class JID.

    Returns the number of byte changes made.
    """
    if not pid_set:
        return 0

    import struct
    from fe8rom import PALETTE_CLASS_TABLE_PTR_OFF, PALETTE_INDEX_TABLE_PTR_OFF, PALETTE_ENTRY_SIZE, ROM_BASE

    pal_class_gba = struct.unpack('<I', rom.data[PALETTE_CLASS_TABLE_PTR_OFF:PALETTE_CLASS_TABLE_PTR_OFF + 4])[0]
    pal_class_off = pal_class_gba - ROM_BASE

    pal_idx_gba = struct.unpack('<I', rom.data[PALETTE_INDEX_TABLE_PTR_OFF:PALETTE_INDEX_TABLE_PTR_OFF + 4])[0]
    pal_idx_off = pal_idx_gba - ROM_BASE

    base_promo_lookup = _build_base_promo_lookup(rom)
    trainee_lookup = _build_trainee_chain_lookup(rom)

    # Pre-build donor lookup (before PaletteClassTable gets modified)
    # Maps class JID -> [donor PIDs with non-zero PaletteIndexTable]
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

        # (A) Find-and-replace the character's own class JID in all slots
        replaced_own = False
        for i in range(7):
            if new[i] == orig_jid:
                new[i] = new_jid
                replaced_own = True
        # Fallback: if orig_jid wasn't found, write new_jid into the
        # appropriate slot based on the NEW class's tier
        jd = ClassData(rom, new_jid)
        if not replaced_own:
            if new_jid in TRAINEE_JIDS:
                new[0] = new_jid
            elif jd.attributes & 0x100:
                new[3] = new_jid
            else:
                new[1] = new_jid

        # (B) Remap promotion chain for the new class
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

        # (C) Tier-crossing
        try:
            orig_jd = ClassData(rom, orig_jid)
            orig_promoted = bool(orig_jd.attributes & 0x100)
            if orig_promoted and new[3] != new_jid:
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

    # (D) Borrow PaletteIndexTable entries for PIDs with all-zero entries
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

        # Prefer player PIDs (1-34) over generic enemies for more natural colors
        player_donors = [d for d in donors if d <= len(PLAYABLE_PLAYABLE_PIDS)]
        donor_pid = player_donors[0] if player_donors else donors[0]

        donor_idx_off = pal_idx_off + (donor_pid - 1) * PALETTE_ENTRY_SIZE
        donor_entry = rom.data[donor_idx_off:donor_idx_off + PALETTE_ENTRY_SIZE]

        for i in range(PALETTE_ENTRY_SIZE):
            if donor_entry[i] != idx_entry[i]:
                rom.data[idx_off + i] = donor_entry[i]
                count += 1

    return count


def _build_ud_to_chapters(rom):
    """Build mapping: UD array file offset -> list of chapter names."""
    data = rom.data
    asset_off = CHAPTER_ASSET_TABLE - ROM_BASE

    chapter_map = {
        0: 'Prologue', 1: 'Ch1: Escape!', 2: 'Ch2: The Protected',
        3: 'Ch3: Bandits of Borgo', 4: 'Ch4: Ancient Horrors',
        5: 'Ch5: Empire\'s Reach', 6: 'Ch5x: Unbroken Heart',
        7: 'Ch6: Victims of War', 8: 'Ch7: Waterside Renvall',
        9: 'Ch8: It\'s a Trap!', 10: 'Ch9: Distant Blade',
        11: 'Ch10: Revolt at Carcino', 12: 'Ch11: Creeping Darkness',
        13: 'Ch12: Village of Silence', 14: 'Ch13: Hamill Canyon',
        15: 'Ch14: Queen of White Dunes', 16: 'Ch15: Scorched Sand',
        17: 'Ch16: Ruled by Madness', 18: 'Ch17: River of Regrets (Eri)',
        19: 'Ch18: Two Faces of Evil (Eri)', 20: 'Ch19: Last Hope (Eri)',
        21: 'Ch20: Darkling Woods (Eri)', 22: 'Ch20: Darkling Woods (Eri)',
        23: 'Ch9: Fort Rigwald', 24: 'Ch10: Turning Traitor',
        25: 'Ch11: Phantom Ship', 26: 'Ch12: Landing at Taizel',
        27: 'Ch13: Fluorspar\'s Oath', 28: 'Ch14: Father and Son',
        29: 'Ch15: Scorched Sand (Eph)', 30: 'Ch16: Ruled by Maddness (Eph)',
        31: 'Ch17: River of Regrets (Eph)', 32: 'Ch18: Two Faces of Evil (Eph)',
        33: 'Ch19: Last Hope (Eph)', 34: 'Ch20: Darkling Woods (Eph)',
    }

    def is_ud_addr(addr):
        if addr == 0 or addr < 0x088B0000 or addr >= 0x088D0000:
            return False
        o = addr - ROM_BASE
        if o + 20 > len(data): return False
        chunk = data[o:o+20]
        if all(b == 0 for b in chunk): return False
        ci, cj = chunk[0], chunk[1]
        return ci > 0 and ci <= 114 and cj <= 114

    # Index LOAD commands in event scripts
    script_to_uds = {}
    for pos in range(len(data) - 8):
        cmd = data[pos]
        if 0x40 <= cmd <= 0x43 and data[pos+1] == 0x2C:
            ptr = struct.unpack_from('<I', data, pos+4)[0]
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

        event_data_ptr = struct.unpack_from('<I', data, asset_off + map_event_data_id * 4)[0]
        event_data_off = event_data_ptr - ROM_BASE

        gmap_event_id = data[ch_off + 0x75]
        gmap_ptr = struct.unpack_from('<I', data, asset_off + gmap_event_id * 4)[0]
        gmap_off = gmap_ptr - ROM_BASE

        chapter_name = chapter_map.get(ch, f'Ch{ch}')

        seen = set()
        # Direct UD pointers in event data
        for off in range(0, 0x400, 4):
            val = struct.unpack_from('<I', data, event_data_off + off)[0]
            if is_ud_addr(val) and val not in seen:
                seen.add(val)
                result.setdefault(val - ROM_BASE, []).append(chapter_name)

        # LOAD-command referenced UDs from scripts in event data
        for off in range(0, 0x400, 4):
            val = struct.unpack_from('<I', data, event_data_off + off)[0]
            if 0x089E0000 <= val < 0x08A00000 and val in script_to_uds:
                for ud_addr in script_to_uds[val]:
                    if is_ud_addr(ud_addr) and ud_addr not in seen:
                        seen.add(ud_addr)
                        result.setdefault(ud_addr - ROM_BASE, []).append(chapter_name)

        # GMap UD arrays
        for off in range(0, 0x200, 4):
            val = struct.unpack_from('<I', data, gmap_off + off)[0]
            if is_ud_addr(val) and val not in seen:
                seen.add(val)
                result.setdefault(val - ROM_BASE, []).append(chapter_name)

    return result


def _find_chapters_for_gba_addr(rom, gba_addr):
    """Return list of chapter names whose event data range contains gba_addr."""
    data = rom.data
    asset_off = CHAPTER_ASSET_TABLE - ROM_BASE

    chapter_map = {
        0: 'Prologue', 1: 'Ch1: Escape!', 2: 'Ch2: The Protected',
        3: 'Ch3: Bandits of Borgo', 4: 'Ch4: Ancient Horrors',
        5: 'Ch5: Empire\'s Reach', 6: 'Ch5x: Unbroken Heart',
        7: 'Ch6: Victims of War', 8: 'Ch7: Waterside Renvall',
        9: 'Ch8: It\'s a Trap!', 10: 'Ch9: Distant Blade',
        11: 'Ch10: Revolt at Carcino', 12: 'Ch11: Creeping Darkness',
        13: 'Ch12: Village of Silence', 14: 'Ch13: Hamill Canyon',
        15: 'Ch14: Queen of White Dunes', 16: 'Ch15: Scorched Sand',
        17: 'Ch16: Ruled by Madness', 18: 'Ch17: River of Regrets (Eri)',
        19: 'Ch18: Two Faces of Evil (Eri)', 20: 'Ch19: Last Hope (Eri)',
        21: 'Ch20: Darkling Woods (Eri)', 22: 'Ch20: Darkling Woods (Eri)',
        23: 'Ch9: Fort Rigwald', 24: 'Ch10: Turning Traitor',
        25: 'Ch11: Phantom Ship', 26: 'Ch12: Landing at Taizel',
        27: 'Ch13: Fluorspar\'s Oath', 28: 'Ch14: Father and Son',
        29: 'Ch15: Scorched Sand (Eph)', 30: 'Ch16: Ruled by Maddness (Eph)',
        31: 'Ch17: River of Regrets (Eph)', 32: 'Ch18: Two Faces of Evil (Eph)',
        33: 'Ch19: Last Hope (Eph)', 34: 'Ch20: Darkling Woods (Eph)',
    }

    ranges = []
    for ch in range(35):
        ch_off = (CHAPTER_DATA_TABLE - ROM_BASE) + ch * CHAPTER_INFO_SIZE
        map_event_data_id = data[ch_off + 0x74]
        event_data_ptr = struct.unpack_from('<I', data, asset_off + map_event_data_id * 4)[0]
        if event_data_ptr == 0: continue
        name = chapter_map.get(ch, f'Ch{ch}')
        ranges.append((event_data_ptr, ch, name))

    ranges.sort()

    result = set()
    for i, (ptr, ch, name) in enumerate(ranges):
        end = ranges[i+1][0] if i+1 < len(ranges) else ptr + 0x400
        if ptr <= gba_addr < end:
            result.add(name)

    return sorted(result)


def _write_report(orig_data, rom, config, seed, output_path):
    """Write a .txt report of all randomization changes alongside the output ROM."""
    data = rom.data

    # Derive .txt path from output .gba path
    if output_path and output_path.lower().endswith('.gba'):
        txt_path = output_path[:-4] + '.txt'
    else:
        base = output_path.rsplit('.', 1)[0] if output_path else 'output'
        txt_path = base + '.txt'

    lines = []
    lines.append('=== FE8 Randomizer Report ===')
    lines.append(f'Seed: {seed}')
    lines.append('')

    # --- Class changes ---
    lines.append('=== Class Changes ===')
    class_changed = 0
    for pid in sorted(PLAYABLE_PLAYABLE_PIDS):
        orig_cd = CharacterData.__new__(CharacterData)
        orig_raw = orig_data[rom_offset(CHARACTER_TABLE_ADDR) + (pid - 1) * PINFO_SIZE:][:PINFO_SIZE]
        orig_cd.jidDefault = orig_raw[4]

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

    # --- Weapon effects ---
    effect_names = {0: '(none)', 1: 'Poison', 2: 'Nosferatu', 3: 'Eclipse', 4: 'Devil', 5: 'Stone'}
    lines.append('=== Weapon Effect Changes ===')
    eff_changed = 0
    for item_id in range(256):
        off = rom_offset(ITEM_TABLE_ADDR) + item_id * ITEM_DATA_SIZE
        if off + ITEM_DATA_SIZE > len(data): break
        stored_id = data[off + 6]
        if stored_id != item_id: continue
        orig_eff = orig_data[off + 0x1F] if off < len(orig_data) else 0
        mod_eff = data[off + 0x1F]
        if orig_eff != mod_eff:
            wep_type = data[off + 7]
            type_name = WEAPON_TYPE_NAMES[wep_type] if wep_type < 8 else f'type{wep_type}'
            from_name = effect_names.get(orig_eff, f'0x{orig_eff:02X}')
            to_name = effect_names.get(mod_eff, f'0x{mod_eff:02X}')
            item_name = ITEM_NAMES.get(item_id, f'0x{item_id:02X}')
            lines.append(f'  {item_name} ({type_name}): {from_name} -> {to_name}')
            eff_changed += 1
    if eff_changed == 0:
        lines.append('  (none)')
    lines.append('')

    # --- Event item swaps ---
    lines.append('=== Event Item Changes ===')
    ev_changed = 0
    for offset, item_id in _scan_giveitem_events(rom):
        if offset + 16 <= len(orig_data):
            orig_item = struct.unpack_from('<I', orig_data, offset + 12)[0]
            mod_item = struct.unpack_from('<I', data, offset + 12)[0]
            if orig_item != mod_item:
                gba_addr = ROM_BASE + offset
                chapters = _find_chapters_for_gba_addr(rom, gba_addr)
                ch_label = ', '.join(chapters) if chapters else 'Unknown'
                orig_name = ITEM_NAMES.get(orig_item, f'0x{orig_item:02X}')
                mod_name = ITEM_NAMES.get(mod_item, f'0x{mod_item:02X}')
                lines.append(f'  [{ch_label}] {orig_name} -> {mod_name}')
                ev_changed += 1
    if ev_changed == 0:
        lines.append('  (none)')
    lines.append('')

    # Write file
    report_text = '\n'.join(lines)
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(report_text)
    print(f'Report written to {txt_path}')


def apply_config(rom_path, config, seed=None, output_path=None):
    if seed is not None:
        random.seed(seed)
    elif 'seed' in config:
        random.seed(config['seed'])
    rom = ROM(rom_path)

    # Snapshot original data for report generation
    original_data = bytearray(rom.data)

    # Snapshot original class JIDs before any randomization (used by palette mapping)
    original_jids = {pid: CharacterData(rom, pid).jidDefault for pid in range(1, 256) if CharacterData(rom, pid).jidDefault != 0}

    modified_pids = randomize_class(rom, config)
    randomize_growths(rom, config)
    randomize_base_stats(rom, config)
    synchronize_promotion_gains(rom)
    randomize_affinity(rom, config)
    randomize_weapon_stats(rom, config)
    randomize_weapon_effects(rom, config)

    randomize_promotion_items(rom, config)

    patched = patch_unit_definitions(rom, modified_pids)
    if patched:
        print(f"Patched {patched} unit definition(s) to use new default classes")

    enemy_patched = randomize_enemies(rom, config)
    if enemy_patched:
        print(f"Randomized {enemy_patched} generic enemy unit(s)")

    # Update palette class table so characters keep custom palettes after class changes
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
        pal_count = randomize_palette_mappings(rom, palette_pids, original_jids)
        if pal_count:
            print(f"Updated palette mappings for {pal_count} unit(s)")

    item_rules = config.get('item_randomization', {})
    mode = item_rules.get('mode', 'random')
    if mode == 'shuffle':
        shuffled = _shuffle_unit_items(rom)
        if shuffled:
            print(f"Shuffled {shuffled} item(s) across unit definitions")
    elif item_rules.get('enabled', True):
        item_patched = randomize_unit_items(rom, modified_pids)
        if item_patched:
            print(f"Randomized items for {item_patched} unit definition(s)")

    if item_rules.get('randomize_events', False) and mode != 'shuffle':
        ev_patched = randomize_event_items(rom, modified_pids)
        if ev_patched:
            print(f"Randomized {ev_patched} event-given item(s)")

    loot_count = randomize_loot(rom, config)
    if loot_count:
        mode_label = config.get('loot_randomization', {}).get('mode', 'random')
        print(f"Randomized {loot_count} loot event(s) ({mode_label} mode)")

    resolved_seed = seed if seed is not None else config.get('seed', None)
    _write_report(original_data, rom, config, resolved_seed, output_path)

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
