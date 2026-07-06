#!/usr/bin/env python3
"""FE8 Randomizer CLI - Randomize Fire Emblem: The Sacred Stones GBA ROM."""

import argparse
import sys
import yaml
from randomizer import apply_config


def main():
    parser = argparse.ArgumentParser(
        description='FE8 (Sacred Stones) ROM Randomizer',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  fe8_randomizer.py ROM.gba -c config.yaml -o output.gba
  fe8_randomizer.py ROM.gba -c config.yaml --seed 42
  fe8_randomizer.py ROM.gba -c config.yaml --seed 42 --dump > dump.txt
        """)

    parser.add_argument('rom', help='Path to FE8U ROM file')
    parser.add_argument('-c', '--config', default='config.yaml',
                        help='YAML configuration file (default: config.yaml)')
    parser.add_argument('-o', '--output',
                        help='Output ROM path (default: input_randomized.gba)')
    parser.add_argument('-s', '--seed', type=int,
                        help='Random seed for reproducible randomization')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Show detailed progress messages')
    parser.add_argument('--dump', action='store_true',
                        help='Dump current config from ROM and exit')

    args = parser.parse_args()

    if args.dump:
        from fe8rom import ROM, CharacterData, PID
        rom = ROM(args.rom)
        print("# Default config generated from ROM")
        print("seed: 0")
        print("")
        print("# --- Classes ---")
        print("# Shuffles which class each playable character belongs to.")
        print("# Characters keep their original stats unless stat randomization is also enabled.")
        print("class_randomization:")
        print("  mode: shuffle")
        print("  manakete_count: 1")
        print("  omit_classes: []")
        print("  # Soldier has no promotion; excluded from player pools by default")
        print("  include_soldier: false")
        print("  # Auto-update palette class table so characters keep custom palettes")
        print("  palette_mapping: true")
        print("")
        print("# --- Recruitment Order ---")
        print("# Randomizes which character is recruited in which story slot by")
        print("# swapping CharacterData blocks among all 33 playable PIDs.")
        print("# PaletteClassTable and PaletteIndexTable are swapped in lockstep")
        print("# so each character's custom palette colours follow their data.")
        print("# The trainee auto-promotion table is rebuit to point at whichever")
        print("# PIDs now hold trainee classes (Ross, Amelia, Ewan).")
        print("recruitment_randomization:")
        print("  enabled: false")
        print("  # 'pre' = swap data first, then randomize classes/stats/growths")
        print("  # 'post' = randomize classes/stats/growths first, then swap data")
        print("  mode: pre")
        print("  # When true, only swap within the same class tier (trainee/unpromoted/promoted)")
        print("  # Prevents a prepromote from appearing in an early-game unpromoted slot")
        print("  preserve_tier: true")
        print("")
        print("# --- Growth Rates ---")
        print("# Randomizes how fast characters grow in each stat as they level up.")
        print("#   character: false | shuffle | random | pool")
        print("#   class: false | shuffle | random | random_buff | pool | <number>")
        print("#   class_buff_range: 0.5   # +/- fractional range for random_buff mode")
        print("growth_randomization:")
        print("  character: false")
        print("  class: false")
        print("  class_buff_range: 0.5")
        print("  min: 0")
        print("  max: 100")
        print("  mean: null")
        print("  stddev: 10")
        print("  pool_total: null")
        print("")
        print("# --- Base Stats ---")
        print("# Randomizes the starting stats of characters or classes.")
        print("base_stat_randomization:")
        print("  character: false")
        print("  class: false")
        print("  preserve_base: true")
        print("  shuffle_con_mov: true")
        print("  cross_tier_scramble: false")
        print("  mean: null")
        print("  stddev: 3")
        print("  con:")
        print("    enabled: true")
        print("    min: 1          # class base Con minimum")
        print("    player_min: 1   # player unit Con minimum")
        print("    stddev: 3")
        print("")
        print("# --- Items (Weapons + Inventory) ---")
        print("# When classes are shuffled, characters get weapons they can actually use.")
        print("# Ballista items (IDs 0x35-0x37) are excluded from all randomization pools")
        print("# by default. Set include_ballista_items: true to allow them in weapon pools,")
        print("# loot, event-given items, and enemy inventories.")
        print("item_randomization:")
        print("  enabled: true")
        print("  mode: random")
        print("  randomize_events: false")
        print("  include_ballista_items: false")
        print("")
        print("# --- Weapon Stats ---")
        print("# Randomizes Might, Hit, Weight, and/or Crit of all weapons.")
        print("weapon_randomization:")
        print("  enabled: false")
        print("  might: true")
        print("  hit: true")
        print("  weight: true")
        print("  crit: true")
        print("  mean: null")
        print("  stddev: 5")
        print("  might_stddev: 3")
        print("  hit_stddev: 20")
        print("  weight_stddev: 3")
        print("  crit_stddev: 5")
        print("  min_might: 1")
        print("  max_might: 20")
        print("  min_hit: 30")
        print("  max_hit: 120")
        print("  min_weight: 1")
        print("  max_weight: 20")
        print("  min_crit: 0")
        print("  max_crit: 30")
        print("")
        print("# --- Weapon Effects ---")
        print("# Randomly adds special effects (Poison, Nosferatu, etc.) to weapons.")
        print("weapon_effects:")
        print("  enabled: false")
        print("  poison: true")
        print("  nosferatu: true")
        print("  eclipse: 1")
        print("  devil: 5")
        print("  stone: 3")
        print("")
        print("# --- Affinities ---")
        print("# Randomizes each character's support affinity.")
        print("affinity_randomization:")
        print("  enabled: false")
        print("")
        print("# --- Promotion Items ---")
        print("# Makes all promotion items (Master Seals, Heaven Seals, etc.) work")
        print("# like Master Seals: usable by any unpromoted class on any unpromoted character.")
        print("promotion_items:")
        print("  enabled: true")
        print("  master_seal_universal: true")
        print("  replace_distribution: true")
        print("")
        print("# --- Loot Randomization ---")
        print("# Randomizes items from chests, house visits, story events, and side objectives.")
        print("# 'random' = each item replaced with a random eligible item.")
        print("# 'shuffle' = all items permuted among drop locations (same pool, different order).")
        print("loot_randomization:")
        print("  enabled: false")
        print("  mode: random")
        print("")
        print("# --- Enemy Randomization (Generic Units) ---")
        print("# Randomizes generic enemy classes and items with terrain-safe movement grouping.")
        print("enemy_randomization:")
        print("  enabled: false")
        print("  randomize_classes: true")
        print("  randomize_items: true")
        print("  include_monsters: false")
        print("  randomize_monster_classes: false")
        print("  include_bosses: false")
        print("  weapon_upgrade_chance: 25")
        print("  omit_classes: []")
        print("  boss_buffs:")
        print("    growths:")
        print("      mode: false")
        print("      buff_range: 0.3")
        print("      mean: null")
        print("      stddev: 10")
        print("    base_stats:")
        print("      mode: false")
        print("      buff_range: 0.3")
        print("      mean: null")
        print("      stddev: 3")
        print("    max_weapon_ranks: true")
        return

    try:
        with open(args.config) as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        config = {}

    output = apply_config(
        args.rom, config,
        seed=args.seed,
        output_path=args.output,
        verbose=args.verbose)

    print(output)


if __name__ == '__main__':
    main()
