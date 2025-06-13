#!/usr/bin/env python3
"""
Simple Directory Tree Demo
Shows directory tree after scanning
"""

import asyncio
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.dirsearch_engine import DirsearchEngine, ScanOptions
from src.config.settings import Settings

console = Console()


async def demo_tree(target_url):
    """Simple demo of directory tree visualization"""
    
    console.print(Panel.fit(
        f"[bold]Directory Tree Demo[/bold]\n"
        f"Target: {target_url}",
        border_style="cyan"
    ))
    
    engine = DirsearchEngine(Settings())
    
    # Basic wordlist
    wordlist = [
        # Directories
        "admin", "api", "config", "css", "docs", "images", "js", "test", "uploads",
        # Subdirectories
        "admin/users", "admin/config", "api/v1", "api/v2",
        # Files
        "index.php", "login.php", "robots.txt", ".htaccess",
        "admin/index.php", "api/index.php", "css/style.css", "js/app.js"
    ]
    
    options = ScanOptions(
        recursive=True,
        recursion_depth=2,
        threads=10,
        timeout=10,
        exclude_status_codes=[404]
    )
    
    try:
        # Run scan
        console.print("\n[yellow]Scanning...[/yellow]")
        results = await engine.scan_target(target_url, wordlist, options)
        console.print(f"[green]✅ Found {len(results)} paths[/green]\n")
        
        # Show directory tree
        console.print("[bold]Directory Tree:[/bold]\n")
        
        tree_string = engine.print_directory_tree()
        if tree_string:
            console.print(tree_string)
        else:
            console.print("[dim]No paths found[/dim]")
        
        # Show summary
        stats = engine.get_directory_statistics()
        console.print(f"\n[bold]Summary:[/bold]")
        console.print(f"📁 Directories: {stats['directories']}")
        console.print(f"📄 Files: {stats['files']}")
        console.print(f"📊 Total: {stats['total_paths']}")
        console.print(f"🔽 Max depth: {stats['max_depth']} levels")
        
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
    finally:
        await engine.close()


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        console.print("[bold]Directory Tree Demo[/bold]")
        console.print("\nUsage: python demo_tree.py <target_url>")
        console.print("Example: python demo_tree.py http://127.0.0.1:8080/")
        sys.exit(1)
    
    target_url = sys.argv[1]
    if not target_url.startswith(('http://', 'https://')):
        target_url = 'http://' + target_url
    
    if not target_url.endswith('/'):
        target_url += '/'
    
    asyncio.run(demo_tree(target_url))


if __name__ == "__main__":
    main()