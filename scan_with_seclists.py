#!/usr/bin/env python3
"""
Example: Using SecLists wordlists with dirsearch-mcp
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

async def scan_with_seclists():
    """Demo scan using SecLists wordlist"""
    from src.core.dirsearch_engine import DirsearchEngine, ScanRequest
    from src.config.settings import Settings
    
    # Create settings
    settings = Settings()
    
    # Create engine
    engine = DirsearchEngine(settings)
    
    # Create scan request with SecLists wordlist
    scan_request = ScanRequest(
        base_url="http://example.com",
        wordlist="/Users/datnlq/SecLists/Discovery/Web-Content/common.txt",
        extensions=["php", "html", "txt", "asp"],
        threads=20,
        timeout=10,
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        follow_redirects=True,
        exclude_status="404"
    )
    
    print("🎯 Dirsearch MCP with SecLists")
    print("=" * 50)
    print(f"Target: {scan_request.base_url}")
    print(f"Wordlist: {scan_request.wordlist}")
    print(f"Extensions: {', '.join(scan_request.extensions)}")
    print(f"Threads: {scan_request.threads}")
    print("=" * 50)
    
    try:
        # Execute scan
        print("\n⏳ Starting scan...")
        response = await engine.execute_scan(scan_request)
        
        print(f"\n✅ Scan completed!")
        print(f"Duration: {response.duration:.2f}s")
        print(f"Total requests: {response.statistics.get('total_requests', 0)}")
        print(f"Found paths: {response.statistics.get('found_paths', 0)}")
        
        # Show results
        if response.results:
            print(f"\n📋 Results (showing first 10):")
            for result in response.results[:10]:
                print(f"  [{result['status']}] {result['path']} - {result['size']} bytes")
                
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

# Command line usage
def main():
    """Main entry point with command line support"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Scan with SecLists wordlists')
    parser.add_argument('url', help='Target URL to scan')
    parser.add_argument('--wordlist', '-w', 
                       default='/Users/datnlq/SecLists/Discovery/Web-Content/common.txt',
                       help='Path to wordlist (default: SecLists common.txt)')
    parser.add_argument('--extensions', '-e', 
                       default='php,html,txt,asp',
                       help='File extensions (comma-separated)')
    parser.add_argument('--threads', '-t', type=int, default=20,
                       help='Number of threads (default: 20)')
    
    args = parser.parse_args()
    
    # Create custom scan function with args
    async def custom_scan():
        from src.core.dirsearch_engine import DirsearchEngine, ScanRequest
        from src.config.settings import Settings
        
        settings = Settings()
        engine = DirsearchEngine(settings)
        
        scan_request = ScanRequest(
            base_url=args.url,
            wordlist=args.wordlist,
            extensions=args.extensions.split(','),
            threads=args.threads,
            timeout=10,
            exclude_status="404"
        )
        
        print(f"🎯 Scanning {args.url}")
        print(f"📁 Wordlist: {Path(args.wordlist).name}")
        print(f"🔧 Extensions: {args.extensions}")
        print(f"⚡ Threads: {args.threads}")
        print("-" * 50)
        
        response = await engine.execute_scan(scan_request)
        
        print(f"\n✅ Completed in {response.duration:.2f}s")
        print(f"📊 Total requests: {response.statistics.get('total_requests', 0)}")
        print(f"🎯 Found: {response.statistics.get('found_paths', 0)} paths")
        
        if response.results:
            print(f"\n📋 Top findings:")
            for r in response.results[:10]:
                status_color = "🟢" if r['status'] == 200 else "🟡" if r['status'] in [301,302] else "🔴"
                print(f"{status_color} [{r['status']}] {r['path']}")
    
    asyncio.run(custom_scan())

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main()
    else:
        # Run demo
        asyncio.run(scan_with_seclists())