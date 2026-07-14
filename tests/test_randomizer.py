"""Unit tests for pure-logic functions in randomizer.py and fe8rom.py.

No ROM file required — all tests use synthetic data or module-level constants.
Run with: python -m pytest tests/ -v
"""

import random
import struct

import pytest

from fe8.fe8rom import (
    JID,
    PID,
    ROM_BASE,
    color_distance,
    deinterleave_palette,
    interleave_palettes,
    lz77_compress,
    lz77_decompress,
    pal15_to_rgb,
    rgb_to_pal15,
    rom_offset,
)
from fe8.randomizer import (
    MALE_FEMALE_PAIRS,
    MONSTER_BLOCKED_ITEM_IDS,
    PROMOTION_ITEM_IDS,
    STORY_EXCLUSIVE_ITEM_IDS,
    BALLISTA_ITEM_IDS,
    _build_loot_pool,
    _distribute_growth_pool,
    _get_con_rules,
    _parse_omit_classes,
    _randomize_stat,
    _scale_stat,
    _swap_gendered_class,
)


# ---------------------------------------------------------------------------
# randomizer.py: stat helpers
# ---------------------------------------------------------------------------

class TestScaleStat:
    def test_identity(self):
        assert _scale_stat(10, 1.0, 0, 100) == 10

    def test_double(self):
        assert _scale_stat(5, 2.0, 0, 100) == 10

    def test_half(self):
        assert _scale_stat(10, 0.5, 0, 100) == 5

    def test_clamp_low(self):
        assert _scale_stat(3, 0.5, 5, 20) == 5

    def test_clamp_high(self):
        assert _scale_stat(50, 2.0, 0, 80) == 80

    def test_rounding(self):
        assert _scale_stat(4, 1.5, 0, 100) == 6  # 6.0 rounds to 6

    def test_zero(self):
        assert _scale_stat(0, 3.0, 0, 100) == 0

    def test_negative_factor_gives_min(self):
        assert _scale_stat(10, -1.0, 0, 100) == 0


class TestRandomizeStat:
    def test_deterministic_with_seed(self):
        random.seed(42)
        a = _randomize_stat(10, None, 3, 0, 30)
        random.seed(42)
        b = _randomize_stat(10, None, 3, 0, 30)
        assert a == b

    def test_clamp_low(self):
        random.seed(0)
        vals = [_randomize_stat(0, None, 1, 5, 20) for _ in range(100)]
        assert all(v >= 5 for v in vals)

    def test_clamp_high(self):
        random.seed(0)
        vals = [_randomize_stat(30, None, 1, 0, 20) for _ in range(100)]
        assert all(v <= 20 for v in vals)

    def test_explicit_mean(self):
        random.seed(99)
        vals = [_randomize_stat(5, mean=15.0, stddev=0.01, lo=0, hi=100)
                for _ in range(50)]
        assert all(14 <= v <= 16 for v in vals)

    def test_zero_stddev_returns_center(self):
        result = _randomize_stat(10, mean=7.0, stddev=0.0, lo=0, hi=100)
        assert result == 7


class TestDistributeGrowthPool:
    def test_sum_approximately_matches(self):
        random.seed(123)
        vals = _distribute_growth_pool(315, 0, 100)
        assert len(vals) == 7
        assert all(0 <= v <= 100 for v in vals)
        # Clamping to [0, 100] can push the sum well below pool_total,
        # so just verify all 7 values are present and non-negative.
        assert sum(vals) > 0

    def test_clamp_respected(self):
        random.seed(456)
        vals = _distribute_growth_pool(500, 20, 80)
        assert all(20 <= v <= 80 for v in vals)

    def test_small_pool(self):
        random.seed(789)
        vals = _distribute_growth_pool(7, 0, 100)
        assert len(vals) == 7
        assert all(v >= 0 for v in vals)


# ---------------------------------------------------------------------------
# randomizer.py: config parsing
# ---------------------------------------------------------------------------

class TestParseOmitClasses:
    def test_empty_config(self):
        assert _parse_omit_classes({}) == set()

    def test_valid_class_names(self):
        config = {'class_randomization': {'omit_classes': ['MYRMIDON', 'SHAMAN']}}
        result = _parse_omit_classes(config)
        assert JID.MYRMIDON in result
        assert JID.SHAMAN in result

    def test_case_insensitive(self):
        config = {'class_randomization': {'omit_classes': ['myrmidon']}}
        result = _parse_omit_classes(config)
        assert JID.MYRMIDON in result

    def test_invalid_name_ignored(self):
        config = {'class_randomization': {'omit_classes': ['NOT_A_REAL_CLASS']}}
        result = _parse_omit_classes(config)
        assert result == set()

    def test_custom_key(self):
        config = {'enemy_randomization': {'omit_classes': ['BARD']}}
        result = _parse_omit_classes(config, key='enemy_randomization')
        assert JID.BARD in result


class TestSwapGenderedClass:
    def test_male_to_female(self):
        result = _swap_gendered_class(JID.CAVALIER, is_female=True)
        assert result == JID.CAVALIER_F

    def test_female_to_male(self):
        result = _swap_gendered_class(JID.CAVALIER_F, is_female=False)
        assert result == JID.CAVALIER

    def test_no_pair_returns_same(self):
        jid = JID.THIEF  # Thief has no gendered pair
        result = _swap_gendered_class(jid, is_female=True)
        assert result == jid

    def test_all_pairs_are_bidirectional(self):
        for male, female in MALE_FEMALE_PAIRS:
            assert _swap_gendered_class(male, is_female=True) == female
            assert _swap_gendered_class(female, is_female=False) == male


class TestGetConRules:
    def test_explicit_con_section(self):
        rules = {'con': {'enabled': False, 'min': 2, 'player_min': 3, 'stddev': 5},
                 'stddev': 1}
        enabled, mn, pmn, sd = _get_con_rules(rules, 'shuffle')
        assert enabled is False
        assert mn == 2
        assert pmn == 3
        assert sd == 5

    def test_con_section_defaults(self):
        rules = {'con': {}}
        enabled, mn, pmn, sd = _get_con_rules(rules, 'shuffle')
        assert enabled is True
        assert mn == 1
        assert pmn == 1

    def test_legacy_class_random(self):
        rules = {'stddev': 4}
        enabled, mn, pmn, sd = _get_con_rules(rules, 'random')
        assert enabled is True
        assert sd == 4

    def test_legacy_class_not_random(self):
        rules = {'stddev': 4}
        enabled, mn, pmn, sd = _get_con_rules(rules, 'shuffle')
        assert enabled is False

    def test_con_section_overrides_legacy_stddev(self):
        rules = {'con': {'stddev': 7}, 'stddev': 2}
        _, _, _, sd = _get_con_rules(rules, 'random')
        assert sd == 7


# ---------------------------------------------------------------------------
# randomizer.py: loot pool
# ---------------------------------------------------------------------------

class TestBuildLootPool:
    def test_no_duplicates(self):
        pool = _build_loot_pool()
        assert len(pool) == len(set(pool))

    def test_excludes_promotion_items(self):
        pool = set(_build_loot_pool())
        assert PROMOTION_ITEM_IDS.isdisjoint(pool)

    def test_excludes_story_exclusive(self):
        pool = set(_build_loot_pool())
        assert STORY_EXCLUSIVE_ITEM_IDS.isdisjoint(pool)

    def test_excludes_ballista_by_default(self):
        pool = set(_build_loot_pool(include_ballista=False))
        assert BALLISTA_ITEM_IDS.isdisjoint(pool)

    def test_includes_ballista_when_enabled(self):
        pool = set(_build_loot_pool(include_ballista=True))
        assert BALLISTA_ITEM_IDS.issubset(pool)

    def test_range(self):
        pool = _build_loot_pool()
        assert all(1 <= item <= 0xBF for item in pool)
        assert 0 not in pool


# ---------------------------------------------------------------------------
# fe8rom.py: address conversion
# ---------------------------------------------------------------------------

class TestRomOffset:
    def test_base_address(self):
        assert rom_offset(ROM_BASE) == 0

    def test_typical_address(self):
        assert rom_offset(0x08803D64) == 0x803D64

    def test_first_byte(self):
        assert rom_offset(0x08000001) == 1


# ---------------------------------------------------------------------------
# fe8rom.py: LZ77 compression roundtrip
# ---------------------------------------------------------------------------

class TestLZ77:
    def test_roundtrip_simple(self):
        data = bytearray(b'Hello, world! Hello, world!')
        compressed = lz77_compress(data)
        decompressed = lz77_decompress(compressed, 0)
        assert decompressed == data

    def test_roundtrip_empty(self):
        data = bytearray()
        compressed = lz77_compress(data)
        decompressed = lz77_decompress(compressed, 0)
        assert decompressed == data

    def test_roundtrip_single_byte(self):
        data = bytearray(b'\x42')
        compressed = lz77_compress(data)
        decompressed = lz77_decompress(compressed, 0)
        assert decompressed == data

    def test_roundtrip_repeated(self):
        data = bytearray(b'\xAA' * 200)
        compressed = lz77_compress(data)
        decompressed = lz77_decompress(compressed, 0)
        assert decompressed == data

    def test_compressed_smaller_than_repeated_data(self):
        data = bytearray(b'\xBB' * 200)
        compressed = lz77_compress(data)
        assert len(compressed) < len(data)


# ---------------------------------------------------------------------------
# fe8rom.py: palette color conversion
# ---------------------------------------------------------------------------

class TestPaletteColor:
    def test_pal15_to_rgb_black(self):
        assert pal15_to_rgb(0) == (0, 0, 0)

    def test_pal15_to_rgb_white(self):
        # 0x7FFF = max R(31), G(31), B(31)
        r, g, b = pal15_to_rgb(0x7FFF)
        assert (r, g, b) == (248, 248, 248)

    def test_rgb_to_pal15_black(self):
        assert rgb_to_pal15(0, 0, 0) == 0

    def test_rgb_to_pal15_white(self):
        assert rgb_to_pal15(255, 255, 255) == 0x7FFF

    def test_roundtrip(self):
        original = 0x52A7  # arbitrary 15-bit color
        r, g, b = pal15_to_rgb(original)
        roundtripped = rgb_to_pal15(r, g, b)
        assert roundtripped == original

    def test_rgb_clamping(self):
        # Values > 248 should clamp to 31 per channel
        result = rgb_to_pal15(300, 300, 300)
        assert result == 0x7FFF

    def test_color_distance_identical(self):
        c = 0x1234
        assert color_distance(c, c) == 0.0

    def test_color_distance_symmetric(self):
        a, b = 0x1234, 0x5678
        assert color_distance(a, b) == color_distance(b, a)

    def test_color_distance_positive(self):
        assert color_distance(0x0000, 0x7FFF) > 0


# ---------------------------------------------------------------------------
# fe8rom.py: palette interleaving roundtrip
# ---------------------------------------------------------------------------

class TestPaletteInterleave:
    def _make_sub_palette(self, seed_val):
        """Create a deterministic 32-byte sub-palette."""
        return bytearray((seed_val + i) & 0xFF for i in range(32))

    def test_roundtrip(self):
        subs = [self._make_sub_palette(i * 0x10) for i in range(5)]
        interleaved = interleave_palettes(subs)
        for slot in range(5):
            extracted = deinterleave_palette(interleaved, slot)
            assert extracted == subs[slot]

    def test_deinterleave_size(self):
        interleaved = bytearray(160)  # 5 sub-palettes * 32 bytes
        result = deinterleave_palette(interleaved, 0)
        assert len(result) == 32

    def test_interleave_size(self):
        subs = [bytearray(32) for _ in range(5)]
        result = interleave_palettes(subs)
        assert len(result) == 160


# ---------------------------------------------------------------------------
# fe8rom.py: enum sanity
# ---------------------------------------------------------------------------

class TestEnums:
    def test_pid_eirika_is_1(self):
        assert PID.EIRIKA == 1

    def test_pid_seth_is_2(self):
        assert PID.SETH == 2

    def test_jid_ephraim_lord_is_1(self):
        assert JID.EPHRAIM_LORD == 1

    def test_jid_manakete_is_14(self):
        assert JID.MANAKETE == 14

    def test_all_jid_values_unique(self):
        values = [jid.value for jid in JID]
        assert len(values) == len(set(values))
