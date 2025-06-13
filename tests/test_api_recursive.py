#!/usr/bin/env python3
"""
Test specifically for /api recursive scanning
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.core.dirsearch_engine import DirsearchEngine, ScanOptions
from src.utils.logger import LoggerSetup


async def test_api_recursive():
    """Test /api recursive scanning"""
    # Initialize with debug logging
    LoggerSetup.initialize(debug=True)
    logger = LoggerSetup.get_logger(__name__)
    engine = DirsearchEngine(logger=logger)
    
    # Target
    target = "http://localhost:8080"
    
    # Wordlist that should find items in /api/
    wordlist = [
        # Root level
        "api", "admin", "test", 
        # API subdirectories/endpoints
        "v1", "v2", "users", "auth", "login", "status",
        # Common files
        "index.php", "test.php"
    ]
    
    print(f"\nTarget: {target}")
    print(f"Wordlist: {wordlist}")
    print("\nExpected behavior:")
    print("1. Find /api (301)")
    print("2. Scan /api/ with same wordlist")
    print("3. Find /api/v1, /api/users, etc.")
    print("\n" + "="*60 + "\n")
    
    # Options
    options = ScanOptions(
        threads=1,
        recursive=True,
        recursion_depth=3,
        detect_wildcards=False,  # Disable for clearer output
        follow_redirects=False
    )
    
    # Manual tracking
    scan_log = []
    
    def on_result(result):
        if result.status_code != 404:
            depth = result.path.strip('/').count('/')
            scan_log.append({
                'path': result.path,
                'url': result.url,
                'status': result.status_code,
                'is_dir': result.is_directory,
                'depth': depth
            })
            
            icon = "📁" if result.is_directory else "📄"
            print(f"Found: [{result.status_code}] {icon} {result.path}")
            
            if result.path == "api" and result.status_code == 301:
                print("  ✅ Found /api redirect! Recursive scan should follow...")
    
    engine.set_result_callback(on_result)
    
    # Run scan
    print("Starting scan...\n")
    results = await engine.scan_target(target, wordlist, options, display_progress=True)
    
    print(f"\n{'='*60}")
    print("SCAN COMPLETE")
    print(f"{'='*60}\n")
    
    # Analysis
    print(f"Total results: {len(results)}")
    
    # Check if we found /api
    api_found = any(r.path == "api" for r in results)
    print(f"\n/api found: {'✅ Yes' if api_found else '❌ No'}")
    
    # Check for paths under /api/
    api_subpaths = [r for r in results if r.path.startswith("api/")]
    print(f"Paths under /api/: {len(api_subpaths)}")
    
    if api_subpaths:
        print("\nFound under /api/:")
        for r in api_subpaths:
            print(f"  - /{r.path} [{r.status_code}]")
    else:
        print("\n⚠️  No paths found under /api/")
        print("Possible issues:")
        print("  1. Recursive scanning not triggered")
        print("  2. /api/ returns 404 for all subpaths")
        print("  3. Wordlist doesn't match actual API structure")
    
    # Show scan log grouped by depth
    print("\n" + "="*60)
    print("SCAN LOG BY DEPTH:")
    for depth in range(4):
        depth_items = [item for item in scan_log if item['depth'] == depth]
        if depth_items:
            print(f"\nDepth {depth}:")
            for item in depth_items:
                print(f"  {item['path']} [{item['status']}]")
    
    await engine.close()
    print("\n✅ Test complete")


if __name__ == "__main__":
    asyncio.run(test_api_recursive())