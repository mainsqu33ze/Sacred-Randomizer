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
- **Class shuffle**: `mode: shuffle` (default) permutes classes within each tier without repeats. `mode: random` samples with replacement (repeats allowed). `manakete_count: N` controls how many characters (0–N) become Manakete (`JID.MANAKETE_MYRRH`, JID=60). `JID.MANAKETE` (14) is excluded from `STANDARD_JIDS`.
- **omit_classes**: case-insensitive JID enum name lookup. Applied after splitting pools.
- **Class base stat shuffle** (`base_stat_randomization.class: shuffle`): tier-scoped swap of full class stat blocks (HP/Pow/Skl/Spd/Def/Res/Con/Mov). `cross_tier_scramble: true` allows swapping across promoted/unpromoted/trainee tiers. `preserve_base: false` assigns random(0,20) instead of swapping existing values. `shuffle_con_mov: false` leaves Con and Mov unchanged. This is the only class stat shuffle option — the old `class_randomization.randomize_stats` was removed in consolidation.
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
Two code paths exist for promotion item permission checking:
- **(A) Function table** at `0x08057DD0` (items `0x62–0x74`): handler loads a byte-per-class table (`0x41` bytes indexed by class_id, `table[class_id] != 0` → usable).
- **(B) USE_EFFECT dispatch** at `0x08029234` (all items): handler at `0x080293E8` (use_eff=0x2D) loads the terminated JID list at `0x088ADF76` (31 JIDs + 0x00 terminator, loops checking if class_id matches any JID).

After randomization BOTH paths are unified to allow all unpromoted classes. Items `0x64–0x68` also keep their non-zero function table entries so FE Builder can trace them; their handler **literals** (byte-per-class table addresses) are filled with universal promotion data (all `0x01` bytes) in Phase 2. All USE_EFFECT sub-dispatch handler literal pools are redirected to `0x088ADF76` in Phase 5 so FE Builder shows the same unified 31-entry list for every promotion item.

**Phase 1** (zero old permission tables): Zeroes all non-Master-Seal item-specific byte-per-class tables in `PROMO_ITEM_TABLES` (items `0x62-0x68`). The MS table (`0x0880CA0F`) is skipped — filled in Phase 2.

**Phase 2** (fill ALL promotion item byte-per-class tables): Fills byte-per-class tables for every promotion item in `PROMO_ITEM_TABLES` (`0x64-0x68, 0x88`). Each is `0x41` bytes initialized to `0x01`, then per-class promo JID (`promo_jid + 1`) is written. This makes the function table handler path return "usable" for all unpromoted classes, and lets FE Builder (which reads these tables directly) see universal permissions.

**Phase 3** (function table entries): Redirects entries 0–1 (items `0x62-0x63` — keys) to Master Seal stub (`0x08057E5C`) for backward compat. Entries 2–6 (items `0x64-0x68`) are **preserved** at their original handler addresses so FE Builder can trace them to their byte-per-class table literals (filled by Phase 2).

**Phase 4** (class-specific tables): Writes `promo_jid+1` for items 0x62-0x69 into the per-class table at `PROMO_CLASS_TABLE_BASE + cls * 0x41 + item_id`. Each class gets a 0x41-byte slot (indexed by item_id). **Class 20 is excluded** because its table at `0x0880D22F` + item offset overflows the 21×0x41 contiguous allocation (`0x0880CD1B`–`0x0880D264`) into the pointer table at `0x0880D270`, corrupting entries 8-10 (`0x081C1E80`, `0x081C1E78`, `0x081C1E74`).

**Phase 4b** (class 20 redirect): Writes `ms_stub_addr` (`0x08057E5C`) to `PROMO_CLASS_FUNCTION_TABLE=0x08057EF0` entry 20 (class 20's handler at `0x08057F40`). This makes class 20 use Master Seal's item-specific handler, which reads `0x0880CA0F[class_id]` (already populated correctly in Phase 2).

**Phases 5-9**: Fix literal pools + permission tables + distribution replacement:
- **Phase 5** (literal pool redirect): Redirects ALL 12 USE_EFFECT and sub-dispatch handler literal pools to the unified 31-entry terminated list at `0x088ADF76`. These include the old sub-dispatch handlers for use_eff `0x19`–`0x1D` (items `0x64`–`0x68`) at `0x08029398`/`0x080293A0`/`0x080293A8`/`0x080293B0`/`0x080293B8`, plus use_eff `0x2E`/`0x2F`/`0x20`/shared sub-dispatch and the main `0x2D` handler. FE Builder reads these literal pools to determine each item's promotion table — all now point to `0x088ADF76`.
- **Phase 5b**: Replaces invalid JID entries `0x7E`/`0x7F` in the terminated class list at `0x088ADF76` with lord class IDs `0x01` and `0x02`.
- **Phase 6**: Sets `use_effect_id=0x2D` on all 10 promotion items (`0x64-0x68, 0x88, 0x8A, 0x97, 0x98, 0x99`), bypassing their original special-case handlers.
- **Phase 7**: Scans UD arrays via `_scan_ud_arrays` and replaces any promotion item ID with Master Seal `0x88`.
- **Phase 8**: Copies Master Seal's item data (icon, name, description, effect) to all other promotion items. Preserves the `number` field (offset 6) for each item.
- **Phase 9**: Full-ROM scan (`0x08800000-0x08FFFFFF`) for GiveItem events (`0x1E` byte, slot 0-3, promo item IDs). Replaces promo items in GiveItem events missed by the UD array scan. Defense-in-depth; vanilla FE8 has no promo items in GiveItem events.

### Key tables for promotion
| Table | Address | Description |
|---|---|---|
| `PROMO_FUNCTION_TABLE_ADDR` | `0x08057DD0` | 19-entry item handler table, entries 0-1 redirect to MS stub after Phase 3; entries 2-6 preserved at original handler addrs |
| `PROMO_ITEM_TABLES` | `0x0880C848`+ | 8 item-specific byte-per-class tables, 0x41 bytes each (`0x62-0x68`, `0x88`) |
| `PROMO_CLASS_TABLE_BASE` | `0x0880CD1B` | 21 class-specific tables, 0x41 bytes each (class 0-20) |
| `PROMO_CLASS_FUNCTION_TABLE` | `0x08057EF0` | 21-entry class handler table |
| Pointer table | `0x0880D270` | Adjacent to class 20 table — must not be overwritten |
| `use_eff` dispatch | `0x08029234` | 256-entry handler table for item use effects |
| byte-per-class table | `0x0880CA0F` | 0x41 bytes (classes 0-64), used by MS stub at `0x08057E5C`, filled by Phase 2 |
| terminated class list | `0x088ADF76` | 31 entries + terminator, used by `use_eff=0x2D` handler (ALL promotion items after Phase 6) |
| pointer structure | `0x088ADFA4` | Count + pointer array for entries beyond byte-per-class table range |

### Handler code structure for function table entries (0x08057E24-0x08057E5C)
All 8 entries follow the same pattern (8 bytes each):
```
4800        LDR r0, [pc, #0]    ; load table address from next 4 bytes
E0XX        B common_handler    ; branch to shared code at 0x08057EBE
.DWORD      table_addr          ; e.g. 0x0880C848 (item 0x62), ..., 0x0880CA0F (item 0x88)
```
The common handler at `0x08057EBE` uses r0 as the permission table base and checks `table[class_id] != 0`. After Phase 3 redirect: entries 0-1 load `0x0880CA0F`, entries 2-6 are preserved (their byte-per-class tables filled by Phase 2), entry 7 loads `0x0880CA0F`.
