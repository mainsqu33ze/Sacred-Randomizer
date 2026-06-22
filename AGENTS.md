# FE8 (Sacred Stones) ROM Randomizer

## Commands
```
pip install -r requirements.txt
python fe8_randomizer.py ROM.GBA -c config.yaml -o output.gba
python fe8_randomizer.py ROM.GBA --seed 42 --dump
```

## Entrypoints & structure
- `fe8_randomizer.py` — CLI entrypoint (argparse)
- `randomizer.py` — `apply_config()` orchestrates all randomization in order: class → growths → base stats → affinity → weapon stats → weapon effects → unit defs → unit items
- `fe8rom.py` — ROM binary parsing: `ROM`, `CharacterData`, `ClassData`, `ItemData`, `ChapterData`, enums (`PID`, `JID`)
- `scripts/_check_*` / `scripts/_find_*` / `scripts/_dump_*` — standalone dev diagnostics, not part of the tool
- No test suite, no lint/typecheck config — verify manually with test ROM

## ROM layout constraints
- Only FE8U accepted (code `BE8E` at 0xAC)
- GBA → file offset: `rom_offset(addr) = addr - 0x08000000`
- Record sizes: `PINFO_SIZE=0x34`, `JINFO_SIZE=0x54`, `UNIT_DEF_SIZE=0x14`, `ITEM_DATA_SIZE=0x24`
- Key tables: `CHARACTER_TABLE_ADDR=0x08803D64`, `CLASS_TABLE_ADDR=0x08807164`, `ITEM_TABLE_ADDR=0x08809B10`, `CHAPTER_DATA_TABLE=0x088B0890`

## Randomization rules
- **Class shuffle**: splits by class attribute bit 8 (`CA_PROMOTED=0x100`). Trainees shuffled within trainee classes only. One random character becomes Manakete (`JID.MANAKETE_MYRRH`, JID=60). `JID.MANAKETE` (14) is excluded from `STANDARD_JIDS` to prevent it being assigned.
- **omit_classes**: case-insensitive JID enum name lookup. Applied after splitting pools.
- **Class base stat scramble** (`randomize_stats`): by default shuffles stat arrays only within the same tier (promoted, unpromoted, trainee). `cross_tier_scramble: true` shuffles across all `STANDARD_JIDS` together. `preserve_base: false` assigns random(0,20); `preserve_base: true` shuffles existing values.
- **Base stat class shuffle** (`base_stat_randomization.class: shuffle`): same tier-scoped swap of whole stat blocks (HP/Pow/Skl/Spd/Def/Res stay together). `cross_tier_scramble: true` under `base_stat_randomization` allows cross-tier. `class: shuffle` no longer scrambles each class's own stats internally (the old behavior that caused 0-HP classes).
- **Weapon rank**: `_adjust_weapon_ranks()` zeros ranks for weapon types the new class can't wield, and uses class baseWexp as floor for supported types.
- **Item pools** (`build_weapon_pools` in fe8rom.py): filters `stored_id == item_id`, `weapon_type ≤ 7`, `uses > 0`, `range > 0`. Excludes `MONSTER_BLOCKED_ITEM_IDS` (16 monster items) and `STORY_EXCLUSIVE_ITEM_IDS` (Rapier 0x09, Reginleif 0x78, Sieglinde 0x85, Siegmund 0x92). Staves (type 4) included even with `might == 0`; non-staves require `might > 0`.
- **Manakete inventory**: replaces all 4 item slots with `[Dragonstone(0xAA), Vulnerary(0x6C), Vulnerary(0x6C), 0]`.
- **Weapon effects**: filters match item pool filters (excludes monster/story). Skips staves. Already-affected weapons may be overwritten.
- **Growth pool** (`_distribute_growth_pool`): 7 random weights normalized to `pool_total`, clamped to min/max.

## UD array scanner gotchas
- `_scan_ud_arrays` searches for event command bytes `{0x40..0x43, 0x54, 0x8C, 0xA8, 0xAA, 0xC4}` + pointer pattern in ROM data
- `_ud_array_at` validates 20-byte entries: terminates on all-zero, rejects if `char_idx > 200 || class_idx > 110 || entries > 100`
- Route split (Eirika ch9–15/16–21x, Ephraim 9x–15x/16x–21x) means route-specific event scripts may reference arrays the byte-scan misses

## Config quirks
- `seed:` in config is only used when no `--seed` CLI arg given
- Weapon `enabled: random` is just truthy — it triggers per-stat randomization mode
- `enabled: true` for weapon_randomization is valid — truthy check uses default per-stat randomization
- Affinity randomization restricted to values 1–7 (valid FE8 affinities)
