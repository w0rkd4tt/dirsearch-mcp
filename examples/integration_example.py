#!/usr/bin/env python3
"""
Example: Using Dirsearch MCP as a library with integration features
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.integration import DirsearchMCP, ScanOptions, Plugin
from src.integration.plugins import WappalyzerPlugin


# Example 1: Basic usage
async def basic_example():
    """Basic scanning example"""
    print("=== Basic Scanning Example ===\n")
    
    # Initialize Dirsearch MCP
    dirsearch = DirsearchMCP()
    await dirsearch.initialize()
    
    # Configure scan options
    options = ScanOptions(
        wordlist="common.txt",
        extensions=["php", "html", "js"],
        threads=20,
        timeout=10
    )
    
    # Run scan
    target = "https://example.com"
    print(f"Scanning {target}...")
    
    scan_data = await dirsearch.scan(target, options)
    
    # Display results
    print(f"\nScan completed in {scan_data.duration:.2f} seconds")
    print(f"Total findings: {scan_data.total_findings}")
    print(f"Successful paths: {len(scan_data.successful_findings)}")
    
    # Show some findings
    print("\nTop findings:")
    for result in scan_data.successful_findings[:5]:
        print(f"  [{result.status}] {result.path} - {result.size} bytes")


# Example 2: Using event hooks
async def event_hooks_example():
    """Example with event hooks"""
    print("\n=== Event Hooks Example ===\n")
    
    dirsearch = DirsearchMCP()
    
    # Register event handlers
    findings_count = 0
    
    def on_finding(data):
        nonlocal findings_count
        findings_count += 1
        if data['status'] == 200:
            print(f"[FOUND] {data['path']} - {data['size']} bytes")
    
    def on_progress(data):
        percentage = data.get('percentage', 0)
        print(f"Progress: {percentage:.1f}% - {data.get('current_path', '')}", end='\r')
    
    async def on_complete(scan_data):
        print(f"\n\nScan completed! Found {findings_count} paths")
        print(f"Technologies detected: {', '.join(scan_data.target_info.technology_stack)}")
    
    # Register handlers
    dirsearch.on_finding(on_finding)
    dirsearch.on_progress(on_progress)
    dirsearch.on_scan_completed(on_complete)
    
    await dirsearch.initialize()
    
    # Run scan
    options = ScanOptions(threads=10, extensions=["php", "html"])
    await dirsearch.scan("https://example.com", options)


# Example 3: Using plugins
async def plugin_example():
    """Example with Wappalyzer plugin"""
    print("\n=== Plugin Example ===\n")
    
    dirsearch = DirsearchMCP()
    
    # Register Wappalyzer plugin
    dirsearch.register_plugin(WappalyzerPlugin, {
        'cache_enabled': True,
        'timeout': 15
    })
    
    await dirsearch.initialize()
    
    # The plugin will automatically enhance target analysis
    target = "https://wordpress.org"
    print(f"Analyzing {target} with technology detection...\n")
    
    target_info = await dirsearch.analyze_target(target)
    
    print(f"Domain: {target_info.domain}")
    print(f"Server: {target_info.server_type}")
    print(f"CMS: {target_info.detected_cms}")
    print(f"Technologies: {', '.join(target_info.technology_stack)}")
    
    # Run scan with technology-aware configuration
    options = ScanOptions(use_mcp=True)
    scan_data = await dirsearch.scan(target, options)
    
    print(f"\nScan completed with {scan_data.total_findings} findings")


# Example 4: Custom plugin
class CustomPlugin(Plugin):
    """Example custom plugin"""
    
    name = "custom_plugin"
    version = "1.0.0"
    description = "Custom plugin example"
    
    async def initialize(self):
        """Initialize the plugin"""
        self.log("Custom plugin initialized")
        self.interesting_paths = []
    
    async def on_finding(self, finding):
        """Process each finding"""
        # Look for interesting paths
        interesting_keywords = ['admin', 'config', 'backup', 'api', 'test']
        path = finding.get('path', '').lower()
        
        for keyword in interesting_keywords:
            if keyword in path:
                self.interesting_paths.append(finding)
                self.log(f"Interesting path found: {finding['path']}")
                break
    
    async def on_scan_completed(self, scan_data):
        """Report interesting findings"""
        if self.interesting_paths:
            self.log(f"\n=== Interesting Paths Report ===")
            self.log(f"Found {len(self.interesting_paths)} interesting paths:")
            for finding in self.interesting_paths:
                self.log(f"  [{finding['status']}] {finding['path']}")


async def custom_plugin_example():
    """Example with custom plugin"""
    print("\n=== Custom Plugin Example ===\n")
    
    dirsearch = DirsearchMCP()
    
    # Register custom plugin
    dirsearch.register_plugin(CustomPlugin)
    
    await dirsearch.initialize()
    
    # Run scan
    options = ScanOptions(
        wordlist="common.txt",
        extensions=["php", "bak", "config", "sql"],
        threads=15
    )
    
    await dirsearch.scan("https://example.com", options)


# Example 5: Export/Import data
async def data_exchange_example():
    """Example of data import/export"""
    print("\n=== Data Exchange Example ===\n")
    
    async with DirsearchMCP() as dirsearch:
        # Run scan
        options = ScanOptions(threads=10)
        scan_data = await dirsearch.scan("https://example.com", options)
        
        # Export to different formats
        print("Exporting scan data...")
        
        # JSON export
        json_file = "scan_results.json"
        scan_data.export_to_file(json_file)
        print(f"Exported to {json_file}")
        
        # Generate reports
        reports = await dirsearch.generate_report(
            scan_data,
            output_dir="./reports",
            formats=["json", "html", "markdown"]
        )
        
        print("\nGenerated reports:")
        for fmt, path in reports.items():
            print(f"  {fmt}: {path}")
        
        # Import data
        print("\nImporting scan data...")
        imported_data = scan_data.import_from_file(json_file)
        print(f"Imported {imported_data.total_findings} findings")


# Example 6: Integration with external tools
async def external_integration_example():
    """Example of integrating with external tools"""
    print("\n=== External Tool Integration Example ===\n")
    
    from src.integration.data_formats import ExchangeFormat
    
    dirsearch = DirsearchMCP()
    await dirsearch.initialize()
    
    # Run scan
    scan_data = await dirsearch.scan("https://example.com")
    
    # Create exchange format for external tools
    exchange = ExchangeFormat(
        scan_data=scan_data,
        metadata={
            'scan_type': 'directory_enumeration',
            'tool_version': '1.0.0',
            'custom_field': 'custom_value'
        }
    )
    
    # Export to different formats
    print("Exporting for external tools:")
    
    # JSON (for most tools)
    with open('export.json', 'w') as f:
        f.write(exchange.to_json())
    print("  - Exported JSON: export.json")
    
    # XML (for tools that prefer XML)
    with open('export.xml', 'w') as f:
        f.write(exchange.to_xml())
    print("  - Exported XML: export.xml")
    
    # CSV (for spreadsheet analysis)
    with open('export.csv', 'w') as f:
        f.write(exchange.to_csv())
    print("  - Exported CSV: export.csv")


# Main execution
async def main():
    """Run all examples"""
    examples = [
        ("Basic Scanning", basic_example),
        ("Event Hooks", event_hooks_example),
        ("Wappalyzer Plugin", plugin_example),
        ("Custom Plugin", custom_plugin_example),
        ("Data Exchange", data_exchange_example),
        ("External Integration", external_integration_example)
    ]
    
    print("Dirsearch MCP Integration Examples")
    print("==================================\n")
    
    for i, (name, func) in enumerate(examples, 1):
        print(f"\n{i}. {name}")
        print("-" * 40)
        
        try:
            await func()
        except Exception as e:
            print(f"Error in {name}: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "=" * 50)
        
        if i < len(examples):
            input("\nPress Enter to continue to next example...")


if __name__ == "__main__":
    # Run examples
    asyncio.run(main())