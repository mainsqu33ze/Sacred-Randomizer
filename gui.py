#!/usr/bin/env python3
"""FE8 Randomizer GUI — convenience wrapper.

Run directly:  python gui.py
"""
from fe8.gui import FE8RandomizerGUI

if __name__ == '__main__':
    app = FE8RandomizerGUI()
    app.mainloop()
