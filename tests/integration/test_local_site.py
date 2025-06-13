#!/usr/bin/env python3
"""
Test all dirsearch features on local website
Target: http://127.0.0.1:8080/
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
from src.config.settings import Settings

console = Console()

# Target URL - extract base URL from login.php
TARGET_URL = "http://127.0.0.1:8080/"


async def run_comprehensive_test():
    """Test all features on local site"""
    console.print(Panel.fit(
        f"[bold]Testing Dirsearch Features[/bold]\n"
        f"Target: {TARGET_URL}",
        border_style="cyan"
    ))
    
    engine = DirsearchEngine(Settings())
    
    # Comprehensive wordlist with extension tags
    wordlist = [
        # Extension tags - will expand to multiple files
        "index.%EXT%",
        "login.%EXT%",
        "admin.%EXT%",
        "config.%EXT%",
        "database.%EXT%",
        "backup.%EXT%",
        "test.%EXT%",
        "api.%EXT%",
        "user.%EXT%",
        "users.%EXT%",
        
        # Common directories
        "admin",
        "administrator",
        "api",
        "backup",
        "backups",
        "config",
        "data",
        "database",
        "db",
        "files",
        "images",
        "img",
        "includes",
        "js",
        "css",
        "lib",
        "logs",
        "private",
        "public",
        "uploads",
        "tmp",
        "temp",
        "test",
        
        # Common files without extension
        "robots.txt",
        ".htaccess",
        ".htpasswd",
        "web.config",
        "sitemap.xml",
        "crossdomain.xml",
        "phpinfo",
        "info",
        "README",
        "LICENSE",
        ".git/config",
        ".env",
        ".gitignore",
        
        # Specific PHP files (since we know login.php exists)
        "index",
        "home",
        "dashboard",
        "panel",
        "logout",
        "register",
        "signup",
        "profile",
        "settings",
        "upload",
        "download",
        "api",
        "ajax",
        "process"
    ]
    
    # Configure all features
    options = ScanOptions(
        # Extension features
        extensions=['php', 'html', 'txt', 'bak', 'old', 'sql', 'zip', 'tar.gz'],
        extension_tag='%EXT%',
        
        # Enable wildcard detection
        detect_wildcards=True,
        
        # Enable content crawling
        crawl=True,
        
        # Random user agents
        random_user_agents=True,
        
        # Blacklist rules
        blacklists={
            403: ['cgi-bin', 'icons', '.ht'],
            500: ['error', 'debug', 'trace']
        },
        
        # Scan configuration
        threads=10,
        timeout=10,
        exclude_status_codes=[404],
        follow_redirects=True
    )
    
    try:
        # Display enabled features
        console.print("\n[bold cyan]Enabled Features:[/bold cyan]")
        feature_table = Table(show_header=False, box=None)
        feature_table.add_column("Feature", style="yellow")
        feature_table.add_column("Status")
        
        feature_table.add_row("Wildcard Detection", "✅ Enabled")
        feature_table.add_row("Extension Tags (%EXT%)", f"✅ {len([w for w in wordlist if '%EXT%' in w])} patterns")
        feature_table.add_row("Extensions", f"✅ {', '.join(options.extensions)}")
        feature_table.add_row("Content Crawling", "✅ Enabled")
        feature_table.add_row("Random User Agents", "✅ Enabled")
        feature_table.add_row("Blacklist Filtering", f"✅ {len(options.blacklists)} rules")
        feature_table.add_row("Threads", str(options.threads))
        
        console.print(feature_table)
        
        # Step 1: Test connectivity
        console.print("\n[bold]Step 1: Testing Connectivity[/bold]")
        test_response = await engine._make_request(TARGET_URL + "login.php", options)
        if test_response:
            console.print(f"✅ Target is accessible: login.php [{test_response.get('status_code')}]")
        else:
            console.print("❌ Cannot connect to target")
            return
        
        # Step 2: Wildcard detection
        console.print("\n[bold]Step 2: Checking for Wildcard Responses[/bold]")
        wildcard_info = await engine._detect_wildcard(TARGET_URL, options)
        if wildcard_info and wildcard_info.get('detected'):
            console.print(f"[yellow]⚠️  Wildcard detected for status {wildcard_info['status']}[/yellow]")
            console.print("   Similar responses will be filtered automatically")
        else:
            console.print("✅ No wildcard behavior detected")
        
        # Step 3: Calculate paths
        console.print("\n[bold]Step 3: Path Generation[/bold]")
        extension_patterns = [w for w in wordlist if '%EXT%' in w]
        regular_paths = [w for w in wordlist if '%EXT%' not in w]
        expanded_paths = len(extension_patterns) * len(options.extensions)
        total_paths = expanded_paths + len(regular_paths)
        
        console.print(f"• Extension patterns: {len(extension_patterns)}")
        console.print(f"• Regular paths: {len(regular_paths)}")
        console.print(f"• Total paths to scan: {total_paths}")
        
        # Step 4: Run the scan
        console.print("\n[bold]Step 4: Running Scan[/bold]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Scanning...", total=None)
            
            start_time = datetime.now()
            results = await engine.scan_target(TARGET_URL, wordlist, options)
            scan_duration = (datetime.now() - start_time).total_seconds()
            
            progress.stop()
        
        # Step 5: Display results
        console.print(f"\n[bold]Step 5: Results[/bold]")
        console.print(f"• Scan duration: {scan_duration:.2f} seconds")
        console.print(f"• Total findings: {len(results)}")
        console.print(f"• Crawled paths: {len(engine._crawled_paths)}")
        
        if results:
            # Group results
            by_status = {}
            directories = []
            files = []
            
            for result in results:
                # By status code
                if result.status_code not in by_status:
                    by_status[result.status_code] = []
                by_status[result.status_code].append(result)
                
                # By type
                if result.is_directory:
                    directories.append(result)
                else:
                    files.append(result)
            
            # Display summary
            console.print(f"\n[bold]Summary:[/bold]")
            console.print(f"• Directories: {len(directories)}")
            console.print(f"• Files: {len(files)}")
            
            # Display by status code
            console.print(f"\n[bold]By Status Code:[/bold]")
            for status in sorted(by_status.keys()):
                console.print(f"\n[{status}] - {len(by_status[status])} results:")
                for result in by_status[status][:5]:
                    type_indicator = "📁" if result.is_directory else "📄"
                    console.print(f"  {type_indicator} {result.path} ({result.size} bytes)")
                if len(by_status[status]) > 5:
                    console.print(f"  ... and {len(by_status[status]) - 5} more")
            
            # Show important findings
            important_keywords = ['admin', 'config', 'backup', 'database', 'api', 'upload']
            important_findings = []
            
            for result in results:
                if any(keyword in result.path.lower() for keyword in important_keywords):
                    important_findings.append(result)
            
            if important_findings:
                console.print(f"\n[bold red]Important Findings:[/bold red]")
                for finding in important_findings[:10]:
                    console.print(f"  [{finding.status_code}] {finding.path}")
            
            # Show crawled paths
            if engine._crawled_paths:
                console.print(f"\n[bold]Paths Discovered via Crawling:[/bold]")
                for path in list(engine._crawled_paths)[:10]:
                    console.print(f"  • {path}")
                if len(engine._crawled_paths) > 10:
                    console.print(f"  ... and {len(engine._crawled_paths) - 10} more")
            
            # Feature effectiveness
            console.print(f"\n[bold]Feature Effectiveness:[/bold]")
            if wildcard_info and wildcard_info.get('detected'):
                console.print("• Wildcard filtering: Active")
            console.print(f"• User agents rotated: Yes")
            console.print(f"• Paths from crawling: {len(engine._crawled_paths)}")
            
            # Export results
            console.print(f"\n[bold]Export Results:[/bold]")
            result_table = Table(title="All Discovered Paths")
            result_table.add_column("Status", style="cyan", width=8)
            result_table.add_column("Type", style="yellow", width=8)
            result_table.add_column("Path", style="white")
            result_table.add_column("Size", style="dim")
            
            for result in sorted(results, key=lambda x: (x.status_code, x.path))[:20]:
                result_table.add_row(
                    str(result.status_code),
                    "DIR" if result.is_directory else "FILE",
                    result.path,
                    f"{result.size} B"
                )
            
            if len(results) > 20:
                result_table.add_row("...", "...", f"... and {len(results) - 20} more results", "...")
            
            console.print(result_table)
            
        else:
            console.print("\n[yellow]No results found. This could mean:[/yellow]")
            console.print("• The server is returning 404 for all paths")
            console.print("• The wordlist doesn't match the site structure")
            console.print("• Access is restricted")
        
        console.print("\n" + "="*60)
        console.print("[bold green]✅ Test completed successfully![/bold green]")
        
    except Exception as e:
        console.print(f"\n[red]❌ Error during test: {e}[/red]")
        import traceback
        traceback.print_exc()
    finally:
        await engine.close()


async def quick_test():
    """Quick test to verify specific functionality"""
    console.print("\n[bold]Quick Feature Test[/bold]")
    console.print("="*40)
    
    engine = DirsearchEngine(Settings())
    
    # Test with known path
    known_paths = ["login.php", "index.php", "admin.php"]
    
    options = ScanOptions(
        threads=5,
        timeout=10,
        exclude_status_codes=[404]
    )
    
    try:
        results = await engine.scan_target(TARGET_URL, known_paths, options)
        
        console.print(f"Testing {len(known_paths)} known paths:")
        for path in known_paths:
            found = any(r.path == path for r in results)
            status = "✅ Found" if found else "❌ Not found"
            console.print(f"  {path}: {status}")
            
    finally:
        await engine.close()


async def main():
    """Main entry point"""
    # Run quick test first
    await quick_test()
    
    # Then run comprehensive test
    await run_comprehensive_test()


if __name__ == "__main__":
    asyncio.run(main())