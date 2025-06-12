#!/usr/bin/env python3
"""Test script to verify enhanced wordlist functionality"""

import asyncio
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.dirsearch_engine import DirsearchEngine, ScanRequest
from src.config.settings import Settings
from src.utils.logger import LoggerSetup

async def test_wordlist_loading():
    """Test loading different wordlists"""
    # Initialize components
    settings = Settings()
    logger = LoggerSetup.get_logger('test_wordlists')
    
    engine = DirsearchEngine(settings, logger)
    
    print("Testing wordlist loading functionality...\n")
    
    # Test 1: Load enhanced wordlist
    print("1. Testing enhanced wordlist:")
    request = ScanRequest(
        base_url="http://example.com",
        wordlist="wordlists/combined-enhanced.txt",
        wordlist_type="enhanced",
        extensions=["php", "txt"]
    )
    
    words = engine._load_wordlists(request)
    print(f"   ✓ Loaded {len(words)} words from enhanced wordlist")
    print(f"   Sample words: {words[:5]}...")
    
    # Test 2: Load API-specific wordlist
    print("\n2. Testing API-specific wordlist:")
    request = ScanRequest(
        base_url="http://example.com/api",
        wordlist="wordlists/api-endpoints.txt",
        wordlist_type="api",
        extensions=["json"]
    )
    
    words = engine._load_wordlists(request)
    print(f"   ✓ Loaded {len(words)} words from API wordlist")
    print(f"   Sample API paths: {[w for w in words if 'api' in w][:5]}...")
    
    # Test 3: Multiple wordlists
    print("\n3. Testing multiple wordlists:")
    request = ScanRequest(
        base_url="http://example.com/api",
        wordlist="wordlists/api-endpoints.txt",
        wordlist_type="api",
        additional_wordlists=["wordlists/hidden-files.txt"],
        extensions=["json", "txt"]
    )
    
    words = engine._load_wordlists(request)
    print(f"   ✓ Loaded {len(words)} words from combined wordlists")
    
    # Check for specific patterns
    api_patterns = [w for w in words if 'api/api' in w]
    hidden_files = [w for w in words if w.endswith('.txt')]
    
    print(f"   Found {len(api_patterns)} nested API patterns (api/api/*)")
    print(f"   Found {len(hidden_files)} hidden file patterns (*.txt)")
    
    # Test 4: Verify specific patterns exist
    print("\n4. Verifying specific patterns:")
    expected_patterns = [
        "api/api/aaa",
        "api/heartbeat",
        "api/health",
        "api/abcv.txt",
        "api/config.json"
    ]
    
    for pattern in expected_patterns:
        if pattern in words:
            print(f"   ✓ Found: {pattern}")
        else:
            print(f"   ✗ Missing: {pattern}")
    
    print("\nWordlist testing complete!")

async def test_api_scanning():
    """Test scanning with API-focused configuration"""
    settings = Settings()
    logger = LoggerSetup.get_logger('test_api_scan')
    
    engine = DirsearchEngine(settings, logger)
    
    print("\n\nTesting API endpoint scanning...\n")
    
    # Create a request specifically for API scanning
    request = ScanRequest(
        base_url="http://192.168.214.143/api",
        wordlist="wordlists/combined-enhanced.txt",
        wordlist_type="enhanced",
        extensions=["json", "txt"],
        threads=5,
        timeout=5,
        recursive=True,
        recursion_depth=3
    )
    
    print(f"Target: {request.base_url}")
    print(f"Wordlist type: {request.wordlist_type}")
    print(f"Extensions: {request.extensions}")
    print(f"Recursive: {request.recursive} (depth: {request.recursion_depth})")
    
    # Load wordlists to show what will be scanned
    words = engine._load_wordlists(request)
    api_specific = [w for w in words[:100] if any(p in w for p in ['api', 'health', 'status', 'heartbeat'])]
    
    print(f"\nSample API-specific paths that will be tested:")
    for path in api_specific[:10]:
        print(f"  - {path}")
    
    print(f"\nTotal paths to test: {len(words)}")

if __name__ == "__main__":
    print("Enhanced Wordlist Testing\n")
    print("=" * 50)
    
    # Run tests
    asyncio.run(test_wordlist_loading())
    asyncio.run(test_api_scanning())
    
    print("\n" + "=" * 50)
    print("Testing complete! The enhanced wordlists are ready for use.")
    print("\nTo use in a scan:")
    print("  python main.py -u 192.168.214.143/api -w wordlists/combined-enhanced.txt")
    print("  python main.py -u 192.168.214.143/api  # Uses enhanced wordlist by default")