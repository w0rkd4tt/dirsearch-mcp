# Dirsearch MCP Integration Guide

This guide explains how to integrate Dirsearch MCP with other tools and use it as a library in your projects.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Core API](#core-api)
3. [Event System](#event-system)
4. [Plugin Architecture](#plugin-architecture)
5. [Data Formats](#data-formats)
6. [Examples](#examples)
7. [Third-Party Integration](#third-party-integration)

## Quick Start

### Installation

```bash
pip install dirsearch-mcp
```

### Basic Usage

```python
from dirsearch_mcp import DirsearchMCP, ScanOptions

async def scan_target():
    # Initialize
    dirsearch = DirsearchMCP()
    await dirsearch.initialize()
    
    # Configure scan
    options = ScanOptions(
        threads=20,
        extensions=['php', 'html'],
        timeout=10
    )
    
    # Run scan
    scan_data = await dirsearch.scan("https://example.com", options)
    
    # Process results
    print(f"Found {scan_data.total_findings} paths")
    for result in scan_data.successful_findings:
        print(f"[{result.status}] {result.path}")
```

## Core API

### DirsearchMCP Class

The main integration class providing a clean API for external tools.

#### Initialization

```python
# Basic initialization
dirsearch = DirsearchMCP()

# With custom config file
dirsearch = DirsearchMCP(config_file="custom_config.json")

# Using context manager
async with DirsearchMCP() as dirsearch:
    # Automatically initializes and cleans up
    scan_data = await dirsearch.scan(target)
```

#### Core Methods

##### scan()
```python
async def scan(target: str, options: ScanOptions = None) -> ScanData
```
Performs a directory scan on the target.

##### analyze_target()
```python
async def analyze_target(url: str) -> TargetData
```
Analyzes a target URL to detect technologies and server information.

##### generate_report()
```python
async def generate_report(scan_data: ScanData, 
                         output_dir: str = "./reports",
                         formats: List[str] = ["json", "html", "markdown"]) -> Dict[str, str]
```
Generates reports in multiple formats.

#### Configuration Methods

##### set_mcp_mode()
```python
dirsearch.set_mcp_mode("ai")  # Options: 'auto', 'local', 'ai'
```

##### set_ai_credentials()
```python
dirsearch.set_ai_credentials("openai", "your-api-key", model="gpt-4")
```

##### configure()
```python
dirsearch.configure(
    threads=30,
    timeout=15,
    user_agent="Custom User Agent"
)
```

## Event System

Dirsearch MCP provides a comprehensive event system for real-time monitoring and integration.

### Available Events

- `SCAN_STARTED` - Fired when scan begins
- `SCAN_COMPLETED` - Fired when scan completes
- `TARGET_ANALYZED` - Fired after target analysis
- `FINDING_DISCOVERED` - Fired for each discovery
- `ERROR_OCCURRED` - Fired on errors
- `PROGRESS_UPDATE` - Fired for progress updates

### Registering Event Handlers

```python
# Method 1: Using convenience methods
dirsearch.on_finding(lambda data: print(f"Found: {data['path']}"))
dirsearch.on_progress(lambda data: print(f"Progress: {data['percentage']}%"))

# Method 2: Using += operator
from dirsearch_mcp import EventType

async def on_scan_complete(scan_data):
    print(f"Scan finished with {scan_data.total_findings} findings")

dirsearch.events[EventType.SCAN_COMPLETED] += on_scan_complete

# Method 3: One-time handlers
def once_handler(data):
    print("This runs only once")

dirsearch.events[EventType.SCAN_STARTED].once(once_handler)
```

### Async Event Handlers

```python
async def async_handler(finding):
    # Perform async operations
    await process_finding(finding)
    await notify_external_service(finding)

dirsearch.on_finding(async_handler)
```

## Plugin Architecture

### Creating a Plugin

```python
from dirsearch_mcp import Plugin

class MyPlugin(Plugin):
    name = "my_plugin"
    version = "1.0.0"
    description = "My custom plugin"
    author = "Your Name"
    
    async def initialize(self):
        """Initialize plugin resources"""
        self.log("Plugin initialized")
        
    async def on_finding(self, finding):
        """Process each finding"""
        if finding['status'] == 200:
            # Custom processing
            await self.process_finding(finding)
            
    async def on_scan_completed(self, scan_data):
        """Generate plugin report"""
        self.log(f"Scan completed: {scan_data.total_findings} findings")
```

### Registering Plugins

```python
# Register plugin class
dirsearch.register_plugin(MyPlugin, config={'option': 'value'})

# Load plugin from file
dirsearch.load_plugin("path/to/plugin.py")

# Load all plugins from directory
dirsearch.plugin_manager.load_plugins_from_directory("./plugins")
```

### Built-in Plugins

#### Wappalyzer Plugin
Detects technologies used by the target website.

```python
from dirsearch_mcp.plugins import WappalyzerPlugin

dirsearch.register_plugin(WappalyzerPlugin, {
    'cache_enabled': True,
    'timeout': 15
})
```

## Data Formats

### ScanOptions

Configuration for scans:

```python
options = ScanOptions(
    wordlist="custom.txt",
    extensions=["php", "asp", "jsp"],
    threads=25,
    timeout=15,
    delay=0.5,
    user_agent="Custom Scanner",
    follow_redirects=True,
    custom_headers={"Authorization": "Bearer token"},
    proxy="http://proxy:8080",
    max_retries=5,
    exclude_status="404,403",
    include_status="200,301",
    use_mcp=True  # Enable MCP intelligence
)
```

### ScanData

Complete scan results:

```python
# Access scan data
print(f"Target: {scan_data.target}")
print(f"Duration: {scan_data.duration}s")
print(f"Total findings: {scan_data.total_findings}")

# Filter findings
success_200 = scan_data.get_findings_by_status(200)
php_files = scan_data.get_findings_by_extension('php')
auth_required = scan_data.auth_required_findings

# Export data
scan_data.export_to_file("results.json")
imported = ScanData.import_from_file("results.json")
```

### ExchangeFormat

Standard format for tool integration:

```python
from dirsearch_mcp import ExchangeFormat

exchange = ExchangeFormat(
    scan_data=scan_data,
    metadata={
        'project': 'security_audit',
        'severity': 'high'
    }
)

# Export formats
json_data = exchange.to_json()
xml_data = exchange.to_xml()
csv_data = exchange.to_csv()
```

## Examples

### Concurrent Scanning

```python
async def scan_multiple_targets(targets):
    dirsearch = DirsearchMCP()
    await dirsearch.initialize()
    
    # Scan multiple targets concurrently
    tasks = []
    for target in targets:
        task = dirsearch.scan(target, ScanOptions(threads=10))
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    
    # Process results
    for scan_data in results:
        print(f"{scan_data.target}: {scan_data.total_findings} findings")
```

### Custom Event Processing

```python
class SecurityAnalyzer:
    def __init__(self):
        self.vulnerabilities = []
        
    async def analyze(self, target):
        dirsearch = DirsearchMCP()
        
        # Register handlers
        dirsearch.on_finding(self.check_vulnerability)
        dirsearch.on_scan_completed(self.generate_report)
        
        await dirsearch.initialize()
        await dirsearch.scan(target)
        
    async def check_vulnerability(self, finding):
        # Check for potential vulnerabilities
        vuln_patterns = [
            'backup', 'config', 'admin', 'test',
            '.git', '.env', 'phpinfo'
        ]
        
        path = finding['path'].lower()
        for pattern in vuln_patterns:
            if pattern in path:
                self.vulnerabilities.append(finding)
                break
```

### Integration with CI/CD

```python
async def security_scan_ci(target, fail_threshold=10):
    """CI/CD security scan with fail conditions"""
    dirsearch = DirsearchMCP()
    await dirsearch.initialize()
    
    # Configure for CI environment
    options = ScanOptions(
        threads=30,  # Faster scanning
        timeout=5,   # Lower timeout
        use_mcp=True # Use AI for better detection
    )
    
    scan_data = await dirsearch.scan(target, options)
    
    # Check security findings
    critical_findings = [
        r for r in scan_data.results 
        if any(p in r.path.lower() for p in ['.git', '.env', 'config.php'])
    ]
    
    # Generate report
    reports = await dirsearch.generate_report(scan_data, "./security-reports")
    
    # Fail if too many critical findings
    if len(critical_findings) > fail_threshold:
        print(f"FAIL: Found {len(critical_findings)} critical findings")
        return False
        
    return True
```

## Third-Party Integration

### Burp Suite Integration

```python
class BurpIntegration:
    """Export findings to Burp Suite"""
    
    async def export_to_burp(self, scan_data: ScanData):
        burp_items = []
        
        for finding in scan_data.results:
            burp_item = {
                'url': f"{scan_data.target}{finding.path}",
                'method': 'GET',
                'status': finding.status,
                'length': finding.size,
                'comment': f"Found by Dirsearch MCP"
            }
            burp_items.append(burp_item)
            
        # Export in Burp format
        with open('burp_import.xml', 'w') as f:
            f.write(self._generate_burp_xml(burp_items))
```

### OWASP ZAP Integration

```python
class ZAPIntegration:
    """Send findings to OWASP ZAP"""
    
    def __init__(self, zap_api_key, zap_url="http://localhost:8080"):
        self.zap_api_key = zap_api_key
        self.zap_url = zap_url
        
    async def send_to_zap(self, scan_data: ScanData):
        # Send each finding to ZAP for further testing
        for finding in scan_data.successful_findings:
            url = f"{scan_data.target}{finding.path}"
            await self._add_url_to_zap(url)
```

### Metasploit Integration

```python
class MetasploitIntegration:
    """Generate Metasploit resource files"""
    
    async def generate_resource_file(self, scan_data: ScanData):
        resource = []
        
        # Add workspace
        resource.append(f"workspace -a {scan_data.target_info.domain}")
        
        # Add host
        resource.append(f"db_nmap -sV {scan_data.target_info.domain}")
        
        # Add web paths
        for finding in scan_data.successful_findings:
            if finding.status in [200, 401, 403]:
                resource.append(
                    f"auxiliary/scanner/http/dir_scanner "
                    f"RHOSTS={scan_data.target_info.domain} "
                    f"PATH={finding.path}"
                )
                
        # Save resource file
        with open('dirsearch_msf.rc', 'w') as f:
            f.write('\n'.join(resource))
```

### Elasticsearch Integration

```python
class ElasticsearchIntegration:
    """Send findings to Elasticsearch for analysis"""
    
    async def index_findings(self, scan_data: ScanData):
        from elasticsearch import AsyncElasticsearch
        
        es = AsyncElasticsearch(['http://localhost:9200'])
        
        # Index scan metadata
        await es.index(
            index='security-scans',
            body={
                'timestamp': scan_data.start_time,
                'target': scan_data.target,
                'duration': scan_data.duration,
                'total_findings': scan_data.total_findings,
                'technologies': scan_data.target_info.technology_stack
            }
        )
        
        # Index each finding
        for finding in scan_data.results:
            await es.index(
                index='security-findings',
                body={
                    'scan_id': scan_data.start_time,
                    'target': scan_data.target,
                    'path': finding.path,
                    'status': finding.status,
                    'size': finding.size,
                    'timestamp': scan_data.end_time
                }
            )
```

## Best Practices

1. **Error Handling**: Always wrap scans in try-except blocks
2. **Resource Management**: Use context managers for automatic cleanup
3. **Concurrent Limits**: Limit concurrent scans to avoid overwhelming targets
4. **Caching**: Enable caching for repeated scans
5. **Logging**: Use structured logging for better debugging

## API Reference

For complete API documentation, see [API_REFERENCE.md](./API_REFERENCE.md)

## Support

For issues and questions:
- GitHub Issues: [https://github.com/dirsearch-mcp/issues](https://github.com/dirsearch-mcp/issues)
- Documentation: [https://dirsearch-mcp.readthedocs.io](https://dirsearch-mcp.readthedocs.io)