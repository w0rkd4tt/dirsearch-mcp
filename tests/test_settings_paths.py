#!/usr/bin/env python3
"""
Test settings paths structure
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.settings import Settings


def test_settings():
    """Test settings paths"""
    print("Testing Settings paths structure...\n")
    
    settings = Settings()
    
    print("1. Paths structure:")
    for key, value in settings.paths.items():
        print(f"   {key}: {type(value).__name__} = {value}")
    
    print("\n2. Wordlists path resolution:")
    wordlists = settings.paths.get('wordlists')
    print(f"   Type: {type(wordlists)}")
    
    if isinstance(wordlists, dict):
        print("   Sub-paths:")
        for k, v in wordlists.items():
            print(f"     - {k}: {v}")
            if Path(v).exists():
                print(f"       ✅ Exists")
            else:
                print(f"       ❌ Not found")
    
    print("\n3. Test path resolution logic:")
    # Simulate the fix logic
    wordlists_path = settings.paths.get('wordlists', 'wordlists')
    if isinstance(wordlists_path, dict):
        resolved = wordlists_path.get('base', wordlists_path.get('general', 'wordlists'))
        print(f"   Resolved path: {resolved}")
        
        # Check if common.txt exists
        test_file = Path(resolved) / 'common.txt'
        if test_file.exists():
            print(f"   ✅ Test file exists: {test_file}")
        else:
            print(f"   ❌ Test file not found: {test_file}")
    
    print("\n✅ Settings test complete!")


if __name__ == "__main__":
    test_settings()