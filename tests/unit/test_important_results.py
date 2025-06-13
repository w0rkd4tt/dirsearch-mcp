#!/usr/bin/env python3
"""
Test dirsearch and show only important results (non-404)
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


async def scan_important_only(target_url):
    """Scan and show only important results"""
    
    console.print(Panel.fit(
        f"[bold]Dirsearch - Important Results Only[/bold]\n"
        f"Target: {target_url}",
        border_style="cyan"
    ))
    
    engine = DirsearchEngine(Settings())
    
    # Focused wordlist
    wordlist = [
        # Common directories
        "admin", "api", "app", "assets", "backup", "bin", "cgi-bin",
        "config", "console", "css", "data", "database", "db", "debug",
        "demo", "dev", "dist", "doc", "docs", "download", "downloads",
        "files", "fonts", "home", "images", "img", "include", "includes",
        "js", "lib", "library", "log", "logs", "media", "old", "panel",
        "phpMyAdmin", "phpmyadmin", "private", "public", "scripts",
        "secure", "server", "src", "static", "storage", "system",
        "temp", "test", "tmp", "upload", "uploads", "user", "users",
        "vendor", "wp-admin", "wp-content", "wp-includes",
        
        # Common files
        "index.php", "login.php", "admin.php", "config.php", "info.php",
        "phpinfo.php", "test.php", "robots.txt", ".htaccess", ".htpasswd",
        ".env", "web.config", "sitemap.xml", "composer.json", "package.json",
        
        # Backup files
        "backup.sql", "backup.zip", "backup.tar.gz", "database.sql",
        "db_backup.sql", "dump.sql", "mysql.sql", "site_backup.zip",
        
        # Config files
        "config.inc.php", "configuration.php", "wp-config.php",
        "settings.php", "database.php", "db.php", "connect.php",
        
        # Hidden files/dirs
        ".git/config", ".git/HEAD", ".svn/entries", ".DS_Store",
        
        # API endpoints
        "api/v1", "api/v2", "api/users", "api/login", "api/admin"
    ]
    
    # Options - exclude 404 to reduce noise
    options = ScanOptions(
        detect_wildcards=True,
        crawl=True,
        random_user_agents=True,
        exclude_status_codes=[404],  # Exclude 404s
        threads=10,
        timeout=10,
        follow_redirects=True
    )
    
    try:
        # Test connectivity
        console.print("\n[bold]Testing connectivity...[/bold]")
        test_response = await engine._make_request(target_url, options)
        if test_response:
            console.print(f"✅ Target accessible: Status {test_response.get('status_code')}")
        else:
            console.print("❌ Cannot connect to target")
            return
        
        # Run scan
        console.print(f"\n[bold]Scanning for important paths...[/bold]")
        console.print(f"[dim]Wordlist: {len(wordlist)} entries[/dim]")
        
        start_time = datetime.now()
        results = await engine.scan_target(target_url, wordlist, options)
        duration = (datetime.now() - start_time).total_seconds()
        
        console.print(f"\n✅ Scan completed in {duration:.2f} seconds")
        console.print(f"Important findings: {len(results)} (excluding 404s)")
        
        if results:
            # Group by status code
            by_status = {}
            for r in results:
                if r.status_code not in by_status:
                    by_status[r.status_code] = []
                by_status[r.status_code].append(r)
            
            # Show results by importance
            console.print("\n[bold green]🎯 SUCCESSFUL PATHS (2xx):[/bold green]")
            successful = [r for r in results if 200 <= r.status_code < 300]
            if successful:
                success_table = Table(show_header=True, box=None)
                success_table.add_column("Path", style="green")
                success_table.add_column("Status", style="cyan", width=8)
                success_table.add_column("Size", style="dim")
                success_table.add_column("Type", style="yellow")
                
                for r in sorted(successful, key=lambda x: x.path):
                    success_table.add_row(
                        r.path,
                        str(r.status_code),
                        f"{r.size} B",
                        "DIR" if r.is_directory else "FILE"
                    )
                console.print(success_table)
            else:
                console.print("[dim]None found[/dim]")
            
            # Show redirects
            console.print("\n[bold yellow]↗️  REDIRECTS (3xx):[/bold yellow]")
            redirects = [r for r in results if 300 <= r.status_code < 400]
            if redirects:
                for r in redirects:
                    console.print(f"  {r.path} → {r.redirect_url}")
            else:
                console.print("[dim]None found[/dim]")
            
            # Show forbidden
            console.print("\n[bold red]🚫 FORBIDDEN (403):[/bold red]")
            forbidden = [r for r in results if r.status_code == 403]
            if forbidden:
                for r in forbidden:
                    console.print(f"  {r.path}")
            else:
                console.print("[dim]None found[/dim]")
            
            # Show server errors
            console.print("\n[bold red]❌ SERVER ERRORS (5xx):[/bold red]")
            errors = [r for r in results if r.status_code >= 500]
            if errors:
                for r in errors:
                    console.print(f"  [{r.status_code}] {r.path}")
            else:
                console.print("[dim]None found[/dim]")
            
            # Summary
            console.print("\n[bold]📊 SUMMARY:[/bold]")
            summary_table = Table(show_header=False, box=None)
            summary_table.add_column("Status", style="cyan")
            summary_table.add_column("Count", style="yellow")
            summary_table.add_column("Description")
            
            if 200 <= min(by_status.keys()) < 300:
                summary_table.add_row("2xx", str(len(successful)), "Accessible paths")
            if any(300 <= s < 400 for s in by_status.keys()):
                summary_table.add_row("3xx", str(len(redirects)), "Redirects")
            if 403 in by_status:
                summary_table.add_row("403", str(len(forbidden)), "Forbidden (may exist)")
            if any(s >= 500 for s in by_status.keys()):
                summary_table.add_row("5xx", str(len(errors)), "Server errors")
            
            console.print(summary_table)
            
            # Interesting findings
            console.print("\n[bold]🔍 INTERESTING FINDINGS:[/bold]")
            interesting = []
            
            # Check for specific patterns
            for r in results:
                path_lower = r.path.lower()
                if any(pattern in path_lower for pattern in [
                    'admin', 'config', 'backup', '.git', '.env', 'api',
                    'phpmyadmin', 'database', 'sql', 'dump'
                ]):
                    interesting.append(r)
            
            if interesting:
                for r in interesting[:10]:
                    console.print(f"  [{r.status_code}] {r.path}")
                if len(interesting) > 10:
                    console.print(f"  ... and {len(interesting) - 10} more")
            else:
                console.print("[dim]No particularly interesting paths found[/dim]")
            
            # Crawled paths
            if engine._crawled_paths:
                console.print(f"\n[bold]🕷️  PATHS FROM CRAWLING:[/bold]")
                for path in list(engine._crawled_paths)[:5]:
                    console.print(f"  • {path}")
                if len(engine._crawled_paths) > 5:
                    console.print(f"  ... and {len(engine._crawled_paths) - 5} more")
            
        else:
            console.print("\n[yellow]No important results found (all paths returned 404)[/yellow]")
        
        console.print("\n" + "="*60)
        console.print("[bold]✅ Scan Complete![/bold]")
        
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
    finally:
        await engine.close()


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        console.print("[bold]Dirsearch - Important Results Scanner[/bold]")
        console.print("\nUsage: python test_important_results.py <target_url>")
        console.print("Example: python test_important_results.py http://127.0.0.1:8080/")
        console.print("\nThis will show only important results (non-404 responses)")
        sys.exit(1)
    
    target_url = sys.argv[1]
    if not target_url.startswith(('http://', 'https://')):
        target_url = 'http://' + target_url
    
    if not target_url.endswith('/'):
        target_url += '/'
    
    asyncio.run(scan_important_only(target_url))


if __name__ == "__main__":
    main()