#!/usr/bin/env python3
"""
Practical examples of using dirsearch-mcp
Real-world scenarios and use cases
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.dirsearch_engine import DirsearchEngine, ScanOptions, ScanRequest
from src.utils.logger import LoggerSetup
from src.utils.reporter import ReportGenerator
from src.core.mcp_coordinator import MCPCoordinator
from src.config.settings import Settings


class DirsearchExamples:
    """Practical examples for dirsearch-mcp"""
    
    def __init__(self):
        LoggerSetup.initialize()
        self.logger = LoggerSetup.get_logger(__name__)
        self.settings = Settings()
        self.engine = DirsearchEngine(settings=self.settings, logger=self.logger)
        self.reporter = ReportGenerator()
        self.mcp = MCPCoordinator(self.settings)
        
    async def example_wordpress_scan(self):
        """Example: Scan WordPress site"""
        print("\n" + "="*60)
        print("EXAMPLE: WordPress Site Scan")
        print("="*60)
        
        target = "http://testphp.vulnweb.com"
        
        # WordPress-specific paths
        wordlist = [
            # Core WordPress
            "wp-admin", "wp-content", "wp-includes", "wp-login.php",
            "wp-config.php", "wp-config.php.bak", "wp-config.old",
            "xmlrpc.php", "wp-json", "wp-cron.php",
            
            # Common plugins paths
            "wp-content/plugins", "wp-content/uploads", "wp-content/themes",
            "wp-content/uploads/2023", "wp-content/uploads/2024",
            
            # Backup files
            "wp-config.php~", "wp-config.txt", ".wp-config.php.swp",
            "wordpress.sql", "backup.sql", "database.sql",
            
            # Admin areas
            "wp-admin/admin-ajax.php", "wp-admin/includes",
            "wp-admin/upload.php", "wp-admin/post.php"
        ]
        
        options = ScanOptions(
            threads=15,
            timeout=10,
            recursive=True,
            recursion_depth=2,
            user_agent="Mozilla/5.0 (compatible; WP-Scanner)",
            detect_wildcards=True
        )
        
        print(f"Target: {target}")
        print(f"Scanning for WordPress-specific paths...")
        
        results = await self.engine.scan_target(target, wordlist, options)
        
        # Analyze results
        wp_found = False
        for r in results:
            if "wp-" in r.path and r.status_code in [200, 301, 302, 403]:
                if not wp_found:
                    print("\n✓ WordPress detected!")
                    wp_found = True
                print(f"  [{r.status_code}] {r.path}")
                
        if not wp_found:
            print("\n✗ No WordPress indicators found")
            
        return results
        
    async def example_api_discovery(self):
        """Example: API endpoint discovery"""
        print("\n" + "="*60)
        print("EXAMPLE: API Endpoint Discovery")
        print("="*60)
        
        target = "http://testphp.vulnweb.com"
        
        # API-focused wordlist
        wordlist = [
            # API versions
            "api", "api/v1", "api/v2", "api/v3", "v1", "v2", "rest",
            
            # Common endpoints
            "api/users", "api/user", "api/auth", "api/login", "api/logout",
            "api/register", "api/token", "api/refresh", "api/verify",
            
            # Documentation
            "api/docs", "api/swagger", "swagger.json", "api-docs",
            "api/documentation", "api/spec", "openapi.json",
            
            # GraphQL
            "graphql", "graphiql", "graphql/schema", "playground",
            
            # Health checks
            "api/health", "api/status", "api/ping", "health", "status",
            
            # Admin endpoints
            "api/admin", "api/config", "api/settings", "api/debug"
        ]
        
        options = ScanOptions(
            threads=20,
            timeout=10,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json"
            },
            follow_redirects=False
        )
        
        print(f"Target: {target}")
        print(f"Looking for API endpoints...")
        
        results = await self.engine.scan_target(target, wordlist, options)
        
        # Analyze API findings
        api_endpoints = []
        for r in results:
            if r.status_code in [200, 301, 302, 401] and ("api" in r.path or "v1" in r.path or "v2" in r.path):
                api_endpoints.append(r)
                
        if api_endpoints:
            print(f"\n✓ Found {len(api_endpoints)} potential API endpoints:")
            for ep in api_endpoints:
                print(f"  [{ep.status_code}] {ep.path}")
                if ep.status_code == 401:
                    print(f"    → Requires authentication")
        else:
            print("\n✗ No API endpoints found")
            
        return results
        
    async def example_security_audit(self):
        """Example: Security-focused scan"""
        print("\n" + "="*60)
        print("EXAMPLE: Security Audit Scan")
        print("="*60)
        
        target = "http://testphp.vulnweb.com"
        
        # Security-focused wordlist
        wordlist = [
            # Sensitive files
            ".git", ".git/config", ".git/HEAD", ".gitignore",
            ".svn", ".svn/entries", ".env", ".env.local", ".env.prod",
            ".htaccess", ".htpasswd", ".DS_Store",
            
            # Backups
            "backup.zip", "backup.tar.gz", "site.zip", "www.zip",
            "database.sql", "dump.sql", "backup.sql", "db.sql",
            "config.php.bak", "index.php.old", "admin.php~",
            
            # Configuration
            "config.php", "configuration.php", "settings.php",
            "database.php", "db.php", "connect.php",
            "web.config", "app.config", "config.xml",
            
            # Logs and debug
            "error.log", "access.log", "debug.log", "app.log",
            "errors.txt", "debug.txt", "phpinfo.php", "info.php",
            
            # Admin panels
            "admin", "administrator", "phpmyadmin", "pma",
            "adminer.php", "mysql", "myadmin", "dbadmin"
        ]
        
        options = ScanOptions(
            threads=10,
            timeout=15,
            recursive=True,
            recursion_depth=2,
            detect_wildcards=True,
            extensions=[".bak", ".old", ".tmp", ".swp", ".log", ".sql"]
        )
        
        print(f"Target: {target}")
        print(f"Running security audit...")
        
        results = await self.engine.scan_target(target, wordlist, options)
        
        # Categorize findings
        critical_findings = []
        high_findings = []
        medium_findings = []
        
        for r in results:
            if r.status_code in [200, 301, 302]:
                # Critical findings
                if any(x in r.path for x in ['.git', '.env', '.sql', 'config.php', 'phpmyadmin']):
                    critical_findings.append(r)
                # High findings
                elif any(x in r.path for x in ['.bak', '.old', 'backup', 'admin']):
                    high_findings.append(r)
                # Medium findings
                elif any(x in r.path for x in ['.log', 'debug', 'test']):
                    medium_findings.append(r)
                    
        # Print security report
        print("\n🔒 SECURITY AUDIT RESULTS")
        
        if critical_findings:
            print(f"\n🚨 CRITICAL ({len(critical_findings)} found):")
            for f in critical_findings:
                print(f"  [{f.status_code}] {f.path} - IMMEDIATE ACTION REQUIRED")
                
        if high_findings:
            print(f"\n⚠️  HIGH ({len(high_findings)} found):")
            for f in high_findings:
                print(f"  [{f.status_code}] {f.path} - Should be addressed")
                
        if medium_findings:
            print(f"\n⚡ MEDIUM ({len(medium_findings)} found):")
            for f in medium_findings:
                print(f"  [{f.status_code}] {f.path} - Review recommended")
                
        if not (critical_findings or high_findings or medium_findings):
            print("\n✓ No significant security issues found")
            
        return results
        
    async def example_comprehensive_scan(self):
        """Example: Comprehensive scan with all features"""
        print("\n" + "="*60)
        print("EXAMPLE: Comprehensive Scan with MCP")
        print("="*60)
        
        target = "http://testphp.vulnweb.com"
        
        # Analyze target first
        print("Phase 1: Target analysis with MCP...")
        target_info = await self.mcp.analyze_target(target)
        
        print(f"\nTarget Information:")
        print(f"  Server: {target_info.server_type}")
        print(f"  Technologies: {', '.join(target_info.technology_stack) or 'Unknown'}")
        print(f"  CMS: {target_info.detected_cms or 'None detected'}")
        
        # Generate optimized scan plan
        print("\nPhase 2: Generating scan plan...")
        scan_plan = await self.mcp.generate_scan_plan(target_info)
        
        # Combine wordlists from scan plan
        all_paths = set()
        for task in scan_plan:
            if hasattr(task, 'wordlist'):
                all_paths.update(task.wordlist)
                
        # Add common paths if wordlist is too small
        if len(all_paths) < 50:
            common_paths = [
                "admin", "login", "api", "config", "backup",
                "uploads", "files", "data", "test", "debug",
                ".git", ".env", "robots.txt", "sitemap.xml"
            ]
            all_paths.update(common_paths)
            
        wordlist = list(all_paths)
        
        # Comprehensive options
        options = ScanOptions(
            threads=20,
            timeout=10,
            recursive=True,
            recursion_depth=3,
            extensions=[".php", ".bak", ".old", ".txt", ".log"],
            detect_wildcards=True,
            crawl=True,
            follow_redirects=False,
            user_agent="Mozilla/5.0 (compatible; SecurityAudit/1.0)"
        )
        
        print(f"\nPhase 3: Scanning with {len(wordlist)} paths...")
        
        # Progress tracking
        found_count = 0
        def on_result(result):
            nonlocal found_count
            if result.status_code in [200, 301, 302, 401, 403]:
                found_count += 1
                
        self.engine.set_result_callback(on_result)
        
        # Run scan
        start_time = datetime.now()
        results = await self.engine.scan_target(target, wordlist, options)
        scan_duration = (datetime.now() - start_time).total_seconds()
        
        # Get insights
        insights = self.engine.get_scan_insights()
        
        # Generate report
        print(f"\n📊 COMPREHENSIVE SCAN REPORT")
        print(f"{'='*50}")
        print(f"Target: {target}")
        print(f"Duration: {scan_duration:.2f} seconds")
        print(f"Total paths scanned: {len(wordlist)}")
        print(f"Results found: {len(results)}")
        print(f"Interesting findings: {found_count}")
        
        # Technology insights
        if insights.get('technology_hints'):
            print(f"\n🔧 Technologies Detected:")
            for tech in insights['technology_hints']:
                print(f"  • {tech}")
                
        # Risk assessment
        if insights.get('risk_assessment'):
            risk = insights['risk_assessment']
            print(f"\n⚠️  Risk Assessment: {risk['level']} (Score: {risk['score']}/100)")
            for r in risk.get('risks', []):
                print(f"  • {r}")
                
        # Important paths
        if insights.get('important_paths'):
            print(f"\n📁 Important Paths Found:")
            for path in insights['important_paths'][:10]:
                print(f"  • {path}")
                
        # Recommendations
        if insights.get('recommendations'):
            print(f"\n💡 Recommendations:")
            for i, rec in enumerate(insights['recommendations'], 1):
                print(f"  {i}. {rec}")
                
        # Export results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Prepare scan data for report
        scan_data = {
            "scan_info": {
                "target": target,
                "start_time": start_time.isoformat(),
                "duration": scan_duration,
                "total_paths": len(wordlist),
                "results_found": len(results)
            },
            "target_analysis": {
                "server": target_info.server_type,
                "technologies": target_info.technology_stack,
                "cms": target_info.detected_cms
            },
            "results": [
                {
                    "url": r.url,
                    "path": r.path,
                    "status": r.status_code,
                    "size": r.size,
                    "is_directory": r.is_directory
                }
                for r in results
            ],
            "insights": insights
        }
        
        # Generate reports
        report_base = f"comprehensive_scan_{timestamp}"
        
        # JSON report
        json_file = f"{report_base}.json"
        with open(json_file, 'w') as f:
            import json
            json.dump(scan_data, f, indent=2)
        print(f"\n📄 JSON report saved: {json_file}")
        
        # HTML report
        html_file = f"{report_base}.html"
        self.reporter.generate_html_report(scan_data, html_file)
        print(f"📄 HTML report saved: {html_file}")
        
        return results


async def main():
    """Main runner"""
    examples = DirsearchExamples()
    
    print("""
╔════════════════════════════════════════════════╗
║        DIRSEARCH-MCP PRACTICAL EXAMPLES        ║
╚════════════════════════════════════════════════╝

Choose an example:

1. WordPress site scan
2. API endpoint discovery
3. Security audit scan
4. Comprehensive scan with MCP intelligence

0. Exit
""")
    
    choice = input("Enter your choice (0-4): ").strip()
    
    try:
        if choice == "1":
            await examples.example_wordpress_scan()
        elif choice == "2":
            await examples.example_api_discovery()
        elif choice == "3":
            await examples.example_security_audit()
        elif choice == "4":
            await examples.example_comprehensive_scan()
        elif choice == "0":
            print("Exiting...")
        else:
            print("Invalid choice!")
            
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await examples.engine.close()
        

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()