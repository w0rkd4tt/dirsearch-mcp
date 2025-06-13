#!/usr/bin/env python3
"""Test script to debug wordlist loading in Monster Mode"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.config.settings import Settings
from src.core.dirsearch_engine import DirsearchEngine, ScanRequest
from src.utils.logger import LoggerSetup
import asyncio


async def test_wordlist_loading():
    """Test wordlist loading for Monster Mode"""
    # Initialize settings and logger
    settings = Settings()
    LoggerSetup.initialize()
    logger = LoggerSetup.get_logger(__name__)
    
    # Create engine
    engine = DirsearchEngine(settings)
    engine.logger = logger
    
    # Test different wordlist paths
    test_cases = [
        "monster-all.txt",
        "wordlists/monster-all.txt",
        str(Path("wordlists/monster-all.txt").absolute())
    ]
    
    print("Testing wordlist loading...")
    print(f"Settings wordlists path: {settings.paths['wordlists']}")
    print()
    
    for wordlist_path in test_cases:
        print(f"\nTesting: {wordlist_path}")
        
        # Create scan request
        scan_request = ScanRequest(
            base_url="http://example.com",
            wordlist=wordlist_path,
            wordlist_type='enhanced'
        )
        
        # Load wordlists
        try:
            words = engine._load_wordlists(scan_request)
            print(f"  ✓ Loaded {len(words)} words")
            if len(words) > 0:
                print(f"  First 5 words: {words[:5]}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    # Test with direct _load_wordlist method
    print("\n\nDirect _load_wordlist test:")
    for wordlist_path in ["monster-all.txt", "wordlists/monster-all.txt"]:
        try:
            words = engine._load_wordlist(wordlist_path)
            print(f"{wordlist_path}: {len(words)} words")
        except Exception as e:
            print(f"{wordlist_path}: Error - {e}")


if __name__ == "__main__":
    asyncio.run(test_wordlist_loading())