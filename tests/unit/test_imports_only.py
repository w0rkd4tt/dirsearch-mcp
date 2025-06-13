#!/usr/bin/env python3
"""
Test only the import structure without requiring dependencies
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

def test_integration_imports():
    """Test integration module imports"""
    print("Testing integration module structure...")
    
    try:
        # Test that we can import from __init__.py
        import src.integration
        
        # Check that ScanOptions is available
        if hasattr(src.integration, 'ScanOptions'):
            print("✅ ScanOptions is available in src.integration")
        else:
            print("❌ ScanOptions not found in src.integration")
            print(f"Available attributes: {dir(src.integration)}")
        
        # Try direct import
        from src.integration import ScanOptions
        print("✅ Can import ScanOptions directly")
        
        # Check other imports
        from src.integration import DirsearchMCP, Plugin, PluginManager
        print("✅ Can import DirsearchMCP, Plugin, PluginManager")
        
        from src.integration import EventHook, EventType
        print("✅ Can import EventHook, EventType")
        
        from src.integration import ScanData, TargetData, ResultData
        print("✅ Can import data formats")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_dataclasses():
    """Test that dataclasses are properly defined"""
    print("\nTesting dataclass definitions...")
    
    try:
        from src.core.dirsearch_engine import ScanRequest, ScanResponse, ScanOptions as EngineScanOptions
        print("✅ DirsearchEngine dataclasses are defined")
        
        # Check ScanRequest fields
        import inspect
        if hasattr(ScanRequest, '__dataclass_fields__'):
            fields = list(ScanRequest.__dataclass_fields__.keys())
            print(f"  ScanRequest fields: {', '.join(fields[:5])}...")
        
        return True
    except Exception as e:
        print(f"❌ Error checking dataclasses: {e}")
        return False

def main():
    """Run import tests"""
    print("Dirsearch MCP - Import Structure Test")
    print("=" * 50)
    
    # Test integration imports
    test_integration_imports()
    
    # Test dataclasses
    test_dataclasses()
    
    print("\n" + "=" * 50)
    print("Import structure test complete!")
    print("\nNote: The 'aiohttp' error is expected - you need to install dependencies:")
    print("  1. Create virtual environment: python3 -m venv venv")
    print("  2. Activate it: source venv/bin/activate")
    print("  3. Install deps: pip install -r requirements.txt")

if __name__ == "__main__":
    main()