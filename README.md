# Dirsearch MCP - Intelligent Directory Scanner with AI Integration

A powerful, multi-threaded directory and file enumeration tool enhanced with MCP (Machine Coordination Protocol) intelligence and AI agent integration for advanced web application scanning.

## 🚀 Key Features

### Core Capabilities
- **Smart Recursive Scanning**: Continues until no new content is found
- **301 Redirect Handling**: Automatically discovers hidden files in redirected directories
- **Deep Content Analysis**: Extracts hidden endpoints from HTML, JavaScript, and API responses
- **Directory Tree Visualization**: Visual representation of discovered site structure
- **Wildcard Detection**: Identifies and filters false positives

### Intelligence Modes
- **Local Mode**: Fast rule-based scanning with predefined logic
- **AI Agent Mode**: Enhanced scanning with ChatGPT/DeepSeek integration

### Advanced Features
- **Multi-threaded Scanning**: Concurrent requests with configurable threads
- **Technology Detection**: Automatic stack identification (WordPress, Laravel, etc.)
- **Smart Wordlist Selection**: Context-aware wordlist choice based on target
- **Multiple Authentication**: Basic, Digest, NTLM support
- **Custom Headers & Cookies**: For bypassing WAF and authentication

### User Experience
- **Interactive CLI**: Rich formatting with color-coded output
- **Real-time Progress**: Live updates with statistics
- **Multiple Report Formats**: JSON, HTML, Markdown with directory trees
- **Monster Mode**: Aggressive scanning with maximum coverage

- **MCP Coordination**:
  - Intelligent scan planning
  - Context-aware decision making
  - Performance optimization
  - Learning from scan results

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/dirsearch-mcp.git
cd dirsearch-mcp
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. (Optional) Set up AI API keys:
```bash
export OPENAI_API_KEY="your-openai-api-key"
export DEEPSEEK_API_KEY="your-deepseek-api-key"
```

## 🚀 Quick Start

### Interactive Mode (Recommended)
```bash
python main.py
```
Choose from:
1. **Quick Scan** - Automatic configuration
2. **Standard Scan** - Balanced approach
3. **Advanced Scan** - Full control
4. **Monster Mode** - Maximum aggression

### Direct Scanning
```bash
# Quick scan with automatic configuration
python scan_any_target.py http://example.com

# Standard scan with common wordlist
python scan_any_target.py http://example.com common 20

# Comprehensive scan
python scan_any_target.py http://example.com comprehensive 30
```

## 📖 Usage Examples

### Discover Hidden Files in 301 Redirects
```bash
python main.py
# Enable recursive scanning
# Set follow_redirects = No
# Watch for 301 paths being explored
```

### API Endpoint Discovery
```bash
python main.py
# Select wordlist: api-endpoints.txt
# Add extensions: json,xml
# Enable content analysis
```

### WordPress Site Scanning
```bash
python main.py
# MCP will detect WordPress
# Automatically use wordpress.txt
# Find wp-admin, wp-content paths
```

## Command Line Options

### Target Options
- `-u, --url URL`: Target URL to scan
- `-l, --url-list FILE`: File containing URLs to scan

### Scan Options
- `-w, --wordlist FILE`: Wordlist file (default: common.txt)
- `-e, --extensions EXT`: Extensions to check (comma-separated)
- `-t, --threads NUM`: Number of threads (default: 10)
- `--timeout SEC`: Request timeout in seconds (default: 10)
- `--delay SEC`: Delay between requests
- `--user-agent STRING`: Custom User-Agent
- `--follow-redirects`: Follow HTTP redirects
- `--exclude-status CODES`: Status codes to exclude (default: 404)

### MCP Intelligence Options
- `--mcp-mode MODE`: MCP mode: auto, local, or ai (default: auto)
- `--ai-provider PROVIDER`: AI provider: openai or deepseek
- `--ai-key KEY`: API key for AI provider
- `--ai-model MODEL`: Specific AI model to use

### Output Options
- `-o, --output-dir DIR`: Output directory for reports
- `--report-format FORMAT`: Report format: json, html, markdown, or all
- `--quiet`: Minimal output
- `--verbose`: Verbose output
- `--no-color`: Disable colored output

## Examples

### Basic WordPress Scan
```bash
python main.py -u https://wordpress-site.com --quick
```

### API Endpoint Discovery
```bash
python main.py -u https://api.example.com -e json,xml -w api_endpoints.txt
```

### Stealth Scan with Low Threads
```bash
python main.py -u https://secure-site.com -t 3 --delay 1 --user-agent "GoogleBot"
```

### Generate HTML Report
```bash
python main.py -u https://example.com --report-format html -o ./scan-reports
```

## Configuration

Create a configuration file to set default options:

```json
{
  "scan": {
    "threads": 20,
    "timeout": 15,
    "user_agent": "Custom-Scanner/1.0"
  },
  "ai": {
    "openai_api_key": "your-key",
    "openai_model": "gpt-4"
  },
  "paths": {
    "wordlists": "/path/to/wordlists",
    "reports": "/path/to/reports"
  }
}
```

Load configuration:
```bash
python main.py --config config.json -u https://example.com
```

## Wordlists

The tool comes with several built-in wordlists:
- `common.txt`: Common directories and files
- `php_common.txt`: PHP-specific paths
- `wordpress.txt`: WordPress-specific paths
- `api_endpoints.txt`: Common API endpoints

You can also use custom wordlists by specifying the path.

## Reports

Reports are generated in multiple formats:

### JSON Report
Machine-readable format with complete scan data, perfect for integration with other tools.

### HTML Report
Interactive web report with:
- Charts and visualizations
- Sortable tables
- Findings summary
- Recommendations

### Markdown Report
Clean, readable format ideal for documentation and sharing.

## Performance Tips

1. **Thread Optimization**: Start with 10-20 threads and adjust based on target response
2. **Wordlist Selection**: Use targeted wordlists for better results
3. **Extension Filtering**: Only scan relevant extensions to reduce requests
4. **AI Mode**: Use for complex targets or when unsure about optimal parameters
5. **Local Mode**: Use for simple targets or when speed is critical

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed:
   ```bash
   pip install -r requirements.txt
   ```

2. **AI Mode Not Working**: Check API key configuration:
   ```bash
   python main.py -u https://example.com --ai-provider openai --ai-key YOUR_KEY --verbose
   ```

3. **Slow Scanning**: Reduce threads or add delay:
   ```bash
   python main.py -u https://example.com -t 5 --delay 0.5
   ```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is designed for authorized security testing only. Users are responsible for complying with applicable laws and obtaining proper authorization before scanning any systems they do not own.

## Author

Dirsearch MCP Team

## Acknowledgments

- Inspired by the original dirsearch project
- Enhanced with modern AI capabilities
- Built with love for the security community