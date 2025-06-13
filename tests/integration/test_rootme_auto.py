#!/usr/bin/env python3
"""
Automated test of all dirsearch features on Root-Me website
Target: http://challenge01.root-me.org/web-serveur/ch4/
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.dirsearch_engine import DirsearchEngine, ScanOptions
from src.config.settings import Settings

# Target URL
TARGET_URL = "http://challenge01.root-me.org/web-serveur/ch4/"


async def run_full_test():
    """Run comprehensive test with all features"""
    print(f"\nTesting all dirsearch features on: {TARGET_URL}")
    print("="*60)
    
    engine = DirsearchEngine(Settings())
    
    # Comprehensive wordlist
    wordlist = [
        # Extension tags - will be expanded to multiple extensions
        "admin.%EXT%",
        "config.%EXT%",
        "login.%EXT%",
        "backup.%EXT%",
        "index.%EXT%",
        # Common admin paths
        "admin",
        "administrator",
        "panel",
        "console",
        # Common files
        "robots.txt",
        ".htaccess",
        "sitemap.xml",
        # Test files
        "test",
        "phpinfo",
        # Backup files
        "backup",
        "old",
        "copy"
    ]
    
    # Configure all features
    options = ScanOptions(
        # Extension features
        extensions=['php', 'html', 'txt', 'bak', 'old', 'asp'],
        extension_tag='%EXT%',
        
        # Wildcard detection
        detect_wildcards=True,
        
        # Enable crawling
        crawl=True,
        
        # Random user agents
        random_user_agents=True,
        
        # Blacklists
        blacklists={
            403: ['cgi-bin', 'icons', '.ht'],
            500: ['error', 'debug', 'trace']
        },
        
        # Scan settings
        threads=10,
        timeout=15,
        exclude_status_codes=[404],
        follow_redirects=True
    )
    
    try:
        print("\nFeatures enabled:")
        print(f"✓ Wildcard detection: {options.detect_wildcards}")
        print(f"✓ Extension tag (%EXT%): {options.extension_tag}")
        print(f"✓ Extensions to test: {', '.join(options.extensions)}")
        print(f"✓ Content crawling: {options.crawl}")
        print(f"✓ Random user agents: {options.random_user_agents}")
        print(f"✓ Blacklist rules: {len(options.blacklists)} status codes")
        print(f"✓ Threads: {options.threads}")
        
        # Check wildcard first
        print("\n1. Checking for wildcard responses...")
        wildcard_info = await engine._detect_wildcard(TARGET_URL, options)
        if wildcard_info and wildcard_info.get('detected'):
            print(f"⚠️  Wildcard detected for status {wildcard_info['status']}")
        else:
            print("✅ No wildcard detected")
        
        # Run the scan
        print("\n2. Starting scan with all features...")
        start_time = datetime.now()
        
        # Calculate total paths
        enhanced_wordlist = engine._enhance_wordlist_with_extensions(
            [w for w in wordlist if '%EXT%' in w],
            options.extensions,
            options.extension_tag
        )
        base_wordlist = [w for w in wordlist if '%EXT%' not in w]
        total_paths = len(enhanced_wordlist) + len(base_wordlist)
        
        print(f"   Original wordlist: {len(wordlist)} entries")
        print(f"   After extension expansion: {total_paths} paths to test")
        
        results = await engine.scan_target(TARGET_URL, wordlist, options)
        scan_time = (datetime.now() - start_time).total_seconds()
        
        print(f"\n3. Scan completed in {scan_time:.2f} seconds")
        print(f"   Total results: {len(results)}")
        
        if results:
            # Group results
            by_status = {}
            directories = []
            files = []
            
            for result in results:
                # Group by status
                if result.status_code not in by_status:
                    by_status[result.status_code] = []
                by_status[result.status_code].append(result)
                
                # Separate dirs and files
                if result.is_directory:
                    directories.append(result)
                else:
                    files.append(result)
            
            print(f"\n4. Results summary:")
            print(f"   Directories found: {len(directories)}")
            print(f"   Files found: {len(files)}")
            print(f"   Crawled additional paths: {len(engine._crawled_paths)}")
            
            print(f"\n5. Results by status code:")
            for status in sorted(by_status.keys()):
                print(f"   [{status}]: {len(by_status[status])} paths")
                for result in by_status[status][:3]:
                    print(f"      - {result.path} ({result.size} bytes)")
                if len(by_status[status]) > 3:
                    print(f"      ... and {len(by_status[status]) - 3} more")
            
            # Show important findings
            important_paths = ['admin', 'login', 'config', 'backup', 'panel']
            found_important = [r for r in results if any(p in r.path.lower() for p in important_paths)]
            
            if found_important:
                print(f"\n6. Important paths found:")
                for result in found_important:
                    print(f"   [{result.status_code}] {result.path}")
            
            # Show crawled paths
            if engine._crawled_paths:
                print(f"\n7. Paths discovered through crawling:")
                for path in list(engine._crawled_paths)[:5]:
                    print(f"   - {path}")
                if len(engine._crawled_paths) > 5:
                    print(f"   ... and {len(engine._crawled_paths) - 5} more")
        else:
            print("\n❌ No paths found")
        
        print("\n" + "="*60)
        print("✅ Test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await engine.close()


if __name__ == "__main__":
    print("Automated Dirsearch Feature Test")
    print("================================")
    asyncio.run(run_full_test())