# Dirsearch MCP - Quick Start Guide

## 🚀 Get Started in 2 Minutes

### 1. Setup (One-time)
```bash
# Run the setup script
./setup_and_run.sh
```

### 2. Activate Virtual Environment
```bash
source venv/bin/activate
```

### 3. Run the Scanner

#### Option A: Interactive Mode (Recommended for beginners)
```bash
python main.py
```
Then select "1" for Quick Scan and enter your target URL.

#### Option B: Command Line
```bash
python main.py --url https://example.com --wordlist common.txt
```

#### Option C: As a Library
```python
# See examples/simple_integration.py
from src.integration import DirsearchMCP, ScanOptions

dirsearch = DirsearchMCP()
await dirsearch.initialize()
scan_data = await dirsearch.scan("https://example.com", ScanOptions())
```

## 📝 Common Commands

```bash
# Quick scan with auto-config
python main.py --url https://example.com --quick

# Scan with specific wordlist
python main.py --url https://example.com --wordlist wordpress.txt

# Scan with extensions
python main.py --url https://example.com -e php,html,js

# Stealth mode (slower, fewer requests)
python main.py --url https://example.com --stealth

# Show help
python main.py --help
```

## 🎯 Tips for Best Results

1. **Start Simple**: Use Quick Scan mode first
2. **Choose Right Wordlist**: 
   - `common.txt` for general sites
   - `wordpress.txt` for WordPress
   - `api_endpoints.txt` for APIs
3. **Add Extensions**: Match your target (php, aspx, jsp, etc.)
4. **Enable AI**: Configure AI agents for smarter scanning

## ❓ Need Help?

- Run the interactive CLI and select "Help & Documentation"
- Check `examples/` directory for code samples
- See full README.md for detailed documentation