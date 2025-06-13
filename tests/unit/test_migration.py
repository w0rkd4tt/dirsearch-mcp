#!/usr/bin/env python3
"""
Test script for migrated dirsearch features
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.dirsearch_engine import DirsearchEngine, ScanOptions
from src.config import Settings


async def test_wildcard_detection():
    """Test wildcard detection feature"""
    print("\n=== Testing Wildcard Detection ===")
    
    engine = DirsearchEngine(Settings())
    options = ScanOptions(
        detect_wildcards=True,
        threads=5,
        timeout=10
    )
    
    # Test with a known wildcard site (example)
    test_url = "http://example.com/"
    
    try:
        wildcard_info = await engine._detect_wildcard(test_url, options)
        if wildcard_info and wildcard_info.get('detected'):
            print(f"✓ Wildcard detected for status {wildcard_info['status']}")
        else:
            print("✓ No wildcard detected")
    except Exception as e:
        print(f"✗ Error: {e}")
    finally:
        await engine.close()


async def test_extension_tags():
    """Test extension tag replacement"""
    print("\n=== Testing Extension Tags ===")
    
    engine = DirsearchEngine(Settings())
    
    # Test wordlist with extension tags
    test_wordlist = [
        "admin.%EXT%",
        "config.%EXT%",
        "backup",
        "test.%EXT%"
    ]
    
    extensions = ['php', 'html', 'asp']
    enhanced = engine._enhance_wordlist_with_extensions(test_wordlist, extensions, "%EXT%")
    
    print(f"Original wordlist: {len(test_wordlist)} entries")
    print(f"Enhanced wordlist: {len(enhanced)} entries")
    print(f"Sample entries: {enhanced[:10]}")
    
    # Verify expansion
    expected = ['admin.php', 'admin.html', 'admin.asp', 'config.php', 'backup']
    for entry in expected:
        if entry in enhanced:
            print(f"✓ Found expected: {entry}")
        else:
            print(f"✗ Missing: {entry}")
    
    await engine.close()


async def test_auth_handlers():
    """Test authentication handlers"""
    print("\n=== Testing Authentication Handlers ===")
    
    engine = DirsearchEngine(Settings())
    
    # Test different auth types
    test_creds = ('user', 'pass')
    
    # Basic auth
    basic_auth = engine._get_auth_handler('basic', test_creds)
    print(f"✓ Basic auth handler: {type(basic_auth).__name__}")
    
    # Digest auth
    digest_auth = engine._get_auth_handler('digest', test_creds)
    print(f"✓ Digest auth handler: {type(digest_auth).__name__}")
    
    # NTLM auth (if available)
    try:
        ntlm_auth = engine._get_auth_handler('ntlm', test_creds)
        print(f"✓ NTLM auth handler: {type(ntlm_auth).__name__}")
    except Exception:
        print("✓ NTLM auth not available (httpx-ntlm not installed)")
    
    await engine.close()


async def test_crawling():
    """Test HTML crawling functionality"""
    print("\n=== Testing Content Crawling ===")
    
    engine = DirsearchEngine(Settings())
    
    # Test HTML content
    test_html = """
    <html>
    <head>
        <link rel="stylesheet" href="/css/style.css">
        <script src="/js/app.js"></script>
    </head>
    <body>
        <a href="/about">About</a>
        <a href="/contact.php">Contact</a>
        <img src="/images/logo.png">
        <form action="/submit.php">
            <input type="submit">
        </form>
    </body>
    </html>
    """
    
    response_data = {
        'headers': {'content-type': 'text/html'},
        'text': test_html,
        'path': 'index.html'
    }
    
    paths = await engine._crawl_response(response_data, "http://example.com/")
    
    print(f"Discovered {len(paths)} paths:")
    for path in paths:
        print(f"  - {path}")
    
    # Test robots.txt
    robots_content = """
    User-agent: *
    Disallow: /admin/
    Disallow: /private/
    Allow: /public/
    Sitemap: /sitemap.xml
    """
    
    response_data = {
        'headers': {'content-type': 'text/plain'},
        'text': robots_content,
        'path': 'robots.txt'
    }
    
    robot_paths = await engine._crawl_response(response_data, "http://example.com/")
    
    print(f"\nFrom robots.txt: {len(robot_paths)} paths")
    for path in robot_paths:
        print(f"  - {path}")
    
    await engine.close()


async def test_blacklists():
    """Test blacklist functionality"""
    print("\n=== Testing Blacklists ===")
    
    engine = DirsearchEngine(Settings())
    
    # Test blacklist checking
    options = ScanOptions(
        blacklists={
            403: ['admin', 'private'],
            500: ['error', 'debug']
        }
    )
    
    test_cases = [
        ('admin/login.php', 403, True),
        ('public/index.php', 403, False),
        ('error/500.html', 500, True),
        ('normal/page.html', 500, False)
    ]
    
    for path, status, expected in test_cases:
        result = engine._is_blacklisted(path, status, options)
        if result == expected:
            print(f"✓ {path} (status {status}): {'blacklisted' if result else 'allowed'}")
        else:
            print(f"✗ {path} (status {status}): expected {expected}, got {result}")
    
    await engine.close()


async def test_full_scan():
    """Test a full scan with migrated features"""
    print("\n=== Testing Full Scan with New Features ===")
    
    engine = DirsearchEngine(Settings())
    
    # Small wordlist for testing
    test_wordlist = [
        'admin',
        'config.%EXT%',
        'backup',
        'test',
        'robots.txt'
    ]
    
    options = ScanOptions(
        extensions=['php', 'html'],
        extension_tag='%EXT%',
        detect_wildcards=True,
        crawl=True,
        threads=5,
        timeout=10,
        exclude_status_codes=[404]
    )
    
    # Test against a local server or example.com
    test_url = "http://example.com/"
    
    print(f"Scanning {test_url} with migrated features...")
    print(f"- Wildcard detection: {options.detect_wildcards}")
    print(f"- Crawling: {options.crawl}")
    print(f"- Extension tag: {options.extension_tag}")
    
    try:
        results = await engine.scan_target(test_url, test_wordlist, options)
        
        print(f"\nResults: {len(results)} paths found")
        for result in results[:5]:  # Show first 5
            print(f"  [{result.status_code}] {result.path} ({result.size} bytes)")
        
        if len(results) > 5:
            print(f"  ... and {len(results) - 5} more")
            
    except Exception as e:
        print(f"Error during scan: {e}")
    finally:
        await engine.close()


async def main():
    """Run all tests"""
    print("Testing Migrated Dirsearch Features")
    print("=" * 50)
    
    await test_extension_tags()
    await test_auth_handlers()
    await test_blacklists()
    await test_wildcard_detection()
    await test_crawling()
    await test_full_scan()
    
    print("\n" + "=" * 50)
    print("Migration testing complete!")


if __name__ == "__main__":
    asyncio.run(main())