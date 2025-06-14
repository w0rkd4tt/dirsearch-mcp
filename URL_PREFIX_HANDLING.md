# URL Prefix Handling in Dirsearch MCP

## Overview
The dirsearch engine now properly handles URLs with prefixes (paths) and ensures that all scan results and reports show the complete path including the prefix.

## What Changed

### 1. Full Path Storage in Results
Previously, when scanning a URL like `http://example.com/app/v1`, the results would only store the relative path (e.g., `/admin`). Now, the full path including the prefix is stored (e.g., `/app/v1/admin`).

**Code Change in `dirsearch_engine.py`:**
```python
# Extract the full path from the URL (including prefix)
parsed_url = urlparse(url)
full_path = parsed_url.path

result = ScanResult(
    url=url,
    path=full_path,  # Use full path including prefix
    ...
)
```

### 2. Report Generation
Reports (JSON, HTML, Markdown) now display the complete paths with prefixes, making it clear where each discovered resource is located relative to the scanned URL.

## Examples

### Example 1: API Versioning
**Scan URL:** `http://api.example.com/v2`

**Old behavior:**
- `/users` → Shows as `/users`
- `/admin` → Shows as `/admin`

**New behavior:**
- `/users` → Shows as `/v2/users`
- `/admin` → Shows as `/v2/admin`

### Example 2: Application Subdirectory
**Scan URL:** `http://example.com/webapp/admin`

**Old behavior:**
- `/dashboard` → Shows as `/dashboard`
- `/config` → Shows as `/config`

**New behavior:**
- `/dashboard` → Shows as `/webapp/admin/dashboard`
- `/config` → Shows as `/webapp/admin/config`

### Example 3: Multiple Path Levels
**Scan URL:** `http://example.com/api/v1/internal`

**Results will show:**
```
/api/v1/internal/users
/api/v1/internal/settings
/api/v1/internal/logs
```

## Benefits

1. **Clarity**: Full paths make it immediately clear where resources are located
2. **Accuracy**: Reports accurately reflect the complete URL structure
3. **Consistency**: All report formats (JSON, HTML, Markdown) show the same path information
4. **Better Analysis**: Security assessments can better understand the application structure

## Directory Tree Visualization

The directory tree in reports now correctly shows the full structure including prefixes:

```
📁 api/
├── 📁 v1/
│   ├── 📁 internal/
│   │   ├── 📄 users [200]
│   │   ├── 📄 settings [403]
│   │   └── 📄 logs [401]
│   └── 📁 public/
│       └── 📄 status [200]
└── 📁 v2/
    └── 📄 users [200]
```

## Usage

No changes are required in how you use the tool. Simply provide the full URL including any path prefix:

```bash
# Scan with prefix
dirsearch-mcp scan http://example.com/app/v1

# The results will automatically include /app/v1 prefix in all paths
```

## Technical Details

- The `parse_response` method now extracts the full path from the URL using `urlparse`
- All report generators use the `path` field which now contains the complete path
- Directory tree generation correctly parses and displays the full path hierarchy
- The change is backward compatible and doesn't affect existing functionality