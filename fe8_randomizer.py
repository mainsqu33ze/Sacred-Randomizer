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
    parser.add_argument('--seed', type=int,
                        help='Random seed for reproducible randomization')
    parser.add_argument('--dump', action='store_true',
                        help='Dump current config from ROM and exit')

    args = parser.parse_args()

    if args.dump:
        from fe8rom import ROM, CharacterData, PID
        rom = ROM(args.rom)
        print("# Default config generated from ROM")
        print("seed: 0")
        print("class_randomization:")
        print("  shuffle: true")
        print("  randomize_stats: false")
        print("  preserve_base: true")
        print("  cross_tier_scramble: false")
        print("growth_randomization:")
        print("  character: false")
        print("  class: false")
        print("  mean: null")
        print("  stddev: 10")
        print("  pool_total: null")
        print("base_stat_randomization:")
        print("  character: false")
        print("  class: false")
        print("  cross_tier_scramble: false")
        print("  mean: null")
        print("  stddev: 3")
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
        print("weapon_effects:")
        print("  enabled: false")
        print("  poison: true")
        print("  nosferatu: true")
        print("  eclipse: 1")
        print("  devil: 5")
        print("  stone: 3")
        print("affinity_randomization:")
        print("  enabled: false")
        print("promotion_items:")
        print("  enabled: false")
        print("  master_seal_universal: true")
        print("  replace_distribution: true")
        return

    try:
        with open(args.config) as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        config = {}

    output = apply_config(
        args.rom, config,
        seed=args.seed,
        output_path=args.output)

    print(output)


if __name__ == '__main__':
    main()
