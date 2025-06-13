#!/usr/bin/env python3
"""
Compare scanning approaches:
1. Basic scan (no recursive, no depth)
2. Recursive only
3. Recursive + Deep analysis of all endpoints (NEW)
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.dirsearch_engine import DirsearchEngine, ScanOptions
from src.config.settings import Settings

console = Console()


async def run_scan(target_url, wordlist, options, description):
    """Run a scan with given options and return results"""
    engine = DirsearchEngine(Settings())
    
    start_time = datetime.now()
    results = await engine.scan_target(target_url, wordlist, options)
    duration = (datetime.now() - start_time).total_seconds()
    
    # Get analysis results if available
    analysis_results = None
    if hasattr(engine, '_endpoint_analysis_results'):
        analysis_results = engine._endpoint_analysis_results
    
    await engine.close()
    
    return {
        'description': description,
        'results': results,
        'duration': duration,
        'analysis_results': analysis_results
    }


async def test_comparison(target_url):
    """Compare different scanning approaches"""
    
    console.print(Panel.fit(
        f"[bold]Scanning Approach Comparison[/bold]\n"
        f"Target: {target_url}",
        border_style="cyan"
    ))
    
    # Common wordlist
    wordlist = [
        "index.php",
        "admin",
        "api",
        "config",
        "test",
        "login.php"
    ]
    
    # Test 1: Basic scan
    console.print("\n[bold]1. Running Basic Scan...[/bold]")
    basic_options = ScanOptions(
        recursive=False,
        crawl=False,
        threads=5,
        timeout=10,
        exclude_status_codes=[404]
    )
    basic_results = await run_scan(target_url, wordlist, basic_options, "Basic Scan")
    
    # Test 2: Recursive only
    console.print("\n[bold]2. Running Recursive Scan...[/bold]")
    recursive_options = ScanOptions(
        recursive=True,
        recursion_depth=2,
        crawl=False,  # No deep analysis
        threads=5,
        timeout=10,
        exclude_status_codes=[404]
    )
    recursive_results = await run_scan(target_url, wordlist, recursive_options, "Recursive Only")
    
    # Test 3: Recursive + Deep Analysis (NEW)
    console.print("\n[bold]3. Running Recursive + Deep Analysis...[/bold]")
    full_options = ScanOptions(
        recursive=True,
        recursion_depth=0,  # Unlimited
        crawl=True,  # Enable deep analysis
        threads=5,
        timeout=10,
        exclude_status_codes=[404]
    )
    full_results = await run_scan(target_url, wordlist, full_options, "Recursive + Deep Analysis")
    
    # Display comparison
    console.print("\n" + "="*80)
    console.print("[bold]COMPARISON RESULTS[/bold]")
    console.print("="*80 + "\n")
    
    # Create comparison table
    comparison_table = Table(title="Scanning Approach Comparison", show_header=True)
    comparison_table.add_column("Approach", style="cyan", width=25)
    comparison_table.add_column("Paths Found", style="yellow", justify="center")
    comparison_table.add_column("Directories", style="green", justify="center")
    comparison_table.add_column("Files", style="green", justify="center")
    comparison_table.add_column("Duration", style="magenta", justify="center")
    comparison_table.add_column("Endpoints Analyzed", style="blue", justify="center")
    comparison_table.add_column("Paths Extracted", style="red", justify="center")
    
    for result in [basic_results, recursive_results, full_results]:
        dirs = len([r for r in result['results'] if r.is_directory])
        files = len([r for r in result['results'] if not r.is_directory])
        
        analyzed = 0
        extracted = 0
        if result['analysis_results']:
            analyzed = len(result['analysis_results'])
            extracted = sum(r['extracted_count'] for r in result['analysis_results'])
        
        comparison_table.add_row(
            result['description'],
            str(len(result['results'])),
            str(dirs),
            str(files),
            f"{result['duration']:.2f}s",
            str(analyzed) if analyzed > 0 else "-",
            str(extracted) if extracted > 0 else "-"
        )
    
    console.print(comparison_table)
    
    # Show improvement metrics
    console.print("\n[bold]Improvement Metrics:[/bold]")
    
    basic_count = len(basic_results['results'])
    recursive_count = len(recursive_results['results'])
    full_count = len(full_results['results'])
    
    improvement_table = Table(show_header=False, box=None)
    improvement_table.add_column("Metric", style="cyan")
    improvement_table.add_column("Value", style="green")
    
    improvement_table.add_row(
        "Basic → Recursive improvement",
        f"+{recursive_count - basic_count} paths ({(recursive_count/basic_count - 1)*100:.0f}% increase)"
    )
    
    improvement_table.add_row(
        "Recursive → Full improvement",
        f"+{full_count - recursive_count} paths ({(full_count/recursive_count - 1)*100:.0f}% increase)"
    )
    
    improvement_table.add_row(
        "Basic → Full improvement",
        f"+{full_count - basic_count} paths ({(full_count/basic_count - 1)*100:.0f}% increase)"
    )
    
    console.print(improvement_table)
    
    # Show unique findings in full scan
    console.print("\n[bold]Unique Findings in Full Scan:[/bold]")
    
    # Get paths found only in full scan
    basic_paths = {r.path for r in basic_results['results']}
    recursive_paths = {r.path for r in recursive_results['results']}
    full_paths = {r.path for r in full_results['results']}
    
    unique_to_full = full_paths - recursive_paths
    
    if unique_to_full:
        console.print(f"[green]Found {len(unique_to_full)} paths only through deep analysis:[/green]")
        
        # Categorize unique findings
        api_paths = [p for p in unique_to_full if '/api/' in p or p.startswith('api/')]
        hidden_paths = [p for p in unique_to_full if any(x in p for x in ['debug', 'test', 'dev', 'admin'])]
        config_paths = [p for p in unique_to_full if any(x in p for x in ['config', 'settings', '.env'])]
        
        if api_paths:
            console.print(f"\n  [yellow]API Endpoints ({len(api_paths)}):[/yellow]")
            for path in api_paths[:5]:
                console.print(f"    • {path}")
        
        if hidden_paths:
            console.print(f"\n  [yellow]Hidden/Debug Paths ({len(hidden_paths)}):[/yellow]")
            for path in hidden_paths[:5]:
                console.print(f"    • {path}")
        
        if config_paths:
            console.print(f"\n  [yellow]Config Files ({len(config_paths)}):[/yellow]")
            for path in config_paths[:5]:
                console.print(f"    • {path}")
    else:
        console.print("[dim]No unique paths found (target may have limited content)[/dim]")
    
    # Visual representation
    console.print("\n[bold]Visual Representation:[/bold]")
    
    # Create visual bars
    max_width = 60
    basic_bar = "█" * int((basic_count / full_count) * max_width) if full_count > 0 else ""
    recursive_bar = "█" * int((recursive_count / full_count) * max_width) if full_count > 0 else ""
    full_bar = "█" * max_width
    
    console.print(f"\nBasic:      [{basic_bar:<{max_width}}] {basic_count} paths")
    console.print(f"Recursive:  [{recursive_bar:<{max_width}}] {recursive_count} paths")
    console.print(f"Full:       [{full_bar:<{max_width}}] {full_count} paths")
    
    # Conclusion
    console.print("\n[bold]Conclusion:[/bold]")
    console.print("✅ Basic scan finds initial paths")
    console.print("✅ Recursive scan explores directories")
    console.print("✅ Deep analysis extracts hidden endpoints from content")
    console.print("✅ Combined approach provides most comprehensive coverage")
    
    console.print("\n" + "="*60)
    console.print("[bold green]✅ Comparison Complete![/bold green]")


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        console.print("[bold]Scanning Approach Comparison[/bold]")
        console.print("\nUsage: python test_comparison.py <target_url>")
        console.print("Example: python test_comparison.py http://127.0.0.1:8080/")
        console.print("\nCompares:")
        console.print("  1. Basic scan (no recursive, no depth)")
        console.print("  2. Recursive scan only")
        console.print("  3. Recursive + Deep endpoint analysis (NEW)")
        sys.exit(1)
    
    target_url = sys.argv[1]
    if not target_url.startswith(('http://', 'https://')):
        target_url = 'http://' + target_url
    
    if not target_url.endswith('/'):
        target_url += '/'
    
    asyncio.run(test_comparison(target_url))


if __name__ == "__main__":
    main()