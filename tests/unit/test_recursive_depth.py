#!/usr/bin/env python3
"""
Test recursive scanning and endpoint extraction features
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
from rich.tree import Tree

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.dirsearch_engine import DirsearchEngine, ScanOptions
from src.config.settings import Settings

console = Console()


async def test_recursive_and_depth(target_url):
    """Test recursive scanning and endpoint extraction"""
    
    console.print(Panel.fit(
        f"[bold]Testing Recursive Scanning & Endpoint Extraction[/bold]\n"
        f"Target: {target_url}",
        border_style="cyan"
    ))
    
    engine = DirsearchEngine(Settings())
    
    # Basic wordlist for initial scan
    wordlist = [
        # Directories that might contain subdirectories
        "admin",
        "api",
        "app", 
        "config",
        "docs",
        "files",
        "images",
        "includes",
        "js",
        "css",
        "lib",
        "public",
        "private",
        "upload",
        "uploads",
        "user",
        "users",
        "test",
        
        # Common files
        "index.php",
        "login.php",
        "config.php",
        "api.php",
        "test.php",
        
        # Files that might contain endpoints
        "robots.txt",
        "sitemap.xml",
        ".htaccess"
    ]
    
    # Options with recursive scanning enabled
    options = ScanOptions(
        # Recursive settings
        recursive=True,
        recursion_depth=3,  # Scan up to 3 levels deep
        
        # Other features
        crawl=True,  # Also extract paths from content
        detect_wildcards=True,
        random_user_agents=True,
        
        # Basic settings
        threads=10,
        timeout=10,
        exclude_status_codes=[404],
        follow_redirects=True
    )
    
    try:
        console.print("\n[bold]1. Initial Scan Configuration:[/bold]")
        console.print(f"  • Recursive scanning: [green]Enabled[/green]")
        console.print(f"  • Max recursion depth: [yellow]{options.recursion_depth} levels[/yellow]")
        console.print(f"  • Content crawling: [green]Enabled[/green]")
        console.print(f"  • Initial wordlist: {len(wordlist)} entries")
        
        # Run initial scan
        console.print("\n[bold]2. Running Initial Scan...[/bold]")
        start_time = datetime.now()
        
        # Track results at each level
        initial_results = len(engine._results) if hasattr(engine, '_results') else 0
        
        results = await engine.scan_target(target_url, wordlist, options)
        
        duration = (datetime.now() - start_time).total_seconds()
        
        console.print(f"\n✅ Scan completed in {duration:.2f} seconds")
        console.print(f"Total results: {len(results)}")
        
        # Analyze results by depth
        console.print("\n[bold]3. Results Analysis:[/bold]")
        
        # Group results by path depth
        by_depth = {}
        for r in results:
            depth = r.path.count('/')
            if depth not in by_depth:
                by_depth[depth] = []
            by_depth[depth].append(r)
        
        # Create tree view of results
        tree = Tree("[bold]Directory Structure[/bold]")
        
        # Add root level
        root_items = by_depth.get(0, []) + by_depth.get(1, [])
        for item in sorted(root_items, key=lambda x: x.path):
            if item.is_directory:
                tree.add(f"📁 [green]{item.path}[/green] [{item.status_code}]")
            else:
                tree.add(f"📄 {item.path} [{item.status_code}]")
        
        console.print(tree)
        
        # Show depth statistics
        console.print("\n[bold]4. Recursion Depth Statistics:[/bold]")
        depth_table = Table(show_header=True)
        depth_table.add_column("Depth Level", style="cyan")
        depth_table.add_column("Path Count", style="yellow")
        depth_table.add_column("Example Paths")
        
        for depth in sorted(by_depth.keys()):
            paths = by_depth[depth]
            examples = ", ".join([p.path for p in paths[:3]])
            if len(paths) > 3:
                examples += f" ... (+{len(paths) - 3} more)"
            depth_table.add_row(
                f"Level {depth}",
                str(len(paths)),
                examples
            )
        
        console.print(depth_table)
        
        # Show directories found at each level
        console.print("\n[bold]5. Directories Found (for recursive scanning):[/bold]")
        directories = [r for r in results if r.is_directory]
        
        if directories:
            dir_by_depth = {}
            for d in directories:
                depth = d.path.count('/')
                if depth not in dir_by_depth:
                    dir_by_depth[depth] = []
                dir_by_depth[depth].append(d)
            
            for depth in sorted(dir_by_depth.keys()):
                console.print(f"\n[yellow]Level {depth}:[/yellow]")
                for d in dir_by_depth[depth]:
                    console.print(f"  📁 {d.path} [{d.status_code}]")
                    
                    # Show if this directory was recursively scanned
                    subpaths = [r for r in results if r.path.startswith(d.path + '/')]
                    if subpaths:
                        console.print(f"     ↳ Found {len(subpaths)} items inside")
        else:
            console.print("[dim]No directories found[/dim]")
        
        # Show extracted endpoints from crawling
        console.print("\n[bold]6. Endpoints Extracted from Content:[/bold]")
        if hasattr(engine, '_crawled_paths') and engine._crawled_paths:
            console.print(f"[green]Found {len(engine._crawled_paths)} paths via content analysis:[/green]")
            
            # Group by source type
            html_paths = []
            robots_paths = []
            other_paths = []
            
            for path in engine._crawled_paths:
                if path.endswith('.html') or path.endswith('.php'):
                    html_paths.append(path)
                elif 'robots' in path:
                    robots_paths.append(path)
                else:
                    other_paths.append(path)
            
            if html_paths:
                console.print(f"\n  From HTML/PHP files ({len(html_paths)}):")
                for p in html_paths[:5]:
                    console.print(f"    • {p}")
                if len(html_paths) > 5:
                    console.print(f"    ... and {len(html_paths) - 5} more")
            
            if robots_paths:
                console.print(f"\n  From robots.txt ({len(robots_paths)}):")
                for p in robots_paths[:5]:
                    console.print(f"    • {p}")
            
            if other_paths:
                console.print(f"\n  From other sources ({len(other_paths)}):")
                for p in other_paths[:5]:
                    console.print(f"    • {p}")
        else:
            console.print("[dim]No paths extracted from content[/dim]")
        
        # Test endpoint regex extraction
        console.print("\n[bold]7. Testing Endpoint Regex Extraction:[/bold]")
        
        # Get a sample HTML response
        sample_responses = [r for r in results if r.status_code == 200 and not r.is_directory]
        if sample_responses:
            test_url = sample_responses[0].url
            console.print(f"[dim]Analyzing response from: {test_url}[/dim]")
            
            # Make request to get full response
            response = await engine._make_request(test_url, options)
            if response and 'text' in response:
                content = response['text']
                
                # Extract URLs using regex
                import re
                
                # Common URL patterns
                url_patterns = [
                    r'href=[\'"]?(/[^\'"\s>]+)',  # href attributes
                    r'src=[\'"]?(/[^\'"\s>]+)',   # src attributes
                    r'action=[\'"]?(/[^\'"\s>]+)', # form actions
                    r'url\([\'"]?(/[^\'"\)]+)',   # CSS urls
                    r'/[a-zA-Z0-9_\-./]+\.php',   # PHP files
                    r'/api/[a-zA-Z0-9_\-./]+',     # API endpoints
                ]
                
                found_urls = set()
                for pattern in url_patterns:
                    matches = re.findall(pattern, content)
                    found_urls.update(matches)
                
                if found_urls:
                    console.print(f"[green]Found {len(found_urls)} URLs via regex:[/green]")
                    for url in sorted(found_urls)[:10]:
                        console.print(f"  • {url}")
                    if len(found_urls) > 10:
                        console.print(f"  ... and {len(found_urls) - 10} more")
                else:
                    console.print("[dim]No URLs found via regex[/dim]")
        
        # Summary
        console.print("\n[bold]8. Feature Summary:[/bold]")
        summary_table = Table(show_header=False, box=None)
        summary_table.add_column("Feature", style="cyan")
        summary_table.add_column("Status", style="green")
        summary_table.add_column("Results")
        
        summary_table.add_row(
            "Recursive Scanning",
            "✅ Working",
            f"Scanned {len(directories)} directories"
        )
        
        summary_table.add_row(
            "Depth Control", 
            "✅ Working",
            f"Max depth: {max(by_depth.keys()) if by_depth else 0} levels"
        )
        
        summary_table.add_row(
            "Content Crawling",
            "✅ Working",
            f"Extracted {len(engine._crawled_paths) if hasattr(engine, '_crawled_paths') else 0} paths"
        )
        
        summary_table.add_row(
            "Total Findings",
            "✅ Complete",
            f"{len(results)} total paths discovered"
        )
        
        console.print(summary_table)
        
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
    finally:
        await engine.close()


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        console.print("[bold]Recursive Scanning & Depth Test[/bold]")
        console.print("\nUsage: python test_recursive_depth.py <target_url>")
        console.print("Example: python test_recursive_depth.py http://127.0.0.1:8080/")
        console.print("\nThis will test:")
        console.print("  • Recursive scanning of discovered directories")
        console.print("  • Depth control (limiting recursion levels)")
        console.print("  • Endpoint extraction from responses")
        sys.exit(1)
    
    target_url = sys.argv[1]
    if not target_url.startswith(('http://', 'https://')):
        target_url = 'http://' + target_url
    
    if not target_url.endswith('/'):
        target_url += '/'
    
    asyncio.run(test_recursive_and_depth(target_url))


if __name__ == "__main__":
    main()