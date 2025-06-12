#!/usr/bin/env python3
"""Demo script to test real-time progress"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.core.dirsearch_engine import DirsearchEngine, ScanRequest, ScanResult
from src.config.settings import Settings

async def main():
    settings = Settings()
    engine = DirsearchEngine(settings=settings)
    
    # Set up progress callback
    def progress_callback(current, total):
        print(f"\rProgress: {current}/{total} ({current/total*100:.1f}%)", end='', flush=True)
    
    def result_callback(result):
        if result.status_code != 404:
            print(f"\nFound: [{result.status_code}] {result.path}")
    
    engine.set_progress_callback(progress_callback)
    engine.set_result_callback(result_callback)
    
    # Create scan request
    scan_request = ScanRequest(
        base_url="https://example.com",
        wordlist="admin,test,login,api,config",
        extensions=["php", "html"],
        threads=5,
        timeout=5
    )
    
    print("Starting scan with real-time progress...")
    
    async with engine:
        response = await engine.execute_scan(scan_request)
        
    print(f"\n\nScan completed!")
    print(f"Total requests: {response.statistics['total_requests']}")
    print(f"Found paths: {response.statistics['found_paths']}")

if __name__ == "__main__":
    asyncio.run(main())