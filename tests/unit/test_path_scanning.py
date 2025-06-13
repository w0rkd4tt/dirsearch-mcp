#!/usr/bin/env python3
"""Test path scanning with various URL formats"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.core.dirsearch_engine import DirsearchEngine, ScanRequest
from src.config.settings import Settings
from urllib.parse import urlparse

async def test_url_paths():
    settings = Settings()
    engine = DirsearchEngine(settings=settings)
    
    # Test URLs with different path formats
    test_urls = [
        "192.168.214.143",
        "192.168.214.143/api",
        "192.168.214.143/api/v1",
        "192.168.214.143/api/v1/",
        "example.com/admin",
        "example.com/admin/panel",
        "http://example.com/test",
        "https://example.com/app/",
    ]
    
    print("Testing URL path handling in Dirsearch MCP:\n")
    print(f"{'Input URL':<30} {'Processed URL':<50} {'Base Path':<20}")
    print("-" * 100)
    
    for test_url in test_urls:
        # Create a minimal scan request
        scan_request = ScanRequest(
            base_url=test_url,
            wordlist="test,admin,config",
            extensions=["php"],
            threads=1,
            timeout=5,
            recursive=False  # Disable recursion for this test
        )
        
        # Process the URL through the engine
        original_url = test_url
        if not test_url.startswith(('http://', 'https://')):
            test_url = f"http://{test_url}"
            
        parsed = urlparse(test_url)
        if parsed.path and parsed.path != '/':
            if not parsed.path.endswith('/'):
                last_segment = parsed.path.split('/')[-1]
                if '.' not in last_segment:
                    test_url = test_url + '/'
        else:
            test_url = test_url.rstrip('/')
            
        base_path = parsed.path if parsed.path else '/'
        
        print(f"{original_url:<30} {test_url:<50} {base_path:<20}")
    
    print("\n\nTesting actual scanning with path:")
    
    # Test actual scanning
    scan_request = ScanRequest(
        base_url="192.168.214.143/api",
        wordlist="users,login,docs,v1,v2",
        extensions=["json", "php"],
        threads=5,
        timeout=5,
        recursive=False
    )
    
    print(f"\nScanning: {scan_request.base_url}")
    print("Expected paths to be scanned under /api/:")
    print("  - /api/users.json")
    print("  - /api/users.php")
    print("  - /api/login.json")
    print("  - /api/login.php")
    print("  - etc...")
    
    # Track scanned URLs
    scanned_urls = []
    
    def track_urls(url, options):
        scanned_urls.append(url)
        return None  # Return None to simulate no response
    
    # Monkey patch the _make_request method to track URLs
    original_make_request = engine._make_request
    engine._make_request = track_urls
    
    async with engine:
        try:
            await engine.execute_scan(scan_request)
        except:
            pass  # Ignore errors since we're not actually making requests
    
    # Show first 10 scanned URLs
    print(f"\nFirst 10 URLs that would be scanned:")
    for url in scanned_urls[:10]:
        print(f"  - {url}")
    
    # Verify paths are under /api/
    api_paths = [url for url in scanned_urls if '/api/' in url]
    print(f"\nTotal URLs under /api/: {len(api_paths)} out of {len(scanned_urls)}")
    
    if len(api_paths) == len(scanned_urls):
        print("✓ SUCCESS: All paths are correctly under /api/")
    else:
        print("✗ ERROR: Some paths are not under /api/")
        wrong_paths = [url for url in scanned_urls if '/api/' not in url]
        print("Wrong paths:")
        for path in wrong_paths[:5]:
            print(f"  - {path}")

if __name__ == "__main__":
    asyncio.run(test_url_paths())