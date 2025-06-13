#!/usr/bin/env python3
"""
Test script to verify wordlist path handling fix
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.settings import Settings
from src.cli.interactive_menu import InteractiveMenu


def test_wordlist_paths():
    """Test wordlist path handling"""
    print("Testing wordlist path handling fix...\n")
    
    # Create settings instance
    settings = Settings()
    
    # Show current path structure
    print("Current paths structure:")
    print(f"settings.paths['wordlists'] = {settings.paths['wordlists']}")
    print(f"Type: {type(settings.paths['wordlists'])}")
    
    # Test the path resolution
    if isinstance(settings.paths['wordlists'], dict):
        base_path = settings.paths['wordlists'].get('base', settings.paths['wordlists'].get('general', 'wordlists'))
        print(f"\nResolved base path: {base_path}")
        
        # Check if directory exists
        wordlist_dir = Path(base_path)
        if wordlist_dir.exists():
            print(f"✅ Directory exists: {wordlist_dir}")
            
            # List some wordlists
            txt_files = list(wordlist_dir.glob('*.txt'))[:5]
            if txt_files:
                print(f"\nFound {len(list(wordlist_dir.glob('*.txt')))} wordlists, showing first 5:")
                for f in txt_files:
                    print(f"  - {f.name}")
            else:
                print("⚠️  No .txt files found in wordlist directory")
        else:
            print(f"❌ Directory does not exist: {wordlist_dir}")
    else:
        print(f"\nPath is a string: {settings.paths['wordlists']}")
    
    # Test InteractiveMenu initialization
    print("\n\nTesting InteractiveMenu initialization...")
    try:
        menu = InteractiveMenu()
        menu.settings = settings
        
        # Test _get_available_wordlists
        wordlists = menu._get_available_wordlists()
        print(f"✅ Successfully loaded {len(wordlists)} wordlists")
        
        # Show first few
        print("\nAvailable wordlists:")
        for name, desc in wordlists[:5]:
            print(f"  - {name}: {desc}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n✅ Test complete!")


if __name__ == "__main__":
    test_wordlist_paths()