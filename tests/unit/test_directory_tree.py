#!/usr/bin/env python3
"""
Test Directory Tree Visualization
Shows directory structure after scan completion
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree as RichTree

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.dirsearch_engine import DirsearchEngine, ScanOptions
from src.config.settings import Settings

console = Console()


def build_rich_tree(tree_dict, parent_node=None):
    """Convert dictionary tree to Rich Tree for better visualization"""
    root_tree = None
    if parent_node is None:
        # Create root
        root_tree = RichTree("🌐 [bold]Scan Results - Directory Structure[/bold]")
        parent_node = root_tree
    
    # Add directories first
    for name, child in sorted(tree_dict.get('children', {}).items()):
        status = child.get('status', '')
        status_color = "green" if status == 200 else "yellow" if status in [301, 302] else "red" if status == 403 else "dim"
        status_text = f"[{status_color}][{status}][/{status_color}]" if status else ""
        
        node = parent_node.add(f"📁 [cyan]{name}/[/cyan] {status_text}")
        build_rich_tree(child, node)
    
    # Add files
    for file in sorted(tree_dict.get('files', []), key=lambda x: x['name']):
        status = file.get('status', '')
        status_color = "green" if status == 200 else "yellow" if status in [301, 302] else "red" if status == 403 else "dim"
        status_text = f"[{status_color}][{status}][/{status_color}]"
        size_text = f"[dim]({file['size']} bytes)[/dim]" if file.get('size', 0) > 0 else ""
        
        parent_node.add(f"📄 {file['name']} {status_text} {size_text}")
    
    return root_tree if root_tree else parent_node


async def test_directory_tree(target_url):
    """Test directory tree visualization"""
    
    console.print(Panel.fit(
        f"[bold]Directory Tree Visualization Test[/bold]\n"
        f"Target: {target_url}",
        border_style="cyan"
    ))
    
    engine = DirsearchEngine(Settings())
    
    # Comprehensive wordlist for better tree
    wordlist = [
        # Root level directories
        "admin", "api", "app", "assets", "backup", "bin", "cache",
        "config", "css", "data", "database", "db", "debug", "demo",
        "dev", "docs", "download", "files", "fonts", "images", "img",
        "includes", "js", "lib", "logs", "media", "private", "public",
        "scripts", "src", "static", "system", "test", "tmp", "tools",
        "upload", "uploads", "user", "users", "vendor", "views",
        
        # Subdirectories
        "admin/users", "admin/config", "admin/logs", "admin/backup",
        "api/v1", "api/v2", "api/users", "api/auth",
        "assets/css", "assets/js", "assets/images",
        "includes/lib", "includes/functions",
        
        # Files at different levels
        "index.php", "login.php", "config.php", "robots.txt",
        "admin/index.php", "admin/login.php", "admin/dashboard.php",
        "api/index.php", "api/v1/users.php", "api/v2/auth.php",
        "css/style.css", "js/app.js", "images/logo.png",
        ".htaccess", ".env", "composer.json", "package.json",
        
        # Deep paths
        "admin/users/list.php", "admin/users/edit.php",
        "api/v1/users/profile.php", "api/v2/auth/login.php"
    ]
    
    options = ScanOptions(
        recursive=True,
        recursion_depth=0,
        crawl=True,
        threads=10,
        timeout=10,
        exclude_status_codes=[404],
        follow_redirects=True
    )
    
    try:
        # Run scan
        console.print("\n[bold]1. Running Scan...[/bold]")
        start_time = datetime.now()
        
        results = await engine.scan_target(target_url, wordlist, options)
        
        duration = (datetime.now() - start_time).total_seconds()
        console.print(f"✅ Scan completed in {duration:.2f} seconds")
        console.print(f"Found {len(results)} paths\n")
        
        # Build and display directory tree
        console.print("[bold]2. Directory Tree Structure:[/bold]\n")
        
        # Method 1: Using Rich Tree (colorful)
        tree_dict = engine.build_directory_tree()
        rich_tree = build_rich_tree(tree_dict)
        console.print(rich_tree)
        
        # Method 2: Using text-based tree
        console.print("\n[bold]3. Text-based Directory Tree:[/bold]\n")
        tree_string = engine.print_directory_tree()
        if tree_string:
            console.print(Panel(tree_string, title="Directory Structure", border_style="green"))
        else:
            console.print("[dim]No directory structure to display[/dim]")
        
        # Get and display statistics
        console.print("\n[bold]4. Directory Statistics:[/bold]")
        stats = engine.get_directory_statistics()
        
        stats_table = Table(show_header=False, box=None)
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="yellow")
        
        stats_table.add_row("Total Paths", str(stats['total_paths']))
        stats_table.add_row("Directories", str(stats['directories']))
        stats_table.add_row("Files", str(stats['files']))
        stats_table.add_row("Maximum Depth", str(stats['max_depth']))
        stats_table.add_row("Deepest Path", stats['deepest_path'] or "N/A")
        
        console.print(stats_table)
        
        # Status code breakdown
        if stats['by_status']:
            console.print("\n[bold]5. Paths by Status Code:[/bold]")
            status_table = Table(show_header=True)
            status_table.add_column("Status", style="cyan")
            status_table.add_column("Count", style="yellow")
            status_table.add_column("Type", style="green")
            
            for status, count in sorted(stats['by_status'].items()):
                status_type = "Success" if status == 200 else \
                             "Redirect" if status in [301, 302] else \
                             "Forbidden" if status == 403 else "Other"
                status_table.add_row(str(status), str(count), status_type)
            
            console.print(status_table)
        
        # Depth distribution
        if stats['by_depth']:
            console.print("\n[bold]6. Paths by Depth Level:[/bold]")
            depth_table = Table(show_header=True)
            depth_table.add_column("Depth", style="cyan")
            depth_table.add_column("Count", style="yellow")
            depth_table.add_column("Visual", style="green")
            
            max_count = max(stats['by_depth'].values())
            for depth, count in sorted(stats['by_depth'].items()):
                bar_length = int((count / max_count) * 30)
                bar = "█" * bar_length
                depth_table.add_row(str(depth), str(count), bar)
            
            console.print(depth_table)
        
        # Largest files
        if stats['largest_files']:
            console.print("\n[bold]7. Largest Files:[/bold]")
            files_table = Table(show_header=True)
            files_table.add_column("File", style="cyan")
            files_table.add_column("Size", style="yellow")
            
            for file_info in stats['largest_files'][:5]:
                size_kb = file_info['size'] / 1024
                files_table.add_row(file_info['path'], f"{size_kb:.2f} KB")
            
            console.print(files_table)
        
        # Summary visualization
        console.print("\n[bold]8. Visual Summary:[/bold]")
        
        # Create a simple ASCII representation
        total = stats['total_paths']
        dirs = stats['directories']
        files = stats['files']
        
        if total > 0:
            dir_percent = int((dirs / total) * 50)
            file_percent = int((files / total) * 50)
            
            console.print(f"\nDirectories: [green]{'█' * dir_percent}[/green] {dirs} ({dirs/total*100:.1f}%)")
            console.print(f"Files:       [blue]{'█' * file_percent}[/blue] {files} ({files/total*100:.1f}%)")
        
        # Export options
        console.print("\n[bold]9. Export Options:[/bold]")
        console.print("The directory tree can be exported in various formats:")
        console.print("  • JSON format for programmatic use")
        console.print("  • HTML format for web display")
        console.print("  • Markdown format for documentation")
        console.print("  • Plain text for simple viewing")
        
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
    finally:
        await engine.close()
    
    console.print("\n" + "="*60)
    console.print("[bold green]✅ Directory Tree Visualization Complete![/bold green]")


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        console.print("[bold]Directory Tree Visualization Test[/bold]")
        console.print("\nUsage: python test_directory_tree.py <target_url>")
        console.print("Example: python test_directory_tree.py http://127.0.0.1:8080/")
        console.print("\nThis will:")
        console.print("  • Scan the target")
        console.print("  • Build directory structure")
        console.print("  • Display visual tree")
        console.print("  • Show statistics")
        sys.exit(1)
    
    target_url = sys.argv[1]
    if not target_url.startswith(('http://', 'https://')):
        target_url = 'http://' + target_url
    
    if not target_url.endswith('/'):
        target_url += '/'
    
    asyncio.run(test_directory_tree(target_url))


if __name__ == "__main__":
    main()