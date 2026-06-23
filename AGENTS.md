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
- **Item mode**: `mode: random` (default) picks random weapons from pools for invalid class-weapon combos. `mode: shuffle` permutes all weapon items across UD arrays.
- **Event items** (`randomize_events: true`): scans for GiveItem (`0x1E`) event commands in chapter data range (`0x088B0000-0x088CFFFF`). Validates slot 0-3 and item_id 0x01-0xBF. Replaces weapon-type items with random picks from weapon pools. Non-weapons, monster-blocked, and story-exclusive items are preserved. Does NOT run in shuffle mode.

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
The `use_effect` dispatch table at `0x08029234` maps item use-effect IDs to handler functions. Item `0x88` (Master Seal) has `use_effect_id=0x2D` → handler at `0x080293E8` → reads byte-per-class table at `0x088ADF9E`. Items `0x64–0x68` (old promo items) still use the **function table handler** at `0x08057DD0` entries 0–6, which Phase 3 redirects to Master Seal's stub (`0x08057E5C`). This stub loads permission table `0x0880CA0F` (filled by Phase 2). These are **two different code paths with different permission tables** — both must be modified.

**Phase 1-3** (item tables + function pointers): Zero out non-Master-Seal item-specific permission tables (`PROMO_ITEM_TABLES`), populate Master Seal's table with promo JIDs. Phase 3 zeroes function table entries 2-6 (`0x08057DD0`, items 0x64-0x68) so they fall through to `use_eff=0x2D` dispatch (reads terminated list at `0x088ADF76`). Entries 0-1 (items 0x62-0x63) redirect to Master Seal's stub (`0x08057E5C`).

**Phase 4** (class-specific tables): Writes `promo_jid+1` for items 0x62-0x69 into the per-class table at `PROMO_CLASS_TABLE_BASE + cls * 0x41 + item_id`. Each class gets a 0x41-byte slot (indexed by item_id). **Class 20 is excluded** because its table at `0x0880D22F` + item offset overflows the 21×0x41 contiguous allocation (`0x0880CD1B`–`0x0880D264`) into the pointer table at `0x0880D270`, corrupting entries 8-10 (`0x081C1E80`, `0x081C1E78`, `0x081C1E74`).

**Phase 4b** (class 20 redirect): Writes `ms_stub_addr` (`0x08057E5C`) to `PROMO_CLASS_FUNCTION_TABLE=0x08057EF0` entry 20 (class 20's handler at `0x08057F40`). This makes class 20 use Master Seal's item-specific handler, which reads `0x0880CA0F[class_id]` (already populated correctly in Phase 2).

**Phases 5-8**: Fix permission tables + distribution replacement:
- **Phase 5**: Writes `0x01` to all 16 bytes of the byte-per-class table at `0x088ADF9E` (used by `use_eff=0x2D` handler). Vanilla had zeros for classes 3-5, 7, 9-13, 15 which blocked those classes from using item 0x88.
- **Phase 5b**: Replaces invalid JID entries `0x7E`/`0x7F` in the terminated class list at `0x088ADF76` (used by `use_eff=0x2E` handler) with lord class IDs `0x01` and `0x02`.
- **Phase 6**: Scans UD arrays via `_scan_ud_arrays` and replaces any promotion item ID (`0x64-0x68, 0x88, 0x8A, 0x97, 0x98, 0x99`) with Master Seal `0x88`.
- **Phase 7**: Copies Master Seal's item data (icon, name, description, effect, `use_effect_id`) to all other promotion items. Preserves the `number` field (offset 6) for each item.
- **Phase 9**: Full-ROM scan (`0x08800000-0x08FFFFFF`) for GiveItem events (`0x1E` byte, slot 0-3, promo item IDs). Replaces 36 promo items missed by the old range-limited `_scan_giveitem_events`. Defense-in-depth; vanilla FE8 has no promo items in GiveItem events.

### Key tables for promotion
| Table | Address | Description |
|---|---|---|
| `PROMO_FUNCTION_TABLE_ADDR` | `0x08057DD0` | 19-entry item handler table, entries 0-6 redirect to Master Seal stub after Phase 3 |
| `PROMO_ITEM_TABLES` | `0x0880C848`+ | 8 item-specific tables, 0x41 bytes each (`0x62-0x68`, `0x69/0x88`) |
| `PROMO_CLASS_TABLE_BASE` | `0x0880CD1B` | 21 class-specific tables, 0x41 bytes each (class 0-20) |
| `PROMO_CLASS_FUNCTION_TABLE` | `0x08057EF0` | 21-entry class handler table |
| Pointer table | `0x0880D270` | Adjacent to class 20 table — must not be overwritten |
| `use_eff` dispatch | `0x08029234` | 256-entry handler table for item use effects |
| byte-per-class table | `0x088ADF9E` | 16 bytes, classes 0-15, used by `use_eff=0x2D` handler (item 0x88) |
| terminated class list | `0x088ADF76` | 31 entries + terminator, used by `use_eff=0x2E` handler |
| pointer structure | `0x088ADFA4` | Count + pointer array for entries beyond byte-per-class table range |

### Handler code structure for function table entries (0x08057E24-0x08057E5C)
All 8 entries follow the same pattern (8 bytes each):
```
4800        LDR r0, [pc, #0]    ; load table address from next 4 bytes
E0XX        B common_handler    ; branch to shared code at 0x08057EBE
.DWORD      table_addr          ; e.g. 0x0880C848 (item 0x62), ..., 0x0880CA0F (item 0x88)
```
The common handler at `0x08057EBE` uses r0 as the permission table base and checks `table[class_id] != 0`. After Phase 3 redirect: entries 0-1 load `0x0880CA0F`, entries 2-6 are zeroed (fall to `use_eff`), entry 7 loads `0x0880CA0F`.
