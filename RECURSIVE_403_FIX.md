# Recursive Scanning 403 Fix

## Change Request
"Nếu status trả về là 403 thì không recursive nữa" (If status returns 403, don't recurse anymore)

## Implementation
Modified the recursive scanning logic in `src/core/dirsearch_engine.py` to skip directories that return 403 Forbidden status.

## Changes Made

### 1. Updated `_handle_recursive_scan` method (line 801-807)
- Changed from including 403 in recursive candidates to excluding them
- Now only directories with status codes 200, 301, 302 are considered for recursive scanning
- Added tracking of forbidden directories for logging

```python
# Before:
if (result.status_code in [200, 301, 302, 403] and 
    result.is_directory and 
    result.url not in self._deep_scanned_dirs):
    all_directories.append(result)

# After:
if result.is_directory and result.url not in self._deep_scanned_dirs:
    if result.status_code in [200, 301, 302]:
        all_directories.append(result)
    elif result.status_code == 403:
        forbidden_directories.append(result)
```

### 2. Added logging for skipped 403 directories (line 809-812)
- Logs the count of forbidden directories being skipped
- Shows details of first 5 forbidden directories in debug mode

### 3. Updated intelligent analysis (line 543)
- Removed 403 from status codes that trigger intelligent path analysis
- Only 200, 301, 302 responses are analyzed for pattern extraction

### 4. Updated deep content analysis (line 1823)
- Confirmed 403 endpoints are already excluded from deep analysis

## Rationale
- **403 Forbidden** means access is denied to the directory
- Attempting to scan subdirectories of a forbidden path will likely also return 403
- This saves unnecessary requests and improves scan efficiency
- Reduces noise in scan results from inaccessible areas

## Impact
- Faster scans by avoiding unnecessary recursive attempts on forbidden directories
- Cleaner results without cascading 403 errors
- Still displays 403 directories in results and tree view for awareness
- More efficient use of scanning resources

## Directory Tree Display
403 directories are still shown in the directory tree visualization but won't be recursively scanned. They appear with [403] status indicator so users know they exist but are inaccessible.