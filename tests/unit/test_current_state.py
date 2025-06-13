#!/usr/bin/env python3
"""
Test current state of dirsearch-mcp after all fixes
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

async def test_imports():
    """Test all imports work correctly"""
    print("Testing imports...")
    
    try:
        from src.core.dirsearch_engine import DirsearchEngine, ScanRequest, ScanResponse
        print("✅ DirsearchEngine imports successful")
        
        from src.core.mcp_coordinator import MCPCoordinator
        print("✅ MCPCoordinator import successful")
        
        from src.cli.interactive_menu import InteractiveMenu
        print("✅ InteractiveMenu import successful")
        
        from src.config.settings import Settings
        print("✅ Settings import successful")
        
        from src.utils.logger import LoggerSetup
        print("✅ LoggerSetup import successful")
        
        from src.utils.reporter import ReportGenerator
        print("✅ ReportGenerator import successful")
        
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

async def test_basic_functionality():
    """Test basic functionality"""
    print("\nTesting basic functionality...")
    
    try:
        from src.core.dirsearch_engine import DirsearchEngine, ScanRequest
        from src.config.settings import Settings
        
        # Create instances
        settings = Settings()
        engine = DirsearchEngine(settings)
        print("✅ Created DirsearchEngine instance")
        
        # Create scan request
        request = ScanRequest(
            base_url="http://test.local",
            wordlist="test,admin,login",
            extensions=["php", "html"],
            threads=5
        )
        print("✅ Created ScanRequest")
        
        # Test wordlist loading
        wordlist = engine._load_wordlist("test,admin,login")
        assert wordlist == ["test", "admin", "login"]
        print("✅ Wordlist loading works")
        
        return True
    except Exception as e:
        print(f"❌ Functionality error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_integration_module():
    """Test integration module"""
    print("\nTesting integration module...")
    
    try:
        from src.integration import DirsearchMCP, ScanOptions
        
        # Create instance
        dirsearch = DirsearchMCP()
        print("✅ Created DirsearchMCP instance")
        
        # Create options
        options = ScanOptions(
            wordlist="test.txt",
            extensions=["php"],
            threads=10
        )
        print("✅ Created ScanOptions")
        
        return True
    except Exception as e:
        print(f"❌ Integration module error: {e}")
        return False

async def main():
    """Run all tests"""
    print("Dirsearch MCP - Current State Test")
    print("=" * 50)
    
    all_passed = True
    
    # Test imports
    if not await test_imports():
        all_passed = False
    
    # Test basic functionality
    if not await test_basic_functionality():
        all_passed = False
    
    # Test integration module
    if not await test_integration_module():
        all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✅ All tests passed! The application is ready to use.")
        print("\nYou can now run:")
        print("  - python main.py          # For interactive CLI")
        print("  - python main.py --help   # For command-line options")
        print("  - See examples/ directory for integration examples")
    else:
        print("❌ Some tests failed. Please check the errors above.")

if __name__ == "__main__":
    asyncio.run(main())