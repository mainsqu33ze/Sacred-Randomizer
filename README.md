# FE8 Randomizer

Randomizes **Fire Emblem: The Sacred Stones** (FE8U) GBA ROMs.

## Requirements

- Python 3.8+
- `pip install -r requirements.txt`

## Usage

```
python fe8_randomizer.py ROM.GBA -c config.yaml -o output.gba
python fe8_randomizer.py ROM.GBA --seed 42          # override config seed
python fe8_randomizer.py ROM.GBA --dump > template.yaml  # print default config
```

Without `-o`, output goes to `ROM_randomized.gba`. You must provide your own FE8U (Sacred Stones) ROM — it is not included.

## Configuration

All features are controlled by `config.yaml`:

| Section | Feature | Modes |
|---|---|---|
| `class_randomization` | Shuffle classes among playable characters | `shuffle`, `randomize_stats`, `preserve_base`, `omit_classes` |
| `growth_randomization` | Randomize growth rates | `false`, `shuffle`, `random`, `pool` |
| `base_stat_randomization` | Randomize base stats | `false`, `shuffle`, `random`, multiplier + `cross_tier_scramble` |
| `item_randomization` | Assign weapons matching new class | `true/false` |
| `weapon_randomization` | Randomize weapon stats (MT/HIT/WT/CRT) | per-stat `false`, `random`, or multiplier |
| `weapon_effects` | Add special effects (poison, nosferatu, etc.) | percent chance + per-effect weights |
| `affinity_randomization` | Randomize character affinities | `true/false` |

## Examples

### class_randomization

Shuffle all playable characters into random classes and scramble class stat spreads within the same tier:

```yaml
class_randomization:
  shuffle: true                 # reassign characters to random classes
  randomize_stats: true         # shuffle base stats across classes in same tier
  preserve_base: true           # keep existing values vs assign random(0,20)
  cross_tier_scramble: false    # true to shuffle across all tiers together
  omit_classes: []              # case-insensitive JID names to exclude from pools
```

Shuffle splits by promotion tier: promoted chars get promoted classes, unpromoted get unpromoted. Trainees (Ross, Amelia, Ewan) shuffle only among trainee classes. One random character becomes a Manakete (`JID.MANAKETE_MYRRH`) with a Dragonstone. `JID.MANAKETE` (14) is excluded from the standard pool and cannot be assigned via shuffle.

When `randomize_stats: true`, each tier's stat arrays are shuffled among classes within that tier — promoted classes exchange stats with promoted, unpromoted with unpromoted, trainees with trainees. Set `cross_tier_scramble: true` to shuffle all classes together regardless of tier.

### growth_randomization

Tight gaussian spread near original values (each growth slightly tweaked):

```yaml
growth_randomization:
  character: random
  class: false
  mean: null          # center each growth on its original value
  stddev: 5           # ~68% of values within ±5 of original
  min: 0
  max: 100
```

Wild variation with a 315-point pool distributed randomly:

```yaml
growth_randomization:
  character: pool
  class: false
  pool_total: 315     # average total across all playable units
  min: 0
  max: 100
```

Characters will have roughly the same total potential, but which stats get the points is completely reshuffled. Use `pool_total: null` to preserve each unit's original total while redistributing.

### base_stat_randomization

Swap stat arrays between classes within the same promotion tier:

```yaml
base_stat_randomization:
  class: shuffle            # swap stat blocks among same-tier classes
  character: false
```

No class ends up with 0 HP — only whole stat blocks are swapped (HP/Pow/Skl/Spd/Def/Res stay together). Promoted ↔ promoted, unpromoted ↔ unpromoted, trainees ↔ trainees. Use `cross_tier_scramble: true` to shuffle across all tiers together.

Scale all stats by 20% for a harder game:

```yaml
base_stat_randomization:
  character: 0.8     # enemies have 80% of their original stats
  class: false
```

Gaussian shuffle centered on original stats, narrow spread:

```yaml
base_stat_randomization:
  character: random
  class: false
  mean: null
  stddev: 2           # typically ±2 from original
```

### weapon_randomization

Scale all weapon might by 1.5x but randomize hit with a wide spread:

```yaml
weapon_randomization:
  enabled: true
  might: 1.5               # scale MT by 1.5x
  hit: random              # randomize hit with gaussian
  weight: false            # leave weight unchanged
  crit: false              # leave crit unchanged
  mean: null
  hit_stddev: 25           # wide spread on hit
  min_hit: 20
  max_hit: 100
```

Fully gaussian — every stat randomized with per-stat stddev:

```yaml
weapon_randomization:
  enabled: random
  might_stddev: 3
  hit_stddev: 20
  weight_stddev: 3
  crit_stddev: 8
  min_might: 1
  max_might: 25
```

Staves are always skipped for might randomization (staff might stays 0).

### weapon_effects

Poison is everywhere, eclipse is a once-in-a-run discovery:

```yaml
weapon_effects:
  enabled: 30        # 30% per weapon to gain an effect
  poison: 40         # weight 40 — appears often
  nosferatu: 10
  eclipse: 1         # weight 1 — extremely rare
  devil: 8
  stone: 3
```

Weapons that already have an effect (e.g., Poison Sword) can be overwritten with a different random effect. Story weapons (Rapier, Sieglinde, Siegmund, Reginleif) and monster-exclusive items are never affected.

### affinity_randomization

```yaml
affinity_randomization:
  enabled: true
```

Assigns a random affinity (fire, thunder, wind, ice, light, dark, or anima — values 1–7) to every playable character. Affinities affect support bonuses.

### item_randomization

```yaml
item_randomization:
  enabled: true
```

After class randomization, each unit's inventory is updated to include weapons their new class can use. Existing weapons are kept only if the unit's weapon rank supports them. Manaketes get `[Dragonstone, Vulnerary, Vulnerary, empty]`.

## Full reference config

```yaml
# FE8 Randomizer — every available option with defaults

seed: 0

class_randomization:
  shuffle: true                 # reassign characters to random classes
  randomize_stats: false        # shuffle base stats across classes in same tier
  preserve_base: true           # keep existing values vs assign random(0,20)
  cross_tier_scramble: false    # allow shuffling across all tiers together
  omit_classes: []              # case-insensitive JID names to exclude from pools

growth_randomization:
  character: false              # false, shuffle, random, or pool
  class: false                  # false, shuffle, random, or pool
  min: 0                        # clamp floor for random/pool modes
  max: 100                      # clamp ceiling for random/pool modes
  mean: null                    # gaussian center (null = original value)
  stddev: 10                    # gaussian standard deviation
  pool_total: null              # total growth pool for pool mode (null = original sum)

base_stat_randomization:
  character: false              # false, shuffle, random, or multiplier
  class: false                  # false, shuffle, random, or multiplier
  cross_tier_scramble: false    # shuffle across all tiers together (class: shuffle only)
  mean: null                    # gaussian center (null = original value)
  stddev: 3                     # gaussian standard deviation

item_randomization:
  enabled: true                 # update unit inventories to match new classes

weapon_randomization:
  enabled: false                # truthy gate to enable weapon stat changes
  might: true                   # per-stat: false to skip, true for gaussian,
  hit: true                     #           or a multiplier number
  weight: true
  crit: true
  mean: null                    # gaussian center (null = original value)
  stddev: 5                     # global gaussian stddev (used if per-stat not set)
  might_stddev: 3               # per-stat stddev overrides
  hit_stddev: 20
  weight_stddev: 3
  crit_stddev: 5
  min_might: 1                  # per-stat clamp bounds
  max_might: 20
  min_hit: 30
  max_hit: 120
  min_weight: 1
  max_weight: 20
  min_crit: 0
  max_crit: 30

weapon_effects:
  enabled: false                # false to disable, or percent chance (e.g., 25)
  poison: true                  # true = weight 1, number = custom weight,
  nosferatu: true               # false = excluded from pool
  eclipse: 1
  devil: 5
  stone: 3

affinity_randomization:
  enabled: false                # assign random affinity (1–7) to all playables
```

