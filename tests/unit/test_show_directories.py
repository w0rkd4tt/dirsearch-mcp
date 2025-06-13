#!/usr/bin/env python3
"""
Test dirsearch and show all directory results
Usage: python test_show_directories.py <target_url>
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


async def scan_and_show_directories(target_url):
    """Scan target and display all directory results"""
    
    console.print(Panel.fit(
        f"[bold]Directory Scanner[/bold]\n"
        f"Target: {target_url}",
        border_style="cyan"
    ))
    
    engine = DirsearchEngine(Settings())
    
    # Comprehensive directory-focused wordlist
    directory_wordlist = [
        # Common directories
        "admin",
        "administrator",
        "api",
        "app",
        "application",
        "assets",
        "backup",
        "backups",
        "bin",
        "cache",
        "cgi-bin",
        "classes",
        "common",
        "conf",
        "config",
        "configuration",
        "content",
        "core",
        "css",
        "data",
        "database",
        "db",
        "demo",
        "dev",
        "development",
        "dist",
        "doc",
        "docs",
        "documentation",
        "download",
        "downloads",
        "error",
        "errors",
        "examples",
        "files",
        "fonts",
        "forum",
        "framework",
        "help",
        "home",
        "html",
        "images",
        "img",
        "imgs",
        "inc",
        "include",
        "includes",
        "js",
        "javascript",
        "lib",
        "library",
        "libs",
        "log",
        "logs",
        "mail",
        "media",
        "misc",
        "modules",
        "old",
        "panel",
        "php",
        "phpMyAdmin",
        "phpmyadmin",
        "plugin",
        "plugins",
        "private",
        "public",
        "resource",
        "resources",
        "script",
        "scripts",
        "secure",
        "server",
        "service",
        "services",
        "site",
        "sites",
        "src",
        "static",
        "stats",
        "storage",
        "style",
        "styles",
        "system",
        "temp",
        "template",
        "templates",
        "test",
        "tests",
        "theme",
        "themes",
        "tmp",
        "tools",
        "upload",
        "uploads",
        "user",
        "users",
        "util",
        "utils",
        "vendor",
        "view",
        "views",
        "web",
        "webroot",
        "wp-admin",
        "wp-content",
        "wp-includes",
        
        # Version control
        ".git",
        ".svn",
        ".hg",
        
        # Hidden directories
        ".well-known",
        ".vscode",
        ".idea",
        
        # API versions
        "v1",
        "v2",
        "api/v1",
        "api/v2",
        
        # Language specific
        "en",
        "es",
        "fr",
        
        # Years (for backups)
        "2020",
        "2021",
        "2022",
        "2023",
        "2024",
        
        # CMS specific
        "wp-admin",
        "wp-content",
        "wp-includes",
        "administrator",
        "components",
        "modules",
        "plugins",
        "themes",
        
        # Framework specific
        "app",
        "application",
        "public",
        "resources",
        "storage",
        "vendor"
    ]
    
    # Also scan for files that might reveal directories
    file_wordlist = [
        "robots.txt",
        "sitemap.xml",
        ".htaccess",
        "web.config",
        "index.html",
        "index.php",
        "readme.txt",
        "README.md"
    ]
    
    # Combine wordlists
    full_wordlist = directory_wordlist + file_wordlist
    
    # Configure options for directory detection
    options = ScanOptions(
        threads=15,
        timeout=10,
        exclude_status_codes=[404],
        follow_redirects=True,
        detect_wildcards=True,
        crawl=True,  # Enable crawling to find more directories
        random_user_agents=True
    )
    
    try:
        # Test connectivity
        console.print("\n[bold]Testing connectivity...[/bold]")
        test_response = await engine._make_request(target_url, options)
        if not test_response:
            console.print("[red]❌ Cannot connect to target[/red]")
            return
        console.print(f"[green]✅ Target is accessible[/green]")
        
        # Check for wildcards
        console.print("\n[bold]Checking for wildcard responses...[/bold]")
        wildcard_info = await engine._detect_wildcard(target_url, options)
        if wildcard_info and wildcard_info.get('detected'):
            console.print(f"[yellow]⚠️  Wildcard detected for status {wildcard_info['status']}[/yellow]")
        else:
            console.print("[green]✅ No wildcard detected[/green]")
        
        # Run scan
        console.print(f"\n[bold]Scanning {len(full_wordlist)} paths...[/bold]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Scanning directories...", total=None)
            
            start_time = datetime.now()
            results = await engine.scan_target(target_url, full_wordlist, options)
            duration = (datetime.now() - start_time).total_seconds()
            
            progress.stop()
        
        console.print(f"\nScan completed in {duration:.2f} seconds")
        
        # Separate directories and files
        directories = []
        files = []
        
        for result in results:
            if result.is_directory:
                directories.append(result)
            else:
                files.append(result)
        
        # Also check crawled paths for directories
        if engine._crawled_paths:
            console.print(f"\n[dim]Also found {len(engine._crawled_paths)} paths via crawling[/dim]")
        
        # Display directory results
        console.print(f"\n[bold green]Found {len(directories)} directories:[/bold green]")
        
        if directories:
            # Group by status code
            dir_by_status = {}
            for d in directories:
                if d.status_code not in dir_by_status:
                    dir_by_status[d.status_code] = []
                dir_by_status[d.status_code].append(d)
            
            # Create detailed table
            dir_table = Table(title="All Discovered Directories", show_lines=True)
            dir_table.add_column("Status", style="cyan", width=8)
            dir_table.add_column("Directory Path", style="green")
            dir_table.add_column("Size", style="dim", width=10)
            dir_table.add_column("Redirect", style="yellow")
            
            # Sort directories by status code and path
            all_dirs = sorted(directories, key=lambda x: (x.status_code, x.path))
            
            for directory in all_dirs:
                redirect_info = ""
                if directory.redirect_url:
                    redirect_info = f"→ {directory.redirect_url}"
                
                dir_table.add_row(
                    str(directory.status_code),
                    directory.path,
                    f"{directory.size} B",
                    redirect_info
                )
            
            console.print(dir_table)
            
            # Summary by status code
            console.print("\n[bold]Directory Summary by Status Code:[/bold]")
            for status in sorted(dir_by_status.keys()):
                count = len(dir_by_status[status])
                console.print(f"  [{status}]: {count} directories")
                
                # Show examples for each status
                examples = dir_by_status[status][:3]
                for ex in examples:
                    console.print(f"    • {ex.path}")
                if count > 3:
                    console.print(f"    ... and {count - 3} more")
            
            # Interesting directories (based on name patterns)
            interesting_patterns = [
                'admin', 'backup', 'config', 'database', 'db', 'private',
                'api', 'upload', 'download', '.git', '.svn', 'wp-', 'phpmyadmin'
            ]
            
            interesting_dirs = []
            for d in directories:
                for pattern in interesting_patterns:
                    if pattern in d.path.lower():
                        interesting_dirs.append(d)
                        break
            
            if interesting_dirs:
                console.print("\n[bold red]Potentially Interesting Directories:[/bold red]")
                for d in interesting_dirs:
                    console.print(f"  [{d.status_code}] {d.path}")
            
            # Export results
            console.print("\n[bold]Export Directory List:[/bold]")
            console.print("[dim]All directories found:[/dim]")
            for d in all_dirs:
                console.print(f"{target_url}{d.path}")
                
        else:
            console.print("[yellow]No directories found[/yellow]")
        
        # Also show files that might be interesting
        if files:
            console.print(f"\n[bold]Also found {len(files)} files[/bold]")
            console.print("[dim]Showing first 10:[/dim]")
            for f in files[:10]:
                console.print(f"  [{f.status_code}] {f.path}")
        
        # Show crawled directories
        if engine._crawled_paths:
            crawled_dirs = [p for p in engine._crawled_paths if p.endswith('/')]
            if crawled_dirs:
                console.print(f"\n[bold]Directories found via crawling:[/bold]")
                for path in crawled_dirs[:10]:
                    console.print(f"  • {path}")
        
    except Exception as e:
        console.print(f"\n[red]❌ Error: {e}[/red]")
        import traceback
        traceback.print_exc()
    finally:
        await engine.close()


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        console.print("[bold]Directory Scanner for Dirsearch[/bold]")
        console.print("\nUsage: python test_show_directories.py <target_url>")
        console.print("Example: python test_show_directories.py http://127.0.0.1:8080/")
        console.print("\nThis will scan for directories and show ALL results in detail.")
        sys.exit(1)
    
    target_url = sys.argv[1]
    if not target_url.startswith(('http://', 'https://')):
        target_url = 'http://' + target_url
    
    if not target_url.endswith('/'):
        target_url += '/'
    
    asyncio.run(scan_and_show_directories(target_url))


if __name__ == "__main__":
    main()