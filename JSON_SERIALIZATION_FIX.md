# JSON Serialization Fix Summary

## Problem
The scan was failing with the error:
```
Object of type DynamicContentParser is not JSON serializable
```

This occurred when trying to save scan reports because the `DynamicContentParser` object from wildcard detection was being included in the data that needed to be JSON serialized.

## Root Cause
The `DynamicContentParser` class in `dirsearch_engine.py` is used for wildcard response detection. It stores parsed response patterns and is not JSON serializable. This object was being stored in the wildcard detection results and inadvertently included in the scan data passed to the report generator.

## Solution
Fixed the issue by updating the `_clean_data_for_json` method in `src/utils/reporter.py` to:

1. **Detect DynamicContentParser objects**: Check for objects with the type name 'DynamicContentParser'
2. **Convert to None**: Replace these objects with `None` in the cleaned data
3. **Handle other non-serializable types**: Added handling for sets (convert to lists) and better error handling for dataclasses
4. **Filter out None values**: Remove None values from dictionaries and lists during cleaning

## Code Changes

### src/utils/reporter.py
```python
def _clean_data_for_json(self, data: Any) -> Any:
    """Recursively clean data for JSON serialization"""
    # Skip DynamicContentParser objects
    if type(data).__name__ == 'DynamicContentParser':
        return None
    
    if hasattr(data, '__dict__'):
        try:
            return self._clean_data_for_json(asdict(data))
        except:
            # If asdict fails, convert to string
            return str(data)
    elif isinstance(data, dict):
        return {k: self._clean_data_for_json(v) for k, v in data.items() if v is not None}
    elif isinstance(data, list):
        return [self._clean_data_for_json(item) for item in data if item is not None]
    elif isinstance(data, (str, int, float, bool, type(None))):
        return data
    elif isinstance(data, set):
        return list(data)
    else:
        return str(data)
```

## Testing
Created `test_json_fix.py` to verify the fix works correctly. The test:
1. Creates a scan data structure with a DynamicContentParser object
2. Passes it through the clean_data_for_json method
3. Verifies the result can be JSON serialized
4. Confirms the parser object was converted to None

## Impact
- Scan reports can now be saved successfully without JSON serialization errors
- Wildcard detection functionality remains intact
- The parser object is simply excluded from saved reports (it's only needed during scanning)
- No impact on scan functionality or accuracy

## Additional Fixes Made

### src/utils/debug_monitor.py
Fixed the `wrap_request` method to handle both dictionary and object responses:
```python
# Handle both dict and object responses
if isinstance(response, dict):
    status_code = response.get('status_code')
    response_size = response.get('size')
else:
    status_code = response.status_code
    response_size = len(response.content) if hasattr(response, 'content') else None
```

This ensures the debug monitor works correctly with the engine's response format.