#!/usr/bin/env python3
"""
Demo Complex Directory Tree
Shows how the tree looks with nested directories
"""

import asyncio
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.tree import Tree as RichTree

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.dirsearch_engine import DirsearchEngine, ScanResult
from src.config.settings import Settings

console = Console()


def create_mock_results():
    """Create mock scan results for demonstration"""
    results = [
        # Root level
        ScanResult(url="http://example.com/admin", path="admin", status_code=200, size=0, is_directory=True),
        ScanResult(url="http://example.com/api", path="api", status_code=200, size=0, is_directory=True),
        ScanResult(url="http://example.com/assets", path="assets", status_code=200, size=0, is_directory=True),
        ScanResult(url="http://example.com/config", path="config", status_code=403, size=0, is_directory=True),
        ScanResult(url="http://example.com/index.php", path="index.php", status_code=200, size=1523),
        ScanResult(url="http://example.com/robots.txt", path="robots.txt", status_code=200, size=26),
        
        # Admin subdirectories
        ScanResult(url="http://example.com/admin/users", path="admin/users", status_code=200, size=0, is_directory=True),
        ScanResult(url="http://example.com/admin/config", path="admin/config", status_code=200, size=0, is_directory=True),
        ScanResult(url="http://example.com/admin/logs", path="admin/logs", status_code=403, size=0, is_directory=True),
        ScanResult(url="http://example.com/admin/index.php", path="admin/index.php", status_code=200, size=2048),
        ScanResult(url="http://example.com/admin/login.php", path="admin/login.php", status_code=200, size=1856),
        
        # API structure
        ScanResult(url="http://example.com/api/v1", path="api/v1", status_code=200, size=0, is_directory=True),
        ScanResult(url="http://example.com/api/v2", path="api/v2", status_code=200, size=0, is_directory=True),
        ScanResult(url="http://example.com/api/docs", path="api/docs", status_code=200, size=0, is_directory=True),
        ScanResult(url="http://example.com/api/index.php", path="api/index.php", status_code=200, size=512),
        
        # Deep nesting in API
        ScanResult(url="http://example.com/api/v1/users", path="api/v1/users", status_code=200, size=0, is_directory=True),
        ScanResult(url="http://example.com/api/v1/posts", path="api/v1/posts", status_code=200, size=0, is_directory=True),
        ScanResult(url="http://example.com/api/v1/users/profile.php", path="api/v1/users/profile.php", status_code=200, size=3072),
        ScanResult(url="http://example.com/api/v1/users/list.php", path="api/v1/users/list.php", status_code=200, size=2560),
        ScanResult(url="http://example.com/api/v2/auth", path="api/v2/auth", status_code=200, size=0, is_directory=True),
        ScanResult(url="http://example.com/api/v2/auth/login.php", path="api/v2/auth/login.php", status_code=200, size=1920),
        
        # Assets structure
        ScanResult(url="http://example.com/assets/css", path="assets/css", status_code=200, size=0, is_directory=True),
        ScanResult(url="http://example.com/assets/js", path="assets/js", status_code=200, size=0, is_directory=True),
        ScanResult(url="http://example.com/assets/images", path="assets/images", status_code=200, size=0, is_directory=True),
        ScanResult(url="http://example.com/assets/css/style.css", path="assets/css/style.css", status_code=200, size=8192),
        ScanResult(url="http://example.com/assets/js/app.js", path="assets/js/app.js", status_code=200, size=16384),
        
        # Hidden/sensitive files
        ScanResult(url="http://example.com/.env", path=".env", status_code=403, size=0),
        ScanResult(url="http://example.com/.git/config", path=".git/config", status_code=403, size=0),
        ScanResult(url="http://example.com/backup.sql", path="backup.sql", status_code=200, size=524288),
    ]
    return results


def build_rich_tree_from_dict(tree_dict, parent_node=None):
    """Convert dictionary tree to Rich Tree"""
    root_tree = None
    if parent_node is None:
        root_tree = RichTree("🌐 [bold]Complex Directory Structure Example[/bold]")
        parent_node = root_tree
    
    # Add directories first
    for name, child in sorted(tree_dict.get('children', {}).items()):
        status = child.get('status', '')
        status_color = "green" if status == 200 else "yellow" if status in [301, 302] else "red" if status == 403 else "dim"
        status_text = f"[{status_color}][{status}][/{status_color}]" if status else ""
        
        node = parent_node.add(f"📁 [cyan]{name}/[/cyan] {status_text}")
        build_rich_tree_from_dict(child, node)
    
    # Add files
    for file in sorted(tree_dict.get('files', []), key=lambda x: x['name']):
        status = file.get('status', '')
        status_color = "green" if status == 200 else "yellow" if status in [301, 302] else "red" if status == 403 else "dim"
        status_text = f"[{status_color}][{status}][/{status_color}]"
        
        # Format file size
        size = file.get('size', 0)
        if size > 1024 * 1024:
            size_text = f"[dim]({size / (1024*1024):.1f} MB)[/dim]"
        elif size > 1024:
            size_text = f"[dim]({size / 1024:.1f} KB)[/dim]"
        else:
            size_text = f"[dim]({size} B)[/dim]" if size > 0 else ""
        
        parent_node.add(f"📄 {file['name']} {status_text} {size_text}")
    
    return root_tree if root_tree else parent_node


def demo_complex_tree():
    """Demo complex directory tree visualization"""
    
    console.print(Panel.fit(
        "[bold]Complex Directory Tree Demo[/bold]\n"
        "Showing nested directory structure visualization",
        border_style="cyan"
    ))
    
    # Create mock engine with results
    engine = DirsearchEngine(Settings())
    engine._results = create_mock_results()
    
    # Build and display directory tree
    console.print("\n[bold]Directory Tree Structure:[/bold]\n")
    
    # Build tree
    tree_dict = engine.build_directory_tree()
    rich_tree = build_rich_tree_from_dict(tree_dict)
    console.print(rich_tree)
    
    # Show text-based tree
    console.print("\n[bold]Text-based Tree:[/bold]\n")
    tree_string = engine.print_directory_tree()
    console.print(Panel(tree_string, title="Directory Structure", border_style="green"))
    
    # Show statistics
    stats = engine.get_directory_statistics()
    
    console.print("\n[bold]Statistics:[/bold]")
    console.print(f"📊 Total paths: {stats['total_paths']}")
    console.print(f"📁 Directories: {stats['directories']}")
    console.print(f"📄 Files: {stats['files']}")
    console.print(f"🔽 Maximum depth: {stats['max_depth']} levels")
    console.print(f"📍 Deepest path: {stats['deepest_path']}")
    
    # Show depth distribution
    console.print("\n[bold]Depth Distribution:[/bold]")
    for depth, count in sorted(stats['by_depth'].items()):
        bar = "█" * (count * 2)
        console.print(f"Level {depth}: {bar} ({count} paths)")
    
    # Show largest files
    if stats['largest_files']:
        console.print("\n[bold]Largest Files:[/bold]")
        for file_info in stats['largest_files'][:5]:
            size_mb = file_info['size'] / (1024 * 1024)
            size_kb = file_info['size'] / 1024
            if size_mb >= 1:
                console.print(f"  • {file_info['path']}: {size_mb:.2f} MB")
            else:
                console.print(f"  • {file_info['path']}: {size_kb:.2f} KB")


def main():
    """Main entry point"""
    console.print("[bold]Complex Directory Tree Demo[/bold]")
    console.print("\nThis demo shows how the directory tree looks with:")
    console.print("  • Multiple levels of nesting")
    console.print("  • Different status codes (200, 403)")
    console.print("  • Various file sizes")
    console.print("  • Complex directory structure")
    
    demo_complex_tree()
    
    console.print("\n" + "="*60)
    console.print("[bold green]✅ Demo Complete![/bold green]")


if __name__ == "__main__":
    main()