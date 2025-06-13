#!/usr/bin/env python3
"""
Full Demo: Complete Directory Tree with All Features
Shows the complete flow with better wordlist
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.tree import Tree as RichTree
from rich.live import Live
from rich.text import Text

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.dirsearch_engine import DirsearchEngine, ScanOptions
from src.config.settings import Settings

console = Console()


def build_tree_with_stats(tree_dict, parent_node=None, stats=None):
    """Build tree with statistics"""
    if stats is None:
        stats = {'dirs': 0, 'files': 0, 'total_size': 0}
    
    root_tree = None
    if parent_node is None:
        root_tree = RichTree("🌐 [bold]Complete Directory Structure[/bold]")
        parent_node = root_tree
    
    # Process directories
    for name, child in sorted(tree_dict.get('children', {}).items()):
        stats['dirs'] += 1
        status = child.get('status', '')
        status_icon = "🟢" if status == 200 else "🟡" if status in [301, 302] else "🔴" if status == 403 else "⚫"
        
        node = parent_node.add(f"📁 [cyan]{name}/[/cyan] {status_icon}")
        build_tree_with_stats(child, node, stats)
    
    # Process files
    for file in sorted(tree_dict.get('files', []), key=lambda x: x['name']):
        stats['files'] += 1
        stats['total_size'] += file.get('size', 0)
        
        status = file.get('status', '')
        status_icon = "🟢" if status == 200 else "🟡" if status in [301, 302] else "🔴" if status == 403 else "⚫"
        
        size = file.get('size', 0)
        if size > 1024:
            size_text = f"[dim]{size/1024:.1f}KB[/dim]"
        else:
            size_text = f"[dim]{size}B[/dim]"
        
        parent_node.add(f"📄 {file['name']} {status_icon} {size_text}")
    
    return root_tree if root_tree else parent_node, stats


async def demo_full_tree(target_url):
    """Full demo with all features"""
    
    console.print(Panel.fit(
        f"[bold]Full Directory Tree Demo[/bold]\n"
        f"Target: {target_url}\n"
        f"Demonstrating: Recursive + Depth + Tree Visualization",
        border_style="cyan"
    ))
    
    engine = DirsearchEngine(Settings())
    
    # Comprehensive wordlist
    wordlist = [
        # Common directories
        "admin", "api", "app", "assets", "backup", "bin", "cache", "cgi-bin",
        "config", "console", "css", "data", "database", "db", "debug", "demo",
        "dev", "dist", "doc", "docs", "download", "downloads", "error", "errors",
        "files", "fonts", "home", "images", "img", "include", "includes", "js",
        "lib", "library", "log", "logs", "mail", "media", "old", "private",
        "public", "scripts", "secure", "server", "src", "static", "storage",
        "system", "temp", "test", "tests", "tmp", "tools", "upload", "uploads",
        "user", "users", "vendor", "webmail", "wp-admin", "wp-content",
        
        # Common files
        "index.php", "index.html", "login.php", "admin.php", "config.php",
        "setup.php", "install.php", "test.php", "info.php", "phpinfo.php",
        "robots.txt", "sitemap.xml", ".htaccess", ".htpasswd", ".env",
        "web.config", "composer.json", "package.json", "README.md",
        
        # API paths
        "api/v1", "api/v2", "api/docs", "api/swagger", "api/users", "api/auth",
        
        # Admin paths
        "admin/login", "admin/dashboard", "admin/users", "admin/config",
        
        # Hidden/Sensitive
        ".git/config", ".git/HEAD", ".svn/entries", "backup.sql", "dump.sql",
        
        # Technology specific
        "phpmyadmin", "phpMyAdmin", "pma", "mysql", "cpanel", "plesk"
    ]
    
    options = ScanOptions(
        recursive=True,
        recursion_depth=0,  # Unlimited
        crawl=True,         # Deep analysis
        threads=20,         # More threads for speed
        timeout=10,
        exclude_status_codes=[404],
        follow_redirects=True
    )
    
    try:
        # Live display
        with Live(console=console, refresh_per_second=2) as live:
            # Phase 1: Scanning
            status_text = Text()
            status_text.append("🔍 Phase 1: Scanning in progress...\n", style="bold yellow")
            status_text.append(f"Wordlist: {len(wordlist)} entries\n")
            status_text.append("Features: Recursive ✓ Depth Analysis ✓")
            
            panel = Panel(status_text, title="Scanning", border_style="cyan")
            live.update(panel)
            
            start_time = datetime.now()
            results = await engine.scan_target(target_url, wordlist, options)
            scan_duration = (datetime.now() - start_time).total_seconds()
            
            # Update with results
            status_text.append(f"\n\n✅ Scan completed in {scan_duration:.2f} seconds")
            status_text.append(f"\nPaths found: {len(results)}")
            live.update(Panel(status_text, title="Scanning Complete", border_style="green"))
            
            await asyncio.sleep(2)
        
        # Phase 2: Analysis
        console.print("\n[bold]📊 Phase 2: Scan Analysis[/bold]")
        
        dirs = [r for r in results if r.is_directory]
        files = [r for r in results if not r.is_directory]
        
        # Show breakdown
        breakdown = f"""
Discovered Paths: {len(results)}
├── 📁 Directories: {len(dirs)}
└── 📄 Files: {len(files)}

Expansion: {len(wordlist)} → {len(results)} ({len(results)/len(wordlist):.1f}x)
        """
        console.print(Panel(breakdown, title="Results Breakdown", border_style="yellow"))
        
        # Deep analysis results
        if hasattr(engine, '_endpoint_analysis_results') and engine._endpoint_analysis_results:
            total_extracted = sum(r['extracted_count'] for r in engine._endpoint_analysis_results)
            console.print(f"\n[green]Deep Analysis: Extracted {total_extracted} hidden paths from {len(engine._endpoint_analysis_results)} endpoints[/green]")
        
        # Phase 3: Directory Tree
        console.print("\n[bold]🌳 Phase 3: Directory Tree Visualization[/bold]")
        
        # Build tree
        tree_dict = engine.build_directory_tree()
        tree, tree_stats = build_tree_with_stats(tree_dict)
        
        # Display tree
        console.print("\n")
        console.print(tree)
        
        # Tree statistics
        console.print(f"\n[bold]Tree Statistics:[/bold]")
        console.print(f"📁 Total Directories: {tree_stats['dirs']}")
        console.print(f"📄 Total Files: {tree_stats['files']}")
        console.print(f"💾 Total Size: {tree_stats['total_size'] / 1024:.2f} KB")
        
        # Get depth statistics
        stats = engine.get_directory_statistics()
        
        # Show depth visualization
        if stats['by_depth']:
            console.print(f"\n[bold]Depth Levels:[/bold]")
            max_depth = max(stats['by_depth'].keys())
            
            for depth in range(max_depth + 1):
                count = stats['by_depth'].get(depth, 0)
                if count > 0:
                    indent = "  " * depth
                    bar = "█" * min(count, 50)
                    console.print(f"{indent}Level {depth}: {bar} ({count})")
        
        # Status legend
        console.print("\n[bold]Status Legend:[/bold]")
        console.print("🟢 = 200 OK")
        console.print("🟡 = 301/302 Redirect") 
        console.print("🔴 = 403 Forbidden")
        
        # Phase 4: Key Findings
        console.print("\n[bold]🔑 Phase 4: Key Findings[/bold]")
        
        # Find interesting paths
        interesting = {
            'admin': [],
            'api': [],
            'config': [],
            'backup': [],
            'hidden': []
        }
        
        for result in results:
            path = result.path.lower()
            if 'admin' in path:
                interesting['admin'].append(result)
            elif 'api' in path:
                interesting['api'].append(result)
            elif 'config' in path or '.env' in path:
                interesting['config'].append(result)
            elif 'backup' in path or 'dump' in path or '.sql' in path:
                interesting['backup'].append(result)
            elif path.startswith('.'):
                interesting['hidden'].append(result)
        
        # Display interesting findings
        for category, items in interesting.items():
            if items:
                console.print(f"\n[yellow]{category.upper()} ({len(items)} items):[/yellow]")
                for item in items[:3]:
                    status_icon = "🟢" if item.status_code == 200 else "🔴" if item.status_code == 403 else "🟡"
                    console.print(f"  {status_icon} {item.path}")
                if len(items) > 3:
                    console.print(f"  ... and {len(items) - 3} more")
        
        # Final summary
        console.print("\n[bold]✨ Summary[/bold]")
        summary = f"""
Scan Duration: {scan_duration:.2f} seconds
Initial Wordlist: {len(wordlist)} entries
Total Discovered: {len(results)} paths
Recursive Depth: {stats['max_depth']} levels
Features Used: Recursive ✓ Deep Analysis ✓ Tree Visualization ✓
        """
        console.print(Panel(summary, title="Final Summary", border_style="green"))
        
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
    finally:
        await engine.close()
    
    console.print("\n[bold green]✅ Full Demo Complete![/bold green]")


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        console.print("[bold]Full Directory Tree Demo[/bold]")
        console.print("\nUsage: python demo_full_tree.py <target_url>")
        console.print("Example: python demo_full_tree.py http://127.0.0.1:8080/")
        sys.exit(1)
    
    target_url = sys.argv[1]
    if not target_url.startswith(('http://', 'https://')):
        target_url = 'http://' + target_url
    
    if not target_url.endswith('/'):
        target_url += '/'
    
    asyncio.run(demo_full_tree(target_url))


if __name__ == "__main__":
    main()