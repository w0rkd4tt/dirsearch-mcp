#!/usr/bin/env python3
"""Test recursion feature"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.core.dirsearch_engine import DirsearchEngine, ScanRequest, ScanOptions
from src.config.settings import Settings

async def test_recursion():
    settings = Settings()
    engine = DirsearchEngine(settings=settings)
    
    print("Testing recursion feature...")
    print("Default settings:")
    print(f"  Recursive: {settings.default_scan_config['recursive']}")
    print(f"  Recursion depth: {settings.default_scan_config['recursion_depth']}")
    
    # Test with recursion enabled
    scan_request = ScanRequest(
        base_url="https://example.com",
        wordlist="admin,api,test,backup,config",
        extensions=["php", "html"],
        threads=5,
        timeout=5,
        recursive=True,
        recursion_depth=3
    )
    
    print("\nScan configuration:")
    print(f"  Recursive: {scan_request.recursive}")
    print(f"  Recursion depth: {scan_request.recursion_depth}")
    
    # Set up callbacks to monitor recursion
    def progress_callback(current, total):
        print(f"\rProgress: {current}/{total}", end='', flush=True)
    
    def result_callback(result):
        if result.is_directory:
            print(f"\nFound directory: {result.path} [{result.status_code}]")
    
    engine.set_progress_callback(progress_callback)
    engine.set_result_callback(result_callback)
    
    print("\nStarting scan with recursion...")
    
    async with engine:
        response = await engine.execute_scan(scan_request)
    
    print(f"\n\nScan completed!")
    print(f"Total requests: {response.statistics['total_requests']}")
    print(f"Found paths: {response.statistics['found_paths']}")
    
    # Test with recursion disabled
    print("\n" + "="*50)
    print("Testing with recursion disabled...")
    
    scan_request.recursive = False
    
    async with engine:
        response2 = await engine.execute_scan(scan_request)
    
    print(f"\nScan completed (no recursion)!")
    print(f"Total requests: {response2.statistics['total_requests']}")
    print(f"Found paths: {response2.statistics['found_paths']}")

if __name__ == "__main__":
    asyncio.run(test_recursion())