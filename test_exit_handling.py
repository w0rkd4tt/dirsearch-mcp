#!/usr/bin/env python3
"""Test exit handling in interactive menu"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.cli.interactive_menu import InteractiveMenu

def main():
    print("Testing exit handling...")
    print("You can:")
    print("1. Type 'exit' at any prompt")
    print("2. Type '0' in main menu")
    print("3. Press Ctrl+C anytime")
    print("\nStarting interactive menu...\n")
    
    menu = InteractiveMenu()
    menu.run()

if __name__ == "__main__":
    main()