#!/usr/bin/env python3
"""
Simple integration example for Dirsearch MCP
Shows basic usage as a Python library
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.integration import DirsearchMCP, ScanOptions


async def main():
    """Simple scanning example"""
    # Initialize Dirsearch MCP
    print("Initializing Dirsearch MCP...")
    dirsearch = DirsearchMCP()
    
    # Set up event handlers to see real-time results
    dirsearch.on_finding(lambda f: print(f"[{f['status']}] {f['path']} - {f['size']} bytes"))
    dirsearch.on_error(lambda e: print(f"Error: {e}"))
    
    # Initialize (loads MCP coordinator, plugins, etc.)
    await dirsearch.initialize()
    
    # Configure scan options
    options = ScanOptions(
        wordlist="common.txt",      # Use common wordlist
        extensions=["php", "html"],  # Look for PHP and HTML files
        threads=15,                  # 15 concurrent threads
        timeout=10,                  # 10 second timeout per request
        use_mcp=True                # Use MCP intelligence
    )
    
    # Target to scan
    target = "https://example.com"
    
    print(f"\nScanning {target}...")
    print(f"Options: {options.threads} threads, extensions: {options.extensions}")
    print("-" * 50)
    
    try:
        # Perform the scan
        scan_data = await dirsearch.scan(target, options)
        
        # Display results summary
        print("\n" + "=" * 50)
        print("SCAN COMPLETE")
        print("=" * 50)
        print(f"Target: {scan_data.target}")
        print(f"Duration: {scan_data.duration:.2f} seconds")
        print(f"Total requests: {scan_data.statistics.get('total_requests', 0)}")
        print(f"Total findings: {scan_data.total_findings}")
        print(f"Successful (200): {len(scan_data.successful_findings)}")
        print(f"Auth required (401/403): {len(scan_data.auth_required_findings)}")
        print(f"Redirects (3xx): {len(scan_data.redirect_findings)}")
        
        # Show technologies detected
        if scan_data.target_info.technology_stack:
            print(f"\nDetected technologies: {', '.join(scan_data.target_info.technology_stack)}")
        if scan_data.target_info.detected_cms:
            print(f"CMS: {scan_data.target_info.detected_cms}")
            
        # Show top findings
        if scan_data.successful_findings:
            print(f"\nTop {min(5, len(scan_data.successful_findings))} successful findings:")
            for result in scan_data.successful_findings[:5]:
                print(f"  - {result.path} ({result.size} bytes)")
                
        # Generate report
        print("\nGenerating reports...")
        reports = await dirsearch.generate_report(
            scan_data,
            output_dir="./simple_scan_reports",
            formats=["json", "html"]
        )
        
        print("Reports saved:")
        for fmt, path in reports.items():
            print(f"  - {fmt}: {path}")
            
    except Exception as e:
        print(f"\nScan failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("Dirsearch MCP - Simple Integration Example")
    print("==========================================\n")
    
    # Run the async main function
    asyncio.run(main())