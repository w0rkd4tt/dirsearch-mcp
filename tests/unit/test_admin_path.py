#!/usr/bin/env python3
"""
Test specifically for /admin path scanning
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.dirsearch_engine import DirsearchEngine, ScanOptions
from src.config import Settings


async def test_admin_path():
    """Test if admin path is being scanned"""
    print("Testing admin path scanning\n")
    
    config = Settings()
    engine = DirsearchEngine(config)
    
    # Test with minimal wordlist
    wordlist = ['admin', 'test', 'login']
    base_url = "http://challenge01.root-me.org/web-serveur/ch4/"
    
    # Create options
    options = ScanOptions(
        extensions=['php', 'html'],
        threads=5,
        timeout=10
    )
    
    print(f"Base URL: {base_url}")
    print(f"Wordlist: {wordlist}")
    print(f"Extensions: {options.extensions}")
    print("\nGenerating paths...")
    
    # Generate paths
    paths = engine._generate_paths(wordlist, options)
    
    print(f"\nGenerated {len(paths)} paths:")
    for path in sorted(paths):
        print(f"  - {path}")
    
    # Test URL construction
    print("\nTesting URL construction:")
    from urllib.parse import urljoin
    
    for path in ['admin', 'admin.php']:
        url = urljoin(base_url, path)
        print(f"  {path} -> {url}")
    
    # Perform actual scan
    print("\nPerforming scan...")
    
    found_admin = False
    
    def on_result(result):
        if 'admin' in result.path.lower():
            print(f"  Found: [{result.status_code}] {result.url}")
            nonlocal found_admin
            found_admin = True
    
    engine.set_result_callback(on_result)
    
    try:
        results = await engine.scan_target(base_url, wordlist, options)
        
        print(f"\nScan completed. Total results: {len(results)}")
        
        # Check results
        admin_results = [r for r in results if 'admin' in r.path.lower()]
        
        if admin_results:
            print(f"\nAdmin paths found: {len(admin_results)}")
            for r in admin_results:
                print(f"  [{r.status_code}] {r.path} - {r.url}")
        else:
            print("\n❌ No admin paths found in results!")
            
        # Debug: Show all results
        print(f"\nAll results ({len(results)}):")
        for r in results:
            print(f"  [{r.status_code}] {r.path}")
            
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await engine.close()
    
    return found_admin


async def main():
    found = await test_admin_path()
    
    if not found:
        print("\n" + "="*60)
        print("ISSUE CONFIRMED: Admin path not being found")
        print("="*60)
        print("\nPossible causes:")
        print("1. Path generation is correct")
        print("2. URL construction is correct") 
        print("3. The issue might be:")
        print("   - The server returns 404 for /admin")
        print("   - The result is being filtered out")
        print("   - Network/request issues")


if __name__ == "__main__":
    asyncio.run(main())