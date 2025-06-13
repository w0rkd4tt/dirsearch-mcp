#!/usr/bin/env python3
"""
Test dirsearch and show ALL results including 404s
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.dirsearch_engine import DirsearchEngine, ScanOptions
from src.config.settings import Settings

console = Console()


async def scan_show_all(target_url):
    """Scan and show ALL results"""
    
    console.print(Panel.fit(
        f"[bold]Dirsearch - Show ALL Results[/bold]\n"
        f"Target: {target_url}",
        border_style="cyan"
    ))
    
    engine = DirsearchEngine(Settings())
    
    # Comprehensive wordlist
    wordlist = [
        # Directories
        "admin",
        "api",
        "app",
        "assets", 
        "backup",
        "config",
        "css",
        "data",
        "database",
        "db",
        "files",
        "images",
        "img",
        "includes",
        "js",
        "lib",
        "logs",
        "panel",
        "private",
        "public",
        "system",
        "test",
        "tmp",
        "upload",
        "uploads",
        "user",
        "users",
        
        # Files with extension tags
        "index.%EXT%",
        "login.%EXT%",
        "admin.%EXT%",
        "config.%EXT%",
        "test.%EXT%",
        "info.%EXT%",
        "phpinfo.%EXT%",
        
        # Common files
        "robots.txt",
        ".htaccess",
        "sitemap.xml",
        ".env",
        ".git/config",
        "web.config",
        
        # PHP specific
        "index.php",
        "login.php", 
        "logout.php",
        "register.php",
        "dashboard.php",
        "profile.php",
        "settings.php",
        "upload.php",
        "download.php",
        "process.php",
        "api.php",
        "config.php",
        "database.php",
        "connection.php",
        "functions.php",
        "common.php",
        "init.php",
        "install.php",
        "setup.php",
        "phpinfo.php",
        "info.php",
        "test.php"
    ]
    
    # Options - NO STATUS CODE FILTERING
    options = ScanOptions(
        # Extensions
        extensions=['php', 'html', 'txt', 'bak', 'sql', 'zip'],
        extension_tag='%EXT%',
        
        # Features
        detect_wildcards=True,
        crawl=True,
        random_user_agents=True,
        
        # IMPORTANT: Don't exclude any status codes
        exclude_status_codes=[],  # Empty list = show all results
        
        # Basic settings
        threads=10,
        timeout=10,
        follow_redirects=True
    )
    
    try:
        # Test connectivity
        console.print("\n[bold]1. Testing connectivity...[/bold]")
        test_response = await engine._make_request(target_url, options)
        if test_response:
            console.print(f"✅ Target accessible: Status {test_response.get('status_code')}")
        else:
            console.print("❌ Cannot connect to target")
            return
        
        # Check wildcards
        console.print("\n[bold]2. Checking for wildcards...[/bold]")
        wildcard_info = await engine._detect_wildcard(target_url, options)
        if wildcard_info and wildcard_info.get('detected'):
            console.print(f"⚠️  Wildcard detected for status {wildcard_info['status']}")
        else:
            console.print("✅ No wildcard detected")
        
        # Run scan
        console.print(f"\n[bold]3. Scanning {len(wordlist)} paths...[/bold]")
        
        start_time = datetime.now()
        results = await engine.scan_target(target_url, wordlist, options)
        duration = (datetime.now() - start_time).total_seconds()
        
        console.print(f"\n✅ Scan completed in {duration:.2f} seconds")
        console.print(f"Total results: {len(results)}")
        
        if results:
            # Group by status code
            by_status = {}
            for r in results:
                if r.status_code not in by_status:
                    by_status[r.status_code] = []
                by_status[r.status_code].append(r)
            
            # Create comprehensive table
            result_table = Table(title="ALL Scan Results", show_lines=True)
            result_table.add_column("Status", style="cyan", width=8)
            result_table.add_column("Type", style="yellow", width=8)
            result_table.add_column("Path", style="white")
            result_table.add_column("Size", style="dim", width=10)
            result_table.add_column("Content Type", style="dim")
            
            # Show all results sorted by status and path
            for status in sorted(by_status.keys()):
                for result in sorted(by_status[status], key=lambda x: x.path):
                    type_str = "DIR" if result.is_directory else "FILE"
                    result_table.add_row(
                        str(result.status_code),
                        type_str,
                        result.path,
                        f"{result.size} B",
                        result.content_type or ""
                    )
            
            console.print(result_table)
            
            # Summary by status
            console.print("\n[bold]Summary by Status Code:[/bold]")
            for status in sorted(by_status.keys()):
                count = len(by_status[status])
                status_name = {
                    200: "OK",
                    301: "Moved Permanently", 
                    302: "Found",
                    403: "Forbidden",
                    404: "Not Found",
                    500: "Internal Server Error"
                }.get(status, "Unknown")
                
                console.print(f"\n[{status}] {status_name} - {count} results:")
                
                # Show some examples
                examples = by_status[status][:5]
                for ex in examples:
                    console.print(f"  • {ex.path}")
                if count > 5:
                    console.print(f"  ... and {count - 5} more")
            
            # Show directories only
            directories = [r for r in results if r.is_directory]
            if directories:
                console.print(f"\n[bold green]Directories Found ({len(directories)}):[/bold green]")
                for d in directories:
                    console.print(f"  [{d.status_code}] {d.path}")
            
            # Show successful (2xx) results
            successful = [r for r in results if 200 <= r.status_code < 300]
            if successful:
                console.print(f"\n[bold green]Successful Paths ({len(successful)}):[/bold green]")
                for s in successful:
                    console.print(f"  {s.path} ({s.size} bytes)")
            
            # Show forbidden (403) results - often interesting
            forbidden = [r for r in results if r.status_code == 403]
            if forbidden:
                console.print(f"\n[bold yellow]Forbidden Paths ({len(forbidden)}):[/bold yellow]")
                for f in forbidden:
                    console.print(f"  {f.path}")
            
            # Show crawled paths
            if engine._crawled_paths:
                console.print(f"\n[bold]Paths from Crawling ({len(engine._crawled_paths)}):[/bold]")
                for path in list(engine._crawled_paths)[:10]:
                    console.print(f"  • {path}")
                if len(engine._crawled_paths) > 10:
                    console.print(f"  ... and {len(engine._crawled_paths) - 10} more")
            
        else:
            console.print("\n[yellow]No results found[/yellow]")
        
        console.print("\n" + "="*60)
        console.print("[bold]Scan Complete![/bold]")
        
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
    finally:
        await engine.close()


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        console.print("[bold]Dirsearch - Show ALL Results[/bold]")
        console.print("\nUsage: python test_all_results.py <target_url>")
        console.print("Example: python test_all_results.py http://127.0.0.1:8080/")
        sys.exit(1)
    
    target_url = sys.argv[1]
    if not target_url.startswith(('http://', 'https://')):
        target_url = 'http://' + target_url
    
    if not target_url.endswith('/'):
        target_url += '/'
    
    asyncio.run(scan_show_all(target_url))


if __name__ == "__main__":
    main()