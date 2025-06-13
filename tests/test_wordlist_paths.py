#!/usr/bin/env python3
"""
Test wordlist path resolution after fix
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.settings import Settings
from src.core.dirsearch_engine import DirsearchEngine


def test_wordlist_paths():
    """Test wordlist path resolution"""
    print("Testing wordlist path resolution...\n")
    
    settings = Settings()
    engine = DirsearchEngine(settings)
    
    # Test wordlist paths
    test_wordlists = [
        "general/monster-all.txt",
        "general/combined-enhanced.txt",
        "api-endpoints.txt",
        "specialized/hidden-files.txt",
        "critical-admin.txt",
        "critical-api.txt",
        "critical-backup.txt"
    ]
    
    print("Testing wordlist loading:")
    for wordlist in test_wordlists:
        try:
            words = engine._load_wordlist(wordlist)
            if words:
                print(f"  ✅ {wordlist}: Loaded {len(words)} entries")
            else:
                print(f"  ❌ {wordlist}: Empty or not found")
        except Exception as e:
            print(f"  ❌ {wordlist}: Error - {e}")
    
    # Test paths with subdirectories
    print("\n\nTesting path resolution:")
    base_path = settings.paths['wordlists']['base']
    
    for wordlist in test_wordlists:
        full_path = Path(base_path) / wordlist
        if full_path.exists():
            print(f"  ✅ {wordlist} exists at: {full_path}")
        else:
            print(f"  ❌ {wordlist} not found at: {full_path}")
    
    print("\n✅ Test complete!")


if __name__ == "__main__":
    test_wordlist_paths()