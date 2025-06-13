#!/usr/bin/env python3
"""
Test edge cases for directory scanning
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from src.core.dirsearch_engine import DirsearchEngine, ScanOptions


async def test_edge_cases():
    """Test various edge cases that might cause NoneType errors"""
    
    print("Testing edge cases for directory scanning")
    print("=" * 60)
    
    # Test 1: Empty wordlist
    print("\n1. Testing with empty wordlist...")
    try:
        async with DirsearchEngine() as engine:
            results = await engine.scan_target(
                url="http://testphp.vulnweb.com",
                wordlist=[],  # Empty wordlist
                options=ScanOptions(extensions=[], threads=5),
                display_progress=False
            )
            print(f"   ✓ Empty wordlist handled: {len(results)} results")
    except Exception as e:
        print(f"   ✗ Error with empty wordlist: {e}")
    
    # Test 2: Single item wordlist
    print("\n2. Testing with single item wordlist...")
    try:
        async with DirsearchEngine() as engine:
            results = await engine.scan_target(
                url="http://testphp.vulnweb.com",
                wordlist=["admin"],  # Single item
                options=ScanOptions(extensions=[], threads=5),
                display_progress=False
            )
            print(f"   ✓ Single item wordlist handled: {len(results)} results")
    except Exception as e:
        print(f"   ✗ Error with single item: {e}")
    
    # Test 3: Wordlist with special characters
    print("\n3. Testing with special characters...")
    try:
        async with DirsearchEngine() as engine:
            results = await engine.scan_target(
                url="http://testphp.vulnweb.com",
                wordlist=[".git", ".svn", "~admin", "@test", "#config"],
                options=ScanOptions(extensions=[], threads=5),
                display_progress=False
            )
            print(f"   ✓ Special characters handled: {len(results)} results")
    except Exception as e:
        print(f"   ✗ Error with special characters: {e}")
    
    # Test 4: Deep path analysis with no results
    print("\n4. Testing deep analysis with no initial results...")
    try:
        async with DirsearchEngine() as engine:
            # Use a wordlist that won't find anything
            results = await engine.scan_target(
                url="http://testphp.vulnweb.com",
                wordlist=["nonexistent1234", "doesnotexist5678"],
                options=ScanOptions(
                    extensions=[],
                    threads=5,
                    recursive=True,
                    crawl=True  # Enable crawling to trigger deep analysis
                ),
                display_progress=False
            )
            print(f"   ✓ Deep analysis with no results handled: {len(results)} results")
    except Exception as e:
        print(f"   ✗ Error with deep analysis: {e}")
    
    # Test 5: URL with existing path
    print("\n5. Testing URL with existing path...")
    try:
        async with DirsearchEngine() as engine:
            results = await engine.scan_target(
                url="http://testphp.vulnweb.com/artists",  # URL with path
                wordlist=["admin", "config", "test"],
                options=ScanOptions(extensions=[], threads=5),
                display_progress=False
            )
            print(f"   ✓ URL with path handled: {len(results)} results")
    except Exception as e:
        print(f"   ✗ Error with URL path: {e}")
    
    # Test 6: Case variations
    print("\n6. Testing case variations...")
    try:
        async with DirsearchEngine() as engine:
            results = await engine.scan_target(
                url="http://testphp.vulnweb.com",
                wordlist=["admin", "Admin", "ADMIN"],
                options=ScanOptions(
                    extensions=[],
                    threads=5,
                    uppercase=True,
                    lowercase=True,
                    capitalization=True
                ),
                display_progress=False
            )
            print(f"   ✓ Case variations handled: {len(results)} results")
    except Exception as e:
        print(f"   ✗ Error with case variations: {e}")
    
    print("\n" + "=" * 60)
    print("Edge case testing completed!")


if __name__ == "__main__":
    asyncio.run(test_edge_cases())