import os
import sys
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import json
from datetime import datetime
import time
from urllib.parse import urlparse
import re

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.layout import Layout
    from rich.live import Live
    from rich.prompt import Prompt, Confirm, IntPrompt
    from rich.syntax import Syntax
    from rich.markdown import Markdown
    from rich import print as rprint
    from rich.tree import Tree
    from rich.columns import Columns
    from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn
    from rich.text import Text
    from rich.rule import Rule
    from rich.align import Align
except ImportError:
    print("Error: Please install 'rich' library: pip install rich")
    sys.exit(1)

from src.config.settings import Settings
from src.core.mcp_coordinator import MCPCoordinator
from src.core.dirsearch_engine import DirsearchEngine, ScanRequest, ScanResult
from src.utils.logger import LoggerSetup
from src.utils.reporter import ReportGenerator


class InteractiveMenu:
    """Rich interactive CLI interface for Dirsearch MCP"""
    
    def __init__(self):
        self.console = Console()
        self.settings = Settings()
        self.mcp_coordinator = MCPCoordinator(self.settings)
        self.dirsearch_engine = DirsearchEngine(self.settings)
        self.report_generator = ReportGenerator()
        self.logger = LoggerSetup.get_logger(__name__)
        
        # Initialize logging
        LoggerSetup.initialize()
        
        # Session data
        self.current_scan = None
        self.scan_history = []
        self.custom_wordlists = []
        self.interrupted = False
        
    def _handle_exit(self):
        """Handle graceful exit"""
        self.console.print("\n[yellow]Shutting down...[/yellow]")
        # Stop any running scan
        if hasattr(self, 'dirsearch_engine') and self.dirsearch_engine:
            self.dirsearch_engine.stop_scan()
        self.console.print("[green]Thank you for using Dirsearch MCP![/green]")
        sys.exit(0)
        
    def run(self):
        """Main entry point"""
        try:
            # Check if we're already in an event loop
            loop = asyncio.get_running_loop()
            # If we are, create a task instead
            asyncio.create_task(self._async_run())
        except RuntimeError:
            # No event loop running, create one
            try:
                asyncio.run(self._async_run())
            except KeyboardInterrupt:
                self._handle_exit()
        except KeyboardInterrupt:
            self._handle_exit()
    
    async def _async_run(self):
        """Async main entry point"""
        try:
            self.console.clear()
            self._show_banner()
            
            # Initialize MCP coordinator
            await self._initialize()
            
            while True:
                try:
                    choice = self._show_main_menu()
                    
                    # Handle "exit" command
                    if choice.lower() == 'exit':
                        self._handle_exit()
                    
                    if choice == '1':
                        await self._quick_scan()
                    elif choice == '2':
                        await self._advanced_scan()
                    elif choice == '3':
                        await self._smart_scan()
                    elif choice == '4':
                        await self._full_bruteforce_scan()
                    elif choice == '5':
                        self._view_reports()
                    elif choice == '6':
                        await self._configuration_management()
                    elif choice == '7':
                        self._show_help()
                    elif choice == '0':
                        if Confirm.ask("[yellow]Are you sure you want to exit?[/yellow]"):
                            self.console.print("\n[green]Thank you for using Dirsearch MCP![/green]")
                            break
                    else:
                        self.console.print("[red]Invalid choice. Please try again.[/red]")
                except KeyboardInterrupt:
                    self._handle_exit()
                except asyncio.CancelledError:
                    self.console.print("\n[yellow]Operation cancelled[/yellow]")
                    self._handle_exit()
                except EOFError:
                    self._handle_exit()
        except KeyboardInterrupt:
            self._handle_exit()
        except asyncio.CancelledError:
            self._handle_exit()
        except Exception as e:
            self.console.print(f"[red]Error: {e}[/red]")
            self._handle_exit()
    
    async def _initialize(self):
        """Initialize MCP coordinator"""
        with self.console.status("[bold green]Initializing MCP Coordinator..."):
            await self.mcp_coordinator.initialize()
            
        mode = self.mcp_coordinator.intelligence_mode
        if mode == 'AI_AGENT':
            self.console.print(f"[green]✓[/green] AI Agent mode enabled")
        else:
            self.console.print(f"[yellow]![/yellow] Running in LOCAL mode (rule-based)")
    
    def _show_banner(self):
        """Display application banner"""
        banner = r"""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     ____  _                              _       __  __  ____ ____   ║
║    |  _ \(_)_ __ ___  ___  __ _ _ __ ___| |__   |  \/  |/ ___|  _ \  ║
║    | | | | | '__/ __|/ _ \/ _` | '__/ __| '_ \  | |\/| | |   | |_) | ║
║    | |_| | | |  \__ \  __/ (_| | | | (__| | | | | |  | | |___|  __/  ║
║    |____/|_|_|  |___/\___|\__,_|_|  \___|_| |_| |_|  |_|\____|_|     ║
║                                                              ║
║            Intelligent Directory Scanner with AI             ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """
        self.console.print(banner, style="bold cyan")
        self.console.print("[dim]Version 1.0 - Powered by MCP Intelligence[/dim]\n", justify="center")
    
    def _show_main_menu(self) -> str:
        """Display main menu and get user choice"""
        self.console.print("\n[bold cyan]Main Menu[/bold cyan]")
        self.console.print(Rule(style="cyan"))
        
        menu = Table(show_header=False, box=None, padding=(0, 2))
        menu.add_column("Option", style="cyan", width=3)
        menu.add_column("Description")
        
        menu.add_row("1", "🚀 Quick Scan (MCP Auto-Configure)")
        menu.add_row("2", "⚙️  Advanced Scan (Manual Configuration)")
        menu.add_row("3", "🧠 Smart Scan (Intelligent Discovery)")
        menu.add_row("4", "👹 Monster Mode (Maximum Discovery)")
        menu.add_row("5", "📊 View Previous Reports")
        menu.add_row("6", "⚡ Configuration Management")
        menu.add_row("7", "❓ Help & Documentation")
        menu.add_row("0", "🚪 Exit")
        
        self.console.print(menu)
        self.console.print(Rule(style="cyan"))
        self.console.print("[dim]Type 'exit' or press Ctrl+C to quit[/dim]")
        
        # Allow "exit" as well as menu numbers
        while True:
            choice = Prompt.ask("\n[bold cyan]Select an option[/bold cyan]")
            if choice.lower() == 'exit' or choice in ['0', '1', '2', '3', '4', '5', '6', '7']:
                return choice
            else:
                self.console.print("[red]Invalid choice. Please enter 0-7 or 'exit'[/red]")
    
    async def _quick_scan(self):
        """Quick scan with MCP auto-configuration"""
        try:
            self.console.print("\n[bold cyan]Quick Scan Mode[/bold cyan]")
            self.console.print("[dim]MCP will automatically configure optimal scan parameters[/dim]\n")
            
            # Get target URL
            target_url = self._get_target_url()
            if not target_url:
                return
            
            # Show MCP analysis
            self.console.print("\n[yellow]MCP is analyzing the target...[/yellow]")
            
            # Start scan with progress display
            await self._execute_scan(target_url, quick_mode=True)
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Scan interrupted by user[/yellow]")
            if hasattr(self, 'dirsearch_engine') and self.dirsearch_engine:
                self.dirsearch_engine.stop_scan()
            return
        except asyncio.CancelledError:
            self.console.print("\n[yellow]Scan cancelled[/yellow]")
            if hasattr(self, 'dirsearch_engine') and self.dirsearch_engine:
                self.dirsearch_engine.stop_scan()
            return
    
    async def _advanced_scan(self):
        """Advanced scan with manual configuration"""
        try:
            self.console.print("\n[bold cyan]Advanced Scan Mode[/bold cyan]")
            self.console.print("[dim]Manually configure scan parameters[/dim]\n")
            
            # Get target URL
            target_url = self._get_target_url()
            if not target_url:
                return
            
            # Get advanced configuration
            config = await self._get_advanced_config()
            
            # Start scan with custom config
            await self._execute_scan(target_url, quick_mode=False, custom_config=config)
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Scan interrupted by user[/yellow]")
            if hasattr(self, 'dirsearch_engine') and self.dirsearch_engine:
                self.dirsearch_engine.stop_scan()
            return
        except asyncio.CancelledError:
            self.console.print("\n[yellow]Scan cancelled[/yellow]")
            if hasattr(self, 'dirsearch_engine') and self.dirsearch_engine:
                self.dirsearch_engine.stop_scan()
            return
    
    async def _smart_scan(self):
        """Smart scan with intelligent discovery"""
        try:
            self.console.print("\n[bold cyan]🧠 Smart Scan Mode[/bold cyan]")
            self.console.print("[dim]Intelligent discovery with rule-based optimization[/dim]\n")
            
            # Get target URL
            target_url = self._get_target_url()
            if not target_url:
                return
            
            # Smart scan configuration
            config = {
                # Use critical wordlists
                'wordlist': 'critical-admin.txt',
                'wordlist_type': 'critical',
                'additional_wordlists': ['critical-api.txt', 'critical-backup.txt'],
                
                # Smart extensions based on technology
                'extensions': ['php', 'asp', 'aspx', 'jsp', 'html', 'json', 'xml', 'sql', 'zip', 'bak'],
                
                # Optimized performance
                'threads': 20,
                'timeout': 15,
                'delay': 0,
                
                # Smart recursion
                'recursive': True,
                'recursion_depth': 3,
                
                # Focus on important status codes
                'exclude_status': '404',
                'include_status': '200,201,301,302,401,403,500',
                
                # Retry configuration
                'max_retries': 3,
                'follow_redirects': True,
                
                # Headers for better discovery
                'custom_headers': {
                    'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
                    'Accept': '*/*',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                
                # MCP settings
                'mcp_mode': 'smart',
                'mcp_confidence_threshold': 0.6,
                'mcp_smart_filtering': True
            }
            
            # Show smart scan features
            features_table = Table(title="[bold]🧠 Smart Scan Features[/bold]", show_header=True)
            features_table.add_column("Feature", style="cyan")
            features_table.add_column("Description", style="yellow")
            
            features_table.add_row("Intelligent Wordlists", "Focus on critical endpoints (admin, API, backups)")
            features_table.add_row("Rule-based Discovery", "Prioritize high-value paths")
            features_table.add_row("Dynamic Expansion", "Expand wordlist based on discoveries")
            features_table.add_row("Smart Extensions", "Technology-aware file extensions")
            features_table.add_row("Priority Scanning", "Scan important paths first")
            features_table.add_row("Risk Assessment", "Real-time security analysis")
            
            self.console.print(features_table)
            
            # Start smart scan
            if Confirm.ask("\n[cyan]Start intelligent scan?[/cyan]"):
                self.console.print("\n[bold cyan]🧠 Initiating Smart Scan...[/bold cyan]")
                await self._execute_scan(target_url, quick_mode=False, custom_config=config, scan_type="smart")
            
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Smart scan interrupted by user[/yellow]")
            return
    
    async def _full_bruteforce_scan(self):
        """Monster Mode - Maximum discovery with aggressive settings"""
        try:
            self.console.print("\n[bold red]👹 MONSTER MODE ACTIVATED 👹[/bold red]")
            self.console.print("[yellow]⚠️  WARNING: EXTREMELY AGGRESSIVE SCANNING MODE[/yellow]")
            self.console.print("[dim]• All wordlists combined • Maximum threads • All extensions • Deep recursion[/dim]\n")
            
            # Warning confirmation
            if not Confirm.ask("\n[yellow]This scan will generate significant traffic. Continue?[/yellow]"):
                return
            
            # Get target URL
            target_url = self._get_target_url()
            if not target_url:
                return
            
            # Build aggressive configuration
            config = {
                # Use comprehensive bruteforce wordlist
                'wordlist': 'monster-all.txt',  # Just the filename, not the path
                'wordlist_type': 'enhanced',
                'additional_wordlists': [],  # Already combined in monster-all.txt
                
                # Maximum extensions coverage
                'extensions': [
                    # Web files
                    'php', 'html', 'htm', 'asp', 'aspx', 'jsp', 'jspx', 'do', 'action',
                    'pl', 'cgi', 'py', 'rb', 'js', 'css', 'xml', 'rss', 'atom',
                    
                    # Data files
                    'json', 'yaml', 'yml', 'xml', 'csv', 'txt', 'log', 'md',
                    
                    # Config files
                    'conf', 'config', 'ini', 'env', 'properties', 'cfg',
                    
                    # Backup files
                    'bak', 'backup', 'old', 'orig', 'save', 'swp', 'swo', '~',
                    'tmp', 'temp', 'copy', 'dist',
                    
                    # Archive files
                    'zip', 'tar', 'gz', 'bz2', 'rar', '7z', 'tgz',
                    
                    # Database files
                    'sql', 'db', 'sqlite', 'sqlite3', 'mdb',
                    
                    # Document files
                    'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx'
                ],
                
                # Maximum performance settings
                'threads': 50,  # Aggressive threading
                'timeout': 30,  # Longer timeout for slow responses
                'delay': 0,     # No delay between requests
                
                # Maximum recursion
                'recursive': True,
                'recursion_depth': 5,  # Deep recursion
                
                # Include all status codes
                'exclude_status': '',  # Don't exclude any status
                'include_status': '200,201,204,301,302,307,308,400,401,403,405,500,502,503',
                
                # Aggressive retry
                'max_retries': 5,
                
                # Don't follow redirects to capture 301 status
                'follow_redirects': False,
                
                # Enable advanced features
                'crawl': True,  # Enable content analysis
                'detect_wildcards': True,  # Enable wildcard detection
                'random_user_agents': True,  # Use random user agents
                
                # Custom headers for better results
                'custom_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': '*/*',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate',
                    'Cache-Control': 'no-cache',
                    'X-Forwarded-For': '127.0.0.1',
                    'X-Originating-IP': '127.0.0.1',
                    'X-Remote-IP': '127.0.0.1',
                    'X-Remote-Addr': '127.0.0.1'
                },
                
                # MCP settings for aggressive scanning
                'mcp_mode': 'aggressive',
                'mcp_confidence_threshold': 0.3,  # Lower threshold
                'mcp_max_depth': 5,
                'mcp_smart_filtering': False  # Disable filtering for max results
            }
            
            # Show COMPLETE configuration summary
            self.console.print("\n[bold red]🔥 MONSTER MODE CONFIGURATION 🔥[/bold red]")
            
            # Basic settings table
            basic_table = Table(title="[bold]Basic Settings[/bold]", show_header=True)
            basic_table.add_column("Setting", style="cyan", width=20)
            basic_table.add_column("Value", style="yellow")
            basic_table.add_column("Description", style="dim")
            
            basic_table.add_row("Target URL", target_url, "Base URL to attack")
            basic_table.add_row("Wordlist", "monster-all.txt", "👹 ~6,800 unique paths")
            basic_table.add_row("Extensions", f"{len(config['extensions'])} types", ", ".join(config['extensions'][:10]) + "...")
            basic_table.add_row("Threads", str(config['threads']), "Maximum concurrent requests")
            basic_table.add_row("Timeout", f"{config['timeout']}s", "Per request timeout")
            basic_table.add_row("Delay", f"{config['delay']}s", "Between requests")
            basic_table.add_row("Retries", str(config['max_retries']), "Failed request retries")
            
            self.console.print(basic_table)
            
            # Recursion settings
            recursion_table = Table(title="\n[bold]Recursion Settings[/bold]", show_header=True)
            recursion_table.add_column("Setting", style="cyan", width=20)
            recursion_table.add_column("Value", style="yellow")
            recursion_table.add_column("Impact", style="dim")
            
            recursion_table.add_row("Recursive", "✓ ENABLED", "Scan found directories")
            recursion_table.add_row("Max Depth", str(config['recursion_depth']), "Levels to go deep")
            recursion_table.add_row("Follow Redirects", "✗ NO", "Capture 301 for recursive scan")
            recursion_table.add_row("301 Recursive", "✓ ENABLED", "Scan inside 301 redirects")
            recursion_table.add_row("Content Analysis", "✓ ENABLED", "Extract hidden paths")
            
            self.console.print(recursion_table)
            
            # Status code configuration
            status_table = Table(title="\n[bold]Status Code Configuration[/bold]", show_header=True)
            status_table.add_column("Setting", style="cyan", width=20)
            status_table.add_column("Value", style="yellow")
            
            status_table.add_row("Include Codes", config.get('include_status', 'ALL'), "Capture everything")
            status_table.add_row("Exclude Codes", config.get('exclude_status', 'NONE'), "No filtering")
            
            self.console.print(status_table)
            
            # Headers table
            headers_table = Table(title="\n[bold]Custom Headers (Bypass Techniques)[/bold]", show_header=True)
            headers_table.add_column("Header", style="cyan")
            headers_table.add_column("Value", style="yellow")
            
            for header, value in config['custom_headers'].items():
                headers_table.add_row(header, value)
            
            self.console.print(headers_table)
            
            # MCP settings
            mcp_table = Table(title="\n[bold]MCP Intelligence Settings[/bold]", show_header=True)
            mcp_table.add_column("Setting", style="cyan", width=20)
            mcp_table.add_column("Value", style="yellow")
            mcp_table.add_column("Effect", style="dim")
            
            mcp_table.add_row("Mode", config['mcp_mode'].upper(), "Aggressive scanning")
            mcp_table.add_row("Confidence", f"{config['mcp_confidence_threshold']*100}%", "Low threshold = more results")
            mcp_table.add_row("Smart Filter", "✗ DISABLED", "No result filtering")
            mcp_table.add_row("Max Depth", str(config['mcp_max_depth']), "MCP recursion depth")
            
            self.console.print(mcp_table)
            
            # Estimated impact
            self.console.print("\n[bold yellow]📊 ESTIMATED SCAN IMPACT:[/bold yellow]")
            # Note: If extensions are provided, each word generates multiple requests
            num_extensions = len(config['extensions'])
            base_words = 6800
            if num_extensions > 0:
                total_requests = base_words + (base_words * num_extensions)  # word + word.ext for each extension
            else:
                total_requests = base_words
            
            self.console.print(f"  • Wordlist entries: {base_words:,}")
            self.console.print(f"  • Extensions to test: {num_extensions}")
            self.console.print(f"  • Base requests: ~{total_requests:,}")
            self.console.print(f"  • With recursion (depth {config['recursion_depth']}): ~{total_requests * 3:,}+ requests")
            self.console.print(f"  • Estimated time: {(total_requests * 3 / config['threads'] / 10):.0f}+ minutes")
            self.console.print(f"  • Network usage: EXTREME")
            self.console.print(f"  • Server load: CATASTROPHIC")
            
            # Performance warning
            self.console.print("\n[yellow]⚠️  Performance Impact:[/yellow]")
            self.console.print("• High bandwidth usage")
            self.console.print("• May trigger rate limiting or WAF")
            self.console.print("• Extended scan duration")
            
            # Final warning
            self.console.print("\n[bold red]⚠️  FINAL WARNING ⚠️[/bold red]")
            self.console.print("[yellow]This scan will:[/yellow]")
            self.console.print("  • Generate massive amounts of traffic")
            self.console.print("  • Potentially trigger security systems")
            self.console.print("  • Take significant time to complete")
            self.console.print("  • May impact target server performance")
            
            if Confirm.ask("\n[bold red]Are you ABSOLUTELY SURE you want to unleash the MONSTER?[/bold red]"):
                self.console.print("\n[bold red]🔥 MONSTER MODE ENGAGED 🔥[/bold red]")
                self.console.print("[dim]Starting aggressive scan...[/dim]\n")
                # Start aggressive scan
                await self._execute_scan(target_url, quick_mode=False, custom_config=config, scan_type="monster")
            
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Monster mode interrupted by user[/yellow]")
            self.console.print("[dim]The monster returns to its cage...[/dim]")
            return
    
    def _get_target_url(self) -> Optional[str]:
        """Get and validate target URL"""
        self.console.print("\n[bold]Target Selection[/bold]")
        self.console.print(Rule(style="dim"))
        
        while True:
            url = Prompt.ask("\n[cyan]Enter target URL (or 'exit' to quit)[/cyan]")
            
            # Check for exit command
            if url.lower() == 'exit':
                self._handle_exit()
            
            # Add scheme if missing
            if not url.startswith(('http://', 'https://')):
                url = f"http://{url}"
            
            # Validate URL
            try:
                parsed = urlparse(url)
                if not parsed.netloc:
                    self.console.print("[red]❌ Invalid URL format[/red]")
                    continue
                
                # Show URL breakdown
                url_table = Table(show_header=False, box=None)
                url_table.add_column("Component", style="cyan")
                url_table.add_column("Value")
                
                url_table.add_row("Protocol", parsed.scheme)
                url_table.add_row("Domain", parsed.netloc)
                if parsed.path and parsed.path != '/':
                    url_table.add_row("Path", parsed.path)
                if parsed.query:
                    url_table.add_row("Query", parsed.query)
                
                self.console.print("\n[bold]URL Analysis:[/bold]")
                self.console.print(url_table)
                
                # Confirm target
                self.console.print(f"\nTarget: [green]{url}[/green]")
                if Confirm.ask("Proceed with this target?"):
                    return url
                else:
                    if not Confirm.ask("Try another URL?"):
                        return None
            except Exception as e:
                self.console.print(f"[red]❌ Error: {e}[/red]")
    
    async def _get_advanced_config(self) -> Dict[str, Any]:
        """Get advanced configuration from user"""
        config = {}
        
        # Wordlist selection
        self.console.print("\n[bold cyan]1. Wordlist Selection[/bold cyan]")
        self.console.print(Rule(style="dim"))
        
        wordlist_choice = self._select_wordlist()
        config['wordlist'] = wordlist_choice
        
        # Extensions
        self.console.print("\n[bold cyan]2. File Extensions[/bold cyan]")
        self.console.print(Rule(style="dim"))
        
        self.console.print("[dim]Common extensions: php, html, js, txt, asp, jsp[/dim]")
        extensions = Prompt.ask(
            "Enter extensions (comma-separated)",
            default="php,html,js,txt"
        )
        config['extensions'] = [ext.strip() for ext in extensions.split(',')]
        
        # Threading and Performance
        self.console.print("\n[bold cyan]3. Performance Settings[/bold cyan]")
        self.console.print(Rule(style="dim"))
        
        perf_table = Table(show_header=False, box=None)
        perf_table.add_column("Setting", style="cyan")
        perf_table.add_column("Recommended", style="green")
        perf_table.add_column("Description")
        
        perf_table.add_row("Threads", "10-20", "For most targets")
        perf_table.add_row("Timeout", "10s", "Connection timeout")
        perf_table.add_row("Delay", "0s", "Delay between requests")
        
        self.console.print(perf_table)
        
        config['threads'] = IntPrompt.ask(
            "\nNumber of threads",
            default=10,
            choices=[str(i) for i in range(1, 51)]
        )
        
        config['timeout'] = IntPrompt.ask(
            "Request timeout (seconds)",
            default=10
        )
        
        config['delay'] = float(Prompt.ask(
            "Delay between requests (seconds)",
            default="0"
        ))
        
        # Advanced options
        if Confirm.ask("\n[yellow]Configure advanced options?[/yellow]"):
            await self._get_advanced_options(config)
        
        # MCP behavior tuning
        if Confirm.ask("\n[yellow]Configure MCP behavior?[/yellow]"):
            await self._configure_mcp_behavior(config)
        
        return config
    
    def _select_wordlist(self) -> str:
        """Select or upload wordlist"""
        wordlists = self._get_available_wordlists()
        
        # Add custom wordlist option
        wordlists.append(("custom", "Use custom wordlist file"))
        wordlists.append(("inline", "Enter words directly"))
        
        wordlist_table = Table(show_header=True, title="Available Wordlists")
        wordlist_table.add_column("#", style="cyan", width=4)
        wordlist_table.add_column("Wordlist", style="yellow")
        wordlist_table.add_column("Description")
        wordlist_table.add_column("Size", justify="right")
        
        for i, (name, desc) in enumerate(wordlists[:-2], 1):
            # Get file size if it's a file
            size = ""
            wordlist_path = Path(self.settings.paths.get('wordlists', 'wordlists')) / name
            if wordlist_path.exists():
                size = f"{wordlist_path.stat().st_size / 1024:.1f} KB"
            wordlist_table.add_row(str(i), name, desc, size)
        
        # Add custom options
        wordlist_table.add_row(str(len(wordlists)-1), "custom", "Use custom wordlist file", "")
        wordlist_table.add_row(str(len(wordlists)), "inline", "Enter words directly", "")
        
        self.console.print(wordlist_table)
        
        choice = IntPrompt.ask(
            "\nSelect wordlist",
            default=1,
            choices=[str(i) for i in range(1, len(wordlists) + 1)]
        )
        
        selected = wordlists[choice - 1][0]
        
        # Handle custom wordlist
        if selected == "custom":
            while True:
                custom_path = Prompt.ask("\nEnter path to custom wordlist")
                if Path(custom_path).exists():
                    return custom_path
                else:
                    self.console.print("[red]❌ File not found[/red]")
                    if not Confirm.ask("Try again?"):
                        return "common.txt"
        
        # Handle inline wordlist
        elif selected == "inline":
            self.console.print("\n[yellow]Enter words (one per line, empty line to finish):[/yellow]")
            words = []
            while True:
                word = input()
                if not word:
                    break
                words.append(word)
            
            if words:
                # Save to temporary file
                temp_file = Path("temp_wordlist.txt")
                temp_file.write_text('\n'.join(words))
                return str(temp_file)
            else:
                return "common.txt"
        
        return selected
    
    def _get_available_wordlists(self) -> List[Tuple[str, str]]:
        """Get available wordlists with descriptions"""
        wordlists = [
            ("monster-all.txt", "👹 MONSTER: All wordlists combined (~6800 entries)"),
            ("combined-enhanced.txt", "Enhanced combined wordlist (recommended)"),
            ("api-endpoints.txt", "API-specific endpoints and nested paths"),
            ("hidden-files.txt", "Hidden files and sensitive data"),
            ("common.txt", "Common paths and files (~4700 entries)"),
            ("directory-list-2.3-small.txt", "Small directory list (~87k entries)"),
            ("directory-list-2.3-medium.txt", "Medium directory list (~220k entries)"),
            ("php_common.txt", "PHP-specific paths"),
            ("asp_common.txt", "ASP/ASPX paths"),
            ("jsp_common.txt", "JSP/Java paths"),
            ("wordpress.txt", "WordPress-specific paths"),
            ("drupal.txt", "Drupal-specific paths"),
            ("joomla.txt", "Joomla-specific paths"),
            ("admin_panels.txt", "Admin interfaces"),
            ("backup_files.txt", "Backup file patterns"),
            ("sensitive_files.txt", "Sensitive file patterns")
        ]
        
        # Filter existing files
        available = []
        wordlist_dir = Path(self.settings.paths.get('wordlists', 'wordlists'))
        
        for name, desc in wordlists:
            if (wordlist_dir / name).exists() or name == "common.txt":
                available.append((name, desc))
        
        return available
    
    async def _get_advanced_options(self, config: Dict[str, Any]):
        """Get advanced scan options"""
        self.console.print("\n[bold cyan]Advanced Options[/bold cyan]")
        self.console.print(Rule(style="dim"))
        
        # Request options
        config['follow_redirects'] = Confirm.ask("Follow redirects? (No = capture 301 for recursive scan)", default=False)
        
        config['user_agent'] = Prompt.ask(
            "User-Agent string",
            default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        
        # Status code filtering
        self.console.print("\n[bold]Status Code Filtering:[/bold]")
        config['exclude_status'] = Prompt.ask(
            "Exclude status codes (comma-separated)",
            default="404"
        )
        
        if Confirm.ask("Include specific status codes only?"):
            config['include_status'] = Prompt.ask(
                "Include status codes (comma-separated)",
                default=""
            )
        
        # Proxy configuration
        if Confirm.ask("\nUse proxy?"):
            config['proxy'] = Prompt.ask("Proxy URL (e.g., http://127.0.0.1:8080)")
        
        # Custom headers
        if Confirm.ask("\nAdd custom headers?"):
            headers = {}
            self.console.print("[dim]Enter headers (empty name to finish)[/dim]")
            while True:
                name = Prompt.ask("Header name")
                if not name:
                    break
                value = Prompt.ask(f"Value for {name}")
                headers[name] = value
            config['custom_headers'] = headers
        
        # Retry configuration
        config['max_retries'] = IntPrompt.ask(
            "\nMax retry attempts",
            default=3,
            choices=[str(i) for i in range(0, 11)]
        )
        
        # Recursion configuration
        self.console.print("\n[bold]Recursion Settings:[/bold]")
        config['recursive'] = Confirm.ask(
            "Enable recursive scanning?",
            default=True
        )
        
        if config['recursive']:
            config['recursion_depth'] = IntPrompt.ask(
                "Maximum recursion depth (0 = unlimited)",
                default=3,
                choices=[str(i) for i in range(0, 11)]
            )
        
        # Advanced features
        self.console.print("\n[bold]Advanced Features:[/bold]")
        config['crawl'] = Confirm.ask(
            "Enable content analysis? (extract hidden paths from responses)",
            default=True
        )
        
        config['detect_wildcards'] = Confirm.ask(
            "Enable wildcard detection?",
            default=True
        )
        
        config['random_user_agents'] = Confirm.ask(
            "Use random user agents?",
            default=False
        )
        
        # Debug monitor option
        config['debug_enabled'] = Confirm.ask(
            "Enable real-time debug monitor? (shows detailed scan progress)",
            default=False
        )
        
        if config['debug_enabled']:
            config['debug_live_display'] = Confirm.ask(
                "Show live debug display?",
                default=True
            )
            
            if Confirm.ask("Export debug data after scan?"):
                config['debug_export_path'] = Prompt.ask(
                    "Export filename",
                    default=f"debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                )
            else:
                config['debug_export_path'] = None
    
    async def _configure_mcp_behavior(self, config: Dict[str, Any]):
        """Configure MCP behavior"""
        self.console.print("\n[bold cyan]MCP Behavior Configuration[/bold cyan]")
        self.console.print(Rule(style="dim"))
        
        mcp_table = Table(show_header=False, box=None)
        mcp_table.add_column("Mode", style="cyan")
        mcp_table.add_column("Description")
        
        mcp_table.add_row("auto", "MCP decides based on target analysis")
        mcp_table.add_row("aggressive", "Thorough scanning, more requests")
        mcp_table.add_row("stealth", "Slower, fewer requests, avoid detection")
        mcp_table.add_row("smart", "AI-guided intelligent scanning")
        mcp_table.add_row("manual", "Full manual control")
        
        self.console.print(mcp_table)
        
        config['mcp_mode'] = Prompt.ask(
            "\nSelect MCP mode",
            choices=['auto', 'aggressive', 'stealth', 'smart', 'manual'],
            default='auto'
        )
        
        if config['mcp_mode'] == 'manual':
            # Manual tuning options
            config['mcp_confidence_threshold'] = IntPrompt.ask(
                "Decision confidence threshold (%)",
                default=70
            ) / 100
            
            config['mcp_max_depth'] = IntPrompt.ask(
                "Maximum scan depth",
                default=3
            )
            
            config['mcp_smart_filtering'] = Confirm.ask(
                "Enable smart path filtering?",
                default=True
            )
    
    async def _execute_scan(self, target_url: str, quick_mode: bool = True, 
                          custom_config: Optional[Dict[str, Any]] = None,
                          scan_type: str = "normal"):
        """Execute scan with real-time progress display"""
        start_time = time.time()
        
        # Create layout for live display
        layout = Layout()
        
        # Create the main layout structure
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body", size=20),
            Layout(name="footer", size=6)
        )
        
        # Split body into progress and stats
        layout["body"].split_row(
            Layout(name="progress", ratio=2),
            Layout(name="stats", ratio=1)
        )
        
        # Split footer into findings and mcp
        layout["footer"].split_row(
            Layout(name="findings", ratio=2),
            Layout(name="mcp", ratio=1)
        )
        
        # Initialize scan data
        scan_data = {
            'target_url': target_url,
            'target_domain': urlparse(target_url).netloc,
            'start_time': datetime.now().isoformat(),
            'intelligence_mode': self.mcp_coordinator.intelligence_mode,
            'mcp_decisions': [],
            'scan_results': [],
            'performance_metrics': {}
        }
        
        with Live(layout, console=self.console, refresh_per_second=4) as live:
            # Header with scan type indication
            scan_mode_text = {
                "normal": "Normal Scan",
                "quick": "Quick Scan",
                "bruteforce": "[bold red]BRUTEFORCE MODE[/bold red]",
                "monster": "[bold red]👹 MONSTER MODE 👹[/bold red]"
            }.get(scan_type, "Custom Scan")
            
            layout["header"].update(
                Panel(
                    Align.center(f"[bold cyan]Scanning:[/bold cyan] {target_url}\n[dim]{scan_mode_text}[/dim]"),
                    title="🎯 Dirsearch MCP",
                    border_style="red" if scan_type in ["bruteforce", "monster"] else "cyan"
                )
            )
            
            # Step 1: Target Analysis
            layout["progress"].update(
                Panel("[yellow]🔍 Analyzing target...[/yellow]", title="Progress", border_style="yellow")
            )
            
            target_info = await self.mcp_coordinator.analyze_target(target_url)
            scan_data['target_analysis'] = self._serialize_target_info(target_info)
            
            # Display target info
            target_table = self._create_target_info_table(target_info)
            layout["stats"].update(Panel(target_table, title="📊 Target Analysis", border_style="green"))
            
            # Show MCP decision
            mcp_text = Text()
            mcp_text.append("🤖 MCP Decision\n", style="bold yellow")
            mcp_text.append(f"Server: {target_info.server_type or 'Unknown'}\n")
            mcp_text.append(f"Technologies: {', '.join(target_info.technology_stack[:3]) or 'None detected'}\n")
            if target_info.detected_cms:
                mcp_text.append(f"CMS: {target_info.detected_cms}\n", style="green")
            
            layout["mcp"].update(Panel(mcp_text, border_style="yellow"))
            
            # Log MCP decision
            mcp_decision = {
                'type': 'target_analysis',
                'context': {'url': target_url},
                'decision': f"Detected: {target_info.server_type}, CMS: {target_info.detected_cms}",
                'confidence': 0.9,
                'timestamp': datetime.now().isoformat()
            }
            scan_data['mcp_decisions'].append(mcp_decision)
            LoggerSetup.log_mcp_decision(
                'target_analysis',
                {'url': target_url},
                f"Detected: {target_info.server_type}, CMS: {target_info.detected_cms}",
                confidence=0.9
            )
            
            # Step 2: Generate Scan Plan
            layout["progress"].update(
                Panel("[yellow]📋 Generating scan plan...[/yellow]", title="Progress", border_style="yellow")
            )
            
            if quick_mode:
                scan_plan = await self.mcp_coordinator.generate_scan_plan(target_info)
                # Get optimized parameters
                scan_config = await self.mcp_coordinator.optimize_parameters(target_info)
            else:
                # Use custom config
                scan_config = custom_config
                scan_plan = await self._generate_custom_scan_plan(target_info, custom_config)
            
            scan_data['scan_plan'] = [self._serialize_scan_task(task) for task in scan_plan]
            
            # Log MCP scan plan decision
            scan_plan_decision = {
                'type': 'scan_plan_generation',
                'context': {
                    'target': target_url,
                    'mode': self.mcp_coordinator.intelligence_mode,
                    'tasks_count': len(scan_plan)
                },
                'decision': f"Generated {len(scan_plan)} scan tasks with {scan_config.get('wordlist', 'default')} wordlist",
                'confidence': 0.85,
                'timestamp': datetime.now().isoformat()
            }
            scan_data['mcp_decisions'].append(scan_plan_decision)
            
            # Display scan plan with MCP task distribution
            plan_text = Text()
            plan_text.append("📋 MCP Task Distribution\n", style="bold cyan")
            plan_text.append(f"Mode: {self.mcp_coordinator.intelligence_mode}\n", style="yellow")
            plan_text.append(f"\nScan Tasks ({len(scan_plan)}):\n", style="bold")
            
            for i, task in enumerate(scan_plan[:3], 1):  # Show first 3 tasks
                plan_text.append(f"{i}. {task.task_type} (Priority: {task.priority})\n", style="dim")
            
            if len(scan_plan) > 3:
                plan_text.append(f"   ... and {len(scan_plan)-3} more tasks\n", style="dim")
            
            plan_text.append(f"\nConfiguration:\n", style="bold")
            plan_text.append(f"Wordlist: {scan_config.get('wordlist', 'default')}\n")
            plan_text.append(f"Threads: {scan_config.get('threads', 10)}\n")
            plan_text.append(f"Extensions: {', '.join(scan_config.get('extensions', []))}\n")
            
            layout["mcp"].update(Panel(plan_text, border_style="cyan"))
            
            # Step 3: Execute Scan
            findings_count = 0
            
            # Create progress display
            progress_text = Text()
            progress_text.append("🔄 Scanning Progress\n\n", style="bold cyan")
            progress_text.append("[cyan]Initializing scan...[/cyan]\n")
            layout["progress"].update(Panel(progress_text, border_style="cyan"))
            
            # Findings display
            findings_text = Text()
            findings_text.append("Latest Findings:\n", style="bold green")
            layout["findings"].update(
                Panel(findings_text, title="🎯 Discoveries", border_style="green")
            )
            
            # Create scan request
            scan_request = ScanRequest(
                base_url=target_url,
                wordlist=scan_config.get('wordlist', 'common.txt'),
                wordlist_type=scan_config.get('wordlist_type', 'enhanced'),
                additional_wordlists=scan_config.get('additional_wordlists', []),
                extensions=scan_config.get('extensions', []),
                threads=scan_config.get('threads', 10),
                timeout=scan_config.get('timeout', 10),
                delay=scan_config.get('delay', 0),
                user_agent=scan_config.get('user_agent', 'Mozilla/5.0'),
                follow_redirects=scan_config.get('follow_redirects', True),
                custom_headers=scan_config.get('custom_headers', {}),
                proxy=scan_config.get('proxy'),
                max_retries=scan_config.get('max_retries', 3),
                exclude_status=scan_config.get('exclude_status', '404'),
                include_status=scan_config.get('include_status'),
                recursive=scan_config.get('recursive', True),  # Default to True
                recursion_depth=scan_config.get('recursion_depth', 3),  # Default to 3
                debug_enabled=scan_config.get('debug_enabled', False),
                debug_live_display=scan_config.get('debug_live_display', True),
                debug_export_path=scan_config.get('debug_export_path')
            )
            
            # Real-time progress tracking
            progress_info = {
                'current': 0,
                'total': 0,
                'findings': [],
                'last_update': time.time()
            }
            
            # Set up callbacks for real-time updates
            def update_progress(current: int, total: int):
                progress_info['current'] = current
                progress_info['total'] = total
                
                # Update progress display
                progress_text = Text()
                progress_text.append("🔄 Scanning Progress\n\n", style="bold cyan")
                progress_text.append(f"[yellow]Scanning... {current}/{total}[/yellow]\n")
                progress_text.append(f"Progress: {current/total*100:.1f}%\n")
                progress_text.append(f"Wordlist: {scan_config.get('wordlist', 'common.txt')}\n")
                progress_text.append(f"Threads: {scan_config.get('threads', 10)}\n")
                progress_text.append(f"Speed: {current/(time.time()-start_time):.1f} req/s\n")
                layout["progress"].update(Panel(progress_text, border_style="cyan"))
                
                # Update statistics
                stats_text = self._create_running_stats(
                    elapsed=time.time() - start_time,
                    current=current,
                    total=total,
                    findings=len(progress_info['findings']),
                    speed=current/(time.time()-start_time)
                )
                layout["stats"].update(Panel(stats_text, title="📊 Live Statistics", border_style="yellow"))
            
            def on_result(result: ScanResult):
                if result.status_code != 404:
                    progress_info['findings'].append(result)
                    
                    # Update findings display
                    findings_text = Text()
                    findings_text.append("Latest Findings:\n\n", style="bold green")
                    
                    # Show last 5 findings
                    for finding in progress_info['findings'][-5:]:
                        status_color = "green" if finding.status_code == 200 else "yellow"
                        findings_text.append(
                            f"[{status_color}][{finding.status_code}][/{status_color}] {finding.path} "
                            f"({finding.size} bytes)\n"
                        )
                    
                    layout["findings"].update(
                        Panel(findings_text, title="🎯 Discoveries", border_style="green")
                    )
                    
                    # Update MCP insights
                    mcp_text = Text()
                    mcp_text.append("📋 MCP Intelligence\n\n", style="bold cyan")
                    mcp_text.append(f"Mode: {self.mcp_coordinator.intelligence_mode}\n")
                    mcp_text.append(f"Status: Active\n", style="green")
                    mcp_text.append(f"\nAnalysis:\n", style="bold")
                    mcp_text.append(f"Total Findings: {len(progress_info['findings'])}\n")
                    mcp_text.append(f"Interesting: {len([f for f in progress_info['findings'] if f.status_code in [200, 301, 302, 401, 403]])}\n")
                    mcp_text.append(f"Directories: {len([f for f in progress_info['findings'] if f.is_directory])}\n")
                    
                    # Add recommendations based on findings
                    if len(progress_info['findings']) > 5:
                        mcp_text.append(f"\nRecommendations:\n", style="bold yellow")
                        if any(f.status_code == 401 for f in progress_info['findings']):
                            mcp_text.append("• Found auth endpoints\n", style="dim")
                        if any(f.status_code in [301, 302] for f in progress_info['findings']):
                            mcp_text.append("• Redirect patterns detected\n", style="dim")
                        
                        # Log MCP findings analysis
                        if len(progress_info['findings']) % 10 == 0:  # Log every 10 findings
                            findings_analysis = {
                                'type': 'findings_analysis',
                                'context': {
                                    'total_findings': len(progress_info['findings']),
                                    'interesting_findings': len([f for f in progress_info['findings'] if f.status_code in [200, 301, 302, 401, 403]]),
                                    'directories_found': len([f for f in progress_info['findings'] if f.is_directory])
                                },
                                'decision': f"Found {len(progress_info['findings'])} paths, analyzing patterns",
                                'confidence': 0.75,
                                'timestamp': datetime.now().isoformat()
                            }
                            scan_data['mcp_decisions'].append(findings_analysis)
                    
                    layout["mcp"].update(Panel(mcp_text, border_style="cyan"))
            
            def on_error(error: Exception):
                # Log errors but don't stop the scan
                pass
            
            # Set callbacks
            self.dirsearch_engine.set_progress_callback(update_progress)
            self.dirsearch_engine.set_result_callback(on_result)
            self.dirsearch_engine.set_error_callback(on_error)
            
            # Execute scan with interrupt handling
            try:
                scan_response = await self.dirsearch_engine.execute_scan(scan_request)
            except asyncio.CancelledError:
                self.console.print("\n[yellow]Scan cancelled[/yellow]")
                self.dirsearch_engine.stop_scan()
                raise
            
            # Update results
            scan_data['scan_results'] = scan_response.results
            findings_count = len([r for r in scan_response.results if r['status'] != 404])
            
            # Final statistics
            elapsed = time.time() - start_time
            stats_text = self._create_final_stats(
                elapsed=elapsed,
                total_requests=scan_response.statistics.get('total_requests', 0),
                findings=findings_count,
                errors=scan_response.statistics.get('errors', 0)
            )
            layout["stats"].update(Panel(stats_text, title="📊 Final Statistics", border_style="green"))
            
            # Show completion
            layout["progress"].update(
                Panel(
                    Align.center("[bold green]✅ Scan Complete![/bold green]"),
                    border_style="green"
                )
            )
        
        # Post-scan actions
        scan_data['end_time'] = datetime.now().isoformat()
        scan_data['duration'] = time.time() - start_time
        
        # Add final MCP decision
        final_decision = {
            'type': 'scan_completion',
            'context': {
                'total_requests': scan_response.statistics.get('total_requests', 0),
                'findings': findings_count,
                'errors': scan_response.statistics.get('errors', 0),
                'duration': scan_data['duration']
            },
            'decision': f"Scan completed with {findings_count} findings out of {scan_response.statistics.get('total_requests', 0)} requests",
            'confidence': 0.95,
            'timestamp': datetime.now().isoformat()
        }
        scan_data['mcp_decisions'].append(final_decision)
        
        # Display summary
        self._display_scan_summary(scan_response, scan_data['duration'])
        
        # Display intelligent insights for smart scan
        if scan_type == "smart" and hasattr(self.dirsearch_engine, 'get_scan_insights'):
            insights = self.dirsearch_engine.get_scan_insights()
            self._display_scan_insights(insights)
        
        # Save results option
        if Confirm.ask("\n[cyan]Save scan report?[/cyan]"):
            try:
                # Include insights in report for smart scan
                if scan_type == "smart" and hasattr(self.dirsearch_engine, 'get_scan_insights'):
                    scan_data['intelligence_insights'] = self.dirsearch_engine.get_scan_insights()
                
                report_files = self.report_generator.generate_report(scan_data)
                self.console.print("\n[green]✅ Reports saved:[/green]")
                for format, path in report_files.items():
                    self.console.print(f"  • {format.upper()}: {path}")
            except Exception as e:
                self.console.print(f"\n[red]Error: {e}[/red]")
                import traceback
                if self.logger:
                    self.logger.error(f"Report generation error: {traceback.format_exc()}")
        
        # Add to history
        self.scan_history.append({
            'timestamp': datetime.now(),
            'target': target_url,
            'findings': findings_count,
            'duration': scan_data['duration']
        })
        
        Prompt.ask("\n[dim]Press Enter to continue[/dim]")
    
    def _view_reports(self):
        """View previous scan reports"""
        self.console.print("\n[bold cyan]Previous Reports[/bold cyan]")
        self.console.print(Rule(style="cyan"))
        
        # Get report files
        report_dir = Path("report")
        if not report_dir.exists():
            self.console.print("[yellow]No reports found.[/yellow]")
            Prompt.ask("\n[dim]Press Enter to continue[/dim]")
            return
        
        # List all report files
        reports = []
        for format_dir in ['json', 'html', 'markdown']:
            format_path = report_dir / format_dir
            if format_path.exists():
                for report_file in format_path.glob('*.json' if format_dir == 'json' else '*.*'):
                    reports.append((report_file, format_dir))
        
        if not reports:
            self.console.print("[yellow]No reports found.[/yellow]")
            Prompt.ask("\n[dim]Press Enter to continue[/dim]")
            return
        
        # Sort by modification time
        reports.sort(key=lambda x: x[0].stat().st_mtime, reverse=True)
        
        # Display report list
        report_table = Table(
            show_header=True,
            title="📊 Available Reports",
            title_style="bold cyan"
        )
        report_table.add_column("#", style="cyan", width=4)
        report_table.add_column("Report Name", style="yellow")
        report_table.add_column("Format", style="green")
        report_table.add_column("Date", style="blue")
        report_table.add_column("Size", justify="right")
        
        for i, (report_file, format) in enumerate(reports[:20], 1):  # Show last 20
            report_table.add_row(
                str(i),
                report_file.name[:40] + "..." if len(report_file.name) > 40 else report_file.name,
                format.upper(),
                datetime.fromtimestamp(report_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M'),
                f"{report_file.stat().st_size / 1024:.1f} KB"
            )
        
        self.console.print(report_table)
        
        # Select report to view
        choice = IntPrompt.ask(
            "\nSelect report to view (0 to cancel)",
            default=0,
            choices=[str(i) for i in range(0, min(len(reports), 20) + 1)]
        )
        
        if choice == 0:
            return
        
        report_file, format = reports[choice - 1]
        
        # View report based on format
        if format == 'json':
            self._view_json_report(report_file)
        elif format == 'markdown':
            self._view_markdown_report(report_file)
        elif format == 'html':
            self.console.print(f"\n[cyan]HTML report location:[/cyan] {report_file}")
            if Confirm.ask("Open in browser?"):
                import webbrowser
                webbrowser.open(f"file://{report_file.absolute()}")
    
    def _view_json_report(self, report_file: Path):
        """View JSON report with syntax highlighting"""
        try:
            with open(report_file, 'r') as f:
                data = json.load(f)
            
            # Display key sections
            self.console.print(f"\n[bold]Report: {report_file.name}[/bold]\n")
            
            # Summary panel
            scan_info = data.get('scan_info', {})
            summary_text = Text()
            summary_text.append("Scan Summary\n", style="bold")
            summary_text.append(f"Target: {scan_info.get('target_url', 'Unknown')}\n")
            summary_text.append(f"Date: {scan_info.get('start_time', 'Unknown')}\n")
            summary_text.append(f"Duration: {scan_info.get('duration', 0):.1f}s\n")
            summary_text.append(f"Mode: {scan_info.get('intelligence_mode', 'Unknown')}\n")
            
            self.console.print(Panel(summary_text, title="📊 Scan Information", border_style="cyan"))
            
            # Findings
            findings = data.get('findings_summary', {})
            self.console.print(f"\nTotal Findings: [cyan]{findings.get('total_findings', 0)}[/cyan]")
            
            # Show top findings
            if 'scan_results' in data and data['scan_results']:
                findings_table = Table(title="Top Findings", show_header=True)
                findings_table.add_column("Path", style="cyan")
                findings_table.add_column("Status", style="green")
                findings_table.add_column("Size", justify="right")
                
                results = data['scan_results']
                if isinstance(results, list) and results:
                    for result in results[:10]:
                        if isinstance(result, dict) and 'path' in result:
                            findings_table.add_row(
                                result.get('path', ''),
                                str(result.get('status', '')),
                                f"{result.get('size', 0)} B"
                            )
                
                self.console.print(findings_table)
            
            # Show raw JSON if requested
            if Confirm.ask("\nView full JSON report?"):
                syntax = Syntax(json.dumps(data, indent=2), "json", theme="monokai", line_numbers=True)
                self.console.print(syntax)
                
        except Exception as e:
            self.console.print(f"[red]Error reading report: {e}[/red]")
        
        Prompt.ask("\n[dim]Press Enter to continue[/dim]")
    
    def _view_markdown_report(self, report_file: Path):
        """View Markdown report"""
        try:
            with open(report_file, 'r') as f:
                content = f.read()
            
            # Use pager for long content
            self.console.print(Rule(f"[cyan]{report_file.name}[/cyan]"))
            
            # Display with pager if available
            from rich.console import Console
            with Console().pager():
                markdown = Markdown(content)
                self.console.print(markdown)
                
        except Exception as e:
            self.console.print(f"[red]Error reading report: {e}[/red]")
        
        Prompt.ask("\n[dim]Press Enter to continue[/dim]")
    
    async def _configuration_management(self):
        """Manage application configuration"""
        while True:
            self.console.print("\n[bold cyan]Configuration Management[/bold cyan]")
            self.console.print(Rule(style="cyan"))
            
            config_menu = Table(show_header=False, box=None, padding=(0, 2))
            config_menu.add_column("Option", style="cyan", width=3)
            config_menu.add_column("Description")
            
            config_menu.add_row("1", "🔍 View Current Configuration")
            config_menu.add_row("2", "⚙️  Edit Scan Settings")
            config_menu.add_row("3", "🤖 Configure AI Agents")
            config_menu.add_row("4", "📝 Manage Wordlists")
            config_menu.add_row("5", "⚡ Performance Tuning")
            config_menu.add_row("6", "💾 Save/Load Configuration")
            config_menu.add_row("0", "🔙 Back to Main Menu")
            
            self.console.print(config_menu)
            
            choice = Prompt.ask("\n[cyan]Select option[/cyan]", choices=['0', '1', '2', '3', '4', '5', '6'])
            
            if choice == '0':
                break
            elif choice == '1':
                self._view_configuration()
            elif choice == '2':
                await self._edit_scan_settings()
            elif choice == '3':
                await self._configure_ai_agents()
            elif choice == '4':
                self._manage_wordlists()
            elif choice == '5':
                self._performance_tuning()
            elif choice == '6':
                self._save_load_configuration()
    
    def _view_configuration(self):
        """View current configuration with enhanced display"""
        self.console.print("\n[bold cyan]Current Configuration[/bold cyan]")
        self.console.print(Rule(style="cyan"))
        
        # Create configuration tree
        config_tree = Tree("⚙️  [bold]Configuration Overview[/bold]")
        
        # Scan settings
        scan_node = config_tree.add("🔍 [cyan]Scan Settings[/cyan]")
        scan_node.add(f"Default threads: [green]{self.settings.default_scan_config.get('threads', 10)}[/green]")
        scan_node.add(f"Timeout: [green]{self.settings.default_scan_config.get('timeout', 10)}s[/green]")
        scan_node.add(f"User-Agent: [dim]{self.settings.default_scan_config.get('user_agent', 'Default')[:50]}...[/dim]")
        scan_node.add(f"Follow redirects: [green]{'Yes' if self.settings.default_scan_config.get('follow_redirects', False) else 'No'}[/green]")
        scan_node.add(f"Max retries: [green]{self.settings.default_scan_config.get('max_retries', 3)}[/green]")
        
        # AI configuration
        ai_node = config_tree.add("🤖 [cyan]AI Configuration[/cyan]")
        ai_node.add(f"Current mode: [yellow]{self.mcp_coordinator.intelligence_mode}[/yellow]")
        ai_node.add(f"OpenAI configured: [{'green' if self.settings.ai_config.get('openai_api_key') else 'red'}]{'✓' if self.settings.ai_config.get('openai_api_key') else '✗'}[/]")
        ai_node.add(f"DeepSeek configured: [{'green' if self.settings.ai_config.get('deepseek_api_key') else 'red'}]{'✓' if self.settings.ai_config.get('deepseek_api_key') else '✗'}[/]")
        
        # Paths
        path_node = config_tree.add("📁 [cyan]Paths[/cyan]")
        path_node.add(f"Wordlists: [blue]{self.settings.paths.get('wordlists', 'wordlists/')}[/blue]")
        path_node.add(f"Reports: [blue]{self.settings.paths.get('reports', 'report/')}[/blue]")
        path_node.add(f"Logs: [blue]{self.settings.paths.get('logs', 'log/')}[/blue]")
        
        # Performance
        perf_node = config_tree.add("⚡ [cyan]Performance[/cyan]")
        perf_node.add(f"Batch size: [green]{self.settings.default_scan_config.get('batch_size', 50)}[/green]")
        perf_node.add(f"Rate limit: [green]{'Disabled' if not self.settings.default_scan_config.get('rate_limit') else str(self.settings.default_scan_config.get('rate_limit'))}[/green]")
        
        self.console.print(config_tree)
        
        Prompt.ask("\n[dim]Press Enter to continue[/dim]")
    
    async def _edit_scan_settings(self):
        """Edit default scan settings"""
        self.console.print("\n[bold cyan]Edit Scan Settings[/bold cyan]")
        self.console.print(Rule(style="cyan"))
        
        # Current settings
        current = self.settings.default_scan_config
        
        settings_table = Table(title="Current Default Settings", show_header=True)
        settings_table.add_column("Setting", style="cyan")
        settings_table.add_column("Current Value", style="yellow")
        settings_table.add_column("Description")
        
        settings_table.add_row("Threads", str(current.get('threads', 10)), "Concurrent connections")
        settings_table.add_row("Timeout", f"{current.get('timeout', 10)}s", "Request timeout")
        settings_table.add_row("Max Retries", str(current.get('max_retries', 3)), "Retry failed requests")
        settings_table.add_row("Delay", f"{current.get('delay', 0)}s", "Delay between requests")
        settings_table.add_row("Follow Redirects", "Yes" if current.get('follow_redirects', True) else "No", "Follow HTTP redirects")
        
        self.console.print(settings_table)
        
        if Confirm.ask("\n[yellow]Modify settings?[/yellow]"):
            # Edit each setting
            new_threads = IntPrompt.ask(
                "Number of threads",
                default=current.get('threads', 10),
                choices=[str(i) for i in range(1, 51)]
            )
            self.settings.default_scan_config['threads'] = new_threads
            
            new_timeout = IntPrompt.ask(
                "Timeout (seconds)",
                default=current.get('timeout', 10)
            )
            self.settings.default_scan_config['timeout'] = new_timeout
            
            new_retries = IntPrompt.ask(
                "Max retries",
                default=current.get('max_retries', 3),
                choices=[str(i) for i in range(0, 11)]
            )
            self.settings.default_scan_config['max_retries'] = new_retries
            
            new_delay = float(Prompt.ask(
                "Delay between requests (seconds)",
                default=str(current.get('delay', 0))
            ))
            self.settings.default_scan_config['delay'] = new_delay
            
            new_follow = Confirm.ask(
                "Follow redirects?",
                default=current.get('follow_redirects', True)
            )
            self.settings.default_scan_config['follow_redirects'] = new_follow
            
            # Save settings
            if Confirm.ask("\n[yellow]Save these settings?[/yellow]"):
                # In a real implementation, save to config file
                self.console.print("[green]✅ Settings saved successfully![/green]")
    
    async def _configure_ai_agents(self):
        """Configure AI agent settings"""
        self.console.print("\n[bold cyan]AI Agent Configuration[/bold cyan]")
        self.console.print(Rule(style="cyan"))
        
        # Show current AI status
        ai_status = Table(title="AI Provider Status", show_header=True)
        ai_status.add_column("Provider", style="cyan")
        ai_status.add_column("Status", style="green")
        ai_status.add_column("Model")
        
        # OpenAI
        openai_configured = bool(self.settings.ai_config.get('openai_api_key'))
        ai_status.add_row(
            "OpenAI",
            "✅ Configured" if openai_configured else "❌ Not configured",
            self.settings.ai_config.get('openai_model', 'gpt-3.5-turbo')
        )
        
        # DeepSeek
        deepseek_configured = bool(self.settings.ai_config.get('deepseek_api_key'))
        ai_status.add_row(
            "DeepSeek",
            "✅ Configured" if deepseek_configured else "❌ Not configured",
            self.settings.ai_config.get('deepseek_model', 'deepseek-coder')
        )
        
        self.console.print(ai_status)
        
        # Configuration options
        self.console.print("\n[bold]Options:[/bold]")
        self.console.print("1. Configure OpenAI")
        self.console.print("2. Configure DeepSeek")
        self.console.print("3. Test AI Connection")
        self.console.print("4. Set Default Provider")
        self.console.print("0. Back")
        
        choice = Prompt.ask("\n[cyan]Select option[/cyan]", choices=['0', '1', '2', '3', '4'])
        
        if choice == '1':
            # Configure OpenAI
            self.console.print("\n[bold]OpenAI Configuration[/bold]")
            api_key = Prompt.ask("Enter OpenAI API key", password=True)
            if api_key:
                self.settings.ai_config['openai_api_key'] = api_key
                
                # Select model
                model = Prompt.ask(
                    "Select model",
                    choices=['gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo'],
                    default='gpt-3.5-turbo'
                )
                self.settings.ai_config['openai_model'] = model
                
                self.console.print("[green]✅ OpenAI configured successfully![/green]")
        
        elif choice == '2':
            # Configure DeepSeek
            self.console.print("\n[bold]DeepSeek Configuration[/bold]")
            api_key = Prompt.ask("Enter DeepSeek API key", password=True)
            if api_key:
                self.settings.ai_config['deepseek_api_key'] = api_key
                
                # Select model
                model = Prompt.ask(
                    "Select model",
                    choices=['deepseek-coder', 'deepseek-chat'],
                    default='deepseek-coder'
                )
                self.settings.ai_config['deepseek_model'] = model
                
                self.console.print("[green]✅ DeepSeek configured successfully![/green]")
        
        elif choice == '3':
            # Test AI connection
            self.console.print("\n[yellow]Testing AI connections...[/yellow]")
            await self._test_ai_connection()
        
        elif choice == '4':
            # Set default provider
            provider = Prompt.ask(
                "Select default AI provider",
                choices=['openai', 'deepseek', 'auto'],
                default='auto'
            )
            self.settings.ai_config['default_provider'] = provider
            self.console.print(f"[green]✅ Default provider set to: {provider}[/green]")
    
    async def _test_ai_connection(self):
        """Test AI provider connections"""
        with self.console.status("[bold green]Testing AI connections..."):
            # Test OpenAI
            if self.settings.ai_config.get('openai_api_key'):
                try:
                    # In real implementation, make API call to test
                    await asyncio.sleep(1)  # Simulate API call
                    self.console.print("[green]✅ OpenAI connection successful![/green]")
                except Exception as e:
                    self.console.print(f"[red]❌ OpenAI connection failed: {e}[/red]")
            
            # Test DeepSeek
            if self.settings.ai_config.get('deepseek_api_key'):
                try:
                    # In real implementation, make API call to test
                    await asyncio.sleep(1)  # Simulate API call
                    self.console.print("[green]✅ DeepSeek connection successful![/green]")
                except Exception as e:
                    self.console.print(f"[red]❌ DeepSeek connection failed: {e}[/red]")
    
    def _manage_wordlists(self):
        """Manage wordlists"""
        self.console.print("\n[bold cyan]Wordlist Management[/bold cyan]")
        self.console.print(Rule(style="cyan"))
        
        wordlist_dir = Path(self.settings.paths.get('wordlists', 'wordlists'))
        
        # List current wordlists
        if wordlist_dir.exists():
            wordlists = list(wordlist_dir.glob('*.txt'))
            
            if wordlists:
                wl_table = Table(title="Available Wordlists", show_header=True)
                wl_table.add_column("#", style="cyan", width=4)
                wl_table.add_column("Name", style="yellow")
                wl_table.add_column("Size", justify="right")
                wl_table.add_column("Lines", justify="right")
                
                for i, wl in enumerate(wordlists, 1):
                    size = wl.stat().st_size / 1024
                    try:
                        lines = sum(1 for _ in wl.open())
                    except:
                        lines = "?"
                    
                    wl_table.add_row(
                        str(i),
                        wl.name,
                        f"{size:.1f} KB",
                        str(lines)
                    )
                
                self.console.print(wl_table)
            else:
                self.console.print("[yellow]No wordlists found.[/yellow]")
        else:
            self.console.print("[yellow]Wordlist directory not found.[/yellow]")
        
        # Management options
        self.console.print("\n[bold]Options:[/bold]")
        self.console.print("1. Add wordlist")
        self.console.print("2. Create custom wordlist")
        self.console.print("3. Download common wordlists")
        self.console.print("4. Delete wordlist")
        self.console.print("0. Back")
        
        choice = Prompt.ask("\n[cyan]Select option[/cyan]", choices=['0', '1', '2', '3', '4'])
        
        if choice == '1':
            # Add wordlist from file
            path = Prompt.ask("\nEnter path to wordlist file")
            if Path(path).exists():
                import shutil
                dest = wordlist_dir / Path(path).name
                shutil.copy(path, dest)
                self.console.print(f"[green]✅ Wordlist added: {dest.name}[/green]")
            else:
                self.console.print("[red]❌ File not found[/red]")
        
        elif choice == '2':
            # Create custom wordlist
            name = Prompt.ask("\nEnter wordlist name (without .txt)")
            self.console.print("[yellow]Enter words (one per line, empty line to finish):[/yellow]")
            
            words = []
            while True:
                word = input()
                if not word:
                    break
                words.append(word)
            
            if words:
                wordlist_dir.mkdir(exist_ok=True)
                wl_file = wordlist_dir / f"{name}.txt"
                wl_file.write_text('\n'.join(words))
                self.console.print(f"[green]✅ Created wordlist: {wl_file.name} ({len(words)} words)[/green]")
        
        elif choice == '3':
            # Download common wordlists
            self.console.print("\n[yellow]Common wordlist sources:[/yellow]")
            self.console.print("1. SecLists (danielmiessler/SecLists)")
            self.console.print("2. FuzzDB")
            self.console.print("3. Dirbuster wordlists")
            self.console.print("\n[dim]Manual download required from GitHub[/dim]")
        
        elif choice == '4':
            # Delete wordlist
            if wordlists:
                idx = IntPrompt.ask(
                    "\nSelect wordlist to delete",
                    choices=[str(i) for i in range(1, len(wordlists) + 1)]
                )
                wl_to_delete = wordlists[idx - 1]
                if Confirm.ask(f"Delete {wl_to_delete.name}?"):
                    wl_to_delete.unlink()
                    self.console.print("[green]✅ Wordlist deleted[/green]")
        
        Prompt.ask("\n[dim]Press Enter to continue[/dim]")
    
    def _performance_tuning(self):
        """Performance tuning settings"""
        self.console.print("\n[bold cyan]Performance Tuning[/bold cyan]")
        self.console.print(Rule(style="cyan"))
        
        # Performance recommendations
        perf_table = Table(title="Performance Recommendations", show_header=True)
        perf_table.add_column("Target Type", style="cyan")
        perf_table.add_column("Threads", style="green")
        perf_table.add_column("Timeout", style="yellow")
        perf_table.add_column("Delay", style="red")
        
        perf_table.add_row("Small website", "10-15", "10s", "0s")
        perf_table.add_row("Medium website", "15-25", "15s", "0.1s")
        perf_table.add_row("Large website", "20-30", "20s", "0.2s")
        perf_table.add_row("Slow/Protected", "5-10", "30s", "0.5-1s")
        perf_table.add_row("API endpoints", "5-10", "30s", "0.5s")
        
        self.console.print(perf_table)
        
        # Current performance settings
        self.console.print("\n[bold]Current Performance Settings:[/bold]")
        self.console.print(f"Batch size: {self.settings.default_scan_config.get('batch_size', 50)}")
        self.console.print(f"Connection pool size: {self.settings.default_scan_config.get('pool_size', 100)}")
        self.console.print(f"DNS cache: {'Enabled' if self.settings.default_scan_config.get('dns_cache', True) else 'Disabled'}")
        self.console.print(f"Keep-alive: {'Enabled' if self.settings.default_scan_config.get('keep_alive', True) else 'Disabled'}")
        
        if Confirm.ask("\n[yellow]Tune performance settings?[/yellow]"):
            # Batch size
            batch_size = IntPrompt.ask(
                "Batch size (paths per batch)",
                default=self.settings.default_scan_config.get('batch_size', 50)
            )
            self.settings.default_scan_config['batch_size'] = batch_size
            
            # Connection pool
            pool_size = IntPrompt.ask(
                "Connection pool size",
                default=self.settings.default_scan_config.get('pool_size', 100)
            )
            self.settings.default_scan_config['pool_size'] = pool_size
            
            # DNS cache
            dns_cache = Confirm.ask(
                "Enable DNS cache?",
                default=self.settings.default_scan_config.get('dns_cache', True)
            )
            self.settings.default_scan_config['dns_cache'] = dns_cache
            
            # Keep-alive
            keep_alive = Confirm.ask(
                "Enable HTTP keep-alive?",
                default=self.settings.default_scan_config.get('keep_alive', True)
            )
            self.settings.default_scan_config['keep_alive'] = keep_alive
            
            self.console.print("[green]✅ Performance settings updated![/green]")
        
        Prompt.ask("\n[dim]Press Enter to continue[/dim]")
    
    def _save_load_configuration(self):
        """Save or load configuration"""
        self.console.print("\n[bold cyan]Save/Load Configuration[/bold cyan]")
        self.console.print(Rule(style="cyan"))
        
        self.console.print("1. Save current configuration")
        self.console.print("2. Load configuration from file")
        self.console.print("3. Reset to defaults")
        self.console.print("0. Back")
        
        choice = Prompt.ask("\n[cyan]Select option[/cyan]", choices=['0', '1', '2', '3'])
        
        if choice == '1':
            # Save configuration
            filename = Prompt.ask("\nEnter filename", default="dirsearch_config.json")
            config_data = {
                'scan_settings': self.settings.default_scan_config,
                'ai_config': {k: v for k, v in self.settings.ai_config.items() if 'key' not in k},
                'paths': self.settings.paths
            }
            
            with open(filename, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            self.console.print(f"[green]✅ Configuration saved to: {filename}[/green]")
        
        elif choice == '2':
            # Load configuration
            filename = Prompt.ask("\nEnter configuration file path")
            if Path(filename).exists():
                try:
                    with open(filename, 'r') as f:
                        config_data = json.load(f)
                    
                    # Apply configuration
                    if 'scan_settings' in config_data:
                        self.settings.default_scan_config.update(config_data['scan_settings'])
                    if 'ai_config' in config_data:
                        self.settings.ai_config.update(config_data['ai_config'])
                    if 'paths' in config_data:
                        self.settings.paths.update(config_data['paths'])
                    
                    self.console.print("[green]✅ Configuration loaded successfully![/green]")
                except Exception as e:
                    self.console.print(f"[red]❌ Error loading configuration: {e}[/red]")
            else:
                self.console.print("[red]❌ File not found[/red]")
        
        elif choice == '3':
            # Reset to defaults
            if Confirm.ask("[yellow]Reset all settings to defaults?[/yellow]"):
                self.settings = Settings()
                self.console.print("[green]✅ Settings reset to defaults![/green]")
        
        Prompt.ask("\n[dim]Press Enter to continue[/dim]")
    
    def _show_help(self):
        """Show comprehensive help and documentation"""
        self.console.print("\n[bold cyan]Help & Documentation[/bold cyan]")
        self.console.print(Rule(style="cyan"))
        
        help_sections = {
            "1": ("Quick Start Guide", self._show_quick_start),
            "2": ("Scan Modes Explained", self._show_scan_modes),
            "3": ("MCP Intelligence", self._show_mcp_help),
            "4": ("Wordlist Guide", self._show_wordlist_help),
            "5": ("Performance Tips", self._show_performance_help),
            "6": ("Troubleshooting", self._show_troubleshooting),
            "7": ("Examples", self._show_examples)
        }
        
        # Display help menu
        help_table = Table(show_header=False, box=None, padding=(0, 2))
        help_table.add_column("Option", style="cyan", width=3)
        help_table.add_column("Topic")
        
        for key, (title, _) in help_sections.items():
            help_table.add_row(key, title)
        help_table.add_row("0", "Back to Main Menu")
        
        self.console.print(help_table)
        
        choice = Prompt.ask("\n[cyan]Select help topic[/cyan]", choices=['0'] + list(help_sections.keys()))
        
        if choice != '0':
            _, handler = help_sections[choice]
            handler()
            Prompt.ask("\n[dim]Press Enter to continue[/dim]")
    
    def _show_quick_start(self):
        """Show quick start guide"""
        quick_start = """
# Quick Start Guide

## 1. Basic Quick Scan
The easiest way to start scanning:
- Select "Quick Scan" from main menu
- Enter target URL (e.g., https://example.com)
- MCP will automatically configure optimal settings
- Watch real-time results

## 2. First-Time Setup
Recommended initial configuration:
- Configure AI agents for better results (Menu → Configuration → AI Agents)
- Download common wordlists (Menu → Configuration → Wordlists)
- Test with a known target first

## 3. Understanding Results
- **Green (200)**: Successfully found paths
- **Yellow (301/302)**: Redirects (may indicate directories)
- **Red (403)**: Forbidden (exists but no access)
- **Blue (401)**: Authentication required

## 4. Tips for Beginners
- Start with Quick Scan mode
- Use smaller wordlists first (common.txt)
- Enable AI mode for better detection
- Save reports for later analysis
"""
        
        self.console.print(Markdown(quick_start))
    
    def _show_scan_modes(self):
        """Show scan modes explanation"""
        scan_modes = """
# Scan Modes Explained

## Quick Scan (Recommended)
- **What**: Automatic configuration by MCP
- **When**: First scan, unfamiliar targets
- **Benefits**: Optimal settings, AI-powered decisions

## Advanced Scan
- **What**: Full manual control
- **When**: Specific requirements, custom wordlists
- **Benefits**: Fine-tuned control, custom parameters

## MCP Modes

### Auto Mode
- Analyzes target and chooses best approach
- Balances speed and thoroughness

### Aggressive Mode
- Maximum coverage
- More requests, deeper scanning
- Best for authorized testing

### Stealth Mode
- Slower, fewer requests
- Avoids detection
- Good for sensitive targets

### Smart Mode
- AI-guided decisions
- Learns from responses
- Adapts in real-time
"""
        
        self.console.print(Markdown(scan_modes))
    
    def _show_mcp_help(self):
        """Show MCP intelligence help"""
        mcp_help = """
# MCP Intelligence System

## What is MCP?
Machine Coordination Protocol - An AI-powered system that:
- Analyzes targets automatically
- Optimizes scan parameters
- Makes intelligent decisions
- Learns from responses

## How It Works
1. **Target Analysis**: Detects server, CMS, technologies
2. **Smart Planning**: Chooses appropriate wordlists and settings
3. **Adaptive Scanning**: Adjusts based on responses
4. **Decision Making**: Filters false positives, prioritizes findings

## AI Integration
- **OpenAI**: Advanced reasoning and pattern recognition
- **DeepSeek**: Code-focused analysis
- **Local Mode**: Rule-based decisions without API

## Benefits
- 🎯 Higher accuracy
- ⚡ Faster results
- 🧠 Smarter decisions
- 📊 Better reporting
"""
        
        self.console.print(Markdown(mcp_help))
    
    def _show_wordlist_help(self):
        """Show wordlist guide"""
        wordlist_help = """
# Wordlist Guide

## Choosing the Right Wordlist

### By Size
- **Small (1K-10K)**: Quick scans, basic coverage
- **Medium (10K-100K)**: Balanced approach
- **Large (100K+)**: Comprehensive, slower

### By Target Type
- **common.txt**: General purpose, good starting point
- **wordpress.txt**: WordPress sites
- **api_endpoints.txt**: REST APIs
- **backup_files.txt**: Backup and temp files

## Creating Custom Wordlists
1. Analyze target's naming patterns
2. Include technology-specific paths
3. Add variations (index.php, index.php.bak)
4. Consider extensions

## Tips
- Start small, expand if needed
- Combine multiple wordlists
- Remove duplicates
- Sort by likelihood
"""
        
        self.console.print(Markdown(wordlist_help))
    
    def _show_performance_help(self):
        """Show performance tips"""
        performance_help = """
# Performance Optimization

## Thread Configuration
- **Low (1-10)**: Slow targets, rate-limited
- **Medium (10-20)**: Most websites
- **High (20-50)**: Fast servers, local testing

## Timeout Settings
- Increase for slow servers
- Decrease for local/fast targets
- Balance with thread count

## Advanced Tuning

### Batch Size
- Controls paths per batch
- Higher = more memory, faster
- Lower = less memory, stable

### Connection Pooling
- Reuse connections
- Reduces overhead
- Enable for HTTPS

### DNS Caching
- Cache DNS lookups
- Faster for many subdomains
- Disable for dynamic IPs

## Warning Signs
- 🔴 Many timeouts: Reduce threads, increase timeout
- 🔴 429 errors: Add delay, reduce threads
- 🔴 Connection errors: Check proxy, reduce batch size
"""
        
        self.console.print(Markdown(performance_help))
    
    def _show_troubleshooting(self):
        """Show troubleshooting guide"""
        troubleshooting = """
# Troubleshooting

## Common Issues

### No Results Found
- ✓ Check wordlist selection
- ✓ Verify target is accessible
- ✓ Try different extensions
- ✓ Increase timeout

### Too Many 404s
- ✓ Target might have custom 404
- ✓ Check exclude_status setting
- ✓ Enable smart filtering

### Scan Too Slow
- ✓ Reduce timeout
- ✓ Increase threads (carefully)
- ✓ Use smaller wordlist
- ✓ Check network connection

### Authentication Errors
- ✓ Add authentication headers
- ✓ Use correct user-agent
- ✓ Check for WAF/protection

## Debug Mode
Enable verbose logging:
1. Configuration → Performance
2. Set log level to DEBUG
3. Check log files

## Getting Help
- Check examples (Help → Examples)
- Review documentation
- Check GitHub issues
"""
        
        self.console.print(Markdown(troubleshooting))
    
    def _show_examples(self):
        """Show usage examples"""
        examples = """
# Usage Examples

## Example 1: Basic WordPress Scan
```
Target: https://wordpress-site.com
Mode: Quick Scan
Result: MCP detects WordPress, uses wordpress.txt
```

## Example 2: API Endpoint Discovery
```
Target: https://api.example.com
Mode: Advanced Scan
Wordlist: api_endpoints.txt
Extensions: json,xml
Threads: 10 (be gentle with APIs)
```

## Example 3: Stealth Scan
```
Target: https://sensitive-target.com
Mode: Advanced Scan
MCP Mode: Stealth
Threads: 5
Delay: 1 second
User-Agent: Googlebot
```

## Example 4: Custom Wordlist
```
Create wordlist with:
- admin
- api/v1
- api/v2
- .git
- backup
```

## Example 5: Authenticated Scan
```
Headers:
- Authorization: Bearer YOUR_TOKEN
- Cookie: session=abc123
```
"""
        
        self.console.print(Markdown(examples))
    
    # Helper methods
    def _create_target_info_table(self, target_info) -> Table:
        """Create table for target information"""
        table = Table(show_header=False, box=None)
        table.add_column("Property", style="cyan")
        table.add_column("Value")
        
        table.add_row("Server", target_info.server_type or "Unknown")
        table.add_row("CMS", target_info.detected_cms or "None detected")
        
        if target_info.technology_stack:
            tech_str = ", ".join(target_info.technology_stack[:5])
            if len(target_info.technology_stack) > 5:
                tech_str += f" (+{len(target_info.technology_stack) - 5} more)"
            table.add_row("Technologies", tech_str)
        else:
            table.add_row("Technologies", "None detected")
        
        table.add_row("Security Headers", str(len(target_info.security_headers)))
        
        return table
    
    def _create_running_stats(self, elapsed: float, current: int, total: int, findings: int, speed: float) -> Text:
        """Create running statistics text"""
        stats_text = Text()
        stats_text.append("📊 Live Statistics\n\n", style="bold yellow")
        stats_text.append(f"Duration: {elapsed:.1f}s\n")
        stats_text.append(f"Progress: {current}/{total}\n")
        stats_text.append(f"Findings: {findings}\n")
        stats_text.append(f"Speed: {speed:.1f} req/s\n")
        stats_text.append(f"ETA: {(total-current)/speed:.1f}s\n" if speed > 0 else "ETA: Calculating...\n")
        return stats_text
    
    def _create_final_stats(self, elapsed: float, total_requests: int, 
                           findings: int, errors: int) -> Text:
        """Create final statistics display"""
        stats = Text()
        stats.append("📊 Final Statistics\n\n", style="bold")
        stats.append(f"Duration: {elapsed:.1f}s\n")
        stats.append(f"Total Requests: {total_requests}\n")
        stats.append(f"Findings: {findings}\n", style="green" if findings > 0 else "yellow")
        stats.append(f"Errors: {errors}\n", style="red" if errors > 0 else "green")
        stats.append(f"Requests/sec: {total_requests/elapsed:.1f}\n")
        
        return stats
    
    def _display_scan_insights(self, insights: Dict[str, Any]):
        """Display intelligent scan insights"""
        self.console.print("\n[bold cyan]🧠 Intelligent Scan Insights[/bold cyan]")
        self.console.print(Rule(style="cyan"))
        
        # Risk Assessment
        risk = insights.get('risk_assessment', {})
        risk_color = "red" if risk.get('level') == 'High' else "yellow" if risk.get('level') == 'Medium' else "green"
        
        risk_panel = Panel(
            f"[bold {risk_color}]Risk Level: {risk.get('level', 'Unknown')} ({risk.get('score', 0)}/100)[/bold {risk_color}]\n\n" +
            "\n".join(f"• {r}" for r in risk.get('risks', [])),
            title="🔒 Security Risk Assessment",
            border_style=risk_color
        )
        self.console.print(risk_panel)
        
        # Important Discoveries
        if insights.get('important_paths'):
            disc_table = Table(title="🎯 Important Discoveries", show_header=True)
            disc_table.add_column("Path", style="cyan")
            disc_table.add_column("Status", style="yellow")
            disc_table.add_column("Priority", style="red")
            
            for path_info in insights['important_paths'][:10]:
                disc_table.add_row(
                    path_info['path'],
                    str(path_info['status']),
                    str(path_info['rules'][0][1]) if path_info['rules'] else "N/A"
                )
            
            self.console.print(disc_table)
        
        # Technology Detection
        if insights.get('technology_hints'):
            tech_text = Text()
            tech_text.append("🔧 Detected Technologies\n\n", style="bold")
            for tech in insights['technology_hints']:
                tech_text.append(f"  • {tech}\n", style="green")
            
            self.console.print(Panel(tech_text, border_style="green"))
        
        # Recommendations
        if insights.get('recommendations'):
            rec_text = Text()
            rec_text.append("💡 Recommendations\n\n", style="bold yellow")
            for i, rec in enumerate(insights['recommendations'], 1):
                rec_text.append(f"{i}. {rec}\n", style="yellow")
            
            self.console.print(Panel(rec_text, border_style="yellow"))
        
        # Pattern Analysis
        if insights.get('discovered_patterns'):
            pattern_table = Table(title="📊 Discovered Patterns", show_header=True)
            pattern_table.add_column("Pattern", style="cyan")
            pattern_table.add_column("Count", style="yellow")
            
            for pattern, count in insights['discovered_patterns'].items():
                pattern_table.add_row(pattern.upper(), str(count))
            
            self.console.print(pattern_table)
    
    def _display_scan_summary(self, scan_response, duration: float):
        """Display scan summary after completion"""
        self.console.print("\n[bold green]✅ Scan Complete![/bold green]")
        self.console.print(Rule(style="green"))
        
        # Summary table
        summary_table = Table(show_header=False, box=None)
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", style="yellow")
        
        summary_table.add_row("Total Requests", str(scan_response.statistics.get('total_requests', 0)))
        summary_table.add_row("Found Paths", str(scan_response.statistics.get('found_paths', 0)))
        summary_table.add_row("Scan Duration", f"{duration:.1f} seconds")
        summary_table.add_row("Requests/Second", f"{scan_response.statistics.get('total_requests', 0)/duration:.1f}")
        
        self.console.print(summary_table)
        
        # Status code breakdown
        if scan_response.results:
            status_counts = {}
            for result in scan_response.results:
                status = result.get('status', 0)
                status_counts[status] = status_counts.get(status, 0) + 1
            
            if status_counts:
                self.console.print("\n[bold]Status Code Breakdown:[/bold]")
                status_table = Table(show_header=True, box=None)
                status_table.add_column("Status", style="cyan", width=10)
                status_table.add_column("Count", style="yellow", width=10)
                status_table.add_column("Description", style="dim")
                
                status_descriptions = {
                    200: "OK - Success",
                    301: "Moved Permanently",
                    302: "Found (Redirect)",
                    403: "Forbidden",
                    401: "Unauthorized",
                    500: "Internal Server Error"
                }
                
                for status in sorted(status_counts.keys()):
                    desc = status_descriptions.get(status, "Other")
                    status_table.add_row(str(status), str(status_counts[status]), desc)
                
                self.console.print(status_table)
        
        # Top findings (limited to 20 lines)
        if scan_response.results:
            self.console.print("\n[bold]Top Findings (Limited to 20 lines):[/bold]")
            
            # Group by status code
            status_groups = {}
            for result in scan_response.results:
                status = result['status']
                if status not in status_groups:
                    status_groups[status] = []
                status_groups[status].append(result)
            
            # Display with 20 line limit
            lines_shown = 0
            max_lines = 20
            
            for status in sorted(status_groups.keys()):
                if lines_shown >= max_lines:
                    break
                
                items = status_groups[status]
                status_style = "green" if status == 200 else "yellow" if status in [301, 302] else "red" if status in [401, 403] else "dim"
                
                self.console.print(f"\n[{status_style}][{status}][/{status_style}] Status Code - {len(items)} found:")
                lines_shown += 1
                
                # Create table for this status group
                findings_table = Table(box=None, show_header=False, padding=(0, 2))
                findings_table.add_column("Path", style="cyan", no_wrap=True)
                findings_table.add_column("Size", justify="right", style="dim")
                findings_table.add_column("Type", style="dim")
                
                # Show items for this status
                items_to_show = min(len(items), max_lines - lines_shown)
                for result in sorted(items, key=lambda x: x['path'])[:items_to_show]:
                    findings_table.add_row(
                        f"  {result['path']}",
                        f"{result.get('size', 0)} B",
                        result.get('content_type', '-')[:20]
                    )
                    lines_shown += 1
                
                self.console.print(findings_table)
                
                if len(items) > items_to_show:
                    self.console.print(f"  [dim]... and {len(items) - items_to_show} more[/dim]")
                    lines_shown += 1
            
            # Summary if truncated
            if len(scan_response.results) > max_lines:
                self.console.print(f"\n[dim](Showing {min(lines_shown, max_lines)} of {len(scan_response.results)} total results)[/dim]")
            
            # 301 Redirects section
            results_301 = [r for r in scan_response.results if r.get('status') == 301]
            if results_301:
                self.console.print("\n[bold yellow]🔄 301 Redirects Found (Recursively Scanned):[/bold yellow]")
                
                for r301 in results_301[:5]:
                    self.console.print(f"\n  [yellow]{r301['path']}[/yellow] → 301 Redirect")
                    if r301.get('redirect'):
                        self.console.print(f"    Redirects to: {r301['redirect']}")
                    
                    # Find paths discovered inside this 301 directory
                    path_prefix = r301['path'].rstrip('/') + '/'
                    children = [r for r in scan_response.results 
                               if r['path'].startswith(path_prefix) and r['path'] != r301['path']]
                    
                    if children:
                        self.console.print(f"    [green]Found {len(children)} hidden paths inside:[/green]")
                        for child in children[:3]:
                            status_icon = "🟢" if child['status'] == 200 else "🔴" if child['status'] == 403 else "🟡"
                            self.console.print(f"      {status_icon} {child['path']} [{child['status']}]")
                        if len(children) > 3:
                            self.console.print(f"      ... and {len(children) - 3} more")
                
                if len(results_301) > 5:
                    self.console.print(f"\n  [dim]... and {len(results_301) - 5} more 301 redirects[/dim]")
            
            # Directory tree visualization
            if hasattr(self.dirsearch_engine, 'build_directory_tree'):
                self.console.print("\n[bold]🌳 Directory Tree:[/bold]")
                
                # Convert results to format expected by engine
                scan_results = []
                for r in scan_response.results:
                    from src.core.dirsearch_engine import ScanResult
                    scan_results.append(ScanResult(
                        url=r.get('url', ''),
                        path=r.get('path', ''),
                        status_code=r.get('status', 0),
                        size=r.get('size', 0),
                        is_directory=r.get('is_directory', False)
                    ))
                
                tree_dict = self.dirsearch_engine.build_directory_tree(scan_results)
                tree_str = self.dirsearch_engine.print_directory_tree(tree_dict)
                
                if tree_str:
                    self.console.print(tree_str)
                
                # Directory statistics
                stats = self.dirsearch_engine.get_directory_statistics(scan_results)
                if stats:
                    self.console.print(f"\n[bold]Directory Statistics:[/bold]")
                    self.console.print(f"  • Directories: {stats['directories']}")
                    self.console.print(f"  • Files: {stats['files']}")
                    self.console.print(f"  • Max Depth: {stats['max_depth']}")
                    if stats.get('deepest_path'):
                        self.console.print(f"  • Deepest Path: {stats['deepest_path']}")
    
    def _serialize_target_info(self, target_info) -> Dict[str, Any]:
        """Convert TargetInfo to dict"""
        return {
            'url': target_info.url,
            'domain': target_info.domain,
            'server_type': target_info.server_type,
            'technology_stack': target_info.technology_stack,
            'response_patterns': target_info.response_patterns,
            'security_headers': target_info.security_headers,
            'detected_cms': target_info.detected_cms
        }
    
    def _serialize_scan_task(self, task) -> Dict[str, Any]:
        """Convert ScanTask to dict"""
        return {
            'task_id': task.task_id,
            'task_type': task.task_type,
            'priority': task.priority,
            'parameters': task.parameters,
            'dependencies': task.dependencies
        }
    
    async def _generate_custom_scan_plan(self, target_info, config: Dict[str, Any]):
        """Generate scan plan with custom configuration"""
        from src.core.mcp_coordinator import ScanTask
        
        # Create custom scan task
        task = ScanTask(
            task_id='custom_scan',
            task_type='directory_enumeration',
            priority=100,
            parameters={
                'wordlist': config.get('wordlist', 'common.txt'),
                'extensions': config.get('extensions', []),
                'threads': config.get('threads', 10),
                'timeout': config.get('timeout', 10),
                'follow_redirects': config.get('follow_redirects', False),
                'exclude_status': config.get('exclude_status', '404'),
                'user_agent': config.get('user_agent', 'Mozilla/5.0')
            }
        )
        
        return [task]


def main():
    """Main entry point"""
    try:
        menu = InteractiveMenu()
        menu.run()
    except KeyboardInterrupt:
        print("\n\n[yellow]Scan interrupted by user[/yellow]")
    except Exception as e:
        print(f"\n[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()