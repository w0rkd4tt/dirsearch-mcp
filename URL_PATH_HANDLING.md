# URL Path Handling Documentation

## Overview
Dirsearch MCP now properly handles URLs that include paths, ensuring that scans are performed within the correct directory context.

## Supported URL Formats

### Basic IP/Domain
```bash
python main.py -u 192.168.214.143
python main.py -u example.com
```
Scans from the root directory

### IP/Domain with Path
```bash
python main.py -u 192.168.214.143/api
python main.py -u example.com/admin
python main.py -u 192.168.214.143/api/v1
```
Scans within the specified directory

### With Protocol
```bash
python main.py -u http://192.168.214.143/api
python main.py -u https://example.com/app
```

### With Port
```bash
python main.py -u 192.168.214.143:8080/api
python main.py -u example.com:3000/admin
```

## How It Works

### 1. Automatic Protocol Addition
If no protocol is specified, `http://` is automatically added:
- `192.168.214.143/api` → `http://192.168.214.143/api`

### 2. Directory Detection
The tool automatically detects if a path represents a directory:
- Paths without file extensions are treated as directories
- Trailing slashes are automatically added to directory paths
- `192.168.214.143/api` → `http://192.168.214.143/api/`

### 3. Path Preservation
When scanning, all paths are correctly joined under the base directory:
- Base: `http://192.168.214.143/api/`
- Wordlist: `users`, `login`, `docs`
- Results: 
  - `http://192.168.214.143/api/users`
  - `http://192.168.214.143/api/login`
  - `http://192.168.214.143/api/docs`

## Examples

### Scanning API Endpoints
```bash
# Scan API v1 endpoints
python main.py -u 192.168.214.143/api/v1 -w api-endpoints.txt

# Scan with extensions
python main.py -u example.com/api -e json,xml
```

### Scanning Admin Panels
```bash
# Scan admin directory
python main.py -u 192.168.214.143/admin -w admin-panels.txt

# With authentication endpoints
python main.py -u example.com/admin/auth -e php,asp
```

### Multi-level Paths
```bash
# Deep path scanning
python main.py -u example.com/app/modules/user

# With recursion
python main.py -u 192.168.214.143/api/v2 -r -R 3
```

## URL Breakdown Display

When entering a URL in interactive mode, you'll see:
```
URL Analysis:
Component   Value
Protocol    http
Domain      192.168.214.143
Path        /api
```

## Path Handling Rules

### 1. File vs Directory Detection
- No extension = Directory: `/api` → `/api/`
- Has extension = File: `/test.php` → `/test.php` (no trailing slash)

### 2. Root URL Handling
- `http://example.com` → No trailing slash
- `http://example.com/` → Normalized to no trailing slash

### 3. Subdirectory Handling
- `http://example.com/api` → `http://example.com/api/`
- Ensures proper path joining for wordlist items

## Recursion with Paths

When recursion is enabled with a path-based URL:
```bash
python main.py -u 192.168.214.143/api -r -R 3
```

The recursion respects the base path:
- Level 1: Scans `/api/*`
- Level 2: Scans `/api/[found_dirs]/*`
- Level 3: Scans `/api/[found_dirs]/[found_subdirs]/*`

## Common Use Cases

### 1. API Version Testing
```bash
python main.py -u api.example.com/v1
python main.py -u api.example.com/v2
```

### 2. Subdomain Path Scanning
```bash
python main.py -u admin.example.com/portal
python main.py -u dev.example.com/staging
```

### 3. Application Module Scanning
```bash
python main.py -u example.com/app/modules
python main.py -u example.com/webapp/controllers
```

## Troubleshooting

### Issue: Paths Not Under Expected Directory
**Symptom**: Scans return paths like `/admin` instead of `/api/admin`
**Solution**: Ensure the URL path doesn't have a trailing slash for directories

### Issue: 404 for All Paths
**Symptom**: All paths return 404 when scanning subdirectory
**Solution**: Verify the base directory exists and is accessible

## Best Practices

1. **Verify Base Path**: Ensure the base path exists before scanning
2. **Use Appropriate Wordlists**: Use context-specific wordlists for subdirectories
3. **Monitor Scan Scope**: Check the scan is staying within the intended directory
4. **Combine with Recursion**: Use recursion to explore found subdirectories

## Integration with MCP

The MCP coordinator considers the base path when:
- Analyzing target characteristics
- Generating optimized scan plans
- Selecting appropriate wordlists
- Determining recursion strategies

Path-aware scanning ensures more targeted and efficient security assessments.