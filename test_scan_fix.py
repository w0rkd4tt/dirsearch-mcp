#!/usr/bin/env python3
"""
Test the scan execution fix
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.dirsearch_engine import DirsearchEngine, ScanRequest
from src.config.settings import Settings


async def test_scan():
    """Test the scan execution"""
    print("Testing DirsearchEngine scan execution...")
    
    # Create engine
    settings = Settings()
    engine = DirsearchEngine(settings)
    
    # Create scan request
    request = ScanRequest(
        base_url="http://example.com",
        wordlist="admin,test,login",  # Simple inline wordlist
        extensions=["php", "html"],
        threads=5,
        timeout=10
    )
    
    print(f"✅ Created ScanRequest for {request.base_url}")
    print(f"   Wordlist: {request.wordlist}")
    print(f"   Extensions: {request.extensions}")
    
    try:
        # Execute scan
        print("\n⏳ Executing scan...")
        response = await engine.execute_scan(request)
        
        print(f"\n✅ Scan completed successfully!")
        print(f"   Duration: {response.duration:.2f}s")
        print(f"   Total requests: {response.statistics.get('total_requests', 0)}")
        print(f"   Found paths: {response.statistics.get('found_paths', 0)}")
        
        if response.results:
            print(f"\n📋 Sample results:")
            for result in response.results[:5]:
                print(f"   [{result['status']}] {result['path']}")
        
    except Exception as e:
        print(f"\n❌ Error during scan: {e}")
        import traceback
        traceback.print_exc()
        

if __name__ == "__main__":
    print("DirsearchEngine Scan Test")
    print("=" * 50)
    
    # Run test
    asyncio.run(test_scan())