# Sacred Randomizer

An extremely fast, efficient randomizer for **Fire Emblem: The Sacred Stones** (FE8U) GBA ROMs. Processes a 16 MB ROM in under a second with zero dependencies beyond Python itself.

## Requirements

- Python 3.8+
- An FE8U (Sacred Stones) ROM — not included

## Installation

```bash
git clone https://github.com/yourname/FE8-Custom-Randomizer.git
cd FE8-Custom-Randomizer
pip install .
```

This installs the `sacred-randomizer` CLI command and all dependencies (`pyyaml`, `tqdm`).

For development (editable install + test dependencies):

```bash
pip install -e ".[dev]"
```

## Quick start

**New users** — the fastest way to get a randomized ROM:

```bash
sacred-randomizer Fire_Emblem_8.GBA -c config.yaml
```

This uses the included `config.yaml` which gives a fun, balanced experience out of the box. The randomized ROM is saved as `Fire_Emblem_8_randomized.gba` alongside the original.

**Common variations:**

```bash
# Use a specific seed (reproducible)
sacred-randomizer Fire_Emblem_8.GBA -c config.yaml -s 42

# Custom output path
sacred-randomizer Fire_Emblem_8.GBA -c config.yaml -o my_randomized.gba

# See what the randomizer is doing step-by-step
sacred-randomizer Fire_Emblem_8.GBA -c config.yaml -v

# Print the full default config to a file for editing
fe8-randomizer Fire_Emblem_8.GBA --dump > my_config.yaml
```

A `.txt` report is generated alongside the output ROM with full details of class changes, weapon effects, event item changes, and per-unit growth rate totals.

**Tip:** Edit `config.yaml` to enable/disable features. Every option has sensible defaults — start with the provided file and tweak what you like. See [Configuration](#configuration) below for all options.

## GUI

A Tkinter GUI is also available for point-and-click configuration:

```bash
python gui.py
```

The GUI covers all common options across tabbed panels (class randomization, growth rates, base stats, weapons, items, enemies, and boss buffs), but has a few **limitations** compared to using a `config.yaml` directly:

- Cannot produce a `--dump` of the default config.
- Seed cannot be overridden via CLI flag (set it inside the window).
- Requires a display (Tkinter, not headless-friendly).

For full control, use the CLI with a `config.yaml`.

## Configuration

All features are controlled by `config.yaml`. Every option has sensible defaults — start with the provided `config.yaml` and tweak what you like.

### Features at a glance

| Section | What it does |
| --- | --- |
| `class_randomization` | Shuffles classes among playable characters (supports gender-locking) |
| `recruitment_randomization` | Shuffles which character is recruited in each story slot |
| `growth_randomization` | Randomizes stat growth rates (character & class) |
| `base_stat_randomization` | Randomizes or swaps base stats |
| `promo_gain_sync` | Syncs promotion stat bonuses between male/female class pairs |
| `item_randomization` | Updates inventories to match new classes |
| `weapon_randomization` | Randomizes weapon stats (MT/HIT/WT/CRT) |
| `weapon_effects` | Adds special effects (poison, nosferatu, etc.) |
| `affinity_randomization` | Randomizes support affinities |
| `promotion_items` | Unifies all promotion items as Master Seals |
| `loot_randomization` | Randomizes items from GiveItem events (houses, villages, story events, recruitment) **and** treasure chests |
| `enemy_randomization` | Randomizes generic enemy classes & loadouts on maps |


### Default Settings Quick-Reference
When running the randomizer with an untouched `config.yaml`, the default profile provides a **fun, balanced gameplay experience** with the following baseline behavior:

* **Playable Characters:** Classes are shuffled (unpromoted to unpromoted, promoted to promoted) without duplication. Custom colors/palettes are intelligently mapped to their new classes. A single unit is guaranteed to become a Manakete.
* **Map Enemies:** Generic enemy classes and inventories are randomized. Their classes respect original map placement boundaries (e.g., flying units replace flying units) so they don't get trapped on mountains or oceans. Bosses are left vanilla.
* **Items & Mechanics:** Inventories auto-adjust so randomized units always spawn with weapons they can actually wield. All promotion items are universally mapped to function as **Master Seals** for ease of progression.
* **Stats & Growths:** Character growths, base stats, weapon values, and event loot locations remain identical to vanilla rules. Chest scanning via Location Events is disabled (entries were false positives).

### class_randomization

```yaml
class_randomization:
  mode: shuffle          # 'shuffle' (permute, no repeats) or 'random' (sample with repeats)
  manakete_count: 1      # max characters that become Manakete (0 = none)
  omit_classes: []       # JID names to exclude, e.g. [NECROMANCER]
  include_soldier: false # Soldier has no promotion; excluded from player pools by default
  gender_lock: false     # Lock classes to same gender as character
  palette_mapping: true       # Auto-update palette class table for custom palettes
  portrait_palettes: true     # Generate class palette from character's portrait colors
```

`mode: shuffle` permutes promoted classes among promoted chars, unpromoted among unpromoted, trainees among trainees—no repeats. `mode: random` picks independently per character; multiple chars can share a class.

`manakete_count` overwrites the mode logic for that many characters, giving them `JID.MANAKETE_MYRRH` with Dragonstone+Vulneraries.

Soldier (`JID.SOLDIER`) is excluded from player pools by default because it has no promotion path (`jidPromotion=0`). Set `include_soldier: true` to allow it. Soldier classes can still appear on generic enemies regardless.

`palette_mapping: true` (default) automatically updates the Palette Class Table so randomized characters keep their custom color schemes. When Eirika becomes a Cavalier, she'll still have her pink palette instead of the generic Cavalier blue. Characters without a custom palette entry (Eirika, Ephraim) will borrow one from another character whose palette table matches their new class — e.g., Eirika randomized to Pegasus Knight borrows Vanessa's palette. Set to `false` to disable (characters will use generic class palettes).

`portrait_palettes: true` (default) when set to `true`, generates a unique palette for each randomized character by mapping their original character portrait colors onto their new class's palette template. Uses color distance to match each template color to the closest color in the character's original portrait palette set, preserving the character's overall color identity. Requires `palette_mapping: true` to be effective. Generated palettes are stored as new entries in the ROM's palette table and don't affect any existing palette data. Set to `false` to disable (characters will use class-default palettes after palette_mapping).

`gender_lock: false` (default) when set to `true`, restricts class randomization so each character only receives classes appropriate to their gender. Gender is inferred from the character's original class before randomization. Classes with male/female variants (e.g., Cavalier/Cavalier_F) are automatically swapped to the correct variant. Gender-exclusive classes (Fighter, Warrior, Berserker, Pirate, Monk, Priest, Thief, Journeyman, Pupil for males; Cleric, Troubadour, Valkyrie, Dancer, Recruit, Pegasus Knight, Falcon Knight for females) are only assigned to characters of that gender. When `manakete_count > 0`, Manakete assignments are limited to female-class characters. Also applies to bosses when `include_bosses: true` under `enemy_randomization`.

### recruitment_randomization

Shuffles which character's identity (stats, growths, class, portrait) occupies each story recruit slot:

```yaml
recruitment_randomization:
  enabled: false           # true = shuffle character data among playable PIDs
  mode: pre                # 'pre' or 'post' — when to swap relative to class/stats
  preserve_tier: true      # promote↔promoted only; prevent prepromotes in early slots
```

When enabled, the 33 playable CharacterData blocks (PIDs 1–34, excluding unused PID 27) are permuted. Each PID slot keeps its own `id` self-reference byte, so the game still knows which characters are the main lords (PID 1 = Eirika, PID 15 = Ephraim) for game-over and story purposes — but all other data follows the swapped block.

**`mode: pre`** (default): swap first, then randomize classes/stats/growths into the swapped arrangement. Each PID slot gets fresh randomized stats based on whoever ended up there. Eirika's slot gets the swapped-in character's personality and appearance but with stats appropriate to the slot's position in the story.

**`mode: post`**: randomize classes/stats/growths first, then swap. Each character carries their pre-rolled class and stats to their new PID slot. Useful if you want a specific set of stats (e.g., those from the seed) to follow the character rather than the slot.

**`preserve_tier: true`** (default): when swapping, characters are grouped by class tier (trainee, unpromoted, promoted) so a prepromote like Seth (promoted) only swaps with other promoted units. This prevents Seth's stats from appearing in an early-game unpromoted slot like Franz's. Disable (`false`) for full chaos — any character can end up in any slot.

**Palette lockstep:** PaletteClassTable and PaletteIndexTable entries (7 bytes each per PID) are swapped alongside the CharacterData so each character's custom palette colours follow their portrait and data to the new PID slot.

**Trainee promotion table:** After a recruitment shuffle, the 3-entry trainee table at `0x08207044` (Ross, Amelia, Ewan) is remapped to whichever PID slots now hold trainee classes. Entries for PIDs that no longer have a trainee class are zeroed out.

**Unconditional guarantees (always active regardless of settings):**
- **PID 1 (Eirika), PID 15 (Ephraim):** These are the main lords — game over if either falls in battle. They are **not** restricted to lord classes and can be assigned any class after the swap.
- **Trainee enforcement:** PIDs 7, 18, 24 (Ross, Amelia, Ewan) always have trainee classes regardless of what data swaps into them.
- **Unpromoted enforcement:** 18 story-critical PID slots (1, 3, 4, 5, 6, 8, 9, 10, 12, 13, 14, 15, 16, 17, 19, 20, 25, 31) are always kept as unpromoted classes to preserve early-game balance.
- **Cutscene weapon guarantee:** PID 2 (Seth) is always given an equippable combat weapon for chapters 0 and 4 to prevent cutscene crashes. PID 13 (Artur) also gets the guarantee for chapter 4.

### growth_randomization

Controls how fast units gain stats per level-up. You can set modes for **character** growths (affects playable units) and **class** growths (affects all instances of each class — both player and enemy):

```yaml
growth_randomization:
  character: random       # false | shuffle | random | pool
  class: random           # false | shuffle | random | random_buff | pool | <number>
  class_buff_range: 0.5   # range for random_buff mode (e.g. 0.3 = stats scaled by 1.0–1.3)
  min: 0                  # clamp floor
  max: 100                # clamp ceiling
  mean: null              # gaussian center (null = original value)
  stddev: 10              # gaussian standard deviation
  pool_total: null        # for 'pool' mode (null = preserve original total)
```

**Modes:**
| Mode | Character | Class | Effect |
|---|---|---|---|
| `false` | ✅ | ✅ | Keep vanilla |
| `shuffle` | ✅ | ✅ | Permute the 7 growth values within each unit/class |
| `random` | ✅ | ✅ | Gaussian with optional mean/stddev |
| `pool` | ✅ | ✅ | Distribute `pool_total` across stats randomly |
| `<number>` | — | ✅ | Scale all growths by factor (e.g. `1.3` = +30%) |
| `random_buff` | — | ✅ | Each growth × `1.0 + random(0, class_buff_range)` |

Class growths affect all instances of each class (JIDs 1–128 including monsters). Since playable characters also belong to classes, class growth changes affect both player and enemy units using that class.

### base_stat_randomization

Swap or randomize starting stats for characters and/or classes:

```yaml
base_stat_randomization:
  character: false        # false | shuffle | random | <multiplier>
  class: false            # false | shuffle | random | <multiplier>
  preserve_base: true     # class=shuffle: swap values vs assign random(0,20)
  shuffle_con_mov: true   # class=shuffle: include Con/Mov in the swap
  cross_tier_scramble: false  # class=shuffle: mix all tiers together
  mean: null              # gaussian center (null = original value)
  stddev: 3               # gaussian standard deviation
  con:                    # separate Con control — affects ALL modes (scale/shuffle/random)
    enabled: true         # false = never modify Con in any mode
    min: 1                # minimum Con for class bases
    player_min: 1         # minimum Con for player unit bases
    stddev: 3             # stddev for Con (separate from global stddev)
```

Scale all player stats down for a harder game:
```yaml
character: 0.8   # 80% of original stats
```

Shuffle stat blocks between same-tier classes:
```yaml
class: shuffle
cross_tier_scramble: false   # keeps promoted/unpromoted/trainee pools separate
```

When `con.enabled: false`, Con is preserved in **all** modes (scale, shuffle, random). In shuffle mode this overrides `shuffle_con_mov` for Con only — Mov is still controlled by `shuffle_con_mov`.

Randomize Con independently with its own minimum and spread:
```yaml
base_stat_randomization:
  character: false
  class: random
  con:
    enabled: true
    min: 3            # class Con never below 3
    player_min: 1     # player Con still allowed as low as 1
    stddev: 5         # wider spread than the global stddev=3
```

### promo_gain_sync

Always active (no config toggle). Synchronizes the class promotion stat bonuses (`promotionHp/Pow/Skl/Spd/Def/Res`) between every male/female class pair — for each stat, whichever variant has the higher bonus "wins" and both classes get that value.

Class pairs synced: Cavalier/Cavalier_F, General/General_F, Hero/Hero_F, Myrmidon/Myrmidon_F, Swordmaster/Swordmaster_F, Assassin/Assassin_F, Mage/Mage_F, Wyvern_Rider/Wyvern_Rider_F, and all other gendered playable class pairs (25 pairs total). This ensures that promoting into Hero vs Hero_F gives identical stat bonuses regardless of gender.

### item_randomization

After class randomization, updates inventories so units get weapons their new class can use:

```yaml
item_randomization:
  enabled: true
  mode: random              # 'random' = pick from weapon pools; 'shuffle' = permute all items
  randomize_events: false   # also randomize GiveItem events (slow)
  include_ballista_items: false   # true = allow ballista items (0x35–0x37) in all pools
```

- **`mode: random`**: picks a random usable weapon for each slot. Existing weapons are kept only if the class+rank supports them.
- **`mode: shuffle`**: permutes all weapons across unit definitions without changing the pool.
- Manaketes always get `[Dragonstone, Vulnerary, Vulnerary, empty]`.

**Note on `randomize_events` + `loot_randomization`:** These are independent features that both affect GiveItem events. `randomize_events` replaces weapon-type items in GiveItem events using weapon pools (weapons only). `loot_randomization` replaces *all* items in GiveItem events using the full item pool (weapons, stat boosters, keys, etc.) and also covers chest items. If both are enabled, GiveItem events are patched twice — first by `randomize_events` (weapons only), then by `loot_randomization` (full pool overwriting the previous result). For most use cases, enabling `loot_randomization` alone is sufficient; `randomize_events` is useful when you want weapon-specific randomization of events without touching chests or non-weapon items.

**Weapon rank transfer:** When a character's class changes, weapon ranks are adjusted to match the new class. Ranks for weapon types the new class can't use are zeroed out. For supported types, the character keeps whichever is higher — their existing rank or the class's base. Additionally, if the character had their highest rank in a type they can no longer use, that rank is transferred to their weakest supported type, so Eirika's S-rank swords aren't wasted when she becomes a Mage.

**Prf weapon type fix:** When Eirika or Ephraim is randomized to a new class, their personal weapons (Rapier `0x09` / Sieglinde `0x85` for Eirika; Reginleif `0x78` / Siegmund `0x92` for Ephraim) get their `weapon_type` byte updated to a type their new class can wield. The Ability 4 byte (offset `0x21`) is set to `0x0A` (Eirika lock) or `0x14` (Ephraim lock), making weapons check PID instead of class. Lord-class attribute lock bits from the class data are also copied into the character's PersonalInfo attributes (offset `0x28`) — Eirika gets bits 17+28 (`0x10020000`), Ephraim gets bit 29 (`0x20000000`) — so the equipped character always passes the item lock check regardless of their current class. This ensures lords can always use their signature weapons even after class randomization.

**Cutscene combat guarantee (always on):** After all randomization completes, Seth (PID 2) and Artur (PID 13) are checked for an equippable combat weapon (sword/lance/axe/bow/anima/light/dark) in their chapter 0 and chapter 4 unit placement arrays. If only staves or empty slots are found, a combat weapon is forced into the first available slot. This includes the hardcoded prologue cutscene battle array at `0x088B3F68` which is not discoverable via normal chapter data scanning. Staff (type 4) is explicitly excluded from the weapon selection to prevent replacing a staff with another staff. No config toggle — always active to prevent cutscene softlocks.

### weapon_randomization

Randomizes numeric stats (Might / Hit / Weight / Crit) independently per stat:

```yaml
weapon_randomization:
  enabled: true             # false to skip all weapon stat changes
  might: true               # false=skip, true=gaussian, <number>=multiplier
  hit: true
  weight: true
  crit: true
  mean: null                # gaussian center (null = original value)
  stddev: 5                 # global stddev (used if per-stat not set)
  might_stddev: 3           # per-stat overrides
  hit_stddev: 20
  weight_stddev: 3
  crit_stddev: 5
  min_might: 1              # clamp bounds per stat
  max_might: 20
  min_hit: 30
  max_hit: 120
  min_weight: 1
  max_weight: 20
  min_crit: 0
  max_crit: 30
```

Staves are always skipped (staff might stays 0).

Scale all weapon MT by 1.5× while randomizing hit widely:
```yaml
weapon_randomization:
  enabled: true
  might: 1.5
  hit: random
  weight: false
  crit: false
  hit_stddev: 25
  min_hit: 20
  max_hit: 100
```

### weapon_effects

Adds special effects to weapons at a configurable chance:

```yaml
weapon_effects:
  enabled: 30          # percent chance per weapon to gain an effect (0 or false = off)
  poison: 40           # relative weight — higher = more likely
  nosferatu: 10
  eclipse: 1           # extremely rare
  devil: 8
  stone: 3
  brave: 5             # independent per-item % chance — adds Brave (extra attack) via attribute bit
  reaver: 3            # independent per-item % chance — adds Reaver (reverses weapon triangle) via attribute bit
```

Weights control how often each effect is chosen from the effect pool (poison/nosferatu/eclipse/devil/stone). Brave and reaver are **independent** — each weapon rolls separately against its `%` chance, orthogonal to the effect pool. A weapon can gain brave, reaver, and an effect simultaneously. Story weapons (Rapier, Sieglinde, etc.) and monster-exclusive items are never affected.

### affinity_randomization

```yaml
affinity_randomization:
  enabled: true
```

Assigns a random affinity (Fire, Thunder, Wind, Ice, Light, Dark, or Anima — values 1–7) to every playable character. Affinities affect support bonuses.

### promotion_items

Unifies all promotion items to work as universal Master Seals:

```yaml
promotion_items:
  enabled: true                    # true = apply Master Seal logic
  master_seal_universal: true      # any unpromoted class can promote
  replace_distribution: true       # replace chests/drops/events with Master Seal (0x88)
```

When enabled, every promotion item (Heaven Seal, Ocean Seal, etc.) behaves like a Master Seal — any unpromoted class can use it and the game's internal class-eligibility tables are patched. Disable `replace_distribution` to keep the original promo item types in chests and drops.

### loot_randomization

Randomizes items from GiveItem events (houses, villages, story events, recruitment rewards):

```yaml
loot_randomization:
  enabled: false        # true = enable loot randomization
  mode: random          # 'random' or 'shuffle'
```

**Modes:**
- `random`: each loot item is replaced with a random eligible item from the full item pool (weapons, items, stat boosters, keys, etc.). Monster-only items and story-exclusive items are excluded.
- `shuffle`: all loot item IDs across all chapters are collected, permuted, and redistributed — the same pool of items appears, just in different locations.

Scans each chapter's event data for `GiveItem` (`0x1E`) commands (villages, houses, story events, recruitment rewards) **and** type-`0x07` CHES entries in `locationBasedEvents` for treasure chests. **40 non-gold chest items** across 17 chapters/route-variants are randomized. Gold chests (items with `givenItem=0x77`, 7 total) are skipped — the gold amount is preserved.

**Excluded item IDs from loot pools:** `0x7D`, `0x7E`, `0x7F`, `0x80`, `0xA2`, `0xA3`, `0xA4`, `0xA5` — these are map-spawn-only deployable items not meant for loot tables. They join the existing exclusions: monster-blocked items (now includes dummy items `0x3D`, `0x44`), story-exclusive items (Rapier etc.), promotion items, ballista items (`0x35`–`0x37`, unless `include_ballista_items: true`), and dummy item `0x8A`.

### enemy_randomization

Randomizes generic enemy classes and loadouts per map:

```yaml
enemy_randomization:
  enabled: true
  randomize_classes: true            # randomize generic enemy classes
  randomize_items: true              # assign weapons compatible with new class
  randomize_monster_classes: false   # true = randomize monster enemies too
  include_monsters: false            # true = let enemies become monster classes
  include_bosses: false              # true = include bosses (PIDs 0x40–0x63, etc.)
  gender_lock: false                 # true = lock boss classes to same gender as boss
  weapon_upgrade_chance: 25          # % chance per unit to get a weapon tier upgrade
  omit_classes: []                   # JID names to exclude, e.g. [SHAMAN]
  boss_buffs:                        # extra buffs when include_bosses: true
    growths:
      mode: false                    # false | <number> | random_buff | random
      buff_range: 0.3                # range for random_buff mode
      mean: null
      stddev: 10
    base_stats:
      mode: false                    # false | <number> | random_buff | random
      buff_range: 0.3
      mean: null
      stddev: 3
    max_weapon_ranks: true           # S-rank for all usable weapon types
```

Classes are grouped by **movement category** (flyer / water / mountain / foot) so enemies placed on mountains or water tiles can still navigate their terrain.

**Exclusions:**
- Manakete, Bard, Dancer, Fleet, Phantom, Demon King, and JIDs 0x67–0x7B never appear in enemy pools.
- Final boss (PID 0xBE) is always excluded regardless of `include_bosses`.
- Lords and trainees are excluded.
- **Staves-only classes** (Cleric, Priest, Troubadour) are automatically filtered out — they can't deal damage.
- Set `include_monsters: true` to allow monster classes in the pool. Set `randomize_monster_classes: true` to also randomize enemies that start as monsters.

**Boss buffs** apply when `include_bosses: true` and a boss PID is in scope. Growth and base stats can be scaled by a multiplier (`1.5`), randomly buffed per-stat (`random_buff`), or fully rerolled with gaussian (`random`). `max_weapon_ranks: true` sets weapon experience to 251 (S-rank) for every weapon type the boss's class can use, and zeroes out weapon types the class can't use — so the boss only keeps ranks relevant to their randomized class.

## Full reference config

```yaml
# FE8 Randomizer — every option with defaults

seed: 0

class_randomization:
  mode: shuffle
  manakete_count: 1
  omit_classes: []
  include_soldier: false
  gender_lock: false
  palette_mapping: true
  portrait_palettes: true

recruitment_randomization:
  enabled: false
  mode: pre
  preserve_tier: true

growth_randomization:
  character: false
  class: false
  class_buff_range: 0.5
  min: 0
  max: 100
  mean: null
  stddev: 10
  pool_total: null

base_stat_randomization:
  character: false
  class: false
  preserve_base: true
  shuffle_con_mov: true
  cross_tier_scramble: false
  mean: null
  stddev: 3
  con:
    enabled: true
    min: 1
    player_min: 1
    stddev: 3

item_randomization:
  enabled: true
  mode: random
  randomize_events: false
  include_ballista_items: false

weapon_randomization:
  enabled: false
  might: true
  hit: true
  weight: true
  crit: true
  mean: null
  stddev: 5
  might_stddev: 3
  hit_stddev: 20
  weight_stddev: 3
  crit_stddev: 5
  min_might: 1
  max_might: 20
  min_hit: 30
  max_hit: 120
  min_weight: 1
  max_weight: 20
  min_crit: 0
  max_crit: 30

weapon_effects:
  enabled: false
  poison: 2
  nosferatu: 3
  eclipse: 1
  devil: 5
  stone: 1
  brave: 0
  reaver: 0

affinity_randomization:
  enabled: false

promotion_items:
  enabled: true
  master_seal_universal: true
  replace_distribution: true

loot_randomization:
  enabled: false
  mode: random

enemy_randomization:
  enabled: true
  randomize_classes: true
  randomize_items: true
  randomize_monster_classes: false
  include_monsters: false
  include_bosses: false
  gender_lock: false
  weapon_upgrade_chance: 25
  omit_classes: []
  boss_buffs:
    growths:
      mode: false
      buff_range: 0.3
      mean: null
      stddev: 10
    base_stats:
      mode: false
      buff_range: 0.3
      mean: null
      stddev: 3
    max_weapon_ranks: true
```
