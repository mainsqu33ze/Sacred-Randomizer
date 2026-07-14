#!/usr/bin/env python3
"""FE8 Randomizer CLI — convenience wrapper.

Run directly:  python fe8_randomizer.py ROM.gba -c config.yaml
Or via pip:    fe8-randomizer ROM.gba -c config.yaml
"""
from fe8.cli import main

if __name__ == '__main__':
    main()
