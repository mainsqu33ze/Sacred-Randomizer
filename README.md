# FE8 Randomizer

Randomizes **Fire Emblem: The Sacred Stones** (FE8U) GBA ROMs.

## Requirements

- Python 3.8+
- `pip install -r requirements.txt`
- An FE8U (Sacred Stones) ROM — not included

## Quick start

```
python fe8_randomizer.py ROM.GBA -c config.yaml -o randomized.gba
python fe8_randomizer.py ROM.GBA --seed 42          # override config seed
python fe8_randomizer.py ROM.GBA --dump > ref.yaml  # print all defaults
```

Without `-o`, output goes to `ROM_randomized.gba`.

## Configuration

All features are controlled by `config.yaml`. Every option has sensible defaults — start with the provided `config.yaml` and tweak what you like.

### Features at a glance

| Section | What it does |
|---|---|---|
| `class_randomization` | Shuffles classes among playable characters |
| `growth_randomization` | Randomizes stat growth rates (character & class) |
| `base_stat_randomization` | Randomizes or swaps base stats |
| `promo_gain_sync` | Syncs promotion stat bonuses between male/female class pairs |
| `item_randomization` | Updates inventories to match new classes |
| `weapon_randomization` | Randomizes weapon stats (MT/HIT/WT/CRT) |
| `weapon_effects` | Adds special effects (poison, nosferatu, etc.) |
| `affinity_randomization` | Randomizes support affinities |
| `promotion_items` | Unifies all promotion items as Master Seals |
| `loot_randomization` | Randomizes items from chests, events, and side objectives |
| `enemy_randomization` | Randomizes generic enemy classes & loadouts on maps |

### class_randomization

```yaml
class_randomization:
  mode: shuffle          # 'shuffle' (permute, no repeats) or 'random' (sample with repeats)
  manakete_count: 1      # max characters that become Manakete (0 = none)
  omit_classes: []       # JID names to exclude, e.g. [NECROMANCER]
  include_soldier: false # Soldier has no promotion; excluded from player pools by default
  palette_mapping: true  # Auto-update palette class table for custom palettes
```

`mode: shuffle` permutes promoted classes among promoted chars, unpromoted among unpromoted, trainees among trainees—no repeats. `mode: random` picks independently per character; multiple chars can share a class.

`manakete_count` overwrites the mode logic for that many characters, giving them `JID.MANAKETE_MYRRH` with Dragonstone+Vulneraries.

Soldier (`JID.SOLDIER`) is excluded from player pools by default because it has no promotion path (`jidPromotion=0`). Set `include_soldier: true` to allow it. Soldier classes can still appear on generic enemies regardless.

`palette_mapping: true` (default) automatically updates the Palette Class Table so randomized characters keep their custom color schemes. When Eirika becomes a Cavalier, she'll still have her pink palette instead of the generic Cavalier blue. Characters without a custom palette entry (Eirika, Ephraim) will borrow one from another character whose palette table matches their new class — e.g., Eirika randomized to Pegasus Knight borrows Vanessa's palette. Set to `false` to disable (characters will use generic class palettes).

### growth_randomization

Controls how fast units gain stats per level-up. You can set modes for **character** growths (affects playable units) and **class** growths (affects generic enemies):

```yaml
growth_randomization:
  character: random       # false | shuffle | random | pool
  class: random           # false | shuffle | random | random_buff | pool | <number>
  class_buff_range: 0.5   # ±range for random_buff mode (e.g. 0.3 = ±30%)
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
| `random_buff` | — | ✅ | Each growth × `1.0 ± random(0, class_buff_range)` |

Class growths affect JIDs 1–128 (all classes including monsters), which primarily impacts generic enemy stats since playable characters use their own growth rates.

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
```

- **`mode: random`**: picks a random usable weapon for each slot. Existing weapons are kept only if the class+rank supports them.
- **`mode: shuffle`**: permutes all weapons across unit definitions without changing the pool.
- Manaketes always get `[Dragonstone, Vulnerary, Vulnerary, empty]`.

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
```

Weights control how often each effect is chosen. Story weapons (Rapier, Sieglinde, etc.) and monster-exclusive items are never affected.

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

Randomizes items from chests, house visits, story events, and side objectives:

```yaml
loot_randomization:
  enabled: false        # true = enable loot randomization
  mode: random          # 'random' or 'shuffle'
```

**Modes:**
- `random`: each loot item is replaced with a random eligible item from the full item pool (weapons, items, stat boosters, keys, etc.). Monster-only items and story-exclusive items are excluded.
- `shuffle`: all loot item IDs across all chapters are collected, permuted, and redistributed — the same pool of items appears, just in different locations.

Scans each chapter's event data for `GiveItem` (`0x1E`) commands, which covers villages, houses, story events, and recruitment rewards.

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
  weapon_upgrade_chance: 25          # % chance per unit to get a weapon tier upgrade
  omit_classes: []                   # JID names to exclude, e.g. [SHAMAN]
  boss_buffs:                        # extra buffs when include_bosses: true
    growths:
      mode: false                    # false | <number> | random_buff | random
      buff_range: 0.3                # ±range for random_buff mode
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
  palette_mapping: true

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
