#!/usr/bin/env python3
"""Test script to verify the dirsearch-mcp functionality"""

import asyncio
from src.core.dirsearch_engine import DirsearchEngine, ScanRequest, ScanOptions
from src.config.settings import Settings

async def test_scan():
    # Initialize settings
    settings = Settings()
    
    # Create engine
    engine = DirsearchEngine(settings=settings)
    
    # Create scan request
    scan_request = ScanRequest(
        base_url="https://example.com",
        wordlist="admin,login,dashboard,api,test",
        extensions=["php", "html"],
        threads=5,
        timeout=10
    )
    
    print("Starting test scan...")
    
    async with engine:
        response = await engine.execute_scan(scan_request)
        
        print(f"\nScan completed!")
        print(f"Target: {response.target_url}")
        print(f"Duration: {response.duration:.2f} seconds")
        print(f"Statistics: {response.statistics}")
        print(f"Found {len(response.results)} results")
        
        for result in response.results[:5]:  # Show first 5 results
            print(f"  - {result['path']} [{result['status']}] {result['size']} bytes")

if __name__ == "__main__":
    asyncio.run(test_scan())