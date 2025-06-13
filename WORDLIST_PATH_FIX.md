# Wordlist Path Fix Summary

## Issue
The error "expected str, bytes or os.PathLike object, not dict" occurred when selecting wordlists in the interactive menu because the `settings.paths['wordlists']` structure was changed from a string to a nested dictionary.

## Root Cause
In `settings.py`, the wordlists path was restructured to:
```python
self.paths = {
    'wordlists': {
        'general': '/path/to/wordlists/general',
        'platform': '/path/to/wordlists/platform', 
        'specialized': '/path/to/wordlists/specialized',
        'base': '/path/to/wordlists'
    }
}
```

But the code was expecting a simple string path.

## Fix Applied

### 1. Updated `interactive_menu.py`
Added logic to handle both string and dict formats:
```python
# Handle nested wordlists path structure
wordlists_path = self.settings.paths.get('wordlists', 'wordlists')
if isinstance(wordlists_path, dict):
    wordlists_path = wordlists_path.get('base', wordlists_path.get('general', 'wordlists'))
wordlist_dir = Path(wordlists_path)
```

### 2. Updated `dirsearch_engine.py` 
Similar fix for wordlist loading:
```python
if isinstance(wordlists_path, dict):
    wordlists_base = wordlists_path.get('base', wordlists_path.get('general', 'wordlists'))
else:
    wordlists_base = wordlists_path
```

### 3. Enhanced Wordlist Discovery
Updated to search in subdirectories:
```python
for subdir in ['general', 'platform', 'specialized']:
    if (wordlist_dir / subdir / name).exists():
        available.append((name, desc))
        break
```

## Files Modified
1. `src/cli/interactive_menu.py` - 4 locations fixed
2. `src/core/dirsearch_engine.py` - 1 location fixed

## Testing
The fix ensures backward compatibility by:
- Supporting both string and dict path formats
- Checking multiple locations for wordlist files
- Using 'base' path as primary, 'general' as fallback

## Result
The interactive menu now properly handles the nested wordlist path structure and can find wordlists in subdirectories.