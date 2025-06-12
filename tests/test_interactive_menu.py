#!/usr/bin/env python3
"""
Test script for Interactive Menu
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from src.cli.interactive_menu import InteractiveMenu
    print("✅ Successfully imported InteractiveMenu")
    
    # Test instantiation
    menu = InteractiveMenu()
    print("✅ Successfully created InteractiveMenu instance")
    
    # Test banner display
    menu._show_banner()
    print("✅ Successfully displayed banner")
    
    # Test main menu display
    print("\n" + "="*50)
    print("Testing main menu display:")
    print("="*50)
    # Note: This will require user input, so just showing it works
    print("Main menu method exists:", hasattr(menu, '_show_main_menu'))
    
    print("\n✅ All basic tests passed!")
    print("\nTo run the full interactive menu, use: python main.py")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure all dependencies are installed: pip install rich")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()