#!/usr/bin/env python3
"""
Test file for dirsearch-mcp
Demonstrates various ways to use the scanner with different options
"""
import asyncio
import sys
from pathlib import Path
from typing import List, Dict, Any
import json
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.dirsearch_engine import DirsearchEngine, ScanOptions, ScanRequest, ScanResult
from src.utils.logger import LoggerSetup
from src.utils.reporter import ReportGenerator
from src.core.mcp_coordinator import MCPCoordinator
from src.config.settings import Settings


class DirsearchTester:
    """Test class for dirsearch-mcp functionality"""
    
    def __init__(self):
        # Initialize components
        LoggerSetup.initialize()
        self.logger = LoggerSetup.get_logger(__name__)
        self.settings = Settings()
        self.engine = DirsearchEngine(settings=self.settings, logger=self.logger)
        self.reporter = ReportGenerator()
        self.mcp = MCPCoordinator(self.settings)
        
    async def test_basic_scan(self, target: str):
        """Test 1: Basic scan with default options"""
        print("\n" + "="*60)
        print("TEST 1: Basic Scan with Default Options")
        print("="*60)
        
        # Simple wordlist
        wordlist = [
            "admin", "login", "dashboard", "api", "config",
            "backup", "test", "dev", "staging", "old",
            ".git", ".env", "robots.txt", "sitemap.xml"
        ]
        
        # Default options
        options = ScanOptions()
        
        print(f"Target: {target}")
        print(f"Wordlist: {len(wordlist)} paths")
        print(f"Threads: {options.threads}")
        print(f"Timeout: {options.timeout}s")
        
        # Run scan
        results = await self._run_scan(target, wordlist, options)
        self._print_results(results)
        
        return results
        
    async def test_advanced_scan(self, target: str):
        """Test 2: Advanced scan with custom options"""
        print("\n" + "="*60)
        print("TEST 2: Advanced Scan with Custom Options")
        print("="*60)
        
        # Extended wordlist
        wordlist = self._load_wordlist("wordlists/common.txt")
        if not wordlist:
            wordlist = self._get_extended_wordlist()
            
        # Advanced options
        options = ScanOptions(
            threads=20,                          # More threads
            timeout=15,                          # Longer timeout
            delay=0.1,                          # Small delay between requests
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            follow_redirects=False,              # Don't follow redirects
            recursive=True,                      # Enable recursive scanning
            recursion_depth=2,                   # Scan 2 levels deep
            extensions=[".php", ".bak", ".old"], # Check these extensions
            exclude_status_codes=[404, 400],    # Exclude these status codes
            include_status_codes=None,           # Include all other codes
            detect_wildcards=True,               # Detect wildcard responses
            crawl=True,                          # Enable content crawling
            max_retries=2                        # Retry failed requests
        )
        
        print(f"Target: {target}")
        print(f"Wordlist: {len(wordlist)} paths")
        print(f"Configuration:")
        print(f"  - Threads: {options.threads}")
        print(f"  - Recursive: {options.recursive} (depth: {options.recursion_depth})")
        print(f"  - Extensions: {options.extensions}")
        print(f"  - Wildcard detection: {options.detect_wildcards}")
        print(f"  - Content crawling: {options.crawl}")
        
        # Run scan
        results = await self._run_scan(target, wordlist, options)
        self._print_results(results)
        
        return results
        
    async def test_with_mcp_intelligence(self, target: str):
        """Test 3: Scan with MCP intelligence"""
        print("\n" + "="*60)
        print("TEST 3: Intelligent Scan with MCP Coordinator")
        print("="*60)
        
        # Analyze target with MCP
        print("Analyzing target with MCP...")
        target_info = await self.mcp.analyze_target(target)
        
        print(f"Target Analysis:")
        print(f"  - Server: {target_info.server_type}")
        print(f"  - Technologies: {', '.join(target_info.technology_stack)}")
        print(f"  - CMS: {target_info.detected_cms or 'None detected'}")
        
        # Generate optimized scan plan
        scan_plan = await self.mcp.generate_scan_plan(target_info)
        
        # Get recommended wordlist from MCP
        wordlist = []
        for task in scan_plan:
            if hasattr(task, 'wordlist'):
                wordlist.extend(task.wordlist)
        
        if not wordlist:
            wordlist = self._get_extended_wordlist()
            
        # MCP-optimized options
        options = ScanOptions(
            threads=15,
            timeout=10,
            recursive=True,
            recursion_depth=3,
            detect_wildcards=True,
            crawl=True,
            user_agent=self._get_random_user_agent()
        )
        
        print(f"\nMCP-optimized scan configuration:")
        print(f"  - Wordlist: {len(set(wordlist))} unique paths")
        print(f"  - Threads: {options.threads}")
        print(f"  - Intelligence mode: {self.mcp.intelligence_mode}")
        
        # Run scan
        results = await self._run_scan(target, list(set(wordlist)), options)
        self._print_results(results)
        
        # Get insights
        insights = self.engine.get_scan_insights()
        self._print_insights(insights)
        
        return results
        
    async def test_with_authentication(self, target: str):
        """Test 4: Scan with authentication"""
        print("\n" + "="*60)
        print("TEST 4: Scan with Authentication Headers")
        print("="*60)
        
        wordlist = ["admin", "api", "user", "profile", "settings", "logout"]
        
        # Options with authentication
        options = ScanOptions(
            threads=5,
            timeout=10,
            headers={
                "Authorization": "Bearer YOUR_TOKEN_HERE",
                "X-API-Key": "your-api-key"
            },
            cookies={
                "session": "your-session-cookie",
                "auth": "your-auth-cookie"
            }
        )
        
        print(f"Target: {target}")
        print(f"Authentication: Custom headers and cookies")
        
        # Run scan
        results = await self._run_scan(target, wordlist, options)
        self._print_results(results)
        
        return results
        
    async def test_with_proxy(self, target: str):
        """Test 5: Scan through proxy"""
        print("\n" + "="*60)
        print("TEST 5: Scan Through Proxy")
        print("="*60)
        
        wordlist = ["admin", "api", "config", "backup"]
        
        # Options with proxy
        options = ScanOptions(
            threads=3,  # Fewer threads for proxy
            timeout=20,  # Longer timeout for proxy
            proxy="http://127.0.0.1:8080",  # Proxy URL
            verify_ssl=False  # Disable SSL verification for proxy
        )
        
        print(f"Target: {target}")
        print(f"Proxy: {options.proxy}")
        print("Note: Make sure your proxy is running!")
        
        try:
            results = await self._run_scan(target, wordlist, options)
            self._print_results(results)
        except Exception as e:
            print(f"Error: {e}")
            print("Make sure your proxy is configured correctly")
            results = []
            
        return results
        
    async def test_specific_extensions(self, target: str):
        """Test 6: Scan for specific file extensions"""
        print("\n" + "="*60)
        print("TEST 6: Scan for Specific File Extensions")
        print("="*60)
        
        # Base paths without extensions
        wordlist = ["index", "config", "database", "backup", "admin", "login"]
        
        # Options with specific extensions
        options = ScanOptions(
            threads=10,
            timeout=10,
            extensions=[".php", ".asp", ".aspx", ".jsp", ".bak", ".old", ".txt", ".log"],
            force_extensions=True  # Force adding extensions to all paths
        )
        
        print(f"Target: {target}")
        print(f"Base paths: {len(wordlist)}")
        print(f"Extensions: {options.extensions}")
        print(f"Total paths to scan: {len(wordlist) * len(options.extensions)}")
        
        # Run scan
        results = await self._run_scan(target, wordlist, options)
        self._print_results(results)
        
        return results
        
    async def test_subdirectory_scan(self, target: str):
        """Test 7: Scan specific subdirectory"""
        print("\n" + "="*60)
        print("TEST 7: Subdirectory Scan")
        print("="*60)
        
        # Add subdirectory to target
        subdirectory = "admin"
        sub_target = f"{target.rstrip('/')}/{subdirectory}/"
        
        wordlist = ["users", "settings", "logs", "config", "dashboard", "profile"]
        
        options = ScanOptions(
            threads=10,
            timeout=10,
            recursive=False  # Don't go deeper
        )
        
        print(f"Target subdirectory: {sub_target}")
        print(f"Wordlist: {len(wordlist)} paths")
        
        # Run scan
        results = await self._run_scan(sub_target, wordlist, options)
        self._print_results(results)
        
        return results
        
    async def test_custom_status_codes(self, target: str):
        """Test 8: Scan with custom status code filtering"""
        print("\n" + "="*60)
        print("TEST 8: Custom Status Code Filtering")
        print("="*60)
        
        wordlist = self._get_basic_wordlist()
        
        # Only look for specific status codes
        options = ScanOptions(
            threads=10,
            timeout=10,
            include_status_codes=[200, 301, 302, 401, 403],  # Only these codes
            exclude_status_codes=[]  # Don't exclude any
        )
        
        print(f"Target: {target}")
        print(f"Looking for status codes: {options.include_status_codes}")
        
        # Run scan
        results = await self._run_scan(target, wordlist, options)
        self._print_results(results)
        
        return results
        
    async def test_with_scan_request(self, target: str):
        """Test 9: Using ScanRequest object"""
        print("\n" + "="*60)
        print("TEST 9: Using ScanRequest Object")
        print("="*60)
        
        # Create scan request
        scan_request = ScanRequest(
            base_url=target,
            wordlist="wordlists/common.txt",
            wordlist_type="common",
            extensions=[".php", ".html"],
            threads=15,
            timeout=10,
            recursive=True,
            recursion_depth=2,
            exclude_status="404,400",
            include_status=None,
            user_agent="DirsearchTester/1.0"
        )
        
        print(f"Target: {scan_request.base_url}")
        print(f"Wordlist: {scan_request.wordlist}")
        print(f"Extensions: {scan_request.extensions}")
        
        # Execute scan
        scan_response = await self.engine.execute_scan(scan_request)
        
        print(f"\nScan completed in {scan_response.duration:.2f} seconds")
        print(f"Total requests: {scan_response.statistics['total_requests']}")
        print(f"Found paths: {scan_response.statistics['found_paths']}")
        
        # Print results
        for result in scan_response.results[:10]:
            print(f"  [{result['status']}] {result['path']} ({result['size']} bytes)")
            
        return scan_response.results
        
    async def test_export_results(self, target: str):
        """Test 10: Scan and export results"""
        print("\n" + "="*60)
        print("TEST 10: Scan and Export Results")
        print("="*60)
        
        wordlist = self._get_basic_wordlist()
        options = ScanOptions(threads=10, timeout=10)
        
        print(f"Target: {target}")
        print("Running scan...")
        
        # Run scan
        results = await self._run_scan(target, wordlist, options)
        
        if results:
            # Generate timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Prepare scan data
            scan_data = {
                "target": target,
                "scan_time": datetime.now().isoformat(),
                "total_paths_scanned": len(wordlist),
                "results_found": len(results),
                "results": [
                    {
                        "url": r.url,
                        "path": r.path,
                        "status_code": r.status_code,
                        "size": r.size,
                        "content_type": r.content_type,
                        "is_directory": r.is_directory
                    }
                    for r in results
                ]
            }
            
            # Export to JSON
            json_file = f"test_results_{timestamp}.json"
            with open(json_file, 'w') as f:
                json.dump(scan_data, f, indent=2)
            print(f"\nResults exported to: {json_file}")
            
            # Generate HTML report
            html_file = f"test_report_{timestamp}.html"
            self.reporter.generate_html_report(scan_data, html_file)
            print(f"HTML report generated: {html_file}")
            
        return results
        
    # Helper methods
    
    async def _run_scan(self, target: str, wordlist: List[str], options: ScanOptions) -> List[ScanResult]:
        """Run scan and handle errors"""
        try:
            print("\nScanning...")
            results = await self.engine.scan_target(target, wordlist, options)
            print(f"Scan completed. Found {len(results)} results.")
            return results
        except Exception as e:
            print(f"Scan error: {e}")
            return []
            
    def _print_results(self, results: List[ScanResult]):
        """Print scan results"""
        if not results:
            print("No results found.")
            return
            
        print("\nResults:")
        # Group by status code
        by_status = {}
        for r in results:
            if r.status_code not in by_status:
                by_status[r.status_code] = []
            by_status[r.status_code].append(r)
            
        # Print grouped results
        for status in sorted(by_status.keys()):
            print(f"\n[{status}] Status Code:")
            for r in by_status[status][:5]:  # Show first 5 of each
                print(f"  - {r.path} ({r.size} bytes)")
            if len(by_status[status]) > 5:
                print(f"  ... and {len(by_status[status]) - 5} more")
                
    def _print_insights(self, insights: Dict[str, Any]):
        """Print scan insights"""
        print("\nScan Insights:")
        
        if insights.get('important_paths'):
            print("\nImportant paths found:")
            for path in insights['important_paths'][:5]:
                print(f"  - {path}")
                
        if insights.get('technology_hints'):
            print(f"\nDetected technologies: {', '.join(insights['technology_hints'])}")
            
        if insights.get('risk_assessment'):
            risk = insights['risk_assessment']
            print(f"\nRisk Assessment: {risk['level']} (Score: {risk['score']}/100)")
            for r in risk.get('risks', []):
                print(f"  - {r}")
                
        if insights.get('recommendations'):
            print("\nRecommendations:")
            for rec in insights['recommendations']:
                print(f"  - {rec}")
                
    def _load_wordlist(self, path: str) -> List[str]:
        """Load wordlist from file"""
        try:
            wordlist_path = Path(path)
            if not wordlist_path.is_absolute():
                wordlist_path = Path(self.settings.paths['wordlists']['base']) / path
                
            if wordlist_path.exists():
                with open(wordlist_path, 'r') as f:
                    return [line.strip() for line in f if line.strip() and not line.startswith('#')]
        except:
            pass
        return []
        
    def _get_basic_wordlist(self) -> List[str]:
        """Get basic wordlist"""
        return [
            "admin", "login", "dashboard", "api", "config",
            "backup", "test", "dev", "staging", "old",
            "user", "users", "profile", "account", "settings",
            ".git", ".env", "robots.txt", "sitemap.xml", ".htaccess"
        ]
        
    def _get_extended_wordlist(self) -> List[str]:
        """Get extended wordlist"""
        basic = self._get_basic_wordlist()
        extended = [
            "administrator", "wp-admin", "phpmyadmin", "cpanel",
            "console", "manager", "portal", "system", "panel",
            "api/v1", "api/v2", "rest", "graphql", "swagger",
            "backup.sql", "db.sql", "dump.sql", "config.php",
            "uploads", "upload", "files", "documents", "media",
            "assets", "static", "public", "private", "secure",
            "tmp", "temp", "cache", "logs", "log", "debug"
        ]
        return basic + extended
        
    def _get_random_user_agent(self) -> str:
        """Get random user agent"""
        agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        ]
        import random
        return random.choice(agents)


async def main():
    """Main test runner"""
    tester = DirsearchTester()
    
    # Get target from command line or use default
    if len(sys.argv) > 1:
        target = sys.argv[1]
    else:
        target = "http://testphp.vulnweb.com"
        
    print(f"\n{'='*60}")
    print(f"DIRSEARCH-MCP TEST SUITE")
    print(f"Target: {target}")
    print(f"{'='*60}")
    
    # Run tests based on command line argument
    if len(sys.argv) > 2:
        test_num = sys.argv[2]
        if test_num == "1":
            await tester.test_basic_scan(target)
        elif test_num == "2":
            await tester.test_advanced_scan(target)
        elif test_num == "3":
            await tester.test_with_mcp_intelligence(target)
        elif test_num == "4":
            await tester.test_with_authentication(target)
        elif test_num == "5":
            await tester.test_with_proxy(target)
        elif test_num == "6":
            await tester.test_specific_extensions(target)
        elif test_num == "7":
            await tester.test_subdirectory_scan(target)
        elif test_num == "8":
            await tester.test_custom_status_codes(target)
        elif test_num == "9":
            await tester.test_with_scan_request(target)
        elif test_num == "10":
            await tester.test_export_results(target)
        else:
            print("Invalid test number. Running all tests...")
            await run_all_tests(tester, target)
    else:
        # Run all tests
        await run_all_tests(tester, target)
        
    # Cleanup
    await tester.engine.close()
    print("\n✅ All tests completed!")


async def run_all_tests(tester: DirsearchTester, target: str):
    """Run all tests"""
    tests = [
        tester.test_basic_scan,
        tester.test_advanced_scan,
        tester.test_with_mcp_intelligence,
        # tester.test_with_authentication,  # Skip - needs real auth
        # tester.test_with_proxy,  # Skip - needs proxy
        tester.test_specific_extensions,
        tester.test_subdirectory_scan,
        tester.test_custom_status_codes,
        tester.test_with_scan_request,
        tester.test_export_results
    ]
    
    for i, test in enumerate(tests, 1):
        try:
            await test(target)
        except Exception as e:
            print(f"\nTest {i} failed: {e}")
            import traceback
            traceback.print_exc()
            
        # Small delay between tests
        await asyncio.sleep(1)


if __name__ == "__main__":
    print("""
Usage:
    python test.py [target_url] [test_number]
    
Examples:
    python test.py                                    # Run all tests on default target
    python test.py http://example.com                 # Run all tests on example.com
    python test.py http://example.com 1              # Run test 1 on example.com
    python test.py http://example.com 3              # Run MCP intelligence test
    
Available tests:
    1  - Basic scan with default options
    2  - Advanced scan with custom options
    3  - Intelligent scan with MCP coordinator
    4  - Scan with authentication headers
    5  - Scan through proxy
    6  - Scan for specific file extensions
    7  - Subdirectory scan
    8  - Custom status code filtering
    9  - Using ScanRequest object
    10 - Scan and export results
    """)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()