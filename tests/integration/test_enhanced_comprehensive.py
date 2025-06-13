#!/usr/bin/env python3
"""
Comprehensive test with enhanced wordlist to show recursive + depth analysis
"""

import asyncio
import sys
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


async def test_comprehensive(target_url):
    """Run comprehensive test with better wordlist"""
    
    console.print(Panel.fit(
        f"[bold]Comprehensive Recursive + Deep Analysis Test[/bold]\n"
        f"Target: {target_url}",
        border_style="cyan"
    ))
    
    engine = DirsearchEngine(Settings())
    
    # More comprehensive wordlist
    wordlist = [
        # Directories
        "admin", "api", "app", "assets", "backup", "bin",
        "config", "css", "data", "database", "db", "debug",
        "demo", "dev", "docs", "download", "files", "images",
        "img", "includes", "js", "lib", "logs", "media",
        "public", "scripts", "static", "system", "test", "tmp",
        "upload", "uploads", "user", "users", "vendor",
        
        # Files
        "index.php", "login.php", "admin.php", "config.php",
        "api.php", "test.php", "info.php", "phpinfo.php",
        "robots.txt", ".htaccess", "sitemap.xml", ".env",
        "composer.json", "package.json", "README.md",
        "wp-config.php", "database.php", "connect.php",
        
        # Hidden files
        ".git/config", ".git/HEAD", ".svn/entries",
        
        # Backup files
        "backup.sql", "backup.zip", "dump.sql",
        
        # Common API paths
        "api/v1", "api/v2", "api/users", "api/login"
    ]
    
    options = ScanOptions(
        recursive=True,
        recursion_depth=0,  # Unlimited
        crawl=True,         # Deep analysis enabled
        threads=10,
        timeout=10,
        exclude_status_codes=[404],
        follow_redirects=True
    )
    
    try:
        console.print(f"\n[bold]Starting comprehensive scan...[/bold]")
        console.print(f"Wordlist: {len(wordlist)} entries")
        
        start_time = datetime.now()
        results = await engine.scan_target(target_url, wordlist, options)
        duration = (datetime.now() - start_time).total_seconds()
        
        # Results summary
        console.print(f"\n[bold green]✅ Scan completed in {duration:.2f} seconds[/bold green]")
        console.print(f"Total discovered: {len(results)} paths")
        
        # Categorize results
        dirs = [r for r in results if r.is_directory]
        files = [r for r in results if not r.is_directory]
        
        # Show results by status code
        by_status = {}
        for r in results:
            if r.status_code not in by_status:
                by_status[r.status_code] = []
            by_status[r.status_code].append(r)
        
        console.print("\n[bold]Results by Status Code:[/bold]")
        status_table = Table(show_header=True)
        status_table.add_column("Status", style="cyan")
        status_table.add_column("Count", style="yellow")
        status_table.add_column("Examples")
        
        for status in sorted(by_status.keys()):
            paths = by_status[status]
            examples = ", ".join([p.path for p in paths[:3]])
            if len(paths) > 3:
                examples += f" (+{len(paths)-3} more)"
            status_table.add_row(str(status), str(len(paths)), examples)
        
        console.print(status_table)
        
        # Show deep analysis results
        if hasattr(engine, '_endpoint_analysis_results') and engine._endpoint_analysis_results:
            console.print(f"\n[bold]Deep Analysis Results:[/bold]")
            console.print(f"Analyzed {len(engine._endpoint_analysis_results)} endpoints")
            
            total_extracted = sum(r['extracted_count'] for r in engine._endpoint_analysis_results)
            console.print(f"Extracted {total_extracted} hidden paths")
            
            # Show top extractors
            top_results = sorted(engine._endpoint_analysis_results, 
                               key=lambda x: x['extracted_count'], reverse=True)[:10]
            
            if top_results:
                extract_table = Table(title="Top Endpoints with Extracted Content")
                extract_table.add_column("Endpoint", style="cyan")
                extract_table.add_column("Extracted", style="yellow")
                extract_table.add_column("Sample Paths", style="green")
                
                for result in top_results:
                    samples = ", ".join(result['extracted_paths'][:2])
                    if result['extracted_count'] > 2:
                        samples += f" (+{result['extracted_count']-2} more)"
                    extract_table.add_row(
                        result['path'], 
                        str(result['extracted_count']),
                        samples
                    )
                
                console.print(extract_table)
        
        # Final summary
        console.print(f"\n[bold]Summary:[/bold]")
        console.print(f"• Initial wordlist: {len(wordlist)} entries")
        console.print(f"• Total discovered: {len(results)} paths")
        console.print(f"• Directories: {len(dirs)}")
        console.print(f"• Files: {len(files)}")
        console.print(f"• Scan time: {duration:.2f} seconds")
        
        if hasattr(engine, '_endpoint_analysis_results'):
            console.print(f"• Endpoints analyzed: {len(engine._endpoint_analysis_results)}")
            console.print(f"• Hidden paths extracted: {sum(r['extracted_count'] for r in engine._endpoint_analysis_results)}")
        
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
    finally:
        await engine.close()
    
    console.print("\n[bold green]✅ Test complete![/bold green]")


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        console.print("[bold]Comprehensive Test[/bold]")
        console.print("\nUsage: python test_enhanced_comprehensive.py <target_url>")
        console.print("Example: python test_enhanced_comprehensive.py http://127.0.0.1:8080/")
        sys.exit(1)
    
    target_url = sys.argv[1]
    if not target_url.startswith(('http://', 'https://')):
        target_url = 'http://' + target_url
    
    if not target_url.endswith('/'):
        target_url += '/'
    
    asyncio.run(test_comprehensive(target_url))


if __name__ == "__main__":
    main()