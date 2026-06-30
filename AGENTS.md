# FE8 (Sacred Stones) ROM Randomizer

## Commands
```
pip install -r requirements.txt
python fe8_randomizer.py ROM.GBA -c config.yaml -o output.gba
python fe8_randomizer.py ROM.GBA --dump          # prints default config to stdout
python fe8_randomizer.py ROM.GBA --seed 42        # overrides config seed
```
Without `-o`, output defaults to `{rom}_randomized.gba`. `--dump` ignores `--seed`. `save()` calls `fix_checksum()` automatically. No test suite — verify manually or run test configs: `incremental_test.yaml` (all features) or `test_config.yaml` (dev baseline).

## Entrypoints & structure
- `fe8_randomizer.py` — CLI entrypoint (argparse)
- `gui.py` — Tkinter GUI (standalone, `python gui.py`; unused by CLI path)
- `randomizer.py` — `apply_config()` orchestrates in order: class → growths → base stats → **promo gain sync** → affinity → weapon stats → weapon effects → promotion items → unit defs → enemy randomize → **palette mapping** → unit items → loot
- `fe8rom.py` — ROM binary parsing: `ROM`, `CharacterData`, `ClassData`, `ItemData`, `ChapterData`, enums (`PID`, `JID`), `build_weapon_pools()`
- `scripts/_check_*` / `_find_*` / `_dump_*` — standalone dev diagnostics, not part of randomizer

## ROM layout constraints
- Only FE8U accepted (code `BE8E` at 0xAC). GBA offset: `addr - 0x08000000`
- Record sizes: `PINFO_SIZE=0x34`, `JINFO_SIZE=0x54`, `UNIT_DEF_SIZE=0x14`, `ITEM_DATA_SIZE=0x24`
- Key tables: `CHARACTER_TABLE_ADDR=0x08803D64`, `CLASS_TABLE_ADDR=0x08807164`, `ITEM_TABLE_ADDR=0x08809B10`, `CHAPTER_DATA_TABLE=0x088B0890`

## Randomization rules
- **Class mode**: `mode: shuffle` (default) permutes classes within each tier without repeats. `mode: random` samples with replacement (repeats allowed). `manakete_count: N` controls how many characters (0–N) become Manakete (`JID.MANAKETE_MYRRH`, JID=60). `JID.MANAKETE` (14) excluded from `STANDARD_JIDS`. `include_soldier: false` (default) removes Soldier (JID 78, no promotion) from player pools — set `true` to allow it.
- **Palette mapping** (`palette_mapping: true`): after class randomization, updates the PaletteClassTable (indexed by PID-1, 7 bytes per entry at GBA address loaded from pointer at 0x575B4) to map each character's new class to their existing custom palette ID. Uses `CA_PROMOTED` (bit 8 of class attributes) to determine tier: trainee→slot 0 (+ slot 1 via base, + slot 3 via promo chain), promoted→slot 3, unpromoted→slot 1 (+ slot 3 via promo chain). Promotion slots are also updated via `ClassData.jidPromotion`. PaletteIndexTable (pointer at 0x57394) left unchanged. Also applied to BOSS_PIDS when `include_bosses: true`.
- **Palette limitation**: Characters with all-zero PaletteIndexTable entries (Eirika PID 1, Ephraim PID 15) have NO palette override — their unique colors come from unique class animations (EirikaLord/EphraimLord). When randomized to a different class, they'll use the new class's default palette. This is acceptable: they had no custom palette entry to preserve. Other unique-class characters (Ross PID 7, Amelia PID 18, Ewan PID 24) DO have PaletteIndexTable entries, so their custom palettes ARE preserved.
- **Palette borrowing** (automatic, part of `randomize_palette_mappings`): After PaletteClassTable updates, for any PID with an all-zero PaletteIndexTable entry, the function builds a reverse lookup from the ORIGINAL (pre-modification) PaletteClassTable mapping class JID → donor PIDs with non-zero PaletteIndexTable. For each zero-index PID, it finds their new class JID in the lookup and copies the first player-character donor's PaletteIndexTable entry. This gives Eirika/Ephraim custom colors (e.g., borrowing Vanessa's palette when becoming a Pegasus Knight) instead of default class colors. PID 27 (unnamed, between DOZLA and RENNAC) and Myrrh (PID 30) also get borrowing when randomized.
- **Promo gain sync** (`synchronize_promotion_gains`): always active, no config. After base stat randomization, iterates all 25 `MALE_FEMALE_PAIRS` (defined at module level) and for each pair takes the higher per-stat value of `promotionHp/Pow/Skl/Spd/Def/Res`, writing the max to both classes. This ensures Hero and Hero_F (etc.) grant identical promotion bonuses.
- **omit_classes**: case-insensitive JID enum name lookup. Applied after splitting pools.
- **Class base stat shuffle** (`base_stat_randomization.class: shuffle`): tier-scoped swap of full class stat blocks (HP/Pow/Skl/Spd/Def/Res/Con/Mov). `cross_tier_scramble: true` allows mixing tiers. `preserve_base: false` assigns random(0,20). `shuffle_con_mov: false` leaves Con/Mov unchanged. This is the only class stat shuffle — old `class_randomization.randomize_stats` was removed.
- **Con randomization** (`base_stat_randomization.con`): optional sub-section with `enabled`, `min`, `stddev`. `min` applies to class bases; `player_min` (default 1) applies to player unit bases. Applies to both `character: random` and `class: random` modes. When absent, legacy behaviour applies (no Con for character, Con with global stddev for class).
- When `con.enabled: false`, Con is preserved in ALL class base stat modes (scale, shuffle, random). In shuffle mode this overrides `shuffle_con_mov` for Con only — Mov is still controlled by `shuffle_con_mov`.
- **Weapon rank**: `_adjust_weapon_ranks()` zeros ranks for weapon types the new class can't wield, uses class `baseWexp` as floor for supported types.
- **Item pools** (`build_weapon_pools`): filters `stored_id == item_id`, `weapon_type ≤ 7`, `uses > 0`, `range > 0`. Excludes `MONSTER_BLOCKED_ITEM_IDS` (16) and `STORY_EXCLUSIVE_ITEM_IDS` (Rapier 0x09, Reginleif 0x78, Sieglinde 0x85, Siegmund 0x92). Staves (type 4) included with `might == 0`; non-staves need `might > 0`.
- **Manakete inventory**: replaces all 4 slots with `[Dragonstone(0xAA), Vulnerary(0x6C), Vulnerary(0x6C), 0]`.
- **Class growth rates** (`growth_randomization.class`): applied to JIDs 1–128 (all classes, including enemies). Modes:
  - `<number>` (e.g., `1.3`): scale all growths by factor, clamped to `min`/`max`.
  - `'random_buff'`: each growth multiplied by `1.0 ± random(0, class_buff_range)`, clamped to `min`/`max`.
  - `'random'`: gaussian with optional `mean`/`stddev` (same as character mode).
  - `'shuffle'`: permutes the 7 growth values within each class.
  - `'pool'`: distributes `pool_total` across 7 stats (7 random weights normalized to total, clamped).
- **Item mode**: `mode: random` (default) picks random weapons from pools for invalid class-weapon combos. `mode: shuffle` permutes all items across UD arrays.
- **Event items** (GiveItem + chests): Two scanner functions:
  - `_scan_giveitem_events()`: Searches for `40 0A 00 00` header + any GBA pointer (`0x08000000-0x08FFFFFF`) + `40 05` subcommand + valid item ID. Yields `(write_offset, item_id, '<I')` where write_offset = pos+12 (u32 item field). Catches all GiveItem variants (Format A with pointer `0x08591F40` + ~24 other-pointer variants), finding ~79 events vs 52 with the old Format-A-only pattern.
  - `_scan_chest_events()`: Scans Location Events tables (types `0x0C/0x10/0x11/0x12/0x14/0x16`) across all 35 chapters. Chest entries (type `0x12`) have format: flag(1) | type(1) | x(1) | y(1) | item(u16 at +4) | unk(u16 at +6) | script(u32 at +8). Yields `(write_offset, item_id, '<H')` where write_offset = off+4 (u16 item field). Finds 5 real chest entries (Ch4, Ch16, Ch26, Ch27, Ch29).
  - `_scan_loot_events()`: Combines both sources, filters out `PROMOTION_ITEM_IDS`, `MONSTER_BLOCKED_ITEM_IDS`, `STORY_EXCLUSIVE_ITEM_IDS`, and dummy items (`0x3D, 0x44, 0x8A`). Yields `(write_offset, item_id, pack_fmt)`.
  - Write formats: GiveItem uses `<I` (u32), chests use `<H` (u16) — using `<I` on chests corrupts byte 6-7 (unknown field).
  - Both shuffle and random modes run via `randomize_loot()` (no separate mode for event items).
- **Loot randomization** (`loot_randomization`): `mode: random | shuffle`. Scans GiveItem (`0x1E`) commands plus chest Location Events via `_scan_loot_events()`. Previously used two false-positive filters (now absorbed into `_scan_giveitem_events`'s strict 40-format validation). Runs after promotion item conversion.
- **Boss buffs** (`boss_buffs`): sub-section of `enemy_randomization` active when `include_bosses: true`. `growths.mode` / `base_stats.mode` support `<number>` (scale), `random_buff` (per-stat random factor), or `random` (gaussian). `max_weapon_ranks: true` sets Wexp=251 (S-rank) for all weapon types the boss's class can use, and zeroes out types the class can't use. Applied between Phase A and Phase B, on CharacterData only.
- **Enemy randomization** (`randomize_enemies`): operates on generic enemies (PID 35–255). **Class randomization** changes both `CharacterData.jidDefault` (Phase A) and UD entry class bytes (Phase B). Groups by movement category via `_move_group_key()`: flyer, water, mountain, or foot — foot classes pooled together for max variety. Excludes `ENEMY_EXCLUDED_JIDS`, lord classes, and trainees. `include_monsters: true` adds `MONSTER_JIDS | EXTRA_MONSTER_JIDS`. `randomize_monster_classes: false` (default) keeps monster-class enemies in original class. `include_bosses: false` (default) skips BOSS_PIDS. `FINAL_BOSS_PID=0xBE` always excluded. **Item randomization** replicates player `mode: random` — keeps weapons if new class allows that weapon type (ignores rank). Prefers `MONSTER_WEAPON_POOLS` for restricted monsters, falls back to `_pick_weapon_for_type()`. Clears slots for weaponless classes.

## UD array scanner gotchas
- `_scan_ud_arrays` searches for `{0x40..0x43, 0x54, 0x8C, 0xA8, 0xAA, 0xC4}` + 0x2C pattern, reads pointer at pos+4 in ROM data. Covers LOAD-event-referenced UD arrays. Uses `_ud_array_at_lenient` for validation.
- `_scan_chapter_ud_arrays` reads UD pointers from chapter event data (direct pointers at 4-byte intervals up to 0x400 bytes) and GMap data (up to 0x200 bytes). Covers arrays FE Builder shows in its Unit Placer view.
- `_ud_array_at` (strict): validates 20-byte entries, terminates on all-zero, returns 0 if `char_idx == 0 || > 114 || class_idx > 114 || entries > 100`. Rejects addrs >= `0x088D0000`. **Only used for debugging/exploration now** — the `char_idx > 114` check incorrectly rejects legitimate generic enemies with PID > 114 (e.g., PID 128, 130).
- `_ud_array_at_lenient` (used by both `_scan_ud_arrays` and `_scan_chapter_ud_arrays`): allows pid > 114 (NPC/allied units embedded alongside generic enemies in chapter data arrays). Only rejects pid=0 mid-array or class_idx > 127.
- **False positive at 0x0880210C**: 6 entries with u16 coordinate pairs. Entries 1/4 have pid=0, now correctly rejected. Writing here corrupted coordinates, causing combat animation glitches.
- **0x08802508** (1 entry, pid=3 valid) still passes — can't filter without breaking real single-entry arrays.
- No `entries < 2` check — many real UD arrays (0x088Bxxxx) have exactly 1 entry.
- Route split (Eirika ch9–21x, Ephraim 9x–21x) means route-specific event scripts may reference arrays the byte-scan misses.

## Config quirks
- `seed:` in config ignored when `--seed` CLI arg given
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

## Enemy randomization constants
- `ENEMY_EXCLUDED_JIDS`: Manakete (0x0E), Bard (0x46), Dancer (0x4D), Fleet (0x50), Phantom (0x51), Demon King (0x66), and 0x67–0x7B (civilians + unused JIDs).
- `BOSS_PIDS`: set(range(0x40, 0x64)) | {0x68, 0x6A, 0x6B, 0x6C, 0x6D} — PIDs 0x40–0x63 (64–99) + stragglers, excluded unless `include_bosses: true`.
- `FINAL_BOSS_PID = 0xBE` — PID 190, always excluded regardless of `include_bosses`.
- `MONSTER_WEAPON_POOLS`: limited item pools for specific monster JIDs (MANAKETE_2 → 0x90, REVENANT/ENTOUMBED/BAEL/ELDER_BAEL → [0x8B, 0xAD, 0xAE, 0xAF], MAUTHEDOOG/GWYLLGI → [0xB1, 0xB2], MOGALL/ARCH_MOGALL → [0xB3, 0xB4, 0xAC], GORGON → [0xAC, 0xAB, 0xB5]).
- `EXTRA_MONSTER_JIDS` = {0x7C, 0x7D} — JIDs beyond the enum range.
