#!/usr/bin/env python3
"""
Simple test for dirsearch-mcp without external dependencies
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.core.dirsearch_engine import DirsearchEngine, ScanOptions
from src.utils.logger import LoggerSetup


async def test_basic_scan():
    """Basic scan test"""
    print("\n" + "="*60)
    print("DIRSEARCH-MCP SIMPLE TEST")
    print("="*60)
    
    # Initialize
    LoggerSetup.initialize()
    logger = LoggerSetup.get_logger(__name__)
    engine = DirsearchEngine(logger=logger)
    
    # Target
    target = sys.argv[1] if len(sys.argv) > 1 else "http://testphp.vulnweb.com"
    
    # Wordlist
    wordlist = [
        "admin", "login", "dashboard", "api", "config",
        "backup", "test", "dev", "staging", "old",
        "user", "users", "profile", "upload", "uploads",
        ".git", ".env", "robots.txt", "sitemap.xml", ".htaccess"
    ]
    
    # Options
    options = ScanOptions(
        threads=10,
        timeout=10,
        recursive=False,  # Keep it simple
        detect_wildcards=True
    )
    
    print(f"\nTarget: {target}")
    print(f"Wordlist: {len(wordlist)} paths")
    print(f"Threads: {options.threads}")
    print(f"Timeout: {options.timeout}s")
    
    print("\nScanning...")
    
    # Progress callback
    def on_progress(current, total):
        percent = (current / total * 100) if total > 0 else 0
        print(f"\rProgress: {current}/{total} ({percent:.1f}%)", end="", flush=True)
    
    engine.set_progress_callback(on_progress)
    
    # Run scan
    try:
        results = await engine.scan_target(target, wordlist, options)
        print(f"\n\nScan completed! Found {len(results)} results.")
        
        # Group results by status code
        by_status = {}
        for result in results:
            status = result.status_code
            if status not in by_status:
                by_status[status] = []
            by_status[status].append(result)
        
        # Print results
        print("\nResults by status code:")
        for status in sorted(by_status.keys()):
            items = by_status[status]
            print(f"\n[{status}] - {len(items)} results:")
            for item in items[:5]:  # Show first 5
                print(f"  • {item.path} ({item.size} bytes)")
            if len(items) > 5:
                print(f"  ... and {len(items) - 5} more")
                
        # Show interesting findings
        interesting = [r for r in results if r.status_code in [200, 301, 302, 401, 403]]
        if interesting:
            print(f"\n🎯 Interesting findings ({len(interesting)}):")
            for r in interesting[:10]:
                status_emoji = {
                    200: "✓",
                    301: "→", 
                    302: "→",
                    401: "🔒",
                    403: "⛔"
                }.get(r.status_code, "•")
                print(f"  {status_emoji} [{r.status_code}] {r.path}")
                
    except Exception as e:
        print(f"\n\nError during scan: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await engine.close()
        print("\n\n✅ Test completed!")


async def test_with_options():
    """Test with various options"""
    print("\n" + "="*60)
    print("TEST WITH OPTIONS")
    print("="*60)
    
    # Initialize
    LoggerSetup.initialize()
    engine = DirsearchEngine()
    
    target = "http://testphp.vulnweb.com"
    
    # Test 1: Extension scanning
    print("\n1. Testing extension scanning...")
    wordlist = ["index", "config", "readme", "database", "backup"]
    options = ScanOptions(
        threads=5,
        extensions=[".php", ".txt", ".bak", ".old"],
        force_extensions=True
    )
    
    results = await engine.scan_target(target, wordlist, options)
    print(f"   Found {len(results)} results with extensions")
    
    # Test 2: Subdirectory scanning
    print("\n2. Testing subdirectory scanning...")
    wordlist = ["admin", "api", "v1", "v2", "users", "config"]
    options = ScanOptions(
        threads=5,
        recursive=True,
        recursion_depth=1
    )
    
    results = await engine.scan_target(target, wordlist, options)
    print(f"   Found {len(results)} results with recursion")
    
    # Test 3: Custom headers
    print("\n3. Testing with custom headers...")
    wordlist = ["api", "admin", "login"]
    options = ScanOptions(
        threads=5,
        headers={
            "X-Custom-Header": "test",
            "User-Agent": "CustomScanner/1.0"
        }
    )
    
    results = await engine.scan_target(target, wordlist, options)
    print(f"   Found {len(results)} results with custom headers")
    
    await engine.close()
    print("\n✅ Options test completed!")


async def test_callbacks():
    """Test callback functionality"""
    print("\n" + "="*60)
    print("TEST CALLBACKS")
    print("="*60)
    
    # Initialize
    LoggerSetup.initialize()
    engine = DirsearchEngine()
    
    target = "http://testphp.vulnweb.com"
    wordlist = ["admin", "api", "login", "test", "backup"]
    
    # Track findings
    findings = []
    errors = []
    
    # Callbacks
    def on_result(result):
        if result.status_code in [200, 301, 302]:
            findings.append(result)
            print(f"\n  ✓ Found: [{result.status_code}] {result.path}")
    
    def on_error(error):
        errors.append(str(error))
        print(f"\n  ✗ Error: {error}")
    
    def on_progress(current, total):
        print(f"\r  Progress: {current}/{total}", end="", flush=True)
    
    # Set callbacks
    engine.set_result_callback(on_result)
    engine.set_error_callback(on_error)
    engine.set_progress_callback(on_progress)
    
    # Run scan
    options = ScanOptions(threads=5)
    await engine.scan_target(target, wordlist, options)
    
    print(f"\n\nSummary:")
    print(f"  • Findings: {len(findings)}")
    print(f"  • Errors: {len(errors)}")
    
    await engine.close()
    print("\n✅ Callback test completed!")


async def main():
    """Run all tests"""
    tests = [
        ("Basic Scan", test_basic_scan),
        ("Options Test", test_with_options),
        ("Callbacks Test", test_callbacks)
    ]
    
    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        # Run all tests
        for name, test in tests:
            print(f"\n{'='*60}")
            print(f"Running: {name}")
            print(f"{'='*60}")
            await test()
            await asyncio.sleep(1)
    else:
        # Run basic test
        await test_basic_scan()


if __name__ == "__main__":
    print("""
Simple test for dirsearch-mcp

Usage:
    python simple_test.py                    # Run basic test on default target
    python simple_test.py http://example.com # Run basic test on specific target
    python simple_test.py --all              # Run all tests
""")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()