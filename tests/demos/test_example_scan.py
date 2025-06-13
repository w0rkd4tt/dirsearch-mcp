#!/usr/bin/env python3
"""
Example scan showing all directory results
Tests against a public website to demonstrate functionality
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


async def run_example_scan():
    """Run example scan and show all results"""
    
    # You can change this to your target
    target_url = "http://example.com/"
    
    print(f"\nDirsearch Directory Scan Example")
    print(f"Target: {target_url}")
    print("="*60)
    
    engine = DirsearchEngine(Settings())
    
    # Basic wordlist for demonstration
    wordlist = [
        # Common directories
        "admin",
        "api", 
        "assets",
        "backup",
        "css",
        "data",
        "files",
        "images",
        "img",
        "js",
        "static",
        "uploads",
        
        # Common files
        "robots.txt",
        "sitemap.xml",
        "index.html",
        "index.php",
        
        # With extensions
        "test.%EXT%",
        "config.%EXT%",
        "admin.%EXT%"
    ]
    
    # Configure scan
    options = ScanOptions(
        # Extension features
        extensions=['php', 'html', 'txt'],
        extension_tag='%EXT%',
        
        # Features
        detect_wildcards=True,
        crawl=True,
        random_user_agents=True,
        
        # Basic settings
        threads=10,
        timeout=10,
        exclude_status_codes=[404]
    )
    
    try:
        print("\nStarting scan...")
        print(f"Wordlist: {len(wordlist)} entries")
        print(f"Features: Wildcard detection, Crawling, Random UAs")
        
        # Run scan
        start = datetime.now()
        results = await engine.scan_target(target_url, wordlist, options)
        duration = (datetime.now() - start).total_seconds()
        
        print(f"\nScan completed in {duration:.2f} seconds")
        print(f"Total results: {len(results)}")
        
        # Separate directories and files
        directories = [r for r in results if r.is_directory]
        files = [r for r in results if not r.is_directory]
        
        print(f"\nDirectories found: {len(directories)}")
        print(f"Files found: {len(files)}")
        
        # Show all directories
        if directories:
            print("\n" + "="*60)
            print("ALL DIRECTORIES FOUND:")
            print("="*60)
            
            for d in sorted(directories, key=lambda x: x.path):
                status_color = ""
                if d.status_code == 200:
                    status_color = "✓"
                elif d.status_code == 301 or d.status_code == 302:
                    status_color = "→"
                elif d.status_code == 403:
                    status_color = "⚠"
                
                print(f"[{d.status_code}] {status_color} /{d.path}")
                
                # Show additional info
                if d.redirect_url:
                    print(f"     ↳ Redirects to: {d.redirect_url}")
                if d.size:
                    print(f"     ↳ Size: {d.size} bytes")
        
        # Show files
        if files:
            print("\n" + "="*60)
            print("FILES FOUND:")
            print("="*60)
            
            for f in sorted(files, key=lambda x: x.path):
                print(f"[{f.status_code}] /{f.path} ({f.size} bytes)")
        
        # Show crawled paths
        if engine._crawled_paths:
            print("\n" + "="*60)
            print(f"PATHS FROM CRAWLING ({len(engine._crawled_paths)}):")
            print("="*60)
            
            for path in sorted(list(engine._crawled_paths))[:20]:
                print(f"  • {path}")
            
            if len(engine._crawled_paths) > 20:
                print(f"  ... and {len(engine._crawled_paths) - 20} more")
        
        # Summary
        print("\n" + "="*60)
        print("SUMMARY:")
        print("="*60)
        print(f"✓ Total paths scanned: {len(wordlist)}")
        print(f"✓ Directories found: {len(directories)}")
        print(f"✓ Files found: {len(files)}")
        print(f"✓ Crawled paths: {len(engine._crawled_paths)}")
        print(f"✓ Scan duration: {duration:.2f} seconds")
        
        # Feature usage
        print("\nFeatures used:")
        print("✓ Wildcard detection: Enabled")
        print("✓ Extension tags: Enabled")
        print("✓ Content crawling: Enabled") 
        print("✓ Random user agents: Enabled")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await engine.close()


if __name__ == "__main__":
    print("Dirsearch Feature Test - Directory Results")
    print("=========================================")
    
    if len(sys.argv) > 1:
        # Use provided target
        target = sys.argv[1]
        if not target.startswith(('http://', 'https://')):
            target = 'http://' + target
        
        # Modify the target_url in the function
        import inspect
        import re
        
        # Get function source
        source = inspect.getsource(run_example_scan)
        # Replace target URL
        source = re.sub(
            r'target_url = ".*?"',
            f'target_url = "{target}"',
            source
        )
        # Execute modified function
        exec(compile(source, '<string>', 'exec'))
    
    asyncio.run(run_example_scan())