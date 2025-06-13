#!/usr/bin/env python3
"""
Demo: Recursive Scanning Flow
Shows how recursive scanning works step by step
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.tree import Tree as RichTree

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.dirsearch_engine import DirsearchEngine, ScanOptions
from src.config.settings import Settings

console = Console()


async def demo_recursive_flow(target_url):
    """Demonstrate recursive scanning flow"""
    
    console.print(Panel.fit(
        f"[bold]Recursive Scanning Flow Demo[/bold]\n"
        f"Target: {target_url}\n"
        f"Showing how recursive scanning explores directories",
        border_style="cyan"
    ))
    
    engine = DirsearchEngine(Settings())
    
    # Minimal wordlist
    wordlist = ["admin", "api", "config", "docs", "test", "index.php"]
    
    # Test without and with recursive
    tests = [
        {
            "name": "Without Recursive",
            "options": ScanOptions(
                recursive=False,
                threads=5,
                timeout=10,
                exclude_status_codes=[404]
            )
        },
        {
            "name": "With Recursive (Unlimited)",
            "options": ScanOptions(
                recursive=True,
                recursion_depth=0,  # Unlimited
                threads=5,
                timeout=10,
                exclude_status_codes=[404]
            )
        }
    ]
    
    try:
        for test in tests:
            console.print(f"\n[bold]Test: {test['name']}[/bold]")
            console.print("="*50)
            
            # Clear previous results
            engine._results.clear()
            engine._scanned_paths.clear()
            if hasattr(engine, '_deep_scanned_dirs'):
                engine._deep_scanned_dirs.clear()
            
            # Run scan
            start_time = datetime.now()
            results = await engine.scan_target(target_url, wordlist, test['options'])
            duration = (datetime.now() - start_time).total_seconds()
            
            console.print(f"\n✅ Scan completed in {duration:.2f} seconds")
            console.print(f"Total paths found: {len(results)}")
            
            # Show what was found
            dirs = [r for r in results if r.is_directory]
            files = [r for r in results if not r.is_directory]
            
            console.print(f"  • Directories: {len(dirs)}")
            console.print(f"  • Files: {len(files)}")
            
            # Show directory tree
            if results:
                tree = RichTree(f"[bold]{test['name']} Results[/bold]")
                
                # Add root level items
                root_items = [r for r in results if r.path.count('/') <= 1]
                for item in sorted(root_items, key=lambda x: (not x.is_directory, x.path)):
                    if item.is_directory:
                        status_icon = "🟢" if item.status_code == 200 else "🟡" if item.status_code in [301, 302] else "🔴"
                        node = tree.add(f"📁 {item.path} {status_icon}")
                        
                        # Add sub-items if recursive
                        if test['options'].recursive:
                            sub_items = [r for r in results if r.path.startswith(item.path) and r.path != item.path]
                            for sub in sorted(sub_items, key=lambda x: x.path):
                                sub_icon = "🟢" if sub.status_code == 200 else "🟡" if sub.status_code in [301, 302] else "🔴"
                                if sub.is_directory:
                                    node.add(f"📁 {sub.path.replace(item.path, '')} {sub_icon}")
                                else:
                                    node.add(f"📄 {sub.path.replace(item.path, '')} {sub_icon}")
                    else:
                        status_icon = "🟢" if item.status_code == 200 else "🟡" if item.status_code in [301, 302] else "🔴"
                        tree.add(f"📄 {item.path} {status_icon}")
                
                console.print(tree)
            
            # Show scanning activity for recursive
            if test['options'].recursive and hasattr(engine, '_deep_scanned_dirs'):
                console.print(f"\n[yellow]Recursive Scanning Activity:[/yellow]")
                console.print(f"Directories scanned: {len(engine._deep_scanned_dirs)}")
                for dir_url in sorted(engine._deep_scanned_dirs)[:10]:
                    console.print(f"  → Scanned: {dir_url}")
                if len(engine._deep_scanned_dirs) > 10:
                    console.print(f"  ... and {len(engine._deep_scanned_dirs) - 10} more")
        
        # Show the difference
        console.print("\n[bold]Recursive Scanning Explanation:[/bold]")
        console.print("1. Initial scan finds directories (e.g., /admin, /api)")
        console.print("2. For each directory found, scan inside it")
        console.print("3. If subdirectories found, scan those too")
        console.print("4. Continue until no new directories with viable status codes")
        console.print("5. Viable status codes: 200, 301, 302, 403")
        
        # Visual flow
        console.print("\n[bold]Flow Visualization:[/bold]")
        flow_tree = RichTree("[bold]Recursive Scanning Flow[/bold]")
        
        step1 = flow_tree.add("1️⃣ Initial Scan")
        step1.add("Find: /admin [301]")
        step1.add("Find: /api [200]")
        step1.add("Find: /config [301]")
        
        step2 = flow_tree.add("2️⃣ Scan Each Directory")
        admin_scan = step2.add("Scan /admin/")
        admin_scan.add("Find: /admin/users [200]")
        admin_scan.add("Find: /admin/config [403]")
        
        api_scan = step2.add("Scan /api/")
        api_scan.add("Find: /api/v1 [200]")
        api_scan.add("Find: /api/v2 [200]")
        
        step3 = flow_tree.add("3️⃣ Continue Recursively")
        step3.add("Scan /admin/users/")
        step3.add("Scan /admin/config/")
        step3.add("Scan /api/v1/")
        step3.add("Scan /api/v2/")
        
        step4 = flow_tree.add("4️⃣ Stop When No New Content")
        step4.add("No new directories found")
        step4.add("All paths exhausted")
        
        console.print(flow_tree)
        
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
    finally:
        await engine.close()
    
    console.print("\n[bold green]✅ Demo Complete![/bold green]")


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        console.print("[bold]Recursive Scanning Flow Demo[/bold]")
        console.print("\nUsage: python demo_recursive_flow.py <target_url>")
        console.print("Example: python demo_recursive_flow.py http://127.0.0.1:8080/")
        sys.exit(1)
    
    target_url = sys.argv[1]
    if not target_url.startswith(('http://', 'https://')):
        target_url = 'http://' + target_url
    
    if not target_url.endswith('/'):
        target_url += '/'
    
    asyncio.run(demo_recursive_flow(target_url))


if __name__ == "__main__":
    main()