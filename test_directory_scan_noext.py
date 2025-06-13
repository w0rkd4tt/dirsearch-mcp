#!/usr/bin/env python3
"""
Test script to verify directory scanning without extensions
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from src.core.dirsearch_engine import DirsearchEngine, ScanOptions


async def test_directory_scan():
    """Test directory scanning without extensions"""
    
    # Create a simple wordlist with directory names (no extensions)
    test_wordlist = [
        'admin',
        'api',
        'backup',
        'config',
        'data',
        'docs',
        'images',
        'includes',
        'js',
        'lib',
        'logs',
        'media',
        'modules',
        'private',
        'public',
        'scripts',
        'static',
        'temp',
        'test',
        'uploads',
        'user',
        'users',
        'vendor',
        '.git',
        '.svn',
        '.env'
    ]
    
    # Test URL (you can change this to test against a real target)
    test_url = "http://testphp.vulnweb.com"
    
    print(f"Testing directory scanning on: {test_url}")
    print(f"Wordlist contains {len(test_wordlist)} directory names without extensions")
    print("-" * 60)
    
    # Create scan options with no extensions
    options = ScanOptions(
        extensions=[],  # No extensions - pure directory scanning
        threads=10,
        timeout=5,
        recursive=False,  # Disable recursive for this test
        detect_wildcards=True
    )
    
    async with DirsearchEngine() as engine:
        print("Starting scan...")
        results = await engine.scan_target(
            url=test_url,
            wordlist=test_wordlist,
            options=options,
            display_progress=False
        )
        
        print(f"\nScan completed. Found {len(results)} results")
        print("-" * 60)
        
        # Analyze results
        directories = [r for r in results if r.is_directory]
        files = [r for r in results if not r.is_directory]
        
        print(f"Directories found: {len(directories)}")
        print(f"Files found: {len(files)}")
        print()
        
        # Show directories
        if directories:
            print("Discovered Directories:")
            print("-" * 60)
            for dir_result in sorted(directories, key=lambda x: x.path):
                status_emoji = {
                    200: "✅",
                    301: "↗️",
                    302: "↗️",
                    403: "🚫",
                    404: "❌"
                }.get(dir_result.status_code, "❓")
                
                print(f"{status_emoji} {dir_result.path:30} [Status: {dir_result.status_code}]")
        
        # Show path generation examples
        print("\nExample paths generated (first 10):")
        print("-" * 60)
        example_paths = engine._generate_paths(test_wordlist[:5], options)
        for i, path in enumerate(example_paths[:10]):
            print(f"  {i+1}. {path}")
        
        # Statistics
        stats = engine.get_scan_statistics()
        print(f"\nScan Statistics:")
        print("-" * 60)
        print(f"Total requests: {stats.total_requests}")
        print(f"Successful requests: {stats.successful_requests}")
        print(f"Failed requests: {stats.failed_requests}")
        print(f"Filtered results: {stats.filtered_results}")
        print(f"Requests per second: {stats.requests_per_second:.2f}")


if __name__ == "__main__":
    asyncio.run(test_directory_scan())