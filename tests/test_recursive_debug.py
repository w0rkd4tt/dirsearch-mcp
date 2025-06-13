#!/usr/bin/env python3
"""
Debug test for recursive scanning functionality
Tests the flow: abc.com -> abc.com/api -> abc.com/api/v1 -> etc.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.core.dirsearch_engine import DirsearchEngine, ScanOptions
from src.utils.logger import LoggerSetup


async def test_recursive_flow():
    """Test recursive scanning flow"""
    print("\n" + "="*60)
    print("RECURSIVE SCANNING DEBUG TEST")
    print("="*60)
    
    # Initialize
    LoggerSetup.initialize()
    logger = LoggerSetup.get_logger(__name__)
    engine = DirsearchEngine(logger=logger)
    
    # Target
    target = sys.argv[1] if len(sys.argv) > 1 else "http://testphp.vulnweb.com"
    
    # Simple wordlist that should find directories
    wordlist = [
        "admin", "api", "v1", "v2", "users", "login", "test", 
        "config", "docs", "images", "css", "js", "uploads",
        "backup", "data", "files", "public", "private",
        "test.php", "index.php", "info.php", "phpinfo.php", "heartbeat", "backup", "backup-db"
    ]
    
    print(f"\nTarget: {target}")
    print(f"Wordlist: {wordlist}")
    print(f"Expected flow: {target} -> {target}/api/ -> {target}/api/v1/ -> etc.")
    
    # Options with recursive enabled
    options = ScanOptions(
        threads=1,  # Single thread for clear output
        timeout=10,
        recursive=True,
        recursion_depth=3,  # Go 3 levels deep
        detect_wildcards=True,
        follow_redirects=False  # Keep false to see 301/302
    )
    
    print(f"\nRecursive scanning enabled with depth: {options.recursion_depth}")
    print("="*60)
    
    # Track directories found at each level
    found_dirs = {0: [], 1: [], 2: [], 3: []}
    current_level = 0
    
    def on_result(result):
        """Track results and show directory discoveries"""
        nonlocal current_level
        
        if result.is_directory and result.status_code in [200, 301, 302]:
            # Calculate depth based on path
            depth = result.path.strip('/').count('/')
            if depth <= 3:
                found_dirs[depth].append(result.path)
            
            print(f"\n🎯 Found directory at level {depth}: {result.path}")
            print(f"   Full URL: {result.url}")
            print(f"   Status: {result.status_code}")
            print(f"   → Will scan: {result.url + '/' if not result.url.endswith('/') else result.url}")
    
    engine.set_result_callback(on_result)
    
    # Run scan
    print("\nStarting recursive scan...\n")
    
    try:
        results = await engine.scan_target(target, wordlist, options, display_progress=True)
        
        print(f"\n\n{'='*60}")
        print("RECURSIVE SCAN RESULTS")
        print(f"{'='*60}")
        
        # Show found directories by level
        for level in range(4):
            if found_dirs[level]:
                print(f"\nLevel {level} directories:")
                for dir_path in sorted(set(found_dirs[level])):
                    print(f"  • {dir_path}")
        
        # Show all results
        print(f"\nTotal results: {len(results)}")
        
        # Group by directory depth
        by_depth = {}
        for result in results:
            if result.status_code not in [404]:
                depth = result.path.strip('/').count('/')
                if depth not in by_depth:
                    by_depth[depth] = []
                by_depth[depth].append(result)
        
        # Show results by depth
        for depth in sorted(by_depth.keys()):
            print(f"\n--- Depth {depth} ({len(by_depth[depth])} results) ---")
            for result in sorted(by_depth[depth], key=lambda x: x.path):
                type_icon = "📁" if result.is_directory else "📄"
                print(f"[{result.status_code}] {type_icon} {result.path}")
        
        # Verify recursive scanning worked
        print(f"\n{'='*60}")
        print("VERIFICATION:")
        print(f"{'='*60}")
        
        # Check if we found nested paths
        nested_paths = [r for r in results if r.path.count('/') >= 2]
        if nested_paths:
            print(f"✅ Recursive scanning worked! Found {len(nested_paths)} nested paths:")
            for path in sorted(nested_paths, key=lambda x: x.path)[:10]:
                print(f"   • {path.path} [{path.status_code}]")
        else:
            print("❌ No nested paths found. Recursive scanning may not be working correctly.")
        
        # Show scan statistics
        stats = engine.get_scan_statistics()
        print(f"\nScan Statistics:")
        print(f"  • Total requests: {stats.total_requests}")
        print(f"  • Successful requests: {stats.successful_requests}")
        print(f"  • Failed requests: {stats.failed_requests}")
        print(f"  • Duration: {stats.duration:.2f}s")
        
    except KeyboardInterrupt:
        print("\n\nScan interrupted")
    finally:
        await engine.close()
        print("\n✅ Test completed!")


if __name__ == "__main__":
    print("""
Recursive Scanning Debug Test

This test verifies that recursive scanning works correctly:
1. Scans the target with initial wordlist
2. When a directory is found (e.g., /api/), uses it as new target
3. Scans the new target (/api/) with the SAME wordlist
4. Continues recursively based on depth setting

Usage:
    python test_recursive_debug.py                    # Default target
    python test_recursive_debug.py http://example.com # Custom target
""")
    
    asyncio.run(test_recursive_flow())