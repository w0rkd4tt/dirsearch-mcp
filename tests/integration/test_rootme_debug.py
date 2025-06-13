#!/usr/bin/env python3
"""
Debug test for Root-Me website with verbose output
Target: http://challenge01.root-me.org/web-serveur/ch4/
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.dirsearch_engine import DirsearchEngine, ScanOptions
from src.config.settings import Settings

# Target URL
TARGET_URL = "http://challenge01.root-me.org/web-serveur/ch4/"


async def test_basic_scan():
    """Test with a basic scan first"""
    print(f"\nTesting basic scan on: {TARGET_URL}")
    print("="*60)
    
    engine = DirsearchEngine(Settings())
    
    # Very basic wordlist
    wordlist = [
        "",  # Root path
        "admin",
        "index",
        "login",
        "test",
        "robots.txt",
        ".htaccess"
    ]
    
    # Simple options
    options = ScanOptions(
        threads=5,
        timeout=20,
        exclude_status_codes=[],  # Don't exclude anything initially
        follow_redirects=True
    )
    
    try:
        print("\nScanning with basic wordlist...")
        print(f"Wordlist: {wordlist}")
        
        results = await engine.scan_target(TARGET_URL, wordlist, options)
        
        print(f"\nRaw results: {len(results)} responses")
        
        # Show all responses
        for result in results:
            print(f"[{result.status_code}] {result.path} - {result.size} bytes")
            
        # Now test with extensions
        print("\n" + "-"*40)
        print("Testing with extensions...")
        
        options.extensions = ['php', 'html', 'txt']
        results2 = await engine.scan_target(TARGET_URL, wordlist, options)
        
        print(f"\nWith extensions: {len(results2)} responses")
        for result in results2:
            print(f"[{result.status_code}] {result.path} - {result.size} bytes")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await engine.close()


async def test_known_path():
    """Test with a known path to verify connectivity"""
    print(f"\n\nTesting connectivity with known path...")
    print("="*60)
    
    engine = DirsearchEngine(Settings())
    
    try:
        # Test the base URL directly
        response = await engine._make_request(
            TARGET_URL, 
            ScanOptions(timeout=20)
        )
        
        if response:
            print(f"✅ Base URL accessible: [{response.get('status_code')}] {TARGET_URL}")
            print(f"   Response size: {response.get('size')} bytes")
            
            # Test a specific path we know might exist
            admin_url = TARGET_URL + "admin"
            response2 = await engine._make_request(
                admin_url,
                ScanOptions(timeout=20)
            )
            
            if response2:
                print(f"\n✅ Admin path test: [{response2.get('status_code')}] {admin_url}")
                print(f"   Response size: {response2.get('size')} bytes")
        else:
            print("❌ Could not connect to target")
            
    except Exception as e:
        print(f"\n❌ Connection error: {e}")
    finally:
        await engine.close()


async def test_with_common_wordlist():
    """Test with a more comprehensive wordlist"""
    print(f"\n\nTesting with common paths...")
    print("="*60)
    
    engine = DirsearchEngine(Settings())
    
    # Common paths that often exist
    wordlist = [
        "",
        "admin",
        "administrator", 
        "login",
        "index",
        "home",
        "panel",
        "console",
        "cp",
        "controlpanel",
        "adminpanel",
        "user",
        "users",
        "member",
        "membres",
        "test",
        "demo",
        "backup",
        "config",
        "configuration",
        "settings",
        "robots.txt",
        "sitemap.xml",
        ".htaccess",
        ".htpasswd",
        "web.config"
    ]
    
    options = ScanOptions(
        extensions=['php', 'html', 'asp', 'aspx'],
        threads=10,
        timeout=20,
        exclude_status_codes=[404],  # Only exclude 404s
        follow_redirects=True,
        random_user_agents=True
    )
    
    try:
        print(f"Testing {len(wordlist)} base paths with {len(options.extensions)} extensions...")
        
        results = await engine.scan_target(TARGET_URL, wordlist, options)
        
        if results:
            print(f"\n✅ Found {len(results)} valid paths:")
            
            # Group by status
            by_status = {}
            for result in results:
                status = result.status_code
                if status not in by_status:
                    by_status[status] = []
                by_status[status].append(result)
            
            for status in sorted(by_status.keys()):
                print(f"\n[{status}] Status - {len(by_status[status])} paths:")
                for result in by_status[status]:
                    print(f"  - {result.path} ({result.size} bytes)")
        else:
            print("\n⚠️  No valid paths found (all returned 404)")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await engine.close()


async def main():
    """Run all debug tests"""
    print("Debug Test for Root-Me Challenge")
    print("================================")
    
    # Run tests in order
    await test_known_path()
    await test_basic_scan()
    await test_with_common_wordlist()
    
    print("\n" + "="*60)
    print("Debug tests completed!")


if __name__ == "__main__":
    asyncio.run(main())