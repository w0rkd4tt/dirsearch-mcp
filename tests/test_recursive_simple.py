#!/usr/bin/env python3
"""
Simple test to verify recursive scanning works
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.core.dirsearch_engine import DirsearchEngine, ScanOptions
from src.utils.logger import LoggerSetup


async def simple_recursive_test():
    """Simple recursive test"""
    # Initialize
    LoggerSetup.initialize()
    engine = DirsearchEngine()
    
    # Target
    target = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080"
    
    # Simple wordlist
    wordlist = ["api", "v1", "v2", "users", "test", "admin", "docs"]
    
    print(f"\nTarget: {target}")
    print(f"Wordlist: {wordlist}")
    print("\nScanning with recursive enabled...\n")
    
    # Enable recursive
    options = ScanOptions(
        threads=1,
        recursive=True,
        recursion_depth=3,
        detect_wildcards=True,
        follow_redirects=False
    )
    
    # Track results
    found_paths = []
    
    def on_result(result):
        if result.status_code not in [404]:
            found_paths.append(result)
            depth = result.path.strip('/').count('/')
            icon = "📁" if result.is_directory else "📄"
            print(f"[{result.status_code}] {icon} {result.path} (depth: {depth})")
            if result.is_directory and result.status_code in [301, 302]:
                print(f"     → Recursive scan will check: {result.url}/")
    
    engine.set_result_callback(on_result)
    
    # Run scan
    results = await engine.scan_target(target, wordlist, options, display_progress=True)
    
    print(f"\n\nTotal results: {len(results)}")
    
    # Group by depth
    by_depth = {}
    for r in results:
        depth = r.path.strip('/').count('/')
        if depth not in by_depth:
            by_depth[depth] = []
        by_depth[depth].append(r.path)
    
    print("\nResults by depth:")
    for depth in sorted(by_depth.keys()):
        print(f"  Depth {depth}: {by_depth[depth]}")
    
    # Check if recursive worked
    if any(r.path.count('/') >= 2 for r in results):
        print("\n✅ Recursive scanning is working!")
    else:
        print("\n⚠️  No nested paths found. Checking why...")
        
        # Show what directories were found
        dirs_found = [r for r in results if r.is_directory]
        print(f"\nDirectories found: {len(dirs_found)}")
        for d in dirs_found:
            print(f"  - {d.path} [{d.status_code}]")
    
    await engine.close()


if __name__ == "__main__":
    asyncio.run(simple_recursive_test())