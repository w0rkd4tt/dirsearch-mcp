# Dirsearch MCP Integration Module

This module provides a clean API and plugin architecture for integrating Dirsearch MCP with other security tools and frameworks.

## Overview

The integration module consists of:

- **DirsearchMCP**: Main integration class with clean API
- **Plugin System**: Extensible plugin architecture
- **Event Hooks**: Real-time event notifications
- **Data Formats**: Standardized data exchange formats

## Quick Example

```python
from dirsearch_mcp.integration import DirsearchMCP, ScanOptions

async def main():
    # Initialize with event handlers
    dirsearch = DirsearchMCP()
    dirsearch.on_finding(lambda f: print(f"Found: {f['path']}"))
    
    await dirsearch.initialize()
    
    # Run scan
    options = ScanOptions(threads=20, extensions=["php", "html"])
    scan_data = await dirsearch.scan("https://example.com", options)
    
    # Generate reports
    reports = await dirsearch.generate_report(scan_data)
    print(f"Reports saved: {reports}")

# Run
import asyncio
asyncio.run(main())
```

## Module Structure

```
integration/
├── __init__.py           # Package exports
├── interface.py          # Main DirsearchMCP class
├── plugin_base.py        # Plugin system base classes
├── events.py             # Event system implementation
├── data_formats.py       # Data exchange formats
└── plugins/              # Built-in plugins
    ├── __init__.py
    └── wappalyzer_plugin.py
```

## Key Features

### 1. Clean API Design

- Async/await support
- Context manager support
- Type hints throughout
- Comprehensive docstrings

### 2. Plugin Architecture

- Easy plugin creation
- Plugin lifecycle management
- Configuration support
- Built-in plugins

### 3. Event System

- Real-time notifications
- Async event handlers
- Multiple handler support
- Event filtering

### 4. Data Exchange

- Standardized formats
- JSON/XML/CSV export
- Import/export capabilities
- Tool-specific adapters

## Creating Plugins

```python
from dirsearch_mcp.integration import Plugin

class MyPlugin(Plugin):
    name = "my_plugin"
    version = "1.0.0"
    
    async def initialize(self):
        self.log("Plugin initialized")
    
    async def on_finding(self, finding):
        # Process finding
        pass
```

## Integration Examples

### Burp Suite
```python
# Export to Burp Suite format
exchange = ExchangeFormat(scan_data=scan_data)
burp_xml = exchange.to_xml()
```

### Metasploit
```python
# Generate MSF resource file
for finding in scan_data.successful_findings:
    msf_commands.append(f"auxiliary/scanner/http/dir_scanner PATH={finding.path}")
```

### ELK Stack
```python
# Send to Elasticsearch
es.index(index='security-findings', body=scan_data.to_dict())
```

## For More Information

See the [Integration Guide](../../docs/INTEGRATION.md) for detailed documentation and examples.