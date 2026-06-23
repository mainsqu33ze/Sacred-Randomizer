# FE8 (Sacred Stones) ROM Randomizer

## Commands
```
pip install -r requirements.txt
python fe8_randomizer.py ROM.GBA -c config.yaml -o output.gba
python fe8_randomizer.py ROM.GBA --dump          # prints hardcoded config template to stdout
python fe8_randomizer.py ROM.GBA --seed 42        # overrides config seed
```

Without `-o`, output defaults to `{rom}_randomized.gba`. `--dump` ignores `--seed` (exits before seeding). `save()` calls `fix_checksum()` automatically.

## Entrypoints & structure
- `fe8_randomizer.py` — CLI entrypoint (argparse)
- `randomizer.py` — `apply_config()` orchestrates all randomization in order: class → growths → base stats → affinity → weapon stats → weapon effects → promotion items → unit defs → unit items
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
- `_ud_array_at` validates 20-byte entries: terminates on all-zero, returns 0 if `char_idx == 0 || char_idx > 114 || class_idx > 114 || entries > 100`. Also rejects arrays at addresses >= `0x088D0000` (compressed animation data). The `char_idx == 0` check catches false positives like 0x0880210C (event coordinate data, not a UD array) which has entries 1/4 with pid=0 but byte[1] ≤ 114.
- **False positive at 0x0880210C**: Contains 6 entries with u16 coordinate pairs (`0x10`/`0x14` high bytes = map layers). Entries 1/4 have pid=0, now correctly rejected. Writing item IDs here corrupted coordinate data, causing combat animation glitches.
- **0x08802508** (1 entry, pid=3 valid) still passes — its content also looks like coordinate data but can't be filtered without breaking real single-entry arrays. Untested whether writes there cause issues.
- No `entries < 2` check — many real UD arrays (e.g., in 0x088Bxxxx) have exactly 1 entry.
- Route split (Eirika ch9–15/16–21x, Ephraim 9x–15x/16x–21x) means route-specific event scripts may reference arrays the byte-scan misses

## Config quirks
- `seed:` in config is only used when no `--seed` CLI arg given
- Weapon `enabled: random` is just truthy — it triggers per-stat randomization mode
- `enabled: true` for weapon_randomization is valid — truthy check uses default per-stat randomization
- Affinity randomization restricted to values 1–7 (valid FE8 affinities)
- `affinity_randomization.enabled: shuffle` is just truthy — Python treats `'shuffle'` as truthy, enabling random affinity assignment

## Promotion items (`promotion_items`)
Toggleable via `promotion_items.enabled: true` / `false`.
- `master_seal_universal: true` — all promotion items behave as Master Seal (every unpromoted class can use them). Modifies `CanUnitUsePromotionItem` function pointer table, item-specific permission tables, and class-specific tables. When `false`, original per-class promotion restrictions remain.
- `replace_distribution: true` — all promotion items in unit definitions (chests, enemy drops, events) are replaced with Master Seal, and items 0x62–0x68 get Master Seal's icon/name/description/effect. When `false`, original promotion items still drop but still behave as Master Seals if `master_seal_universal` is on.
- Disable both to keep vanilla promotion behavior entirely.

### Implementation details

**Phase 1-3** (item tables + function pointers): Zero out non-Master-Seal item-specific permission tables (`PROMO_ITEM_TABLES`), populate Master Seal's table with promo JIDs, and redirect all item function table entries (`PROMO_FUNCTION_TABLE_ADDR=0x08057DD0`, items 0x62-0x74) to Master Seal's handler (`0x08057E5C`).

**Phase 4** (class-specific tables): Writes `promo_jid+1` for items 0x62-0x69 into the per-class table at `PROMO_CLASS_TABLE_BASE + cls * 0x41 + item_id`. Each class gets a 0x41-byte slot (indexed by item_id). **Class 20 is excluded** because its table at `0x0880D22F` + item offset overflows the 21×0x41 contiguous allocation (`0x0880CD1B`–`0x0880D264`) into the pointer table at `0x0880D270`, corrupting entries 8-10 (`0x081C1E80`, `0x081C1E78`, `0x081C1E74`).

**Phase 4b** (class 20 redirect): Writes `ms_stub_addr` (`0x08057E5C`) to `PROMO_CLASS_FUNCTION_TABLE=0x08057EF0` entry 20 (class 20's handler at `0x08057F40`). This makes class 20 use Master Seal's item-specific handler, which reads `0x0880CA0F[class_id]` (already populated correctly in Phase 2).

**Phases 5-7**: Zero remaining item function table entries (0x6A-0x74), replace promotion item distribution with Master Seal in UD arrays, copy Master Seal's item data (icon/name/effect) to items 0x62-0x68.

### Key tables for promotion
| Table | Address | Description |
|---|---|---|
| `PROMO_FUNCTION_TABLE_ADDR` | `0x08057DD0` | 19-entry item handler table |
| `PROMO_ITEM_TABLES` | `0x0880C848`+ | 8 item-specific tables, 0x41 bytes each |
| `PROMO_CLASS_TABLE_BASE` | `0x0880CD1B` | 21 class-specific tables, 0x41 bytes each (class 0-20) |
| `PROMO_CLASS_FUNCTION_TABLE` | `0x08057EF0` | 21-entry class handler table |
| Pointer table | `0x0880D270` | Adjacent to class 20 table — must not be overwritten |
