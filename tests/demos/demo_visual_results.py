#!/usr/bin/env python3
"""
Visual Demo of Recursive + Deep Analysis Results
Shows the complete flow with visual output
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.dirsearch_engine import DirsearchEngine, ScanOptions
from src.config.settings import Settings

console = Console()


async def demo_visual_results(target_url):
    """Visual demonstration of the scanning process and results"""
    
    # Create layout
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main"),
        Layout(name="footer", size=3)
    )
    
    # Header
    layout["header"].update(Panel(
        f"[bold]Visual Demo: Recursive + Deep Analysis[/bold]\n"
        f"Target: {target_url}",
        style="cyan"
    ))
    
    # Footer
    layout["footer"].update(Panel(
        "[dim]Watch the scanning process in action![/dim]",
        style="green"
    ))
    
    # Main content
    main_content = Text()
    layout["main"].update(Panel(main_content))
    
    # Start live display
    with Live(layout, refresh_per_second=2, console=console):
        # Initialize engine
        engine = DirsearchEngine(Settings())
        
        # Small wordlist
        wordlist = ["index.php", "admin", "api", "test", "robots.txt"]
        
        # Options
        options = ScanOptions(
            recursive=True,
            recursion_depth=0,
            crawl=True,
            threads=3,
            timeout=10,
            exclude_status_codes=[404]
        )
        
        # Phase 1: Initial scan
        main_content.append("[bold yellow]Phase 1: Initial Scan[/bold yellow]\n\n")
        main_content.append(f"Starting with {len(wordlist)} paths...\n")
        time.sleep(1)
        
        start_time = datetime.now()
        
        # Track progress
        original_scan_single = engine._scan_single_path
        scan_count = [0]
        
        async def tracked_scan(*args, **kwargs):
            scan_count[0] += 1
            if scan_count[0] % 5 == 0:
                main_content.append(f"  Scanned {scan_count[0]} paths...\n")
            return await original_scan_single(*args, **kwargs)
        
        engine._scan_single_path = tracked_scan
        
        # Run scan
        results = await engine.scan_target(target_url, wordlist, options)
        
        duration = (datetime.now() - start_time).total_seconds()
        
        # Show results
        main_content.append(f"\n✅ Scan completed in {duration:.2f} seconds\n")
        main_content.append(f"Total paths found: {len(results)}\n\n")
        
        # Phase 2: Show recursive results
        main_content.append("[bold yellow]Phase 2: Recursive Scan Results[/bold yellow]\n\n")
        
        dirs = [r for r in results if r.is_directory]
        files = [r for r in results if not r.is_directory]
        
        main_content.append(f"📁 Directories found: {len(dirs)}\n")
        for d in dirs[:5]:
            main_content.append(f"   • {d.path}\n")
        if len(dirs) > 5:
            main_content.append(f"   ... and {len(dirs) - 5} more\n")
        
        main_content.append(f"\n📄 Files found: {len(files)}\n")
        for f in files[:5]:
            main_content.append(f"   • {f.path}\n")
        if len(files) > 5:
            main_content.append(f"   ... and {len(files) - 5} more\n")
        
        time.sleep(2)
        
        # Phase 3: Deep analysis results
        main_content.append("\n[bold yellow]Phase 3: Deep Endpoint Analysis[/bold yellow]\n\n")
        
        if hasattr(engine, '_endpoint_analysis_results') and engine._endpoint_analysis_results:
            analysis_results = engine._endpoint_analysis_results
            total_analyzed = len(analysis_results)
            total_extracted = sum(r['extracted_count'] for r in analysis_results)
            
            main_content.append(f"🔍 Analyzed {total_analyzed} endpoints\n")
            main_content.append(f"🎯 Extracted {total_extracted} hidden paths\n\n")
            
            # Show top extractors
            top_extractors = sorted(analysis_results, key=lambda x: x['extracted_count'], reverse=True)[:3]
            if top_extractors:
                main_content.append("Top endpoints with extracted content:\n")
                for result in top_extractors:
                    main_content.append(f"  • {result['path']} → {result['extracted_count']} paths\n")
                    for path in result['extracted_paths'][:2]:
                        main_content.append(f"    - {path}\n")
        else:
            main_content.append("[dim]No deep analysis results available[/dim]\n")
        
        time.sleep(2)
        
        # Phase 4: Summary
        main_content.append("\n[bold yellow]Phase 4: Final Summary[/bold yellow]\n\n")
        
        # Create summary table
        summary = f"""
Initial wordlist:     {len(wordlist)} paths
Total discovered:     {len(results)} paths
Expansion factor:     {len(results) / len(wordlist):.1f}x
Directories found:    {len(dirs)}
Files found:         {len(files)}
Scan duration:       {duration:.2f} seconds
"""
        main_content.append(summary)
        
        # Success message
        main_content.append("\n[bold green]✅ Complete scan with deep analysis finished![/bold green]\n")
        main_content.append("\nThe engine automatically:\n")
        main_content.append("1. Scanned initial paths\n")
        main_content.append("2. Recursively explored directories\n")
        main_content.append("3. Analyzed ALL endpoints for hidden content\n")
        main_content.append("4. Scanned extracted paths\n")
        
        await engine.close()
        time.sleep(3)
    
    # Final display
    console.print("\n" + "="*60)
    console.print("[bold green]✅ Visual Demo Complete![/bold green]")
    console.print("="*60)


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        console.print("[bold]Visual Results Demo[/bold]")
        console.print("\nUsage: python demo_visual_results.py <target_url>")
        console.print("Example: python demo_visual_results.py http://127.0.0.1:8080/")
        console.print("\nShows a visual demonstration of the scanning process")
        sys.exit(1)
    
    target_url = sys.argv[1]
    if not target_url.startswith(('http://', 'https://')):
        target_url = 'http://' + target_url
    
    if not target_url.endswith('/'):
        target_url += '/'
    
    asyncio.run(demo_visual_results(target_url))


if __name__ == "__main__":
    main()