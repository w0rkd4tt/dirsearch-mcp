#!/usr/bin/env python3
"""
Quick test example for dirsearch-mcp
Simple examples to get started quickly
"""
import asyncio
from src.core.dirsearch_engine import DirsearchEngine, ScanOptions
from src.utils.logger import LoggerSetup


async def simple_scan():
    """Example 1: Simplest possible scan"""
    print("\n=== Simple Scan Example ===")
    
    # Initialize
    LoggerSetup.initialize()
    engine = DirsearchEngine()
    
    # Target and wordlist
    target = "http://testphp.vulnweb.com"
    wordlist = ["admin", "login", "api", "test", "backup"]
    
    # Run scan with default options
    results = await engine.scan_target(target, wordlist)
    
    # Print results
    print(f"\nFound {len(results)} results:")
    for result in results:
        print(f"  [{result.status_code}] {result.path}")
        
    await engine.close()


async def scan_with_options():
    """Example 2: Scan with custom options"""
    print("\n=== Scan with Options Example ===")
    
    # Initialize
    LoggerSetup.initialize()
    engine = DirsearchEngine()
    
    # Configure options
    options = ScanOptions(
        threads=20,              # Use 20 threads
        timeout=15,              # 15 second timeout
        recursive=True,          # Enable recursive scanning
        recursion_depth=2,       # Go 2 levels deep
        extensions=[".php", ".bak"],  # Check these extensions
        detect_wildcards=True    # Detect wildcard responses
    )
    
    # Target and wordlist
    target = "http://testphp.vulnweb.com"
    wordlist = ["admin", "api", "backup", "config", "data", "files", "upload"]
    
    # Run scan
    results = await engine.scan_target(target, wordlist, options)
    
    # Print results grouped by status
    print(f"\nFound {len(results)} results:")
    
    # Group by status code
    by_status = {}
    for r in results:
        by_status.setdefault(r.status_code, []).append(r)
    
    for status, items in sorted(by_status.items()):
        print(f"\n[{status}] Status Code:")
        for item in items:
            print(f"  - {item.path} ({item.size} bytes)")
            
    await engine.close()


async def scan_with_callbacks():
    """Example 3: Scan with progress callbacks"""
    print("\n=== Scan with Callbacks Example ===")
    
    # Initialize
    LoggerSetup.initialize()
    engine = DirsearchEngine()
    
    # Define callbacks
    def on_progress(current: int, total: int):
        print(f"\rProgress: {current}/{total} ({current/total*100:.1f}%)", end="")
        
    def on_result(result):
        if result.status_code in [200, 301, 302]:
            print(f"\n✓ Found: [{result.status_code}] {result.path}")
            
    def on_error(error):
        print(f"\n✗ Error: {error}")
    
    # Set callbacks
    engine.set_progress_callback(on_progress)
    engine.set_result_callback(on_result)
    engine.set_error_callback(on_error)
    
    # Configure and run
    target = "http://testphp.vulnweb.com"
    wordlist = ["admin", "api", "login", "test", "backup", "config", "uploads"]
    options = ScanOptions(threads=5, timeout=10)
    
    results = await engine.scan_target(target, wordlist, options)
    
    print(f"\n\nScan complete! Total results: {len(results)}")
    
    await engine.close()


async def scan_subdirectory():
    """Example 4: Scan a specific subdirectory"""
    print("\n=== Subdirectory Scan Example ===")
    
    # Initialize
    LoggerSetup.initialize()
    engine = DirsearchEngine()
    
    # Target subdirectory
    target = "http://testphp.vulnweb.com/admin/"
    wordlist = ["users", "settings", "config", "dashboard", "login", "logout"]
    
    options = ScanOptions(
        threads=10,
        recursive=False  # Don't scan recursively in subdirectory
    )
    
    print(f"Scanning subdirectory: {target}")
    
    results = await engine.scan_target(target, wordlist, options)
    
    print(f"\nResults in /admin/:")
    for r in results:
        print(f"  [{r.status_code}] {r.path}")
        
    await engine.close()


async def scan_with_extensions():
    """Example 5: Scan for files with specific extensions"""
    print("\n=== Extension Scan Example ===")
    
    # Initialize
    LoggerSetup.initialize()
    engine = DirsearchEngine()
    
    # Base paths (without extensions)
    wordlist = ["index", "config", "database", "backup", "readme"]
    
    # Options with extensions
    options = ScanOptions(
        extensions=[".php", ".txt", ".bak", ".old", ".log"],
        force_extensions=True  # Add extensions to all paths
    )
    
    target = "http://testphp.vulnweb.com"
    
    print(f"Scanning for files with extensions: {options.extensions}")
    
    results = await engine.scan_target(target, wordlist, options)
    
    print(f"\nFound files:")
    for r in results:
        if '.' in r.path:  # Has extension
            print(f"  [{r.status_code}] {r.path}")
            
    await engine.close()


async def intelligent_scan():
    """Example 6: Intelligent scan with insights"""
    print("\n=== Intelligent Scan Example ===")
    
    # Initialize
    LoggerSetup.initialize()
    engine = DirsearchEngine()
    
    # Extended wordlist
    wordlist = [
        "admin", "administrator", "login", "dashboard",
        "api", "v1", "v2", "swagger", "docs",
        "backup", "backups", "old", "temp",
        "config", "configuration", "settings",
        ".git", ".env", ".htaccess", "robots.txt"
    ]
    
    options = ScanOptions(
        threads=15,
        recursive=True,
        recursion_depth=2,
        detect_wildcards=True,
        crawl=True  # Enable content crawling
    )
    
    target = "http://testphp.vulnweb.com"
    
    print("Running intelligent scan...")
    
    results = await engine.scan_target(target, wordlist, options)
    
    # Get insights
    insights = engine.get_scan_insights()
    
    print(f"\n=== Scan Results ===")
    print(f"Total findings: {len(results)}")
    
    print(f"\n=== Insights ===")
    if insights.get('important_paths'):
        print(f"Important paths: {', '.join(insights['important_paths'][:5])}")
        
    if insights.get('technology_hints'):
        print(f"Technologies detected: {', '.join(insights['technology_hints'])}")
        
    if insights.get('risk_assessment'):
        risk = insights['risk_assessment']
        print(f"Risk level: {risk['level']} (Score: {risk['score']}/100)")
        
    if insights.get('recommendations'):
        print("\nRecommendations:")
        for rec in insights['recommendations'][:3]:
            print(f"  - {rec}")
            
    await engine.close()


# Main menu
async def main():
    """Run examples"""
    print("""
╔══════════════════════════════════════════╗
║        DIRSEARCH-MCP QUICK TEST          ║
╚══════════════════════════════════════════╝

Select an example to run:

1. Simple scan (basic usage)
2. Scan with custom options
3. Scan with progress callbacks
4. Subdirectory scan
5. Extension-based scan
6. Intelligent scan with insights
7. Run all examples

0. Exit
""")
    
    choice = input("Enter your choice (0-7): ").strip()
    
    examples = {
        "1": simple_scan,
        "2": scan_with_options,
        "3": scan_with_callbacks,
        "4": scan_subdirectory,
        "5": scan_with_extensions,
        "6": intelligent_scan
    }
    
    if choice == "0":
        print("Exiting...")
        return
    elif choice == "7":
        # Run all examples
        for name, func in examples.items():
            await func()
            await asyncio.sleep(1)  # Small delay between examples
    elif choice in examples:
        await examples[choice]()
    else:
        print("Invalid choice!")
        

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()