# Dirsearch MCP - Intelligent Directory Scanner with AI Integration

A powerful, multi-threaded directory and file enumeration tool enhanced with MCP (Machine Coordination Protocol) intelligence and AI agent integration for advanced web application scanning.

## Features

- **Dual Intelligence Modes**:
  - **Local Mode**: Fast rule-based scanning with predefined logic
  - **AI Agent Mode**: Enhanced scanning with ChatGPT/DeepSeek integration for intelligent decision making

- **Advanced Scanning Capabilities**:
  - Multi-threaded concurrent scanning
  - Automatic technology stack detection
  - CMS identification (WordPress, Joomla, Drupal, etc.)
  - Smart wordlist selection based on target analysis
  - Dynamic parameter optimization

- **Rich User Interface**:
  - Interactive CLI with rich formatting
  - Real-time progress tracking
  - Color-coded output
  - Multiple report formats (JSON, HTML, Markdown)

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

## Usage

### Interactive Mode
Launch the interactive menu:
```bash
python main.py
```

### Quick Scan
Let MCP automatically configure optimal parameters:
```bash
python main.py -u https://example.com --quick
```

### Custom Scan
Specify your own parameters:
```bash
python main.py -u https://example.com -w custom_wordlist.txt -e php,html,js -t 20
```

### AI-Enhanced Scan
Use AI agent for intelligent scanning:
```bash
python main.py -u https://example.com --ai-provider openai --ai-key YOUR_KEY
```

### Batch Scanning
Scan multiple targets from a file:
```bash
python main.py -l targets.txt --report-format json -o ./reports
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