#!/usr/bin/env python3
"""
Dirsearch MCP - Intelligent Directory Scanner with AI Integration
Main application entry point with CLI and interactive mode support
"""

import sys
import os
import argparse
import asyncio
import signal
from pathlib import Path
import json
from typing import Optional, List, Dict, Any
import logging
from urllib.parse import urlparse

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from src.cli.interactive_menu import InteractiveMenu
    from src.core.dirsearch_engine import DirsearchEngine, ScanRequest
    from src.core.mcp_coordinator import MCPCoordinator
    from src.utils.logger import LoggerSetup
    from src.utils.reporter import ReportGenerator
    from src.config.settings import Settings
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Please ensure all dependencies are installed: pip install -r requirements.txt")
    sys.exit(1)

# Version information
__version__ = "1.0.0"
__author__ = "Dirsearch MCP Team"
__description__ = "Intelligent Directory Scanner with MCP AI Integration"


class DirsearchMCPCLI:
    """Command-line interface for Dirsearch MCP"""
    
    def __init__(self):
        self.settings = None
        self.logger = None
        self.interrupted = False
        self.current_engine = None
        self.current_tasks = []
        
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            self.interrupted = True
            if self.logger:
                self.logger.warning("\nReceived interrupt signal. Shutting down gracefully...")
            else:
                print("\nReceived interrupt signal. Shutting down gracefully...")
            
            # Stop any running scan engine
            if self.current_engine:
                self.current_engine.stop_scan()
            
            # Cancel all running tasks
            for task in self.current_tasks:
                if not task.done():
                    task.cancel()
            
            # For immediate exit on macOS, raise KeyboardInterrupt
            raise KeyboardInterrupt()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def shutdown(self):
        """Graceful shutdown procedure"""
        # Cancel all running tasks
        try:
            # Python 3.7+
            tasks = [t for t in asyncio.all_tasks() if t != asyncio.current_task()]
        except AttributeError:
            try:
                # Python 3.9+ (asyncio.all_tasks might be deprecated)
                tasks = [t for t in asyncio.Task.all_tasks() if t != asyncio.Task.current_task()]
            except AttributeError:
                # Fallback for newer Python versions
                loop = asyncio.get_event_loop()
                tasks = [t for t in asyncio.all_tasks(loop) if t != asyncio.current_task()]
        
        for task in tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        if self.logger:
            self.logger.info("Shutdown complete")
    
    def create_parser(self) -> argparse.ArgumentParser:
        """Create command-line argument parser"""
        parser = argparse.ArgumentParser(
            prog='dirsearch-mcp',
            description=__description__,
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Interactive mode
  %(prog)s
  
  # Quick scan with auto-configuration
  %(prog)s -u https://example.com
  
  # Scan with custom wordlist and extensions
  %(prog)s -u https://example.com -w wordlist.txt -e php,html,js
  
  # Advanced scan with specific parameters
  %(prog)s -u https://example.com -t 20 --timeout 10 --follow-redirects
  
  # Generate specific report format
  %(prog)s -u https://example.com --report-format html --output-dir ./reports
  
  # Use AI agent mode (requires API key)
  %(prog)s -u https://example.com --ai-provider openai --ai-key YOUR_KEY
            """
        )
        
        # Version
        parser.add_argument(
            '-v', '--version',
            action='version',
            version=f'%(prog)s {__version__}'
        )
        
        # Target options
        target_group = parser.add_argument_group('Target options')
        target_group.add_argument(
            '-u', '--url',
            type=str,
            help='Target URL to scan'
        )
        target_group.add_argument(
            '-l', '--url-list',
            type=str,
            help='File containing URLs to scan'
        )
        
        # Scan options
        scan_group = parser.add_argument_group('Scan options')
        scan_group.add_argument(
            '-w', '--wordlist',
            type=str,
            default='common.txt',
            help='Wordlist file (default: common.txt)'
        )
        scan_group.add_argument(
            '-e', '--extensions',
            type=str,
            help='Extensions to check (comma-separated, e.g., php,html,js)'
        )
        scan_group.add_argument(
            '-t', '--threads',
            type=int,
            default=10,
            help='Number of threads (default: 10)'
        )
        scan_group.add_argument(
            '--timeout',
            type=int,
            default=10,
            help='Request timeout in seconds (default: 10)'
        )
        scan_group.add_argument(
            '--delay',
            type=float,
            default=0,
            help='Delay between requests in seconds (default: 0)'
        )
        scan_group.add_argument(
            '--user-agent',
            type=str,
            help='Custom User-Agent string'
        )
        scan_group.add_argument(
            '--follow-redirects',
            action='store_true',
            help='Follow HTTP redirects'
        )
        scan_group.add_argument(
            '--exclude-status',
            type=str,
            default='404',
            help='Status codes to exclude (comma-separated, default: 404)'
        )
        scan_group.add_argument(
            '--include-status',
            type=str,
            help='Only include these status codes (comma-separated)'
        )
        scan_group.add_argument(
            '-r', '--recursive',
            action='store_true',
            default=True,
            help='Enable recursive scanning (default: True)'
        )
        scan_group.add_argument(
            '--no-recursive',
            action='store_true',
            help='Disable recursive scanning'
        )
        scan_group.add_argument(
            '-R', '--recursion-depth',
            type=int,
            default=3,
            help='Maximum recursion depth (default: 3)'
        )
        
        # MCP options
        mcp_group = parser.add_argument_group('MCP Intelligence options')
        mcp_group.add_argument(
            '--mcp-mode',
            choices=['auto', 'local', 'ai'],
            default='auto',
            help='MCP mode: auto, local (rule-based), or ai (default: auto)'
        )
        mcp_group.add_argument(
            '--ai-provider',
            choices=['openai', 'deepseek'],
            help='AI provider to use'
        )
        mcp_group.add_argument(
            '--ai-key',
            type=str,
            help='API key for AI provider'
        )
        mcp_group.add_argument(
            '--ai-model',
            type=str,
            help='Specific AI model to use'
        )
        
        # Output options
        output_group = parser.add_argument_group('Output options')
        output_group.add_argument(
            '-o', '--output-dir',
            type=str,
            default='./report',
            help='Output directory for reports (default: ./report)'
        )
        output_group.add_argument(
            '--report-format',
            choices=['json', 'html', 'markdown', 'all'],
            default='all',
            help='Report format (default: all)'
        )
        output_group.add_argument(
            '--quiet',
            action='store_true',
            help='Minimal output'
        )
        output_group.add_argument(
            '--verbose',
            action='store_true',
            help='Verbose output'
        )
        output_group.add_argument(
            '--no-color',
            action='store_true',
            help='Disable colored output'
        )
        
        # Advanced options
        advanced_group = parser.add_argument_group('Advanced options')
        advanced_group.add_argument(
            '--config',
            type=str,
            help='Configuration file path'
        )
        advanced_group.add_argument(
            '--proxy',
            type=str,
            help='HTTP/HTTPS proxy URL'
        )
        advanced_group.add_argument(
            '--headers',
            type=str,
            help='Custom headers (JSON format)'
        )
        advanced_group.add_argument(
            '--max-retries',
            type=int,
            default=3,
            help='Maximum retry attempts (default: 3)'
        )
        advanced_group.add_argument(
            '--batch-size',
            type=int,
            default=50,
            help='Batch size for concurrent requests (default: 50)'
        )
        
        # Mode options
        mode_group = parser.add_argument_group('Mode options')
        mode_group.add_argument(
            '-i', '--interactive',
            action='store_true',
            help='Run in interactive mode (default if no URL provided)'
        )
        mode_group.add_argument(
            '--quick',
            action='store_true',
            help='Quick scan with MCP auto-configuration'
        )
        mode_group.add_argument(
            '--smart',
            action='store_true',
            help='Smart scan with intelligent discovery (Recommended)'
        )
        mode_group.add_argument(
            '--monster',
            action='store_true',
            help='Monster mode with maximum discovery (WARNING: Extremely aggressive)'
        )
        
        return parser
    
    def load_configuration(self, args: argparse.Namespace) -> Settings:
        """Load configuration from file and arguments"""
        # Start with default settings
        settings = Settings()
        
        # Load from config file if specified
        if args.config:
            config_path = Path(args.config)
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config_data = json.load(f)
                    # Update settings with config file data
                    for key, value in config_data.items():
                        if hasattr(settings, key):
                            setattr(settings, key, value)
            else:
                print(f"Warning: Config file not found: {args.config}")
        
        # Override with command-line arguments
        if args.threads:
            settings.default_scan_config['threads'] = args.threads
        if args.timeout:
            settings.default_scan_config['timeout'] = args.timeout
        if args.user_agent:
            settings.default_scan_config['user_agent'] = args.user_agent
        if args.follow_redirects:
            settings.default_scan_config['follow_redirects'] = True
        if args.exclude_status:
            settings.default_scan_config['exclude_status'] = args.exclude_status
        
        # AI configuration
        if args.ai_key:
            if args.ai_provider == 'openai':
                settings.ai_config['openai_api_key'] = args.ai_key
            elif args.ai_provider == 'deepseek':
                settings.ai_config['deepseek_api_key'] = args.ai_key
        
        if args.ai_model:
            settings.ai_config['model'] = args.ai_model
        
        # Output configuration
        settings.paths['reports'] = args.output_dir
        
        return settings
    
    async def run_direct_scan(self, args: argparse.Namespace):
        """Run scan in direct CLI mode"""
        # Initialize components
        settings = self.load_configuration(args)
        LoggerSetup.initialize()
        self.logger = LoggerSetup.get_logger(__name__)
        
        # Set logging level
        if args.quiet:
            logging.getLogger().setLevel(logging.WARNING)
        elif args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)
        
        self.logger.info(f"Starting Dirsearch MCP v{__version__}")
        
        # Initialize MCP coordinator
        mcp = MCPCoordinator(settings)
        
        # Set MCP mode
        if args.mcp_mode == 'local':
            mcp.intelligence_mode = 'LOCAL'
        elif args.mcp_mode == 'ai' and (args.ai_key or settings.ai_config.get('openai_api_key') or settings.ai_config.get('deepseek_api_key')):
            await mcp.initialize()
        else:
            await mcp.initialize()  # Auto mode
        
        self.logger.info(f"MCP Intelligence Mode: {mcp.intelligence_mode}")
        
        # Initialize scan engine
        engine = DirsearchEngine(settings)
        
        # Get URLs to scan
        urls = []
        if args.url:
            urls.append(args.url)
        elif args.url_list:
            with open(args.url_list, 'r') as f:
                urls.extend(line.strip() for line in f if line.strip())
        
        if not urls:
            self.logger.error("No target URLs specified")
            return
        
        # Process each URL
        for url in urls:
            if self.interrupted:
                break
                
            self.logger.info(f"\nScanning target: {url}")
            
            try:
                # Step 1: Target analysis
                self.logger.info("Analyzing target...")
                target_info = await mcp.analyze_target(url)
                
                # Log target information
                self.logger.info(f"Server: {target_info.server_type}")
                self.logger.info(f"Technologies: {', '.join(target_info.technology_stack)}")
                if target_info.detected_cms:
                    self.logger.info(f"CMS: {target_info.detected_cms}")
                
                # Step 2: Generate scan plan
                if args.smart:
                    # Smart mode configuration
                    self.logger.info("🧠 SMART MODE: Using intelligent discovery with rule-based optimization")
                    params = {
                        'threads': 20,
                        'timeout': 15,
                        'delay': 0,
                        'user_agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
                        'follow_redirects': True
                    }
                    wordlist = 'critical-admin.txt'  # Located in wordlists root
                    # TODO: Add support for multiple wordlists in CLI mode
                    extensions = ['php', 'asp', 'aspx', 'jsp', 'html', 'json', 'xml', 'sql', 'zip', 'bak']
                    args.recursive = True
                    args.recursion_depth = 3
                    args.include_status = '200,201,301,302,401,403,500'
                    
                elif args.monster:
                    # Monster mode configuration
                    self.logger.warning("👹 MONSTER MODE: Using EXTREMELY aggressive settings for maximum discovery")
                    if not args.quiet:
                        print("\n⚠️  WARNING: Monster mode generates MASSIVE traffic!")
                        print("👹 Only unleash the monster with explicit permission!\n")
                    
                    params = {
                        'threads': 50,  # Maximum threads
                        'timeout': 30,  # Extended timeout
                        'delay': 0,     # No delay
                        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'follow_redirects': True
                    }
                    wordlist = 'general/monster-all.txt'  # Full path with subdirectory
                    extensions = [
                        'php', 'html', 'htm', 'asp', 'aspx', 'jsp', 'jspx', 'do', 'action',
                        'pl', 'cgi', 'py', 'rb', 'js', 'css', 'xml', 'json', 'yaml', 'yml',
                        'txt', 'log', 'md', 'conf', 'config', 'ini', 'env', 'properties',
                        'bak', 'backup', 'old', 'orig', 'save', 'swp', 'tmp', 'temp',
                        'zip', 'tar', 'gz', 'rar', '7z', 'sql', 'db', 'sqlite'
                    ]
                    args.recursive = True
                    args.recursion_depth = 5
                    args.exclude_status = ''  # Don't exclude any status
                    args.max_retries = 5
                    
                elif args.quick:
                    self.logger.info("Generating optimized scan plan...")
                    scan_plan = await mcp.generate_scan_plan(target_info)
                    
                    # Get optimized parameters
                    params = await mcp.optimize_parameters(target_info)
                    wordlist = scan_plan[0].parameters.get('wordlist', args.wordlist)
                    extensions = scan_plan[0].parameters.get('extensions', [])
                else:
                    # Use manual parameters
                    params = {
                        'threads': args.threads,
                        'timeout': args.timeout,
                        'delay': args.delay,
                        'user_agent': args.user_agent or settings.default_scan_config.get('user_agent'),
                        'follow_redirects': args.follow_redirects
                    }
                    wordlist = args.wordlist
                    extensions = args.extensions.split(',') if args.extensions else []
                
                # Step 3: Execute scan
                self.logger.info(f"Starting scan with {params['threads']} threads...")
                
                # Parse custom headers
                custom_headers = {}
                if args.headers:
                    try:
                        custom_headers = json.loads(args.headers)
                    except json.JSONDecodeError:
                        self.logger.warning("Invalid headers format, ignoring")
                
                scan_request = ScanRequest(
                    base_url=url,
                    wordlist=wordlist,
                    extensions=extensions,
                    threads=params['threads'],
                    timeout=params['timeout'],
                    delay=params.get('delay', 0),
                    user_agent=params['user_agent'],
                    follow_redirects=params.get('follow_redirects', False),
                    custom_headers=custom_headers,
                    proxy=args.proxy,
                    max_retries=args.max_retries,
                    exclude_status=args.exclude_status,
                    include_status=args.include_status,
                    recursive=not args.no_recursive,  # True by default, False if --no-recursive
                    recursion_depth=args.recursion_depth
                )
                
                # Execute scan
                self.current_engine = engine
                try:
                    scan_response = await engine.execute_scan(scan_request)
                finally:
                    self.current_engine = None
                
                # Log results
                self.logger.info(f"\nScan completed:")
                self.logger.info(f"Total requests: {scan_response.statistics['total_requests']}")
                self.logger.info(f"Found paths: {scan_response.statistics['found_paths']}")
                self.logger.info(f"Errors: {scan_response.statistics.get('errors', 0)}")
                
                # Display results (limited to 20 lines)
                if scan_response.results and not args.quiet:
                    self.logger.info("\nDiscovered paths:")
                    sorted_results = sorted(scan_response.results, key=lambda x: (x['status'], x['path']))
                    
                    # Group by status code for better display
                    status_groups = {}
                    for result in sorted_results:
                        status = result['status']
                        if status not in status_groups:
                            status_groups[status] = []
                        status_groups[status].append(result)
                    
                    # Display up to 20 lines total
                    lines_shown = 0
                    max_lines = 20
                    
                    for status in sorted(status_groups.keys()):
                        if lines_shown >= max_lines:
                            break
                        
                        items = status_groups[status]
                        self.logger.info(f"\n  [{status}] Status Code - {len(items)} found:")
                        lines_shown += 1
                        
                        # Show up to remaining lines for this status
                        items_to_show = min(len(items), max_lines - lines_shown)
                        for i, result in enumerate(items[:items_to_show]):
                            self.logger.info(f"    • {result['path']} - {result['size']} bytes")
                            lines_shown += 1
                        
                        if len(items) > items_to_show:
                            self.logger.info(f"    ... and {len(items) - items_to_show} more")
                            lines_shown += 1
                    
                    # Show summary if results were truncated
                    if len(sorted_results) > max_lines:
                        self.logger.info(f"\n  (Showing {min(lines_shown, max_lines)} of {len(sorted_results)} total results)")
                
                # Step 4: Generate report
                if args.report_format:
                    self.logger.info(f"\nGenerating {args.report_format} report...")
                    
                    reporter = ReportGenerator(args.output_dir)
                    
                    # Prepare scan data
                    scan_data = {
                        'target_url': url,
                        'target_domain': target_info.domain if target_info.domain else urlparse(url).netloc,
                        'start_time': scan_response.statistics.get('start_time', ''),
                        'end_time': scan_response.statistics.get('end_time', ''),
                        'duration': scan_response.statistics.get('duration', 0),
                        'intelligence_mode': mcp.intelligence_mode,
                        'target_analysis': {
                            'server_type': target_info.server_type,
                            'technology_stack': target_info.technology_stack,
                            'detected_cms': target_info.detected_cms,
                            'security_headers': target_info.security_headers
                        },
                        'scan_results': [{
                            'task_id': 'cli_scan',
                            'status': 'completed',
                            'findings': scan_response.results,
                            'metrics': scan_response.statistics,
                            'timestamp': scan_response.statistics.get('end_time', '')
                        }],
                        'performance_metrics': {
                            'total_requests': scan_response.statistics['total_requests'],
                            'found_paths': scan_response.statistics['found_paths'],
                            'errors': scan_response.statistics.get('errors', 0),
                            'requests_per_second': scan_response.statistics.get('requests_per_second', 0)
                        }
                    }
                    
                    report_files = reporter.generate_report(scan_data, format=args.report_format)
                    
                    self.logger.info("Reports saved:")
                    for format_type, file_path in report_files.items():
                        self.logger.info(f"  {format_type.upper()}: {file_path}")
                
            except Exception as e:
                self.logger.error(f"Error scanning {url}: {e}")
                if args.verbose:
                    import traceback
                    traceback.print_exc()
        
        self.logger.info("\nAll scans completed")
    
    async def run_interactive_mode(self, args: argparse.Namespace):
        """Run in interactive mode"""
        settings = self.load_configuration(args)
        menu = InteractiveMenu()
        menu.settings = settings
        await menu._async_run()
    
    async def main(self):
        """Main application entry point"""
        # Parse command-line arguments first (before signal handlers)
        parser = self.create_parser()
        args = parser.parse_args()
        
        # Disable colors if requested
        if args.no_color:
            os.environ['NO_COLOR'] = '1'
        
        try:
            # Setup signal handlers after parsing args
            self.setup_signal_handlers()
            
            # Determine mode
            if args.url or args.url_list:
                # Direct scan mode
                task = asyncio.create_task(self.run_direct_scan(args))
                self.current_tasks.append(task)
                await task
            else:
                # Interactive mode
                task = asyncio.create_task(self.run_interactive_mode(args))
                self.current_tasks.append(task)
                await task
                
        except KeyboardInterrupt:
            print("\nOperation cancelled by user")
            await self.shutdown()
            sys.exit(0)
        except asyncio.CancelledError:
            print("\nOperation cancelled")
            await self.shutdown()
            sys.exit(0)
        except Exception as e:
            print(f"\nError: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            sys.exit(1)


def main():
    """Main entry point"""
    cli = DirsearchMCPCLI()
    
    # Handle Windows event loop
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # Run the application
    try:
        asyncio.run(cli.main())
    except RuntimeError as e:
        if "This event loop is already running" in str(e):
            # Handle Jupyter notebook environment
            try:
                import nest_asyncio
                nest_asyncio.apply()
                loop = asyncio.get_event_loop()
                loop.run_until_complete(cli.main())
            except ImportError:
                print("Note: For Jupyter notebook support, install nest-asyncio: pip install nest-asyncio")
                raise
        else:
            raise
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(0)


if __name__ == "__main__":
    main()