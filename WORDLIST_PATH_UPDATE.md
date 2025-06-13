# Wordlist Path Update Summary

## Changes Made

### 1. Updated `_get_available_wordlists()` in `interactive_menu.py`
- Added subdirectory paths to match actual file locations:
  - `general/monster-all.txt` - Monster wordlist in general subdirectory
  - `general/combined-enhanced.txt` - Combined enhanced wordlist
  - `specialized/hidden-files.txt` - Hidden files wordlist
  - `platform/` prefix for platform-specific wordlists
  - `specialized/` prefix for specialized wordlists

### 2. Updated wordlist references
- Changed `monster-all.txt` → `general/monster-all.txt` in:
  - Monster mode configuration
  - Display tables
  - Main.py monster mode

### 3. Fixed path resolution logic
- Simplified to handle paths with subdirectories directly
- Removed redundant subdirectory checking since paths now include subdirectories

## Current Wordlist Structure

```
wordlists/
├── api-endpoints.txt
├── critical-backup.txt
├── general/
│   ├── monster-all.txt (69,137 entries)
│   └── combined-enhanced.txt (458 entries)
└── specialized/
    └── hidden-files.txt (487 entries)
```

## Available Wordlists in Menu

1. **general/monster-all.txt** - Comprehensive wordlist for aggressive scanning
2. **general/combined-enhanced.txt** - Recommended balanced wordlist
3. **api-endpoints.txt** - API-specific paths
4. **specialized/hidden-files.txt** - Hidden and sensitive files
5. **critical-backup.txt** - Backup file patterns

## Notes

- Some wordlists like `critical-admin.txt` and `critical-api.txt` don't exist as files
- The engine treats non-existent files as inline wordlists (comma-separated)
- Platform-specific wordlists (PHP, ASP, JSP, WordPress, etc.) are placeholders for future additions

## Testing

All existing wordlists load correctly with their subdirectory paths:
- ✅ general/monster-all.txt
- ✅ general/combined-enhanced.txt  
- ✅ api-endpoints.txt
- ✅ specialized/hidden-files.txt
- ✅ critical-backup.txt