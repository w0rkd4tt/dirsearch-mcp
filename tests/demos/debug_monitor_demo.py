#!/usr/bin/env python3
"""
Demo script for the real-time debug monitor
Shows how to use the debug monitor to track scan progress and analyze results
"""
import asyncio
import sys
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.dirsearch_engine import DirsearchEngine, ScanOptions
from src.utils.debug_monitor import DebugMonitor, EventType
from src.utils.logger import Logger
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich import print as rprint


class DebugMonitorDemo:
    """Demo for debug monitor functionality"""
    
    def __init__(self):
        self.console = Console()
        self.logger = Logger()
        
    async def run_basic_demo(self):
        """Basic debug monitor demo with live display"""
        rprint("\n[bold cyan]Basic Debug Monitor Demo[/bold cyan]")
        rprint("This demo shows real-time monitoring of a directory scan\n")
        
        # Get target URL
        target = Prompt.ask("Enter target URL", default="http://testphp.vulnweb.com")
        
        # Create scan options with debug enabled
        options = ScanOptions(
            threads=5,
            timeout=10,
            recursive=False,
            debug_enabled=True,
            debug_live_display=True
        )
        
        # Create engine
        engine = DirsearchEngine(logger=self.logger)
        
        # Load a small wordlist for demo
        wordlist = [
            "admin", "login", "dashboard", "api", "config", 
            "test", "backup", "old", "temp", "upload",
            "images", "css", "js", "fonts", "assets"
        ]
        
        rprint(f"\n[yellow]Starting scan on {target} with {len(wordlist)} paths...[/yellow]\n")
        
        try:
            # Run scan with debug monitor
            results = await engine.scan_target(target, wordlist, options)
            
            rprint(f"\n[green]Scan completed! Found {len(results)} results[/green]")
            
            # Show summary from debug monitor
            if engine.debug_monitor:
                summary = engine.debug_monitor.get_summary()
                self._display_summary(summary)
                
        except KeyboardInterrupt:
            rprint("\n[red]Scan interrupted by user[/red]")
        finally:
            await engine.close()
            
    async def run_advanced_demo(self):
        """Advanced demo with custom callbacks and filtering"""
        rprint("\n[bold cyan]Advanced Debug Monitor Demo[/bold cyan]")
        rprint("This demo shows advanced features: callbacks, filtering, and export\n")
        
        # Get target URL
        target = Prompt.ask("Enter target URL", default="http://testphp.vulnweb.com")
        
        # Create debug monitor
        monitor = DebugMonitor(self.console)
        
        # Register custom callbacks
        found_paths = []
        
        def on_directory_found(event):
            found_paths.append(event.path)
            rprint(f"[yellow]➜ Found directory: {event.path}[/yellow]")
            
        def on_file_found(event):
            found_paths.append(event.path)
            rprint(f"[cyan]➜ Found file: {event.path}[/cyan]")
            
        def on_error(event):
            rprint(f"[red]✗ Error: {event.error}[/red]")
            
        monitor.register_callback(EventType.DIRECTORY_FOUND, on_directory_found)
        monitor.register_callback(EventType.FILE_FOUND, on_file_found)
        monitor.register_callback(EventType.ERROR_OCCURRED, on_error)
        
        # Set filters
        monitor.set_filter("min_status_code", 200)
        monitor.set_filter("max_status_code", 403)
        
        # Create scan options
        options = ScanOptions(
            threads=10,
            timeout=10,
            recursive=True,
            recursion_depth=2,
            debug_enabled=True,
            debug_live_display=False  # We'll use custom display
        )
        
        # Create engine with monitor
        engine = DirsearchEngine(logger=self.logger)
        engine.debug_monitor = monitor
        engine.debug_integration = monitor.get_integration()
        
        # Start monitoring
        monitor.start_monitoring(target, live_display=True)
        
        # Load wordlist
        wordlist = self._get_demo_wordlist()
        
        try:
            # Run scan
            results = await engine.scan_target(target, wordlist, options)
            
            # Stop monitoring
            monitor.stop_monitoring()
            
            # Display results
            rprint(f"\n[green]Scan completed![/green]")
            rprint(f"Found paths: {', '.join(found_paths[:10])}{'...' if len(found_paths) > 10 else ''}")
            
            # Export data
            if Confirm.ask("\nExport debug data?"):
                export_path = f"debug_export_{target.replace('://', '_').replace('/', '_')}.json"
                monitor.export_events(export_path)
                rprint(f"[green]Debug data exported to: {export_path}[/green]")
                
        except KeyboardInterrupt:
            rprint("\n[red]Scan interrupted[/red]")
        finally:
            monitor.stop_monitoring()
            await engine.close()
            
    async def run_filter_demo(self):
        """Demo showing filtering capabilities"""
        rprint("\n[bold cyan]Debug Monitor Filtering Demo[/bold cyan]")
        rprint("This demo shows how to filter events for focused analysis\n")
        
        # Create monitor
        monitor = DebugMonitor(self.console)
        
        # Configure filters
        filter_choice = Prompt.ask(
            "Choose filter mode",
            choices=["errors-only", "successful-only", "status-range", "path-pattern"],
            default="successful-only"
        )
        
        if filter_choice == "errors-only":
            monitor.set_filter("show_errors_only", True)
            rprint("[yellow]Filtering: Showing only errors[/yellow]")
        elif filter_choice == "successful-only":
            monitor.set_filter("event_types", {
                EventType.DIRECTORY_FOUND, 
                EventType.FILE_FOUND,
                EventType.RESPONSE_RECEIVED
            })
            monitor.set_filter("min_status_code", 200)
            monitor.set_filter("max_status_code", 299)
            rprint("[yellow]Filtering: Showing only successful responses (200-299)[/yellow]")
        elif filter_choice == "status-range":
            min_status = int(Prompt.ask("Minimum status code", default="200"))
            max_status = int(Prompt.ask("Maximum status code", default="403"))
            monitor.set_filter("min_status_code", min_status)
            monitor.set_filter("max_status_code", max_status)
            rprint(f"[yellow]Filtering: Status codes {min_status}-{max_status}[/yellow]")
        elif filter_choice == "path-pattern":
            pattern = Prompt.ask("Path regex pattern", default="admin|api|config")
            monitor.set_filter("path_pattern", pattern)
            rprint(f"[yellow]Filtering: Paths matching /{pattern}/[/yellow]")
            
        # Run scan with filters
        target = "http://testphp.vulnweb.com"
        
        options = ScanOptions(
            threads=5,
            timeout=10,
            debug_enabled=False  # We're using custom monitor
        )
        
        engine = DirsearchEngine(logger=self.logger)
        engine.debug_monitor = monitor
        engine.debug_integration = monitor.get_integration()
        
        monitor.start_monitoring(target, live_display=True)
        
        wordlist = ["admin", "api", "config", "test", "backup", "login", "users", "data"]
        
        try:
            await engine.scan_target(target, wordlist, options)
            monitor.stop_monitoring()
            
            summary = monitor.get_summary()
            self._display_summary(summary)
            
        except KeyboardInterrupt:
            rprint("\n[red]Scan interrupted[/red]")
        finally:
            monitor.stop_monitoring()
            await engine.close()
            
    def _get_demo_wordlist(self):
        """Get a comprehensive wordlist for demo"""
        return [
            # Admin paths
            "admin", "administrator", "admin-panel", "control-panel",
            "wp-admin", "admin/login", "admin.php",
            
            # API paths
            "api", "api/v1", "api/v2", "api/users", "api/auth",
            "graphql", "rest", "api/docs",
            
            # Common directories
            "backup", "old", "temp", "tmp", "test", "dev",
            "staging", "uploads", "download", "files",
            
            # Config files
            "config", "config.php", "settings", "conf",
            ".env", ".git", ".svn", "web.config",
            
            # Auth paths
            "login", "signin", "auth", "authenticate",
            "logout", "register", "signup",
            
            # Data paths
            "data", "database", "db", "sql", "dump",
            
            # Framework specific
            "vendor", "node_modules", "components", "modules",
            "plugins", "themes", "assets", "public"
        ]
        
    def _display_summary(self, summary: dict):
        """Display scan summary"""
        duration = summary.get('duration', 0)
        
        summary_text = f"""
[bold]Scan Summary[/bold]
────────────────────
Target: {summary.get('target', 'N/A')}
Duration: {duration:.2f} seconds
Total Events: {summary.get('total_events', 0)}
Requests/sec: {summary.get('requests_per_second', 0):.2f}

[bold]Statistics:[/bold]
• Total Requests: {summary['stats'].get('total_requests', 0)}
• Successful: {summary['stats'].get('successful_responses', 0)}
• Errors: {summary['stats'].get('errors', 0)}
• Directories Found: {summary['stats'].get('directories_found', 0)}
• Files Found: {summary['stats'].get('files_found', 0)}
• Filtered: {summary['stats'].get('filtered_paths', 0)}
• Wildcards: {summary['stats'].get('wildcard_hits', 0)}

[bold]Status Code Distribution:[/bold]"""
        
        for code, count in sorted(summary['stats'].get('status_codes', {}).items()):
            summary_text += f"\n• {code}: {count}"
            
        self.console.print(Panel(summary_text, title="Debug Monitor Summary"))


async def main():
    """Main demo runner"""
    demo = DebugMonitorDemo()
    
    while True:
        rprint("\n[bold cyan]Debug Monitor Demo Menu[/bold cyan]")
        rprint("1. Basic Demo - Live monitoring with default settings")
        rprint("2. Advanced Demo - Custom callbacks and export")
        rprint("3. Filter Demo - Event filtering examples")
        rprint("4. Exit")
        
        choice = Prompt.ask("\nSelect demo", choices=["1", "2", "3", "4"], default="1")
        
        if choice == "1":
            await demo.run_basic_demo()
        elif choice == "2":
            await demo.run_advanced_demo()
        elif choice == "3":
            await demo.run_filter_demo()
        elif choice == "4":
            rprint("\n[yellow]Thanks for trying the debug monitor demo![/yellow]")
            break
            
        if not Confirm.ask("\nRun another demo?", default=True):
            break


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[red]Demo interrupted[/red]")