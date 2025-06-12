# Recursion Feature Documentation

## Overview
The Dirsearch MCP tool now includes powerful recursive scanning capabilities that allow it to automatically explore discovered directories to find deeper paths and hidden content.

## Default Settings
- **Recursive scanning**: Enabled by default (`recursive=True`)
- **Recursion depth**: 3 levels by default (`recursion_depth=3`)

## How It Works

### 1. Directory Detection
During the initial scan, the tool identifies directories by:
- Paths ending with `/`
- HTTP responses indicating directory listings
- Status codes 200, 301, 302, or 403 (often indicate accessible directories)

### 2. Recursive Scanning
When a directory is found:
1. The tool adds it to the scan queue
2. After the initial scan completes, it scans each discovered directory
3. This process repeats up to the configured recursion depth
4. Each level uses a optimized wordlist for better performance

### 3. Duplicate Prevention
- The tool tracks all scanned paths to avoid duplicates
- Full URLs are checked to prevent re-scanning the same path

## Command Line Usage

### Enable Recursion (Default)
```bash
python main.py -u https://example.com
# or explicitly
python main.py -u https://example.com -r
```

### Disable Recursion
```bash
python main.py -u https://example.com --no-recursive
```

### Set Recursion Depth
```bash
python main.py -u https://example.com -R 5  # Scan up to 5 levels deep
```

### Combined Example
```bash
python main.py -u https://example.com -r -R 4 -t 20 -e php,html
```

## Interactive Menu Options

In the advanced scan configuration:
1. You'll be asked: "Enable recursive scanning?" (Default: Yes)
2. If enabled, you can set the recursion depth (1-10, Default: 3)

## Recursion Behavior

### Level 1 (Initial Scan)
- Scans: `/admin`, `/api`, `/config`, etc.
- Finds: `/admin/` (directory)

### Level 2 
- Scans: `/admin/login`, `/admin/users`, `/admin/config`, etc.
- Finds: `/admin/users/` (directory)

### Level 3
- Scans: `/admin/users/list`, `/admin/users/edit`, etc.
- Continues until reaching the configured depth

## Performance Considerations

### Wordlist for Recursive Scans
The tool uses an optimized wordlist for recursive scans containing common subdirectories:
- admin, api, backup, config, data, db, files
- images, includes, js, lib, logs, media, scripts
- src, static, temp, test, tmp, upload, uploads
- user, users, vendor, wp-admin, wp-content, wp-includes

### Thread Management
- The same thread pool is used for all recursion levels
- No additional threads are spawned for recursive scans
- Maintains consistent performance throughout the scan

### Memory Usage
- Path tracking prevents duplicate scans
- Results are stored incrementally
- Memory usage scales with the number of discovered paths

## Best Practices

### 1. Appropriate Depth Settings
- **Depth 1-2**: Quick reconnaissance
- **Depth 3-4**: Standard thorough scan (Default: 3)
- **Depth 5+**: Deep exploration (may take significantly longer)

### 2. Target-Specific Tuning
- **Static sites**: Lower depth (1-2) usually sufficient
- **Complex applications**: Higher depth (3-5) recommended
- **APIs**: Often benefit from deeper recursion

### 3. Performance Optimization
- Use `--threads` to control concurrent requests
- Add `--delay` for rate limiting if needed
- Monitor scan progress with real-time display

## Example Scenarios

### Web Application Scanning
```bash
python main.py -u https://webapp.com -r -R 4 -e php,asp,aspx
```

### API Endpoint Discovery
```bash
python main.py -u https://api.example.com -r -R 5 -w api-endpoints.txt
```

### WordPress Site
```bash
python main.py -u https://wordpress-site.com -r -R 3 -e php
```

### Disable for Simple Scans
```bash
python main.py -u https://example.com --no-recursive --quick
```

## Monitoring Recursion

During the scan, you'll see:
- "Found X directories for recursive scan at depth Y"
- "Recursive scan: [URL] (depth: Z)"
- Real-time progress updates for each level

## Integration with MCP

The MCP coordinator considers recursion when:
- Analyzing target characteristics
- Optimizing scan parameters
- Generating scan plans
- Providing recommendations

Recursive scanning works seamlessly with all MCP modes (AUTO, LOCAL, AI).