#!/usr/bin/env python3
"""
Interactive demo for testing migrated dirsearch features
This script allows users to test each feature individually
"""

import asyncio
import sys
import os
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.dirsearch_engine import DirsearchEngine, ScanOptions, DynamicContentParser
from src.config import Settings

console = Console()


class FeatureDemo:
    def __init__(self):
        self.engine = None
        self.console = console
    
    async def setup(self):
        """Initialize engine"""
        self.engine = DirsearchEngine(Settings())
        return self
    
    async def cleanup(self):
        """Clean up resources"""
        if self.engine:
            await self.engine.close()
    
    def show_menu(self):
        """Display feature menu"""
        self.console.print("\n[bold cyan]Dirsearch Feature Demo Menu[/bold cyan]\n")
        
        menu = Table(show_header=False, box=None)
        menu.add_column("Option", style="yellow")
        menu.add_column("Feature")
        
        menu.add_row("1", "Test Wildcard Detection")
        menu.add_row("2", "Test Extension Tags")
        menu.add_row("3", "Test Authentication Methods")
        menu.add_row("4", "Test Content Crawling")
        menu.add_row("5", "Test Blacklist Filtering")
        menu.add_row("6", "Test Random User Agents")
        menu.add_row("7", "Run Full Scan Demo")
        menu.add_row("0", "Exit")
        
        self.console.print(menu)
        return Prompt.ask("\nSelect option", choices=["0", "1", "2", "3", "4", "5", "6", "7"])
    
    async def demo_wildcard_detection(self):
        """Demo wildcard detection"""
        self.console.print(Panel("[bold]Wildcard Detection Demo[/bold]"))
        
        self.console.print("\nThis feature detects if a server returns the same response")
        self.console.print("for any random path (wildcard behavior).\n")
        
        # Test with two different contents
        content1 = "Error: Page not found - /random123"
        content2 = "Error: Page not found - /random456"
        
        parser = DynamicContentParser(content1, content2)
        
        self.console.print(f"Content 1: {content1}")
        self.console.print(f"Content 2: {content2}")
        self.console.print(f"\nIs static content: {parser._is_static}")
        
        # Test with new content
        test_content = "Error: Page not found - /random789"
        matches = parser.compare_to(test_content)
        
        self.console.print(f"\nTest content: {test_content}")
        self.console.print(f"Matches pattern: {matches}")
        
        if matches:
            self.console.print("\n[yellow]⚠️  This would be filtered as a wildcard response[/yellow]")
        else:
            self.console.print("\n[green]✅ This is a unique response[/green]")
        
        # Show how to use in scanning
        code = '''
# Enable wildcard detection in scan
options = ScanOptions(
    detect_wildcards=True,
    extensions=['php', 'html']
)

results = await engine.scan_target(url, wordlist, options)
'''
        self.console.print("\n[bold]Usage Example:[/bold]")
        self.console.print(Syntax(code, "python"))
    
    def demo_extension_tags(self):
        """Demo extension tag replacement"""
        self.console.print(Panel("[bold]Extension Tag Demo[/bold]"))
        
        self.console.print("\nExtension tags allow flexible wordlist entries")
        self.console.print("that expand to multiple file extensions.\n")
        
        # Demo wordlist
        demo_wordlist = [
            "config.%EXT%",
            "database.%EXT%",
            "backup.%EXT%.bak",
            "readme"  # No tag
        ]
        
        extensions = ['php', 'asp', 'jsp']
        
        self.console.print("[bold]Original wordlist:[/bold]")
        for word in demo_wordlist:
            self.console.print(f"  • {word}")
        
        # Enhance wordlist
        enhanced = self.engine._enhance_wordlist_with_extensions(
            demo_wordlist, extensions, "%EXT%"
        )
        
        self.console.print(f"\n[bold]Enhanced wordlist ({len(enhanced)} entries):[/bold]")
        for word in sorted(enhanced)[:15]:  # Show first 15
            self.console.print(f"  • {word}")
        
        if len(enhanced) > 15:
            self.console.print(f"  ... and {len(enhanced) - 15} more")
        
        # Show usage
        code = '''
# Use extension tags in wordlist
wordlist = ['admin.%EXT%', 'config.%EXT%', 'login']

options = ScanOptions(
    extensions=['php', 'asp', 'jsp'],
    extension_tag='%EXT%'
)

# This will scan: admin.php, admin.asp, admin.jsp, config.php, etc.
'''
        self.console.print("\n[bold]Usage Example:[/bold]")
        self.console.print(Syntax(code, "python"))
    
    def demo_authentication(self):
        """Demo authentication methods"""
        self.console.print(Panel("[bold]Authentication Methods Demo[/bold]"))
        
        self.console.print("\nDirsearch now supports multiple authentication methods:\n")
        
        auth_types = [
            ("basic", "Basic Authentication (username:password)"),
            ("digest", "Digest Authentication (more secure)"),
            ("ntlm", "NTLM Authentication (Windows domains)")
        ]
        
        for auth_type, description in auth_types:
            auth = self.engine._get_auth_handler(auth_type, ('user', 'pass'))
            status = "✅ Available" if auth else "❌ Not available"
            self.console.print(f"• {auth_type.upper()}: {description} - {status}")
        
        # Show usage examples
        code = '''
# Basic Authentication
options = ScanOptions(
    auth=('username', 'password'),
    auth_type='basic'
)

# Digest Authentication
options = ScanOptions(
    auth=('username', 'password'),
    auth_type='digest'
)

# NTLM Authentication
options = ScanOptions(
    auth=('DOMAIN\\\\username', 'password'),
    auth_type='ntlm'
)
'''
        self.console.print("\n[bold]Usage Examples:[/bold]")
        self.console.print(Syntax(code, "python"))
    
    async def demo_crawling(self):
        """Demo content crawling"""
        self.console.print(Panel("[bold]Content Crawling Demo[/bold]"))
        
        self.console.print("\nCrawling extracts additional paths from discovered content.\n")
        
        # Demo HTML
        html = '''<html>
<head>
    <link href="/css/style.css" rel="stylesheet">
    <script src="/js/app.js"></script>
</head>
<body>
    <a href="/admin/">Admin Panel</a>
    <a href="/api/v1/users">API Endpoint</a>
    <form action="/login.php" method="post">
        <input type="submit" value="Login">
    </form>
    <img src="/images/logo.png" alt="Logo">
</body>
</html>'''
        
        self.console.print("[bold]Sample HTML:[/bold]")
        self.console.print(Syntax(html, "html", line_numbers=True))
        
        # Crawl the content
        response_data = {
            'headers': {'content-type': 'text/html'},
            'text': html,
            'path': 'index.html'
        }
        
        paths = await self.engine._crawl_response(response_data, "http://example.com/")
        
        self.console.print("\n[bold]Discovered paths:[/bold]")
        for path in sorted(paths):
            self.console.print(f"  • /{path}")
        
        # Show usage
        code = '''
# Enable crawling in scan
options = ScanOptions(
    crawl=True,  # Enable crawling
    extensions=['html', 'php'],
    threads=10
)

# Discovered paths will be automatically added to the scan queue
'''
        self.console.print("\n[bold]Usage Example:[/bold]")
        self.console.print(Syntax(code, "python"))
    
    def demo_blacklists(self):
        """Demo blacklist filtering"""
        self.console.print(Panel("[bold]Blacklist Filtering Demo[/bold]"))
        
        self.console.print("\nBlacklists filter out common false positives")
        self.console.print("based on status codes and path patterns.\n")
        
        # Demo blacklist
        demo_blacklist = {
            403: ['cgi-bin', 'icons', '.htaccess'],
            500: ['error', 'debug', 'trace']
        }
        
        options = ScanOptions(blacklists=demo_blacklist)
        
        # Test cases
        test_cases = [
            ("cgi-bin/test.cgi", 403, "Blacklisted (403 + cgi-bin)"),
            ("admin/panel.php", 403, "Allowed (403 but not blacklisted path)"),
            ("debug.log", 500, "Blacklisted (500 + debug)"),
            ("contact.php", 500, "Allowed (500 but not blacklisted path)"),
            ("cgi-bin/test.cgi", 200, "Allowed (200 status)")
        ]
        
        self.console.print("[bold]Blacklist rules:[/bold]")
        for status, patterns in demo_blacklist.items():
            self.console.print(f"  {status}: {', '.join(patterns)}")
        
        self.console.print("\n[bold]Test results:[/bold]")
        table = Table()
        table.add_column("Path", style="cyan")
        table.add_column("Status")
        table.add_column("Result")
        
        for path, status, expected in test_cases:
            is_blacklisted = self.engine._is_blacklisted(path, status, options)
            result = "🚫 Filtered" if is_blacklisted else "✅ Included"
            table.add_row(path, str(status), result)
        
        self.console.print(table)
        
        # Show usage
        code = '''
# Define custom blacklists
options = ScanOptions(
    blacklists={
        403: ['cgi-bin', 'icons'],
        500: ['error', 'debug']
    }
)

# Or load from files (automatic)
# wordlists/blacklists/403_blacklist.txt
# wordlists/blacklists/500_blacklist.txt
'''
        self.console.print("\n[bold]Usage Example:[/bold]")
        self.console.print(Syntax(code, "python"))
    
    def demo_user_agents(self):
        """Demo random user agents"""
        self.console.print(Panel("[bold]Random User Agents Demo[/bold]"))
        
        self.console.print("\nRotate user agents to avoid detection and blocking.\n")
        
        # Get some user agents
        user_agents = []
        for _ in range(5):
            ua = self.engine._get_random_user_agent()
            if ua not in user_agents:
                user_agents.append(ua)
        
        self.console.print("[bold]Sample user agents:[/bold]")
        for i, ua in enumerate(user_agents, 1):
            self.console.print(f"{i}. {ua[:80]}...")
        
        # Show usage
        code = '''
# Enable random user agents
options = ScanOptions(
    random_user_agents=True,  # Rotate user agents
    threads=10
)

# Each request will use a different user agent
'''
        self.console.print("\n[bold]Usage Example:[/bold]")
        self.console.print(Syntax(code, "python"))
    
    async def demo_full_scan(self):
        """Demo full scan with all features"""
        self.console.print(Panel("[bold]Full Scan Demo[/bold]"))
        
        self.console.print("\nThis demonstrates a scan using multiple features together.\n")
        
        # Get target URL
        target = Prompt.ask("Enter target URL", default="http://example.com")
        
        # Demo configuration
        wordlist = [
            'admin.%EXT%',
            'config.%EXT%',
            'backup',
            'login',
            'api',
            'test'
        ]
        
        options = ScanOptions(
            extensions=['php', 'html', 'asp'],
            extension_tag='%EXT%',
            detect_wildcards=True,
            crawl=True,
            random_user_agents=True,
            threads=5,
            timeout=10,
            exclude_status_codes=[404]
        )
        
        self.console.print("\n[bold]Scan Configuration:[/bold]")
        config_table = Table(show_header=False, box=None)
        config_table.add_column("Setting", style="cyan")
        config_table.add_column("Value")
        
        config_table.add_row("Target", target)
        config_table.add_row("Wordlist entries", str(len(wordlist)))
        config_table.add_row("Extensions", ', '.join(options.extensions))
        config_table.add_row("Wildcard detection", "Enabled" if options.detect_wildcards else "Disabled")
        config_table.add_row("Crawling", "Enabled" if options.crawl else "Disabled")
        config_table.add_row("Random user agents", "Enabled" if options.random_user_agents else "Disabled")
        config_table.add_row("Threads", str(options.threads))
        
        self.console.print(config_table)
        
        if Confirm.ask("\nRun the demo scan?"):
            self.console.print("\n[yellow]Scanning... (this is a demo, results may be limited)[/yellow]\n")
            
            try:
                # Show what would happen
                paths = self.engine._generate_paths(wordlist, options)
                self.console.print(f"Generated {len(paths)} paths to scan")
                self.console.print(f"Sample paths: {', '.join(paths[:5])}...")
                
                # Note: Actual scanning would happen here
                # results = await self.engine.scan_target(target, wordlist, options)
                
                self.console.print("\n[green]✅ Demo scan configuration complete![/green]")
                self.console.print("\nIn a real scan, this would:")
                self.console.print("• Check for wildcard responses first")
                self.console.print("• Scan all generated paths with random user agents")
                self.console.print("• Crawl discovered content for more paths")
                self.console.print("• Filter results using blacklists")
                
            except Exception as e:
                self.console.print(f"\n[red]Error: {e}[/red]")


async def main():
    """Main demo runner"""
    console.print(Panel.fit(
        "[bold]Dirsearch Migrated Features Demo[/bold]\n"
        "Interactive demonstration of new features",
        border_style="cyan"
    ))
    
    demo = FeatureDemo()
    await demo.setup()
    
    try:
        while True:
            choice = demo.show_menu()
            
            if choice == "0":
                break
            elif choice == "1":
                await demo.demo_wildcard_detection()
            elif choice == "2":
                demo.demo_extension_tags()
            elif choice == "3":
                demo.demo_authentication()
            elif choice == "4":
                await demo.demo_crawling()
            elif choice == "5":
                demo.demo_blacklists()
            elif choice == "6":
                demo.demo_user_agents()
            elif choice == "7":
                await demo.demo_full_scan()
            
            if choice != "0":
                input("\nPress Enter to continue...")
    
    finally:
        await demo.cleanup()
        console.print("\n[green]Thank you for testing the migrated features![/green]")


if __name__ == "__main__":
    asyncio.run(main())