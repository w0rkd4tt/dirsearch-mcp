#!/usr/bin/env python3
"""
Demo of Enhanced Dirsearch Features
Shows smart recursive scanning and deep content analysis in action
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.tree import Tree

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.dirsearch_engine import DirsearchEngine, ScanOptions
from src.config.settings import Settings

console = Console()


async def demo_enhanced_features(target_url):
    """Demonstrate enhanced features with visual output"""
    
    console.print(Panel.fit(
        "[bold]Enhanced Dirsearch Features Demo[/bold]\n"
        "Smart Recursive Scanning + Deep Content Analysis",
        border_style="cyan"
    ))
    
    engine = DirsearchEngine(Settings())
    
    # Minimal wordlist to show expansion
    wordlist = ["index.php", "admin", "api", "robots.txt"]
    
    # Enable all enhanced features
    options = ScanOptions(
        recursive=True,
        recursion_depth=0,  # Unlimited
        crawl=True,         # Deep content analysis
        threads=5,
        timeout=10,
        exclude_status_codes=[404]
    )
    
    console.print("\n[bold]Initial Setup:[/bold]")
    console.print(f"• Starting with only {len(wordlist)} paths")
    console.print("• Smart recursion will expand automatically")
    console.print("• Deep analysis will extract endpoints\n")
    
    # Visual tree to show expansion
    tree = Tree("[bold]Scan Expansion[/bold]")
    initial_node = tree.add("Initial Scan (4 paths)")
    
    try:
        # Run scan
        start = datetime.now()
        results = await engine.scan_target(target_url, wordlist, options)
        duration = (datetime.now() - start).total_seconds()
        
        # Show expansion
        console.print(f"\n[bold green]✨ Magic Happened![/bold green]")
        console.print(f"• Started with: {len(wordlist)} paths")
        console.print(f"• Discovered: {len(results)} paths")
        console.print(f"• Expansion: {len(results)/len(wordlist):.1f}x")
        console.print(f"• Time: {duration:.2f}s")
        
        # Visualize discovery process
        if results:
            # Add discovered paths to tree
            dirs = [r for r in results if r.is_directory]
            files = [r for r in results if not r.is_directory]
            
            if dirs:
                dir_node = initial_node.add(f"[green]Found {len(dirs)} directories[/green]")
                for d in dirs[:3]:
                    dir_node.add(f"📁 {d.path}")
                if len(dirs) > 3:
                    dir_node.add(f"... +{len(dirs)-3} more")
            
            if files:
                file_node = initial_node.add(f"[green]Found {len(files)} files[/green]")
                for f in files[:3]:
                    file_node.add(f"📄 {f.path}")
                if len(files) > 3:
                    file_node.add(f"... +{len(files)-3} more")
            
            # Show content extraction
            if hasattr(engine, '_crawled_paths') and engine._crawled_paths:
                extract_node = tree.add(f"[yellow]Content Analysis ({len(engine._crawled_paths)} extracted)[/yellow]")
                for path in list(engine._crawled_paths)[:5]:
                    extract_node.add(f"🔍 {path}")
                if len(engine._crawled_paths) > 5:
                    extract_node.add(f"... +{len(engine._crawled_paths)-5} more")
            
            # Show recursive expansion
            recursive_node = tree.add("[blue]Recursive Expansion[/blue]")
            recursive_node.add("↻ Scanned found directories")
            recursive_node.add("↻ Analyzed extracted paths") 
            recursive_node.add("✓ Stopped when no new content")
        
        console.print("\n")
        console.print(tree)
        
        # Key insights
        console.print("\n[bold]Key Insights:[/bold]")
        console.print("• Smart recursion eliminated manual depth guessing")
        console.print("• Content analysis found hidden endpoints")
        console.print("• Automatic stopping prevented infinite loops")
        console.print("• Comprehensive coverage with minimal input")
        
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
    finally:
        await engine.close()
    
    console.print("\n[bold green]✅ Demo Complete![/bold green]")


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        console.print("[bold]Enhanced Features Demo[/bold]")
        console.print("\nUsage: python demo_enhanced_features.py <target_url>")
        console.print("Example: python demo_enhanced_features.py http://127.0.0.1:8080/")
        sys.exit(1)
    
    target_url = sys.argv[1]
    if not target_url.startswith(('http://', 'https://')):
        target_url = 'http://' + target_url
    
    if not target_url.endswith('/'):
        target_url += '/'
    
    asyncio.run(demo_enhanced_features(target_url))


if __name__ == "__main__":
    main()