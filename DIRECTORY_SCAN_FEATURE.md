# Directory Scanning Without Extensions

## Overview
The dirsearch engine now has enhanced support for scanning directories without file extensions. This feature is particularly useful for discovering:
- API endpoints (e.g., `/api`, `/v1`, `/graphql`)
- Admin panels (e.g., `/admin`, `/dashboard`, `/panel`)
- Hidden directories (e.g., `/.git`, `/.svn`, `/.env`)
- Common web directories (e.g., `/images`, `/uploads`, `/static`)

## How It Works

### 1. Path Generation
When generating paths, the engine now:
- Always includes the base path without any extension
- Automatically adds a trailing slash variant for each path
- Supports case variations (uppercase, lowercase, capitalization)

Example: For the word "admin", the engine generates:
- `admin`
- `admin/`
- `ADMIN` (if uppercase option enabled)
- `ADMIN/` (if uppercase option enabled)

### 2. Directory Detection
The engine detects directories through multiple methods:
- **Path ending with `/`**: Explicitly marked as directory
- **Response analysis**: Checks for directory listing indicators
- **Status codes**: 301/302 redirects to paths with trailing slash
- **Content type**: HTML content for extensionless paths
- **403 responses**: Often indicate protected directories

### 3. Enhanced Detection Patterns
The engine looks for these indicators in responses:
- `index of`
- `directory listing`
- `parent directory`
- `[dir]`
- `apache server at`
- `nginx`

## Usage Example

```python
from src.core.dirsearch_engine import DirsearchEngine, ScanOptions

# Create wordlist with directory names (no extensions)
wordlist = ['admin', 'api', 'backup', 'config', 'data']

# Configure options for directory scanning
options = ScanOptions(
    extensions=[],  # Empty = no file extensions
    threads=10,
    timeout=5,
    detect_wildcards=True
)

# Run scan
async with DirsearchEngine() as engine:
    results = await engine.scan_target(
        url="http://example.com",
        wordlist=wordlist,
        options=options
    )
    
    # Filter directory results
    directories = [r for r in results if r.is_directory]
```

## Benefits
1. **Better Coverage**: Discovers endpoints that don't have file extensions
2. **API Discovery**: Finds RESTful API endpoints effectively
3. **Hidden Paths**: Uncovers version control and configuration directories
4. **Reduced False Negatives**: Doesn't miss directories due to lack of extensions

## Test Results
Testing against http://testphp.vulnweb.com:
- Successfully discovered: `/admin/`, `/images/`, `/vendor/`
- Correctly identified 301 redirects and 200 OK responses
- Properly marked paths as directories based on response analysis