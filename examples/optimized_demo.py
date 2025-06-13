#!/usr/bin/env python3
"""
Optimized Demo - Shows enhanced features with limited terminal output
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.dirsearch_engine import DirsearchEngine, ScanOptions
from src.utils.logger import LoggerSetup


async def optimized_demo():
    """Demo optimized features with limited output"""
    print("\n" + "="*60)
    print("DIRSEARCH-MCP OPTIMIZED DEMO")
    print("Features: Recursive scan, Smart display (20 lines limit)")
    print("="*60)
    
    # Initialize
    LoggerSetup.initialize()
    engine = DirsearchEngine()
    
    # Target
    target = sys.argv[1] if len(sys.argv) > 1 else "http://testphp.vulnweb.com"
    
    # Optimized wordlist for demo
    wordlist = [
        # High-value directories
        "admin", "api", "backup", "config", "data", "dev", "test",
        # Common files
        "index.php", "login.php", "robots.txt", ".htaccess",
        # API paths
        "v1", "v2", "users", "auth",
        # Hidden/sensitive
        ".git", ".env", "wp-admin", "phpmyadmin"
    ]
    
    print(f"\nTarget: {target}")
    print(f"Wordlist: {len(wordlist)} paths")
    print(f"Mode: Optimized with recursive scanning")
    
    # Options
    options = ScanOptions(
        threads=1,            # Single thread for clear output
        timeout=10,
        recursive=True,       # Enable recursive
        recursion_depth=2,    # Scan 2 levels deep
        detect_wildcards=True,
        follow_redirects=False,
        exclude_status_codes=[404]
    )
    
    print(f"\nSettings:")
    print(f"  • Threads: {options.threads}")
    print(f"  • Recursive: Yes (depth: {options.recursion_depth})")
    print(f"  • Wildcard detection: Yes")
    
    print("\n" + "-"*60)
    print("SCANNING...")
    print("-"*60 + "\n")
    
    # Track results for optimized display
    all_results = []
    dir_count = 0
    
    def on_result(result):
        """Collect results for optimized display"""
        if result.status_code != 404:
            all_results.append(result)
            if result.is_directory:
                nonlocal dir_count
                dir_count += 1
    
    engine.set_result_callback(on_result)
    
    # Run scan
    start_time = asyncio.get_event_loop().time()
    results = await engine.scan_target(target, wordlist, options, display_progress=True)
    duration = asyncio.get_event_loop().time() - start_time
    
    # Display optimized results (20 lines max)
    print("\n" + "="*60)
    print("SCAN RESULTS (Limited to 20 lines)")
    print("="*60)
    
    # Group by status
    status_groups = {}
    for r in results:
        status = r.status_code
        if status not in status_groups:
            status_groups[status] = []
        status_groups[status].append(r)
    
    # Display with line limit
    lines = 0
    max_lines = 20
    
    for status in sorted(status_groups.keys()):
        if lines >= max_lines:
            break
            
        items = status_groups[status]
        print(f"\n[{status}] Status Code - {len(items)} found:")
        lines += 1
        
        # Show items
        show_count = min(len(items), max_lines - lines)
        for i, result in enumerate(sorted(items, key=lambda x: x.path)[:show_count]):
            icon = "📁" if result.is_directory else "📄"
            print(f"  {icon} {result.path} ({result.size} bytes)")
            lines += 1
        
        if len(items) > show_count:
            print(f"  ... and {len(items) - show_count} more")
            lines += 1
    
    # Summary
    print("\n" + "-"*60)
    print("SUMMARY")
    print("-"*60)
    print(f"Duration: {duration:.2f}s")
    print(f"Total Results: {len(results)}")
    print(f"Directories Found: {dir_count}")
    print(f"Requests/sec: {engine.get_scan_statistics().requests_per_second:.1f}")
    
    # Show if recursive worked
    nested = [r for r in results if r.path.count('/') >= 2]
    if nested:
        print(f"\n✅ Recursive scan found {len(nested)} nested paths")
    
    await engine.close()
    print("\n✅ Demo complete!")


if __name__ == "__main__":
    print("""
Optimized Dirsearch-MCP Demo

This demo shows:
- Enhanced recursive scanning
- Optimized terminal output (20 lines max)
- Smart result grouping by status code
- Performance metrics

Usage:
    python optimized_demo.py                    # Default target
    python optimized_demo.py http://example.com # Custom target
""")
    
    asyncio.run(optimized_demo())