# FE8 (Sacred Stones) ROM Randomizer

## Commands
```
pip install -r requirements.txt
python fe8_randomizer.py ROM.GBA -c config.yaml -o output.gba
python fe8_randomizer.py ROM.GBA --dump          # prints default config to stdout
python fe8_randomizer.py ROM.GBA --seed 42        # overrides config seed
```
Without `-o`, output defaults to `{rom}_randomized.gba`. `--dump` ignores `--seed`. `save()` calls `fix_checksum()` automatically. No test suite — verify manually with test ROM.

## Entrypoints & structure
- `fe8_randomizer.py` — CLI entrypoint (argparse)
- `randomizer.py` — `apply_config()` orchestrates in order: class → growths → base stats → affinity → weapon stats → weapon effects → promotion items → unit defs → unit items
- `fe8rom.py` — ROM binary parsing: `ROM`, `CharacterData`, `ClassData`, `ItemData`, `ChapterData`, enums (`PID`, `JID`), `build_weapon_pools()`
- `scripts/_check_*` / `_find_*` / `_dump_*` — standalone dev diagnostics, not part of randomizer

## ROM layout constraints
- Only FE8U accepted (code `BE8E` at 0xAC). GBA offset: `addr - 0x08000000`
- Record sizes: `PINFO_SIZE=0x34`, `JINFO_SIZE=0x54`, `UNIT_DEF_SIZE=0x14`, `ITEM_DATA_SIZE=0x24`
- Key tables: `CHARACTER_TABLE_ADDR=0x08803D64`, `CLASS_TABLE_ADDR=0x08807164`, `ITEM_TABLE_ADDR=0x08809B10`, `CHAPTER_DATA_TABLE=0x088B0890`

## Randomization rules
- **Class mode**: `mode: shuffle` (default) permutes classes within each tier without repeats. `mode: random` samples with replacement (repeats allowed). `manakete_count: N` controls how many characters (0–N) become Manakete (`JID.MANAKETE_MYRRH`, JID=60). `JID.MANAKETE` (14) excluded from `STANDARD_JIDS`.
- **omit_classes**: case-insensitive JID enum name lookup. Applied after splitting pools.
- **Class base stat shuffle** (`base_stat_randomization.class: shuffle`): tier-scoped swap of full class stat blocks (HP/Pow/Skl/Spd/Def/Res/Con/Mov). `cross_tier_scramble: true` allows mixing tiers. `preserve_base: false` assigns random(0,20). `shuffle_con_mov: false` leaves Con/Mov unchanged. This is the only class stat shuffle — old `class_randomization.randomize_stats` was removed.
- **Weapon rank**: `_adjust_weapon_ranks()` zeros ranks for weapon types the new class can't wield, uses class `baseWexp` as floor for supported types.
- **Item pools** (`build_weapon_pools`): filters `stored_id == item_id`, `weapon_type ≤ 7`, `uses > 0`, `range > 0`. Excludes `MONSTER_BLOCKED_ITEM_IDS` (16) and `STORY_EXCLUSIVE_ITEM_IDS` (Rapier 0x09, Reginleif 0x78, Sieglinde 0x85, Siegmund 0x92). Staves (type 4) included with `might == 0`; non-staves need `might > 0`.
- **Manakete inventory**: replaces all 4 slots with `[Dragonstone(0xAA), Vulnerary(0x6C), Vulnerary(0x6C), 0]`.
- **Growth pool** (`_distribute_growth_pool`): 7 random weights normalized to `pool_total`, clamped to min/max.
- **Item mode**: `mode: random` (default) picks random weapons from pools for invalid class-weapon combos. `mode: shuffle` permutes all items across UD arrays.
- **Event items**: GiveItem (`0x1E`) in chapter data range (`0x088B0000-0x088CFFFF`). Non-weapons, monster-blocked, story-exclusive preserved. Does NOT run in shuffle mode.

## UD array scanner gotchas
- `_scan_ud_arrays` searches for `{0x40..0x43, 0x54, 0x8C, 0xA8, 0xAA, 0xC4}` + pointer pattern in ROM data
- `_ud_array_at` validates 20-byte entries: terminates on all-zero, returns 0 if `char_idx == 0 || > 114 || class_idx > 114 || entries > 100`. Rejects addrs >= `0x088D0000` (compressed anim data). `char_idx == 0` check catches false positives like `0x0880210C` (coordinate data, not a UD array).
- **False positive at 0x0880210C**: 6 entries with u16 coordinate pairs. Entries 1/4 have pid=0, now correctly rejected. Writing here corrupted coordinates, causing combat animation glitches.
- **0x08802508** (1 entry, pid=3 valid) still passes — can't filter without breaking real single-entry arrays.
- No `entries < 2` check — many real UD arrays (0x088Bxxxx) have exactly 1 entry.
- Route split (Eirika ch9–21x, Ephraim 9x–21x) means route-specific event scripts may reference arrays the byte-scan misses.

## Config quirks
- `seed:` in config ignored when `--seed` CLI arg given
- Weapon `enabled: random` is truthy — triggers per-stat gaussian randomization mode
- `affinity_randomization.enabled: shuffle` is truthy — Python treats `'shuffle'` as truthy, enabling random affinity assignment

## Promotion items
Two code paths must both be patched:
- **(A) Function table** at `0x08057DD0` (items `0x62–0x74`): handler loads byte-per-class table, `table[class_id] != 0` → usable.
- **(B) USE_EFFECT dispatch** at `0x08029234` (all items): handler at `0x080293E8` (use_eff=0x2D) loads terminated JID list at `0x088ADF76` (31 JIDs + terminator, loop checks class_id match).

Phases (in `randomize_promotion_items`):
1. Zero non-MS byte-per-class tables (`0x62-0x68`) except MS table `0x0880CA0F`.
2. Fill ALL byte-per-class tables (`0x64-0x68, 0x88`) with `0x01` + per-class `promo_jid+1`.
3. Function table: entries 0–1 redirect to MS stub (`0x08057E5C`); entries 2–6 preserved at original handler addrs so FE Builder can trace them to filled tables.
4. Class-specific tables: write `promo_jid+1` for items `0x62-0x69`. **Class 20 excluded** — its table at `0x0880D22F` + item offset overflows into pointer table at `0x0880D270`, corrupting entries 8-10. Phase 4b redirects class 20's handler to MS stub.
5. Redirect ALL 12 USE_EFFECT literal pools (including sub-dispatch for old use_eff `0x19–0x1D` at `0x08029398–0x080293B8`) to `0x088ADF76`. Phase 5b replaces invalid JIDs `0x7E`/`0x7F` with lords `0x01`/`0x02`.
6. Set `use_eff=0x2D` on all 10 promotion items (`0x64-0x68, 0x88, 0x8A, 0x97, 0x98, 0x99`).
7. Replace promo items in UD arrays with Master Seal `0x88`.
8. Copy MS icon/name/desc/effect to other promo items (preserves `number` field at offset 6).
9. Full-ROM GiveItem (`0x1E`) scan for promo items missed by UD scan.

**Key addresses**: `PROMO_FUNCTION_TABLE=0x08057DD0`, `PROMO_ITEM_TABLES=0x0880C848+`, `PROMO_CLASS_TABLE_BASE=0x0880CD1B`, `terminated_list=0x088ADF76`, `MS_table=0x0880CA0F`. FE Builder reads literal pools from handler code — all must point to `0x088ADF76` for Phase 5 to appear correct.
