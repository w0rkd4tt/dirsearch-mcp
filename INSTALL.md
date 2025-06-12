# Installation Guide for Dirsearch MCP

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment (recommended)

## Installation Steps

### 1. Create a Virtual Environment (Recommended)

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 2. Install Dependencies

```bash
# Install all required packages
pip install -r requirements.txt
```

If you encounter any issues with specific packages, you can install them individually:

```bash
# Core dependencies
pip install aiohttp httpx rich colorama

# For reports
pip install matplotlib seaborn

# For AI features (optional)
pip install openai
```

### 3. Configure AI API Keys (Optional)

For AI-enhanced scanning, set your API keys:

```bash
# Option 1: Environment variables
export OPENAI_API_KEY="your-openai-api-key"
export DEEPSEEK_API_KEY="your-deepseek-api-key"

# Option 2: Create a .env file
echo "OPENAI_API_KEY=your-openai-api-key" > .env
echo "DEEPSEEK_API_KEY=your-deepseek-api-key" >> .env
```

### 4. Create Wordlists Directory

```bash
# Create wordlists directory
mkdir -p wordlists

# Download common wordlists (optional)
wget https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/Web-Content/common.txt -O wordlists/common.txt
wget https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/Web-Content/directory-list-2.3-small.txt -O wordlists/directory-list-small.txt
```

## Running the Application

### Interactive Mode

```bash
python main.py
```

### Command Line Mode

```bash
# Show help
python main.py --help

# Quick scan
python main.py -u https://example.com --quick

# Custom scan
python main.py -u https://example.com -w wordlists/common.txt -e php,html -t 20

# AI-enhanced scan
python main.py -u https://example.com --ai-provider openai --ai-key YOUR_KEY
```

## Troubleshooting

### Event Loop Error

If you get "asyncio.run() cannot be called from a running event loop":

1. You might be running in Jupyter notebook. Try running from terminal instead.
2. Install nest-asyncio: `pip install nest-asyncio`

### Import Errors

If you get import errors:

1. Make sure all dependencies are installed: `pip install -r requirements.txt`
2. Check you're in the correct directory
3. Verify Python version: `python --version` (should be 3.8+)

### Permission Errors

On Unix systems, make the script executable:

```bash
chmod +x main.py
```

### Missing Wordlists

Create a basic wordlist:

```bash
mkdir -p wordlists
echo -e "admin\nlogin\ntest\napi\nconfig" > wordlists/common.txt
```

## Quick Test

Test if everything is working:

```bash
# Test help
python main.py --help

# Test with a simple scan
python main.py -u http://example.com -w admin,test,login -t 5
```

## Next Steps

1. Read the README.md for detailed usage instructions
2. Configure your preferred settings in a config file
3. Set up AI API keys for enhanced scanning
4. Customize wordlists for your targets

## Support

If you encounter issues:

1. Check the error logs in the `log/` directory
2. Run with `--verbose` flag for detailed output
3. Ensure all dependencies are correctly installed
4. Check Python version compatibility