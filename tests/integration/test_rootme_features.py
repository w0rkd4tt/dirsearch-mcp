#!/usr/bin/env python3
"""
Test all migrated dirsearch features on Root-Me challenge website
Target: http://challenge01.root-me.org/web-serveur/ch4/
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.dirsearch_engine import DirsearchEngine, ScanOptions
from src.config import Settings

console = Console()

# Target URL
TARGET_URL = "http://challenge01.root-me.org/web-serveur/ch4/"


async def test_wildcard_detection():
    """Test wildcard detection on target"""
    console.print("\n[bold cyan]1. Testing Wildcard Detection[/bold cyan]")
    
    engine = DirsearchEngine(Settings())
    options = ScanOptions(
        detect_wildcards=True,
        threads=5,
        timeout=10
    )
    
    try:
        wildcard_info = await engine._detect_wildcard(TARGET_URL, options)
        if wildcard_info and wildcard_info.get('detected'):
            console.print(f"[yellow]⚠️  Wildcard detected for status {wildcard_info['status']}[/yellow]")
            console.print(f"   This means the server returns similar responses for random paths")
        else:
            console.print("[green]✅ No wildcard detected - Good for scanning![/green]")
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
    finally:
        await engine.close()


async def test_extension_scan():
    """Test extension tag feature with common extensions"""
    console.print("\n[bold cyan]2. Testing Extension Tags (%EXT%)[/bold cyan]")
    
    engine = DirsearchEngine(Settings())
    
    # Small wordlist with extension tags
    wordlist = [
        "admin.%EXT%",
        "config.%EXT%",
        "backup.%EXT%",
        "login.%EXT%",
        "index.%EXT%"
    ]
    
    options = ScanOptions(
        extensions=['php', 'html', 'txt', 'bak'],
        extension_tag='%EXT%',
        threads=5,
        timeout=10,
        exclude_status_codes=[404]
    )
    
    console.print(f"[dim]Testing {len(wordlist)} patterns with {len(options.extensions)} extensions[/dim]")
    
    try:
        results = await engine.scan_target(TARGET_URL, wordlist, options)
        
        if results:
            console.print(f"[green]✅ Found {len(results)} paths:[/green]")
            for result in results[:5]:
                console.print(f"   [{result.status_code}] {result.path}")
            if len(results) > 5:
                console.print(f"   ... and {len(results) - 5} more")
        else:
            console.print("[yellow]No paths found with extension tags[/yellow]")
            
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
    finally:
        await engine.close()


async def test_authentication():
    """Test authentication methods (may not be needed for this target)"""
    console.print("\n[bold cyan]3. Testing Authentication Support[/bold cyan]")
    
    engine = DirsearchEngine(Settings())
    
    # Test if authentication handlers are available
    auth_types = ['basic', 'digest', 'ntlm']
    for auth_type in auth_types:
        handler = engine._get_auth_handler(auth_type, ('test', 'test'))
        if handler:
            console.print(f"[green]✅ {auth_type.upper()} authentication: Available[/green]")
        else:
            console.print(f"[yellow]⚠️  {auth_type.upper()} authentication: Not available[/yellow]")
    
    await engine.close()


async def test_crawling():
    """Test content crawling on discovered pages"""
    console.print("\n[bold cyan]4. Testing Content Crawling[/bold cyan]")
    
    engine = DirsearchEngine(Settings())
    
    # First find some pages to crawl
    wordlist = ['index', 'admin', 'login', 'robots.txt']
    
    options = ScanOptions(
        crawl=True,  # Enable crawling
        extensions=['php', 'html', 'txt'],
        threads=5,
        timeout=10,
        exclude_status_codes=[404]
    )
    
    try:
        console.print("[dim]Scanning and crawling for additional paths...[/dim]")
        results = await engine.scan_target(TARGET_URL, wordlist, options)
        
        # Check if any paths were discovered through crawling
        crawled = len(engine._crawled_paths)
        if crawled > 0:
            console.print(f"[green]✅ Crawling discovered {crawled} additional paths[/green]")
            for path in list(engine._crawled_paths)[:5]:
                console.print(f"   - {path}")
        else:
            console.print("[yellow]No additional paths discovered through crawling[/yellow]")
            
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
    finally:
        await engine.close()


async def test_blacklists():
    """Test blacklist filtering"""
    console.print("\n[bold cyan]5. Testing Blacklist Filtering[/bold cyan]")
    
    engine = DirsearchEngine(Settings())
    
    # Define custom blacklists
    blacklists = {
        403: ['cgi-bin', 'icons', '.htaccess'],
        500: ['error', 'debug']
    }
    
    wordlist = ['cgi-bin/test', 'icons/folder', 'admin', 'error.log', 'index']
    
    options = ScanOptions(
        blacklists=blacklists,
        extensions=['php'],
        threads=5,
        timeout=10
    )
    
    try:
        console.print("[dim]Testing with blacklist rules...[/dim]")
        console.print(f"[dim]403 blacklist: {', '.join(blacklists[403])}[/dim]")
        console.print(f"[dim]500 blacklist: {', '.join(blacklists[500])}[/dim]")
        
        results = await engine.scan_target(TARGET_URL, wordlist, options)
        
        # The blacklisted paths should be filtered out if they return the specified status codes
        console.print(f"[green]✅ Scan completed with blacklist filtering[/green]")
        console.print(f"   Results after filtering: {len(results)} paths")
        
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
    finally:
        await engine.close()


async def test_random_user_agents():
    """Test random user agent rotation"""
    console.print("\n[bold cyan]6. Testing Random User Agents[/bold cyan]")
    
    engine = DirsearchEngine(Settings())
    
    # Get some sample user agents
    user_agents = set()
    for _ in range(5):
        ua = engine._get_random_user_agent()
        user_agents.add(ua)
    
    console.print(f"[green]✅ Random user agents available: {len(user_agents)} different agents[/green]")
    console.print("[dim]Sample user agents:[/dim]")
    for ua in list(user_agents)[:3]:
        console.print(f"   - {ua[:60]}...")
    
    await engine.close()


async def test_full_featured_scan():
    """Run a full scan with all features enabled"""
    console.print("\n[bold cyan]7. Full Featured Scan[/bold cyan]")
    
    engine = DirsearchEngine(Settings())
    
    # Comprehensive wordlist with extension tags
    wordlist = [
        # Extension tags
        "admin.%EXT%",
        "config.%EXT%",
        "login.%EXT%",
        "backup.%EXT%",
        # Regular paths
        "admin",
        "administrator",
        "login",
        "panel",
        "console",
        "robots.txt",
        ".htaccess",
        # Common files
        "index",
        "default",
        "test"
    ]
    
    options = ScanOptions(
        # Extension features
        extensions=['php', 'html', 'txt', 'bak', 'old'],
        extension_tag='%EXT%',
        
        # Wildcard detection
        detect_wildcards=True,
        
        # Crawling
        crawl=True,
        
        # Random user agents
        random_user_agents=True,
        
        # Blacklists
        blacklists={
            403: ['cgi-bin', 'icons'],
            500: ['error']
        },
        
        # Basic settings
        threads=10,
        timeout=15,
        exclude_status_codes=[404]
    )
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Running full featured scan...", total=None)
        
        try:
            start_time = datetime.now()
            results = await engine.scan_target(TARGET_URL, wordlist, options)
            scan_time = (datetime.now() - start_time).total_seconds()
            
            progress.stop()
            
            # Display results
            console.print(f"\n[bold green]✅ Scan completed in {scan_time:.2f} seconds[/bold green]")
            console.print(f"[green]Found {len(results)} paths[/green]")
            
            if results:
                # Group by status code
                by_status = {}
                for result in results:
                    status = result.status_code
                    if status not in by_status:
                        by_status[status] = []
                    by_status[status].append(result)
                
                # Display table
                table = Table(title="Discovered Paths", show_header=True)
                table.add_column("Status", style="cyan", width=8)
                table.add_column("Path", style="white")
                table.add_column("Size", style="dim", width=10)
                table.add_column("Type", style="yellow", width=10)
                
                for status in sorted(by_status.keys()):
                    for result in by_status[status][:3]:  # Show first 3 per status
                        file_type = "DIR" if result.is_directory else "FILE"
                        table.add_row(
                            str(status),
                            result.path,
                            f"{result.size} B",
                            file_type
                        )
                    if len(by_status[status]) > 3:
                        table.add_row(
                            "...",
                            f"... and {len(by_status[status]) - 3} more with status {status}",
                            "...",
                            "..."
                        )
                
                console.print(table)
                
                # Show feature usage
                console.print("\n[bold]Feature Usage Summary:[/bold]")
                console.print(f"• Wildcard detection: {'Yes' if options.detect_wildcards else 'No'}")
                console.print(f"• Paths crawled: {len(engine._crawled_paths)}")
                console.print(f"• Extension variations tested: {len(options.extensions)}")
                console.print(f"• Random user agents: {'Enabled' if options.random_user_agents else 'Disabled'}")
                console.print(f"• Blacklist rules: {len(options.blacklists) if options.blacklists else 0}")
                
        except Exception as e:
            progress.stop()
            console.print(f"[red]❌ Error during scan: {e}[/red]")
    
    await engine.close()


async def main():
    """Run all feature tests"""
    console.print(Panel.fit(
        f"[bold]Testing Dirsearch Features on Root-Me[/bold]\n"
        f"Target: {TARGET_URL}",
        border_style="cyan"
    ))
    
    tests = [
        ("Wildcard Detection", test_wildcard_detection),
        ("Extension Tags", test_extension_scan),
        ("Authentication", test_authentication),
        ("Content Crawling", test_crawling),
        ("Blacklist Filtering", test_blacklists),
        ("Random User Agents", test_random_user_agents),
        ("Full Featured Scan", test_full_featured_scan)
    ]
    
    # Ask user which tests to run
    console.print("\n[bold]Select tests to run:[/bold]")
    console.print("1. Run all tests")
    console.print("2. Run full featured scan only")
    console.print("3. Exit")
    
    choice = input("\nEnter choice (1-3): ")
    
    if choice == "1":
        for name, test_func in tests:
            await test_func()
            console.print("\n" + "="*50)
    elif choice == "2":
        await test_full_featured_scan()
    else:
        console.print("[yellow]Exiting...[/yellow]")
        return
    
    console.print("\n[bold green]✅ All tests completed![/bold green]")
    console.print(f"\n[dim]Target tested: {TARGET_URL}[/dim]")


if __name__ == "__main__":
    asyncio.run(main())